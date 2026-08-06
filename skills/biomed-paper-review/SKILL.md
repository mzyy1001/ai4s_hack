---
name: biomed-paper-review
description: 生物医药论文结构化抽取与审稿辅助。输入一篇论文（PDF / JATS XML / 纯文本），输出结构化证据表、图表解读与原图定位、多维审核发现、抽取覆盖率与复核置信度，以及分优先级的人工复核建议。支持四种执行模式（完整审核 / 仅结构化抽取 / 图表解析 / 定向核查）。当用户需要预审、复核生物医药论文或稿件，或需要抽取论文中的实验条件、剂量响应曲线、统计图、实验流程图、显微图的关键数值时使用。
---

# 生物医药论文审稿辅助 Skill

## 0. 定位与边界

**做什么**：自动化并辅助审稿的**基础性工作** —— 结构化证据抽取、图表解读、
报告规范核查，以及为专家复核排定优先级。

**明确声明（必须原样写入每份输出报告）**：

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查
> 与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。**
> 本 Skill 的任何评分均为筛查信号（screening / triage signal），
> 不构成录用、退稿或发表决定。

### 0.1 核心原则：证据可审计

**每一条稿件级 finding 都必须有可审计的证据支撑。** 针对**已存在内容**给出 `present`
证据（含结构化 locator）；针对**缺失内容**给出 `absence` 证据（显式检索范围 + 检索词 +
检索结果），**绝不为不存在的内容伪造引文**。证据的规范存储是**证据登记表**
`evidence_registry`，一切引用位置只存 `evidence_refs[]`（`references/00-contracts.md §1`）。
给不出上述任一种证据的判断一律丢弃 —— 这是本 Skill 与「大模型泛泛点评」的根本区别。

### 0.2 当前实现边界与联网增强原则

执行环境允许访问白名单内的公开科学数据源，网络与 12 小时超时**不再构成分期依据**。
当前提交包已定义论文内部证据与通用规范库的离线流程，并交付四项可独立运行的确定性脚本；
外部 evidence 契约与解析层尚未落地，因此本版本**不得声称已完成外部数据库核验**。
后续一期可加入可选联网增强；外部源不可达、
限流或无权访问时必须产 `system_limitation`，不得据此判稿件有问题，离线流程仍须完整结束。

| 能力 | 当前离线做法 | 一期联网增强归属 | 接入前置条件 |
| --- | --- | --- | --- |
| 判断结论在科学上是否**为真** | 只做 claim↔evidence 对齐 | M7 | 文献库 MCP（PubMed / Europe PMC） |
| 判断领域**创新性 / 重要性** | 不判断 | M7 | 文献库 + 引用网络；需先定义可量化新颖度判据 |
| 判断违背基础常识的结论 | 标记「结论超出证据支持范围」交人工 | M7 | 领域常识规则库；先积累一期误判样本 |
| 复现统计计算 | 已做 p/CI/计数/GRIM 四类无需原始数据的一致性取证 | M4 | 原始数据可得时重跑主要分析 |

联网增强应**扩展**而非重构主框架：新增 `database` / `query` / `retrieval_date` / `record_id` / `version` /
`retraction_or_correction_status` / `relation_to_claim` 等元数据。外部证据型与唯一产出阶段
尚未进入当前 schema；完成契约迁移前不得声称已核验外部数据库。

## 1. 执行模式与依赖图

**先判定执行模式，再进入流水线。** 默认 `full_review`；用户只要一张图或一个数值时，
**不得**自动跑完整审核。

**总原则：任何阶段不得消费尚未产出的产物。** 每个模式必须在输出中声明
`execution_scope`（`references/00-contracts.md` §7.1），
其中 `executed_stages[]` 是消费权限的白名单。

### 1.1 `full_review`

```
Stage 1 → Stage 2 → Stage 3 → Stage 3b → Stage 4 (M2–M7) → Stage 5
```

输出：`review_report`、`structured_result_v2`、`figure_records[]`、`table_records[]`、
`issue_clusters[]`、`all_extraction_signals[]`、`all_system_limitations[]`、
`manuscript_risk_score`（`partial: false`）、`extraction_coverage`、`review_confidence`。
这是唯一产出**非 partial** 风险分的模式。

