---
name: biomed-paper-review
description: 生物医药论文结构化抽取与审稿辅助。输入一篇论文（PDF / JATS XML / 纯文本），输出结构化证据表、图表解读与原图定位、多维审核发现、抽取覆盖率与复核置信度，以及分优先级的人工复核建议。支持四种执行模式（完整审核 / 仅结构化抽取 / 仅图表解析 / 定向核查）。当用户需要预审、复核生物医药论文或稿件，或需要抽取论文中的实验条件、剂量响应曲线、统计图、实验流程图、显微图的关键数值时使用。
---

# 生物医药论文审稿辅助 Skill

## 0. 定位与边界

**做什么**：自动化并辅助审稿的**基础性工作** —— 结构化证据抽取、图表解读、报告规范核查、
以及为专家复核排定优先级。

**明确声明（必须原样写入每份输出报告）**：

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查
> 与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。**
> 本 Skill 的任何评分均为筛查信号（screening recommendation / triage signal），
> 不构成录用、退稿或发表决定。

### 0.1 核心原则：证据可审计

**每一条稿件级 finding 都必须有可审计的证据支撑。**

- **针对已存在内容的 finding**：必须给出稿件内 `locator`（见 §3.1），可附原文引用。
- **针对缺失内容的 finding**：必须给出**显式的检索范围与缺失证据记录**（`type: "absence"`，
  见 §3.1），**不得**为不存在的内容伪造引文。

无法给出上述任一种证据的判断，一律丢弃，不得输出。这是本 Skill 与"大模型泛泛点评"的根本区别。

### 0.2 一期能力边界

一期仅基于**论文自身内容 + 通用规范库**完成校验，**不调用外部数据库**。
下列四项能力**不是做不到，是一期先不做**；每项已指派归属模块，规则写在该模块 reference 的
「二期扩展」一节。

| 能力 | 一期做法 | 二期归属 | 二期前置条件 |
| --- | --- | --- | --- |
| 判断论文结论在科学上是否**为真** | 只做 claim↔evidence 对齐，不查外部证据 | M7 | 文献库 MCP（PubMed / Europe PMC） |
| 判断领域**创新性 / 重要性** | 不判断 | M7 | 文献库 + 引用网络；需先定义可量化的新颖度判据 |
| 判断违背基础常识的结论 | 标记「结论超出证据支持范围」交人工 | M7 | 领域常识规则库；先积累一期人工复核的误判样本 |
| 复现统计计算 / 重跑分析 | 只校验方法选择与报告完整性 | M4 | 需原始数据；可先做「不依赖原始数据的一致性检验」子集 |

**二期与一期的关系**：二期应尽可能**保留核心流水线**，通过**扩展** provenance、外部证据、
来源版本与冲突消解契约来实现，而不是重构主框架。外部证据将需要额外元数据：
`database` / `query` / `retrieval_date` / `record_id` / `version` /
`retraction_or_correction_status` / `relation_to_claim`。

---

## 1. 执行模式

**首先判定执行模式，再进入流水线。**默认 `full_review`；用户只要一张图或一个数值时，
**不得**自动跑完整审核。

| 模式 | 触发条件 | 执行阶段 | 输出 |
| --- | --- | --- | --- |
| `full_review` | 用户要求审稿、预审、全面复核，或未指明范围地提交整篇论文 | Stage 1 → 5 | 完整 `review_report` |
| `structured_extraction` | 用户只要"抽取关键信息 / 结构化结果表" | Stage 1、2，以及仅针对被引用图表的 3 与 3b | `structured_result_v2` + `extraction_signals[]` + `system_limitations[]` |
| `figure_analysis` | 用户指定某几张图，或要求"解析全部图表" | Stage 1、3（限定范围）、3b | `figure_records[]` / `table_records[]` + 相关 `findings[]`（仅 M5） |
| `targeted_check` | 用户提出具体问题（如"样本量够不够""伦理声明齐全吗"） | Stage 1、2、3b，加上问题相关模块 | 相关模块 `findings[]` + `manual_review_plan[]` |

