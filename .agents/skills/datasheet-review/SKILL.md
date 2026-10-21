---
name: datasheet-review
description: 处理电子器件PDF手册的定位式文本检索、来源页码和参数证据核查；用于电源、MCU、接口电气条件检查，不允许臆测datasheet参数。
---
# 器件数据手册核查

本项目仅实现**PDF定向文本检索**。更完整的分阶段提取流程优先参考 Seeed Studio `ee-datasheet-master`，但该依赖尚未集成。

## 使用
```bash
python -m pip install -e ".[pdf]"
hardwarecheck pdf-search --pdf "path/to/MPN_datasheet.pdf" --term "VIH" --max-hits 8
```

## 工作方法
1. 先确认制造商、完整MPN、封装后缀、数据手册修订版本。
2. 定向定位章节与表格。命中片段的 `page` 是PDF页序号（从1开始），不必等于文档内印刷页码。
3. 必须核对电压/温度测试条件、单位、脚注、min/typ/max，避免错用典型值。
4. 图片扫描、时序图或复杂表格需本地渲染后人工视觉核对；不把关键词匹配当参数提取成功。
5. 向审查Agent返回 `MPN,revision,param,value,unit,min/typ/max,conditions,page,method,verification_state`。未核查的字段记缺失，而非补行业常识。
6. 所有设计合规结论还需真实电路工作条件和需求作比较；PDF关键词命中本身不构成检查通过。
