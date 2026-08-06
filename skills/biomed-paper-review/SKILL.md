---
name: biomed-paper-review
description: 生物医药论文 AI 审稿与图谱解析。输入一篇论文（PDF / JATS XML / 纯文本），输出结构化结果表、图表解读与原图定位、七维审核发现、整体置信度与人工复核建议。当用户需要审阅、复核、预审生物医药领域论文或稿件，或需要抽取论文中的实验条件、剂量响应曲线、统计图、实验流程图、显微图的关键数值时使用。
---

# 生物医药论文 AI 审稿 Skill

## 0. 这个 Skill 做什么、不做什么

**做**：替代人工审稿的**基础环节** —— 把一篇论文压缩成结构化事实，解析全部图表，再按七个维度对照通用规范做合规性校验，最后给出置信度评分和明确的人工复核方向。

**不做**（团队已达成共识的边界，越界会导致误判并拖垮可信度）：

| 不做 | 原因 |
| --- | --- |
| 判断论文结论在科学上是否**为真** | 需要外部领域数据；本 Skill 仅基于论文自身 + 通用规范 |
| 判断领域**创新性 / 重要性** | 主观，属于资深审稿人职责 |
| 判断违背基础常识的结论（如"面粉可治疗癌症"） | 交由人工复核环节，Skill 只标记"结论超出证据支持范围" |
| 复现统计计算或重跑分析 | 只校验方法选择与报告完整性，不重算 |

**核心原则：一切发现必须可回溯到论文中的具体位置。** 无法给出 `evidence.locator` 的发现一律丢弃，不得输出。这是本 Skill 与"大模型泛泛点评"的根本区别。

---

## 1. 执行流程

按顺序执行五个阶段。每个阶段的产物是下一阶段的输入，不要跳步。

```
① 载入与切分  →  ② 结构化抽取  →  ③ 图谱解析  →  ④ 七维审核  →  ⑤ 汇总与输出
   normalize      structured_       figure_          findings[]      review_report
                  result表          record[]
```

### ① 载入与切分

1. 判断输入类型：JATS/PMC XML（最优，章节与图注已结构化）> PDF > 纯文本。
2. 切分出标准章节：`title / abstract / introduction / methods / results / discussion / conclusion / ethics / funding / data_availability / references`。
   - 章节缺失**本身就是一条 finding**（交给模块 M2）。不要静默补齐。
3. 为每个段落与每张图表分配稳定的定位符（见 §3 定位符规范）。PDF 输入时必须记录页码。
4. 清单化所有图表：`Fig 1..n`、`Table 1..n`、补充材料。正文引用了但不存在的图表，反之亦然，都记为 finding。

### ② 结构化抽取

产出 `structured_result`（模式见 `schemas/structured_result.schema.json`），四大核心维度：
**研究目标 / 实验方法 / 核心数据 / 初步结论**。

规则见 `references/01-structured-extraction.md`。要点：

- 只抽取论文**明确写出**的内容。缺失字段填 `null` 并在 `gaps[]` 中登记，**严禁推断填充** —— 推断出来的数值会污染下游全部七个模块。
- 数值必须带单位、样本量、误差类型（SD / SEM / 95%CI）。三者缺一即降置信度。
- 每个字段都要带 `evidence.locator`。

### ③ 图谱解析

对每张图产出一条 `figure_record`（模式见 `schemas/figure_record.schema.json`）。流程：

1. **分类**：`dose_response`（剂量响应）/ `statistical_plot`（柱状、箱线、散点）/ `workflow`（实验流程、CONSORT、PRISMA）/ `micrograph`（显微、组化、荧光）/ `blot`（WB / 凝胶）/ `survival`（KM 曲线）/ `heatmap` / `flow_cytometry` / `schematic` / `other`。
2. **读取实验条件**：分组、剂量梯度、时间点、n、重复类型（生物学重复 vs 技术重复）。
3. **抽取关键数值**：IC50/EC50、拟合参数、误差棒、显著性标记与对应 p 值、坐标轴范围与刻度类型（线性/对数）。
4. **原图定位**：给出页码 + 图号 + 在正文中首次被引用的位置。
5. **置信度**：数值来自图注/正文文字 = 高；来自坐标轴刻度读数 = 中；来自像素估读 = 低，且必须写进 `manual_review`。

**硬性要求：从像素估读的数值一律标 `confidence: low` 并给出区间而非点值。** 编造精确读数是本 Skill 最严重的失败模式。

详细规则见 `references/05-figures-and-charts.md`。

### ④ 七维审核

七个模块**相互独立**，可并行执行；每个模块读取自己的 reference 文件，输出统一格式的 `finding[]`。

| # | 模块 | 负责人 | 规则文件 | 核心问题 |
| --- | --- | --- | --- | --- |
| M1 | 结构化抽取 | MZYY（陈泓睿） | `references/01-structured-extraction.md` | 关键信息是否完整抽出？ |
| M2 | 宏观逻辑与格式 | ZY（卓妍） | `references/02-macro-logic.md` | 抛开生物专业性，整体逻辑链是否闭环？各部分是否完整？有无数据泄露、前后矛盾？ |
| M3 | 实验方法合规性 | Peter | `references/03-experimental-methods.md` | 方法有无 reference 依据？实验动物是否必要？有无异常实验对象/非通用流程？ |
| M4 | 统计学方法 | JY（蒋运） | `references/04-statistics.md` | 统计方法是否匹配数据类型？样本量是否过小？多重比较是否校正？ |
| M5 | 图表使用规范 | MY（敏仪） | `references/05-figures-and-charts.md` | 图表类型是否匹配研究目的？创新画法有无足够证据支撑？ |
| M6 | 伦理合规 | Peter | `references/06-ethics-compliance.md` | 动物/人体试验流程是否合规？有无对应伦理批件号与知情同意？ |
| M7 | 结论与讨论 | MY（敏仪） | `references/07-conclusions-discussion.md` | 结论是否被数据支持？讨论有无过度外推、避谈局限？ |