**模式约束**

- `structured_extraction` 与 `figure_analysis` **不产出** `manuscript_risk_score`
  —— 未跑审核模块就没有稿件风险结论。二者仍产出 `extraction_coverage`。
- `targeted_check` 必须在输出中列明**实际执行了哪些模块**、**跳过了哪些**，
  且 `manuscript_risk_score` 标记为 `partial: true`，不得与 `full_review` 的分数并列比较。
- 任何模式下，`review_confidence` 与 `system_limitations[]` 都必须输出。

---

## 2. 流水线

### 2.1 模块关系（不要说错）

本 Skill 含**七个分析模块**：**M1 是前置抽取层，M2–M7 是并行审核模块**。

M2–M7 全部消费 M1 的产物，因此 **M1 与 M2–M7 不是并行关系**。
只有在 Stage 2 与 Stage 3b 完成之后，M2–M7 才可并行执行。
可以说"一个抽取模块 + 六个审核模块"，**不要**说"七个模块相互独立"。

### 2.2 阶段与产物

```
Stage 1  文档归一化与切分
         └─> normalized_document, asset_inventory, system_limitations[]

Stage 2  M1 结构化抽取（文本来源）
         └─> structured_result_v1, extraction_signals[], extraction_quality_findings[]

Stage 3  图表解析（M5 执行解析部分）
         └─> figure_records[], table_records[]

Stage 3b 证据合并与冲突消解
         └─> structured_result_v2, source_conflict_signals[], unresolved_evidence_links[]

Stage 4  M2–M7 并行审核
         └─> findings[]

Stage 5  去重、评分、人工复核动作、报告渲染
         └─> review_report
```

### 2.3 产出者 / 消费者对照（每个产物有且只有一个产出者）

| 产物 | 唯一产出者 | 消费者 |
| --- | --- | --- |
| `normalized_document` | Stage 1 | M1, M5, M2 |
| `asset_inventory`（图/表/补充材料清单 + 可读性） | Stage 1 | Stage 3, Stage 5（覆盖率） |
| `structured_result_v1` | Stage 2 (M1) | Stage 3（提供上下文）, Stage 3b |
| `extraction_signals[]` | Stage 2 (M1) + Stage 3b | M2, M4, M7（按 signal 类型路由） |
| `extraction_quality_findings[]` | Stage 2 (M1) | Stage 5（仅影响 coverage/confidence） |
| `figure_records[]` / `table_records[]` | Stage 3 (M5 解析部分) | Stage 3b, M4, M5 审核部分, M7 |
| `structured_result_v2` | Stage 3b | **M2–M7 全部** |
| `source_conflict_signals[]` | Stage 3b | M2（判定是否为稿件矛盾）, M4 |
| `unresolved_evidence_links[]` | Stage 3b | M7（判定 claim 是否失据）, Stage 5 |
| `findings[]` | Stage 4（各模块） | Stage 5 |
| `system_limitations[]` | Stage 1 / 2 / 3（任一阶段可追加） | Stage 5 |
| `review_report` | Stage 5 | 用户 |

### 2.4 Stage 1 · 文档归一化与切分

1. 判定输入类型：JATS/PMC XML（最优，章节与图注已结构化）> PDF > 纯文本。
2. 切分标准章节：`title / abstract / introduction / methods / results / discussion /
   conclusion / declarations / ethics / funding / conflict_of_interest /
   data_availability / references / supplement`。
   - 章节缺失**不在本阶段判定为问题**，只写入 `asset_inventory.missing_sections[]`，
     由 M2 结合刊型决定是否构成 finding。
3. 为每个段落分配 `paragraph_id`，为每张图表分配稳定 id，构造 §3.1 的 locator 对象。
   PDF 输入必须记录 `pdf_file_page`；若能识别印刷页码则同时记录 `printed_page`。
4. 建立 `asset_inventory`：图、表、补充材料清单，逐项标注
   `readable` / `low_resolution` / `inaccessible`。
5. 解析失败（页面无法提取、图像损坏、补充材料不可得）产出 **`system_limitation`**，
   **不是** finding（见 §3.3）。

