# 审查清单的用法、覆盖面和证据门槛

权威清单：仓库 `rules/review_matrix.json`，用 `hardwarecheck checklist` 查询，不要把全部清单一次性粘入LLM上下文。

- 入口：先 `inspect`，再根据电源、接口、时钟、保护、模拟、高速、PCB等功能识别相关类别。
- 每条保留 `id/category/title/required_evidence/method/implemented`。
- `baseline_rule`：只有运行已有规则时才能记录该规则实际输出，不能把它外推成整个领域通过。
- `partial_tool`：有辅助脚本取得部分事实或比较已声明参数，**不具备全项自动PASS/FAIL能力**。
- `guided`：由Agent按原理图、数据手册、要求和必要时示波/仿真/PCB数据逐项评审；欠缺输入记 `INSUFFICIENT_EVIDENCE` 或 `not_executed`。
- 一项不适用可以记 `NOT_APPLICABLE` 并说明；未执行不能自动记PASS。确认错误要求原理图/手册原始证据与人工复核。
- 风险优先级先看安全关键/过压损毁/上电失败/大电流/不可恢复失效，再看接口/EMI/可测试性。风险严重度与判断确定性分开。

## 每次原理图评审建议顺序

1. 数据完整、网表/原图关键管脚对照、NC/DNP概念区分。
2. 电源树：输入→电源防护→各级转换器→各负载，检查各轨参数、顺序、反馈、去耦、热与浪涌。
3. 主控和关键器件逐芯片：每个电源/地/复位/Boot/EN/PG/FB/时钟/接口管脚，关联缺失的推荐外围器件。
4. 外设、通讯总线、模拟和高速接口：电气兼容及端接、上拉、保护、跨域、时序。
5. PCB布局与测试：有Allegro导出数据才涉及几何规则，缺时提供必须人工核实的清单。
6. 严格记录被覆盖、跳过、阻塞的检查项和证据等级；报告不得将guided checklist误记为“已自动扫描通过”。

## 来源与复用边界

参考开源项目的检查维度及方法，清单与脚本为本项目自编，未复制其实现：
- Seeed schematic-analyzer（准确优先、结构事实与语义分离）：https://github.com/Seeed-Studio/ai-skills/tree/main/skills/schematic-analyzer
- Seeed ee-datasheet-master（datasheet页码、条件、型号校验）：https://github.com/Seeed-Studio/ai-skills/tree/main/skills/ee-datasheet-master
- aklofas/kicad-happy（电源反馈、降额、保护、EMC、仿真）：https://github.com/aklofas/kicad-happy
- settchan2003-design/kicad-schematic-review-skill（逐器件pin-level契约、DCDC及生产检查）：https://github.com/settchan2003-design/kicad-schematic-review-skill

原生Cadence ERC/Allegro DRC与电气/热仿真仍需保留，不应以Agent输出代替。
