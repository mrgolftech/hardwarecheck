# 研发进度记录 — hardwarecheck

更新：2026-10-22 · 版本：V0.2-alpha（通用Agent + Python工具+ Skills 工程骨架）

## 状态口径

- **已提交**：文件/代码已写入GitHub，并不自动意味着执行成功。
- **合成样本测试**：仅在虚构网表/PCB导出样本上运行测试，无法替代真实OrCAD/Allegro工程验证。
- **未验证**：未拿到真实EDA文件运行，或没有可核查测试日志。
- **未实现**：仅出现在规则清单、Skill规划或文档中。

## 已落盘内容

| 能力/模块 | 状态 | 文件/说明 |
|---|---|---|
| 项目目标、技术方案、输入契约、开源调研 | 已提交 | `README.md`、`docs/01*—08*` |
| Python包、统一CLI、JSON结构输出 | 代码已提交，待执行核验 | `pyproject.toml`、`src/hardwarecheck/cli.py` |
| OrCAD PSTXNET平面连通性子集解析 | 代码已提交，**真实EDA未验证** | `src/hardwarecheck/cadence.py` |
| PSTXPRT基础部件名/部分属性解析 | 代码已提交，真实EDA未验证 | 同上，不包含完整多Section映射 |
| CSV BOM导入与位号差异 | 代码已提交，合成样本覆盖 | `bom.py` |
| 4条确定性/启发式检查 | 代码已提交，合成样本覆盖 | `rules.py`、`rules/catalog.json` |
| 证据字段与网表引用校验 | 代码已提交，**尚非完整电气证据验证** | `report.py` |
| PDF关键词文本查找 | 代码已提交，依赖PyMuPDF；真实资料未验证 | `datasheet.py` |
| Allegro JSON/XML导出清点 | 代码已提交，**未实现PCB几何分析** | `pcb.py` |
| ECO平面网表结构差异 | 代码已提交，**未实现电气等价与风险分级** | `eco.py` |
| 7个可发现的专业Agent Skills | 已提交，**尚未实测Agent自动调用** | `.agents/skills/*/SKILL.md` |
| 完全虚构设计的回归测试 + CI定义 | 测试文件已提交，CI结果待确认 | `tests/`、`.github/workflows/ci.yml` |

## 尚未实现与待验证

| 优先级 | 内容 | 首要验收点 |
|---|---|---|
| P0 | 用真实OrCAD DAT+可选Capture XML核实解析适配 | 关键器件/物理引脚/网络与原图逐点一致 |
| P0 | 运行Python单元测试及CI，修复异常 | 记录执行环境、日志、失败情况 |
| P1 | 正式接入Seeed适配或对现有解析器补充层次/多单元支持 | 稳定统一Schema，不误合并网络 |
| P1 | 完整BOM变体、DNP、封装型号映射 | 规则不把正常BOM差异误判设计错误 |
| P1 | 电源反馈、电平/时序等专业电气规则 | 有已验证数据手册参数+计算依据+人审真值 |
| P1 | PDF参数提取、复杂表格/扫描件的独立验证 | 不混淆min/typ/max和适用测试条件 |
| P2 | Allegro IPC-2581与SKILL导出真实坐标/走线/层叠解析 | 几何数据真实可核对，再实现PCB规则 |
| P2 | Agent完整审查计划、结构化报告与人审闭环 | 有真实历史问题/正常设计测试集 |
| P3 | 跨版本+跨域ECO风险与性能验证 | 工程审查收益有独立对照和样本口径 |

## 推荐下一轮迭代

1. 在已授权本地环境按 `docs/07-开发架构与运行指南.md` 安装并跑合成测试；把版本和日志摘要写入进度记录。
2. 拿一套真实OrCAD导出网表，以 `docs/06-首次验证操作指南.md` 做P0对照。
3. 运行Seeed Schematic Analyzer，比较同一套人工金标准，确认是否需要引入更完整的Capture XML适配。
4. 把部门检查要素表分类，选取首批可执行规则（不要一次性承诺全部完成）。
5. 只有完成这些门槛之后，再启动PCB几何引擎与更复杂的多Agent编排。

## 进度变更记录

| 日期 | 版本 | 修改内容 |
|---|---|---|
| 2026-10-22 | V0.1 | 项目定位、技术架构、输入、里程碑及开源项目调研入库 |
| 2026-10-22 | V0.2-alpha | 新增Python CLI原型、7个Skills、规则目录、合成测试与CI定义；真实工程效果暂未验证 |

## 安全记录

GitHub仓库是公开仓库。样例必须完全虚构；真实OrCAD网表、Allegro PCB、企业检查要素表、BOM、需求、手册和内部故障数据，必须在获批位置处理，不得提交该仓库或未经批准的远端CI和模型。


## V0.3 开发分支进度（2026-10-30）

| 项目 | 状态 | 说明 |
|---|---|---|
| Codex 综合 `hardware-design-review` Skill | 已提交分支，待Codex真实触发验证 | 标准路径 `.agents/skills/hardware-design-review/SKILL.md`，含方法引用与报告模板 |
| 0Ω电阻装配状态路径追踪 | 已提交分支，2026-10-30 CI通过 | `src/hardwarecheck/connectivity.py`、CLI `trace-zero`；严格区分已明确装配与可能连通 |
| DNP、BOM未知装配、阻值冲突 | 已提交分支，合成数据覆盖 | 仅处理受支持的CSV字段值，不推断真实电路装配 |
| 合成网表、BOM、自动测试 | 已提交分支，2026-10-30 CI通过 | `tests/test_connectivity.py` + 合成fixtures |
| 真实OrCAD DAT/PSTXPRT兼容性 | 未验证 | 必须在授权环境用真实样本核对 |
| 真实Allegro几何、电平/极性、数据手册参数电气规则 | 未实现/未验证 | 不可用Skill提示词代替算法与测试 |

注意：本节为 **V0.3开发分支** 状态，旧V0.2-alpha表格历史口径保留，不能由新代码提交直接推断全套测试通过。

CI 验证：https://github.com/mrgolftech/hardwarecheck/actions/runs/41080228107 （PR #1，tests job success）。此处只证明合成测试和CLI smoke通过；尚未验证Codex实际调用和真实EDA解析。
