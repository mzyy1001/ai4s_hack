# 稿件审核评分片段

评分规则：每个 `major` finding cluster 记 10 分；同一 `category` 的累计分最多为 30；总分为各 category 截断后之和。

某动物感染研究有 5 个相互独立的实验：病毒载量、血管通透性、生存、组织病理和细胞因子。审稿系统确认每个实验都把同窝幼鼠当作独立样本，且模型没有处理 litter clustering。5 条 finding 均为 `major`，主证据分别位于 Figure 2、3、4、5、6，统一归类为 `pseudoreplication`。

当前系统输出：

```text
raw category score = 5 × 10 = 50
capped category score = 30
manuscript_risk_score = 30
```

随后在第六个独立实验中发现同样的伪重复，仍归入 `pseudoreplication`；系统总分保持 30。
