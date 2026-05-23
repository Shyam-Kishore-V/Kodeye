# 👁️ Kodeye — Intelligent Code Analysis

AI-powered code review, security scanning, static analysis, and documentation
generation — directly inside VS Code. No setup required.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Code Review** | LLM-powered quality feedback with ratings and suggestions |
| **Security Scan** | OWASP Top 10 vulnerability detection |
| **Static Analysis** | AST + Pylint + Bandit for Python; pattern checks for JS/HTML |
| **Documentation** | Auto-generate docstrings, README, and API reference |
| **Ensemble Score** | Combined quality grade (A–F) using static + LLM signals |
| **Multi-Provider LLM** | Groq · OpenAI · Anthropic · Google Gemini |

---

## 🚀 Getting Started

1. Install the extension
2. Open any `.py`, `.js`, or `.html` file
3. **Right-click** anywhere in the editor
4. Choose an action:
   - **Kodeye: Analyze Entire File**
   - **Kodeye: Analyze Selected Code**
   - **Kodeye: Generate Documentation**
5. Results appear in a panel on the right

No API keys needed — Kodeye connects to a hosted backend at
[kodeye.onrender.com](https://kodeye.onrender.com) out of the box.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+K` | Analyse entire file |
| `Ctrl+Shift+A` | Analyse selected code |

---

## ⚙️ Settings

Go to **File → Preferences → Settings** and search for `Kodeye`:

| Setting | Default | Description |
|---|---|---|
| `kodeye.backendUrl` | `https://kodeye.onrender.com` | Backend URL (change for self-hosting) |
| `kodeye.provider` | `groq` | LLM provider (`groq`, `openai`, `anthropic`, `google`) |
| `kodeye.model` | `llama-3.3-70b-versatile` | Model ID |

---

## 🔧 Self-Hosting

Prefer to run your own backend? The full source is on GitHub:

👉 [github.com/theonlyvsk/Kodeye](https://github.com/theonlyvsk/Kodeye)

Follow the README there to spin up the FastAPI backend locally or on any cloud platform.

---

## 📋 Supported Languages

- Python
- JavaScript
- HTML

---

## 🐛 Issues & Feedback

Found a bug or have a feature request?
[Open an issue on GitHub](https://github.com/theonlyvsk/Kodeye/issues)