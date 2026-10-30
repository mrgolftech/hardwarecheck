# Engineering checklist and evidence gates

Apply only applicable checks. Each entry requires design evidence and, where parameters are involved, a correctly identified datasheet or requirement. This is a review procedure, not a claim of implemented deterministic rules.

| Circuit | Questions | Required evidence | Missing data response |
|---|---|---|---|
| Power | rail input/output, feedback divider, EN, decoupling, sequence, current/thermal headroom | nets, populated values, MPN/datasheet, specified load/current | insufficient evidence |
| UART/SBUS/RS485/CAN | TX/RX mapping, polarity/inversion, logic levels, frame timing, termination/bias/ESD | actual pin function, circuit topology, transceiver datasheet, firmware/peripheral configuration | suspected / needs review |
| Clock | source, crystal topology, load, I/O compatibility | nets, clock-source MPN, load cap and clock requirements | insufficient evidence |
| Reset/boot | POR, pull network, timing, boot strapping | nets, BOM population, controller datasheet | needs review |
| Connector/external interface | pinout, ground return, protection, level compatibility | connector standard + both ends of link | insufficient evidence |
| BOM | refdes/MPN/value/footprint/DNP and assembly variants | variant BOM + part properties + assembly field definition | review variant mismatch |
| PCB | placement, trace geometry, impedance/clearance, return paths | **verified** Allegro geometry export and stackup | not executed |

## Evidence discipline

1. Treat netlist records as structural facts only after parser compatibility and source checks.
2. Do not assume polarity, supply voltage, clock tolerance, or input thresholds from a net name.
3. For datasheet statements record vendor/MPN/revision/page/parameter/min/typ/max/unit/test conditions.
4. Distinguish numeric calculation from interpretation; show formula and parameter provenance.
5. A missing datasheet or uncertain pin assignment is not a FAIL; use `INSUFFICIENT_EVIDENCE`.
6. If critical parser errors exist, isolate impacted circuits and report `ERROR` or `NEEDS_REVIEW`.
7. Never use PDF keyword-search hits as proof of graph/table content without visual or manual verification.


## 扩展后的工程审查清单

使用 `rules/review_matrix.json` / `hardwarecheck checklist` 获取完整、分领域的审查项，每条包含证据要求和实现程度。先完成电源树再逐块分析信号接口；不能只按网名推断功能，参见 `power-tree.md` 和 `checklist-guide.md`。
