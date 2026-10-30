"""Versioned engineering checklist catalog; entries != executable ERC rules."""
from __future__ import annotations

import json
from pathlib import Path


def query_checklist(category: str | None = None) -> dict:
    path = Path(__file__).resolve().parents[2] / "rules" / "review_matrix.json"
    if not path.is_file():
        raise ValueError("review_matrix.json not found; use the hardwarecheck repository in editable mode")
    data = json.loads(path.read_text(encoding="utf-8"))
    checks = data["checks"]
    if category:
        category = category.upper()
        choices = sorted({x["category"] for x in checks})
        if category not in choices:
            raise ValueError(f"unknown category {category!r}; valid: {choices}")
        checks = [x for x in checks if x["category"] == category]
    return {
        "catalog_version": data["catalog_version"],
        "category": category or "ALL",
        "count": len(checks),
        "checks": checks,
        "warning": "Checklist != execution: guided and partial_tool entries are NOT deterministic PASS/FAIL rules.",
    }
