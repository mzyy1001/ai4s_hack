# 00 · 共享契约（全模块通用）

**本文件定义 Stage 1–5、可选外部验证层 X1 与 M1–M7 共用的数据契约。任何模块输出不符合此处定义的内容，一律视为无效。**

由 `SKILL.md §3` 引用。修改此文件等于修改全部模块的接口，需全组同步。
本文件所有示例**必须**能通过 §11 的契约 lint 检查表。

**术语约定**：本文件中「记录（record）」特指 §6 的三类顶层记录（`finding` / `extraction_signal` /
`system_limitation`）。§7 的对象（`execution_scope` / `coverage_breakdown`）**不是记录**，
不得称为 finding，不得带 `severity`。

---

## 1. 证据登记表（evidence_registry）

### 1.1 为什么需要登记表

同一处证据常被多个字段、多条 finding、多个 signal 引用。若各处内联复制，
同一段落会出现七份不同措辞的 locator，去重与聚簇无从对齐。

**规则：证据的规范存储是登记表；其他一切位置只存 `evidence_ref` 字符串。**

```json
{
  "evidence_registry": {
    "EV-018": {
      "id": "EV-018",
      "type": "present",
      "locator": {
        "section": "methods",
        "subsection": "2.4",
        "paragraph_id": "methods-p17",
        "pdf_file_page": 7,
        "printed_page": 1043,
        "xml_id": "para-0042",
        "scope": "paragraph"
      },
      "quote": "Data are presented as mean ± SEM (n = 3).",
      "created_by": "stage_2"
    },
    "EV-019": {
      "id": "EV-019",
      "type": "absence",
      "scope": "document",
      "searched_locations": [
        {"section": "methods", "scope": "section"},
        {"section": "declarations", "scope": "section"},
        {"supplement_id": "S1", "scope": "supplement"}
      ],
      "search_terms": ["randomization", "random allocation", "randomly assigned", "随机分组", "随机化"],
      "search_result": "no_match",
      "created_by": "stage_2"
    }
  }
}
```

### 1.2 三种证据型

| type | 用于 | 必填 | 禁止 |
| --- | --- | --- | --- |
| `present` | 稿件中已有的内容 | `locator` 对象 | —— |
| `absence` | 稿件中不存在的内容 | `scope` + `searched_locations[]` + `search_terms[]` + `search_result` | **`quote`**、**`locator`** |
| `external` | X1 从公开科学数据源取得的事实 | `database` + `endpoint` + `query` + `retrieval_status` + 响应 hash/版本 + `assertions[]` | 稿件 `locator`/`quote`、API key、Cookie、Authorization header、整份响应 |

**`search_result` 枚举**：`no_match` / `partial_match_ambiguous`。
后者**不足以**支撑缺失结论，引用它的字段必须判 `ambiguous` 而非 `not_reported`。

**`external.retrieval_status` 枚举**：`resolved` / `not_found` / `not_addressed`。
`not_found` 仅用于**格式合法的精确标识符**获得权威 404 或成功响应中的明确零记录；
名称、关键词或语义查询零命中只能记 `not_addressed`。DNS、超时、TLS、白名单拦截、
401/403、429、5xx 或响应结构漂移**不得创建 external evidence**，按 §6.3 产
`system_limitation`。数据库沉默不是反证。

### 1.3 登记表硬性规则

1. 每个 `evidence_ref` **必须**能在 `evidence_registry` 中解析到**恰好一个**条目。
   解析不到即为契约违规，该条 finding / signal 一律丢弃。
2. 证据 id 在**一次审核运行内**稳定，格式 `EV-<三位以上数字>`，全局递增，不复用。
3. `type: "absence"` 的条目**禁止**含 `quote`。**绝不为不存在的内容编造引文。**
4. `absence` 的 `searched_locations[]` 必须反映**实际执行过**的检索。
   检索范围之外的部分不得声称"缺失"，应改产出 `system_limitation`。
5. `created_by` 取 `stage_1` / `stage_2` / `stage_3` / `stage_3b` /
   `stage_3c_external_validation` / `M2`…`M7`，用于排障；`external` 只能由
   `stage_3c_external_validation` 创建。
6. 同一 locator + 同一 quote 的证据**复用既有条目**，不新建。
7. `external.assertions[]` 只保存外部响应中的原子事实与 `source_path`；稿件值与外部值的
   比较写入 `extraction_signal.external_check`，不得把比较结论伪装成数据库原文。

### 1.4 引用规则：evidence_refs[] 是唯一规范形式

| 位置 | 存储形式 |
| --- | --- |
| `finding` | `evidence_refs[]`（**必填，非空**） |
| `extraction_signal` | `evidence_refs[]` + 可选 `observation_refs[]` |
| `system_limitation` | `evidence_refs[]`（可为空数组：输入截断等情形无处可指） |
| `extracted_field` | `evidence_refs[]` |
| `provenance` | `evidence_ref`（**单个**字符串） |
| `evaluation_matrix` 条目 | `evidence_refs[]` |

**渲染层**（`templates/review_report.md`）负责把 ref 展开成引文与页码；
**机器可读 JSON 保留 ref**，同时在顶层附完整 `evidence_registry`，使 JSON 自洽可校验。

**禁止**在上述任何位置内联 `evidence[]` 对象数组。旧契约的内联形式见 §10 迁移表。

### 1.5 external evidence 示例

```json
{
  "id": "EV-120",
  "type": "external",
  "database": "ClinicalTrials.gov",
  "endpoint": "https://clinicaltrials.gov/api/v2/studies/NCT01234567",
  "query": {"query_kind": "trial_registration", "normalized_input": "NCT01234567"},
  "record_id": "NCT01234567",
  "retrieved_at": "2026-08-07T03:20:00Z",
  "database_version": "2026-08-07",
  "http_status": 200,
  "retrieval_status": "resolved",
  "response_sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "parser_version": "clinicaltrials_gov/1.0.0",
  "assertions": [{
    "predicate": "study_first_submit_date",
    "subject": "NCT01234567",
    "external_value": "2021-05-04",
    "unit": null,
    "source_path": "protocolSection.statusModule.studyFirstSubmitDate"
  }],
  "created_by": "stage_3c_external_validation"
}
```

### 1.6 X1 获取、缓存与重试契约

1. X1 只接受 Stage 3b 封闭后的 `lookup_request`：`request_id`、`connector`、
   `query_kind`、`normalized_input`、稿件 `present` evidence refs 与请求断言。X1 只产
   `external` evidence、`external_validation_candidate` signal 或 X1 本地
   `system_limitation`，**禁止产 finding**。
2. 缓存键为 `sha256(connector_version + HTTP method + endpoint template + 排序后的规范化参数
   + Accept)`；响应体按原始字节计算 SHA-256。缓存保存状态码、响应头中的 ETag/Last-Modified、
   获取时间、数据库版本与 parser 版本，不保存凭证；缓存目录由运行参数指定，不进入提交包。
3. 同一次审核运行首次成功响应后冻结，不在运行中刷新。`resolved` 缓存默认 TTL 24 小时；
   精确标识符的 `not_found` 与语义查询的 `not_addressed` 最多缓存 1 小时；过期条目优先用
   `If-None-Match` / `If-Modified-Since` 复核。429、5xx、网络异常与解析失败不得负缓存为
   `not_found`。
4. 仅对连接超时、读超时、429、502、503、504 重试，最多 4 次；等待 1、2、4 秒，
   有 `Retry-After` 时取其值但上限 120 秒。400/401/403/404 不重试；401/403/白名单拦截
   记 `external_access_denied`，404 仅在精确标识符规则满足时记 `not_found`。
5. 所有 connector 先执行本地格式校验再联网，并遵守数据源公布的速率限制；无凭证时不得
   通过提高并发绕过限流。离线模式或 X1 未执行时，Stage 1–5 仍须完整结束。

### 1.7 locator 字段表

| 字段 | 说明 |
| --- | --- |
| `section` | 归一化章节名，取 Stage 1 枚举 |
| `subsection` | 小节编号，如 `"2.4"` |
| `paragraph_id` | Stage 1 分配的段落 id |
| `pdf_file_page` | **PDF 物理页码**（从 1 起数），PDF 输入必填 |
| `printed_page` | **印刷页码**，能识别则填，否则 `null` |
| `supplement_page` | 补充材料内页码 |
| `figure` / `panel` | 图号与面板号 |
| `table` | 表号 |
| `supplement_id` | 补充材料标识，如 `"S1"` |
| `xml_id` | JATS/XML 元素 id，XML 输入必填 |
| `scope` | `document` / `section` / `paragraph` / `figure` / `panel` / `table` / `supplement` |

