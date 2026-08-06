# 00 · 共享契约（全模块通用）

**本文件定义七个模块共用的数据契约，是 M1–M7 能合成一个 Skill 的关键。
任何模块输出不符合此处定义的内容，一律视为无效。**

由 `SKILL.md` §3 引用。修改此文件等于修改全部模块的接口，需全组同步。

---

## 1. 证据与字段契约

### 1.1 evidence 对象

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

### 1.2 locator 规范

**存储形式为结构化对象**（见 §1.1），字段：

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

### 1.3 extracted_field 结构

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

### 1.4 provenance 对象

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

### 1.5 抽取置信度 vs 报告完整性

**两个正交概念，不得合并。**

| 概念 | 字段 | 回答的问题 |
| --- | --- | --- |
| 抽取置信度 | `extraction_confidence`: `high` / `medium` / `low` | 我们对"读出来的这个值就是稿件写的值"有多确定？ |
| 报告完整性 | `reporting_completeness`: `complete` / `incomplete` / `not_applicable` | 稿件对这个数值的报告是否符合该指标族的要求？ |

例：图注写明 `IC50 = 12.4 μM`，但未给拟合方法与置信区间 →
`extraction_confidence: "high"`（我们确信读对了）+ `reporting_completeness: "incomplete"`
（稿件报告不全，是 M4 的 finding 线索）。

---

## 2. 三类输出契约

系统产出三种彼此不可混用的记录。**判断归属的唯一标准：这是稿件的问题，还是我们的观察，还是我们的能力限制？**

### 2.1 finding · 稿件级审核判断

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

### 2.2 extraction_signal · 机器级观察

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

### 2.3 system_limitation · 系统能力限制

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

### 2.4 去重与聚簇

Stage 5 执行，顺序固定：

1. **同模块内合并**：同一模块内 `category` 相同且 `evidence` 主锚点
   （第一条 `present` 证据的 `locator`，比较 `figure`+`panel` 或 `paragraph_id`）相同的
   findings，合并为一条，保留 `severity` 最高者，其余进 `related_findings[]`。
2. **跨模块聚簇**：不同模块命中同一主锚点且语义重合时，构成一个 `issue_cluster`。
   保留 `severity` 最高的一条为簇代表，其余挂 `related_findings[]`。
   **不要把同一个问题报告六遍。**
3. **簇内证据合并**：簇代表的 `evidence[]` 并入各成员的证据，去重后保留。

聚簇结果 `issue_clusters[]` 是 §6.1 评分的输入单位。

### 2.5 M1 可以产出的 finding（严格受限）

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
