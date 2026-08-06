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

- **针对已存在内容的 finding**：必须给出稿件内 `locator`（见 §3.2），可附原文引用。
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
3. 为每个段落分配 `paragraph_id`，为每张图表分配稳定 id，构造 §3.2 的 locator 对象。
   PDF 输入必须记录 `pdf_file_page`；若能识别印刷页码则同时记录 `printed_page`。
4. 建立 `asset_inventory`：图、表、补充材料清单，逐项标注
   `readable` / `low_resolution` / `inaccessible`。
5. 解析失败（页面无法提取、图像损坏、补充材料不可得）产出 **`system_limitation`**，
   **不是** finding（见 §4.3）。

### 2.5 Stage 2 · M1 结构化抽取

产出 `structured_result_v1`（**仅文本来源**：正文、表格、图注文字）、
`extraction_signals[]`、`extraction_quality_findings[]`。
详细规则见 `references/01-structured-extraction.md`。

**本阶段的三条硬性规则**

- 只抽取论文**明确写出**的内容，**严禁推断填充**。推断出的数值会污染下游全部六个审核模块。
- 每个重要字段使用 §3.3 的 `extracted_field` 结构，`status` 必须显式给出，
  **不得用裸 `null` 编码多种缺失状态**。
- M1 **不做稿件级判断**。M1 只产出 `extraction_signal`（机器级观察），
  由 M2 / M4 / M7 决定其是否构成稿件问题（见 §4.2）。

### 2.6 Stage 3 · 图表解析

对每张图产出 `figure_record`，每张表产出 `table_record`。执行者是 M5 的解析部分，
规则见 `references/05-figures-and-charts.md`。

关键约束（完整规则在 M5 文件）：

- 先确定该图试图回答的**科学问题**，再判断图表类型是否匹配。
- 从图中读出的数值必须带 §3.4 的 `provenance` 对象。
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
   `reporting_completeness` 独立判定（见 §3.5）。
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
**不得**仅凭 `evaluation_matrix` 的摘要值直接产出 finding（见 §5.2）。

### 2.9 Stage 5 · 汇总与输出

1. **去重与聚簇**：按 §4.4 规则把 findings 归并为 issue cluster。
2. **评分**：计算 §6 的三项指标。
3. **人工复核动作**：每一条 `severity >= major` 的 finding 必须对应一条可执行动作，
   写明"看哪里、核什么、若属实该补什么"。
4. **渲染**：按 `templates/review_report.md` 输出 Markdown；需要机器消费时同时输出
   符合 `schemas/review_report.schema.json` 的 JSON。

---

## 3. 证据与字段契约

### 3.1 evidence 对象

`evidence` 是**数组**（一条 finding 可由多处证据支撑）。每个元素为下列两型之一。

**存在型证据**（针对稿件中已有内容）：

```json
{
  "type": "present",
  "locator": {
    "section": "methods", "subsection": "2.4", "paragraph_id": "methods-p17",
    "pdf_file_page": 7, "printed_page": 1043,
    "figure": null, "panel": null, "table": null,
    "supplement_id": null, "xml_id": "para-0042", "scope": "paragraph"
  },
  "quote": "Data are presented as mean ± SEM (n = 3)."
}
```

**缺失型证据**（针对稿件中不存在的内容）：

```json
{
  "type": "absence",
  "scope": "document",
  "searched_locations": [
    {"section": "methods", "scope": "section"},
    {"section": "declarations", "scope": "section"},
    {"supplement_id": "S1", "scope": "supplement"}
  ],
  "search_terms": ["randomization", "random allocation", "randomly assigned", "随机分组"],
  "search_result": "no_match"
}
```

**规则**

- `type: "absence"` 的证据**不得**含 `quote` 字段。绝不为不存在的内容编造引文。
- `searched_locations[]` 与 `search_terms[]` 在 `absence` 型中**必填**，且必须反映实际检索范围。
  检索范围之外的部分不得声称"缺失"，应改用 `system_limitation`。
- `search_result` 取值：`no_match` / `partial_match_ambiguous`。
  后者不足以支撑缺失结论，应改产出 `ambiguous` 状态。

### 3.2 locator 规范

**存储形式为结构化对象**（见 §3.1），字段：

