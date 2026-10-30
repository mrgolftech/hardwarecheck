---
name: hardware-design-review
description: Review OrCAD Capture pstxnet.dat/pstxprt.dat netlists, BOM CSV, datasheets and Allegro exports. Use for hardware schematic review, UART/SBUS or other interface debugging, 0-ohm link tracing, DNP variants, evidence-backed electrical risk reports. Do not claim full ERC/DRC or unverified PCB analysis.
---

# Hardware Design Review — Codex entry skill

Use this skill when the user requests a hardware-design audit, schematic/netlist interpretation, pin-to-net tracing, BOM cross-check, datasheet-based interface review, or a review report. This is **read-only**. Existing specialist workflows live in sibling `schematic-review`, `bom-review`, `datasheet-review`, `pcb-review` and `review-report` skills; follow their procedures as needed. Do not assume all agent runtimes support nested skill invocation: read these files directly when needed.

## 0. Data safety and scope

- Check data classification and model authorization before processing company/customer files. The repository is **public**; never commit real designs, private BOMs, internal rules, datasheets, findings or credentials.
- Local Python CLI does not call network APIs. Codex *may* transmit tool output to its configured model; use only approved execution/model environments.
- Never edit input EDA sources; never infer true electrical behavior from names alone; do not promote unconfirmed findings to validated defects.
- Current parser supports only a conservative **flat** OrCAD `EXPANDEDNETLIST` subset. If format unrecognized, stop and request an approved export, not an invented interpretation.

## 1. Inventory + input validation (always)

1. Identify netlist `pstxnet.dat`, optional parts `pstxprt.dat`, BOM **CSV**, relevant PDFs, requirements, and optional Allegro **export** files.
2. Record missing input types and which review categories they block.
3. From repository root install once: `python -m pip install -e .`; use `python -m hardwarecheck` commands below (Windows PowerShell supported).
4. Run `inspect` first. Capture SHA-256 sources, parser warnings, counts and limitations. If critical pin/net ambiguity is detected, **quarantine affected circuit analysis** until the original schematic is checked.
5. Validate representative power, ground, interface, cross-page and multi-section pins against original exported data. A CLI parse alone is not a guarantee of a real OrCAD project.

```powershell
python -m hardwarecheck inspect --netlist "C:\Approved\pstxnet.dat" --parts "C:\Approved\pstxprt.dat"
python -m hardwarecheck component --netlist "C:\Approved\pstxnet.dat" --parts "C:\Approved\pstxprt.dat" U1
python -m hardwarecheck net --netlist "C:\Approved\pstxnet.dat" UART_TX
```

## 2. Deterministic checks + 0-ohm trace

- Run `review` with available BOM; current four baseline rules are **not** a full circuit inspection.
- If the task mentions 0-ohm links, strapping, DNP, UART/SBUS or signal continuity, use `trace-zero` from the starting **net**. Read `references/connectivity.md` for interpretation.
- `confirmed_reachable` uses explicitly fitted zero-ohm resistors **according to BOM fields**. `possible_reachable` also includes resistors listed without explicit population status or without a BOM. A path in `possible_reachable` is **not** proof that signal is physically connected.
- A resistor marked DNP is excluded; contradictory resistance and assembly values are quarantined.
- The tool does **not** traverse other device internals, ferrites, jumpers, MOSFETs, links or PCB copper shorts; reason about those separately using verified evidence.
- When BOM is a manufacturing variant, record its revision and interpretation. When only a purchasing BOM exists, flag the population assumption.

```powershell
python -m hardwarecheck review --netlist "C:\Approved\pstxnet.dat" --parts "C:\Approved\pstxprt.dat" --bom "C:\Approved\bom.csv"
python -m hardwarecheck trace-zero --netlist "C:\Approved\pstxnet.dat" --parts "C:\Approved\pstxprt.dat" --bom "C:\Approved\bom.csv" --net UART_TX
```

## 3. Engineering interpretation

For each relevant circuit: identify nets/components and primary purpose, then examine electrical constraints:

- **Power**: topology, operating rails, enable/reset sequence, regulator feedback, limits and likely error modes.
- **Interfaces**: direction, levels, inversion, timing, termination, pull-up/pull-down, ESD, isolation; e.g. UART vs SBUS requires checking polarity/format and actual transceiver topology, not assuming the name implies conversion.
- **Clocks/reset/boot**: crystal/load requirements, reset pin types, POR, strap and sequencing assumptions.
- **BOM/variants**: resistors, footprint, model identity, fitted/DNP conditions.
- **PCB**: only if exported geometry/stackup fields are available and separately validated. Existing `pcb-summary` only inventories export data, **not** geometric DRC or SI/PI checks.

Read `references/electrical-review.md` for review categories, applicability gates and evidence handling. Use `pdf-search` only to locate relevant datasheet passages. Min/typ/max, units, operating conditions, part revisions, and page numbers require direct validation; PDF keyword hits cannot prove an electrical claim.

## 4. Findings and report gate

Write candidate findings with `rule_id`, status, severity, subject, evidence and statement; validate with `validate-findings`. Structural acceptance **does not** authenticate datasheet quotations or the engineering conclusion. Read `references/reporting.md` and use `assets/report-template.md`.

Use one status per executed rule: `PASS` (that rule only), `FAIL` (structurally substantiated breach), `SUSPECTED`, `NEEDS_REVIEW`, `INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE` or `ERROR`. Also separately track **not executed** checks, rather than inventing PASS states.

Always provide: scope, input/hash/variant, parsing exceptions, inspected circuits and rules, evidence-backed findings with actual refdes/pin/net/datasheet references, open questions, remediation/testing suggestions, and human sign-off status. Explicitly distinguish deterministic facts, AI interpretations, and manual verification requirements.

## 5. Smoke-test with public synthetic fixtures

```powershell
python -m unittest discover -s tests -v
python -m hardwarecheck trace-zero --netlist tests/fixtures/zero_ohm_net.dat --parts tests/fixtures/zero_ohm_parts.dat --bom tests/fixtures/zero_ohm_bom.csv --net UART_TX
```

**Do not claim success unless commands actually ran.** See `docs/PROGRESS.md` for what was submitted, locally tested and actually verified against real OrCAD/Allegro.
