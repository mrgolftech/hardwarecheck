# hardwarecheck — 基于通用 Agent 的硬件设计智能审查

> 项目状态：V0.2-alpha 工程骨架已提交（真实EDA尚未验证） · 方案版本：V0.2 · 更新：2026-10-22  
> 重要声明：当前仓库包含**方案文档、7个Agent Skills和初版Python只读CLI**。平面网表解析、基础BOM差异等已有实现和合成测试用例，但尚未在真实OrCAD/Allegro项目验证；完整PCB几何检查、电气规则与实际缺陷检出率仍未实现或未验证。AI输出不能替代正式的硬件评审、EDA ERC/DRC、必要仿真或实测。

## 快速开始（V0.2-alpha）

本项目**不开发新的通用Agent**，在支持Skills的OpenCode/Codex等现成客户端里运行。专业工具本地执行，无需单独LLM调用；有意调用外部模型前须遵循单位授权和数据分级要求。

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m hardwarecheck inspect --netlist tests/fixtures/pstxnet.dat --parts tests/fixtures/pstxprt.dat
python -m hardwarecheck review --netlist tests/fixtures/pstxnet.dat --parts tests/fixtures/pstxprt.dat --bom tests/fixtures/bom.csv
```

其余命令包括 `component`、`net`、`bom-diff`、`eco-diff`、`validate-findings`、`pdf-search`（需可选PyMuPDF）和 `pcb-summary`（仅数据清点）。

**当前已实现四项小型规则**：同一物理引脚解析到多个网络、单成员网络提示、BOM/网表双向位号差异；其余电源反馈、UART电平、PCB去耦等规则仍未实现。当前脚本不进行真正的Allegro PCB几何DRC/SI/PI或完整器件手册电气验证。

- [V0.2工程架构与运行说明](docs/07-开发架构与运行指南.md)
- [当前进度、已完成与待验证能力](docs/PROGRESS.md)
- [第三方项目接入计划](docs/08-外部项目集成指南.md)
- [可执行与规划规则能力清单](rules/catalog.json)
- [7个Agent专业Skills](.agents/skills/)

> 请勿把真实公司网表、PCB、BOM、内部检查规则或设计资料上传到本公开仓库。单元测试全部使用虚构数据。

## 1. 项目愿景

以部门已有的原理图与 PCB 检查要素表为专业知识基础，结合器件数据手册、设计需求、OrCAD 网表、Allegro PCB 数据和 BOM，构建可在**通用 Agent** 中调用的硬件设计审查能力：

- 自动理解工程数据中的器件、引脚、网络和功能模块；
- 将检查表转化为可执行、可版本化、可追溯的专业规则；
- 由确定性脚本处理结构、公式、连接和几何事实，由 LLM Agent 处理语义理解、适用性判断和复杂审查；
- 将每条检查结论绑定到规则、设计对象、计算或数据手册证据；
- 通过真实缺陷 / 注入缺陷 / 正常样本验证其检出率与误报率，最终沉淀为可跨项目复用的部门技术能力。

**项目不以开发新的 Agent 框架或独立 GUI 为第一目标**。初期选择通用 Agent（先以 OpenCode 作为验证入口，兼容其他支持 Skills/MCP/脚本执行的平台），自主建设专业 Skills、Python 工具和规则库。

## 2. 现有工作环境

| 输入 | 计划用途 | 初期状态 |
|---|---|---|
| OrCAD Capture 导出网表：`pstxnet.dat`、`pstxprt.dat`，可补充 `pstchip.dat` | 构建器件/引脚/网络连接图 | 待真实样本验证 |
| OrCAD Capture XML（如可导出） | 补充图纸页、层次及属性 | 可选增强；Seeed 方案可能要求 |
| BOM（Excel/CSV） | 型号、位号、数值、封装与网表对应 | 待字段映射 |
| 器件数据手册（PDF） | 额定参数、引脚功能、电平、时序、推荐应用 | 待证据提取验证 |
| Allegro PCB `.brd`、导出 IPC-2581/XML 或 SKILL/JSON | PCB 布局布线与部分几何规则分析 | 第二阶段验证 |
| 设计需求与部门检查要素表 | 目标参数、规则和验收依据 | 需结构化分类 |

对 `.brd` 等专有文件**不假设通用 LLM 可直接可靠解读**。先通过 Allegro 的 IPC-2581 导出或 SKILL 提取生成结构化数据；IPC-2581 内容随导出模式/字段而变，须检查实际覆盖范围。

## 3. 技术路线

```text
OrCAD 网表 / BOM / Datasheet / 需求 / Allegro 导出
                       │
          EDA 解析与统一设计数据模型
                       │
      专业规则引擎 ── 工具调用 ── 通用 Agent + Skills
                       │             │
            确定性结果      器件手册与复杂语义审查
                       └──────┬──────┘
                         证据校验与去重
                               │
                       人工确认与问题闭环
                               │
                      HTML/Markdown/JSON报告
