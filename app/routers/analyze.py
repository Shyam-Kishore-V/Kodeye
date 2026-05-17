"""Analysis router — all code analysis endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import llm_service, static_analysis, ensemble
from app.services import doc_service

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyseRequest(BaseModel):
    code:     str
    language: str = "python"
    provider: Optional[str] = None
    model:    Optional[str] = None


# ── 1. Code Review ────────────────────────────────────────────
@router.post("/review")
async def code_review(req: AnalyseRequest):
    prompt = "\n".join([
        "Review the following " + req.language + " code thoroughly. Provide:",
        "1. **Overall Assessment** — quality rating 1-10 with rationale",
        "2. **Issues Found** — bugs, anti-patterns, code smells",
        "3. **Best Practice Violations** — naming, structure, readability",
        "4. **Refactoring Suggestions** — concrete improvements with examples",
        "5. **Positive Highlights** — what is done well",
        "",
        "```" + req.language,
        req.code,
        "```",
    ])
    try:
        result = await llm_service.chat(
            prompt=prompt,
            system="You are a senior software engineer doing a thorough code review. Be specific and cite line numbers.",
            provider=req.provider,
            model=req.model,
        )
        return {"review": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 2. Security Scan ──────────────────────────────────────────
@router.post("/security")
async def security_scan(req: AnalyseRequest):
    prompt = "\n".join([
        "Perform a security audit of the following " + req.language + " code.",
        "For each vulnerability specify:",
        "- **Type** (e.g. SQL Injection, XSS, Command Injection, Hardcoded Secret)",
        "- **Severity** — Critical / High / Medium / Low",
        "- **Location** — line number or function name",
        "- **Description** — what it is and how it can be exploited",
        "- **Remediation** — specific code fix",
        "",
        "If no vulnerabilities found, confirm the code is secure.",
        "",
        "```" + req.language,
        req.code,
        "```",
    ])
    try:
        result = await llm_service.chat(
            prompt=prompt,
            system="You are a cybersecurity expert specialising in OWASP Top 10 and application security.",
            provider=req.provider,
            model=req.model,
        )
        return {"security_report": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 3. Static Analysis ────────────────────────────────────────
@router.post("/static")
async def run_static(req: AnalyseRequest):
    try:
        return static_analysis.run_static_analysis(req.code, req.language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 4. Documentation ──────────────────────────────────────────
@router.post("/docs")
async def generate_docs(req: AnalyseRequest, doc_type: str = "docstring"):
    try:
        prov  = req.provider or ""
        mod   = req.model or ""
        if doc_type == "readme":
            result = await doc_service.generate_readme(req.code, req.language, prov, mod)
        elif doc_type == "api":
            result = await doc_service.generate_api_docs(req.code, req.language, prov, mod)
        else:
            result = await doc_service.generate_docstring(req.code, req.language, prov, mod)
        return {"documentation": result, "doc_type": doc_type, "rag_enabled": False}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 5. Ensemble ───────────────────────────────────────────────
@router.post("/ensemble")
async def run_ensemble(req: AnalyseRequest):
    try:
        static_result = static_analysis.run_static_analysis(req.code, req.language)
        review = await llm_service.chat(
            prompt="Briefly review this " + req.language + " code in 3 sentences:\n```\n" + req.code + "\n```",
            provider=req.provider,
            model=req.model,
            max_tokens=512,
        )
        verdict = ensemble.ensemble_score(static_result, review)
        verdict["llm_summary"] = review
        return verdict
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── 6. Full Analyse (VS Code extension) ───────────────────────
@router.post("/analyze")
async def full_analyze(req: AnalyseRequest):
    try:
        static_result = static_analysis.run_static_analysis(req.code, req.language)
        review = await llm_service.chat(
            prompt="Review this " + req.language + " code:\n```\n" + req.code + "\n```",
            provider=req.provider,
            model=req.model,
        )
        verdict = ensemble.ensemble_score(static_result, review)
        return {"static": static_result, "review": review, "ensemble": verdict}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