### 1.2 `structured_extraction`

触发：用户只要「抽取关键信息 / 结构化结果表」。

```
Stage 1
→ Stage 2
→ [条件] scoped Stage 3    仅当被请求字段依赖视觉证据
→ [条件] scoped Stage 3b   仅当上一步执行了
→ 输出装配
```

**规则**

- 无视觉需求 → 输出 **`structured_result_v1`** + `stage_3b_executed: false`；
  执行了 scoped Stage 3 + 3b → 输出 **`structured_result_v2`** + `stage_3b_executed: true`。
  **不得**把 v1 冒充 v2。v1 中允许保留 `status: "unresolved"`，
  但必须计入 `coverage_breakdown.unresolved_required_fields[]`。
- **不跑 M2–M7**，**不输出** `manuscript_risk_score`。
- 置信度用 **`output_confidence`**，不用 `review_confidence` —— 没做审核就没有审核置信度。

### 1.3 `figure_analysis`（两个 submode，必须显式声明）

#### 1.3.1 `interpretation_only` —— 只解读，不评判

触发：用户指定某几张图要「看懂它在说什么 / 读出数值」。

```
Stage 1 → scoped Stage 3 → 输出装配
```

**规则**

- **不跑 Stage 2**，**不跑 Stage 3b**（除非用户明确要求把读数合并回结构化字段；
  合并即需先跑最小 Stage 2 以提供 `structured_result_v1`）。
- 产出 `figure_records[]` / `table_records[]`。
- **不产出任何 M5 稿件级 finding**，**不产出** `manuscript_risk_score`。
- 置信度用 **`output_confidence`**。

#### 1.3.2 `figure_review` —— 解读 + 图表使用规范审核

触发：用户要求「审一下图表是否规范 / 图用得对不对」。

```
Stage 1
→ Stage 2 (minimal context)   仅抽取 study_design、endpoint、arms、statistical_methods
→ scoped Stage 3
→ scoped Stage 3b
→ Stage 4: 仅 M5
→ Stage 5 (partial aggregation)
```

**规则**

- 最小 Stage 2 是 Stage 3b 的前置 —— 没有 `structured_result_v1` 就无从合并。
- 产出 M5 finding 与 partial `issue_clusters[]`。
- `manuscript_risk_score.partial = true`，`comparable_to_full_review = false`。
- 置信度用 **`review_confidence`**（跑了审核模块）。

### 1.4 `targeted_check`

触发：用户提出具体问题（「样本量够不够」「伦理声明齐全吗」）。

```
Stage 1
→ Stage 2
→ [条件] scoped Stage 3    问题依赖图表，或 v1 的 scope 内存在 `unresolved`
→ scoped Stage 3b
→ Stage 4: 仅选定模块
→ Stage 5 (partial aggregation)
```

**规则**

- scoped Stage 3b 始终执行。若 v1 的 scope 内存在 `unresolved`，必须先执行
  覆盖其 `expected_sources[]` 的 scoped Stage 3；仅当 scope 内没有 `unresolved` 时才可跳过
  Stage 3。**未尝试视觉来源不得把 pending 收敛为 `not_reported` 或 `parse_failed`。**
- 输出**必须**列明 `executed_stages[]` / `executed_modules[]` / `skipped_modules[]` /
  `execution_scope`。
- `manuscript_risk_score.partial = true`，禁止与 `full_review` 分数并列比较。
- 置信度用 **`review_confidence`**。

### 1.5 模式约束速查

| 模式 / submode | 跑审核模块 | risk_score | 置信度字段 | 主结构化产物 |
| --- | --- | --- | --- | --- |
| `full_review` | M2–M7 | 完整 | `review_confidence` | `structured_result_v2` |
| `structured_extraction` | 无 | **不输出** | `output_confidence` | v1 或 v2（见 §1.2） |
| `figure_analysis / interpretation_only` | 无 | **不输出** | `output_confidence` | 无（仅 records） |
| `figure_analysis / figure_review` | 仅 M5 | partial | `review_confidence` | `structured_result_v2` |
| `targeted_check` | 选定模块 | partial | `review_confidence` | `structured_result_v2` |