**渲染形式**（仅供展示，不作存储）：`fig:3B | p.7 | sec:methods§2.4`；
缺失型渲染为 `absence:document`。**禁止**把自由文本作为 locator 的唯一存储形式。

---

## 2. 数值契约

### 2.1 numeric value 变体（全局唯一形式）

**任何数值一律使用带 `type` 标签的对象，禁止裸数字、禁止字符串区间。**

```
point | interval | lower_bound | upper_bound | categorical
```

| type | 形状 | 用于 |
| --- | --- | --- |
| `point` | `{"type": "point", "number": 12.4}` | 明确报告的点值 |
| `interval` | `{"type": "interval", "low": 40, "high": 50}` | 像素估读、原文给出的范围 |
| `lower_bound` | `{"type": "lower_bound", "low": 100}` | `> 100`、`≥ LLOQ` |
| `upper_bound` | `{"type": "upper_bound", "high": 0.001}` | `p < 0.001`、`< LOD` |
| `categorical` | `{"type": "categorical", "label": "not_detected"}` | `ND` / `n.s.` / 分级标签 |

**明令禁止**：`"value": "40–50"`、`"value": 12.4`、`"value": "<0.001"`。
旧字符串区间的迁移见 §10。

### 2.2 unit 与 uncertainty

```json
{
  "unit": "μM",
  "unit_normalized": "uM",
  "uncertainty": {"type": "95CI", "low": 9.8, "high": 15.7}
}
```

- `unit` 保留稿件原写法；`unit_normalized` 保存归一化器返回的 `ucum_code`，只是单位
  拼写的审计轨迹，**不表示 `value` 已换算**。兼容性比较必须调用归一化器取
  `factor_a_to_b`，按 §5.4 对数值的工作副本做换算；禁止因两个 `unit_normalized`
  字符串相同就直接比较未换算的原数值。无量纲指标 `unit: null`、
  `unit_normalized: null`。
- **归一化由 Skill 根目录相对路径 `scripts/normalize_biomed_units.py` 执行**
  （一期能力，只用标准库）。
  它是 fail-closed 的：只做**同量纲**确定性换算；未登记别名返回 `unknown_unit`，
  调用方据此判 `ambiguous`，**不得猜**。三条永不合并的量纲边界：
  剂量 `mg/kg` ≠ 速率 `mg/kg/day`；按体重 `mg/kg` ≠ 按体表面积 `mg/m2`；
  质量浓度 ↔ 摩尔浓度**必须**同时给出 analyte 与明确分子量，
  否则返回 `conversion_requires_molecular_weight`，**绝不用近似分子量代换**。
- `uncertainty.type` 枚举：`SD` / `SEM` / `95CI` / `IQR` / `range` / `none`。
  `SD` / `SEM` 用 `{"type": "SD", "value": 1.2}`；区间型用 `low` / `high`。

### 2.3 provenance（含 derivation，必填）

**所有数值型结果必须带 `provenance`，且 `provenance.derivation` 必填** ——
否则 §8.3 的 pixel / OCR 依赖率无法计算。

```json
{
  "source_type": "explicit_figure_caption",
  "source_id": "fig:2C",
  "evidence_ref": "EV-014",
  "derivation": {
    "extraction_method": "caption_parse",
    "ocr_used": false
  }
}
```

**`source_type` 枚举（全局唯一，五值，所有文件与示例必须一致）**：

```
explicit_main_text | explicit_table | explicit_figure_caption | axis_readable | pixel_estimated
```

**`derivation.extraction_method` 枚举**：

```
text_parse | table_parse | caption_parse | axis_read | visual_estimation | ocr_text
```

**`derivation.ocr_used`**：布尔，`true` 表示该数值经过 OCR 文本层。
`extraction_method = ocr_text` 当且仅当 `ocr_used = true`；其余五种方法的
`ocr_used` 必须为 `false`。

**`source_type` × `extraction_method` 合法组合**（其余组合为契约违规）：

| source_type | 允许的 extraction_method |
| --- | --- |
| `explicit_main_text` | `text_parse`, `ocr_text` |
| `explicit_table` | `table_parse`, `ocr_text` |
| `explicit_figure_caption` | `caption_parse`, `ocr_text` |
| `axis_readable` | `axis_read` |
| `pixel_estimated` | `visual_estimation` |

**两级来源分类**（§5.5 canonical 选择的基础）：

```
explicit_reported  = {explicit_main_text, explicit_table, explicit_figure_caption}
visually_derived   = {axis_readable, pixel_estimated}
```

### 2.4 pixel_estimated 的强制约束

`source_type: "pixel_estimated"` 时**同时**满足，缺一即为契约违规：

1. `value.type` 必须为 `interval` 且 `low < high`；仅当图像可见范围把真实值截在边界外、
   只能支持单侧约束时才可用 `lower_bound` / `upper_bound`；不得用 `low == high` 的
   零宽区间或单侧边界伪装 `point`；
2. `extraction_confidence` 必须为 `low`；
3. `manual_review_needed` 必须为 `true`；
4. **不得**作为 M4 任何统计复算或一致性检验的输入；
5. 引用它的 finding，其 `review_confidence` 上限为 `medium`。

`axis_readable` 允许 `point`，但 `extraction_confidence` 上限为 `medium`。

---

## 3. 字段契约（extracted_field）

### 3.1 三个正交维度

旧契约把「适用性」与「必填性」混在 `not_applicable` 一个值里，导致
「不进覆盖率分母」被错写成「本研究不适用」。**三者独立存储**：

| 维度 | 字段 | 回答的问题 |
| --- | --- | --- |
| 适用性 applicability | `applicability` | 这个概念对本研究/本实验**说得通吗**？ |
| 必填性 requiredness | `requiredness` | 这个设计**多大程度上应该**报告它？ |
| 抽取状态 status | `status` | 我们**实际抽到了什么**？ |

```
applicability : applicable | not_applicable | applicability_uncertain
requiredness  : required | recommended | optional
status        : reported | not_reported | not_applicable | ambiguous
                | conflicting | parse_failed | unresolved
```

**判定顺序固定**：先定 `applicability`（依 §9.1 的路由优先级），
再定 `requiredness`，最后由检索结果定 `status`。

### 3.2 组合语义（唯一合法映射）

| applicability | 检索结果 | status | 附加必填 |
| --- | --- | --- | --- |
| `applicable` | 找到明确报告 | `reported` | ≥1 条 `present` 证据 |
| `applicable` | 完整检索后确认未报告 | `not_reported` | ≥1 条 `absence` 证据 |
| `applicable` | 有相关文本但读不出唯一解 | `ambiguous` | ≥1 条 `present`（指向歧义文本） |
| `applicable` | 多来源不兼容 | `conflicting` | 见 §5（key_data）或 `candidate_refs[]` |
| `applicable` | 等待 Stage 3 视觉解析 | `unresolved` | `resolution_state` 块，见 §4 |
| `applicable` | 技术原因抽不出 | `parse_failed` | `system_limitation_ref` |
| `not_applicable` | ——（不检索） | `not_applicable` | `na_reason` |
| `applicability_uncertain` | —— | `ambiguous` | 关联 `ambiguous_study_design` signal |

**`requiredness` 不改变 `status`**，只改变覆盖率分母（§8.2）与下游 severity 基线。

### 3.3 结构

```json
{
  "field_path": "measurement.sample_size_justification",
  "applicability": "applicable",
  "requiredness": "required",
  "status": "not_reported",
  "value": null,
  "unit": null,
  "evidence_refs": ["EV-019"],
  "extraction_confidence": "high",
  "na_reason": null,
  "resolution_state": null,
  "system_limitation_ref": null,
  "candidate_refs": [],
  "alternatives": []
}
```

- `value` 为 §2.1 的 numeric 对象、字符串、结构化对象或 `null`。
  `status ∈ {not_reported, not_applicable, ambiguous, conflicting, parse_failed, unresolved}`
  时 `value` **必须**为 `null`。
