"""JSON-output CLI for hardware review Agent Skills."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .cadence import build_design, get_component, get_net, file_digest
from .bom import parse_bom_csv, compare_bom
from .rules import run_rules
from .report import validate_findings
from .pcb import summarize_pcb
from .datasheet import search_pdf
from .eco import compare_designs
from .connectivity import trace_zero_ohm
from .power import analyze_power_tree
from .review_catalog import query_checklist


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hardwarecheck", description="Read-only EDA review tools (prototype)")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("inspect", "component", "net", "bom-diff", "review"):
        x = sub.add_parser(command)
        x.add_argument("--netlist", required=True, help="pstxnet.dat path")
        x.add_argument("--parts", help="optional pstxprt.dat path")
        if command in ("bom-diff", "review"):
            x.add_argument("--bom", required=command == "bom-diff",
                           help="optional UTF-8 CSV BOM")
        if command in ("component", "net"):
            x.add_argument("name", help="reference designator or network name")
        x.add_argument("--output", help="JSON report path (no original input overwritten)")
    x = sub.add_parser("trace-zero")
    x.add_argument("--netlist", required=True)
    x.add_argument("--parts")
    x.add_argument("--bom", help="optional manufacturing-variant CSV BOM")
    x.add_argument("--net", required=True, help="existing starting net name")
    x = sub.add_parser("power-tree")
    x.add_argument("--netlist", required=True)
    x.add_argument("--parts")
    x.add_argument("--power-spec", help="optional reviewed power pin and load JSON mapping")
    x = sub.add_parser("checklist")
    x.add_argument("--category", help="EDA/POWER/PROTECTION/CLOCK/DIGITAL/HIGHSPEED/ANALOG/PCB/BOM/VERIFICATION")
    x = sub.add_parser("pdf-search")
    x.add_argument("--pdf", required=True)
    x.add_argument("--term", required=True)
    x.add_argument("--max-hits", type=int, default=12)
    x = sub.add_parser("pcb-summary")
    x.add_argument("--path", required=True)
    x = sub.add_parser("eco-diff")
    x.add_argument("--old-netlist", required=True)
    x.add_argument("--new-netlist", required=True)
    x = sub.add_parser("validate-findings")
    x.add_argument("--netlist", required=True)
    x.add_argument("--findings", required=True, help="JSON array or {findings: [...]}")
    return p


def execute(args: argparse.Namespace) -> dict:
    if args.command == "checklist":
        return query_checklist(args.category)
    if args.command == "power-tree":
        design = build_design(args.netlist, args.parts)
        spec = None
        if args.power_spec:
            path = Path(args.power_spec)
            if path.stat().st_size > 2_000_000:
                raise ValueError("power spec JSON exceeds 2 MB")
            spec = json.loads(path.read_text(encoding="utf-8-sig"))
        report = analyze_power_tree(design, spec)
        if args.power_spec:
            report["annotation_source"] = file_digest(args.power_spec)
        return report
    if args.command == "trace-zero":
        design = build_design(args.netlist, args.parts)
        bom = parse_bom_csv(args.bom) if args.bom else None
        return trace_zero_ohm(design, args.net, bom)
    if args.command == "pdf-search":
        return search_pdf(args.pdf, args.term, args.max_hits)
    if args.command == "pcb-summary":
        return summarize_pcb(args.path)
    if args.command == "eco-diff":
        return compare_designs(build_design(args.old_netlist), build_design(args.new_netlist))
    if args.command == "validate-findings":
        path = Path(args.findings)
        if path.stat().st_size > 5_000_000:
            raise ValueError("candidate findings JSON exceeds 5MB")
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        candidate = raw if isinstance(raw, list) else raw.get("findings") if isinstance(raw, dict) else None
        if not isinstance(candidate, list) or any(not isinstance(x, dict) for x in candidate):
            raise ValueError("Expected findings array of JSON objects")
        return validate_findings(build_design(args.netlist), candidate)
    design = build_design(args.netlist, args.parts)
    if args.command == "inspect":
        return {
            "schema_version": design["schema_version"],
            "components": len(design["components"]),
            "nets": len(design["nets"]),
            "connected_pins": sum(len(p) for p in design["nets"].values()),
            "sources": design["sources"],
            "warnings": design["warnings"],
            "limitations": design["limitations"]
        }
    if args.command == "component":
        return get_component(design, args.name)
    if args.command == "net":
        return get_net(design, args.name)
    if args.command == "bom-diff":
        return compare_bom(design, parse_bom_csv(args.bom))
    if args.command == "review":
        bom = parse_bom_csv(args.bom) if args.bom else None
        raw = run_rules(design, bom)
        validated = validate_findings(design, raw["findings"])
        return {
            "schema_version": "0.1",
            "design_sources": design["sources"],
            "rules_executed": raw["checks_run"],
            "status": raw["status"],
            "findings": validated,
            "warnings": raw["warnings"],
            "limitations": raw["limitations"],
            "disclaimer": "Not a replacement for human sign-off, ERC/DRC, simulation or test"
        }
    raise ValueError("Unrecognized command")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = execute(args)
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
        if getattr(args, "output", None):
            output = Path(args.output)
            if output.exists():
                raise ValueError("Output already exists; refusing to overwrite")
            if output.resolve() in {
                Path(args.netlist).resolve(),
                *([Path(args.parts).resolve()] if args.parts else [])
            }:
                raise ValueError("Refusing to overwrite input")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
