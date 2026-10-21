---
name: eco-review
description: 对比两版OrCAD平面网表的器件、网络及引脚成员变化，为硬件ECO提供差异清单；不推断电气等价或改版风险等级。
---
# 设计版本变更审查

```bash
hardwarecheck eco-diff --old-netlist path/to/old/pstxnet.dat --new-netlist path/to/new/pstxnet.dat
```

## 方法
1. 两版使用一致的OrCAD导出方式、统一的目标配置；分别进行输入解析可靠性检查。
2. 查看增加/移除的位号、网络和相同网络下增减的(位号,引脚)成员。
3. 对所有差异判断是否存在改名、换位号、引脚互换等，仅靠字符串diff**不可自动消除这种等价情况**。
4. 需结合两版BOM、数据手册、需求、PCB约束及专家复核，才能进行真正的ECO影响风险分析。

这是**结构化变更清单生成器**，不等于已经实现基于器件行为和上下电条件的智能ECO审核。