```

- **事实层**：本地 Python，可信解析、可重复运行，不把大网表原文全部塞进提示词。
- **规则层**：检查项 ID、适用范围、前置数据、判定方式、证据、严重度、规则版本。
- **Agent 层**：按功能电路组织任务、选择规则、调用只读工具、解释疑似问题；不擅自修改工程数据。
- **验证层**：校验位号/引脚/网络存在性、参数来源及适用条件，区分确定性错误与需复核意见。
- **交付层**：首先以 Skills + CLI + 报告使用，后续视推广需要再做 MCP 或 GUI。

详见：[目标与边界](docs/01-目标与范围.md) · [技术架构](docs/02-技术架构.md) · [输入与数据模型](docs/03-输入及数据契约.md) · [实施路线与验收](docs/04-实施路线及验证.md) · [开源参考项目](docs/05-参考项目.md) · [P0首次验证指南](docs/06-首次验证操作指南.md) · [Agent协作规范](AGENTS.md) · [规则示例](templates/rule-example.yaml)。

## 4. 分阶段落地

| 阶段 | 核心任务 | 验收产出 |
|---|---|---|
| P0：解析可行性 | 验证 Seeed Schematic Analyzer 对 OrCAD 导出数据的适配；必要时增加轻量适配器 | 网表对象数量/连接关系核对记录 |
| P1：原理图智能审查 | 首批 10–20 条规则；电源/复位/UART 等样例；BOM 与 Datasheet 引用 | 专业 Skill、规则库、证据报告、测试集 |
| P2：PCB 审查 | 验证 Allegro IPC-2581 / SKILL 导出；优先可量化几何与一致性规则 | PCB数据抽取与检查结果 |
| P3：跨域与组织推广 | ECO差异、原理图↔PCB↔BOM一致性、历史质量问题回灌 | 跨项目报告、准确性/效率验证与应用案例 |

详见 [实施路线及验收](docs/04-实施路线及验证.md)。

## 5. 参考开源项目（按直接价值）

1. [Seeed Studio / schematic-analyzer](https://github.com/Seeed-Studio/ai-skills/tree/main/skills/schematic-analyzer)：OrCAD/KiCad 结构化网表查询；**首先验证**。
2. [Seeed Studio / ee-datasheet-master](https://github.com/Seeed-Studio/ai-skills/tree/main/skills/ee-datasheet-master)：PDF 参数提取与来源引用。
3. [aklofas / kicad-happy](https://github.com/aklofas/kicad-happy)：确定性检查、Agent 深度审查、证据门禁和回归测试方法；以思路复用为主。
4. [yuravg / cadence_netlist_format](https://github.com/yuravg/cadence_netlist_format)：`pstxnet.dat` 轻量解析参考。
5. [juulsA / exportJson](https://github.com/juulsA/exportJson)：Allegro SKILL 提取 JSON（面向 InteractiveHtmlBom 的数据结构，非全量 PCB 语义）。
6. [oaslananka / kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro)：只读工具、MCP 接口、人工审查门禁的架构参考。
7. [AllSpice DRCY](https://arxiv.org/abs/2603.15672)：工业应用方法参考，**商业非开源**。

详见 [参考项目与复用策略](docs/05-参考项目.md)。引用开源代码前应核查许可证和实际兼容性。

## 6. 安全边界

此仓库当前为公开仓库：**禁止提交**真实客户/企业原理图、PCB、BOM、专有器件手册、内部检查表、需求、测试数据、密钥、许可证或私有报告；仅用公开或完全脱敏的测试夹具。项目本地工作数据应位于仓库以外，或由严格 `.gitignore` 排除，并在提交前人工检查。

## 7. 近期启动动作

1. 固定一份获准使用的 OrCAD 导出样例（不提交公开仓库），验证 DAT / XML 解析覆盖率与连接正确性。
2. 把原理图检查要素表逐条分为结构型、计算型、知识型、跨域型、人工型，选择首批规则。
3. 建立正例、缺陷注入、已知历史问题对照集，记录实际检出和误报，避免以 Agent 自评代替验收。
4. 在通用 Agent 中加载专业 Skill，优先使用只读工具执行首轮审查。

> 研发产出定位：**硬件专业知识工程化、可验证的专用审查方法和质量闭环**；不将通用 Agent 的已有能力包装为自研算法。


## 2026-10-30 V0.3 开发分支：Codex 综合 Skill 与 0Ω 路径工具

- 新增可被 Codex 从项目根目录发现的 `.agents/skills/hardware-design-review/SKILL.md`；这是综合工作流入口，原7个专项Skills仍然保留。
- 新增 `hardwarecheck trace-zero --netlist ... --parts ... --bom ... --net UART_TX`，按BOM装配状态区分 `confirmed_reachable`（明确装配字段）与 `possible_reachable`（还包含假设装配的路径），报告DNP及阻值/装配冲突。
- 不对物理走线、方向、反相、电平、完整层次网表及真实PCB实施推断；现有四条基础规则未扩展为完整ERC/DRC。
- 新增完全合成的0Ω/DNP/UART连接样例回归测试；**不等于真实Cadence网表适配已验证**。
- 演示命令：

```powershell
python -m unittest discover -s tests -v
python -m hardwarecheck trace-zero --netlist tests/fixtures/zero_ohm_net.dat --parts tests/fixtures/zero_ohm_parts.dat --bom tests/fixtures/zero_ohm_bom.csv --net UART_TX
```

完整边界见 `.agents/skills/hardware-design-review/references/connectivity.md` 和 `docs/PROGRESS.md`。