`review_confidence` 与 `output_confidence` **互斥，不得同时输出**。任何模式都必须输出
`execution_scope`、`coverage_breakdown`、`extraction_coverage`、`all_system_limitations[]`。

## 2. 流水线

### 2.1 模块关系（不要说错）

本 Skill 含**七个分析模块**：**M1 是前置抽取层，M2–M7 是并行审核模块。**

M2–M7 全部消费 M1（经 Stage 3b 合并后）的产物，因此 **M1 与 M2–M7 不是并行关系**。
只有在 Stage 2 与 Stage 3b 完成之后，M2–M7 才可并行执行。
可以说「一个抽取层 + 六个审核模块」，**不要**说「七个模块相互独立」。

### 2.2 Figure Parser 与 M5 Reviewer 是两个执行角色

两者共用 `references/05-figures-and-charts.md`，但**执行位置与产物完全不同**：

| 角色 | 阶段 | 产物 | 产出 finding |
| --- | --- | --- | --- |
| **Figure Parser** | Stage 3 | `figure_records[]`、`table_records[]`、`stage3_system_limitations[]` | **否** |
| **M5 Figure-Use Reviewer** | Stage 4 | `m5_findings[]`（图型选择、标注、一致性、位置、报告规范） | 是 |

**不得**说「Stage 3 产出 M5 findings」—— Stage 3 只解读，不评判。

### 2.3 阶段与阶段本地产物

```
Stage 1  文档归一化与切分   └─> normalized_document, asset_inventory,
                                stage1_system_limitations[], evidence_registry（开始登记）
Stage 2  M1 结构化抽取      └─> structured_result_v1, m1_extraction_signals[],
                                stage2_system_limitations[]
Stage 3  图表解析(Parser)   └─> figure_records[], table_records[], stage3_system_limitations[]
Stage 3b 合并与冲突消解     └─> structured_result_v2, merge_extraction_signals[],
                                stage3b_system_limitations[]
Stage 4  M2–M7 并行审核     └─> m2_findings[] … m7_findings[]
Stage 5  聚合评分渲染       └─> all_extraction_signals[], all_system_limitations[],
                                all_findings[], issue_clusters[], 三项评分, review_report
```

### 2.4 产出者与聚合器（每个数组恰好一个）

**跨阶段同名数组一律拆为阶段本地数组，由 Stage 5 单一聚合。**
非 `full_review` 模式下，聚合职责由「输出装配」步骤承担，规则相同。

| 产物 | 唯一产出者 / 聚合器 | 主要消费者 |
| --- | --- | --- |
| `normalized_document` | Stage 1 | Stage 2, Stage 3, M2 |
| `asset_inventory` | Stage 1 | Stage 3, Stage 5（覆盖率） |
| `evidence_registry` | Stage 1 建立，各阶段**追加**（id 全局递增，不改已有条目） | 全部 |
| `structured_result_v1` | Stage 2 (M1) | Stage 3（上下文）, Stage 3b |
| `m1_extraction_signals[]` | Stage 2 (M1) | Stage 5 聚合 |
| `figure_records[]` / `table_records[]` | Stage 3 (Figure Parser) | Stage 3b, M4, M5, M7 |
| `structured_result_v2` | Stage 3b | **M2–M7 全部** |
| `merge_extraction_signals[]` | Stage 3b | Stage 5 聚合 |
| `stage{1,2,3,3b}_system_limitations[]` | 对应阶段 | Stage 5 聚合 |
| `m2_findings[]` … `m7_findings[]` | 对应审核模块 | Stage 5 |
| `all_extraction_signals[]` | **Stage 5** 聚合 `m1_` + `merge_` | 报告 |
| `all_system_limitations[]` | **Stage 5** 聚合四个 stage-local | 报告 |
| `execution_scope` | **执行规划步骤（Stage 1 前初始化）**；条件阶段触发时由同一步骤先更新再执行 | 全阶段（消费白名单与评分分母） |
| `all_findings[]` / `issue_clusters[]` / `coverage_breakdown` / `review_report` | **Stage 5** | 评分、报告、用户 |

