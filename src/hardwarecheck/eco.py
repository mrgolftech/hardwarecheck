"""Deterministic revision comparison, not an electrical ECO risk assessment."""
from __future__ import annotations


def compare_designs(old: dict, new: dict) -> dict:
    old_nets, new_nets = old["nets"], new["nets"]
    old_set, new_set = set(old_nets), set(new_nets)
    modified = []
    for name in sorted(old_set & new_set):
        before = {(x["refdes"], x["pin"]) for x in old_nets[name]}
        after = {(x["refdes"], x["pin"]) for x in new_nets[name]}
        if before != after:
            modified.append({
                "net": name,
                "removed_pins": [list(p) for p in sorted(before-after)],
                "added_pins": [list(p) for p in sorted(after-before)]
            })
    old_parts, new_parts = set(old["components"]), set(new["components"])
    return {
        "schema_version": "0.1",
        "status": "STRUCTURAL_DIFF_ONLY",
        "added_components": sorted(new_parts-old_parts),
        "removed_components": sorted(old_parts-new_parts),
        "added_nets": sorted(new_set-old_set),
        "removed_nets": sorted(old_set-new_set),
        "modified_nets": modified,
        "warning": (
            "Renamed nets, pin-swaps, component renumbering and equivalent "
            "circuits are NOT semantically matched; verify with both revisions "
            "and datasheets before evaluating ECO risk."
        )
    }
