# 路由规范：L0 条目 + 工具信号 → 专家（全文 + 规则库 + 索引）→ 确定性工具

> 这张表是 L0/L0b 与 L1 专家之间的接口：决定每类问题交给谁、附带哪些索引与工具。
>
> 核心原则（架构公理）：**隔离的是审阅目标与规则，不是论文正文。**
> 每个专家都拿全文，但只拿**自己那一本**规则库。
> 指标不是「读满八个 reference」，而是「这次任务要求的 reference 一个不漏」。

## 0. 为什么需要显式路由

上一版没有路由层，后果是模型自己决定读什么 —— 实测一次全流程只读了
`00-contracts` 一个文件，七个模块规则库一个没读。既没有人告诉它
「这篇论文的哪些问题该查哪本规则」，它就只能凭直觉，而直觉倾向于
「先把契约读了再说」，注意力全花在形式上。

显式路由把这件事变成可检查的：**要求读的读了没有，可以算成一个比率。**

## 1. 主路由表

| 候选类型 | 专家 | 证据包 | 规则库 | 确定性工具 |
| --- | --- | --- | --- | --- |
| `possible_internal_inconsistency` | M2 | 跨节包 | `02-macro-logic` | `statistical_forensics`（数值可算时） |
| `possible_reporting_omission` | M2 | 方法包 + 声明包 | `02-macro-logic` | — |
| `possible_data_leakage` | M2 | 方法包（建模部分） | `02-macro-logic` | — |
| `possible_reference_problem` | M2 | 参考文献包 | `02-macro-logic` | `external_figure_validation`（`reference_exists` / `cited_retracted`） |
| `possible_method_underreporting` | M3 | 方法包 | `03-experimental-methods` | — |
| `possible_cell_line_issue` | M3 | 方法标识符包 | `03-experimental-methods` | `external_figure_validation`（`cell_line`） |
| `possible_identifier_issue` | M3 | 方法标识符包 | `03-experimental-methods` | `sequence_identifier_audit` + X1（`variant` / `gene_symbol` / `species` / `rrid`） |
| `possible_animal_necessity_issue` | M3 | 方法包 + 伦理包 | `03-experimental-methods` | — |
| `possible_statistical_test_mismatch` | M4 | 统计包 | `04-statistics` | — |
| `possible_sample_size_issue` | M4 | 统计包 | `04-statistics` | `statistical_forensics`（可算时） |
| `possible_numeric_inconsistency` | M4 | 统计包 + 表格 | `04-statistics` | `statistical_forensics`（**必跑**） |
| `possible_multiplicity_issue` | M4 | 统计包 | `04-statistics` | — |
| `possible_outcome_switching` | M4 | 统计包 + 注册信息 | `04-statistics` | X1（`outcome_switching`） |
| `possible_figure_presentation_issue` | M5 | 图包 | `05-figures-and-charts` | — |
| `possible_figure_duplication` | M5 | 图包（原图） | `05-figures-and-charts` | `figure_integrity_audit`（**必跑**） |
| `possible_figure_text_contradiction` | M5 | 图包 + 相关 Results | `05-figures-and-charts` | — |
| `possible_blot_annotation_issue` | M5 | 图包 | `05-figures-and-charts` | X1（`blot_band`） |
| `possible_ethics_issue` | M6 | 伦理包 | `06-ethics-compliance` | `ethics_compliance_check` |
| `possible_registration_issue` | M6 | 伦理包 + 注册信息 | `06-ethics-compliance` | X1（`trial_registration`） |
| `possible_consent_issue` | M6 | 伦理包 | `06-ethics-compliance` | `ethics_compliance_check` |
| `possible_unsupported_claim` | M7 | 主张-证据包 | `07-conclusions-discussion` | — |
| `possible_overgeneralization` | M7 | 主张-证据包 + 人群描述 | `07-conclusions-discussion` | — |
| `possible_followup_overreach` | M7 | 主张-证据包 + 随访时长 | `07-conclusions-discussion` | — |
| `possible_causal_overreach` | M7 | 主张-证据包 + 研究设计 | `07-conclusions-discussion` | — |
| `possible_unit_dimension_issue` | M4 / M3 | 剂量与单位相关段落 | 对应规则库 | `normalize_biomed_units`（**必跑**） |

## 2. 歧义与兜底

候选类型无法确定时，按以下顺序兜底，**不得直接丢弃**：

1. **候选可路由到多个专家** → 全部路由。同一问题被两个专家各立一条 finding，
   由 Layer 4 全局校正合并（`merged`），这比漏掉安全。
2. **候选类型不在上表** → 路由到 M2（宏观逻辑是默认接收方），
   并在 `candidate_resolution_log` 记 `routing_fallback: true`。