### 2.5 Stage 1 · 文档归一化与切分

1. 判定输入类型：JATS/PMC XML（最优）> PDF > 纯文本。
2. 切分标准章节：`title / abstract / introduction / methods / results / discussion /
   conclusion / declarations / ethics / funding / conflict_of_interest /
   data_availability / references / supplement`。章节缺失**不在本阶段判定为问题**，
   只写入 `asset_inventory.missing_sections[]`，由 M2 结合刊型决定。
3. 为每段分配 `paragraph_id`、每张图表分配稳定 id；PDF 输入必须记录 `pdf_file_page`，
   能识别印刷页码则同时记录 `printed_page`。初始化 `evidence_registry`。
4. 建立 `asset_inventory`：图、表、补充材料清单，逐项标注
   `readable` / `low_resolution` / `inaccessible`。
5. 解析失败产出 **`stage1_system_limitations[]`**，**不是** finding。

### 2.6 Stage 2 · M1 结构化抽取

产出 `structured_result_v1`（**仅文本来源**：正文、表格、图注文字）。
详细规则见 `references/01-structured-extraction.md`。四条硬性规则：

- 只抽取论文**明确写出**的内容，**严禁推断填充** —— 推断值会污染下游六个模块。
- 每个重要字段使用 `extracted_field` 结构，`applicability` / `requiredness` / `status`
  三者**分别显式给出**，不得用裸 `null` 编码多种缺失状态。
- **M1 不产出任何 `finding`。** M1 只产出 `extraction_signal`（机器级观察），
  由 M2 / M4 / M7 决定其是否构成稿件问题。
- 文本没有、但图里可能有的字段判 `status: "unresolved"` +
  `resolution_state.state = "pending_visual_resolution"`，**不判 `parse_failed`**
  —— Stage 3 尚未尝试，谈不上失败。

### 2.7 Stage 3 · 图表解析（Figure Parser）

每个可独立解读的 panel 产出一条 `figure_record`；只有共享科学问题、坐标与图型且不可独立解释时才按整图产出。每张表产出 `table_record`。
规则见 `references/05-figures-and-charts.md`。关键约束：

- Figure Parser 只记录**科学问题**、图型、条件、坐标与可见结果；**图型是否匹配、呈现是否规范只由 Stage 4 的 M5 判断**。
- 从图中读出的数值必须带 `provenance`（含 `derivation`）。
- **像素估读一律 `pixel_estimated` + `interval` + `low` + `manual_review_needed: true`**；仅图像边界只能支持单侧约束时可用 `lower_bound` / `upper_bound`，不得编造点值。
- `curve_fit` 与 `significance_markers` 只是 panel 注释；任何拟合参数、p 值或其他定量结果若要进入审核，必须同时写入 `observations[]`。
- 图像不可读产出 `stage3_system_limitations[]`（`figure_unreadable`），不是 finding。

### 2.8 Stage 3b · 证据合并与冲突消解

**数据流的关键一环：图表解析结果必须回流，`structured_result_v1` 不得直接交给 M2–M7。**

1. **收敛 pending** —— 每个 `status: "unresolved"` 必须解析为 `reported` /
   `not_reported` / `ambiguous` / `conflicting` / `parse_failed`。
   **v2 中不得残留 `unresolved`。**
2. **观测分组** —— 对 `figure_record.observations[]`，先比较 `metric_family + metric_name`，再逐项比较 `target_grouping_key` 与 `key_data.grouping_key` 五键。完全相同则并入，否则新建组，**不得猜配或判冲突**。入组时移除临时路由字段，保持 `observation_id`、`value`、`provenance`；同一 id 的重复副本不一致时终止入组，产出
   `category: "parse_failed"` 的 Stage 3b `system_limitation`，不得择一覆盖。
