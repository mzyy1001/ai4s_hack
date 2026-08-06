# M1 · 结构化抽取（前置层）

**负责人：MZYY（陈泓睿）** · 状态：**契约已定，规则库填充中**

M1 是流水线的**前置抽取层**，不是与 M2–M7 并列的审核模块。
M2–M7 全部消费 M1（经 Stage 3b 合并后）的产物，因此这里的错误会放大六倍。
唯一的安全策略是：**宁可标记状态，不可推断填充。**

---

## 1. 职责与非职责

### 1.1 M1 做什么

| 职责 | 产物 |
| --- | --- |
| 从**文本来源**（正文、表格、图注文字）抽取结构化事实 | `structured_result_v1` |
| 为每个重要字段给出显式状态与证据 | `extracted_field`（§2） |
| 判定研究设计并据此决定哪些字段适用 | `study_design`（§4） |
| 记录机器级观察，供下游解读 | `extraction_signals[]`（§7） |
| 记录抽取质量问题 | `extraction_quality_findings[]`（§8.1） |
| 记录系统能力限制 | `system_limitations[]`（§8.2） |
| 提供路由索引 | `evaluation_matrix`（§9） |

### 1.2 M1 **不**做什么

**M1 不做稿件级审核判断。** 同一现象，M1 只描述「观察到什么」，
由对应模块决定「这是否构成稿件问题」。

| 现象 | M1 输出 | 由谁判定 | 判定什么 |
| --- | --- | --- | --- |
| 两处数值不一致 | `source_value_conflict` signal | **M2** | 是否构成稿件内部矛盾 |
| claim 找不到支撑证据 | `claim_without_resolved_evidence_link` signal | **M7** | 是否构成无支撑主张 / 过度外推 |
| 未见随机化描述 | `randomization.status = not_reported` + absence 证据 | **M3 / M4** | 是否构成设计缺陷 |
| 未见伦理声明 | `ethics_statement.status = not_reported` + absence 证据 | **M6** | 是否构成合规问题 |
| 未见样本量依据 | `sample_size_justification.status = not_reported` | **M4** | 是否构成统计报告缺陷 |
| 研究设计线索矛盾 | `ambiguous_study_design` signal | **M2 / M3 / M4** | 是否构成设计描述不清 |
| 图像不可读 | `system_limitation` | —— | 不是稿件问题，只降覆盖率 |

> 旧版 M1 曾直接产出 `unsupported_claim` / `conflicting_values` / `abstract_text_mismatch`
> 等 finding，现已全部改为 signal 并移交下游。见 §D 迁移说明。

---

## 2. 字段状态模型

### 2.1 extracted_field 结构

**所有重要字段**（清单见 §3）统一使用此结构，**不得用裸 `null` 编码多种缺失状态**：

```json
{
  "value": null,
  "status": "not_reported",
  "evidence": [],
  "extraction_confidence": "high",
  "alternatives": [],
  "candidates": [],
  "na_reason": null,
  "system_limitation_ref": null
}
```

### 2.2 status 枚举

| status | 精确含义 | `value` | `evidence` 要求 | 下游可否据此立 finding |
| --- | --- | --- | --- | --- |
| `reported` | 稿件明确报告了该值 | 非 null | ≥1 条 `present` | 可（针对内容本身） |
| `not_reported` | **已检索**相关位置，稿件确实未报告 | `null` | ≥1 条 `absence`，含 `searched_locations` 与 `search_terms` | **可** |
| `not_applicable` | 该字段对本研究设计不适用 | `null` | 可空，须填 `na_reason` | **否** |
| `ambiguous` | 存在相关文本但无法唯一解读 | `null` | ≥1 条 `present`（指向歧义文本） | 否，先出 signal |
| `conflicting` | 多来源报告不兼容的值 | `null` | `candidates[]` 各带证据 | 否，先出 signal |
| `parse_failed` | 内容可能存在，系统无法可靠抽取 | `null` | 可空，须填 `system_limitation_ref` | **否，绝不可** |

### 2.3 三条不可混淆的边界

