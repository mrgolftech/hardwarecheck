# 第一版演示脚本（完全虚构的数据）

> 对象：用于项目组自测和在通用Agent中验证工具调用；**不是已完成的真实硬件检查案例**。

## 1. 无LLM可运行演示

在仓库根目录安装：
```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

查询合成OrCAD网表：
```bash
hardwarecheck inspect --netlist tests/fixtures/pstxnet.dat --parts tests/fixtures/pstxprt.dat
hardwarecheck component --netlist tests/fixtures/pstxnet.dat --parts tests/fixtures/pstxprt.dat U1
hardwarecheck net --netlist tests/fixtures/pstxnet.dat GND
hardwarecheck review --netlist tests/fixtures/pstxnet.dat --parts tests/fixtures/pstxprt.dat --bom tests/fixtures/bom.csv
```

期望：5条网、5个有记录器件、13个网络引脚成员；U1的5脚连接 `+3V3`。规则产生一个TEST_NC的启发式疑点，以及J2、MH1相关的需复核BOM差异。以上属于**测试夹具的设计预期**，只有实际运行测试后才可标“通过”。

另有：
```bash
hardwarecheck pcb-summary --path tests/fixtures/pcb_sample.json
hardwarecheck eco-diff --old-netlist tests/fixtures/pstxnet.dat --new-netlist tests/fixtures/pstxnet.dat
```

## 2. 通用Agent交互演示

以仓库为工作目录启动OpenCode等支持Skills的Agent后，使用如下提示：

> 使用schematic-review和bom-review Skill读取本仓库完全虚构的tests/fixtures设计。先调用Python命令取得真实连接事实，再审查网表/BOM差异。区分结构性问题、疑似问题、DNP/机械件解释可能性，逐条附证据。不输出“该设计合格”的整体结论。

第二个提示：

> 使用eco-review Skill对同一个文件作为前后版本进行diff，解释“无结构变更”不等于“电气正确”的原因。

第三个提示：

> 使用rule-authoring Skill，针对“电源反馈电阻检查”写一条规则草案，列出必要的真实输入字段和缺失数据处理方法。不要声称该检测器已实现。

## 3. 真实设计演示前置条件

1. 使用获授权的内网模型和本地工程数据，不允许把企业网表提交此公开仓库。
2. 先在本地完成解析对照，包括多个复杂层次网络、物理引脚与实际网表的一致性。
3. 先准备“人工标注已知问题”与正常对照电路，再运行AI审查。
4. 设计问题发现、误报/漏报、复核工时等指标只使用实际记录，不以演示画面代替测试结论。