3. **兼容性判定** —— 单位归一化 → 变体兼容 → 区间重叠 → 四舍五入容差 → 单边界。
   **四舍五入差异不得判为冲突**；无法建立可比性判 `ambiguous`，不判 `conflicting`。
4. **canonical 选择** —— `explicit_reported` 优先于 `visually_derived`；其内部按
   「主要结果 → 带不确定度 → 精度 → 非叙述性摘要 → 要素齐全 → 字典序」有序判据。
   **给不出可辩护选择时 `canonical_observation = null`，组判 `ambiguous`。**
5. **保全** —— 全部 observation 保留，**禁止静默覆盖**。不兼容时产出
   `source_value_conflict` signal，交 M2 判定。
6. **claim 链接** —— `claims[].supported_by` 解析不到任何 `key_data.id` 或证据的，
   产出 `claim_without_resolved_evidence_link` signal（`target` 携带 `claim_id`
   与 `unresolved_refs[]`），交 M7 判定。**M1 与 Stage 3b 都不下这个结论。**

完整判定规则见 `references/00-contracts.md` §5.4 与 §5.5。

### 2.9 Stage 4 · M2–M7 并行审核

**前置条件：Stage 2 与 Stage 3b 均已完成。** 六个审核模块此时可并行执行，
各自读取自己的 reference 文件，消费 `structured_result_v2`、`figure_records[]`、
`all` 之前的 stage-local signals，输出统一格式的 `finding`。

| # | 模块 | 负责人 | 规则文件 | 核心问题 |
| --- | --- | --- | --- | --- |
| M1 | 结构化抽取（**前置层，非审核模块，不产 finding**） | MZYY（陈泓睿） | `references/01-structured-extraction.md` | 关键信息是否完整、可溯源地抽出？ |
| M2 | 宏观逻辑与格式 | ZY（卓妍） | `references/02-macro-logic.md` | 逻辑链是否闭环？章节是否完整？有无数据泄露、前后矛盾？ |
| M3 | 实验方法合规性 | Peter | `references/03-experimental-methods.md` | 方法有无 reference 依据？动物实验是否必要？ |
| M4 | 统计学方法 | JY（蒋运） | `references/04-statistics.md` | 统计方法是否匹配数据类型？样本量与多重比较是否充分？ |
| M5 | 图表使用规范（Reviewer 角色） | MY（敏怡） | `references/05-figures-and-charts.md` | 图表类型是否匹配研究目的？呈现与位置是否规范？ |
| M6 | 伦理合规 | Peter | `references/06-ethics-compliance.md` | 动物/人体试验是否合规？有无批件号与知情同意？ |
| M7 | 结论与讨论 | MY（敏怡） | `references/07-conclusions-discussion.md` | 结论是否被本文数据支持？有无过度外推、避谈局限？ |

**模块路由**：各模块依据 `structured_result_v2.article_design` 与 `evaluation_matrix`
决定跑哪些规则集。路由字段仅用于**选择规则**与**定位证据**，
**不得**仅凭 `evaluation_matrix` 的摘要值直接产出 finding（见 §4.2）。

### 2.10 Stage 5 · 聚合与输出

1. **聚合**：按 §2.4 合并 stage-local 数组为 `all_*`。
2. **去重与聚簇**：按 `references/00-contracts.md` §9.3 归并为 `issue_clusters[]`。
3. **评分**：计算 §5 的三项指标，分母全部取自 `execution_scope`。
4. **人工复核动作**：每一条 `severity >= major` 的 finding 必须对应一条可执行动作，
   写明「看哪里、核什么、若属实该补什么」。报告级 `manual_review_plan` 按 P0 → P1 →
   P2、severity 降序、finding id 升序排列；P0/P1/P2 的唯一口径见 §6。
5. **渲染**：按 `templates/review_report.md` 输出 Markdown；需要机器消费时同时输出
   符合 `schemas/review_report.schema.json` 的 JSON（含完整 `evidence_registry`）。

## 3. 契约总览（详见 `references/00-contracts.md`）

**需要输出任何结构化内容前必须先读该文件。** 此处只列必须随时记住的要点。

### 3.1 证据（§1）

