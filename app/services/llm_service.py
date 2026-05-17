"""
Multi-provider LLM service.
Supports Groq, OpenAI, Anthropic and Google Gemini with a unified interface.
"""

from typing import Optional
from app.config import settings


async def chat(
    prompt: str,
    system: str = "You are an expert software engineer and code reviewer.",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 2048,
) -> str:
    """Send a prompt to the selected provider and return the text response."""
    prov = (provider or settings.default_provider or "groq").lower()
    mod = model or settings.default_model or "llama-3.3-70b-versatile"

    if prov == "groq":
        return await _call_groq(prompt, system, mod, max_tokens)
    elif prov == "openai":
        return await _call_openai(prompt, system, mod, max_tokens)
    elif prov == "anthropic":
        return await _call_anthropic(prompt, system, mod, max_tokens)
    elif prov == "google":
        return await _call_google(prompt, system, mod, max_tokens)
    else:
        raise ValueError("Unknown provider: " + prov)


async def _call_groq(prompt: str, system: str, model: str, max_tokens: int) -> str:
    from groq import Groq
    if not settings.groq_api_key:
        raise RuntimeError("Groq API key not set. Open Settings and add your key.")
    client = Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


async def _call_openai(prompt: str, system: str, model: str, max_tokens: int) -> str:
    from openai import AsyncOpenAI
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key not set. Open Settings and add your key.")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


async def _call_anthropic(prompt: str, system: str, model: str, max_tokens: int) -> str:
    import anthropic
    if not settings.anthropic_api_key:
        raise RuntimeError("Anthropic API key not set. Open Settings and add your key.")
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=model,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return resp.content[0].text if resp.content else ""


async def _call_google(prompt: str, system: str, model: str, max_tokens: int) -> str:
    import google.generativeai as genai
    if not settings.google_api_key:
        raise RuntimeError("Google API key not set. Open Settings and add your key.")
    genai.configure(api_key=settings.google_api_key)
    full_prompt = system + "\n\n" + prompt
    gemini = genai.GenerativeModel(model)
    resp = gemini.generate_content(
        full_prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.3,
        ),
    )
    return resp.text or ""
