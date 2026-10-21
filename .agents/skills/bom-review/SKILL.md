---
name: bom-review
description: 对照OrCAD网表与CSV BOM位号进行只读清点和差异审查，区别装配变体、DNP、机械位号与已确认的设计问题。
---
# BOM一致性检查

前置：`hardwarecheck` 已安装；CSV含 `RefDes` / `Designator` / `位号` 等列。Excel请先在获批环境另存为UTF-8 CSV。

```bash
hardwarecheck bom-diff --netlist path/to/pstxnet.dat --parts path/to/pstxprt.dat --bom path/to/bom.csv
hardwarecheck review --netlist path/to/pstxnet.dat --parts path/to/pstxprt.dat --bom path/to/bom.csv
```

## 检查方法
1. 核对工程版本一致，说明装配变体；CSV位号按单条或逗号/分号分隔支持。
2. 分别列出网表有/BOM无、BOM有/网表无、重复位号以及匹配位号。
3. 向用户询问或检索是否有DNP、机械件、安装孔、多个位号共物料、器件多Section。
4. 当前差异只输出NEEDS_REVIEW，不直接判为原理图设计缺陷。
5. 若需型号/封装/替代料参数深入审查，需要额外项目专用规则与已核对手册，**当前未实现自动型号等价性判断**。

结果要含来源文件/设计版本，不能把BOM缺少未连接的机械件当成高风险故障。