- `alternatives[]`：**抽取器对同一事实的不同解读**（我们不确定），每项 `{value, evidence_refs}`。
- `candidate_refs[]`：`status: conflicting` 时指向 §5 的 `observation_id`。
- **禁止**用裸 `null` 编码多种缺失状态。

### 3.4 三条不可混淆的边界

1. **`not_reported` ≠ `parse_failed`** —— 前者是**稿件**没写（已检索确认），
   **可以**成为 M2/M4/M6 的 finding 依据；后者是**我们**没读出来，
   **绝不可**成为稿件 finding，只降 `extraction_coverage` 与 confidence。
   无法确定属于哪一种时，一律用 `parse_failed` —— 宁可承认看不清，不可冤枉稿件。

2. **`not_reported` ≠ `not_applicable`** —— 前者「该写没写」，后者「本来就不需要写」。
   **不得**因为某字段不在覆盖率分母内就判 `not_applicable`（§3.1）。

3. **`ambiguous` ≠ `conflicting`** —— 前者是**一处**文本读不出唯一解；
   后者是**多处**来源互相打架，且已通过 §5.4 判定为不兼容。
   来源之间**无法建立可比性**时用 `ambiguous`，**不得**自动判 `conflicting`。

### 3.5 抽取置信度 vs 报告完整性（正交）

| 概念 | 字段 | 回答 |
| --- | --- | --- |
| 抽取置信度 | `extraction_confidence`: `high`/`medium`/`low` | 我们读出的值就是稿件写的值吗？ |
| 报告完整性 | `reporting_completeness`: `complete`/`incomplete`/`not_assessed` | 稿件对这个数值报全了吗？ |

例：图注写明 `IC50 = 12.4 μM` 但无 CI 与拟合方法 →
`extraction_confidence: "high"` + `reporting_completeness: "incomplete"`。
**两者不得互相传染。**

---

## 4. pending 生命周期（unresolved）

M1 在 Stage 2 遇到「文本没有、但图里可能有」的字段时，**不得**判 `parse_failed`
—— Stage 3 尚未尝试，谈不上失败。使用 `unresolved` 生命周期状态：

```json
{
  "field_path": "objective.primary_endpoint",
  "applicability": "applicable",
  "requiredness": "required",
  "status": "unresolved",
  "value": null,
  "resolution_state": {
    "state": "pending_visual_resolution",
    "pending_stage": "stage_3",
    "expected_sources": ["fig:2C"]
  },
  "evidence_refs": ["EV-022"],
  "extraction_confidence": "high",
  "system_limitation_ref": null
}
```

**规则**

1. `status: "unresolved"` **只允许出现在 `structured_result_v1`**。
2. 它**不是** `system_limitation`，**不得**填 `system_limitation_ref`。尚将执行
   Stage 3b 的模式不提前结算覆盖率；若 `structured_extraction` 以 v1 为终态输出，
   则按本节末的规则把它计入 `unresolved_required_fields[]`。
3. `resolution_state.state` 一期只有一个值：`pending_visual_resolution`。
   `pending_stage` 恒为 `stage_3`。`expected_sources[]` 至少一项，形如 `fig:2C` / `table:3`。
4. **Stage 3b 必须把每个 `unresolved` 解析为**下列之一：
   `reported` / `not_reported` / `ambiguous` / `conflicting` / `parse_failed`。
5. **`structured_result_v2` 中不得出现 `status: "unresolved"`**，
   也不得出现非空 `resolution_state`。这是 §11 lint 的强制检查项。
6. 只有 Stage 3 **真正尝试并失败**（图像不可读、面板缺失）才可转为 `parse_failed`，
   并**必须**关联一条 `system_limitation`。

**Stage 3b 未执行时**（如 `structured_extraction` 无视觉需求模式）：
输出停在 v1，`unresolved` 合法保留，但该字段计入
`coverage_breakdown.unresolved_required_fields[]`，且输出必须标注 `stage_3b_executed: false`。

**要求 v2 的模式**：若 v1 的当前 scope 内存在 `unresolved`，编排器必须先执行
覆盖其 `expected_sources[]` 的 Stage 3，再进入 Stage 3b。Stage 3 未执行时，
Stage 3b 不得把该项改为 `not_reported` 或 `parse_failed`：前者缺完整检索，
后者缺真实解析尝试，两者均违反状态机。

---

## 5. key_data 观测组契约

### 5.1 为什么是「组」而不是「点」

同一个 IC50 可能同时出现在图注、正文、表格。旧契约的扁平 `key_data` 只能存一个值，
合并时必然静默覆盖。**`key_data[]` 的每个元素是一个观测组（observation group）**，
组内保留全部来源，组本身承载合并结论。

### 5.2 结构

```json
{
  "id": "KD-007",
  "metric_name": "IC50",
  "metric_family": "dose_response",
  "grouping_key": {
    "experiment_id": "EXP-02",
    "group": "Compound A",
    "comparison": "Compound A vs vehicle",
    "timepoint": "72h",
    "endpoint": "cell_viability"
  },
  "status": "conflicting",
  "canonical_observation": null,
  "canonical_rationale": null,
  "observations": [
    {
      "observation_id": "OBS-014",
      "value": {"type": "point", "number": 12.4},
      "unit": "μM",
      "unit_normalized": "uM",
      "uncertainty": {"type": "95CI", "low": 9.8, "high": 15.7},
      "n": 3,
      "replicate_type": "biological",
      "provenance": {
        "source_type": "explicit_figure_caption",
        "source_id": "fig:2C",
        "evidence_ref": "EV-014",
        "derivation": {"extraction_method": "caption_parse", "ocr_used": false}
      },
      "extraction_confidence": "high",
      "manual_review_needed": false
    },
    {
      "observation_id": "OBS-015",
      "value": {"type": "point", "number": 15.1},
      "unit": "μM",
      "unit_normalized": "uM",
      "uncertainty": {"type": "none"},
      "n": 3,
      "replicate_type": "biological",
      "provenance": {
        "source_type": "explicit_main_text",
        "source_id": "results-p8",
        "evidence_ref": "EV-015",
        "derivation": {"extraction_method": "text_parse", "ocr_used": false}
      },
      "extraction_confidence": "high",
      "manual_review_needed": false
    }
  ],
  "compatible_observations": [],
  "conflicting_observations": ["OBS-014", "OBS-015"],
  "reporting_completeness": "not_assessed",
  "missing_elements": [],
  "signal_refs": ["SIG-002"]
}
```

### 5.3 组 status 枚举

```
reported | compatible_multiple_sources | conflicting | ambiguous
| pending_visual_resolution | parse_failed
```

| status | 含义 | `canonical_observation` |
| --- | --- | --- |
| `reported` | 单一来源，正常报告 | 该唯一 `observation_id` |
| `compatible_multiple_sources` | 多来源且已判定兼容 | 按 §5.5 选出的 id |
| `conflicting` | 多来源且已判定不兼容 | **`null`** |
| `ambiguous` | 同组观测无法建立可比性（单位不可归一 / 数值变体不可比） | **`null`** |
| `pending_visual_resolution` | 仅 v1 合法，等待 Stage 3 | **`null`** |
| `parse_failed` | Stage 3 尝试后仍无法读出 | **`null`** |

**`pending_visual_resolution` 不得出现在 v2**（与 §4 规则 5 同）。
`pending_visual_resolution` 与 `parse_failed` 的 `observations[]` 为空；前者必须带
`resolution_state`，后者必须带 `system_limitation_ref`。`reported` 恰有一个 observation；
`compatible_multiple_sources` 与 `conflicting` 至少两个。

### 5.4 分组与兼容性判定（Stage 3b 执行）

**第一步 · 分组。** Stage 2 文本观测使用所在组的 `grouping_key`；Stage 3 图观测
必须携带 `metric_family`、规范化 `metric_name` 与 `target_grouping_key`。Stage 3b 先要求
两个 observation 的指标身份相同，再比较五键**全部相等**：
`experiment_id` / `group` / `comparison` / `timepoint` / `endpoint`
（`null` 与 `null` 视为相等；一方为 `null` 另一方有值视为**不相等**）。
指标身份或分组键不匹配 → 是两个不同的 `key_data`，**不是冲突**。
`metric_name` 使用本项目指标词表的规范名（如 `IC50`）；原文写法保留在
observation 的证据与 `quote`，不用原始大小写或别名参与分组。

