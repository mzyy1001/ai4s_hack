# Schema 迁移方案（第二轮契约审计）

对应 `SKILL.md`、`references/00-contracts.md`、`references/01-structured-extraction.md`
的第二轮修订。**不保留任何向后兼容别名** —— 旧字段一律按本文改写，改完即删。

契约层面的旧→新映射表在 `references/00-contracts.md §10`；本文只讲 **schema 文件**该怎么改。

---

## 0. 文件清单

| 文件 | 状态 | 说明 |
| --- | --- | --- |
| `schemas/common.schema.json` | **新增** | 全局原子定义（numeric_value / provenance / locator / 三维度枚举） |
| `schemas/evidence.schema.json` | **新增** | 证据登记表 + present/absence/external 三型 |
| `schemas/key_data.schema.json` | **新增** | 观测组 + observation |
| `schemas/extraction_signal.schema.json` | **新增** | 机器级观察 |
| `schemas/system_limitation.schema.json` | **新增** | 系统能力限制 |
| `schemas/execution_scope.schema.json` | **新增** | 执行范围 + 覆盖率明细 |
| `schemas/finding.schema.json` | **重写** | 仅 M2–M7；evidence_refs 取代内联 evidence |
| `schemas/structured_result.schema.json` | **重写** | 三维度字段、article_design、design_specific |
| `schemas/figure_record.schema.json` | **重写** | Figure Parser 产物，剥离 finding |
| `schemas/review_report.schema.json` | **重写** | 三项评分分离、partial 语义、registry 内嵌 |

> `common.schema.json` 是本方案相对原需求清单的**增补**。
> 若把 numeric_value / provenance / locator 复制进每个文件，五处定义必然漂移 ——
> 这正是第一轮审计发现的 `source_type` 枚举不一致的成因。集中定义是治本做法。

---

## 1. `schemas/finding.schema.json`

### 必填字段

```
id, module, category, severity, title, detail,
evidence_refs, review_confidence, manual_review
```

### 枚举变更

| 字段 | 旧值 | 新值 |
| --- | --- | --- |
| `id` pattern | `^M[1-7]-[0-9]{3}$` | `^M[2-7]-[0-9]{3}$` |
| `module` | `M1`–`M7` | **`M2`–`M7`**（M1 非法） |
| `confidence` | `high/medium/low` | **重命名为 `review_confidence`**，取值不变 |
| `manual_review.who` | 中文枚举（`统计审稿人`…） | **英文枚举**：`statistical_reviewer` / `domain_reviewer` / `ethics_committee` / `editor` / `author` |
| `manual_review.priority` | 不存在 | 新增 `P0` / `P1` / `P2` |

### 条件约束

```
if severity ∈ {critical, major}
   then manual_review.action 必填且 minLength 1，且 manual_review.priority 必填
```

### 废弃字段

| 废弃 | 迁移到 |
| --- | --- |
| `evidence`（内联对象，`$defs.evidence`） | `evidence_refs[]` → `evidence.schema.json` 登记表 |
| `evidence.locator`（字符串 + pattern） | `common.schema.json#/$defs/locator` 结构化对象 |
| `evidence.external_source` | `evidence_registry` 的 `external` 分支 + `extraction_signal.external_check`；仅 X1 创建 |

### 新增字段

`derived_from_signals[]` —— 溯源用。**不得**替代 `evidence_refs[]`；
仅凭 signal id 立 finding 为契约违规（`00-contracts.md §6.1` 规则 5）。

---

## 2. `schemas/structured_result.schema.json`

### 必填字段

```
version, stage_3b_executed, meta, article_design, objective, population,
design, measurement, conclusion, declarations, key_data,
evaluation_matrix, coverage_inputs
```

### 结构性变更

**a. 顶层新增 `version` / `stage_3b_executed`**
`version ∈ {v1, v2}`。条件约束：`version = v2` ⇒ `stage_3b_executed = true`
且 `key_data[].status ≠ pending_visual_resolution`。
这把「pending 状态不得存活到 v2」变成**机器可校验**的约束，而不只是文档里的一句话。