1. **`not_reported` ≠ `parse_failed`**
   前者是**稿件**没写（已检索确认），可成为 finding 依据；
   后者是**我们**没读出来，只降 `extraction_coverage`，**不得**变成稿件 finding。
   无法确定属于哪一种时，一律用 `parse_failed` —— 宁可承认看不清，不可冤枉稿件。

2. **`not_reported` ≠ `not_applicable`**
   前者是"该写没写"，后者是"本来就不需要写"。
   研究设计不适用的字段必须用 `not_applicable` + `na_reason`，
   **不得**产生虚假的缺失项 finding。判定依据见 §4.3。

3. **`ambiguous` ≠ `conflicting`**
   前者是**一处**文本读不出唯一解；后者是**多处**文本互相打架。
   后者才产出 `source_value_conflict`。

### 2.4 absence 证据的取证要求

`status: not_reported` 的字段，其 `absence` 证据必须真实反映检索过程：

```json
{
  "type": "absence",
  "scope": "document",
  "searched_locations": [
    {"section": "methods", "scope": "section"},
    {"section": "declarations", "scope": "section"},
    {"supplement_id": "S1", "scope": "supplement"}
  ],
  "search_terms": ["randomization", "random allocation", "randomly assigned",
                   "随机分组", "随机化"],
  "search_result": "no_match"
}
```

**规则**

- `absence` 证据**禁止**含 `quote`。绝不为不存在的内容编造引文。
- 检索范围必须覆盖该字段的**全部常规位置**（见 §3 各字段的 `search_scope` 列）。
  范围不全时不得声称缺失，应降级为 `parse_failed` 并说明未覆盖的部分。
- 补充材料不可得时，`supplement_accessibility` 受影响，该字段应为 `parse_failed`
  而非 `not_reported` —— 我们没看过补充材料，就不能说它没写。
- `search_result: partial_match_ambiguous` 不足以支撑缺失结论，应改判 `ambiguous`。

---

## 3. 重要字段清单与 provenance 要求

下列字段**全部**使用 §2.1 的 `extracted_field` 结构。
`search_scope` 列定义 `absence` 取证时的最小检索范围。

### 3.1 objective · 研究目标

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `research_question` | 论文要回答的问题，一句话 | abstract, introduction, discussion |
| `hypothesis` | 明确陈述的假设 | introduction, methods |
| `study_design` | 研究设计，取 §4.1 层级枚举 | title, abstract, methods |
| `primary_endpoint` | 主要终点/主要观测指标 | abstract, methods, results |
| `secondary_endpoints` | 次要终点（数组） | methods, results |

> `study_design` 是**主路由字段**：M3 用它决定是否启动动物实验必要性检查，
> M4 用它选统计规范表，M6 用它决定伦理要求，M1 自己用它决定哪些字段适用。
> 抽错会导致四处跑错规则集。判定不唯一时**必须**出 `ambiguous_study_design` signal。

### 3.2 population · 受试对象

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `subjects` | 物种/品系/细胞系/人群，含来源 | methods |
| `inclusion_criteria` | 纳入标准 | methods |
| `exclusion_criteria` | 排除标准 | methods |
| `participant_spectrum` | 受试者谱（诊断准确性研究必填） | methods |

### 3.3 design · 设计与干预

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `arms` | 试验臂/实验组（数组，见 §3.7） | methods, figures |
| `interventions` | 干预措施（数组） | methods |
| `controls` | 对照设置（数组） | methods |
| `exposure` | 暴露因素（观察性研究） | methods |
| `confounders` | 混杂因素与校正方式（观察性研究） | methods, statistics |
| `follow_up` | 随访时长与失访 | methods, results |
| `randomization` | 随机化方法描述 | methods |
| `blinding` | 盲法：`none`/`single`/`double`/`triple` | methods |
| `allocation_concealment` | 分配隐藏 | methods |
| `registration` | 注册号与注册时间 | abstract, methods, declarations |

### 3.4 measurement · 测量与分析

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `assays` | 每项 `{name, purpose, reference_citation}` | methods |
| `index_test` | 待评价试验（诊断研究） | methods |
| `reference_standard` | 金标准（诊断研究） | methods |
| `statistical_methods` | 每项 `{test, applied_to, software, correction}` | methods, figure captions |
| `sample_size_justification` | 效能分析或样本量依据 | methods |
| `missing_data_handling` | 缺失数据处理 | methods, statistics |