> 与会议纪要"分层审核"的映射：第一层内部逻辑校验 = M2；第二层实验方法 = M3；第三层统计学 = M4；第四层呈现规范 = M5；第五层特殊场景合规 = M6。M1 是全部层的输入，M7 是全部层的收口。

### ⑤ 汇总与输出

1. 合并七个模块的 findings，按 §3 去重规则消歧。
2. 计算整体置信度（§4）。
3. 生成人工复核建议：**每一条 `severity >= major` 的 finding 必须对应一条可执行的复核动作**，写明"看哪里、核什么、若属实该补什么实验或数据"。
4. 按 `templates/review_report.md` 渲染。

---

## 2. 统一 Finding 契约

**这是七个模块能合成一个 Skill 的关键。任何模块输出不符合此格式的内容，一律视为无效。**

```json
{
  "id": "M4-003",
  "module": "M4",
  "category": "sample_size",
  "severity": "major",
  "title": "组间比较样本量 n=3，未报告效应量与检验效能",
  "detail": "Fig 3B 三组比较使用 one-way ANOVA，各组 n=3（生物学重复未说明），未见效能分析或效应量报告。n=3 时该检验对中等效应几乎无检出力。",
  "evidence": {
    "locator": "fig:3B | p.7 | Methods §2.4",
    "quote": "Data are presented as mean ± SEM (n = 3)."
  },
  "rule_ref": "04-statistics#sample-size-floor",
  "confidence": "high",
  "manual_review": {
    "action": "核对 n=3 指生物学重复还是技术重复；要求作者补充效能分析或提高重复数",
    "who": "统计审稿人"
  }
}
```

**枚举值（不得自创）**

- `severity`: `critical`（结论不成立 / 伦理违规 / 疑似造假）> `major`（需作者补充材料或重做分析）> `minor`（表述与规范问题）> `info`（提示，不影响录用）
- `confidence`: `high`（论文明文写出）/ `medium`（由明文内容可靠推导）/ `low`（依赖估读或假设）
- `category`: 由各模块 reference 文件定义，必须是该文件中已登记的 slug。

**去重规则**：多个模块命中同一 `evidence.locator` 且语义重合时，保留 `severity` 最高的一条，其余降级为 `related_findings[]` 挂在其下。不要把同一个问题报告七遍。

---

## 3. 定位符（locator）规范

原图定位与证据回溯的统一寻址格式，管道符分隔，从粗到细：

| 形式 | 示例 | 用途 |
| --- | --- | --- |
| `sec:<章节>§<小节>` | `sec:methods§2.4` | 正文段落 |
| `fig:<图号><面板>` | `fig:3B` | 图与子图 |
| `tab:<表号>` | `tab:2` | 表格 |
| `p.<页码>` | `p.7` | PDF 页码，PDF 输入时必填 |
| `ref:<文献编号>` | `ref:14` | 参考文献 |

组合书写：`fig:3B | p.7 | Methods §2.4`。至少给出一项；PDF 输入必须含 `p.`。

---

## 4. 置信度评分

单条 finding 的置信度按 §2 枚举。**论文整体置信度**（0–100）用于回答"这篇稿子能不能进入下一轮"：

```
起始 100
  每条 critical  -25
  每条 major     -10
  每条 minor     -3
  info            0
结构化抽取覆盖率修正：若 structured_result 必填字段缺失率 > 30%，额外 -10
                      （信息缺失 ≠ 论文没问题，而是我们看不清）
下限 0
```

分段建议：`>= 80` 可进入常规同行评审；`60–79` 需作者澄清后复审；`< 60` 建议退回补充；出现任一 `critical` 时无论分数如何，**一律标记为需人工优先复核**。

评分只是排序信号，不是录用决定。报告中必须原文注明这一点。

---

## 5. 输出

主输出为 `templates/review_report.md` 渲染的 Markdown 报告，含五节：
结构化结果表 / 图表解读与原图定位 / 七维审核发现 / 整体置信度 / 人工复核建议。

需要机器消费时，同时输出符合 `schemas/review_report.schema.json` 的 JSON。

---

## 6. 参考文件索引

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| `references/01-structured-extraction.md` | 结构化字段定义、抽取规则、gap 登记 | 阶段 ② |
| `references/02-macro-logic.md` | 逻辑链校验、章节完整性、数据泄露场景库 | 阶段 ④ M2 |
| `references/03-experimental-methods.md` | 实验设计惯例库、动物实验必要性判据 | 阶段 ④ M3 |
| `references/04-statistics.md` | 统计方法选择表、样本量下限、多重比较 | 阶段 ④ M4 |
| `references/05-figures-and-charts.md` | 图表类型解析规则、图表规范库 | 阶段 ③ + ④ M5 |
| `references/06-ethics-compliance.md` | 伦理批件、知情同意、3R 原则核查 | 阶段 ④ M6 |
| `references/07-conclusions-discussion.md` | 结论-证据对齐、过度外推识别 | 阶段 ④ M7 |
| `schemas/*.json` | 全部输出的机器可校验模式 | 输出前自检 |
| `templates/review_report.md` | 报告渲染模板 | 阶段 ⑤ |

按需读取，不要一次性全部载入。
