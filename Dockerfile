# ── Base image ────────────────────────────────────────────────
FROM python:3.10-slim

# ── Set working directory ─────────────────────────────────────
WORKDIR /app

# ── Install system dependencies ───────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Install Poetry ────────────────────────────────────────────
RUN pip install poetry==2.0.0

# ── Copy dependency files first (for Docker layer caching) ────
COPY pyproject.toml ./

# ── Configure Poetry to not create virtualenv inside container ─
RUN poetry config virtualenvs.create false

# ── Install dependencies ──────────────────────────────────────
RUN poetry install --no-root --no-interaction

# ── Copy rest of application ──────────────────────────────────
COPY . .

# ── Expose port ───────────────────────────────────────────────
EXPOSE 8000

# ── Start server ──────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]