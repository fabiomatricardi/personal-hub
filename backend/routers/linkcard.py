from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.models import LinkCardRequest, LinkCardResponse
from backend.services.config import load_config
from backend.services.linkcard import generate_card_html, fetch_metadata

router = APIRouter(prefix="/api/linkcard", tags=["linkcard"])


class FetchMetadataRequest(BaseModel):
    url: str


@router.post("/generate", response_model=LinkCardResponse)
async def api_generate_card(req: LinkCardRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
    config = load_config()
    theme = config.get("card_theme", "dark")
    try:
        html = generate_card_html(
            url=req.url,
            title=req.title,
            description=req.description,
            image_url=req.image_url,
            theme=theme,
        )
        return LinkCardResponse(html=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-metadata")
async def api_fetch_metadata(req: FetchMetadataRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return fetch_metadata(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
