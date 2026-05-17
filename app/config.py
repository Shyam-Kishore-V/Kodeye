"""Kodeye configuration — loads from .env, overridable at runtime via API."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "groq")
    default_model: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()

PROVIDER_MODELS = {
    "groq": [
        {"id": "llama-3.3-70b-versatile",            "name": "Llama 3.3 70B"},
        {"id": "llama-4-maverick-17b-128e-instruct",  "name": "Llama 4 Maverick"},
        {"id": "llama-4-scout-17b-16e-instruct",      "name": "Llama 4 Scout"},
        {"id": "llama3-8b-8192",                      "name": "Llama 3 8B"},
        {"id": "qwen-qwq-32b",                        "name": "Qwen QwQ 32B"},
    ],
    "openai": [
        {"id": "gpt-4o",       "name": "GPT-4o"},
        {"id": "gpt-4o-mini",  "name": "GPT-4o Mini"},
        {"id": "gpt-4-turbo",  "name": "GPT-4 Turbo"},
    ],
    "anthropic": [
        {"id": "claude-sonnet-4-20250514",   "name": "Claude Sonnet 4"},
        {"id": "claude-3-5-haiku-20241022",  "name": "Claude 3.5 Haiku"},
    ],
    "google": [
        {"id": "gemini-1.5-pro",   "name": "Gemini 1.5 Pro"},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
    ],
}
