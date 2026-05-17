"""
RAG Documentation Service
Uses ChromaDB + sentence-transformers to generate context-aware documentation.
Falls back to direct LLM generation when vector store is empty.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional, Any

RAG_AVAILABLE = False
_collection = None

def _init_rag():
    global RAG_AVAILABLE, _collection
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        client = chromadb.Client()
        _collection = client.get_or_create_collection(
            name="kodeye_docs",
            metadata={"hnsw:space": "cosine"},
        )
        RAG_AVAILABLE = True
    except Exception as exc:
        print(f"[Kodeye] RAG init skipped: {exc}")
        RAG_AVAILABLE = False


_init_rag()


# ── Seed corpus ────────────────────────────────────────────────────────────────
_SEED_DOCS = [
    {
        "id": "pep257",
        "text": (
            "PEP 257 Docstring Convention: The docstring for a function or method should "
            "summarize its behavior and document its arguments, return value(s), side effects, "
            "exceptions raised, and restrictions on when it can be called. "
            "Format: Args: section, Returns: section, Raises: section."
        ),
    },
    {
        "id": "jsdoc",
        "text": (
            "JSDoc standard: Use @param {type} name - description for parameters. "
            "@returns {type} description for return value. @throws {Error} for exceptions. "
            "@example for usage examples. Place block comment /** before function."
        ),
    },
    {
        "id": "readme_template",
        "text": (
            "README.md structure: Title and badges, Short description, Features list, "
            "Installation instructions, Quick-start usage, Configuration, API reference, "
            "Contributing guide, License."
        ),
    },
    {
        "id": "api_doc_rest",
        "text": (
            "REST API documentation: Document each endpoint with HTTP method, URL path, "
            "request headers, request body schema (JSON), response body schema, "
            "HTTP status codes, and a curl example."
        ),
    },
    {
        "id": "type_hints",
        "text": (
            "Python type hints best practice: Use typing module for complex types. "
            "Annotate all public function parameters and return types. "
            "Use Optional[T] for nullable values, Union[A,B] for multiple types, "
            "List, Dict, Tuple from typing for Python < 3.9."
        ),
    },
]


def _seed_if_empty():
    if not RAG_AVAILABLE or _collection is None:
        return
    if _collection.count() == 0:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode([d["text"] for d in _SEED_DOCS]).tolist()
        _collection.add(
            ids=[d["id"] for d in _SEED_DOCS],
            embeddings=embeddings,
            documents=[d["text"] for d in _SEED_DOCS],
        )


def _retrieve_context(query: str, top_k: int = 3) -> str:
    """Retrieve relevant documentation context from the vector store."""
    if not RAG_AVAILABLE or _collection is None:
        return ""
    try:
        _seed_if_empty()
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        q_emb = model.encode([query]).tolist()
        results = _collection.query(query_embeddings=q_emb, n_results=min(top_k, _collection.count()))
        docs = results.get("documents", [[]])[0]
        return "\n\n".join(docs) if docs else ""
    except Exception as exc:
        print(f"[Kodeye] RAG retrieval error: {exc}")
        return ""


async def generate_docstring(code: str, language: str, provider: str, model: str) -> str:
    """Generate inline docstrings/JSDoc for the given code."""
    from app.services.llm_service import chat
    context = _retrieve_context(f"{language} docstring conventions best practices")
    prompt = f"""You are an expert at writing documentation.
{f'Use these documentation standards as reference:\n{context}\n' if context else ''}
Generate comprehensive docstrings/comments for every function, class, and method in the following {language} code.
Return ONLY the fully documented code (no extra explanation).

```{language}
{code}
```
"""
    return await chat(prompt, provider=provider, model=model, max_tokens=2048)


async def generate_readme(code: str, language: str, provider: str, model: str) -> str:
    """Generate a README.md for the given code module."""
    from app.services.llm_service import chat
    context = _retrieve_context("README.md template structure")
    prompt = f"""You are a technical writer creating a README.md.
{f'Follow this README structure:\n{context}\n' if context else ''}
Analyse the following {language} code and generate a complete, professional README.md with:
- Project title and one-line description
- Features list (inferred from the code)
- Installation/setup steps
- Usage examples with code snippets
- API/Function reference table

```{language}
{code}
```

Return valid Markdown only.
"""
    return await chat(prompt, provider=provider, model=model, max_tokens=2048)


async def generate_api_docs(code: str, language: str, provider: str, model: str) -> str:
    """Generate API/function reference documentation."""
    from app.services.llm_service import chat
    context = _retrieve_context("API documentation REST endpoint reference")
    prompt = f"""You are a technical writer creating API documentation.
{f'Use this as reference:\n{context}\n' if context else ''}
Analyse the following {language} code and generate a structured API reference document including:
- Function/method signatures with parameter types and descriptions
- Return value descriptions
- Example usage for each function
- Any raised exceptions

```{language}
{code}
```

Return clean Markdown.
"""
    return await chat(prompt, provider=provider, model=model, max_tokens=2048)
