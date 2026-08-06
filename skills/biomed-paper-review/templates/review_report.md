# 论文审核报告 · {{paper.title}}

> DOI: {{paper.doi}} ｜ 输入格式: {{paper.input_format}} ｜ 执行模块: {{paper.reviewed_modules}}
> **本报告由 AI 生成，仅覆盖审稿的基础环节，不构成录用或退稿决定。**

---

## 一、整体置信度

**{{confidence_score.score}} / 100 — {{confidence_score.band}}**

| critical | major | minor | info | 抽取缺口扣分 |
| --- | --- | --- | --- | --- |
| {{n_critical}} | {{n_major}} | {{n_minor}} | {{n_info}} | {{extraction_gap_penalty}} |

{{#if confidence_score.priority_manual_review}}
> ⚠️ **存在 critical 级发现，无论分数高低均需人工优先复核。**
{{/if}}

{{#each paper.skipped_modules}}
- 已跳过 {{module}}：{{reason}}
{{/each}}

---

## 二、结构化结果表

### 研究目标

| 项 | 内容 | 出处 |
| --- | --- | --- |
| 研究问题 | {{objective.research_question}} | {{locator}} |
| 假设 | {{objective.hypothesis}} | |
| 研究类型 | {{objective.study_type}} | |
| 主要终点 | {{objective.primary_endpoint}} | |

### 实验方法

| 项 | 内容 |
| --- | --- |
| 受试对象 | {{methods.subjects}} |
| 分组 | {{#each methods.groups}}{{name}} (n={{n}}, {{intervention}} {{dose}} {{route}} × {{duration}}){{/each}} |
| 对照类型 | {{methods.control_type}} |
| 随机化 / 盲法 | {{methods.randomization}} / {{methods.blinding}} |
| 统计方法 | {{#each methods.stats_methods}}{{test}}（{{applied_to}}，校正: {{correction}}）{{/each}} |
| 样本量依据 | {{methods.sample_size_justification}} |

### 核心数据

| ID | 指标 | 数值 | 单位 | n | 误差 | p | 来源 | 置信度 | 出处 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {{id}} | {{metric}} | {{value}} | {{unit}} | {{n}} | {{ci.type}} {{ci.low}}–{{ci.high}} | {{p_value}} | {{source}} | {{confidence}} | {{evidence.locator}} |

### 初步结论

| 主张 | 适用范围 | 支撑证据 |
| --- | --- | --- |
| {{statement}} | {{scope}} | {{supported_by}} |

### 评估矩阵

| 键 | 值 | | 键 | 值 |
| --- | --- | --- | --- | --- |
| 含动物实验 | {{has_animal_experiment}} | | 含人体受试 | {{has_human_subjects}} |
| 有伦理声明 | {{has_ethics_statement}} | | 有随机化 | {{has_randomization}} |
| 有盲法 | {{has_blinding}} | | 有效能分析 | {{has_power_analysis}} |
| 多重比较校正 | {{has_multiple_comparison_correction}} | | 最小组 n | {{min_group_n}} |
| 图 / 表数 | {{figure_count}} / {{table_count}} | | 图表全部被引用 | {{all_figures_cited_in_text}} |

### 抽取缺口

| 字段 | 原因 | 已检索位置 | 影响 |
| --- | --- | --- | --- |
| {{field}} | {{reason}} | {{searched}} | {{impact}} |

---

## 三、图表解读与原图定位

{{#each figure_records}}

### {{location.figure_label}}{{location.panel}} · {{chart_type}}

**原图定位**：{{location.figure_label}}{{location.panel}} ｜ p.{{location.page}} ｜ 正文首次引用于 {{location.first_cited_at}}

**解读**：{{interpretation}}

**实验条件**：分组 {{experimental_conditions.groups}}；剂量 {{experimental_conditions.dose_levels}}；
时间点 {{experimental_conditions.timepoints}}；n={{experimental_conditions.n_per_group}}（{{experimental_conditions.replicate_type}}）

**坐标轴**：x = {{axes.x.label}} ({{axes.x.unit}}, {{axes.x.scale}})；
y = {{axes.y.label}} ({{axes.y.unit}}, {{axes.y.scale}}{{#if axes.y.truncated}}，**已截断**{{/if}})

**抽取数值**：

| 指标 | 数值 | 来源 | 置信度 |
| --- | --- | --- | --- |
| {{metric}} | {{value}} {{unit}} | {{source}} | {{confidence}} |

{{#if curve_fit}}
**拟合**：{{curve_fit.model}}，IC50/EC50 = {{curve_fit.ic50_ec50}} {{curve_fit.unit}}，
Hill = {{curve_fit.hill_slope}}，拟合优度 {{curve_fit.goodness_of_fit}}
{{/if}}

**置信度**：{{confidence}}{{#if manual_review_needed}} ⚠️ 含像素估读或信息缺失，需人工核对原图{{/if}}

{{/each}}

---

## 四、七维审核发现

按 severity 降序。每条均附原文出处；无出处的发现已在生成阶段丢弃。

{{#each findings}}

### [{{severity}}] {{id}} · {{title}}

- **模块**：{{module}} ｜ **类别**：{{category}} ｜ **置信度**：{{confidence}}
- **出处**：`{{evidence.locator}}`
- **原文**：> {{evidence.quote}}
- **说明**：{{detail}}
- **依据规则**：`{{rule_ref}}`
{{#if related_findings}}
- **关联发现**：{{related_findings}}
{{/if}}

{{/each}}

---

## 五、人工复核建议

{{#each manual_review_plan}}

**[{{priority}}] {{action}}**
— 建议由：{{who}} ｜ 对应发现：{{finding_ids}}

{{/each}}

---

*{{confidence_score.disclaimer}}*
