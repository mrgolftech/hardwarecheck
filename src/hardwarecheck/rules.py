"""Small deterministic rule pilot; never asserts whole-board validity."""
from __future__ import annotations
from .bom import compare_bom


def _finding(rule: str, status: str, severity: str,
             subject: dict, statement: str, evidence: list[dict]) -> dict:
    return {
        "rule_id": rule, "rule_version": "0.1",
        "status": status, "severity": severity,
        "subject": subject, "statement": statement,
        "evidence": evidence, "reviewer_decision": "unreviewed"
    }


def run_rules(design: dict, bom: dict | None = None) -> dict:
    findings = []
    for conflict in design["conflicts"]:
        findings.append(_finding(
            "SCH-NET-001", "FAIL", "high",
            {"refdes": conflict["refdes"], "pin": conflict["pin"]},
            "Same physical refdes/pin appears on different flat networks; "
            "could also be invalid source data or unsupported netlist semantics.",
            [{"kind": "netlist", "net": conflict["net_a"]},
             {"kind": "netlist", "net": conflict["net_b"]}]
        ))
    for name, members in design["nets"].items():
        if len(members) == 1:
            findings.append(_finding(
                "SCH-NET-002", "SUSPECTED", "low",
                {"net": name},
                "Single-member net needs review; legitimate test/NC/unused nets exist.",
                [{"kind": "netlist", "net": name, "nodes": members}]
            ))
    if bom is not None:
        diff = compare_bom(design, bom)
        for refdes in diff["not_in_bom"]:
            findings.append(_finding(
                "SCH-BOM-001", "NEEDS_REVIEW", "medium",
                {"refdes": refdes}, "Netlist refdes absent from this BOM variant; "
                "check DNP, unconnected and multi-section components.",
                [{"kind": "netlist", "refdes": refdes},
                 {"kind": "bom", "source": bom["source"], "present": False}]
            ))
        for refdes in diff["not_in_netlist"]:
            findings.append(_finding(
                "SCH-BOM-002", "NEEDS_REVIEW", "medium",
                {"refdes": refdes}, "BOM refdes absent from this flat netlist; "
                "may be mechanical or unconnected.",
                [{"kind": "bom", "refdes": refdes, "source": bom["source"]}]
            ))
    return {
        "schema_version": "0.1", "checks_run": [
            "SCH-NET-001", "SCH-NET-002",
            * (["SCH-BOM-001", "SCH-BOM-002"] if bom is not None else [])
        ],
        "status": "review_required" if findings else "no_findings_in_executed_rules",
        "findings": findings,
        "limitations": design["limitations"],
        "warnings": design["warnings"] + (bom["warnings"] if bom else [])
    }