证据存于 `evidence_registry`，各处只写 `evidence_refs[]`，每个 ref 必须解析到
**恰好一个**登记条目，否则该 finding 无效。`present` 型必填 `locator` 对象；
`absence` 型必填 `searched_locations[]` + `search_terms[]` + `search_result`，
且**禁止**含 `quote` 或 `locator`。

### 3.2 字段的三个正交维度（§3）

```
applicability : applicable | not_applicable | applicability_uncertain
requiredness  : required | recommended | optional
status        : reported | not_reported | not_applicable | ambiguous
                | conflicting | parse_failed | unresolved
```

**适用性 ≠ 必填性** —— 不得因为某字段不进覆盖率分母就判 `not_applicable`。
`not_reported`（**稿件**没写，已检索确认）**可以**成为 finding 依据；
`parse_failed`（**我们**没读出来）**绝不可以**，只降覆盖率。
`unresolved` 只允许存在于 v1。`extraction_confidence`（我们读对了吗）与
`reporting_completeness`（稿件报全了吗）**正交**，不得互相传染。

### 3.3 数值（§2）

一律用带 `type` 的对象：`point` / `interval` / `lower_bound` / `upper_bound` / `categorical`。
**禁止**裸数字与字符串区间（`"40–50"` 非法）。
`provenance.source_type` 五值，**且必须带 `derivation`**（否则 pixel/OCR 依赖率算不出来）：

```
explicit_reported  = explicit_main_text | explicit_table | explicit_figure_caption
visually_derived   = axis_readable | pixel_estimated
```

`pixel_estimated` 强制 `interval` + `extraction_confidence: low` +
`manual_review_needed: true`，且**不得**用于任何统计复算。

### 3.4 三类记录（§6，不可混用）

| 契约 | 产出者 | 含 severity | 影响 |
| --- | --- | --- | --- |
| `finding` | **仅 M2–M7** | ✅ `critical`/`major`/`minor`/`info` | 稿件风险分 |
| `extraction_signal` | Stage 2、Stage 3b | ❌ | 路由给下游判定，本身不是结论 |
| `system_limitation` | Stage 1/2/3/3b | ❌ | 只降覆盖率与置信度 |

**M1 不产出 finding。** `coverage_breakdown` 与 `execution_scope` **不是记录**，
其条目不得称为 finding。**解析失败不得赋予稿件 severity。**
下游据 signal 立 finding 时，必须在 `evidence_refs[]` 中独立给出稿件证据，
不得仅引用 signal id。

## 4. 结构化结果与路由

### 4.1 v1 与 v2

| 版本 | 产出者 | 内容 | 谁能用 |
| --- | --- | --- | --- |
| `structured_result_v1` | Stage 2 (M1) | **仅文本来源**，可含 `unresolved` | Stage 3（上下文）、Stage 3b；`structured_extraction` 无视觉需求时可直接输出 |
| `structured_result_v2` | Stage 3b | 合并图表来源、消解冲突、**无 `unresolved` 残留** | **M2–M7 全部** |

**M2–M7 一律消费 v2。** 直接读 v1 会漏掉全部图表来源数值。

### 4.2 evaluation_matrix 的正确用法

`evaluation_matrix` 是**路由与索引**工具，每个条目是状态感知对象而非裸布尔
（`{status, applicability, requiredness, applies_to[], evidence_refs[],
extraction_confidence}`，见 `01-structured-extraction.md §11`）：

1. **可以**用它决定跑哪些规则集、定位相关证据。
2. **不得**仅凭它直接立 finding —— M2–M7 必须回查 `evidence_refs`，
   在自己的 finding 中独立给出 `evidence_refs[]`。
3. 实验级字段**不得**压缩为单一数字，用 `group_sizes[]` 保留实验级上下文。

### 4.3 研究设计路由

设计存为 `article_design`，区分「文章主设计」`primary_design` 与
「实验级设计」`design_components[]`（每项带 `experiment_id` + `family` + `type`）。

**适用性路由优先级（命中即停）**：

```
实验级类型规则 > 文章级专门规则 > 族级规则 > 默认规则
```