| 字段 | 说明 |
| --- | --- |
| `section` | 归一化章节名，取 Stage 1 的枚举 |
| `subsection` | 小节编号，如 `"2.4"` |
| `paragraph_id` | Stage 1 分配的段落 id |
| `pdf_file_page` | **PDF 文件页码**（从 1 起数的物理页），PDF 输入必填 |
| `printed_page` | **印刷页码**（论文上印的页码），能识别则填，否则 `null` |
| `supplement_page` | 补充材料内页码 |
| `figure` / `panel` | 图号与面板号 |
| `table` | 表号 |
| `supplement_id` | 补充材料标识，如 `"S1"` |
| `xml_id` | JATS/XML 元素 id，XML 输入必填 |
| `scope` | `document` / `section` / `paragraph` / `figure` / `panel` / `table` / `supplement` |

**渲染形式**（仅供报告展示，不作为唯一存储）：由渲染器按
`fig:3B | p.7 | sec:methods§2.4` 拼装。缺失型证据渲染为 `absence:doc:whole`。

**禁止**把自由文本（如 `"Methods §2.4"`）作为 locator 的唯一存储形式。

### 3.3 extracted_field 结构

**所有重要字段**（清单见 `references/01-structured-extraction.md` §3）统一使用：

```json
{
  "value": null,
  "status": "not_reported",
  "evidence": [],
  "extraction_confidence": "high",
  "alternatives": [],
  "candidates": []
}
```

**`status` 枚举（不得自创）**

| status | 含义 | `value` | `evidence` |
| --- | --- | --- | --- |
| `reported` | 稿件明确报告了该值 | 非 null | 至少一条 `present` |
| `not_reported` | **已检索**相关位置，稿件确实未报告 | `null` | 至少一条 `absence` |
| `not_applicable` | 该字段对本研究设计不适用 | `null` | 可为空，需填 `na_reason` |
| `ambiguous` | 存在相关文本但无法唯一解读 | `null` | 至少一条 `present`（指向歧义文本） |
| `conflicting` | 多个来源报告了不兼容的值 | `null` | 每个 `candidates[]` 元素各带证据 |
| `parse_failed` | 内容可能存在，但系统无法可靠抽取 | `null` | 可为空，需关联 `system_limitation.id` |

**关键区分**（下游模块行为完全不同）：

- `not_reported` → 稿件的报告完整性问题，**可以**成为 M2/M4/M6 的 finding 依据。
- `parse_failed` → **系统的**能力问题，**不得**成为稿件 finding，只降低 coverage 与 confidence。
- `ambiguous` / `conflicting` → 产出 signal，由下游模块判定，M1 不下结论。

### 3.4 provenance 对象

所有数值型抽取结果（`key_data[]` 及图表读数）必须带：

```json
{
  "source_type": "figure_caption",
  "source_id": "fig:2C",
  "locator": { "figure": "2", "panel": "C", "pdf_file_page": 5, "scope": "panel" }
}
```

**`source_type` 枚举（全局唯一，所有文件与示例必须一致）**：

```
explicit_main_text | explicit_table | explicit_figure_caption | axis_readable | pixel_estimated
```

> 旧值 `"figure"` / `"text"` / `"figure_axis"` / `"figure_pixel"` 已废弃，见 §D 迁移说明。

**`pixel_estimated` 的强制约束**：`extraction_confidence` 必须为 `low`；
`value` 必须为区间（如 `"40–50"`）而非点值；必须置 `manual_review_needed = true`。

### 3.5 抽取置信度 vs 报告完整性

**两个正交概念，不得合并。**

| 概念 | 字段 | 回答的问题 |
| --- | --- | --- |
| 抽取置信度 | `extraction_confidence`: `high` / `medium` / `low` | 我们对"读出来的这个值就是稿件写的值"有多确定？ |
| 报告完整性 | `reporting_completeness`: `complete` / `incomplete` / `not_applicable` | 稿件对这个数值的报告是否符合该指标族的要求？ |

例：图注写明 `IC50 = 12.4 μM`，但未给拟合方法与置信区间 →
`extraction_confidence: "high"`（我们确信读对了）+ `reporting_completeness: "incomplete"`
（稿件报告不全，是 M4 的 finding 线索）。

---

## 4. 三类输出契约

系统产出三种彼此不可混用的记录。**判断归属的唯一标准：这是稿件的问题，还是我们的观察，还是我们的能力限制？**