### 3.5 conclusion · 结论

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `claims` | 每条 `{statement, scope, supported_by[]}` | abstract, discussion, conclusion |
| `limitations` | 作者自述的局限 | discussion |
| `generalization_scope` | 作者主张的适用范围 | discussion, conclusion |

### 3.6 declarations · 声明

| 字段 | search_scope |
| --- | --- |
| `ethics_statement`（含批件号、机构） | declarations, methods, ethics |
| `informed_consent` | declarations, methods |
| `funding` | declarations, funding |
| `conflict_of_interest` | declarations |
| `data_availability` | declarations, data_availability |

### 3.7 实验级结构

`arms[]` 保留**实验级**上下文，不压缩为全局单值：

```json
{
  "experiment_id": "EXP-01",
  "arm_name": "vehicle",
  "n": {"value": 6, "status": "reported", "evidence": [...], "extraction_confidence": "high"},
  "replicate_type": "biological",
  "intervention": {"value": "0.9% saline", "status": "reported", "evidence": [...]},
  "dose": {"value": null, "status": "not_applicable", "na_reason": "vehicle control"},
  "route": {"value": "i.p.", "status": "reported", "evidence": [...]},
  "duration": {"value": "14 d", "status": "reported", "evidence": [...]}
}
```

---

## 4. 研究设计路由

### 4.1 study_design 层级枚举

```
experimental
  in_vitro | ex_vivo | organoid | in_vivo_animal | preclinical_mixed

human_interventional
  randomized_controlled_trial | nonrandomized_trial | single_arm_trial

human_observational
  cohort | case_control | cross_sectional | diagnostic_accuracy
  case_series | case_report

evidence_synthesis
  systematic_review | meta_analysis | scoping_review

computational
  bioinformatics | prediction_model | simulation | method_development | benchmark_study

mixed
other
```

存储形式保留层级：

```json
"study_design": {
  "value": {"family": "human_interventional", "type": "randomized_controlled_trial"},
  "status": "reported",
  "evidence": [...],
  "extraction_confidence": "high"
}
```

一篇论文含多类研究时，`value` 取主设计，其余进 `alternatives[]`，
并为每个 `experiment_id` 单独标注设计类型。

### 4.2 条件必填字段

**不同设计的必填字段不同。** 下表之外的字段一律 `not_applicable`。
**禁止**对所有设计统一要求 `arms[]` / `controls` / `assays[]` / `primary_endpoint`。

| 设计族 | 条件必填字段 |
| --- | --- |
| `human_interventional` | `arms`, `allocation`(randomization + concealment), `interventions`, `primary_endpoint`, `secondary_endpoints`, `registration`, `sample_size_justification`, `statistical_methods` |
| `human_observational`（除诊断） | `subjects`, `exposure`, `primary_endpoint`, `confounders`, `follow_up`, `statistical_methods` |
| `diagnostic_accuracy` | `index_test`, `reference_standard`, `primary_endpoint`(目标疾病), `participant_spectrum`, `statistical_methods` |
| `evidence_synthesis` | `databases_searched`, `search_date`, `inclusion_criteria`, `risk_of_bias_method`, `synthesis_method` |
| `experimental / in_vitro` | `subjects`(细胞系), `interventions`, `assays`, `arms`(含生物学重复数), `statistical_methods` |
| `experimental / in_vivo_animal` | `subjects`(物种品系), `arms`, `interventions`, `controls`, `assays`, `randomization`, `blinding`, `sample_size_justification`, `ethics_statement`, `statistical_methods` |
| `computational` | `dataset`, `split_strategy`, `baselines`, `metrics`, `validation_protocol` |
| `case_report / case_series` | `subjects`, `interventions`, `informed_consent`；**不要求** `arms` / `randomization` / `sample_size_justification` |

`evidence_synthesis` 与 `computational` 专属字段同样使用 `extracted_field` 结构，
定义在 `structured_result.schema.json` 的 `design_specific` 块下。

### 4.3 not_applicable 的判定