Stage 3 图观测与既有组完全匹配则并入；没有完全匹配的组就新建组，不按相似名称
猜配。入组时移除 `target_grouping_key` / `metric_name` / `metric_family` 三个临时路由字段，
由组级字段承载它们；其余 `observation_core` 字段必须逐字段原样保留，包括
`observation_id` / `value` / `unit` / `unit_normalized` / `uncertainty` / `n` /
`replicate_type` / `provenance` / `extraction_confidence` / `manual_review_needed` / `quote`。
同一 `observation_id` 在两个 Stage 3 副本中出现时，含三个路由字段在内的全部字段必须
完全相同；它在 `structured_result_v2.key_data` 中的落盘副本必须与移除三个路由字段后的
`observation_core` 完全相同，且目标组的指标身份与五键必须等于原路由字段。任一不一致时，
Stage 3b 必须停止该 id 入组并产出 `category: "parse_failed"` 的 `system_limitation`，
把该 `observation_id` 写入 `affected_targets[]`；不得择一覆盖或仅比较 `value` /
`provenance`。`structured_result_v2` 中每条 Stage 3 图观测必须恰好落入一个 `key_data`
组，或被这类 Stage 3b limitation 明确拒收；既未落盘又未列入 `affected_targets[]` 即为
无轨迹数据丢失。

**第二步 · 可比性。** 同组内对全部无序 observation 对逐对判定，顺序固定；
每一对必须得到 `compatible` / `conflicting` / `ambiguous` 中的恰好一个结果：

1. **单位门控与工作值换算**。双方 `unit` 均为 `null`，或原单位字符串完全相同时，
   换算因子为 1。其余情形必须运行 `scripts/normalize_biomed_units.py --compare`。
   调用时把 `observation_id` 字典序较大者的单位作为 `unit_a`、较小者作为 `unit_b`。
   返回 `comparable` 时，恒将较大 id 的观测换算到较小 id 的单位：
   用 `factor_a_to_b` 同比例乘其 `value` 的 `number/low/high`、`uncertainty`
   的 `value/low/high` 与原文精度单位 `u`，只形成本次比较的工作副本，不改写
   `observations[]`。`unknown_unit` / `incomparable_dimension` /
   `conversion_requires_molecular_weight` 一律→ `ambiguous`。质量浓度↔摩尔浓度只有
   analyte 与稿件明示的正分子量都存在时才可传入脚本。
2. **分类值**。双方均为 `categorical` 且 `label` 完全相同 → `compatible`；
   标签不同 → `ambiguous`。`categorical` 与任一数值型组合 → `ambiguous`。
3. **先比数值本体**。双方均为 `point`：取原表示精度较低一方的最后一位
   有效数字单位 `u`，`tol = 0.5 × u`。`|a − b| ≤ tol` → 数值本体兼容；
   否则→ `conflicting`。若两数值 JSON 完全相等则直接视为本体兼容；否则原文
   不足以恢复 `u` 时→ `ambiguous`。例：`12.4` vs `12.43` 的 `tol = 0.05`，
   差 `0.03` → 兼容；`12.4` vs `15.1` → 冲突。
4. **区间与边界型数值本体**。把 `interval`、`lower_bound`、`upper_bound`
   分别解释为闭约束 `[low, high]`、`[low, +∞)`、`(-∞, high]`；点值解释为
   `[number − tol, number + tol]`。两约束交集非空→数值本体兼容，否则→
   `conflicting`；点值 `tol` 无法恢复时→ `ambiguous`。
5. **再核对 uncertainty**。只有数值本体已兼容才执行。任一方为 `none`，
   或双方 type 不同，不用 uncertainty 覆盖本体结果。同为 `SD` / `SEM` 时比较
   `value`；同为 `95CI` / `IQR` / `range` 时分别比较对应 `low` 与 `high`。
   对应值 JSON 相等则通过；否则用各自原表示的舍入区间判定：舍入区间有交集
   才通过，无交集→ `conflicting`，无法恢复精度→ `ambiguous`。
   **禁止用两个 95% CI 有重叠代替点估计与区间端点的一致性核对**；
   CI 重叠只说明两个不确定范围相交，不能证明稿件两处报告的是同一数值。
6. **兜底**。任一必需分支未覆盖或无法执行→ `ambiguous`。不得默认为冲突。

**第三步 · 组状态与归档。** `compatible_observations[]` 收录至少参加一对
`compatible` 关系的 id；`conflicting_observations[]` 收录至少参加一对
`conflicting` 关系的 id，同一 id 可以同时出现在两者中。数组按 id 字典序去重。

- 只有一个 observation → `reported`；
- 存在任一 `conflicting` 对 → `conflicting`；
- 无冲突但存在任一 `ambiguous` 对 → `ambiguous`；
- 至少两个 observation 且全部配对均 `compatible` → `compatible_multiple_sources`。

**全部 observation 一律保留在 `observations[]`，禁止删除或静默覆盖。**

**第四步 · 出信号。** 存在 `conflicting_observations[]` → 产出一条
`source_value_conflict` signal（§6.2），`signal_refs[]` 回填。默认路由 M2/M4；若冲突组
至少含一个 `axis_readable` 或 `pixel_estimated` 观测，`routed_to` 还必须包含 M5，
由 M5 回查原图后判断是否构成 `figure_text_contradiction`。Stage 3b 只产 signal，不产 finding。

### 5.5 canonical_observation 的选择

**不使用「正文 > 表 > 图注 > 轴 > 像素」的绝对顺序**。该顺序在
「正文是四舍五入的叙述性摘要、表格才是完整结果」这一常见情形下是错的。

**唯一保留的绝对规则**：`explicit_reported` 一律优先于 `visually_derived`。
若组内同时存在两类且已判定兼容，canonical 必须取自 `explicit_reported`。

只有 `reported` 与 `compatible_multiple_sources` 可选择 canonical：前者直接选择唯一 observation；
后者先应用绝对来源规则，再按下列判据做**稳定的逐层筛选**。每一层只保留该判据最优的
候选；剩一项即停止，多项并列才进入下一层。**只有当本层判据能从每个剩余
候选的 observation 与 `evidence_ref` 恢复时才应用该层**；任一候选的本层信息缺失，
必须对全体跳过该层，不得把“未知”当成“较差”。

| # | 判据 | 说明 |
| --- | --- | --- |
| 1 | 稿件明示为主要数值结果 | 如「primary outcome」「主要终点」所在的表或段 |
| 2 | 携带不确定度信息 | 有 CI/SD/SEM 者优于裸点值 |
| 3 | 有效数字精度更高 | `12.43` 优于 `12.4` |
| 4 | 非叙述性四舍五入摘要 | 表格/图注的完整结果优于正文的「约 12 μM」 |
| 5 | 该指标族要素更齐全 | 依 `01-structured-extraction.md §6.3` |
| 6 | 以上全部持平 | 取 `observation_id` 字典序最小者，保证可复现 |

单一 observation 的理由写 `single_observation`。多来源选中后**必须**在
`canonical_rationale` 写明首个排除其他候选的层：绝对来源规则命中时写
`"source_class: explicit_reported over visually_derived"`；表中判据命中时写判据编号与理由，
如 `"criterion_2: fig:2C 带 95% CI，results-p8 为裸点值"`；全部并列时写
`"criterion_6: observation_id lexical minimum"`。

`ambiguous` / `conflicting` / `pending_visual_resolution` / `parse_failed` 的
`canonical_observation` 一律为 `null`；不得在这些状态下运行上述排序。

### 5.6 reporting_completeness 与指标族

指标族要素表见 `01-structured-extraction.md §6.3`。
`reporting_completeness` 在**组层级**判定，取 `canonical_observation` 的要素齐备情况；
`canonical_observation` 为 `null` 时一律 `not_assessed`，`missing_elements` 为空数组。

---

## 6. 三类顶层记录（不可混用）

**判断归属的唯一标准：这是稿件的问题，还是我们的观察，还是我们的能力限制？**

| 契约 | 产出者 | 有 severity | 影响 |
| --- | --- | --- | --- |
| `finding` | **仅 M2–M7** | ✅ `critical`/`major`/`minor`/`info` | 稿件风险分 |
| `extraction_signal` | Stage 2、Stage 3、Stage 3b、可选 X1 | ❌ 无 | 路由给下游判定，本身不是结论 |
| `system_limitation` | Stage 1 / 2 / 3 / 3b、可选 X1 | ❌ 无 | 披露能力限制；不增加稿件风险 |