**b. `objective.study_type` → `article_design`**

| 旧 | 新 |
| --- | --- |
| `objective.study_type`（扁平 7 值枚举，含 `null`） | `article_design.primary_design.{family,type}`（7 族 × 24 型） |
| 多设计塞进 `alternatives[]` | `article_design.design_components[]`（事实层多设计） |
| —— | `primary_design.alternatives[]` 仅用于**抽取器不确定** |

条件约束：`family/type` 必须按 7 族 × 24 型成对；
`primary_design.family = "mixed"` ⇒ `design_components` 至少 2 项；
`primary_design.type = "preclinical_mixed"` ⇒ 至少 2 个 `experimental` 实验组件；
`family = "other"` ⇒ `other_description` 必填非空。

**c. `methods` 拆为 `population` / `design` / `measurement`**

| 旧路径 | 新路径 |
| --- | --- |
| `methods.subjects` | `population.subjects` |
| `methods.groups[]` | `design.arms[]`（新增 `experiment_id`、`replicate_type`） |
| `methods.control_type` | `design.controls` |
| `methods.randomization` | `design.randomization` |
| `methods.blinding` | `design.blinding` |
| —— | `design.allocation_concealment`（**新增**） |
| `methods.assays[]` | `measurement.assays` |
| `methods.stats_methods[]` | `measurement.statistical_methods` |
| `methods.sample_size_justification` | `measurement.sample_size_justification` |

> **`allocation` 字段被彻底废除。** 旧 `01-…md §4.2` 写
> `allocation(randomization + concealment)`，把 CONSORT 中相互独立的两项混为一谈
> —— 随机化做了但分配未隐藏是常见缺陷，合并后无法表达。拆为两个独立 `extracted_field`。

**d. 每个字段从裸值改为 `extracted_field`**

旧：`"subjects": {"type": ["string","null"]}`
新：`{"$ref": "#/$defs/extracted_field"}`，必填
`applicability` / `requiredness` / `status` / `value` / `evidence_refs` / `extraction_confidence`。

`extracted_field` 的条件约束：

```
status ∈ {not_reported, not_applicable, ambiguous, conflicting, parse_failed, unresolved}
    ⇒ value = null
status = not_applicable    ⇒ na_reason 必填非空
status = not_reported      ⇒ evidence_refs 非空（absence 证据）
status = reported          ⇒ evidence_refs 非空（present 证据）
status = parse_failed      ⇒ system_limitation_ref 必填
status = unresolved        ⇒ resolution_state 必填，且 system_limitation_ref = null
```

最后一条是**关键修正**：旧 M1 用 `status: parse_failed` + `pending_visual_resolution: true`
表示「等 Stage 3」，语义错误（Stage 3 还没尝试，谈不上失败），且污染覆盖率。

**e. `key_data[]` 从数据点改为观测组**

旧 `$defs.data_point` 是扁平单值对象，**无法表达多来源**：

| 旧字段 | 新位置 |
| --- | --- |
| `value`（`number \| string \| null`） | `observations[].value`（`numeric_value` 对象） |
| `unit` / `ci` / `n` / `replicate_type` | `observations[].*`（`ci` → `uncertainty`） |
| `source`（5 值旧枚举） | `observations[].provenance.source_type`（5 值新枚举） |
| `evidence`（内联） | `observations[].provenance.evidence_ref` |
| `confidence` | `observations[].extraction_confidence` |
| `group` | `grouping_key.group` |
| `p_value` / `test` | 单独的 `key_data` 组，`metric_family = p_value` |
| —— | `status` / `canonical_observation` / `canonical_rationale`（**新增**） |
| —— | `compatible_observations[]` / `conflicting_observations[]`（**新增**） |

