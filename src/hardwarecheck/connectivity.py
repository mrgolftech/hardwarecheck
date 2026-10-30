"""Read-only, assembly-aware 0-ohm resistor trace over a *flat* netlist.

No inference of signal polarity, pin direction, PCB routing, or unknown population.
This is a narrow topological helper, not ERC/DRC or electrical sign-off.
"""
from __future__ import annotations

import re
from collections import deque

_VALUE_KEYS = ("VALUE", "VAL", "RESISTANCE", "阻值")
_DNP_KEYS = ("DNP", "DNS", "DO_NOT_POPULATE", "DO NOT POPULATE", "不贴装")
_FIT_KEYS = ("FITTED", "POPULATED", "POPULATE", "MOUNTED", "装配", "贴装")
_DNP_YES = {"Y", "YES", "TRUE", "1", "DNP", "DNS", "NO FIT", "NOT FITTED", "不贴", "不装", "是"}
_DNP_NO = {"N", "NO", "FALSE", "0", "FITTED", "POPULATED", "装", "贴", "否"}
_FIT_YES = {"Y", "YES", "TRUE", "1", "FITTED", "POPULATED", "装", "贴", "是"}
_FIT_NO = {"N", "NO", "FALSE", "0", "DNP", "DNS", "NO FIT", "NOT FITTED", "不贴", "不装", "否"}
_UNKNOWN = {"", "-", "NA", "N/A", "UNKNOWN", "TBD", "?"}


def is_zero_ohm(value: str | None) -> bool:
    """Recognize explicit zero-ohm markings; never infer from refdes alone."""
    if value is None:
        return False
    cleaned = re.sub(r"\s+", "", str(value).upper().replace("Ω", "OHM").replace("Ω", "OHM"))
    return bool(re.fullmatch(r"(?:0+(?:\.0+)?(?:OHMS?)?|0R0*|0R)", cleaned))


def _attributes(item: dict | None) -> dict:
    if not item:
        return {}
    return {str(k).strip().upper(): str(v or "").strip()
            for k, v in item.get("attributes", {}).items() if k is not None}


def _value(attrs: dict) -> str | None:
    return next((attrs[k] for k in _VALUE_KEYS if k in attrs and attrs[k]), None)


def _population(attrs: dict, listed: bool) -> tuple[str, str]:
    """Return explicit_fitted / explicit_dnp / assumed_fitted / unknown / conflict."""
    if not listed:
        return "unknown", "no BOM row or BOM not provided"
    flags = []
    for key in _DNP_KEYS:
        if key in attrs:
            flag = attrs[key].upper()
            if flag in _UNKNOWN:
                continue
            if flag in _DNP_YES:
                flags.append("explicit_dnp")
            elif flag in _DNP_NO:
                flags.append("explicit_fitted")
            else:
                return "unknown", "unrecognized DNP field: " + key
    for key in _FIT_KEYS:
        if key in attrs:
            flag = attrs[key].upper()
            if flag in _UNKNOWN:
                continue
            if flag in _FIT_YES:
                flags.append("explicit_fitted")
            elif flag in _FIT_NO:
                flags.append("explicit_dnp")
            else:
                return "unknown", "unrecognized fitted field: " + key
    if len(set(flags)) > 1:
        return "conflict", "conflicting assembly fields"
    if flags:
        return flags[0], "explicit BOM population field"
    return "assumed_fitted", "BOM-listed; assembly state not explicitly confirmed"


def _resistor(refdes: str, part: dict) -> bool:
    return bool(re.fullmatch(r"R[0-9]+[A-Z]?", refdes, re.I)) or (
        "RES" in str(part.get("part_name") or "").upper()
    )


