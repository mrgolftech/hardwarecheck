"""Bounded textual PDF search. It does NOT validate datasheet parameter meaning."""
from __future__ import annotations
from pathlib import Path


def search_pdf(path: str | Path, term: str, max_hits: int = 12,
               context_chars: int = 110) -> dict:
    if not term.strip() or len(term) > 128:
        raise ValueError("term must be 1..128 nonempty characters")
    if not 1 <= max_hits <= 100:
        raise ValueError("max_hits must be 1..100")
    file = Path(path)
    if file.suffix.lower() != ".pdf":
        raise ValueError("Expected a PDF datasheet")
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Optional dependency missing; pip install -e '.[pdf]'") from exc
    hits = []
    with fitz.open(str(file)) as doc:
        if doc.is_encrypted:
            raise ValueError("Encrypted PDF is not supported")
        pages_scanned = 0
        for index, page in enumerate(doc):
            pages_scanned += 1
            text = page.get_text("text", sort=True)
            start = 0
            lowered = text.casefold()
            token = term.casefold()
            while len(hits) < max_hits:
                found = lowered.find(token, start)
                if found == -1:
                    break
                snippet = text[max(0, found-context_chars):
                               min(len(text), found+len(term)+context_chars)]
                hits.append({"page": index+1, "snippet": snippet.strip()})
                start = found + len(term)
            if len(hits) >= max_hits:
                break
        return {
            "source": file.name, "query": term, "hits": hits,
            "pages_scanned": pages_scanned,
            "total_pages": len(doc),
            "truncated": len(hits) >= max_hits,
            "status": "TEXT_MATCH_ONLY",
            "warning": (
                "A text match is not a validated parameter. Check exact MPN, "
                "revision, table headers, min/typ/max, footnotes, units and test conditions. "
                "For scanned/timing-diagram PDF, render and confirm visually."
            )
        }
