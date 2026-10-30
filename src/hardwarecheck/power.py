"""Conservative flat-netlist power rail inventory and annotation-driven power tree.

No part-model, pin-function, current, voltage or source direction is inferred from a
net name.  The optional manifest expresses *user-supplied, unverified* design
claims, checked against existing component/pin/network structural facts.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict

_GROUND = re.compile(r"^(?:GND|AGND|DGND|PGND|SGND|VSS|VSSA|VSSD|EARTH)(?:$|[_\d])", re.I)
_POWER = re.compile(
    r"^(?:[+-]?\d+(?:[P.]\d+)?V(?:\d+)?(?:$|[_-])|"
    r"(?:VDD|VCC|VBAT|VSYS|VIN|VOUT|PWR|VREF|AVDD|DVDD|PVDD|VCORE|VIO|VAA)(?:$|[_-]))",
    re.I,
)


def candidate_rails(design: dict) -> list[dict]:
    """Net name hints only; includes provenance but no 'true power rail' assertion."""
    result = []
    for name, members in sorted(design["nets"].items()):
        if _GROUND.match(name.strip()):
            continue
        if not _POWER.match(name.strip()):
            continue
        result.append({
            "net": name, "hint": "name_pattern_only",
            "connected_pins": [{"refdes": x["refdes"], "pin": x["pin"]} for x in members],
            "member_count": len(members),
        })
    return result


def _number(obj: dict, key: str, path: str, errors: list[str],
            *, positive: bool = False) -> float | None:
    if key not in obj or obj[key] is None:
        return None
    v = obj[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or (positive and v <= 0):
        errors.append(f"{path}.{key}: must be a finite {'positive' if positive else 'numeric'} value")
        return None
    return float(v)


def _connected(design: dict, obj: dict, path: str, errors: list[str]) -> tuple[str, str, str] | None:
    ref, pin = obj.get("refdes"), obj.get("pin")
    if not isinstance(ref, str) or not isinstance(pin, str) or not ref or not pin:
        errors.append(f"{path}: refdes and pin must be nonempty strings")
        return None
    component = design["components"].get(ref)
    if component is None:
        errors.append(f"{path}: component {ref!r} not in netlist")
        return None
    net = component["pins"].get(pin)
    if net is None:
        errors.append(f"{path}: {ref} pin {pin} not connected in this netlist")
        return None
    return ref, pin, net


def _issue(code: str, subject: str, details: str) -> dict:
    return {"check_id": code, "status": "SUSPECTED", "subject": subject, "reason": details,
            "evidence_kind": "annotated_values_plus_netlist_mapping"}


def _cycles(converters: list[dict]) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for c in converters:
        graph[c["input_net"]].add(c["output_net"])
    colors: dict[str, int] = {}
    stack: list[str] = []
    loops: set[tuple[str, ...]] = set()

    def visit(n: str) -> None:
        colors[n] = 1
        stack.append(n)
        for target in sorted(graph[n]):
            if colors.get(target) == 1:
                i = stack.index(target)
                loops.add(tuple(stack[i:] + [target]))
            elif colors.get(target, 0) == 0:
                visit(target)
        stack.pop()
        colors[n] = 2

    for start in sorted(graph):
        if colors.get(start, 0) == 0:
            visit(start)
    return [list(x) for x in sorted(loops)]


def analyze_power_tree(design: dict, spec: dict | None = None) -> dict:
    """Inspect rail candidates; directed graph only from explicit validated pin maps."""
    base = {
        "schema_version": "0.4",
        "sources": design["sources"],
        "candidate_rails": candidate_rails(design),
        "input_warnings": design["warnings"],
        "limitations": [
            "Power net names are candidate hints, never pin-function proof.",
            "Direction, voltage, load and limits originate only from explicit review annotations.",
            "Annotated values are unverified design claims, not independently validated datasheet ratings.",
            "The analysis does not cross DNP/0-ohm, ferrites, diodes, FETs, power muxes or internal silicon paths.",
            "No automatic sequencing, dropout-versus-temperature, ripple, efficiency, thermal, SI/PI or PCB geometry sign-off.",
            "Load budgets contain only explicitly annotated direct loads; downstream converter input demand is not modeled.",
            "Flat Cadence parser has no verified page hierarchy or full hidden-pin coverage.",
        ],
    }
    if spec is None:
        return {**base, "mode": "candidate_only", "converters": [], "loads": [],
                "declared_sources": [], "rails": [], "findings": [],
                "annotation_errors": [], "unchecked": [
                    "power direction", "nominal rail voltage", "converter input limits",
                    "load current budget", "voltage compatibility", "sequencing",
                    "feedback/inductor/capacitance", "thermal and transient behavior",
                ]}

    if not isinstance(spec, dict) or str(spec.get("schema_version")) != "0.1":
        raise ValueError("power spec must be JSON object with schema_version '0.1'")
    errors: list[str] = []
    findings: list[dict] = []
    converters: list[dict] = []
    sources: list[dict] = []
    loads: list[dict] = []
    for key in ("sources", "converters", "loads"):
        if not isinstance(spec.get(key, []), list) or any(not isinstance(x, dict) for x in spec.get(key, [])):
            raise ValueError(f"power spec {key} must be an array of objects")

    # Declare external power sources; known net identity, but unverified physical source.
    nominal_by_rail: dict[str, list[dict]] = defaultdict(list)
    for idx, row in enumerate(spec.get("sources", [])):
        path = f"sources[{idx}]"
        net = row.get("net")
        if not isinstance(net, str) or net not in design["nets"]:
            errors.append(f"{path}.net: network {net!r} not in netlist")
            continue
        voltage = _number(row, "voltage_v", path, errors, positive=True)
        if voltage is None:
            errors.append(f"{path}: voltage_v is required")
            continue
        source = {"net": net, "voltage_v": voltage, "kind": "declared_external_source"}
        sources.append(source)
        nominal_by_rail[net].append({"source": path, "voltage_v": voltage})

    for idx, row in enumerate(spec.get("converters", [])):
        path = f"converters[{idx}]"
        ref = row.get("refdes")
        input_pin, output_pin = row.get("input_pin"), row.get("output_pin")
        if not all(isinstance(x, str) and x for x in (ref, input_pin, output_pin)):
            errors.append(f"{path}: refdes/input_pin/output_pin must be nonempty strings")
            continue
        a = _connected(design, {"refdes": ref, "pin": input_pin}, path + ".input", errors)
        b = _connected(design, {"refdes": ref, "pin": output_pin}, path + ".output", errors)
        if a is None or b is None:
            continue
        if a[2] == b[2]:
            errors.append(f"{path}: input and output map to same net {a[2]!r}; no directed conversion edge")
            continue
        out_v = _number(row, "output_voltage_v", path, errors, positive=True)
        max_a = _number(row, "max_output_current_a", path, errors, positive=True)
        min_v = _number(row, "min_input_v", path, errors, positive=True)
        max_v = _number(row, "max_input_v", path, errors, positive=True)
        dropout = _number(row, "dropout_v", path, errors)
        if min_v is not None and max_v is not None and min_v > max_v:
            errors.append(f"{path}: min_input_v exceeds max_input_v")
            continue
        if dropout is not None and dropout < 0:
            errors.append(f"{path}: dropout_v must be >= 0")
            continue
        # No guessed direction: this edge is specifically declared and pin-mapped.
        converter = {
            "refdes": ref, "input_pin": input_pin, "output_pin": output_pin,
            "input_net": a[2], "output_net": b[2],
            "kind": str(row.get("kind", "unspecified")).upper(),
            "output_voltage_v": out_v,
            "max_output_current_a": max_a,
            "min_input_v": min_v, "max_input_v": max_v, "dropout_v": dropout,
            "basis": "explicit_annotation_verified_against_netlist_pin_connection",
        }
        converters.append(converter)
        if out_v is not None:
            nominal_by_rail[b[2]].append({"source": path, "voltage_v": out_v})

    for idx, row in enumerate(spec.get("loads", [])):
        path = f"loads[{idx}]"
        obj = _connected(design, row, path, errors)
        if obj is None:
            continue
        current = _number(row, "max_current_a", path, errors, positive=True)
        lo = _number(row, "min_voltage_v", path, errors, positive=True)
        hi = _number(row, "max_voltage_v", path, errors, positive=True)
        if lo is not None and hi is not None and lo > hi:
            errors.append(f"{path}: min_voltage_v exceeds max_voltage_v")
            continue
        loads.append({"refdes": obj[0], "pin": obj[1], "net": obj[2],
                      "max_current_a": current,
                      "min_voltage_v": lo, "max_voltage_v": hi})

    voltages: dict[str, float] = {}
    for rail, entries in sorted(nominal_by_rail.items()):
        vals = {entry["voltage_v"] for entry in entries}
        if len(vals) > 1:
            findings.append(_issue("PWR-VOLT-001", rail,
                                   f"conflicting declared voltages: {sorted(vals)} V"))
        else:
            voltages[rail] = next(iter(vals))
    for c in converters:
        vin = voltages.get(c["input_net"])
        if vin is not None:
            if c["min_input_v"] is not None and vin < c["min_input_v"]:
                findings.append(_issue("PWR-VIN-001", c["refdes"],
                    f"declared input {vin:g} V below annotated min {c['min_input_v']:g} V"))
            if c["max_input_v"] is not None and vin > c["max_input_v"]:
                findings.append(_issue("PWR-VIN-001", c["refdes"],
                    f"declared input {vin:g} V above annotated max {c['max_input_v']:g} V"))
            if c["kind"] == "LDO" and c["dropout_v"] is not None and c["output_voltage_v"] is not None:
                headroom = vin - c["output_voltage_v"]
                if headroom < c["dropout_v"]:
                    findings.append(_issue("PWR-LDO-001", c["refdes"],
                        f"annotated headroom {headroom:g} V < dropout {c['dropout_v']:g} V (check Iload/temperature)"))
    for load in loads:
        v = voltages.get(load["net"])
        if v is not None and (
            (load["min_voltage_v"] is not None and v < load["min_voltage_v"]) or
            (load["max_voltage_v"] is not None and v > load["max_voltage_v"])
        ):
            findings.append(_issue("PWR-LOAD-001", f"{load['refdes']}.{load['pin']}",
                                  f"declared rail voltage {v:g} V outside annotated load range"))
    rail_loads: dict[str, list[dict]] = defaultdict(list)
    for load in loads:
        rail_loads[load["net"]].append(load)
    rails: list[dict] = []
    all_rails = set(nominal_by_rail) | set(rail_loads)
    for c in converters:
        all_rails.add(c["input_net"])
        all_rails.add(c["output_net"])
    for net in sorted(all_rails):
        own = rail_loads.get(net, [])
        total = sum(x["max_current_a"] for x in own if x["max_current_a"] is not None)
        missing = [x["refdes"] + "." + x["pin"] for x in own if x["max_current_a"] is None]
        downstream = [c["refdes"] for c in converters if c["input_net"] == net]
        drivers = [c for c in converters if c["output_net"] == net]
        if len(drivers) + sum(x["net"] == net for x in sources) > 1:
            findings.append(_issue("PWR-SOURCE-001", net,
                                   "multiple annotated sources/drivers; verify power OR-ing and protection"))
        for c in drivers:
            if c["max_output_current_a"] is not None and total > c["max_output_current_a"] + 1e-12:
                findings.append(_issue("PWR-CURRENT-001", net,
                    f"direct load annotated max sum {total:g} A exceeds {c['refdes']} capacity {c['max_output_current_a']:g} A; concurrency/thermal unverified"))
        rails.append({
            "net": net, "declared_voltage_v": voltages.get(net),
            "declared_direct_load_current_sum_a": round(total, 9),
            "missing_load_currents": missing,
            "downstream_converter_inputs_unbudgeted": downstream,
            "drivers": [{"refdes": c["refdes"], "max_output_current_a": c["max_output_current_a"]} for c in drivers],
            "load_count": len(own),
            "note": "partial sum only; cannot mark current budget PASS",
        })

    for cycle in _cycles(converters):
        findings.append(_issue("PWR-CYCLE-001", " -> ".join(cycle),
                               "annotated converter dependency cycle; verify topology and operating modes"))
    return {
        **base,
        "mode": "annotated_power_tree",
        "declared_sources": sources,
        "converters": converters,
        "loads": loads,
        "rails": rails,
        "findings": findings,
        "annotation_errors": errors,
        "unchecked": [
            "automatic pin function/direction verification", "true load coverage",
            "efficiency and upstream current", "peak/inrush current", "regulator output tolerance/ripple",
            "sequencing and EN/PGOOD timing", "feedback compensation/stability",
            "DNP/0-ohm/ferrite/diode/ideal-diode switch conduction",
            "thermal/derating/PCB layout",
        ],
        "note": "SUSPECTED flags compare unverified annotations; they are not design sign-off or measured faults.",
    }