### 2.5 Stage 2 · M1 结构化抽取

产出 `structured_result_v1`（**仅文本来源**：正文、表格、图注文字）、
`extraction_signals[]`、`extraction_quality_findings[]`。
详细规则见 `references/01-structured-extraction.md`。

**本阶段的三条硬性规则**

- 只抽取论文**明确写出**的内容，**严禁推断填充**。推断出的数值会污染下游全部六个审核模块。
- 每个重要字段使用 §3.2 的 `extracted_field` 结构，`status` 必须显式给出，
  **不得用裸 `null` 编码多种缺失状态**。
- M1 **不做稿件级判断**。M1 只产出 `extraction_signal`（机器级观察），
  由 M2 / M4 / M7 决定其是否构成稿件问题（见 §3.3）。

### 2.6 Stage 3 · 图表解析

对每张图产出 `figure_record`，每张表产出 `table_record`。执行者是 M5 的解析部分，
规则见 `references/05-figures-and-charts.md`。

关键约束（完整规则在 M5 文件）：

- 先确定该图试图回答的**科学问题**，再判断图表类型是否匹配。
- 从图中读出的数值必须带 §3.2 的 `provenance` 对象。
- **像素估读的数值一律 `extraction_confidence: low`，必须写成区间而非点值**，
  并置 `manual_review_needed = true`。编造精确读数是本 Skill 最严重的失败模式。
- 图像不可读产出 `system_limitation`（`category: figure_unreadable`），不是 finding。

### 2.7 Stage 3b · 证据合并与冲突消解

把 Stage 3 的图表来源数值合并回结构化结果，产出 `structured_result_v2`。
**这是数据流的关键一环：图表解析结果必须回流，`structured_result_v1` 不得直接交给 M2–M7。**

**来源可靠性排序**（高 → 低）：

```
1. explicit_main_text     正文明文数值
2. explicit_table         表格明文数值
3. explicit_figure_caption 图注明文数值
4. axis_readable          可读坐标轴刻度
5. pixel_estimated        像素估读
```

**合并规则**

1. 同一字段有多个来源且**数值兼容**（在各自不确定度内一致）：
   取最高可靠性来源为 `value`，其余全部保留在 `alternatives[]`，`status: "reported"`。
2. 同一字段有多个来源且**数值不兼容**：
   - **不得静默覆盖**。
   - `status` 置为 `"conflicting"`，`value` 置为 `null`。
   - 全部来源值保留在 `candidates[]`，各带自己的 `provenance`。
   - 产出 `source_value_conflict` signal，交 **M2** 判定是否构成稿件内部矛盾。
3. 字段仅有 `pixel_estimated` 来源：`value` 写区间，`extraction_confidence: low`，
   `reporting_completeness` 独立判定（见 §3.2）。
4. `claims[].supported_by` 中无法解析到任何 `key_data.id` 或 locator 的条目：
   写入 `unresolved_evidence_links[]`，产出 `claim_without_resolved_evidence_link` signal，
   交 **M7** 判定是否构成无支撑主张。**M1 与 Stage 3b 都不下这个结论。**

### 2.8 Stage 4 · M2–M7 并行审核

**前置条件：Stage 2 与 Stage 3b 均已完成。** 六个审核模块此时可并行执行，
各自读取自己的 reference 文件，消费 `structured_result_v2`、`figure_records[]`、
`extraction_signals[]`，输出统一格式的 `finding[]`。

