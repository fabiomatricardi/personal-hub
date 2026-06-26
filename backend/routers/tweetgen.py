import os
import json
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.models import TweetRequest, TweetResponse, ChatRequest
from backend.services.config import load_config
from backend.services.tweetgen import parse_file, split_into_tweets, call_llm, call_llm_stream, MAX_INPUT_CHARS

router = APIRouter(prefix="/api/tweetgen", tags=["tweetgen"])

TWEET_GEN_SYSTEM = """You are an expert social media copywriter. Your job is to convert articles or text into engaging tweet threads.

Rules:
- Each tweet must be under 280 characters
- Break long content into a thread (numbered tweets)
- Be concise, punchy, and engaging
- Preserve the key message and tone
- Use line breaks within tweets for readability
- Do NOT use hashtags excessively (0-2 per tweet max)
- Start with a hook that makes people want to read the thread"""


class ParseRequest(BaseModel):
    file_name: str


class ParseResponse(BaseModel):
    text: str


@router.post("/parse", response_model=ParseResponse)
async def api_parse_file(req: ParseRequest):
    upload_dir = os.path.join(tempfile.gettempdir(), "myhub_uploads")
    filepath = os.path.join(upload_dir, req.file_name)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail=f"File '{req.file_name}' not found")
    try:
        text = parse_file(filepath)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")
    return ParseResponse(text=text)


@router.post("/generate", response_model=TweetResponse)
async def api_generate_tweets(req: TweetRequest):
    config = load_config()

    text = req.text
    if req.file_name:
        upload_dir = os.path.join(tempfile.gettempdir(), "myhub_uploads")
        filepath = os.path.join(upload_dir, req.file_name)
        if not os.path.isfile(filepath):
            raise HTTPException(status_code=404, detail=f"File '{req.file_name}' not found")
        try:
            text = parse_file(filepath)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text content to generate tweets from")

    truncated = False
    original_len = len(text)
    if original_len > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS]
        truncated = True

    messages = [
        {"role": "system", "content": TWEET_GEN_SYSTEM},
        {"role": "user", "content": f"Convert the following text into a tweet thread. Each tweet must be under 280 characters. Number them (1/N format). If the content is short enough for a single tweet, just return one tweet.\n\n---\n{text}\n---"},
    ]

    try:
        response_text = call_llm(messages, config, provider_index=req.provider_index, model=req.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}")

    tweets = split_into_tweets(response_text)
    warning = None
    if truncated:
        warning = f"Input was truncated from {original_len} to {MAX_INPUT_CHARS} characters to fit token limits"
    return TweetResponse(tweets=tweets, warning=warning)


@router.post("/upload")
async def api_upload_file(file: UploadFile = File(...)):
    upload_dir = os.path.join(tempfile.gettempdir(), "myhub_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {"filename": file.filename, "size": len(content)}


@router.post("/chat")
async def api_chat(req: ChatRequest):
    config = load_config()

    messages = [{"role": "system", "content": TWEET_GEN_SYSTEM}]

    if req.context:
        messages.append({"role": "system", "content": f"Original content for reference:\n---\n{req.context}\n---"})

    for msg in req.messages:
        messages.append({"role": msg.role, "content": msg.content})

    async def event_stream():
        try:
            for chunk in call_llm_stream(messages, config, provider_index=req.provider_index, model=req.model):
                data = json.dumps({"content": chunk})
                yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
