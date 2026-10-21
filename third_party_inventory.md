# 第三方依赖与复用清单（初稿）

状态：本仓库V0.2-alpha中的专业检查代码均为新建示例实现，**尚未复制第三方开源项目源文件**。第三方代码是否引入要先完成版本、许可证、兼容性和本地安全审查。

| 项目 | 来源 | 当前用法 | 待办 |
|---|---|---|---|
| Seeed Schematic Analyzer | https://github.com/Seeed-Studio/ai-skills/tree/main/skills/schematic-analyzer | 方法和适配目标参考 | 核实许可证与当前commit；在真网表上对照 |
| Seeed EE Datasheet Master | https://github.com/Seeed-Studio/ai-skills/tree/main/skills/ee-datasheet-master | PDF检索/抽取流程参考 | 参数表格、OCR边界和许可确认 |
| kicad-happy | https://github.com/aklofas/kicad-happy | 证据门禁、回归方法参考 | 选可迁移算法而非直接复用KiCad解析 |
| Allegro exportJson | https://github.com/juulsA/exportJson | SKILL数据导出参考 | 检查JSON对象覆盖与许可证 |
| KiCad MCP Pro | https://github.com/oaslananka/kicad-mcp-pro | 只读工具/MCP架构参考 | 如需MCP再评估 |
| PyMuPDF | https://pymupdf.readthedocs.io/ | 可选PDF检索运行依赖 | 检查许可证与组织分发模式 |
| GitHub Actions官方checkout/setup-python | https://github.com/actions | 仅合成测试CI | 固定版本/版本策略与供应链审查 |

本仓库 `pyproject.toml` 运行基础无第三方库（Python标准库）；PDF功能可选PyMuPDF。完整供应链/许可批准和企业安全检查仍待实施。