只有在**该设计的条件必填表中不含该字段**时，才可置 `not_applicable`，
并在 `na_reason` 写明依据：

```json
{"value": null, "status": "not_applicable",
 "na_reason": "study_design=case_report，条件必填表不含 randomization"}
```

设计判定为 `ambiguous_study_design` 时，**不得**使用 `not_applicable`
—— 设计未定就无法判断适用性，相关字段应为 `parse_failed` 或 `ambiguous`。

---

## 5. key_data 与指标族规则

### 5.1 数据点结构

```json
{
  "id": "KD-007",
  "metric_name": "IC50",
  "metric_family": "dose_response",
  "value": 12.4,
  "unit": "μM",
  "uncertainty": {"type": "95CI", "low": 9.8, "high": 15.7},
  "n": 3,
  "replicate_type": "biological",
  "experiment_id": "EXP-02",
  "comparison": "Compound A vs vehicle",
  "provenance": {
    "source_type": "explicit_figure_caption",
    "source_id": "fig:2C",
    "locator": {"figure": "2", "panel": "C", "pdf_file_page": 5, "scope": "panel"}
  },
  "quote": "IC50 = 12.4 μM (95% CI 9.8–15.7), four-parameter logistic fit",
  "extraction_confidence": "high",
  "reporting_completeness": "complete",
  "missing_elements": []
}
```

### 5.2 source_type 枚举（全局唯一）

```
explicit_main_text | explicit_table | explicit_figure_caption | axis_readable | pixel_estimated
```

**所有示例与 schema 必须使用此枚举。** 旧值 `text` / `table` / `figure` /
`figure_caption` / `figure_axis` / `figure_pixel` 已废弃，映射见 §D。

`pixel_estimated` 的强制约束：
`extraction_confidence` 必须为 `low`；`value` 必须为区间字符串（如 `"40–50"`）而非点值；
必须置 `manual_review_needed = true`；**不得**用于 M4 的任何复算。

### 5.3 指标族完整性规则

**取消旧版"任何数值都要 unit + n + 误差"的三要素规则** —— 它对计数、比例、
无量纲指标都不成立。改为按**指标族**判定 `reporting_completeness`：

| metric_family | 完整报告所需要素 | 备注 |
| --- | --- | --- |
| `continuous_summary` | value + unit（有量纲时）+ n + dispersion(SD/SEM/IQR/range) | 无量纲指标不要求 unit |
| `effect_estimate` | estimate + CI + reference_group + model | 如均差、OR、RR |
| `count` | count + population_or_denominator_context | 不要求 unit、不要求误差 |
| `proportion` | (numerator + denominator) 或 (proportion + n) | 不要求 unit |
| `p_value` | p_value + test + comparison | 不要求 n（n 挂在被比较的数据点上） |
| `correlation` | coefficient + n + method(Pearson/Spearman/…) | 不要求 unit |
| `time_to_event` | HR + CI + reference_group + model | 中位生存另计为 `continuous_summary` |
| `dose_response` | IC50/EC50 + unit + fitting_method + CI（原文报告时） | CI 未报告不降 extraction_confidence |
| `classification_metric` | metric_name + value + evaluation_set + threshold_or_averaging（相关时） | AUC/F1/准确率等，无量纲 |

**判定规则**

- 要素齐全 → `reporting_completeness: "complete"`。
- 缺少要素 → `reporting_completeness: "incomplete"`，
  缺失项逐一列入 `missing_elements[]`（如 `["dispersion", "n"]`）。
- 该族不要求的要素缺失 → **不计入** `missing_elements`，不影响完整性判定。

### 5.4 抽取置信度与报告完整性正交

**两者独立判定，不得互相传染。**

| 场景 | extraction_confidence | reporting_completeness |
| --- | --- | --- |
| 图注明写 `IC50 = 12.4 μM (95% CI …)`，含拟合方法 | `high` | `complete` |
| 图注明写 `IC50 = 12.4 μM`，无 CI 无拟合方法 | `high`（我们确信读对了） | `incomplete`（缺 fitting_method） |
| 只能从对数坐标轴读出约 12–15 μM | `low`（估读） | 视原文报告要素另判 |
| 相关文本存在但表述矛盾 | 字段 `status: conflicting` | 不判定，先出 signal |

