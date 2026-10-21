"""JSON-output CLI for hardware review Agent Skills."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .cadence import build_design, get_component, get_net
from .bom import parse_bom_csv, compare_bom
from .rules import run_rules
from .report import validate_findings
from .pcb import summarize_pcb
from .datasheet import search_pdf


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
    x = sub.add_parser("pdf-search")
    x.add_argument("--pdf", required=True)
    x.add_argument("--term", required=True)
    x.add_argument("--max-hits", type=int, default=12)
    x = sub.add_parser("pcb-summary")
    x.add_argument("--path", required=True)
    return p


def execute(args: argparse.Namespace) -> dict:
    if args.command == "pdf-search":
        return search_pdf(args.pdf, args.term, args.max_hits)
    if args.command == "pcb-summary":
        return summarize_pcb(args.path)
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