def zero_ohm_bridges(design: dict, bom: dict | None = None) -> dict:
    """Return candidates with object and source evidence, without merging nets."""
    bridges = []
    excluded = []
    warnings = []
    bom_items = bom["items"] if bom else {}
    for refdes in sorted(design["components"]):
        comp = design["components"][refdes]
        if not _resistor(refdes, comp):
            continue
        part_props = {str(k).upper(): str(v) for k, v in comp.get("properties", {}).items()}
        bom_item = bom_items.get(refdes)
        attrs = _attributes(bom_item)
        part_value = _value(part_props)
        bom_value = _value(attrs)
        values = [x for x in (part_value, bom_value) if x]
        if not values or not any(is_zero_ohm(x) for x in values):
            continue
        # A zero/nonzero mismatch must not silently convert into a bridge.
        if any(not is_zero_ohm(x) for x in values):
            warnings.append(f"{refdes}: conflicting resistance values from part list / BOM")
            excluded.append({"refdes": refdes, "reason": "resistance_value_conflict",
                             "values": {"part": part_value, "bom": bom_value}})
            continue
        pins = comp.get("pins", {})
        if len(pins) != 2 or len(set(pins.values())) != 2:
            warnings.append(f"{refdes}: cannot bridge: requires exactly two distinct pins/nets")
            excluded.append({"refdes": refdes, "reason": "not_two_distinct_pin_nets"})
            continue
        population, basis = _population(attrs, bom_item is not None)
        p1, p2 = sorted(pins, key=lambda p: (not str(p).isdigit(), int(p) if str(p).isdigit() else str(p)))
        edge = {
            "refdes": refdes,
            "pins": [{"pin": p1, "net": pins[p1]}, {"pin": p2, "net": pins[p2]}],
            "nets": [pins[p1], pins[p2]],
            "part_value": part_value,
            "bom_value": bom_value,
            "population": population,
            "population_basis": basis,
            "bom_row": bom_item["row"] if bom_item else None,
        }
        if population in {"explicit_dnp", "conflict"}:
            excluded.append({**edge, "reason": "not_fitted" if population == "explicit_dnp" else "population_conflict"})
        else:
            bridges.append(edge)
    return {"bridges": bridges, "excluded": excluded, "warnings": warnings}


def _walk(start: str, bridges: list[dict]) -> list[dict]:
    adjacency: dict[str, list[tuple[str, dict]]] = {}
    for bridge in bridges:
        left, right = bridge["nets"]
        adjacency.setdefault(left, []).append((right, bridge))
        adjacency.setdefault(right, []).append((left, bridge))
    seen = {start}
    q = deque([(start, [])])
    paths = []
    while q:
        net, path = q.popleft()
        for other, edge in sorted(adjacency.get(net, []), key=lambda item: (item[0], item[1]["refdes"])):
            if other in seen:
                continue
            seen.add(other)
            new_path = path + [{
                "refdes": edge["refdes"], "from_net": net, "to_net": other,
                "population": edge["population"], "pins": edge["pins"],
                "part_value": edge["part_value"], "bom_value": edge["bom_value"],
                "bom_row": edge["bom_row"],
            }]
            paths.append({"net": other, "hops": len(new_path), "path": new_path})
            q.append((other, new_path))
    return paths


def trace_zero_ohm(design: dict, start_net: str, bom: dict | None = None) -> dict:
    """Report confirmed (explicit) and possible (unconfirmed) paths separately."""
    if start_net not in design["nets"]:
        raise KeyError(f"Unknown network: {start_net}")
    scan = zero_ohm_bridges(design, bom)
    confirmed = [x for x in scan["bridges"] if x["population"] == "explicit_fitted"]
    # Unknown/BOM-listed state extends candidate paths, NOT electrically proven paths.
    certain_paths = _walk(start_net, confirmed)
    possible_paths = _walk(start_net, scan["bridges"])
    return {
        "schema_version": "0.3",
        "start_net": start_net,
        "confirmed_reachable": certain_paths,
        "possible_reachable": possible_paths,
        "bridges": scan["bridges"],
        "excluded_bridges": scan["excluded"],
        "warnings": scan["warnings"] + (bom["warnings"] if bom else []),
        "sources": design["sources"] + ([{"name": bom["source"]}] if bom else []),
        "limitations": [
            "Only explicit 0-ohm two-pin resistors; not jumpers, ferrites, switches or implicit short circuits",
            "BOM inclusion without an explicit fitted field is a candidate path, not verified assembly",
            "A flat netlist cannot validate hierarchy, pin direction, voltage, isolation, or signal polarity",
            "Confirmed means explicit BOM population evidence, not physical inspection",
        ],
    }
