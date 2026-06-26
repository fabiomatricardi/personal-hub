from fastapi import APIRouter, HTTPException
from backend.models import WikiFile, WikiContent
from backend.services.wiki import list_files, read_file

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


@router.get("/files", response_model=list[WikiFile])
async def api_list_wiki_files():
    return list_files()


@router.get("/file/{name}", response_model=WikiContent)
async def api_get_wiki_file(name: str):
    result = read_file(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Wiki file '{name}' not found")
    return result