**f. `evaluation_matrix` 从裸布尔改为状态感知对象**

| 旧键 | 新键 |
| --- | --- |
| `has_ethics_statement: boolean\|null` | `ethics_statement: matrix_entry \| matrix_entry[]` |
| `has_randomization` / `has_blinding` / `has_power_analysis` | `randomization` / `blinding` / `sample_size_justification` |
| `has_multiple_comparison_correction` | `multiple_comparison_correction` |
| `has_data_availability` / `has_conflict_of_interest` | `data_availability` / `conflict_of_interest` |
| **`min_group_n: integer\|null`** | **`group_sizes: group_size[]`**（保留实验级上下文） |
| —— | `has_split_strategy` / `has_external_validation`（**新增**，M2 泄露检查用） |

`matrix_entry` 允许取**数组**，用于不同实验状态不同时拆条目（`applies_to` 各自列出），
不取「或」。

**g. `gaps[]` 语义收窄**

旧 `gaps[].reason` 枚举承担了状态表示职能，与 `status` 重复。
新 `gaps[]` 纯为**运维日志**：`field_path` / `status_assigned` / `attempts[]` /
`search_terms[]` / `resolution` / `note`。`resolution` 枚举：
`confirmed_absent` / `unresolved` / `resolved_in_stage3b` / `blocked_by_system_limitation`。

**h. 新增 `design_specific` 块与 `coverage_inputs` 块**

`design_specific` 收纳 11 个设计专属字段（`databases_searched` / `search_date` /
`search_strategy` / `risk_of_bias_method` / `synthesis_method` / `protocol_registration` /
`dataset` / `split_strategy` / `baselines` / `metrics` / `validation_protocol`）——
它们在旧条件必填表中被引用但**从未定义**。

`coverage_inputs` 提供覆盖率原始计数，约束：
`len(resolved) + len(unresolved) = required_applicable_total`。

---

## 3. `schemas/figure_record.schema.json`

### 必填字段

```
figure_id, chart_type, chart_type_confidence, location, scientific_question,
interpretation, observations, extraction_confidence, manual_review_needed
```

### 结构性变更

**a. 剥离 finding —— 这是本轮最重要的一处**

旧 schema 有 `issues: [{$ref: finding.schema.json}]`，注释写「module 恒为 M5」。
这让 Stage 3 的解析器产出 Stage 4 的审核结论，混淆了两个执行角色。

新 schema 用顶层 `not` 禁止 `issues` 与 `findings` 两个键：

```json
"not": {"anyOf": [{"required": ["issues"]}, {"required": ["findings"]}]}
```

图表使用规范的 finding 由 **M5 Reviewer**（Stage 4）产出，存于 `m5_findings[]`。
Figure Parser 只解读，不评判。

**b. `extracted_data[]` → `observations[]`**

不再 `$ref` 已废除的 `structured_result.schema.json#/$defs/data_point`，
改为 `key_data.schema.json#/$defs/observation` **加上**三个必填增补：
`target_grouping_key`（Stage 3b 据此归组）、`metric_name`、`metric_family`。

**c. `location.page` → `location.evidence_ref`**

页码不再重复存储，统一由证据登记表承载。
`first_cited_at` 同样改为 `evidence_ref`（旧为自由文本 locator 字符串）。

**d. `curve_fit` 新增 `reported_in_manuscript: boolean`**

旧 schema 无法区分「稿件报告的 IC50」与「我们自己拟合出来的 IC50」。
后者**不得**当作稿件数值参与冲突判定 —— 这是一个会产生假冲突的严重缺口。

**e. `confidence` → `extraction_confidence`**；新增 `parse_limitations[]`
（指向 `system_limitation.id`，取代旧的「图像不可读也写成 issue」做法）。

**f. `chart_type` 枚举扩充**：新增 `forest_plot`、`roc_curve`
（语料含 meta 分析与诊断准确性研究，旧枚举只能落到 `other`）。

---

