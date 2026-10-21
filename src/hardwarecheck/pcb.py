"""PCB data inventory only: no geometric rule checking in v0.1."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


def summarize_pcb(path: str | Path) -> dict:
    file = Path(path)
    if file.suffix.lower() == ".brd":
        raise ValueError("Binary Allegro .brd unsupported: export IPC-2581 or SKILL JSON")
    if file.stat().st_size > 50_000_000:
        raise ValueError("PCB export exceeds v0.1 50MB inventory limit")
    if file.suffix.lower() == ".json":
        data = json.loads(file.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("PCB JSON root must be an object")
        return {
            "source": file.name, "format": "json-unverified",
            "top_level_keys": sorted(data.keys()),
            "counts": {
                k: len(v) for k, v in data.items()
                if isinstance(v, (list, dict))
            },
            "capability": "inventory_only",
            "warning": "Not a normalized layout model; no geometric/ERC/DRC result generated"
        }
    if file.suffix.lower() in {".xml", ".ipc2581"}:
        # Avoid handling custom DTD/external XML entities. The stdlib parser
        # does not fetch external resources, but disallow declarations anyway.
        raw = file.read_bytes()
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ValueError("XML with DOCTYPE/ENTITY declarations not allowed")
        root = ET.fromstring(raw)
        counts = Counter(node.tag.rsplit("}", 1)[-1] for node in root.iter())
        return {
            "source": file.name, "format": "xml-unverified-ipc2581",
            "root_tag": root.tag.rsplit("}", 1)[-1],
            "tag_counts": dict(counts.most_common(35)),
            "capability": "inventory_only",
            "warning": "XML syntax and tags inspected only; no IPC-2581 geometry or connectivity validation"
        }
    raise ValueError("PCB input must be SKILL JSON, IPC-2581 XML or .ipc2581")
