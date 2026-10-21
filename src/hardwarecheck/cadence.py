"""Conservative subset parser for OrCAD/Allegro Capture expanded netlists.

Handles NET_NAME/NODE_NAME from pstxnet.dat and basic PART_NAME in pstxprt.dat.
Does NOT infer symbol graphics, page coordinates, hidden pins, pin electrical
types or complete physical/logic pin mapping from the flat netlist.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

_NODE = re.compile(r"^NODE_NAME\s+(\S+)\s+(\S+)", re.IGNORECASE)
_QUOTED = re.compile(r"^'([^']*)'")
_PART = re.compile(r"^([^\s;]+)\s+'([^']*)'")
_PROPERTY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'([^']*)'")
_SAFE = re.compile(r"^[A-Za-z0-9_.$/#@+~:()\-]+$")


def read_eda_text(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unsupported text encoding: expected UTF-8 or GB18030")


def file_digest(path: str | Path) -> dict:
    file = Path(path)
    return {"name": file.name, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}


def parse_pstxnet(path: str | Path) -> tuple[dict, list[str]]:
    """Return net -> member pin records, plus warnings.

    Fails closed if no valid NET_NAME blocks are present.
    """
    text = read_eda_text(path)
    if not re.search(r"\bFILE_TYPE\s*=\s*EXPANDEDNETLIST\b", text, re.I):
        raise ValueError("Not a supported pstxnet.dat EXPANDEDNETLIST")
    nets: dict[str, list[dict]] = {}
    warnings: list[str] = []
    current: str | None = None
    want_name = False
    for line_number, source in enumerate(text.splitlines(), 1):
        line = source.strip()
        if line.upper() == "NET_NAME":
            want_name = True
            current = None
            continue
        if want_name:
            if not line or line.startswith("{"):
                continue
            m = _QUOTED.match(line)
            if m is None or not m.group(1):
                warnings.append(f"net name unreadable at line {line_number}")
                want_name = False
                continue
            current = m.group(1)
            if current in nets:
                warnings.append(f"repeated NET_NAME {current!r} at line {line_number}")
            nets.setdefault(current, [])
            want_name = False
            continue
        if line.upper().startswith("NODE_NAME"):
            m = _NODE.match(line)
            if m is None or current is None:
                warnings.append(f"unbound or malformed NODE_NAME at line {line_number}")
                continue
            refdes, pin = m.group(1), m.group(2).rstrip(";")
            if not refdes or not pin:
                warnings.append(f"empty refdes/pin at line {line_number}")
                continue
            nets[current].append({"refdes": refdes, "pin": pin, "line": line_number})
    if not nets:
        raise ValueError("No readable NET_NAME sections; netlist schema not supported")
    return nets, warnings


def parse_pstxprt(path: str | Path) -> tuple[dict, list[str]]:
    """Read basic part blocks; no guarantee of resolving all Cadence properties."""
    text = read_eda_text(path)
    if not re.search(r"\bFILE_TYPE\s*=\s*EXPANDEDPARTLIST\b", text, re.I):
        raise ValueError("Not a supported pstxprt.dat EXPANDEDPARTLIST")
    parts: dict[str, dict] = {}
    warnings: list[str] = []
    expect_part = False
    current: str | None = None
    for line_number, source in enumerate(text.splitlines(), 1):
        line = source.strip()
        if line.upper() == "PART_NAME":
            expect_part = True
            current = None
            continue
        if expect_part:
            if not line or line.startswith("{"):
                continue
            m = _PART.match(line)
            if m is None:
                warnings.append(f"unreadable PART_NAME at line {line_number}")
            else:
                current = m.group(1)
                parts[current] = {
                    "part_name": m.group(2),
                    "properties": {},
                    "line": line_number
                }
            expect_part = False
            continue
        if current and not line.upper().startswith(("SECTION_NUMBER", "END.")):
            m = _PROPERTY.match(line)
            if m:
                # Only retain simple property values; never infer pin mapping.
                parts[current]["properties"].setdefault(m.group(1).upper(), m.group(2))
    if not parts:
        warnings.append("no readable PART_NAME records")
    return parts, warnings


def build_design(netlist: str | Path, parts: str | Path | None = None) -> dict:
    nets, warnings = parse_pstxnet(netlist)
    part_data, part_warn = parse_pstxprt(parts) if parts else ({}, [])
    warnings.extend(part_warn)
    components: dict[str, dict] = {}
    conflicts: list[dict] = []
    for refdes, part in part_data.items():
        components[refdes] = {
            "refdes": refdes, "part_name": part["part_name"],
            "properties": part["properties"], "pins": {}
        }
    for net_name, pins in nets.items():
        for node in pins:
            refdes, pin = node["refdes"], node["pin"]
            item = components.setdefault(refdes, {
                "refdes": refdes, "part_name": None, "properties": {}, "pins": {}
            })
            prior = item["pins"].get(pin)
            if prior is not None and prior != net_name:
                conflicts.append({
                    "refdes": refdes, "pin": pin, "net_a": prior, "net_b": net_name
                })
            item["pins"][pin] = net_name
    return {
        "schema_version": "0.1",
        "sources": [file_digest(netlist)] + ([file_digest(parts)] if parts else []),
        "components": components,
        "nets": nets,
        "warnings": warnings,
        "conflicts": conflicts,
        "capabilities": [
            "flat_net_connectivity", "basic_part_names" if parts else "netlist_only"
        ],
        "limitations": [
            "No validated schematic page/graphics coordinates",
            "No verified electrical pin types or hidden-pin completeness",
            "No guaranteed multi-section or hierarchical alias reconstruction",
            "No design-level electrical correctness inference"
        ]
    }


def get_component(design: dict, refdes: str) -> dict:
    value = design["components"].get(refdes)
    if value is None:
        raise KeyError(f"Unknown refdes: {refdes}")
    neighbors = {}
    for pin, net in value["pins"].items():
        neighbors[pin] = {
            "net": net,
            "connected": [
                {"refdes": n["refdes"], "pin": n["pin"]}
                for n in design["nets"][net]
                if n["refdes"] != refdes or n["pin"] != pin
            ]
        }
    return {**value, "neighbors": neighbors}


def get_net(design: dict, name: str) -> dict:
    if name not in design["nets"]:
        raise KeyError(f"Unknown network: {name}")
    return {"name": name, "pins": design["nets"][name]}