| # | 模块 | 负责人 | 规则文件 | 核心问题 |
| --- | --- | --- | --- | --- |
| M1 | 结构化抽取（**前置层，非审核模块**） | MZYY（陈泓睿） | `references/01-structured-extraction.md` | 关键信息是否完整、可溯源地抽出？ |
| M2 | 宏观逻辑与格式 | ZY（卓妍） | `references/02-macro-logic.md` | 逻辑链是否闭环？章节是否完整？有无数据泄露、前后矛盾？ |
| M3 | 实验方法合规性 | Peter | `references/03-experimental-methods.md` | 方法有无 reference 依据？实验动物是否必要？有无非通用流程？ |
| M4 | 统计学方法 | JY（蒋运） | `references/04-statistics.md` | 统计方法是否匹配数据类型？样本量报告是否充分？多重比较是否校正？ |
| M5 | 图表解析与使用规范 | MY（敏怡） | `references/05-figures-and-charts.md` | 图表类型是否匹配研究目的？呈现是否规范？正文/supplement 位置是否合理？ |
| M6 | 伦理合规 | Peter | `references/06-ethics-compliance.md` | 动物/人体试验流程是否合规？有无伦理批件号与知情同意？ |
| M7 | 结论与讨论 | MY（敏怡） | `references/07-conclusions-discussion.md` | 结论是否被本文数据支持？有无过度外推、避谈局限？ |

> 与会议纪要"分层审核"的映射：第一层内部逻辑 = M2；第二层实验方法 = M3；第三层统计学 = M4；
> 第四层呈现规范 = M5；第五层特殊场景合规 = M6。M1 是全部层的输入，M7 是全部层的收口。

**模块路由**：各模块依据 `structured_result_v2.study_design` 与 `evaluation_matrix`
决定跑哪些规则集。路由字段仅用于**选择规则**与**定位证据**，
**不得**仅凭 `evaluation_matrix` 的摘要值直接产出 finding（见 §4.2）。

### 2.9 Stage 5 · 汇总与输出

1. **去重与聚簇**：按 `references/00-contracts.md` §2.4 把 findings 归并为 issue cluster。
2. **评分**：计算 §5 的三项指标。
3. **人工复核动作**：每一条 `severity >= major` 的 finding 必须对应一条可执行动作，
   写明"看哪里、核什么、若属实该补什么"。
4. **渲染**：按 `templates/review_report.md` 输出 Markdown；需要机器消费时同时输出
   符合 `schemas/review_report.schema.json` 的 JSON。

---

## 3. 契约总览（详见 `references/00-contracts.md`）

全部模块共用三套契约。**完整定义、字段表与示例见 `references/00-contracts.md`，
需要输出任何结构化内容前必须先读该文件。** 此处仅给出必须随时记住的要点。

### 3.1 证据（evidence）

`evidence` 是**数组**，每个元素为两型之一：

| type | 用于 | 必填 | 禁止 |
| --- | --- | --- | --- |
| `present` | 稿件中已有的内容 | `locator` 对象 | —— |
| `absence` | 稿件中不存在的内容 | `searched_locations[]` + `search_terms[]` + `search_result` | **`quote`** |

`locator` 以**结构化对象**存储（`section` / `subsection` / `paragraph_id` /
`pdf_file_page` / `printed_page` / `figure` / `panel` / `table` / `supplement_id` /
`xml_id` / `scope`），`fig:3B | p.7` 只是渲染形式。**绝不为不存在的内容编造引文。**

### 3.2 字段状态（extracted_field）

所有重要字段用 `{value, status, evidence[], extraction_confidence, ...}`，
`status` 取六值之一，**不得用裸 `null` 编码多种缺失状态**：

```
reported | not_reported | not_applicable | ambiguous | conflicting | parse_failed
```

最关键的两条区分：`not_reported`（**稿件**没写，已检索确认）**可以**成为 finding 依据；
`parse_failed`（**我们**没读出来）**绝不可以**，只降覆盖率。
无法确定属于哪种时一律用 `parse_failed` —— 宁可承认看不清，不可冤枉稿件。

数值来源统一用 `provenance.source_type`：

```
explicit_main_text | explicit_table | explicit_figure_caption | axis_readable | pixel_estimated
```

`pixel_estimated` 强制 `extraction_confidence: low` + 区间值 + `manual_review_needed`。

`extraction_confidence`（我们读对了吗）与 `reporting_completeness`（稿件报全了吗）
是**正交**的两个字段，不得互相传染。

### 3.3 三类输出（不可混用）