### 4.1 finding · 稿件级审核判断

由 M2–M7 产出（M1 只在 §4.5 的受限情形下产出）。

```json
{
  "id": "M4-003",
  "module": "M4",
  "category": "sample_size_reporting",
  "severity": "major",
  "title": "组间比较未报告样本量依据与效应量",
  "detail": "Fig 3B 三组比较使用 one-way ANOVA，各组 n=3 且未说明为生物学或技术重复；正文与方法节均未见效能分析或效应量报告。",
  "evidence": [
    {"type": "present",
     "locator": {"figure": "3", "panel": "B", "pdf_file_page": 7, "scope": "panel"},
     "quote": "Data are presented as mean ± SEM (n = 3)."},
    {"type": "absence", "scope": "document",
     "searched_locations": [{"section": "methods", "scope": "section"},
                            {"section": "results", "scope": "section"}],
     "search_terms": ["power analysis", "sample size", "effect size", "样本量"],
     "search_result": "no_match"}
  ],
  "rule_ref": "04-statistics#sample-size-reporting",
  "review_confidence": "high",
  "related_findings": [],
  "manual_review": {
    "action": "核对 n=3 指生物学重复还是技术重复；要求作者补充效能分析或效应量",
    "who": "statistical_reviewer"
  }
}
```

**枚举（不得自创）**

- `severity`: `critical`（结论不成立 / 伦理违规 / 疑似不端）> `major`（需作者补充材料或重做分析）
  > `minor`（表述与规范问题）> `info`（提示）
- `review_confidence`: `high` / `medium` / `low` —— 指**本条判断本身**的可靠程度。
  依赖 `pixel_estimated` 证据或 `ambiguous` 字段的 finding，上限为 `medium`。
- `category`: 必须是该模块 reference 文件中已登记的 slug。
- `manual_review.who`: `statistical_reviewer` / `domain_reviewer` / `ethics_committee` /
  `editor` / `author`。

**硬性规则**

- `severity >= major` 的 finding **必须**有非空 `manual_review.action`。
- **解析失败不得赋予稿件 severity。** 任何源于 `parse_failed` 的情形一律走 §4.3。

### 4.2 extraction_signal · 机器级观察

由 M1（Stage 2）与 Stage 3b 产出。**signal 不是结论，是待下游解读的观察。**

```json
{
  "id": "SIG-002",
  "type": "source_value_conflict",
  "target": "key_data.KD-007",
  "detail": "IC50 在图注为 12.4 μM，在 Results 正文为 15.1 μM，两者置信区间不重叠。",
  "candidates": [
    {"value": 12.4, "unit": "μM",
     "provenance": {"source_type": "explicit_figure_caption", "source_id": "fig:2C",
                    "locator": {"figure": "2", "panel": "C", "pdf_file_page": 5, "scope": "panel"}}},
    {"value": 15.1, "unit": "μM",
     "provenance": {"source_type": "explicit_main_text", "source_id": "results-p8",
                    "locator": {"section": "results", "paragraph_id": "results-p8",
                                "pdf_file_page": 6, "scope": "paragraph"}}}
  ],
  "routed_to": ["M2"]
}
```

**`type` 枚举**

| type | 触发条件 | 路由到 | 下游判定什么 |
| --- | --- | --- | --- |
| `source_value_conflict` | 同一字段多来源数值不兼容 | M2（主）、M4 | 是否构成稿件内部矛盾 |
| `claim_without_resolved_evidence_link` | claim 的 `supported_by` 无法解析到任何证据 | M7 | 是否构成无支撑主张 / 过度外推 |
| `ambiguous_study_design` | 研究设计线索冲突或不足以唯一归类 | M2、M3、M4、M6 | 是否构成设计描述不清 |
| `unresolved_cross_reference` | 正文引用的图/表/补充材料无法解析到实体 | M2、M5 | 是否构成引用错误 |
| `partial_extraction` | 字段部分抽出（如有 n 无分组归属） | M4、M5 | 是否构成报告不完整 |
| `parse_failure` | 抽取因技术原因失败 | **不路由到审核模块** | 仅关联 `system_limitation` |

**规则**：signal **不得**带 `severity`。下游模块若据此立 finding，必须在该 finding 的
`evidence[]` 中**独立**给出稿件证据，不得仅引用 signal id。