`reporting_completeness: "incomplete"` 是 **M4 的 finding 线索**，M1 只记录，不立 finding。

---

## 6. structured_result_v1 与 v2

### 6.1 两个版本的分界

| 版本 | 产出者 | 数据来源 | 消费者 |
| --- | --- | --- | --- |
| `structured_result_v1` | **M1（Stage 2）** | 仅文本：正文、表格、图注**文字** | 仅 Stage 3（作上下文）与 Stage 3b |
| `structured_result_v2` | **Stage 3b** | v1 + 图表解析结果，已完成冲突消解 | **M2–M7 全部** |

**M1 不产出 v2。** M1 的职责在 v1 结束；合并是 Stage 3b 的职责。
**M2–M7 一律消费 v2**，直接读 v1 会漏掉全部图像来源数值。

### 6.2 抽取顺序（v1 阶段）

1. **Methods 优先**，不要从 Abstract 开始。摘要是作者的宣传语，方法学才是事实来源。
2. Results 正文 → 补 `key_data`，标 `explicit_main_text`。
3. 表格 → 补 `key_data`，标 `explicit_table`。
4. 图注**文字** → 补 `key_data`，标 `explicit_figure_caption`。
5. Abstract **最后**读，**仅用于交叉校验**：
   摘要与正文数值不一致时，**不得**用摘要覆盖正文，应记为 `conflicting` 并出
   `source_value_conflict` signal（由 M2 判定）。
6. **图像本体不在 v1 阶段读取** —— 那是 Stage 3 的职责，结果在 Stage 3b 回流。

### 6.3 图表合并接口（Stage 3b 消费，M1 需保证可对接）

M1 为每个可能从图中补全的字段预留挂载点：

```json
{
  "value": null,
  "status": "parse_failed",
  "pending_visual_resolution": true,
  "expected_source": ["fig:2C"],
  "system_limitation_ref": null
}
```

`pending_visual_resolution: true` 告诉 Stage 3b：该字段等待图表解析结果。
Stage 3b 合并后按 `SKILL.md §2.7` 的来源可靠性排序更新 `status`：

- 图表来源解析成功且与文本兼容 → `reported`
- 图表来源与文本不兼容 → `conflicting` + `source_value_conflict` signal
- 图表来源也解析失败 → 保持 `parse_failed`，关联 `system_limitation`

---

## 7. extraction_signals

M1（Stage 2）与 Stage 3b 产出。**signal 不带 `severity`，不是结论。**

### 7.1 signal 类型与路由

| type | M1 触发条件 | 路由到 | 下游判定 |
| --- | --- | --- | --- |
| `source_value_conflict` | 同一字段多来源数值不兼容（含摘要-正文不一致） | M2（主）、M4 | 是否构成稿件内部矛盾 |
| `claim_without_resolved_evidence_link` | `claims[].supported_by` 解析不到任何 `key_data.id` 或 locator | M7 | 是否构成无支撑主张 |
| `ambiguous_study_design` | 设计线索冲突或不足以唯一归类 | M2、M3、M4、M6 | 是否构成设计描述不清 |
| `unresolved_cross_reference` | 正文引用的图/表/补充材料无法解析到实体 | M2、M5 | 是否构成引用错误 |
| `partial_extraction` | 字段部分抽出（如有 n 但无分组归属、有剂量无单位） | M4、M5 | 是否构成报告不完整 |
| `parse_failure` | 抽取因技术原因失败 | **不路由到审核模块** | 仅关联 `system_limitation` |

### 7.2 结构

```json
{
  "id": "SIG-002",
  "type": "source_value_conflict",
  "target": "key_data.KD-007",
  "detail": "IC50 在图注为 12.4 μM，在 Results 正文为 15.1 μM，置信区间不重叠。",
  "candidates": [
    {"value": 12.4, "unit": "μM",
     "provenance": {"source_type": "explicit_figure_caption", "source_id": "fig:2C",
                    "locator": {"figure": "2", "panel": "C", "pdf_file_page": 5, "scope": "panel"}}},
    {"value": 15.1, "unit": "μM",
     "provenance": {"source_type": "explicit_main_text", "source_id": "results-p8",
                    "locator": {"section": "results", "paragraph_id": "results-p8",
                                "pdf_file_page": 6, "scope": "paragraph"}}}
  ],
  "routed_to": ["M2", "M4"]
}
```