## 4. `schemas/review_report.schema.json`

### 必填字段

```
paper, execution_scope, coverage_breakdown, evidence_registry,
all_extraction_signals, all_system_limitations, extraction_coverage, disclaimer
```

注意：`structured_result` / `figure_records` / `all_findings` / `issue_clusters`
**不在必填列**——非 `full_review` 模式下它们可以合法缺席。

### 结构性变更

**a. 单一 `confidence_score` 拆为三项**

| 旧 | 新 |
| --- | --- |
| `confidence_score.score`（0–100，越高越好） | `manuscript_risk_score.value`（0–100，**越高风险越大**，方向相反） |
| `confidence_score.band`（中文三值） | `manuscript_risk_score.band`（完整审核英文三值；partial 固定 `partial_not_classified`） |
| `confidence_score.breakdown.extraction_gap_penalty` | **删除** —— 抽取缺口不再降低稿件分，改由 `extraction_coverage` 承载 |
| —— | `extraction_coverage`（**新增**，三子率各带显式分子分母） |
| —— | `review_confidence` / `output_confidence`（**新增**，二者互斥） |

**b. partial 语义**

`manuscript_risk_score` 新增 `partial` / `executed_modules[]` / `skipped_modules[]` /
`comparable_to_full_review`。条件约束：

```
partial = true                  ⇒ comparable_to_full_review = false
partial = true                  ⇒ band = partial_not_classified
len(executed_modules) ≤ 5       ⇒ partial = true
len(executed_modules) = 6       ⇒ partial = false
```

**c. 置信度互斥（顶层 allOf）**

```
not (review_confidence ∧ output_confidence)

execution_scope.executed_modules 非空
    ⇒ 必填 review_confidence + manuscript_risk_score，禁止 output_confidence
    否则
    ⇒ 必填 output_confidence，禁止 review_confidence 与 manuscript_risk_score
```

这把「未跑审核模块就不得声称审核置信度」变成 schema 层的强制约束。

**d. 内嵌 `evidence_registry`**

顶层必填，使输出 JSON **自洽可校验** —— 任何 `evidence_refs` 都能在同一份文档内解析。

**e. 新增 `issue_clusters[]`**，`$defs.issue_cluster` 含 `cluster_id` /
`representative_finding` / `member_findings[]` / `max_severity` / `anchor` / `evidence_refs[]`。
它是 `manuscript_risk_score` 的**唯一计分单位**（旧版直接对 findings 计分，
会把一个问题拆成六条放大分数）。

**f. `manual_review_plan[].who` 中文枚举 → 英文枚举**；`priority` 改为必填。

**g. `disclaimer` 提升为顶层必填 `const`**，与 `SKILL.md §0` 的声明逐字一致。

---

## 5. 新增 schema 的要点速查

| 文件 | 必填 | 关键条件约束 |
| --- | --- | --- |
| `common` | —— （纯 $defs） | `provenance`: `source_type × extraction_method` 5 组合法组合 |
| `evidence` | `evidence_registry` | `absence` 型：`additionalProperties:false` 天然禁止 `quote`/`locator`；`searched_locations`/`search_terms` 各 `minItems:1` |
| `key_data` | 见文件头 | `status ∈ {conflicting, ambiguous, pending, parse_failed}` ⇒ `canonical_observation = null`；canonical 非 null ⇒ `canonical_rationale` 必填；canonical = null ⇒ `reporting_completeness = not_assessed` 且 `missing_elements` 为空 |
| `key_data.observation` | 见文件头 | `pixel_estimated` ⇒ `value.type ∈ {interval, lower_bound, upper_bound}` ∧ `extraction_confidence = low` ∧ `manual_review_needed = true`；`axis_readable` ⇒ 置信度 ≤ medium |
| `extraction_signal` | 见文件头 | 顶层 `not.required:["severity"]`；`source_value_conflict` ⇒ `produced_by = stage_3b` ∧ `observation_refs` ≥ 2；`claim_without_resolved_evidence_link` ⇒ `target` 为 `claim_target` 对象 |
| `system_limitation` | 见文件头 | 顶层 `not.anyOf` 禁止 `severity` 与 `manual_review` |
| `execution_scope` | `execution_scope`, `coverage_breakdown` | `stage_3b ∈ executed_stages ⇒ stage_2 ∈ executed_stages`；`stage_4 ⇒ stage_3b`；`full_review ⇒ len(executed_modules) ≥ 6 ∧ skipped 为空`；`figure_review ⇒ executed_modules = ["M5"]`；`submode` 仅 `figure_analysis` 下非 null |

