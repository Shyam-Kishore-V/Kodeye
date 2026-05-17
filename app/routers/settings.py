"""Settings router — live API key management without server restart."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings, PROVIDER_MODELS

router = APIRouter(prefix="/api/settings", tags=["settings"])


class KeysPayload(BaseModel):
    groq_api_key:      Optional[str] = None
    openai_api_key:    Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key:    Optional[str] = None
    default_provider:  Optional[str] = None
    default_model:     Optional[str] = None


def _mask(key: Optional[str]) -> str:
    if not key:
        return ""
    return key[:6] + "\u2022" * max(0, len(key) - 6) if len(key) > 6 else "\u2022" * len(key)


@router.get("/")
def get_settings():
    return {
        "groq_api_key":      _mask(settings.groq_api_key),
        "openai_api_key":    _mask(settings.openai_api_key),
        "anthropic_api_key": _mask(settings.anthropic_api_key),
        "google_api_key":    _mask(settings.google_api_key),
        "default_provider":  settings.default_provider,
        "default_model":     settings.default_model,
    }


@router.post("/")
def update_settings(payload: KeysPayload):
    if payload.groq_api_key      is not None: settings.groq_api_key      = payload.groq_api_key
    if payload.openai_api_key    is not None: settings.openai_api_key    = payload.openai_api_key
    if payload.anthropic_api_key is not None: settings.anthropic_api_key = payload.anthropic_api_key
    if payload.google_api_key    is not None: settings.google_api_key    = payload.google_api_key
    if payload.default_provider  is not None: settings.default_provider  = payload.default_provider
    if payload.default_model     is not None: settings.default_model     = payload.default_model
    return {"status": "ok", "message": "Settings updated."}


@router.get("/models")
def get_models():
    return {"providers": PROVIDER_MODELS}