**M1 不产出任何 `finding`。** 旧契约的 `extraction_quality_findings[]` 已废除，
迁移映射见 §10。

### 6.1 finding · 稿件级审核判断

```json
{
  "id": "M4-003",
  "module": "M4",
  "category": "power_and_sample_size",
  "severity": "major",
  "title": "组间比较未报告样本量依据与效应量",
  "detail": "Fig 3B 三组比较使用 one-way ANOVA，各组 n=3 且未说明为生物学或技术重复；正文与方法节均未见效能分析或效应量报告。",
  "evidence_refs": ["EV-018", "EV-019"],
  "rule_ref": "04-statistics#sample-size-reporting",
  "review_confidence": "high",
  "derived_from_signals": ["SIG-004"],
  "related_findings": [],
  "manual_review": {
    "action": "核对 n=3 指生物学重复还是技术重复；要求作者补充效能分析或效应量",
    "who": "statistical_reviewer",
    "priority": "P1"
  }
}
```

**枚举（不得自创）**

- `module`: `M2` / `M3` / `M4` / `M5` / `M6` / `M7`。**`M1` 非法。**
- `severity`: `critical`（结论不成立 / 伦理违规 / 疑似不端）> `major`（需作者补材料或重做分析）
  > `minor`（表述与规范问题）> `info`（提示）
- `review_confidence`: `high` / `medium` / `low` —— 指**本条判断本身**的可靠程度。
- `category`: 必须是该模块 reference 文件已登记的 slug。
- `manual_review.who`: `statistical_reviewer` / `domain_reviewer` / `ethics_committee` /
  `editor` / `author`
- `manual_review.priority`: `P0` / `P1` / `P2`

**人工复核优先级的唯一口径**

- `P0`：不先核对就无法可靠解释核心结论、伦理授权或数据完整性；全部 critical 固定为
  P0，直接阻断核心结论解释的 major 也可为 P0。
- `P1`：不阻断其他结论阅读，但会改变 major finding 的成立、严重度或作者必须补交的
  分析/材料。major 若不满足 P0 条件则固定为 P1。
- `P2`：minor/info 的报告澄清、定位核对或编辑性修正，不改变当前核心推断。

P0/P1/P2 是核对顺序，不是 severity，不进入风险分。同一优先级内按 severity 降序、
finding id 升序排列。

**硬性规则**

1. `evidence_refs[]` **必须非空**，且每项在登记表中可解析。
2. `severity >= major` 的 finding **必须**有非空 `manual_review.action`。
3. 证据中含 `pixel_estimated` 或指向 `ambiguous` 字段的 finding，
   `review_confidence` 上限为 `medium`。
4. **`system_limitation` 不得转成 finding**。若确要就同一位置立 finding，
   必须**另行**给出稿件证据（`present` 或合规的 `absence`）。
5. `derived_from_signals[]` 只作溯源，**不得**替代 `evidence_refs[]`
   —— 仅凭 signal id 立 finding 为契约违规。
6. critical 的 `manual_review.priority` 必须为 P0；major 只能为 P0/P1；minor/info 若设置
   priority 只能为 P2。每条 critical/major 必须进入报告级 `manual_review_plan`；minor/info
   设置了 P2 且 action 非空时也必须进入。
7. 凡引用 `external` evidence 的 finding，`evidence_refs[0]` 必须解析到稿件内
   `present` evidence，且 refs 中至少各有一条 `present` 与 `external`。外部记录只能核验
   稿件中**实际出现的主张、标识符或数值**；`absence + external` 不能替代稿件内锚点。
8. `external.retrieval_status ∈ {not_found, not_addressed}`、X1 `system_limitation` 或
   `external_check.comparison_result ∈ {not_comparable, needs_manual_review}` 均不得单独支撑
   finding。数据库没查到、接口失败或语义不可比绝不等于稿件有问题。

### 6.2 extraction_signal · 机器级观察

```json
{
  "id": "SIG-002",
  "type": "source_value_conflict",
  "target": "key_data.KD-007",
  "detail": "IC50 图注 12.4 μM (95% CI 9.8–15.7)，正文 15.1 μM 无区间；四舍五入容差 0.05，差值 2.7，判定不兼容。",
  "observation_refs": ["OBS-014", "OBS-015"],
  "evidence_refs": ["EV-014", "EV-015"],
  "routed_to": ["M2", "M4"],
  "produced_by": "stage_3b"
}
```

**`type` 枚举（十五值）**

| type | 触发条件 | 路由到 | 下游判定什么 |
| --- | --- | --- | --- |
| `source_value_conflict` | 同一观测组多来源不兼容（§5.4） | M2（主）、M4；含视觉来源时再路由 M5 | 是否构成稿件内部矛盾；M5 判断图文矛盾 |
| `claim_without_resolved_evidence_link` | claim 的 `supported_by` 解析不到任何 `key_data.id` 或证据 | M7 | 是否构成无支撑主张 |
| `ambiguous_study_design` | 设计线索冲突或不足以唯一归类 | M2、M3、M4、M6 | 是否构成设计描述不清 |
| `unresolved_cross_reference` | 正文引用的图/表/补充材料解析不到实体 | M2、M5 | 是否构成引用错误 |
| `partial_extraction` | 字段部分抽出（有 n 无分组归属、有剂量无单位） | M4、M5 | 是否构成报告不完整 |
| `ambiguous_extraction` | 字段 `status: ambiguous`，存在文本但读不出唯一解 | M2、M4 | 是否构成表述不清 |
| `test_statistic_p_mismatch` | 由检验统计量与自由度反算的 p 落在报告值的舍入区间之外 | M4 | 是否构成统计报告错误 |
| `ci_estimate_mismatch` | 点估计落在其自身报告的置信区间之外，或区间端点不合法 | M4 | 是否构成结果报告错误 |
| `count_percentage_mismatch` | 计数与百分比不自洽（计数超分母，或百分比超出舍入区间） | M4、M2 | 是否构成数据报告错误 |
| `grim_incompatible_mean` | 整数量表均值在给定 n 下不存在可行整数总和（GRIM） | M4 | 是否构成汇总统计不可能 |
| `table_total_mismatch` | 互斥穷尽的分类计数之和不等于声明的分母 | M4、M2 | 是否构成表格计数错误 |
| `ethics_requirement_unmet` | 规范库某条伦理要求适用，但稿件未见对应报告 | M6 | 是否构成伦理合规问题 |
| `sequence_identifier_inconsistent` | 变异命名/序列/登录号/基因符号存在明确违规，或表达式超出本地解析子集、需人工复核 | M2、M3 | 是否构成表述或方法学错误 |
| `figure_integrity_candidate` | 图像审计检出候选重复区域、背景拼接不连续或异常均匀区块 | M5 | 人工核对原图、图注与合法复用说明后，是否构成图像完整性问题 |
| `external_validation_candidate` | X1 对稿件 `present` 事实与 `external` 原子事实完成可比性判定 | M2、M4、M6、M7 | 回查稿件与外部记录后，是否存在身份、注册、统计或主张不一致 |

> 五种统计取证 signal（`test_statistic_p_mismatch`、`ci_estimate_mismatch`、
> `count_percentage_mismatch`、`grim_incompatible_mean`、`table_total_mismatch`）由
> `scripts/statistical_forensics.py` 在 Stage 2 产出（路径相对 Skill 根目录），
> **不需要原始数据**，
> 是一期就能做的确定性一致性检验（`produced_by: "stage_2"`，`routed_to: ["M4"]`）。
> 它们**仍然只是 signal** —— 工具层不下稿件结论，是否构成稿件问题由 M4 判定。
> 每种检验的适用前提见该脚本文档；**前提不满足一律产出 `partial_extraction` 而不是猜**。
> Stage 2 构造脚本输入时应同时传入已绑定的 `observation_refs[]` / `evidence_refs[]`；脚本原样
> 保留这些 ref，但不会自行生成 locator。`test_statistic_p_mismatch.forensics` 必须保存
> `test_family`、`statistic`、`tail` 与相应自由度，确保 M4 可独立复算。

