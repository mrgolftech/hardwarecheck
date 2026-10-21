---
name: pcb-review
description: 清点Allegro PCB Designer导出的IPC-2581 XML或SKILL JSON，梳理实现PCB布局布线检查所需的数据；当前只做结构信息清点，不做真正的SI/PI/EMC或几何DRC判定。
---
# Allegro PCB审查数据准备

**当前能力边界：只有PCB导出数据清点器。不能声称已支持完整PCB设计检查。**

## 使用
从Allegro的制造数据导出流程获得IPC-2581 XML，或经审查的SKILL脚本导出JSON。别将Cross-section层叠专用导出等同完整布线导出。

```bash
hardwarecheck pcb-summary --path "path/to/board_ipc2581.xml"
hardwarecheck pcb-summary --path "path/to/board_export.json"
```

直接传入 `.brd` 会显式报错。当前命令仅统计XML标签或JSON顶层结构，不保证其符合完整IPC-2581 Schema，不提取可用于真实距离测量的坐标、走线、过孔或网络几何。

## 计划中的后续审查（均未实现）
- 基于已验证坐标、器件中心和焊盘网络检查去耦位置；
- PCB布线/过孔/层分布检查；
- 根据设计层叠和约束核对差分对、走线与回流问题；
- 原理图↔PCB网络/BOM一致性。

无层叠、铜皮、焊盘、实际线段、可用空间尺度与工艺参数时，规则输出INSUFFICIENT_EVIDENCE。不从PCB截图推断定量SI/PI/EMC合格。
