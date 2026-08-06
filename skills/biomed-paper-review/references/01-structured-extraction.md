# M1 · 结构化抽取：抽取关键信息

**负责人：MZYY（陈泓睿）** · 状态：**框架已定，规则库填充中**

本模块是全流程的**输入层**。M2–M7 全部消费本模块的输出，因此这里的错误会放大七倍。
唯一的安全策略是：**宁可留空，不可推断。**

---

## 1. 输出对象

`structured_result`，四个核心维度 + 两个辅助块。完整模式见 `../schemas/structured_result.schema.json`。

```
structured_result
├── meta            题名、期刊、年份、DOI、文章类型、通讯作者单位
├── objective       研究目标
├── methods         实验方法
├── key_data        核心数据
├── conclusion      初步结论
├── evaluation_matrix   评估矩阵（供 M2–M7 快速查表）
└── gaps[]          未能抽取的必填字段登记
```

---

## 2. 字段定义

### 2.1 objective · 研究目标

| 字段 | 说明 | 必填 |
| --- | --- | --- |
| `research_question` | 论文要回答的问题，一句话 | ✅ |
| `hypothesis` | 明确陈述的假设；无则 `null` | |
| `study_type` | `in_vitro` / `in_vivo_animal` / `clinical_trial` / `observational` / `meta_analysis` / `computational` / `mixed` | ✅ |
| `primary_endpoint` | 主要终点/主要观测指标 | ✅ |
| `secondary_endpoints[]` | 次要终点 | |

> `study_type` 是**路由字段**：M3 用它决定是否启动动物实验必要性检查，M4 用它选统计规范表，M6 用它决定是否要求伦理批件。抽错会导致三个下游模块跑错规则集。

### 2.2 methods · 实验方法

| 字段 | 说明 | 必填 |
| --- | --- | --- |
| `subjects` | 物种/品系/细胞系/人群，含来源 | ✅ |
| `groups[]` | 每组：`{name, n, intervention, dose, route, duration}` | ✅ |
| `control_type` | `vehicle` / `sham` / `placebo` / `untreated` / `historical` / `none` | ✅ |
| `randomization` | 方法描述；未提及填 `"not_reported"` | ✅ |
| `blinding` | `none` / `single` / `double` / `not_reported` | ✅ |
| `assays[]` | 每项：`{name, purpose, reference_citation}` | ✅ |
| `stats_methods[]` | 每项：`{test, applied_to, software, correction}` | ✅ |
| `sample_size_justification` | 效能分析或依据；未提及填 `"not_reported"` | ✅ |

> `"not_reported"` 与 `null` 含义不同：`"not_reported"` = 我们确认论文没写（这是 M2/M4 的一条 finding 线索）；`null` = 我们没抽出来（这是我们的 gap）。**不要混用。**

### 2.3 key_data · 核心数据

每条数据点：

```json
{
  "id": "KD-007",
  "metric": "IC50",
  "value": 12.4,
  "unit": "μM",
  "ci": {"type": "95CI", "low": 9.8, "high": 15.7},
  "n": 3,
  "replicate_type": "biological",
  "group": "Compound A vs vehicle",
  "p_value": 0.003,
  "test": "two-way ANOVA + Tukey",
  "source": "figure",
  "evidence": {"locator": "fig:2C | p.5", "quote": "IC50 = 12.4 μM (95% CI 9.8–15.7)"},
  "confidence": "high"
}
```

**三要素规则**：`value` 必须同时具备 `unit`、`n`、误差信息（`ci` 或 `sd`/`sem`）。
缺一 → `confidence` 降一级；缺二及以上 → `confidence: low` 且写入 `gaps[]`。

`source` 取值：`text`（正文明写）/ `table` / `figure_caption` / `figure_axis`（读坐标轴）/ `figure_pixel`（像素估读）。
`figure_pixel` **强制** `confidence: low`，且 `value` 必须写成区间。

### 2.4 conclusion · 初步结论

| 字段 | 说明 |
| --- | --- |
| `claims[]` | 每条：`{statement, scope, supported_by[]}`，`supported_by` 填 `key_data.id` 或 locator |
| `limitations_stated[]` | 作者自述的局限 |
| `generalization_scope` | 作者主张的适用范围（物种/人群/条件） |