一篇论文**真的**含多种设计时用 `design_components[]`；
`alternatives[]` **只**用于「抽取器在几种解读之间不确定」。二者不得混用。
完整枚举、字段清单与各设计的适用性规则见 `references/01-structured-extraction.md` §4–§5。

## 5. 三项评分（互不替代）

**禁止**把稿件风险分称作「置信度」。三项分别输出，不得合并为单一数字。
完整公式与可计算性证明见 `references/00-contracts.md` §8。
当前权重、category 上限、分段阈值、惩罚系数与 `0.5` 提示阈值均为**未经语料标定的
初始专家参数**；公式可复算不等于参数已有实证效度。报告不得把这些数值表述为概率、
校准后的质量测量或录用/退稿界值。

### 5.1 manuscript_risk_score（0–100，越高风险越大）

以 `issue_clusters[]` 为单位计分（防止一个问题拆成多条放大分数），
**不因**解析失败而升高：

```
每簇权重 w：critical 25 / major 10 / minor 3 / info 0（簇内取最高 severity，只计一次）
manuscript_risk_score = min(100, Σ_category min(30, Σ_cluster w))    每 category 上限 30
```

未跑满六个审核模块时**必须**标 `partial: true` + `comparable_to_full_review: false`，
并列出 `executed_modules[]` / `skipped_modules[]`；partial 分数**禁止**与完整分数比较，
其 `band` 固定为 `partial_not_classified`，不得套用完整审核的三个分段。
`executed_modules` 为空时**不输出本项**。分段（`routine_review` 0–19 /
`clarification_needed` 20–49 / `major_revision_suggested` 50+）**仅为筛查信号，
且只适用于 `partial: false`；阈值未经实证验证，报告中必须注明，不得表述为录用/退稿决定。
出现任一 `critical` 簇时 `priority_manual_review = true`。

### 5.2 extraction_coverage（0.0–1.0）

**全部分母取自 `execution_scope`** —— 单图任务不得用全文分母。

```
field_resolution_rate    = |scope 内 applicable ∧ required ∧ status ∈ {reported, not_reported}|
                         / |scope 内 applicable ∧ required|
asset_readability_rate   = |scope 内 readable 图表| / |scope 内图表|          （分母 0 → 1.0）
supplement_accessibility = |scope 内可得补充材料| / |scope 内被引用补充材料|  （分母 0 → 1.0）

extraction_coverage = 0.60 × field_resolution_rate + 0.25 × asset_readability_rate
                    + 0.15 × supplement_accessibility
```

三个子率必须**分别列出显式分子分母** —— 覆盖率 0.6 因字段缺失与因图像不可读，
含义完全不同。`requiredness = recommended` 的字段可另报
`recommended_field_coverage`，**不进**加权。

### 5.3 review_confidence 与 output_confidence（互斥）

**跑过至少一个审核模块**用 `review_confidence`；一个都没跑用 `output_confidence`。

```
output_confidence = extraction_coverage × max(0, 1 − 0.30 × pixel_share − 0.20 × ocr_share)

review_confidence = extraction_coverage × Q × C
  Q = max(0, 1 − 0.30 × pixel_dependency_rate − 0.20 × ocr_dependency_rate
                − 0.10 × low_conf_finding_rate)
  C = max(0, 1 − 0.10 × min(未消解 conflicting 组数, 5))
```

scope 内 observation 由 `execution_scope.observations[]` 唯一圈定；变量均可从 `provenance.source_type`、
`provenance.derivation.ocr_used`、`finding.evidence_refs[]`、`finding.review_confidence`、`key_data.status` 直接算出（`00-contracts.md §8.3`）。
`review_confidence < 0.5` 时，报告首屏必须提示「本次审核证据基础较弱，结论仅供参考」。

## 6. 输出规范

