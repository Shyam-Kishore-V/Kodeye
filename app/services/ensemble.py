"""
Ensemble Analysis Service
Combines static analysis issue counts with LLM review sentiment
to produce a weighted quality score and letter grade.
"""

from typing import Any

_SEVERITY_WEIGHT = {"error": 3, "warning": 2, "info": 1}
_TOOL_WEIGHT     = {"Bandit": 1.5, "Pylint": 1.2, "AST": 1.0, "JSLint": 1.0, "HTMLLint": 1.0}

_POSITIVE_KW = ["well written", "clean", "good", "excellent", "properly", "correct",
                "solid", "no issues", "great", "well structured"]
_NEGATIVE_KW = ["bug", "issue", "problem", "error", "vulnerability", "insecure",
                "refactor", "improve", "missing", "incorrect", "bad", "risk",
                "concern", "deprecated", "dangerous", "injection"]


def ensemble_score(static_result: dict, llm_review: str) -> dict:
    issues  = static_result.get("issues", [])
    metrics = static_result.get("metrics", {})

    # Static penalty score
    penalty = sum(
        _SEVERITY_WEIGHT.get(i.get("severity", "info"), 1) * _TOOL_WEIGHT.get(i.get("tool", "AST"), 1.0)
        for i in issues
    )
    static_score = max(0.0, 100.0 - min(penalty, 100.0))

    # LLM sentiment score
    text = llm_review.lower()
    pos  = sum(text.count(w) for w in _POSITIVE_KW)
    neg  = sum(text.count(w) for w in _NEGATIVE_KW)
    llm_score = round(pos / (pos + neg) * 100, 1) if (pos + neg) else 50.0

    ensemble = round(0.6 * static_score + 0.4 * llm_score, 1)

    if ensemble >= 85:
        grade, label = "A", "Excellent"
    elif ensemble >= 70:
        grade, label = "B", "Good"
    elif ensemble >= 55:
        grade, label = "C", "Fair"
    elif ensemble >= 40:
        grade, label = "D", "Needs Work"
    else:
        grade, label = "F", "Poor"

    security = [i for i in issues if i.get("tool") == "Bandit"]
    style    = [i for i in issues if i.get("tool") in ("Pylint", "JSLint", "HTMLLint")]
    logic    = [i for i in issues if i.get("tool") == "AST"]
    top5     = sorted(issues, key=lambda i: _SEVERITY_WEIGHT.get(i.get("severity", "info"), 1), reverse=True)[:5]

    return {
        "ensemble_score": ensemble,
        "static_score":   round(static_score, 1),
        "llm_score":      llm_score,
        "grade":          grade,
        "label":          label,
        "breakdown": {
            "security": len(security),
            "style":    len(style),
            "logic":    len(logic),
            "total":    len(issues),
        },
        "metrics":    metrics,
        "top_issues": top5,
    }
