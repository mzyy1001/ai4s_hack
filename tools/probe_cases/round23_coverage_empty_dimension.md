# 单图解读评分片段

用户只要求解读 Figure 3B。执行范围没有结构化必填字段，也没有被引用的补充材料；唯一资产 Figure 3B 因分辨率过低完全不可读。

系统按以下规则计算：

```text
field_resolution_rate = 1.0          # 分母为 0
asset_readability_rate = 0.0         # 0/1
supplement_accessibility = 1.0       # 分母为 0
extraction_coverage = 0.60×1.0 + 0.25×0.0 + 0.15×1.0 = 0.75
```

报告显示“抽取覆盖率 0.75”，但没有从该图成功提取任何信息。