**规则**：下游模块据 signal 立 finding 时，必须在该 finding 的 `evidence[]` 中
**独立**给出稿件证据，不得仅引用 signal id。

---

## 8. 抽取质量与系统限制

### 8.1 extraction_quality_findings（M1 可产出的唯一 finding 类）

**只影响 `extraction_coverage` 与 `review_confidence`，不影响 `manuscript_risk_score`。**

| category | 触发条件 | 影响 |
| --- | --- | --- |
| `ambiguous_extraction` | 字段 `status: ambiguous` | 降 coverage / confidence |
| `required_field_unresolved` | 条件必填字段最终为 `ambiguous`/`conflicting`/`parse_failed` | 降 coverage / confidence |

这两类 finding 的 `module` 恒为 `M1`，**不得**赋予 `critical`/`major` 等稿件 severity；
在 `review_report` 中单列，不进入 `issue_clusters[]` 的风险计分。

### 8.2 system_limitations（不是 finding）

抽取因技术原因失败时产出，结构与枚举见 `00-contracts.md` §2.3。M1 常见触发：

| category | 场景 |
| --- | --- |
| `parse_failed` | 段落无法提取、编码错乱 |
| `table_unparseable` | 表格结构无法还原 |
| `supplement_inaccessible` | 引用了补充材料但无法获取 |
| `ocr_low_quality` | 扫描件 OCR 质量不足 |
| `input_truncated` | 输入被截断，部分章节缺失 |

**`supplement_inaccessible` 时，依赖补充材料的字段一律 `parse_failed`，
不得判 `not_reported`** —— 我们没看过，就不能说它没写。

### 8.3 gaps[] · 操作日志

`gaps[]` 保留为**运维日志**，记录未解决抽取问题的排查线索，
**不再是**字段状态的表示方式（状态由 §2 的 `status` 承载）：

```json
{
  "field": "measurement.sample_size_justification",
  "status_assigned": "not_reported",
  "attempts": ["methods§2.6 全文检索", "supplement S1 检索", "figure captions 检索"],
  "search_terms": ["power", "sample size", "样本量", "效能"],
  "resolution": "confirmed_absent",
  "impact": "M4 无法评估效能，相关 finding 将依赖 absence 证据"
}
```

`resolution` 取值：`confirmed_absent` / `unresolved` / `resolved_in_stage3b` / `blocked_by_system_limitation`。

---

## 9. evaluation_matrix

### 9.1 用途与限制

`evaluation_matrix` 是 M2–M7 的**路由与索引**工具，让下游无需重读全文即可
判断该跑哪些规则、去哪里找证据。

**三条硬性限制**

1. **可以**用它决定跑哪些规则集、定位相关证据。
2. **不得**仅凭它直接立 finding。M2–M7 必须回查 `evidence_refs` 指向的证据记录，
   在 finding 中独立给出 `evidence[]`。
3. 实验级信息**不得**压缩为单一全局数字。

### 9.2 条目结构

每个条目是**状态感知对象**，不是裸布尔：

```json
"randomization": {
  "status": "not_reported",
  "applies_to": ["EXP-01", "EXP-02"],
  "evidence_refs": ["EV-018"],
  "extraction_confidence": "high"
}
```

`status` 取 §2.2 枚举。`applies_to` 列出该判断覆盖的实验；
不同实验状态不同时，拆成多个条目而非取"或"。

### 9.3 条目清单