> `claims[].supported_by` 为空 = 论文提出了没有数据支撑的主张，**直接移交 M7**，这是 M7 最重要的输入。

### 2.5 evaluation_matrix · 评估矩阵

会议纪要要求结构化结果表"具备评估矩阵功能"。一张固定的布尔/枚举速查表，让 M2–M7 无需重读全文即可判断该跑哪些规则：

| 键 | 值 | 谁在用 |
| --- | --- | --- |
| `has_animal_experiment` | bool | M3, M6 |
| `has_human_subjects` | bool | M6 |
| `has_ethics_statement` | bool | M6 |
| `has_randomization` | bool | M3, M4 |
| `has_blinding` | bool | M3, M4 |
| `has_power_analysis` | bool | M4 |
| `has_multiple_comparison_correction` | bool | M4 |
| `min_group_n` | int | M4 |
| `has_data_availability` | bool | M2 |
| `has_conflict_of_interest` | bool | M2 |
| `figure_count` / `table_count` | int | M5 |
| `all_figures_cited_in_text` | bool | M2, M5 |

### 2.6 gaps · 缺口登记

```json
{"field": "methods.sample_size_justification", "reason": "not_found_in_text",
 "searched": ["Methods §2.6", "Supplementary S1"], "impact": "M4 无法评估效能"}
```

`reason` 取值：`not_found_in_text` / `ambiguous` / `conflicting_values` / `parse_failed`。
`conflicting_values`（同一数值在正文与图注中不一致）**同时**记为 M2 的矛盾 finding。

---

## 3. 抽取顺序

1. **Methods 优先**，不要从 Abstract 开始。摘要是作者的宣传语，方法学才是事实来源。
2. Results 正文 → 补 `key_data`。
3. 图注（caption）→ 补 `key_data`，标 `source: figure_caption`。
4. 图像本体（交由阶段 ③）→ 只在前三步都拿不到时使用，标 `figure_axis` / `figure_pixel`。
5. Abstract **最后**读，仅用于交叉校验：**摘要与正文数值不一致是高价值 finding**（移交 M2），不要用摘要覆盖正文。

---

## 4. 本模块自己产出的 finding

| category slug | 触发条件 | severity |
| --- | --- | --- |
| `missing_core_field` | 必填字段为 `null` | major |
| `conflicting_values` | 同一数值在两处不一致 | major |
| `abstract_text_mismatch` | 摘要数值与正文不符 | major |
| `unit_missing` | 数值无单位 | minor |
| `n_undefined` | 未说明 n 或未区分生物学/技术重复 | major |
| `unsupported_claim` | `claims[].supported_by` 为空 | major |

---

## 5. TODO（一期）

- [ ] 补齐 `study_type` 判定的边界样例（如 ex vivo、类器官算哪一类）
- [ ] 补齐单位归一化表（μM/µM/uM、mg/kg vs mg·kg⁻¹）
- [ ] 与 M5 对齐 `key_data.source = figure_*` 时的字段交接口
- [ ] 在 `datasets/` 的 10 篇语料上跑一遍，统计必填字段实际缺失率

---

## 6. 二期扩展：标识符核验（本期不实现，规则先写下）

一期只抽取，不核验"抽出来的标识符是否真实存在"。二期接入 MCP 后逐项核验：

| 标识符 | 核验数据源 | 查出什么 |
| --- | --- | --- |
| 临床试验注册号 | ClinicalTrials.gov / ChiCTR | 号码不存在、与论文描述的终点不符、注册晚于入组（→ M6） |
| 细胞系名称 | Cellosaurus / ICLAC | 已知误认或交叉污染细胞系 |
| 抗体 / 试剂 | RRID (Antibody Registry) | 货号不存在、抗体已被证实无特异性 |
| 基因 / 蛋白符号 | HGNC / UniProt | 符号已废弃或写错、物种不匹配 |
| 参考文献 | Crossref / PubMed | 引用的文献不存在、已被撤稿（→ M2/M3） |

**注意**：本模块二期只负责**核验标识符本身的真实性**，核验结果的解读归对应模块 ——
注册号问题归 M6，撤稿引用归 M2，抗体特异性归 M3。不要在 M1 里下审核结论。

新增 category：`identifier_not_found`(major) / `identifier_mismatch`(major)
