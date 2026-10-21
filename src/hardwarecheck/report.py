"""Provenance checks for deterministic findings; no invented datasheet claims."""
from __future__ import annotations
from collections import Counter


def validate_findings(design: dict, findings: list[dict]) -> dict:
    accepted, quarantined = [], []
    for finding in findings:
        subject = finding.get("subject") or {}
        refdes = subject.get("refdes")
        net = subject.get("net")
        reasons = []
        if refdes and refdes not in design["components"]:
            # BOM-only rules may legitimately point at BOM refdes.
            if finding.get("rule_id") != "SCH-BOM-002":
                reasons.append("referenced component absent from netlist")
        if net and net not in design["nets"]:
            reasons.append("referenced net absent from netlist")
        for item in finding.get("evidence") or []:
            if item.get("kind") == "netlist":
                if item.get("net") and item["net"] not in design["nets"]:
                    reasons.append("netlist evidence names unknown network")
                if item.get("refdes") and item["refdes"] not in design["components"]:
                    reasons.append("netlist evidence names unknown component")
            if item.get("kind") == "datasheet":
                if not (item.get("mpn") and item.get("page") and item.get("source")):
                    reasons.append("datasheet evidence lacks model/page/source")
        if not finding.get("rule_id") or not finding.get("status"):
            reasons.append("finding has no rule_id/status")
        if reasons:
            quarantined.append({"finding": finding, "reasons": sorted(set(reasons))})
        else:
            accepted.append(finding)
    return {
        "accepted": accepted, "quarantined": quarantined,
        "counts_by_status": dict(Counter(x["status"] for x in accepted)),
        "note": "Structural validation only; electrical correctness needs separate review."
    }
