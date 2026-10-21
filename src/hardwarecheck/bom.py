"""CSV BOM adapter. Excel can be exported as CSV; XLSX is not yet implemented."""
from __future__ import annotations
import csv
import re
from pathlib import Path

REF_KEYS = ("refdes", "reference", "references", "designator", "位号", "ref")


def parse_bom_csv(path: str | Path) -> dict:
    file = Path(path)
    if file.suffix.lower() != ".csv":
        raise ValueError("Only BOM CSV is supported in v0.1; export XLSX as UTF-8 CSV")
    text = file.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    fields = reader.fieldnames or []
    match = next((f for f in fields if f.strip().lower() in REF_KEYS), None)
    if not match:
        raise ValueError(f"BOM is missing refdes column; available columns: {fields}")
    items = {}
    warnings = []
    for row_number, row in enumerate(reader, 2):
        refs = re.split(r"[,;\s]+", (row.get(match) or "").strip())
        for refdes in (r for r in refs if r):
            if refdes in items:
                warnings.append(f"duplicated BOM reference {refdes} at row {row_number}")
                continue
            items[refdes] = {
                "refdes": refdes,
                "row": row_number,
                "attributes": {k: v for k, v in row.items() if k is not None}
            }
    return {"items": items, "warnings": warnings, "source": file.name}


def compare_bom(design: dict, bom: dict) -> dict:
    schematic_refs = set(design["components"])
    bom_refs = set(bom["items"])
    return {
        "matched": sorted(schematic_refs & bom_refs),
        "not_in_bom": sorted(schematic_refs - bom_refs),
        "not_in_netlist": sorted(bom_refs - schematic_refs),
        "note": (
            "These are inventory differences, NOT verified defects. "
            "DNP, variant, mechanical, unconnected and multi-section parts require review."
        )
    }