`ethics_requirement_unmet` 与 `sequence_identifier_inconsistent` 分别由
`scripts/ethics_compliance_check.py`、`scripts/sequence_identifier_audit.py` 在 Stage 2 产出。
序列工具只把位点越界、明确参考残基不符、受支持数据库的格式违规和非法字母表视为
确定性检查；其中位点越界与参考残基不符还必须具备完整参考序列、accession 与版本。
给了序列但参考上下文不全时产 `partial_extraction`，不得把序列片段当完整参考判错。
超出其 HGVS 子集的表达式必须标 `candidate: true`，不得当作语法错误。

**规则**

1. signal **没有 `severity`**，**不直接**影响 `manuscript_risk_score`。
2. `produced_by` 取 `stage_2` / `stage_3` / `stage_3b` /
   `stage_3c_external_validation`。
   `stage_3` **仅**用于图像完整性审计 —— 它是像素级机器观察，
   自然产生于图像解析阶段；`stage_3c_external_validation` **仅**用于
   `external_validation_candidate`；两者都**不产出 finding**。
3. `claim_without_resolved_evidence_link` 的 `target` 必须携带目标元数据：
   `{"claim_id": "CLM-03", "unresolved_refs": ["Fig 5D"]}`，
   **不另设** `unresolved_evidence_links[]` 数组（§10）。
4. 旧 `parse_failure` type **已废除** —— 解析失败是 `system_limitation`，不是 signal（§10）。
5. `external_validation_candidate` 必填 `external_check`，并同时引用至少一条稿件内
   `present` 与一条 `retrieval_status: resolved` 的 `external` evidence；顶层
   `evidence_refs[]` 必须恰好覆盖 `external_check` 的两组 refs。`not_found` / `not_addressed`
   没有可比较原子事实，不得创建 signal。`comparison_result` 只取 `match` / `mismatch` /
   `not_comparable` / `needs_manual_review`；只有 `mismatch` 可进入下游 finding 候选，仍须
   接收模块独立回查证据。**X1 可路由 M2/M3/M4/M5/M6/M7，不路由 M1**（M1 只抽取标识符供 X1 使用，自身不产 finding）。
   每个 `check_type` 必须在接收模块的 reference 里登记消费判据，否则运行时模型拿到 signal 无处安放。

> **图像完整性审计的定性禁令。** `figure_integrity_candidate` 的
> `image_audit.severity_hint` **恒为 `null`**，`candidate` 恒为 `true`，
> `manual_review_required` 恒为 `true`。图像重复有大量正当解释（同一对照组复用、
> 模板化示意图、放大插图），把它自动化为学术不端指控是本项目名誉风险最高的动作。
> M5 据此立 finding 时，**必须**先人工核对原图；且沉默不代表图像无问题
> —— 该方法只覆盖网格对齐的重复，不覆盖旋转与缩放。

### 6.3 system_limitation · 系统能力限制

```json
{
  "id": "SYS-004",
  "category": "figure_unreadable",
  "impact": "Figure 4 的面板 B 无法解析，M4 与 M5 对该图的审核不完整",
  "affected_modules": ["M4", "M5"],
  "affected_targets": ["fig:4B"],
  "affected_fields": ["key_results.tumor_volume_day28"],
  "evidence_refs": ["EV-041"],
  "recommended_action": "调取原始高分辨率图件或矢量 PDF 后重新解析",
  "produced_by": "stage_3"
}
```

**`category` 枚举（十二值）**

```
parse_failed | figure_unreadable | table_unparseable | supplement_inaccessible
| section_missing_from_input | ocr_low_quality | encoding_error | input_truncated
| external_source_unavailable | external_access_denied | external_rate_limited
| external_response_unparseable
```

**硬性规则**

1. **没有 `severity` 字段。** 它不是稿件问题。
2. Stage 1–3b 限制本身不直接扣分；只有它使 scope 内字段成为 `parse_failed`、资产不可读、
   补充材料不可得，或使 observation 依赖 pixel/OCR 时，才通过 §8 已声明的变量降低
   `extraction_coverage` 与 confidence。X1 限制只降低后续
   `external_validation_coverage`（未落地前只展示），**不得改变现有三项评分**，更不得提高
   `manuscript_risk_score`。
3. **不得**在无独立稿件证据的情况下转成稿件缺陷（§6.1 规则 4）。
4. 报告中必须单列一节 —— 让人看到「哪些地方我们没看清」。
5. `produced_by` 取 `stage_1` / `stage_2` / `stage_3` / `stage_3b` /
   `stage_3c_external_validation`；四类 `external_*` category 只能由 X1 产出。

### 6.4 边界矩阵（争议情形的唯一判法）

| 情形 | 正确契约 | 错误做法 |
| --- | --- | --- |
| 补充材料引用了但下载不到 | `system_limitation: supplement_inaccessible`；依赖字段 `parse_failed` | 判 `not_reported` 并立缺失 finding |
| 图片糊到读不出坐标 | `system_limitation: figure_unreadable` | 立「图表质量差」finding |
| 稿件确实没写伦理声明（已全文检索） | 字段 `not_reported` + `absence` 证据 → M6 立 finding | 判 `parse_failed` |
| 正文与图注数值打架 | `source_value_conflict` signal → M2 判定 | M1 直接立 `internal_inconsistency` finding |
| 字段等 Stage 3 解析 | `status: unresolved` | `parse_failed` + `pending_visual_resolution: true` |
| 单位不可归一无法比较 | 组 status `ambiguous` | 组 status `conflicting` |
| 外部主机未进白名单、429、5xx 或响应结构漂移 | X1 `system_limitation`；离线流程继续 | `not_found`、mismatch signal 或 finding |
| 精确登录号权威 404 | `external: not_found`；最多进入人工核对，不自动 finding | 宣称编号虚假或数据不可用 |
| 名称/语义查询零命中 | `external: not_addressed` | 当作外部反证 |

---

## 7. 非记录对象

以下两者**不是记录**，不得称为 finding，不得带 `severity`。

### 7.1 execution_scope · 执行范围

**一切覆盖率与置信度的分母都取自本对象。** 全模式必填。

```json
{
  "execution_scope": {
    "mode": "targeted_check",
    "submode": null,
    "executed_stages": ["stage_1", "stage_2", "stage_3b"],
    "executed_modules": ["M6"],
    "skipped_modules": ["M2", "M3", "M4", "M5", "M7"],
    "fields": ["declarations.ethics_statement", "declarations.informed_consent",
               "population.subjects"],
    "assets": [],
    "observations": [],
    "supplements": ["S1"],
    "scope_rationale": "用户仅询问伦理声明是否齐全"
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `mode` | `full_review` / `structured_extraction` / `figure_analysis` / `targeted_check` |
| `submode` | 仅 `figure_analysis` 使用：`interpretation_only` / `figure_review`；其余为 `null` |
| `executed_stages[]` | `stage_1` / `stage_2` / `stage_3` / `stage_3b` / `stage_3c_external_validation` / `stage_4` / `stage_5`；X1 未运行时不列该值 |
| `executed_modules[]` | 实际运行的审核模块；非审核模式为空数组 |
| `skipped_modules[]` | `full_review` 下为空数组 |
| `fields[]` | 进入覆盖率分母的字段路径全集 |
| `assets[]` | 进入 `asset_readability_rate` 分母的图表 id |
| `observations[]` | 进入 pixel/OCR 比率与冲突计数分母的 `observation_id` 全集 |
| `supplements[]` | 进入 `supplement_accessibility` 分母的补充材料 id |

**硬性规则**：任何阶段**不得**消费未在 `executed_stages[]` 中声明的上游产物。
这是 §11 lint 的强制检查项。

### 7.2 coverage_breakdown · 覆盖率明细

```json
{
  "coverage_breakdown": {
    "resolved_fields": ["population.subjects", "declarations.informed_consent"],
    "unresolved_required_fields": [
      {"field_path": "declarations.ethics_statement", "status": "parse_failed",
       "reason_ref": "SYS-007"}
    ],
    "unreadable_assets": [],
    "inaccessible_supplements": ["S1"],
    "scope_denominators": {
      "required_fields_total": 3,
      "assets_total": 0,
      "supplements_total": 1
    }
  }
}
```

**规则**

1. 本块的条目**不是 finding**，不进 `issue_clusters[]`，不影响 `manuscript_risk_score`。
2. `resolved_fields[]` 与 `unresolved_required_fields[]` 之和
   **必须**等于 `scope_denominators.required_fields_total`。
3. `unresolved_required_fields[]` 的 `reason_ref` 指向 `system_limitation.id`
   或 `extraction_signal.id`；`status: not_reported` 的字段**属于已解析**，进 `resolved_fields[]`。

---

## 8. 评分契约

三项指标**互不替代，分别输出**，报告中不得合并为单一数字。
**禁止**把稿件风险分称作「置信度」。
当前权重、category 上限、分段阈值、惩罚系数与 `0.5` 提示阈值均为**未经语料标定的
初始专家参数**。本节保证的是确定性复算，不是经验校准；报告不得把分值表述为概率、
经验证的稿件质量测量或录用/退稿界值。

### 8.1 manuscript_risk_score · 稿件风险分（0–100）

以 §9.3 的 `issue_clusters[]` 为计分单位（防止一个问题拆成多条放大分数）。
每簇只归入 `representative_finding` 的 `category` 计分；`categories[]` 仅用于展示，
不得让同一簇在多个 category 下重复得分：

```
每簇权重 w：critical 25 / major 10 / minor 3 / info 0
  （簇内取最高 severity，只计一次）
