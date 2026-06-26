from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.config import load_config, save_config
from backend.services.tweetgen import test_provider_connection

router = APIRouter(prefix="/api/settings", tags=["settings"])


class TestProviderRequest(BaseModel):
    provider_index: int = 0
    model: str | None = None


@router.get("")
async def api_get_settings():
    return load_config()


@router.post("")
async def api_update_settings(config: dict):
    save_config(config)
    return {"status": "ok", "config": load_config()}


@router.post("/test-provider")
async def api_test_provider(req: TestProviderRequest):
    config = load_config()
    result = test_provider_connection(config, provider_index=req.provider_index, model=req.model)
    return result
