# 👁️ Kodeye — Intelligent Code Analysis & Documentation Generation
---

## What is Kodeye?

Kodeye is an AI-powered code analysis system that provides:

| Feature | Description |
|---|---|
| **Code Review** | LLM-powered quality review with ratings and suggestions |
| **Security Scan** | OWASP Top 10 vulnerability detection |
| **Static Analysis** | AST + Pylint + Bandit for Python; pattern checks for JS/HTML |
| **Documentation** | Auto-generate docstrings, README, and API reference |
| **Ensemble Score** | Combined quality grade (A–F) using static + LLM signals |
| **Multi-Provider LLM** | Groq · OpenAI · Anthropic · Google Gemini |
| **VS Code Extension** | Right-click analysis directly in your editor |

---

## Project Structure

```
kodeye/
├── main.py                        ← FastAPI server entry point
├── pyproject.toml                 ← Poetry dependencies
├── .env.example                   ← Copy to .env and add API keys
│
├── app/
│   ├── config.py                  ← Settings and provider model list
│   ├── routers/
│   │   ├── analyze.py             ← /api/review, /security, /static, /docs, /ensemble
│   │   └── settings.py            ← /api/settings (live key management)
│   └── services/
│       ├── llm_service.py         ← Groq / OpenAI / Anthropic / Google
│       ├── static_analysis.py     ← AST + Pylint + Bandit + JS/HTML checks
│       ├── doc_service.py         ← Documentation generation
│       └── ensemble.py            ← Weighted ensemble scoring
│
├── static/
│   └── index.html                 ← Full web UI (served by FastAPI)
│
└── vscode-extension/
    ├── package.json               ← Extension manifest
    └── src/
        └── extension.js           ← Extension logic
```

---

## Part 1 — Running the Web Application

### Prerequisites
- Python 3.10
- Poetry 2.0+
- At least one LLM API key (Groq is free and recommended)

### Step 1 — Get an API Key
Go to **https://console.groq.com** → sign up → create an API key (it's free).

### Step 2 — Set up environment
Open Git Bash, go into the kodeye folder, and create your `.env` file:

```bash
cd /d/Personal/Project/kodeye
cp .env.example .env
```

Open `.env` in Notepad and paste your key:
```
GROQ_API_KEY=gsk_your_key_here
```

### Step 3 — Install dependencies

```bash
poetry install
```

This takes 2–3 minutes the first time.

### Step 4 — Start the server

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You will see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 5 — Open the web app

Open your browser and go to:
```
http://localhost:8000
```

You will see the Kodeye UI with a code editor on the left and results panel on the right.

### How to use the web UI

1. **Select a language** — Python / JavaScript / HTML (top right of editor)
2. **Load a demo** — Click any demo button (🐍 Py Bugs, 🔒 Py Security, etc.)
3. **Select analysis mode** — Click one of the chips: Code Review / Security / Static / Docs / Ensemble
4. **Click Analyse** — Results appear on the right panel
5. **Switch providers** — Use the Provider and Model dropdowns at the top
6. **Add API keys** — Click "API Keys" button at top right

---

## Part 2 — VS Code Extension

The VS Code extension connects to your running Kodeye server and lets you right-click any file to analyse it directly in the editor.

### Prerequisites
- The Kodeye server must be running (Part 1 above)
- VS Code installed

### Step 1 — Open a NEW Git Bash window

Keep the server running in the first window. Open a second Git Bash and run:

```bash
code --extensionDevelopmentPath="D:\Personal\Project\kodeye\vscode-extension"
```

> ⚠️ Change the path to wherever you extracted kodeye.

### Step 2 — Confirm it loaded

A **second VS Code window** opens with **`[Extension Development Host]`** in the title bar.

You will see a notification: **"👁️ Kodeye loaded! Right-click any file → Kodeye options."**

You will also see **`👁 Kodeye`** in the bottom-right status bar.

### Step 3 — Analyse code

In the Extension Development Host window:

1. Open any `.py`, `.js`, or `.html` file
2. **Right-click** anywhere in the editor
3. You will see:
   - **Kodeye: Analyze Entire File**
   - **Kodeye: Analyze Selected Code**
   - **Kodeye: Generate Documentation**
4. Click one — a results panel opens on the right side

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+K` | Analyse entire file |
| `Ctrl+Shift+A` | Analyse selected code |

### Changing settings

Go to **File → Preferences → Settings** → search for "Kodeye":

| Setting | Default | Description |
|---|---|---|
| `kodeye.backendUrl` | `http://localhost:8000` | Your server URL |
| `kodeye.provider` | `groq` | LLM provider |
| `kodeye.model` | `llama-3.3-70b-versatile` | Model to use |

---

## API Reference

The server exposes these endpoints (also available at `http://localhost:8000/api/docs`):

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | Web UI |
| `POST /api/review` | POST | LLM code review |
| `POST /api/security` | POST | Security scan |
| `POST /api/static` | POST | Static analysis |
| `POST /api/docs` | POST | Documentation generation |
| `POST /api/ensemble` | POST | Ensemble quality score |
| `POST /api/analyze` | POST | Full analysis (used by VS Code extension) |
| `GET /api/settings/` | GET | View current settings |
| `POST /api/settings/` | POST | Update API keys live |
| `GET /api/health` | GET | Health check |

### Example API call

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{"code": "def add(a,b): return a+b", "language": "python", "provider": "groq", "model": "llama-3.3-70b-versatile"}'
```

---

## Supported LLM Providers

| Provider | Models | Get Key |
|---|---|---|
| **Groq** (recommended, free) | Llama 3.3 70B, Llama 4 Maverick, Llama 4 Scout, Llama 3 8B, Qwen QwQ 32B | console.groq.com |
| **OpenAI** | GPT-4o, GPT-4o Mini, GPT-4 Turbo | platform.openai.com |
| **Anthropic** | Claude Sonnet 4, Claude 3.5 Haiku | console.anthropic.com |
| **Google** | Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0 Flash | aistudio.google.com |

API keys can be added in the `.env` file **or** directly in the web UI under **API Keys** (no server restart needed).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `poetry: command not found` | Close and reopen Git Bash |
| `Port 8000 already in use` | Run with `--port 8001` instead |
| Kodeye not showing in right-click | Make sure you are in the **Extension Development Host** window (title bar shows this) |
| LLM returns error | Check your API key is set correctly in `.env` or Settings panel |
| `chromadb` install error | Already removed from dependencies — safe to ignore |
| White box in editor | Hard refresh browser with `Ctrl+Shift+R` |

---

## Running Every Time

You need **two** things running simultaneously:

**Terminal 1 — Backend server:**
```bash
cd kodeye
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — VS Code extension (optional):**
```bash
code --extensionDevelopmentPath="D:\Personal\Project\kodeye\vscode-extension"
```

**Browser:** Open `http://localhost:8000`