### 4.3 system_limitation · 系统能力限制

```json
{
  "id": "SYS-004",
  "category": "figure_unreadable",
  "impact": "M4 与 M5 对 Figure 4 的审核不完整",
  "affected_modules": ["M4", "M5"],
  "affected_targets": ["fig:4"],
  "evidence": [
    {"type": "present",
     "locator": {"figure": "4", "pdf_file_page": 9, "scope": "figure"}}
  ],
  "recommended_action": "调取原始高分辨率图件或矢量 PDF 后重新解析"
}
```

**`category` 枚举**：`parse_failed` / `figure_unreadable` / `table_unparseable` /
`supplement_inaccessible` / `section_missing_from_input` / `ocr_low_quality` /
`encoding_error` / `input_truncated`。

**硬性规则**

- `system_limitation` **没有 `severity` 字段**。它不是稿件问题。
- 它**降低** `extraction_coverage` 与 `review_confidence`，
  **不降低** `manuscript_risk_score`（见 §6）。
- 报告中必须单列一节，让人看到"哪些地方我们没看清"。

### 4.4 去重与聚簇

Stage 5 执行，顺序固定：

1. **同模块内合并**：同一模块内 `category` 相同且 `evidence` 主锚点
   （第一条 `present` 证据的 `locator`，比较 `figure`+`panel` 或 `paragraph_id`）相同的
   findings，合并为一条，保留 `severity` 最高者，其余进 `related_findings[]`。
2. **跨模块聚簇**：不同模块命中同一主锚点且语义重合时，构成一个 `issue_cluster`。
   保留 `severity` 最高的一条为簇代表，其余挂 `related_findings[]`。
   **不要把同一个问题报告六遍。**
3. **簇内证据合并**：簇代表的 `evidence[]` 并入各成员的证据，去重后保留。

聚簇结果 `issue_clusters[]` 是 §6.1 评分的输入单位。

### 4.5 M1 可以产出的 finding（严格受限）

M1 **仅**可产出**抽取质量类** finding，且这类 finding **只影响系统覆盖率与复核置信度，
不直接降低稿件风险分**：

| category | 触发 | 影响 |
| --- | --- | --- |
| `ambiguous_extraction` | 字段 `status: ambiguous` | 降 coverage / confidence |
| `required_field_unresolved` | 条件必填字段最终为 `ambiguous`/`conflicting`/`parse_failed` | 降 coverage / confidence |

`parse_failed` 与 `unreadable_figure` **不走 finding**，走 §4.3 `system_limitation`。

M1 **不得**产出 `unsupported_claim`、`internal_inconsistency`、`missing_ethics_statement`
等稿件级判断 —— 这些分别属于 M7、M2、M6。

---

## 5. 结构化结果与路由

### 5.1 structured_result 的两个版本

| 版本 | 产出者 | 内容 | 谁能用 |
| --- | --- | --- | --- |
| `structured_result_v1` | Stage 2 (M1) | **仅文本来源**的抽取结果 | 仅 Stage 3（作上下文）与 Stage 3b |
| `structured_result_v2` | Stage 3b | 合并图表来源、完成冲突消解后的结果 | **M2–M7 全部** |

**M2–M7 一律消费 `v2`。** 直接读 `v1` 会漏掉全部图表来源数值。

### 5.2 evaluation_matrix 的正确用法

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

## 6. 三项评分（互不替代）

**禁止**把稿件风险分称作"置信度"。三项分别输出，报告中不得合并为单一数字。

```json
{
  "manuscript_risk_score": 34,
  "extraction_coverage": 0.82,
  "review_confidence": 0.71
}
```

### 6.1 manuscript_risk_score · 稿件风险分（0–100，越高风险越大）

反映**已验证的稿件 finding** 的严重度与范围。
**不因 PDF 不可读或解析失败而升高**（那属于 coverage 与 confidence）。

以 §4.4 的 `issue_clusters[]` 为单位计分，防止把一个问题拆成多条来放大分数：

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

### 6.2 extraction_coverage · 抽取覆盖率（0.0–1.0）

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

### 6.3 review_confidence · 复核置信度（0.0–1.0）

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

## 7. 输出规范

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

## 8. 参考文件索引

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
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