判断归属的唯一标准：**这是稿件的问题，还是我们的观察，还是我们的能力限制？**

| 契约 | 产出者 | 含 severity | 影响 |
| --- | --- | --- | --- |
| `finding` | M2–M7（M1 仅限抽取质量类） | ✅ `critical/major/minor/info` | 稿件风险分 |
| `extraction_signal` | M1、Stage 3b | ❌ **无** | 路由给下游判定，本身不是结论 |
| `system_limitation` | Stage 1/2/3 | ❌ **无** | 只降覆盖率与置信度 |

**解析失败不得赋予稿件 severity。** `severity >= major` 的 finding 必须有可执行的
`manual_review.action`。`extraction_signal` 的六种 type 与路由去向见
`references/00-contracts.md` §2.2；下游据 signal 立 finding 时，
必须在 `evidence[]` 中独立给出稿件证据，不得仅引用 signal id。

Stage 5 的去重与聚簇规则（同模块合并 → 跨模块聚簇 → 证据合并）见
`references/00-contracts.md` §2.4，其产物 `issue_clusters[]` 是 §5.1 计分的单位。


## 4. 结构化结果与路由

### 4.1 structured_result 的两个版本

| 版本 | 产出者 | 内容 | 谁能用 |
| --- | --- | --- | --- |
| `structured_result_v1` | Stage 2 (M1) | **仅文本来源**的抽取结果 | 仅 Stage 3（作上下文）与 Stage 3b |
| `structured_result_v2` | Stage 3b | 合并图表来源、完成冲突消解后的结果 | **M2–M7 全部** |

**M2–M7 一律消费 `v2`。** 直接读 `v1` 会漏掉全部图表来源数值。

### 4.2 evaluation_matrix 的正确用法

`evaluation_matrix` 是**路由与索引**工具，每个条目是**状态感知对象**而非裸布尔：

```json
"randomization": {
  "status": "not_reported",
  "applies_to": ["EXP-01", "EXP-02"],
  "evidence_refs": ["EV-018"],
  "extraction_confidence": "high"
}
```

**三条用法规则**

1. **可以**用它决定跑哪些规则集、定位相关证据。
2. **不得**仅凭它直接立 finding。M2–M7 必须回查 `evidence_refs` 指向的证据记录，
   在自己的 finding 中独立给出 `evidence[]`。
3. 实验级字段（如组样本量）**不得**压缩为单一数字。使用 `group_sizes[]` 保留实验级上下文：

```json
"group_sizes": [
  {"experiment_id": "EXP-01", "group": "vehicle", "n": 6, "replicate_type": "biological",
   "evidence_refs": ["EV-021"]}
]
```

---

## 5. 三项评分（互不替代）

**禁止**把稿件风险分称作"置信度"。三项分别输出，报告中不得合并为单一数字。

```json
{
  "manuscript_risk_score": 34,
  "extraction_coverage": 0.82,
  "review_confidence": 0.71
}
```

### 5.1 manuscript_risk_score · 稿件风险分（0–100，越高风险越大）

反映**已验证的稿件 finding** 的严重度与范围。
**不因 PDF 不可读或解析失败而升高**（那属于 coverage 与 confidence）。

以 `references/00-contracts.md` §2.4 产出的 `issue_clusters[]` 为单位计分，防止把一个问题拆成多条来放大分数：

```
每簇权重 w：critical 25 / major 10 / minor 3 / info 0
  （簇内取最高 severity，只计一次）

每个 category 的累计上限：30
  （同一类问题反复出现不应无限累加）

manuscript_risk_score = min(100, Σ_category min(30, Σ_cluster w))
```

**分段仅为筛查信号，不是录用决定**：

| 分数 | 标签（screening recommendation） |
| --- | --- |
| 0–19 | `routine_review` 可进入常规同行评审 |
| 20–49 | `clarification_needed` 建议作者澄清后复审 |
| 50+ | `major_revision_suggested` 建议退回补充 |

出现任一 `critical` 簇时，无论分数如何，`priority_manual_review = true`。