3. **候选描述过于笼统、无法定位证据** → 状态记 `unresolved`，
   **不得**记 `rejected` —— 那是我们没定位到，不是问题不存在。
4. **跨节问题**（两个 section 互相矛盾）→ 仍然进 L4 全局校正队列汇总，
   但**不再是因为专家看不到** —— 专家现在有全文，也应该主动报跨节矛盾；
   L4 的价值转为**汇总、去重、审计**，以及对 L0 条目做最终归宿判定。

## 3. 索引定义（原「证据包」）

> **重要变更（架构公理）**：专家现在**拿全文**。下表不再是「专家只能看这些」，
> 而是「这些位置已知相关，从这里开始看」。**索引是起点，不是边界。**
> 旧写法「全篇论文不得整篇塞给专家」已作废 —— 实测证明那会让最深的科学问题
> 结构性不可发现（见 SKILL.md §0.0）。

| 包 | 内容 |
| --- | --- |
| 方法包 | Methods 全节、试剂与设备段落、样本来源、相关 Supplement 方法 |
| 方法标识符包 | Methods 中的细胞系、抗体/RRID、基因符号、物种品系、登录号、变异写法 |
| 统计包 | 统计方法段落、相关 Results 段落、表格、图注中的统计量、样本量、检验、p 值、CI |
| 图包 | 图像本身、图注、正文首次引用处、相关 Results 段落、相关方法 |
| 伦理包 | 研究设计摘要、人/动物受试者方法、伦理声明、知情同意、注册信息、利益冲突与数据可得性声明 |
| 主张-证据包 | 主张原文、支撑该主张的 Results、关联表/图、随访时长、研究人群、局限性段落 |
| 参考文献包 | 参考文献列表、DOI/PMID、正文引用位置 |
| 跨节包 | `paper_map` + `claim_map` + 涉及的两个及以上 section 的相关段落 |
| 声明包 | 资助、利益冲突、数据可得性、作者贡献、注册号 |

**所有索引都附带轻量全局上下文**（见 §4）。

## 4. 每个专家必带的全局上下文

除全文外，仍要给这份摘要 —— 它让专家一眼看清自己在看什么，省去重新推断：

```json
{
  "study_design": "randomised controlled trial",
  "experiment_id": "EXP-02",
  "supports_claims": ["CL-05"],
  "related_figures": ["Figure 4"],
  "related_tables": ["Table 3"],
  "n_total": 89,
  "followup_duration": "48 hours"
}
```

统计专家一眼就知道 Table 3 属于 EXP-02、支撑 CL-05，不必自己从头推断；
但**该读 Discussion 时仍然要去读** —— 全文就在它手里。

## 5. 工具的两种触发模式

工具**不只**用来验证 LLM 的候选，还要**主动扫**。
后者尤其重要：真正的增益往往来自裸模型根本不会想到去做的确定性检查。

| 模式 | 触发 | 例 |
| --- | --- | --- |
| **候选验证** | 专家怀疑某处有问题 → 请求工具核算 | 怀疑分母对不上 → `statistical_forensics` 复算 |
| **主动扫描** | 解析出结构化对象即自动跑，不等候选 | 表格解析出计数列 → 自动跑 `table_total_mismatch` |

主动扫描的对象清单：

| 解析到什么 | 自动跑什么 |
| --- | --- |
| 任何含互斥穷尽分类计数的表格 | `statistical_forensics.table_total` |
| 任何「计数 + 百分比」 | `statistical_forensics.count_percentage` |
| 任何「均值 + 整数量表 + n」 | `statistical_forensics.grim` |
| 任何检验统计量 + df + p | `statistical_forensics.test_statistic_p` |
| 任何点估计 + CI | `statistical_forensics.ci_estimate` |
| 任何细胞系名 | X1 `cell_line` |
| 任何 NCT 注册号 | X1 `trial_registration` + `outcome_switching` |
| 参考文献列表全部 DOI | X1 `reference_exists` + `cited_retracted` |
| 任何人类基因符号 | X1 `gene_symbol` |
| 任何图像文件 | `figure_integrity_audit` |
| 任何剂量单位对 | `normalize_biomed_units` |

**主动扫描不得因为「没有候选指向它」而跳过。**

## 6. 每条最终 finding 必须标注来源

```
global_review | specialist_rule | deterministic_tool | external_validation |
cross_section_reconciliation | multiple_sources
```

这是判断「本架构到底有没有增益」的唯一依据：`global_review` 独有的部分是裸模型
本来就有的，**不算增益**；其余来源独有的部分才是。若增益很小，
说明五千行规则库贡献有限，应当据此裁剪而不是继续加规则。