`execution_scope` 的两条阶段依赖约束，把「任何阶段不得消费未产出的产物」
从文档规则变成了 **schema 可拒绝的非法输入**——这正是第 1 号审计问题的根因修复。

---

## 6. 全局废弃清单

改写时按此清单全文搜索，命中即改：

```
# 枚举值
"text"          → "explicit_main_text"
"table"         → "explicit_table"
"figure"        → "explicit_figure_caption"
"figure_caption"→ "explicit_figure_caption"
"figure_axis"   → "axis_readable"
"figure_pixel"  → "pixel_estimated"

# 字段名
evidence[]（内联）            → evidence_refs[] + evidence_registry
provenance.locator（内联）    → provenance.evidence_ref
confidence（finding 上）      → review_confidence
confidence（figure_record 上）→ extraction_confidence
ci                            → uncertainty
extracted_data[]              → observations[]
issues[]（figure_record 上）  → 删除（改由 m5_findings[]）
study_type                    → article_design.primary_design.{family,type}
allocation                    → randomization + allocation_concealment
min_group_n                   → group_sizes[]
methods.groups[]              → design.arms[]
gaps[].reason                 → gaps[].status_assigned + gaps[].resolution
confidence_score              → manuscript_risk_score + extraction_coverage + (review|output)_confidence
extraction_gap_penalty        → 删除（缺口不降稿件分）

# 数组
extraction_quality_findings[] → extraction_signal(ambiguous_extraction)
                                + coverage_breakdown.unresolved_required_fields[]
source_conflict_signals[]     → merge_extraction_signals[] 中 type=source_value_conflict
unresolved_evidence_links[]   → signal claim_without_resolved_evidence_link 的 target 元数据

# 值形式
"value": 12.4       → {"type": "point", "number": 12.4}
"value": "40–50"    → {"type": "interval", "low": 40, "high": 50}
"value": "<0.001"   → {"type": "upper_bound", "high": 0.001}

# 生命周期
status:"parse_failed" + pending_visual_resolution:true
    → status:"unresolved" + resolution_state{state,pending_stage,expected_sources}

# signal type
"parse_failure"  → 删除（改为 system_limitation，category=parse_failed）

# 中文枚举
"统计审稿人"/"领域审稿人"/"伦理委员会"/"编辑"/"作者"
    → statistical_reviewer / domain_reviewer / ethics_committee / editor / author
"可进入常规同行评审"/"需作者澄清后复审"/"建议退回补充"
    → routine_review / clarification_needed / major_revision_suggested
```

---

## 7. 校验方式

```bash
python3 tools/validate_schemas.py          # 解析 + 跨文件 $ref 解析 + 契约 lint 规则
python3 tools/validate_schemas.py --sample # 附带对 4 个模拟实例的实例级校验
```

`tools/validate_schemas.py` 不依赖第三方库（沙箱无 `jsonschema`），
实现的是**本方案关心的那部分**约束：枚举合法性、`evidence_ref` 可解析、
v2 无 pending 残留、`system_limitation` 无 severity、`finding.module ≠ M1`、
数值非裸、pixel 四项约束、覆盖率分子分母自洽、置信度字段互斥。
完整 JSON Schema 校验待环境具备 `jsonschema` 后再启用。
