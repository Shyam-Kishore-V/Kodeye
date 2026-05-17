"""
Static Analysis Service
Python  : AST parsing + Pylint + Bandit
JavaScript : pattern-based checks
HTML    : html.parser-based checks
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from typing import Any


# ─────────────────────────────────────────────────────────────
#  PYTHON
# ─────────────────────────────────────────────────────────────

def _ast_analysis(tree: ast.Module, lines: list) -> tuple:
    issues = []
    functions, classes, documented = [], [], 0
    complex_funcs = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            if ast.get_docstring(node):
                documented += 1
            else:
                issues.append({
                    "tool": "AST", "severity": "warning",
                    "line": node.lineno,
                    "message": "Missing docstring in function '" + node.name + "'",
                })
            complexity = sum(
                1 for n in ast.walk(node)
                if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                  ast.With, ast.Assert, ast.comprehension))
            )
            if complexity > 10:
                complex_funcs.append({"name": node.name, "complexity": complexity})
                issues.append({
                    "tool": "AST", "severity": "warning",
                    "line": node.lineno,
                    "message": "High cyclomatic complexity (" + str(complexity) + ") in '" + node.name + "'",
                })

        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            if not ast.get_docstring(node):
                issues.append({
                    "tool": "AST", "severity": "info",
                    "line": node.lineno,
                    "message": "Missing docstring in class '" + node.name + "'",
                })

    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            issues.append({
                "tool": "AST", "severity": "info",
                "line": i,
                "message": "Line too long (" + str(len(line)) + " chars, max 120)",
            })

    total = len(functions)
    metrics = {
        "lines_of_code":     len([l for l in lines if l.strip()]),
        "total_lines":       len(lines),
        "functions":         total,
        "classes":           len(classes),
        "doc_coverage":      round(documented / total * 100, 1) if total else 0,
        "complex_functions": len(complex_funcs),
    }
    return issues, metrics


def _run_pylint(code: str) -> list:
    fd, tmp = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(code)
        result = subprocess.run(
            [sys.executable, "-m", "pylint", tmp,
             "--output-format=json", "--max-line-length=120",
             "--disable=C0114,C0115,C0116"],
            capture_output=True, text=True, timeout=30,
        )
        raw = result.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        smap = {"E": "error", "W": "warning", "C": "info", "R": "info"}
        return [
            {
                "tool": "Pylint",
                "severity": smap.get((item.get("type") or "W")[0], "info"),
                "line": item.get("line", 0),
                "message": "[" + item.get("symbol", "") + "] " + item.get("message", ""),
            }
            for item in data
        ]
    except Exception:
        return []
    finally:
        os.unlink(tmp)


def _run_bandit(code: str) -> list:
    fd, tmp = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(code)
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-f", "json", "-q", tmp],
            capture_output=True, text=True, timeout=30,
        )
        raw = result.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        smap = {"HIGH": "error", "MEDIUM": "warning", "LOW": "info"}
        return [
            {
                "tool": "Bandit",
                "severity": smap.get(r.get("issue_severity", "LOW"), "info"),
                "line": r.get("line_number", 0),
                "message": "[" + r.get("test_id", "") + "] " + r.get("issue_text", "")
                           + " (confidence: " + r.get("issue_confidence", "") + ")",
            }
            for r in data.get("results", [])
        ]
    except Exception:
        return []
    finally:
        os.unlink(tmp)


def analyse_python(code: str) -> dict:
    issues = []
    metrics = {}
    lines = code.splitlines()
    try:
        tree = ast.parse(code)
        ast_issues, ast_metrics = _ast_analysis(tree, lines)
        issues.extend(ast_issues)
        metrics.update(ast_metrics)
    except SyntaxError as exc:
        issues.append({
            "tool": "AST", "severity": "error",
            "line": exc.lineno or 0,
            "message": "Syntax error: " + str(exc.msg),
        })
        return {"issues": issues, "metrics": metrics, "summary": "Syntax error — cannot analyse further."}

    issues.extend(_run_pylint(code))
    issues.extend(_run_bandit(code))

    errors   = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    info     = sum(1 for i in issues if i["severity"] == "info")
    security = sum(1 for i in issues if i.get("tool") == "Bandit")
    summary  = (str(errors) + " error(s), " + str(warnings) + " warning(s), "
                + str(info) + " info, " + str(security) + " security issue(s).")
    return {"issues": issues, "metrics": metrics, "summary": summary}


# ─────────────────────────────────────────────────────────────
#  JAVASCRIPT
# ─────────────────────────────────────────────────────────────

_JS_PATTERNS = [
    (r"\beval\s*\(",             "error",   "eval() — serious security risk, never use it"),
    (r"document\.write\s*\(",    "error",   "document.write() — XSS risk"),
    (r"\.innerHTML\s*=",         "warning", "innerHTML assignment — potential XSS, use textContent"),
    (r"\bvar\s+",                "warning", "Use 'let' or 'const' instead of 'var'"),
    (r"[^=!<>]=={1}(?!=)",      "warning", "Use === instead of =="),
    (r"!={1}(?!=)",              "warning", "Use !== instead of !="),
    (r"console\.log\s*\(",       "info",    "Remove console.log() before production"),
    (r"\balert\s*\(",            "warning", "alert() is intrusive — use UI notifications"),
    (r"debugger\s*;",            "error",   "debugger statement left in code"),
    (r"new XMLHttpRequest\(\)",  "info",    "Consider fetch() instead of XMLHttpRequest"),
]


def analyse_javascript(code: str) -> dict:
    issues = []
    lines = code.splitlines()
    for i, line in enumerate(lines, 1):
        for pattern, severity, message in _JS_PATTERNS:
            if re.search(pattern, line):
                issues.append({"tool": "JSLint", "severity": severity, "line": i, "message": message})

    func_count  = len(re.findall(r"\bfunction\b|=>", code))
    jsdoc_count = len(re.findall(r"/\*\*", code))
    errors   = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    info     = sum(1 for i in issues if i["severity"] == "info")
    metrics = {
        "lines_of_code": len([l for l in lines if l.strip()]),
        "total_lines":   len(lines),
        "functions":     func_count,
        "jsdoc_blocks":  jsdoc_count,
        "doc_coverage":  round(jsdoc_count / func_count * 100, 1) if func_count else 0,
    }
    summary = (str(errors) + " error(s), " + str(warnings) + " warning(s), "
               + str(info) + " info. Doc coverage: " + str(metrics["doc_coverage"]) + "%.")
    return {"issues": issues, "metrics": metrics, "summary": summary}


# ─────────────────────────────────────────────────────────────
#  HTML
# ─────────────────────────────────────────────────────────────

class _HTMLChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.issues = []
        self.img_count = self.form_count = self.input_count = self.label_count = 0
        self._deprecated = {"font", "center", "marquee", "blink", "strike", "basefont", "big", "tt"}

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        line = self.getpos()[0]

        if tag == "img":
            self.img_count += 1
            if "alt" not in attr_dict:
                self.issues.append({"tool": "HTMLLint", "severity": "warning", "line": line,
                                    "message": "<img> missing alt attribute — accessibility issue"})
        if tag == "form":
            self.form_count += 1
        if tag == "input":
            self.input_count += 1
        if tag == "label":
            self.label_count += 1
        if tag in self._deprecated:
            self.issues.append({"tool": "HTMLLint", "severity": "warning", "line": line,
                                 "message": "Deprecated tag <" + tag + "> — use CSS instead"})
        if "style" in attr_dict:
            self.issues.append({"tool": "HTMLLint", "severity": "info", "line": line,
                                 "message": "Inline style on <" + tag + "> — move to stylesheet"})
        if tag == "a" and attr_dict.get("href", "").startswith("javascript:"):
            self.issues.append({"tool": "HTMLLint", "severity": "error", "line": line,
                                 "message": "javascript: href — XSS risk, use event listeners"})


def analyse_html(code: str) -> dict:
    checker = _HTMLChecker()
    try:
        checker.feed(code)
    except Exception as exc:
        return {"issues": [{"tool": "HTMLLint", "severity": "error", "line": 0, "message": str(exc)}],
                "metrics": {}, "summary": "HTML parse error."}

    issues = checker.issues
    lines  = code.splitlines()

    if "viewport" not in code:
        issues.append({"tool": "HTMLLint", "severity": "warning", "line": 0,
                        "message": "Missing <meta name='viewport'> — not mobile-friendly"})
    if not re.search(r"<html[^>]+lang=", code, re.IGNORECASE):
        issues.append({"tool": "HTMLLint", "severity": "warning", "line": 0,
                        "message": "Missing lang attribute on <html> — accessibility issue"})
    if not re.search(r"<title>", code, re.IGNORECASE):
        issues.append({"tool": "HTMLLint", "severity": "warning", "line": 0,
                        "message": "Missing <title> tag"})
    if "document.write" in code:
        issues.append({"tool": "HTMLLint", "severity": "error", "line": 0,
                        "message": "document.write() found — XSS risk"})

    errors   = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    info     = sum(1 for i in issues if i["severity"] == "info")
    metrics = {
        "total_lines": len(lines),
        "images":      checker.img_count,
        "forms":       checker.form_count,
        "inputs":      checker.input_count,
        "labels":      checker.label_count,
    }
    summary = str(errors) + " error(s), " + str(warnings) + " warning(s), " + str(info) + " info."
    return {"issues": issues, "metrics": metrics, "summary": summary}


# ─────────────────────────────────────────────────────────────
#  DISPATCHER
# ─────────────────────────────────────────────────────────────

def run_static_analysis(code: str, language: str) -> dict:
    lang = language.lower()
    if lang == "python":
        return analyse_python(code)
    elif lang in ("javascript", "js", "typescript"):
        return analyse_javascript(code)
    elif lang == "html":
        return analyse_html(code)
    else:
        return {"issues": [], "metrics": {}, "summary": "Static analysis not supported for '" + lang + "'."}
