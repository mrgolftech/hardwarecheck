# 0Ω connection tracing: semantics and limitations

- Original netlist nets are **never globally merged**; the program computes separate graph traversals across eligible two-pin 0Ω resistor components.
- Resistor recognition requires an R-prefixed numeric refdes or a part name containing RES, explicit zero resistance value from BOM and/or part list, exactly two physical pins and two distinct networks.
- Supported zero markings include 0, 0R, 0R0, 0.0, 0Ω, 0 Ohm. Unrecognized strings are not treated as short circuits.
- BOM DNP/DNS fields interpret YES/1 as not fitted, NO/0 as fitted. FITTED/POPULATE/装配 fields interpret YES/1 as fitted, NO/0 as not fitted. Ambiguous or contradictory flags never become a confirmed bridge.
- The absence of an explicit populated field (even if a BOM row exists) is **assumed_fitted**, only eligible for possible traversal; missing BOM rows are **unknown**.
- If part-list resistance conflicts with BOM resistance, that device is excluded and separately flagged.
- `confirmed_reachable` is topology under **explicit BOM fitted assertion**. It is not a physical measurement. `possible_reachable` can include unknown/assumed states.
- Pins, net names and resistor refdes are reported verbatim. Verify output against original OrCAD source before treating it as a design verdict.
- Not supported: switch/jumper state, 0Ω solder bridges, net ties, ferrites, internal silicon connectivity, diode direction, signal direction/inversion, logical functionality, parasitics, isolation or PCB geometry.
- Risk example: UART_TX may be reachable to SBUS_OUT only through an assembled 0Ω component, while SBUS framing and signal inversion cannot be established by connectivity alone.

## Example commands

```powershell
python -m hardwarecheck trace-zero --netlist path/to/pstxnet.dat --parts path/to/pstxprt.dat --net UART_TX
python -m hardwarecheck trace-zero --netlist path/to/pstxnet.dat --parts path/to/pstxprt.dat --bom path/to/bom.csv --net UART_TX
```

Do not upload genuine proprietary EDA data to a public repo or use an unapproved cloud AI runtime.