| 键 | 消费者 | 备注 |
| --- | --- | --- |
| `has_animal_experiment` | M3, M6 | |
| `has_human_subjects` | M6 | |
| `ethics_statement` | M6 | |
| `informed_consent` | M6 | |
| `registration` | M6, M4 | |
| `randomization` | M3, M4 | |
| `blinding` | M3, M4 | |
| `allocation_concealment` | M4 | |
| `sample_size_justification` | M4 | |
| `multiple_comparison_correction` | M4 | |
| `has_ml_model` | M2, M4 | 触发 M2 数据泄露场景库 |
| `data_availability` | M2 | |
| `conflict_of_interest` | M2 | |
| `all_figures_cited_in_text` | M2, M5 | |
| `figure_count` / `table_count` | M5 | 计数字段，直接取整数 |
| `group_sizes` | M4 | **数组**，见 §9.4 |

### 9.4 group_sizes：保留实验级上下文

**取消旧版 `min_group_n` 单一整数** —— 它把所有实验压成一个数，丢掉了
"哪个实验的哪一组样本量小"这个 M4 真正需要的信息。

```json
"group_sizes": [
  {"experiment_id": "EXP-01", "group": "vehicle", "n": 6,
   "replicate_type": "biological", "evidence_refs": ["EV-021"]},
  {"experiment_id": "EXP-01", "group": "treated", "n": 6,
   "replicate_type": "biological", "evidence_refs": ["EV-021"]},
  {"experiment_id": "EXP-03", "group": "siRNA", "n": 3,
   "replicate_type": "technical", "evidence_refs": ["EV-034"]}
]
```

M4 自行按实验分组计算最小值与分布，M1 不做聚合判断。

---

## 10. TODO（一期）

- [ ] 补齐 §4.1 层级枚举的边界样例：ex vivo 与 organoid 的区分、
      preclinical_mixed 的适用条件、prediction_model 与 benchmark_study 的分界
- [ ] 补齐单位归一化表（μM/µM/uM、mg/kg vs mg·kg⁻¹、log vs ln）
- [ ] 补齐各字段 `search_scope` 的检索词表（中英双语），供 absence 取证使用
- [ ] 与 M5 确认 §6.3 `pending_visual_resolution` 挂载点的字段级对接清单
- [ ] 在 `datasets/` 的 10 篇语料上跑一遍，按 study_design 分别统计
      `field_resolution_rate`，校准 §4.2 条件必填表是否过严
- [ ] 为 §5.3 每个 metric_family 各写 1 个 complete + 1 个 incomplete 样例

---

## 11. 二期扩展：标识符核验（本期不实现，规则先写下）

一期只抽取标识符，不核验其真实性。二期接入 MCP 后逐项核验。
**二期应扩展而非重构** `provenance` 与 `evidence` 契约（见 `SKILL.md §0.2`）。

| 标识符 | 核验数据源 | 查出什么 | 结果解读归属 |
| --- | --- | --- | --- |
| 临床试验注册号 | ClinicalTrials.gov / ChiCTR / WHO ICTRP | 号码不存在、终点与注册不符、注册晚于入组 | **M6** |
| 细胞系名称 | Cellosaurus / ICLAC | 已知误认或交叉污染细胞系 | **M3** |
| 抗体 / 试剂 | RRID (Antibody Registry) | 货号不存在、抗体已被证实无特异性 | **M3** |
| 基因 / 蛋白符号 | HGNC / UniProt | 符号已废弃或写错、物种不匹配 | **M1**（表述层）/ **M2** |
| 参考文献 | Crossref / PubMed / Retraction Watch | 文献不存在、已被撤稿或更正 | **M2** |

**M1 二期只负责核验标识符本身的真实性**，产出的是
`identifier_verification` 类 signal，**不下审核结论**：

```json
{
  "id": "SIG-011",
  "type": "identifier_verification",
  "target": "design.registration",
  "identifier": {"scheme": "clinicaltrials", "value": "NCT01234567"},
  "verification": {
    "database": "ClinicalTrials.gov",
    "query": "NCT01234567",
    "retrieval_date": "2026-08-07",
    "record_id": "NCT01234567",
    "version": "2024-03-11",
    "retraction_or_correction_status": "none",
    "result": "not_found",
    "relation_to_claim": "registration_unverifiable"
  },
  "routed_to": ["M6"]
}
```

`result` 枚举：`verified` / `not_found` / `mismatch` / `retracted` / `superseded` / `lookup_failed`。
`lookup_failed`（网络或接口故障）产出 `system_limitation`，**不得**当作 `not_found`。
