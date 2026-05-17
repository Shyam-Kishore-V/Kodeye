"""
Documentation Generation Service
Pure LLM-based — no external vector store required.
Generates docstrings, README and API reference for Python, JS and HTML.
"""

from app.services.llm_service import chat


async def generate_docstring(code: str, language: str, provider: str, model: str) -> str:
    """Add docstrings / JSDoc comments to every function and class."""
    lines = [
        "You are an expert technical writer.",
        "Add comprehensive docstrings/comments to EVERY function, class and method",
        "in the following " + language + " code.",
        "Return ONLY the fully documented code — no extra explanation.",
        "",
        "```" + language,
        code,
        "```",
    ]
    prompt = "\n".join(lines)
    system = "You are an expert software engineer specialising in code documentation."
    return await chat(prompt, system=system, provider=provider, model=model, max_tokens=2048)


async def generate_readme(code: str, language: str, provider: str, model: str) -> str:
    """Generate a complete README.md for the given code module."""
    lines = [
        "You are a technical writer. Analyse the following " + language + " code",
        "and generate a complete, professional README.md that includes:",
        "- Project title and one-line description",
        "- Feature list inferred from the code",
        "- Installation / setup steps",
        "- Usage examples with code snippets",
        "- Function / API reference table",
        "- License section",
        "",
        "Return valid Markdown only.",
        "",
        "```" + language,
        code,
        "```",
    ]
    prompt = "\n".join(lines)
    system = "You are a professional technical writer creating open-source documentation."
    return await chat(prompt, system=system, provider=provider, model=model, max_tokens=2048)


async def generate_api_docs(code: str, language: str, provider: str, model: str) -> str:
    """Generate a structured API reference document."""
    lines = [
        "You are a technical writer. Analyse the following " + language + " code",
        "and generate a structured API reference document that includes:",
        "- Function / method signatures with parameter types and descriptions",
        "- Return value descriptions",
        "- Example usage for each function",
        "- Exceptions / errors raised",
        "",
        "Return clean Markdown only.",
        "",
        "```" + language,
        code,
        "```",
    ]
    prompt = "\n".join(lines)
    system = "You are a professional API documentation writer."
    return await chat(prompt, system=system, provider=provider, model=model, max_tokens=2048)
