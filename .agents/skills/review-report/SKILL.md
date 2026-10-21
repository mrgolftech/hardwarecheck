---
name: review-report
description: 对硬件审查Agent提出的问题进行设计对象证据检查、隔离虚构网络或器件引用，并形成专家复核报告，不把AI意见直接等同设计合格证明。
---
# 审查证据门禁与报告

结构化候选问题可整理为JSON数组，如：
```json
[
  {
    "rule_id": "CUSTOM-01",
    "status": "SUSPECTED",
    "severity": "medium",
    "subject": {"net": "UART_TX"},
    "evidence": [{"kind":"netlist","net":"UART_TX"}],
    "statement": "接口方向需要结合MCU引脚复用配置确认"
  }
]
```

在获批的本地文件夹保存为 `findings.json`，运行：

```bash
hardwarecheck validate-findings --netlist path/to/pstxnet.dat --findings path/to/findings.json
```

返回 `accepted` 与 `quarantined`。当前只核对基本对象存在、部分datasheet引用字段是否齐全，**不验证datasheet引文真伪、具体电压计算或其他工程正确性**。不能把accepted当作通过同行审核。

报告要分别写：规则是否已执行、数据是否完整、系统结论状态、工程风险、实际证据、专家决议，以及解析器/规则/模型版本。无法验证的结果隔离，记录原因。
