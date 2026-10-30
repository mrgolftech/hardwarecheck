# Hardware review report and issue gate

Use `assets/report-template.md`, and produce a machine-readable findings array where possible. A finding schema:

```json
{
  "rule_id": "INTERFACE-UART-SBUS-REVIEW",
  "status": "SUSPECTED",
  "severity": "medium",
  "subject": {"net": "UART_TX"},
  "statement": "Check inversion, logic levels and firmware UART framing",
  "evidence": [{"kind": "netlist", "net": "UART_TX"}],
  "reviewer_decision": "unreviewed"
}
```

The validator checks basic object references, **not** whether the electrical reasoning or datasheet passage is correct. Report confirmed facts and engineering hypotheses in different columns. For every important observation report:

- source + SHA-256 (when available), BOM variant, rule ID/version and exact component/net/pin;
- deterministic observation vs LLM hypothesis;
- severity distinct from analysis status and human approval status;
- basis, unverified assumptions, missing evidence;
- suggested corrective or verification procedure (e.g. schematic inspection, scope check, simulation);
- checks not executed, with their reasons.

Do not describe a circuit as certified / passed if only a subset of rules ran.
