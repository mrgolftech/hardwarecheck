---
name: schematic-review
description: 只读审查OrCAD Capture/Allegro导出网表，查询器件、引脚、网络与连通性，并按证据生成检查意见。输入pstxnet.dat、可选pstxprt.dat、BOM和需求。
---
# OrCAD原理图结构化审查

适用：用户提供OrCAD导出网表，要求查器件、追网络、复核接口，或评估设计检查要素。

## 必须遵循
- 本仓库CLI **只支持pstxnet.dat的NET_NAME/NODE_NAME子集**、pstxprt.dat基础PART_NAME属性；真实项目必须验证层次与映射。
- 禁止仅凭平面网表推断信号方向、电压等级、复位时序、隐藏引脚、原理图图形位置或PCB布局。
- 优先调用CLI获取**客观连接事实**，避免把整个网表粘给LLM；工具失败不得凭推测补全。
- OrCAD带Capture XML完整模式可按需另装Seeed Studio Schematic Analyzer，并验证兼容性；当前仓库**尚未集成**该外部实现。

## 从仓库根目录运行

```powershell
python -m pip install -e .
hardwarecheck inspect --netlist "C:\work\pstxnet.dat" --parts "C:\work\pstxprt.dat"
hardwarecheck component --netlist "C:\work\pstxnet.dat" --parts "C:\work\pstxprt.dat" U1
hardwarecheck net --netlist "C:\work\pstxnet.dat" GND
hardwarecheck review --netlist "C:\work\pstxnet.dat" --parts "C:\work\pstxprt.dat" --bom "C:\work\bom.csv"
```

## 标准审查流程
1. 确认数据授权与导出版本；限制数据流向获批模型。
2. 先 `inspect`，核对数量/警告/数据完整性；对关键连接人工抽查。
3. 用 `component` 和 `net` 逐个查询电源、复位、UART/SBUS等局部网络。
4. `review` 运行已实现的四项基础规则；将其视为小范围原型**而不是原理图全检查**。
5. 根据企业检查规则确定适用性；若需datasheet，调用datasheet-review查找并人工确认参数/条件。
6. 输出“确定性发现/疑似/证据不足”，附位号、引脚、网络、规则ID、参考手册/需求来源、工具版本；工程师最终确认。

## 接受标准
所有输出结论须有设计数据证据；未知项目/型号/逻辑关系保持未知。对未检查规则不得自动标记PASS。完整实施情况见 `docs/PROGRESS.md`。