> 阈值**未经实证验证**，是初始经验值。报告中必须注明这一点，
> 且不得表述为自动化的录用/退稿决定。

### 5.2 extraction_coverage · 抽取覆盖率（0.0–1.0）

反映我们**成功抽出了多少应抽的内容**。三个子率加权：

```
field_resolution_rate = |status ∈ {reported, not_reported, not_applicable} 的条件必填字段|
                        / |该 study_design 下的条件必填字段总数|
   （status ∈ {ambiguous, conflicting, parse_failed} 计为未解析）

asset_readability_rate = |asset_inventory 中 readable 的图表数| / |图表总数|

supplement_accessibility = 1.0 若无补充材料或全部可得；
                           否则 |可得补充材料| / |被引用的补充材料总数|

extraction_coverage = 0.60 × field_resolution_rate
                    + 0.25 × asset_readability_rate
                    + 0.15 × supplement_accessibility
```

三个子率必须在报告中**分别列出**，不只给加权结果 —— 覆盖率 0.6 因字段缺失
与因图像不可读，含义完全不同。

### 5.3 review_confidence · 复核置信度（0.0–1.0）

反映**系统对自身审核结论的支撑强度**。

```
pixel_dependency_rate = |证据中含 pixel_estimated 的 finding 数| / max(1, |finding 总数|)
ocr_dependency_rate   = |依赖 OCR 文本的 finding 数| / max(1, |finding 总数|)

Q（证据质量因子）= max(0, 1 - 0.30 × pixel_dependency_rate - 0.20 × ocr_dependency_rate)
C（冲突因子）    = max(0, 1 - 0.10 × min(未消解的 source_value_conflict 数, 5))

review_confidence = extraction_coverage × Q × C
```

`review_confidence < 0.5` 时，报告首屏必须提示"本次审核证据基础较弱，结论仅供参考"。

---

## 6. 输出规范

主输出为 `templates/review_report.md` 渲染的 Markdown，固定七节：

1. **执行摘要** —— 执行模式、三项评分、§0 的声明原文
2. **结构化结果表** —— `structured_result_v2`，每字段带 status 与证据引用
3. **图表解读与原图定位** —— `figure_records[]` / `table_records[]`
4. **审核发现** —— `issue_clusters[]`，按 severity 降序，每条附证据
5. **抽取信号** —— `extraction_signals[]` 及其路由去向
6. **系统限制** —— `system_limitations[]`，即"哪些地方我们没看清"
7. **人工复核建议** —— 按 P0/P1/P2 排序的可执行动作

机器消费时同时输出符合 `schemas/review_report.schema.json` 的 JSON。

非 `full_review` 模式下，未执行阶段对应的节写明"本模式未执行"，**不得**省略节标题
（避免读者误以为该维度无问题）。

---

## 7. 参考文件索引

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| `references/00-contracts.md` | **共享契约**：evidence/locator/extracted_field/三类输出/去重聚簇 | **产出任何结构化内容前** |
| `references/01-structured-extraction.md` | 字段状态模型、研究设计路由、指标族规则、v1/v2、抽取信号 | Stage 2、3b |
| `references/02-macro-logic.md` | 逻辑链校验、章节完整性、数据泄露场景库 | Stage 4 M2 |
| `references/03-experimental-methods.md` | 实验设计惯例库、动物实验必要性判据 | Stage 4 M3 |
| `references/04-statistics.md` | 统计方法选择表、样本量报告、多重比较 | Stage 4 M4 |
| `references/05-figures-and-charts.md` | 图表类型知识库、解析流程、设计规范、正文/supplement 位置适配 | Stage 3、Stage 4 M5 |
| `references/06-ethics-compliance.md` | 伦理批件、知情同意、3R 原则核查 | Stage 4 M6 |
| `references/07-conclusions-discussion.md` | 结论-证据对齐、过度外推识别 | Stage 4 M7 |
| `schemas/*.json` | 全部输出的机器可校验模式 | 输出前自检 |
| `templates/review_report.md` | 报告渲染模板 | Stage 5 |

按需读取，不要一次性全部载入。
