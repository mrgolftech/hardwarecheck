# 电源树分析工作流（V0.4，Codex）

## 核心原则：电源网名 ≠ 确认的供电轨；两点连线 ≠ 确认的转换方向

1. 首先运行 `inspect`，检查来源SHA-256、网表格式、解析异常、物理管脚映射。
2. 不带映射运行 `power-tree`：仅列出 **候选电源网络**（网名规则匹配），不能推出真实电压、电流、转换方向、负载、级联关系。
3. 从原理图/器件手册核对每个关键转换器的 **物理 VIN/VOUT 引脚号**，以及负载 **真实 VDD/AVDD/VCC 供电脚**。当前平面 DAT/PSTXPRT 解析 **不能证明管脚功能**。多路输出PMIC可将每路单独声明为一条 converter 边，但必须核验每路输入路径；目前仅支持每条边单输入管脚/单输出管脚，不支持内部电源路径推断。
4. 按 `schema_version=0.1` 生成 **独立于真实工程的本地 power_spec.json**（不得提交公开Git仓库），其中仅填已得到依据的字段，不得按芯片型号臆测数值。
5. 带 `--power-spec` 运行后，工具校验每条声明的管脚确实属于位号，并取出网名，返回 **声明驱动的电源有向边**，同时保留注释错误与风险线索。输出不是已核验的电路功能。
6. 逐级分析：外部电源 → 输入保护/电源选择 → 转换器 → 各负载实际供电脚；再根据手册、BOM、原图和PCB补足数据。特别关注 DNP/0Ω/磁珠/二极管/负载开关和多供电模式，工具现在不会跨这些器件合并网。
7. 独立核实量化计算和工况：额定输入范围、各轨容差、最大输出电流预算、级联电流（需效率）、启动浪涌/峰值、PGOOD/EN次序、LDO压差/功耗、反馈分压、输入输出电容偏压和温度降额、纹波/稳定性、热设计、PCB回流。
8. 标记检查完成范围；只在有适用证据且有可复核公式或规则时给出具体问题。**零项疑点 ≠ 电源树检查通过。**

## CLI

```powershell
# 不带注释文件：只列出候选电源网
python -m hardwarecheck power-tree --netlist tests/fixtures/power_tree_net.dat --parts tests/fixtures/power_tree_parts.dat

# 带经原图和datasheet核对的本地映射（合成演示）
python -m hardwarecheck power-tree --netlist tests/fixtures/power_tree_net.dat --parts tests/fixtures/power_tree_parts.dat --power-spec tests/fixtures/power_tree_spec.json

# 获取电源检查清单（含每项的自动化程度）
python -m hardwarecheck checklist --category POWER
```

## power_spec.json 格式

```json
{
  "schema_version": "0.1",
  "sources": [
    {"net": "+12V", "voltage_v": 12}
  ],
  "converters": [
    {
      "refdes": "U1", "input_pin": "1", "output_pin": "2",
      "kind": "BUCK", "output_voltage_v": 5,
      "min_input_v": 7, "max_input_v": 24,
      "max_output_current_a": 2
    },
    {
      "refdes": "U2", "input_pin": "1", "output_pin": "2",
      "kind": "LDO", "output_voltage_v": 3.3,
      "min_input_v": 3.5, "max_input_v": 6,
      "dropout_v": 0.2, "max_output_current_a": 0.6
    }
  ],
  "loads": [
    {
      "refdes": "U3", "pin": "1", "max_current_a": 0.15,
      "min_voltage_v": 3.0, "max_voltage_v": 3.6
    }
  ]
}
```

**示例必须按自己的网表实际位号、物理引脚和手册修订调整；切勿套用示例电压或额定值。**

所有电压单位V，电流单位A。`sources[]` 表示人工声明的外部电源；不从原理图反向证明其真实输出电压。`converters[]` 表示经人工确认应执行转换的物理管脚；额定能力需来自手册，实际电流来自设计负载预算。`loads[]` 电流是用户给出的 **最大预估值**，未注释负载不会被自动包含。

## 输出判读

- `candidate_rails`：网名候选，仅用于下一步查询，不是电源树。
- `converters`：有向图，前提是映射者核对过器件功能；工具本身只校验物理连线存在。
- `annotation_errors`：映射或数值错误，禁止将对应条目当成正确拓扑。
- `PWR-VOLT-001`：多个来源声明电压不一致；`PWR-VIN-001`：已声明输入电压越界；`PWR-LOAD-001`：负载供电范围与声明电压不符。
- `PWR-CURRENT-001`：**已声明直接负载**的最大电流之和大于已声明转换器容量。未统计下游转换器输入电流/效率/其它负载，不能因为未超限就判定 PASS。
- `PWR-LDO-001`：根据声明的压差比较，但必须结合 Iload/温度/输出精度复核。
- `PWR-SOURCE-001`：多重供电源，需确认并联/OR-ing/防反灌；`PWR-CYCLE-001`：声明依赖成环，需核对实际电路与工作模式。
- 所有 `SUSPECTED` 只代表 **声明参数+已解析结构的风险线索**；必须标注输入来源，不是自动签核。
- `unchecked`：未实现/无法凭当前数据完成的内容，必须带入报告。

## 重要边界及后续增强

- 不从电阻/网络名推测调压反馈；当前没有自动计算真实FB等效电阻、相位裕量、滤波元件选型。
- 不跨接0Ω路径、磁珠/二极管/开关内部；需要另行运行 `trace-zero` 并核对装配状态，磁珠等靠人工绘制路径。
- 不把LDO压差限制当作恒定值；必须回到实际负载与温度曲线。
- 多路输出PMIC和复杂上电排序必须进一步验证数据手册与完整Capture XML，而不能只靠扁平网表。
- 不评估功率分配到上游的真实输入电流；需要效率曲线和工作模式后再做级联功耗计算。
- 不把“物理连接存在”当作“信号正常工作/电源能够启动”。