主输出为 `templates/review_report.md` 渲染的 Markdown，固定八节：
①**执行摘要**（范围、三项评分、partial、前三条 P0/P1）；②**结构化结果表**（v1/v2、
三维度、定位）；③**图表解读与原图定位**；④**审核发现**（每簇一次）；⑤**抽取信号**
（明示非稿件问题）；⑥**系统限制**（明示非作者问题）；⑦**覆盖率明细**（显式分子分母）；
⑧**人工复核建议**（动作、执行者、finding、展开证据）。详细渲染算法以模板注释为准。
**证据必须解析，禁止只打印 `EV-*`：** `present` 按 PDF 物理页→印刷页→章节/段落/XML→
图/表/补充材料输出非 null 定位与至多 300 字摘录；无 quote 明示按定位核对。`absence` 只显示
检索范围、检索词与结果。ref 不存在或不唯一即渲染失败。
**排序：** cluster 按 critical→major→minor→info、id 排序且 finding 不重复；计划按
P0→P1→P2、关联 finding 最高 severity、首个 finding id 排序。
**优先级：** P0=形成审稿结论前必须核对的核心结论/伦理授权/数据完整性阻断项（全部
critical 及直接阻断核心解释的 major）；P1=给出修改要求前核对的其他 major；P2=不改变核心
推断的 minor/info 澄清。它是核对顺序，不是 severity，不进风险分。critical/major 必须入
`manual_review_plan`；minor/info 仅在 priority=P2 且 action 非空时进入；渲染其证据并集。
机器消费时同时输出符合 schema 且内含完整 `evidence_registry` 的 JSON。八节不得省略；
`structured_extraction`/`interpretation_only` 明示未审核，`figure_review` 明示仅 M5，
`targeted_check` 明示仅 `executed_modules[]`；零 finding 只能写「已执行范围内未产出」。

## 7. 参考文件索引（按需读取，不要一次性全部载入）

| 文件 | 内容 | 何时读取 |
| --- | --- | --- |
| `references/00-contracts.md` | **共享契约**：证据登记表、数值变体、字段三维度、观测组、三类记录、执行范围、评分、聚合聚簇、迁移表、lint 清单 | **产出任何结构化内容前** |
| `references/01-structured-extraction.md` | 字段清单与适用性规则、设计路由、指标族、v1/v2、抽取信号、evaluation_matrix | Stage 2、3b |
| `references/02-macro-logic.md` | 逻辑链校验、章节完整性、数据泄露场景库 | Stage 4 M2 |
| `references/03-experimental-methods.md` | 实验设计惯例库、动物实验必要性判据 | Stage 4 M3 |
| `references/04-statistics.md` | 统计方法选择表、样本量报告、多重比较 | Stage 4 M4 |
| `references/05-figures-and-charts.md` | 图表类型知识库、Stage 3 解析流程、M5 审核规范 | Stage 3、Stage 4 M5 |
| `references/06-ethics-compliance.md` | 伦理批件、知情同意、3R 原则核查 | Stage 4 M6 |
| `references/07-conclusions-discussion.md` | 结论-证据对齐、过度外推识别 | Stage 4 M7 |
| `scripts/normalize_biomed_units.py` | 单位归一化（fail-closed，只做同量纲确定性换算） | Stage 3b 兼容性判定 |
| `scripts/statistical_forensics.py` | 统计取证：p 反算 / CI 自洽 / 计数-百分比 / GRIM | Stage 2，产 signal 交 M4 |
| `scripts/ethics_compliance_check.py` | 伦理规范库筛查 | Stage 2，产 signal 交 M6 |
| `scripts/sequence_identifier_audit.py` | 序列与标识符确定性审计：HGVS 语法、变异位点越界、参考残基不符、登录号格式、基因符号物种惯例、引物 QC | Stage 2，产 signal 交 M2 / M3 |
| `scripts/figure_integrity_audit.py` | 论文内图像完整性：候选重复区域、拼接不连续、异常均匀区块。**只出候选，禁止自动定性** | Stage 3，产 signal 交 M5 |
| `resources/ethics_rules.json` | 三法域伦理规范库（25 部规范 / 22 条要求） | M6 |
| `schemas/*.json` | 全部输出的机器可校验模式 | 输出前自检 |
| `templates/review_report.md` | 报告渲染模板 | Stage 5 |