每个 category 的累计上限：30
manuscript_risk_score = min(100, Σ_category min(30, Σ_cluster w))
```

**不因** PDF 不可读或解析失败而升高 —— 那属于 coverage 与 confidence。

**partial 语义**

```json
{
  "manuscript_risk_score": {
    "value": 22,
    "partial": true,
    "executed_modules": ["M6"],
    "skipped_modules": ["M2", "M3", "M4", "M5", "M7"],
    "comparable_to_full_review": false,
    "band": "partial_not_classified",
    "priority_manual_review": false,
    "threshold_caveat": "分段阈值未经实证验证，是初始经验值，不得表述为自动化的录用/退稿决定。"
  }
}
```

- `executed_modules` 未覆盖全部六个审核模块时，`partial` **必须**为 `true`。
- `partial: true` 的分数**禁止**与任何其他报告的风险分并列比较或排序，包括
  partial↔partial 与 partial↔`full_review`；报告与 JSON 均须带
  `comparable_to_full_review: false`，且 `band` 固定为 `partial_not_classified`，
  不得套用完整审核分段。
- 仅当 `executed_modules` 恰好覆盖 M2–M7 时，`partial` 才能为 `false`、
  `comparable_to_full_review` 才能为 `true`，并按下表生成 `band`。
- `executed_modules` 为空数组时**不得输出本项**（见 SKILL.md §1 模式约束）。

**下列分段仅用于 `partial: false` 的完整审核，且仅为筛查信号**
（阈值未经实证验证，报告中必须注明）：

| 分数 | 标签 |
| --- | --- |
| 0–19 | `routine_review` |
| 20–49 | `clarification_needed` |
| 50+ | `major_revision_suggested` |

出现任一 `critical` 簇时，无论分数如何，`priority_manual_review = true`。

### 8.2 extraction_coverage · 抽取覆盖率（0.0–1.0）

**全部分母取自 `execution_scope`（§7.1）**，禁止用全文分母评估单图任务。

```
field_resolution_rate
  分子 = |execution_scope.fields 中 applicability=applicable ∧ requiredness=required
          ∧ status ∈ {reported, not_reported} 的字段|
  分母 = |execution_scope.fields 中 applicability=applicable ∧ requiredness=required 的字段|
  （status ∈ {ambiguous, conflicting, parse_failed, unresolved} 计为未解析）
  （applicability = not_applicable 或 applicability_uncertain 的字段不入分子分母）
  分母为 0 → 1.0（与下面两个子率同规则；如仅解读一张图时 scope 内无条件必填字段）

asset_readability_rate
  分子 = |execution_scope.assets 中 readable 的图表|
  分母 = |execution_scope.assets|
  分母为 0 → 1.0

supplement_accessibility
  分子 = |execution_scope.supplements 中可得的|
  分母 = |execution_scope.supplements|
  分母为 0 → 1.0

extraction_coverage = 0.60 × field_resolution_rate
                    + 0.25 × asset_readability_rate
                    + 0.15 × supplement_accessibility
```

各子率的 `rate` 与三项最终小数分数均以**未舍入的分子/分母**计算，最后四舍五入到
小数点后三位；不得用已显示的三位子率继续连乘。`manuscript_risk_score` 保持整数。

**报告必须给出显式分子分母**，不只给加权结果：

```json
{
  "extraction_coverage": 0.78,
  "field_resolution": {"resolved": 12, "total": 15, "rate": 0.80},
  "asset_readability": {"resolved": 6, "total": 8, "rate": 0.75},
  "supplement_accessibility": {"resolved": 0, "total": 1, "rate": 0.0},
  "recommended_field_coverage": {"resolved": 4, "total": 7, "rate": 0.571}
}
```

`recommended_field_coverage` 为**可选**的旁路指标，统计
`requiredness = recommended` 的字段，**不进** `extraction_coverage` 加权。

### 8.3 confidence · 两个互斥指标

**跑过至少一个审核模块** → 输出 `review_confidence`；
**一个都没跑**（`structured_extraction`、`figure_analysis / interpretation_only`）
→ 输出 `output_confidence`。**二者不得同时输出。**

**`output_confidence`**（无审核结论可言，只反映抽取本身的稳固程度）：

```
pixel_share = |execution_scope.observations 中 source_type = pixel_estimated 的 id|
              / max(1, |execution_scope.observations|)
ocr_share   = |execution_scope.observations 中 derivation.ocr_used = true 的 id|
              / max(1, |execution_scope.observations|)

Q_out = max(0, 1 − 0.30 × pixel_share − 0.20 × ocr_share)
output_confidence = extraction_coverage × Q_out
```

**`review_confidence`**（系统对自身审核结论的支撑强度）：

```
pixel_dependency_rate = |evidence_refs 关联到 scope 内 pixel_estimated observation 的 finding|
                        / max(1, |finding 总数|)
ocr_dependency_rate   = |evidence_refs 关联到 scope 内 ocr_used=true observation 的 finding|
                        / max(1, |finding 总数|)
low_conf_finding_rate = |review_confidence = low 的 finding| / max(1, |finding 总数|)

Q = max(0, 1 − 0.30 × pixel_dependency_rate
              − 0.20 × ocr_dependency_rate
              − 0.10 × low_conf_finding_rate)
C = max(0, 1 − 0.10 × min(|status=conflicting 且未消解的 key_data 组|, 5))

review_confidence = extraction_coverage × Q × C
```

**关联算法固定如下**：先用 `execution_scope.observations[]` 取得 scope 内 observation，
再把 observation 的 `provenance.evidence_ref` 与 finding 的 `evidence_refs[]` 求交；交集非空
即认定该 finding 依赖该 observation。一个 observation id 在 `structured_result` 与
`figure_records` 重复出现时按一个计数，重复副本的 `value` 与 `provenance` 必须完全一致。
`finding 总数` 取 `all_findings[]` 长度。冲突数只统计至少含一个 scope observation 的
`key_data.status = conflicting` 组。

**可计算性保证**：上述每个变量都能从已声明字段直接算出 ——
`provenance.source_type`（§2.3）、`provenance.derivation.ocr_used`（§2.3）、
`finding.review_confidence`（§6.1）、`key_data.status`（§5.3）。
**不得**定义无法从 schema 推出的评分变量。

`review_confidence < 0.5` 时，报告首屏必须提示
「本次审核证据基础较弱，结论仅供参考」。

---

## 9. 路由优先级、聚合与聚簇

### 9.1 适用性路由优先级（自高向低，命中即停）

```
1. 实验级类型规则   design_components[].type 对该 experiment_id 的专门规则
2. 文章级专门规则   article_design.primary_design.type 的专门规则（如 case_report）
3. 族级规则         article_design.primary_design.family 的规则
4. 默认规则         通用字段清单
```

字段清单与各级规则见 `01-structured-extraction.md §5`。
**专门规则覆盖族级规则**：`case_report` 的 `not_applicable(randomization)`
覆盖 `human_observational` 族的通用要求。

### 9.2 阶段本地产物与最终聚合

**每个数组有且只有一个产出者。** 跨阶段同名数组一律拆为阶段本地数组，
再由单一聚合器合并 —— 这是旧契约「一个产物一个产出者」被违反的根因。

`execution_scope` 不是 Stage 5 产物：由执行规划步骤在 Stage 1 前初始化；遇到条件阶段时，
规划步骤必须先把该阶段加入 `executed_stages[]`，再允许阶段读取上游产物。Stage 5 只读取并
原样写入最终报告，不得重建或改写执行历史。

| 阶段本地数组 | 产出者 |
| --- | --- |
| `stage1_system_limitations[]` | Stage 1 |
| `stage2_system_limitations[]` | Stage 2 (M1) |
| `stage3_system_limitations[]` | Stage 3 (Figure Parser) |
| `stage3b_system_limitations[]` | Stage 3b |
| `external_system_limitations[]` | X1 (`stage_3c_external_validation`) |
| `m1_extraction_signals[]` | Stage 2 (M1) |
| `stage3_extraction_signals[]` | Stage 3（图像完整性审计） |
| `merge_extraction_signals[]` | Stage 3b |
| `external_validation_signals[]` | X1 (`stage_3c_external_validation`) |
| `m2_findings[]` … `m7_findings[]` | 对应审核模块 |

| 聚合产物 | **唯一聚合器** | 组成 |
| --- | --- | --- |
| `all_system_limitations[]` | **Stage 5**（非 `full_review` 模式为输出装配步骤） | Stage 1/2/3/3b 四个数组 + 可选 `external_`，按 id 升序拼接 |
| `all_extraction_signals[]` | 同上 | `m1_` + `stage3_` + `merge_` + 可选 `external_validation_` 拼接 |
| `all_findings[]` | **Stage 5** | `m2_`…`m7_` 六个数组拼接 |
| `issue_clusters[]` | **Stage 5** | 对 `all_findings[]` 执行 §9.3 |

**已废除的冗余数组**：`source_conflict_signals[]`、`unresolved_evidence_links[]`、
`extraction_quality_findings[]`。迁移见 §10。

### 9.3 去重与聚簇（Stage 5，顺序固定）

1. **同模块内建子簇** —— 同一模块内 `category` 相同、且**主锚点**相同的 findings 归入同一子簇。
   **主锚点定义**：`evidence_refs[0]` 解析出的证据，比较其 locator 的
   `figure`+`panel`（有图时）或 `paragraph_id`（无图时）或 `table`；上述定位均不存在，
   或证据为 `absence` 时，退回比较 `evidence_refs[0]` 本身。
   保留 `severity` 最高者为代表；同 severity 时取 finding id 字典序最小者，
   其余 id 进代表的 `related_findings[]`。**本步不删除、合并或改写 `all_findings[]`**；
   否则 §9.2 的“六个本地数组按序拼接”与评分复算将失去原始输入。
2. **跨模块聚簇** —— 不同模块命中同一主锚点且语义重合时构成一个 `issue_cluster`。
   保留 `severity` 最高的一条为簇代表；同 severity 时取 finding id 字典序最小者。
   **不要把同一个问题报告六遍。**
3. **簇内证据并集** —— `issue_cluster.evidence_refs[]` 取全部成员 `evidence_refs[]`
   的并集，按 id 去重后保留；不回写或改写任一 finding 的 `evidence_refs[]`。

```json
{
  "cluster_id": "CL-002",
  "representative_finding": "M4-003",
  "member_findings": ["M4-003", "M2-011"],
  "categories": ["power_and_sample_size", "internal_inconsistency"],
  "max_severity": "major",
  "anchor": {"figure": "3", "panel": "B"},
  "evidence_refs": ["EV-018", "EV-019", "EV-020"]
}
```

`issue_clusters[]` 是 §8.1 计分的唯一单位。

---

## 10. 迁移表（旧契约 → 新契约）

**不保留任何向后兼容的别名。** 旧字段一律按下表改写，改完即删。

| 旧形式 | 新形式 | 说明 |
| --- | --- | --- |
| `extraction_quality_findings[]` 之 `ambiguous_extraction` | `extraction_signal` type `ambiguous_extraction` | §6.2 |
| `extraction_quality_findings[]` 之 `required_field_unresolved` | `coverage_breakdown.unresolved_required_fields[]` | §7.2，非记录 |
| `source_conflict_signals[]` | `merge_extraction_signals[]` 中 type `source_value_conflict` | §9.2 |
| `unresolved_evidence_links[]` | signal `claim_without_resolved_evidence_link` 的 `target` 元数据 | §6.2 规则 3 |
| signal type `parse_failure` | `system_limitation`（category `parse_failed`） | §6.3；signal 枚举已删该值 |
| 内联 `evidence[]` 对象数组 | `evidence_refs[]` + 顶层 `evidence_registry` | §1.4 |
| `provenance.locator` 内联 | `provenance.evidence_ref` | §2.3 |
| `source_type: "text"` | `explicit_main_text` | §2.3 |
| `source_type: "table"` | `explicit_table` | §2.3 |
| `source_type: "figure"` / `"figure_caption"` | `explicit_figure_caption` | §2.3 |
| `source_type: "figure_axis"` | `axis_readable` | §2.3 |
| `source_type: "figure_pixel"` | `pixel_estimated` | §2.3 |
| `"value": "40–50"` | `{"type": "interval", "low": 40, "high": 50}` | §2.1 |
| `"value": 12.4` | `{"type": "point", "number": 12.4}` | §2.1 |
| `status: parse_failed` + `pending_visual_resolution: true` | `status: unresolved` + `resolution_state` 块 | §4 |
| 扁平 `key_data` 单值对象 | 观测组（`observations[]`） | §5.2 |
| `evaluation_matrix.min_group_n` 整数 | `group_sizes[]` 数组 | `01-…md §11.4` |
| `reporting_completeness: "not_applicable"` | `not_assessed` | §3.5 |
| 绝对来源顺序「正文>表>图注>轴>像素」 | 两级分类 + §5.5 有序判据 | §5.5 |

---

## 11. 契约 lint 检查表

**输出任何结构化内容前逐条自检；任一项不通过即为无效输出。**

```
[ ] 全部 enum 取值合法（source_type 五值 / extraction_method 六值 / status 七值 /
    applicability 三值 / requiredness 三值 / severity 四值 / signal type 十五值 /
    system_limitation category 十二值 / key_data status 六值 / numeric type 五值）
[ ] 全部 §x.y 内部引用可解析到本仓库真实存在的小节
[ ] 全部 evidence_ref / evidence_refs[] 在 evidence_registry 中解析到恰好一个条目
[ ] 全部 observation_refs[] 在对应 key_data.observations[] 中可解析
[ ] 每个数组产物都在 §9.2 声明了唯一产出者或唯一聚合器
[ ] 没有任何阶段消费 execution_scope.executed_stages[] 之外的产物
[ ] structured_result_v2 中不存在 status = "unresolved" 或非空 resolution_state
[ ] structured_result_v2 中不存在 key_data.status = "pending_visual_resolution"
[ ] 没有 system_limitation 携带 severity
[ ] 没有 finding 的 module 为 M1
[ ] 每条 finding 的 evidence_refs[] 非空
[ ] severity >= major 的 finding 均有非空 manual_review.action
[ ] type = "absence" 的证据均无 quote 字段
[ ] type = "external" 的证据均由 X1 创建、带响应 hash/版本，且不含凭证或稿件 locator/quote
[ ] 引用 external evidence 的 finding 以 present evidence 为首锚点，且同时含 present + external
[ ] X1 失败只产 external_* system_limitation，不产 mismatch signal 或 finding
[ ] 全部数值为 §2.1 的 numeric 对象，无裸数字、无字符串区间
[ ] 全部 pixel_estimated 数值满足 §2.4 五项强制约束
[ ] 全部 provenance 带 derivation，且 source_type × extraction_method 组合合法
[ ] 覆盖率与置信度的分母全部取自 execution_scope
[ ] 未跑审核模块的模式不输出 review_confidence 与 manuscript_risk_score
[ ] executed_modules 未覆盖六个审核模块时 manuscript_risk_score.partial = true
[ ] partial 风险分未与任何其他报告的风险分并列比较或排序
[ ] coverage_breakdown 的条目未被称为 finding
[ ] resolved_fields + unresolved_required_fields = scope_denominators.required_fields_total
```
