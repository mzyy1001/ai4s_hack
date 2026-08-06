# M1 · 结构化抽取（前置层）

**负责人：MZYY（陈泓睿）** · 状态：**契约已定，规则库填充中**

M1 是流水线的**前置抽取层**，不是与 M2–M7 并列的审核模块。
M2–M7 全部消费 M1（经 Stage 3b 合并后）的产物，因此这里的错误会放大六倍。
唯一的安全策略是：**宁可标记状态，不可推断填充。**

**本文件依赖 `00-contracts.md`。** 证据登记表、数值变体、字段三维度、观测组、
三类记录、执行范围、评分公式的**定义**都在那里；本文件只定义 M1 的**字段清单、
设计路由与操作规则**。两者冲突时以 `00-contracts.md` 为准。

---

## 1. 职责与非职责

### 1.1 M1 做什么

| 职责 | 产物 |
| --- | --- |
| 从**文本来源**（正文、表格、图注文字）抽取结构化事实 | `structured_result_v1` |
| 为每个重要字段给出适用性 / 必填性 / 状态与证据 | `extracted_field`（§3） |
| 判定研究设计并据此决定哪些字段适用 | `article_design`（§4） |
| 把数值组织为观测组，为 Stage 3b 合并做准备 | `key_data[]`（§6） |
| 记录机器级观察，供下游解读 | `m1_extraction_signals[]`（§9） |
| 记录系统能力限制 | `stage2_system_limitations[]`（§10.2） |
| 登记全部证据 | 向 `evidence_registry` 追加条目（§10.1） |
| 提供路由索引 | `evaluation_matrix`（§11） |
| 提供覆盖率原始数据 | `coverage_inputs`（§12.2） |

### 1.2 M1 **不**做什么

**M1 不产出任何 `finding`。** 这是硬性契约，无例外。
`00-contracts.md §6.1` 规定 `finding.module` 只能取 `M2`–`M7`，`M1` 非法。

同一现象，M1 只描述「观察到什么」，由对应模块决定「这是否构成稿件问题」：

| 现象 | M1 输出 | 由谁判定 | 判定什么 |
| --- | --- | --- | --- |
| 两处数值不一致 | `source_value_conflict` signal | **M2** | 是否构成稿件内部矛盾 |
| claim 找不到支撑证据 | `claim_without_resolved_evidence_link` signal | **M7** | 是否构成无支撑主张 |
| 未见随机化描述 | `randomization.status = not_reported` + absence 证据 | **M3 / M4** | 是否构成设计缺陷 |
| 未见伦理声明 | `ethics_statement.status = not_reported` + absence 证据 | **M6** | 是否构成合规问题 |
| 未见样本量依据 | `sample_size_justification.status = not_reported` | **M4** | 是否构成统计报告缺陷 |
| 研究设计线索矛盾 | `ambiguous_study_design` signal | **M2 / M3 / M4** | 是否构成设计描述不清 |
| 字段存在但读不出唯一解 | `ambiguous_extraction` signal | **M2 / M4** | 是否构成表述不清 |
| 条件必填字段最终未解析 | `coverage_inputs.unresolved[]` 条目（**非记录**） | —— | 只降覆盖率 |
| 图像不可读 / 段落抽不出 | `system_limitation` | —— | 不是稿件问题，只降覆盖率 |

> **迁移提示**：旧版 M1 曾产出 `extraction_quality_findings[]`（含
> `ambiguous_extraction` 与 `required_field_unresolved` 两类「finding」）。
> 该数组**已废除**：前者改为 signal，后者改为 `coverage_breakdown` 条目。
> 完整映射见 `00-contracts.md §10`。

---

## 2. 抽取顺序（v1 阶段）

1. **Methods 优先**，不要从 Abstract 开始 —— 摘要是作者的宣传语，方法学才是事实来源。
2. Results 正文 → 补 `key_data` 观测，标 `explicit_main_text`。
3. 表格 → 补观测，标 `explicit_table`。
4. 图注**文字** → 补观测，标 `explicit_figure_caption`。
5. Declarations / Ethics / Funding / Data availability → 补声明类字段。
6. Abstract **最后**读，**仅用于交叉校验**。摘要与正文数值不一致时，
   **不得**用摘要覆盖正文 —— 两个观测都进同一观测组，由 Stage 3b 依
   `00-contracts.md §5.4` 判定兼容性。
7. **图像本体不在 v1 阶段读取** —— 那是 Stage 3（Figure Parser）的职责，
   结果在 Stage 3b 回流。文本没有、图里可能有的字段判 `unresolved`（§7）。

---

## 3. 字段的三个维度（本地约定）

维度定义见 `00-contracts.md §3`。M1 的操作要点：

### 3.1 判定顺序不可颠倒

```
1. 定 applicability   ← 由 §4 的设计路由 + §5 的适用性规则决定
2. 定 requiredness    ← 由 §5 的条件路由表决定
3. 定 status          ← 由实际检索结果决定
```

**先判适用性再检索。** `applicability = not_applicable` 的字段**不检索、不出 absence 证据**，
直接写 `status: not_applicable` + `na_reason`。

### 3.2 `not_applicable` 的唯一合法依据

只有 §5.3 条件路由表明确判定该字段对当前设计**概念上不成立**时，才可置 `not_applicable`：

```json
{
  "field_path": "design.randomization",
  "applicability": "not_applicable",
  "requiredness": "optional",
  "status": "not_applicable",
  "value": null,
  "na_reason": "article_design.primary_design.type = case_report；单例报告无分组，随机化概念不成立",
  "evidence_refs": []
}
```

**明令禁止**：因为某字段「不进覆盖率分母」就判 `not_applicable`。
覆盖率分母由 `requiredness` 控制（`00-contracts.md §8.2`），与适用性无关。
一个 `applicable + optional` 的字段照样要检索、照样可能是 `not_reported`，
只是不进主分母。

设计判定为 `applicability_uncertain` 时（§4.4），相关字段的 `applicability`
一律继承 `applicability_uncertain`，`status` 判 `ambiguous`，
**不得**判 `not_applicable` —— 设计未定就无法判断适用性。

### 3.3 absence 取证要求

`status: not_reported` 必须有 `absence` 证据，且检索范围必须覆盖 §5 各字段
`search_scope` 列的**全部**位置：

```json
{
  "id": "EV-019",
  "type": "absence",
  "scope": "document",
  "searched_locations": [
    {"section": "methods", "scope": "section"},
    {"section": "declarations", "scope": "section"},
    {"supplement_id": "S1", "scope": "supplement"}
  ],
  "search_terms": ["randomization", "random allocation", "randomly assigned",
                   "随机分组", "随机化"],
  "search_result": "no_match",
  "created_by": "stage_2"
}
```

**四条规则**

1. `absence` 证据**禁止**含 `quote` 或 `locator`。绝不为不存在的内容编造引文。
2. 检索范围不全时**不得**声称缺失，应降级为 `parse_failed` 并在
   `system_limitation.impact` 说明未覆盖的部分。
3. **补充材料不可得时，依赖补充材料的字段一律 `parse_failed`，不得判 `not_reported`**
   —— 我们没看过补充材料，就不能说它没写。同时产出
   `supplement_inaccessible` 的 `system_limitation`。
4. `search_result: partial_match_ambiguous` **不足以**支撑缺失结论，改判 `ambiguous`
   并产出 `ambiguous_extraction` signal。

---

## 4. 研究设计路由

### 4.1 层级枚举

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
  mixed_multi_family

other
  other_unclassified
```

**`family` 与 `type` 必须成对出现且匹配。** 只给 family 不给 type 为契约违规。

### 4.2 存储形式：article_design

**区分「文章有多种设计」与「抽取器不确定」**——旧契约把两者都塞进 `alternatives[]`，
导致 M3/M4/M6 无法知道该对哪个实验跑哪套规则。

```json
"article_design": {
  "primary_design": {
    "family": "experimental",
    "type": "preclinical_mixed",
    "status": "reported",
    "evidence_refs": ["EV-003"],
    "extraction_confidence": "high",
    "alternatives": []
  },
  "design_components": [
    {"experiment_id": "EXP-01", "family": "experimental", "type": "in_vitro",
     "evidence_refs": ["EV-005"], "extraction_confidence": "high"},
    {"experiment_id": "EXP-02", "family": "experimental", "type": "in_vivo_animal",
     "evidence_refs": ["EV-007"], "extraction_confidence": "high"}
  ]
}
```

| 用途 | 字段 | 语义 |
| --- | --- | --- |
| 论文**真的**含多种设计 | `design_components[]` | 每个 `experiment_id` 一条，各自路由规则 |
| 抽取器在几种解读间**不确定** | `primary_design.alternatives[]` | 每项 `{family, type, evidence_refs}`；同时出 `ambiguous_study_design` signal |

**二者不得混用。** `design_components[]` 非空表示事实层面的多设计，
与置信度无关；`alternatives[]` 非空表示我们没读准，必须出 signal。

`primary_design` 的选取规则（有序，命中即停）：

1. 承载 `primary_endpoint` 的那个实验的设计；
2. 稿件标题或摘要自述的设计（如 "a randomized controlled trial"）；
3. 占 Results 篇幅最大的实验的设计；
4. 以上都判不出时，先区分两种原因：已确认多个设计组件且无单一主设计
   → 按 §4.4 判 `mixed`；抽取器在多个候选解读间不确定 → 写
   `primary_design.alternatives[]` 并出 `ambiguous_study_design` signal。
5. 只有按 §4.1 的全部族与类型均无法归类时，才可判 `other`（§4.4）。

### 4.3 适用性路由优先级

```
1. 实验级类型规则   design_components[].type 对该 experiment_id 的专门规则
2. 文章级专门规则   primary_design.type 的专门规则（如 case_report）
3. 族级规则         primary_design.family 的规则
4. 默认规则         §5.1 通用字段清单
```

**命中即停，高优先级完全覆盖低优先级。**

例：`primary_design.type = case_report`（族为 `human_observational`）。
族级规则要求 `confounders` 与 `follow_up`，但 `case_report` 的专门规则把两者判为
`not_applicable` —— **专门规则胜出**，不得产生虚假缺失。

例：`primary_design.type = preclinical_mixed`，`EXP-01` 为 `in_vitro`、
`EXP-02` 为 `in_vivo_animal`。`ethics_statement` 对 `EXP-02` 适用且必填，
对 `EXP-01` 不适用 —— **按实验级分别判定**，`evaluation_matrix` 中拆成两个条目
（`applies_to` 各自列出），不取「或」。

### 4.4 mixed 与 other 的存储语义

**`family: "mixed"`** 仅在**同时满足**下列条件时合法：

1. `design_components[]` 含 ≥2 个 **family 不同**的条目；
2. 没有任何单一组件承载全部 `primary_endpoint`（即 §4.2 的规则 1–3 都判不出主设计）。

此时 `primary_design = {"family": "mixed", "type": "mixed_multi_family"}`，
适用性路由**取各组件族级规则的并集**：
某字段只要对**任一**组件 `applicable`，文章级即 `applicable`；
`requiredness` 取各组件中**最高**者（`required` > `recommended` > `optional`）。

**`family: "other"`** 表示设计**无法归入**上述任何族，必须同时：

1. 填 `other_description`（自由文本，写明稿件自述的设计）；
2. 全部 design-specific 字段（§5.2）的 `applicability` 置 `applicability_uncertain`；
3. 产出 `ambiguous_study_design` signal，`routed_to: ["M2", "M3", "M4", "M6"]`。

**`other` 不是兜底选项。** 能归入某族就必须归入；
`other` 的使用率高于语料的 5% 即说明 §4.1 枚举需要扩充（见 §13 TODO）。

---

## 5. 字段清单与条件路由

### 5.1 通用字段清单

全部使用 `00-contracts.md §3.3` 的 `extracted_field` 结构。
`search_scope` 定义 `absence` 取证时的**最小**检索范围。

#### 5.1.1 objective · 研究目标

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `research_question` | 论文要回答的问题，一句话 | abstract, introduction, discussion |
| `hypothesis` | 明确陈述的假设 | introduction, methods |
| `primary_endpoint` | 主要终点 / 主要观测指标 | abstract, methods, results |
| `secondary_endpoints` | 次要终点（数组） | methods, results |

> `article_design` 不在本表 —— 它有专门的存储结构（§4.2），不是普通 `extracted_field`。
> 它是**主路由字段**：M3 用它决定是否启动动物实验必要性检查，M4 用它选统计规范表，
> M6 用它决定伦理要求，M1 自己用它决定哪些字段适用。抽错会导致四处跑错规则集。

#### 5.1.2 population · 受试对象

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `subjects` | 物种/品系/细胞系/人群，含来源 | methods |
| `inclusion_criteria` | 纳入标准 | methods |
| `exclusion_criteria` | 排除标准 | methods |
| `participant_spectrum` | 受试者谱（疾病严重度分布、招募场景） | methods |

#### 5.1.3 design · 设计与干预

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `arms` | 试验臂 / 实验组（数组，见 §5.4） | methods, figure captions |
| `interventions` | 干预措施（数组） | methods |
| `controls` | 对照设置（数组） | methods |
| `exposure` | 暴露因素（观察性研究） | methods |
| `confounders` | 混杂因素与校正方式 | methods, statistics |
| `follow_up` | 随访时长与失访 | methods, results |
| `randomization` | **随机化方法**描述（序列如何生成） | methods |
| `allocation_concealment` | **分配隐藏**（序列如何对招募者屏蔽） | methods |
| `blinding` | 盲法：`none`/`single`/`double`/`triple` | methods |
| `registration` | 注册号与注册时间 | abstract, methods, declarations |

> **旧契约的 `allocation` 字段已废除。** 它把「随机化」与「分配隐藏」混为一谈，
> 而二者是 CONSORT 中相互独立的两项（随机了但未隐藏分配是常见缺陷）。
> 一律拆为 `randomization` + `allocation_concealment` 两个字段。

#### 5.1.4 measurement · 测量与分析

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `assays` | 每项 `{name, purpose, reference_citation}` | methods |
| `index_test` | 待评价试验（诊断研究） | methods |
| `reference_standard` | 参照标准 / 金标准（诊断研究） | methods |
| `target_condition` | **目标疾病 / 待诊断状态**（诊断研究） | title, abstract, methods |
| `statistical_methods` | 每项 `{test, applied_to, software, correction}` | methods, figure captions |
| `sample_size_justification` | 效能分析或样本量依据 | methods |
| `missing_data_handling` | 缺失数据处理 | methods, statistics |

> **`target_condition` 是新增字段，用于修正旧契约的误用。** 旧表让诊断准确性研究
> 把「目标疾病」塞进 `primary_endpoint`，二者语义完全不同：
> `target_condition` 是**被诊断的对象**（如「肺结核」），
> `primary_endpoint` 是**准确性指标**（如「敏感度与特异度」）。两者都必填，不得互相顶替。

#### 5.1.5 conclusion · 结论

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `claims` | 每条 `{claim_id, statement, scope, supported_by[]}` | abstract, discussion, conclusion |
| `limitations` | 作者自述的局限 | discussion |
| `generalization_scope` | 作者主张的适用范围 | discussion, conclusion |

`claims[].supported_by[]` 存 `key_data.id` 或 `evidence_ref`；
解析不到任何一项的，见 §9 产出 `claim_without_resolved_evidence_link`。

#### 5.1.6 declarations · 声明

| 字段 | search_scope |
| --- | --- |
| `ethics_statement`（含批件号、批准机构） | declarations, methods, ethics |
| `informed_consent` | declarations, methods |
| `funding` | declarations, funding |
| `conflict_of_interest` | declarations |
| `data_availability` | declarations, data_availability |

### 5.2 design_specific 字段定义

下列字段**只对特定设计族适用**，存储在 `structured_result.design_specific` 块下，
结构同样是 `extracted_field`。**每个在 §5.3 路由表中出现的字段都必须在此处或 §5.1 有定义。**

#### 5.2.1 evidence_synthesis 专属

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `databases_searched` | 检索的数据库清单（PubMed / Embase / CENTRAL / CNKI…） | methods |
| `search_date` | 检索执行日期或截止日期 | methods, abstract |
| `search_strategy` | 完整检索式（常在补充材料） | methods, supplement |
| `risk_of_bias_method` | 偏倚风险评估工具（RoB 2 / ROBINS-I / NOS / QUADAS-2） | methods |
| `synthesis_method` | 合成方法（固定/随机效应模型、异质性度量、定性合成） | methods |
| `protocol_registration` | 方案注册号（PROSPERO 等） | methods, declarations |

#### 5.2.2 computational 专属

| 字段 | 说明 | search_scope |
| --- | --- | --- |
| `dataset` | 数据集来源、规模、版本、可及性 | methods, data_availability |
| `split_strategy` | 训练/验证/测试划分方式与比例；是否按受试者划分 | methods |
| `baselines` | 对比基线方法清单 | methods, results |
| `metrics` | 评价指标清单（AUC / F1 / MAE…） | methods, results |
| `validation_protocol` | 验证方案（交叉验证折数、外部验证队列、时间外验证） | methods |

> `split_strategy` 与 `validation_protocol` 是 M2 数据泄露场景库的主输入
> （见 `02-macro-logic.md`）。M1 只抽取，**不判定**是否存在泄露。

### 5.3 条件路由表

**列义**：`applicability rule` 给出适用性的判定条件；`requiredness` 给出必填等级；
`applicable study types` 给出适用的设计；`review consumer` 给出主要下游模块。
未在本表出现的通用字段，默认 `applicable + optional`（**不是** `not_applicable`）。

#### 5.3.1 全设计通用（默认规则，优先级 4）

| 字段 | applicability rule | requiredness | 适用设计 | search scope | review consumer |
| --- | --- | --- | --- | --- | --- |
| `research_question` | 恒适用 | `required` | 全部 | abstract, introduction | M2, M7 |
| `hypothesis` | 恒适用 | `optional` | 全部 | introduction, methods | M2, M7 |
| `primary_endpoint` | 恒适用 | `required` | 全部 | abstract, methods, results | M2, M4, M7 |
| `secondary_endpoints` | 恒适用 | `optional` | 全部 | methods, results | M4, M7 |
| `subjects` | 恒适用 | `required` | 全部 | methods | M3, M6 |
| `statistical_methods` | 有任何统计比较时适用 | `required` | 全部 | methods, figure captions | M4 |
| `claims` | 恒适用 | `required` | 全部 | abstract, discussion | M7 |
| `limitations` | 恒适用 | `recommended` | 全部 | discussion | M7 |
| `generalization_scope` | 恒适用 | `optional` | 全部 | discussion, conclusion | M7 |
| `funding` | 恒适用 | `recommended` | 全部 | declarations, funding | M2 |
| `conflict_of_interest` | 恒适用 | `recommended` | 全部 | declarations | M2 |
| `data_availability` | 恒适用 | `recommended` | 全部 | declarations | M2 |
| `missing_data_handling` | 存在失访或缺失值时适用 | `recommended` | 全部 | methods, statistics | M4 |

#### 5.3.2 human_interventional 族（优先级 3）

| 字段 | applicability rule | requiredness | 适用设计 | search scope | review consumer |
| --- | --- | --- | --- | --- | --- |
| `arms` | 恒适用 | `required` | 全族 | methods | M3, M4 |
| `interventions` | 恒适用 | `required` | 全族 | methods | M3 |
| `controls` | `single_arm_trial` 不适用 | `required` | RCT, nonrandomized | methods | M3, M4 |
| `randomization` | 仅 RCT 适用 | `required` | RCT | methods | M3, M4 |
| `allocation_concealment` | 仅 RCT 适用 | `required` | RCT | methods | M4 |
| `blinding` | 恒适用（可为 `none`） | `required` | 全族 | methods | M3, M4 |
| `registration` | 恒适用 | `required` | 全族 | abstract, methods, declarations | M6, M4 |
| `sample_size_justification` | 恒适用 | `required` | 全族 | methods | M4 |
| `inclusion_criteria` / `exclusion_criteria` | 恒适用 | `required` | 全族 | methods | M3, M6 |
| `follow_up` | 恒适用 | `required` | 全族 | methods, results | M4 |
| `ethics_statement` | 恒适用 | `required` | 全族 | declarations, methods | M6 |
| `informed_consent` | 恒适用 | `required` | 全族 | declarations, methods | M6 |
| `exposure` | 干预性研究不适用（干预即 `interventions`） | `optional` | —— | —— | —— |

#### 5.3.3 human_observational 族（优先级 3）

| 字段 | applicability rule | requiredness | 适用设计 | search scope | review consumer |
| --- | --- | --- | --- | --- | --- |
| `exposure` | 恒适用 | `required` | cohort, case_control, cross_sectional | methods | M3, M4 |
| `confounders` | 恒适用 | `required` | cohort, case_control, cross_sectional | methods, statistics | M4 |
| `follow_up` | **仅纵向设计适用**；`cross_sectional` 与 `case_control` **不适用** | `required` | cohort | methods, results | M4 |
| `inclusion_criteria` / `exclusion_criteria` | 恒适用 | `required` | 全族 | methods | M3, M6 |
| `ethics_statement` | 恒适用 | `required` | 全族 | declarations, methods | M6 |
| `informed_consent` | 回顾性去标识数据可豁免 → `applicable + recommended` | `recommended` | 全族 | declarations, methods | M6 |
| `sample_size_justification` | 恒适用 | `recommended` | 全族 | methods | M4 |
| `randomization` / `allocation_concealment` / `arms` | 观察性研究不适用 | `optional` | —— | —— | —— |

> **`cross_sectional` 不得要求 `follow_up`。** 横断面研究在单一时点测量，
> 随访概念不成立，判 `not_applicable` + `na_reason: "横断面设计无随访期"`。
> 旧契约对整个 `human_observational` 族统一要求 `follow_up` 是错的。
> `case_control` 同理 —— 它按结局状态抽样，研究可以回顾也可以嵌套于前瞻队列，
> 但指标时点后的随访不是该设计的必备概念。

#### 5.3.4 diagnostic_accuracy 专门规则（优先级 2）

| 字段 | applicability rule | requiredness | search scope | review consumer |
| --- | --- | --- | --- | --- |
| `target_condition` | 恒适用 | `required` | title, abstract, methods | M3, M4 |
| `index_test` | 恒适用 | `required` | methods | M3 |
| `reference_standard` | 恒适用 | `required` | methods | M3, M4 |
| `participant_spectrum` | 恒适用 | `required` | methods | M4 |
| `primary_endpoint` | 恒适用；**指准确性指标**，非目标疾病 | `required` | abstract, methods, results | M4 |
| `blinding` | 指标试验与参照标准的判读是否互盲 | `required` | methods | M3, M4 |
| `exposure` / `confounders` | 诊断准确性研究不适用 | `optional` | —— | —— |
| `follow_up` | 仅延迟型参照标准适用 | `optional` | methods | M4 |

#### 5.3.5 case_report / case_series 专门规则（优先级 2，覆盖族级）

| 字段 | applicability | requiredness | na_reason 模板 |
| --- | --- | --- | --- |
| `subjects` | `applicable` | `required` | —— |
| `inclusion_criteria` / `exclusion_criteria` | `case_series`: `applicable`；`case_report`: `not_applicable` | `case_series`: `required`；`case_report`: `optional` | 单一病例无入组与排除标准；病例系列必须抽取病例选择规则 |
| `interventions` | `applicable` | `required` | —— |
| `informed_consent` | `applicable` | **`required`** | —— |
| `ethics_statement` | `applicable` | `recommended` | —— |
| `limitations` | `applicable` | `recommended` | —— |
| `arms` | **`not_applicable`** | `optional` | 单例/小系列报告无分组结构 |
| `randomization` | **`not_applicable`** | `optional` | 无分组，随机化概念不成立 |
| `allocation_concealment` | **`not_applicable`** | `optional` | 无随机分配 |
| `controls` | **`not_applicable`** | `optional` | 描述性报告无对照组 |
| `sample_size_justification` | **`not_applicable`** | `optional` | 描述性病例报告/系列不做预设推断性样本量估计 |
| `confounders` | **`not_applicable`** | `optional` | 无统计校正 |
| `follow_up` | `applicable` | `recommended` | —— |
| `statistical_methods` | 有描述性统计以外的比较时才适用 | `optional` | 纯描述性报告无统计检验 |

#### 5.3.6 experimental 族（优先级 3，含实验级细分）

| 字段 | applicability rule | requiredness | 适用设计 | review consumer |
| --- | --- | --- | --- | --- |
| `subjects` | 恒适用（细胞系 / 物种品系） | `required` | 全族 | M3, M6 |
| `interventions` | 恒适用 | `required` | 全族 | M3 |
| `controls` | 恒适用 | `required` | 全族 | M3, M4 |
| `assays` | 恒适用 | `required` | 全族 | M3 |
| `arms` | 恒适用（含重复数与重复类型） | `required` | 全族 | M4 |
| `ethics_statement` | `in_vivo_animal` 恒适用；`in_vitro` / `ex_vivo` / `organoid` 仅在使用人体或研究动物新取一级材料时适用；来源不明时为 `applicability_uncertain` | `required` | in_vivo_animal；使用受监管一级材料的 in_vitro, ex_vivo, organoid | M6 |
| `informed_consent` | 使用人体一级材料时适用，值可为已同意或经批准豁免；稳定商业细胞系与纯动物材料不适用；来源不明时为 `applicability_uncertain` | `required` | 使用人体一级材料的 in_vitro, ex_vivo, organoid | M6 |
| `randomization` | **仅 `in_vivo_animal` 适用** | `required` | in_vivo_animal | M3, M4 |
| `blinding` | **仅 `in_vivo_animal` 适用** | `recommended` | in_vivo_animal | M3, M4 |
| `sample_size_justification` | **仅 `in_vivo_animal` 适用** | `required` | in_vivo_animal | M4, M6 |
| `inclusion_criteria` / `exclusion_criteria` | `in_vivo_animal` 恒适用，用于抽取预设纳入与剔除标准 | `recommended` | in_vivo_animal | M3 |
| `registration` | 实验研究不适用 | `optional` | —— | —— |

> `preclinical_mixed` 不在本表单列 —— 它必须展开为 `design_components[]`，
> 按实验级类型（`in_vitro` / `in_vivo_animal`）分别路由。
> 例：`ethics_statement` 对 `EXP-02`(in_vivo_animal) 是 `applicable + required`，
> 对 `EXP-01`(in_vitro) 是 `not_applicable`。

> 稳定商业细胞系不因“人源”三个字自动触发受试者同意。
> M1 必须先从 `subjects` 抽取材料来源（稳定细胞系 / 人体一级材料 /
> 研究动物材料 / 不明），再路由上述两字段；来源不明不得判 `not_applicable`。

#### 5.3.7 evidence_synthesis 族（优先级 3）

| 字段 | applicability rule | requiredness | 适用设计 | review consumer |
| --- | --- | --- | --- | --- |
| `databases_searched` | 恒适用 | `required` | 全族 | M2, M3 |
| `search_date` | 恒适用 | `required` | 全族 | M2 |
| `search_strategy` | 恒适用 | `recommended` | 全族 | M3 |
| `inclusion_criteria` / `exclusion_criteria` | 恒适用 | `required` | 全族 | M2, M3 |
| `risk_of_bias_method` | systematic_review / meta_analysis 恒适用；scoping_review 可执行但非强制 | systematic_review, meta_analysis: `required`；scoping_review: `optional` | 全族 | M4 |
| `synthesis_method` | 恒适用 | `required` | 全族 | M4 |
| `protocol_registration` | 恒适用 | `recommended` | 全族 | M2, M6 |
| `subjects` | 指纳入研究的人群 | `required` | 全族 | M3 |
| `ethics_statement` | 二次文献研究不适用 | `optional` | —— | —— |
| `informed_consent` | 二次文献研究不适用 | `optional` | —— | —— |
| `arms` / `randomization` / `follow_up` | 综述层面不适用 | `optional` | —— | —— |

> `scoping_review` 不强制做偏倚风险评估，但该概念仍然成立。因此必须判
> `applicable + optional`；未报告时是 `not_reported`，不是 `not_applicable`，也不进主覆盖率分母。

#### 5.3.8 computational 族（优先级 3）

| 字段 | applicability rule | requiredness | 适用设计 | review consumer |
| --- | --- | --- | --- | --- |
| `dataset` | 恒适用 | `required` | 全族 | M2, M3 |
| `split_strategy` | **仅 `prediction_model` / `benchmark_study` 适用** | `required` | prediction_model, benchmark_study | **M2**（泄露）, M4 |
| `baselines` | `method_development` / `benchmark_study` 适用 | `required` | method_development, benchmark_study | M2, M4 |
| `metrics` | 恒适用 | `required` | 全族 | M4 |
| `validation_protocol` | **仅 `prediction_model` / `benchmark_study` 适用** | `required` | prediction_model, benchmark_study | **M2**（泄露）, M4 |
| `statistical_methods` | 有统计比较时适用 | `recommended` | 全族 | M4 |
| `data_availability` | 恒适用 | **`required`**（计算研究的复现前提） | 全族 | M2 |
| `ethics_statement` | 使用人类受试者数据时适用 | `required` | 用到人体数据者 | M6 |
| `arms` / `randomization` / `follow_up` | 计算研究不适用 | `optional` | —— | —— |

### 5.4 arms[] · 实验级结构

`arms[]` 保留**实验级**上下文，不压缩为全局单值：

```json
{
  "experiment_id": "EXP-01",
  "arm_name": "vehicle",
  "n": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": {"type": "point", "number": 6},
    "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  },
  "replicate_type": "biological",
  "intervention": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": "0.9% saline", "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  },
  "dose": {
    "applicability": "not_applicable", "requiredness": "optional",
    "status": "not_applicable", "value": null,
    "na_reason": "溶剂对照组无给药剂量", "evidence_refs": []
  },
  "route": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": "i.p.", "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  },
  "duration": {
    "applicability": "applicable", "requiredness": "required", "status": "reported",
    "value": "14 d", "evidence_refs": ["EV-021"], "extraction_confidence": "high"
  }
}
```

`replicate_type` 枚举：`biological` / `technical` / `unspecified`。
稿件未写明时用 `unspecified` 并产出 `partial_extraction` signal（M4 消费）——
**不得**默认填 `biological`。

---

## 6. key_data 观测组

### 6.1 M1 在 v1 阶段的职责

结构定义见 `00-contracts.md §5.2`。**M1 只负责建组与投放观测，不做合并判定**：

1. 从文本来源抽出的每个数值建一个 `observation`，带完整 `provenance`（含 `derivation`）。
2. 按 §6.2 的 `grouping_key` 把观测投入对应的 `key_data` 组；组不存在则新建。
3. **v1 阶段的组 `status`**：
   - 组内只有一个观测 → `reported`，`canonical_observation` 指向它。
   - 组内有多个观测 → **一律 `ambiguous`，`canonical_observation: null`**。
     兼容性判定是 Stage 3b 的职责，M1 不做。
   - 组预期从图中补值 → `pending_visual_resolution`（§7）。
4. `reporting_completeness` 在 v1 阶段一律 `not_assessed`，`missing_elements: []`
   —— 等 Stage 3b 定下 canonical 之后才能按 §6.3 判定。

**M1 绝不删除或覆盖任何观测。**

### 6.2 指标身份 + grouping_key 五键

```
experiment_id | group | comparison | timepoint | endpoint
```

先要求 `metric_family` 与规范化后 `metric_name` 相同，再要求五键**全部相等**
才是同一组（`null` 与 `null` 相等；一方 `null` 一方有值视为不等）。
`metric_name` 存项目指标词表的规范名，原文别名保留在证据 `quote` 中。

**填键规则**

| 键 | 填法 | 无法确定时 |
| --- | --- | --- |
| `experiment_id` | 稿件的实验编号，或 M1 分配的 `EXP-nn` | `null` + `partial_extraction` signal |
| `group` | 组名，取 `arms[].arm_name` | `null` |
| `comparison` | 比较关系，如 `"Compound A vs vehicle"` | `null`（单组描述性数值本就无比较） |
| `timepoint` | 测量时点，如 `"72h"` / `"day 28"` | `null`（单时点研究） |
| `endpoint` | 该数值对应的终点名 | `null` + `partial_extraction` signal |

**常见错误**：把「Fig 2C 的 IC50」与「Table 1 的 IC50」在 `experiment_id` 不同时
强行归为一组 —— 那是两个实验的两个值，不是冲突。**键不匹配就是两个组。**

### 6.3 指标族完整性规则

**取消旧版「任何数值都要 unit + n + 误差」的三要素规则** —— 它对计数、比例、
无量纲指标都不成立。按**指标族**判定 `reporting_completeness`（Stage 3b 定下 canonical 后执行）：

| metric_family | 完整报告所需要素 | 备注 |
| --- | --- | --- |
| `continuous_summary` | value + unit（有量纲时）+ n + dispersion(SD/SEM/IQR/range) | 无量纲指标不要求 unit |
| `effect_estimate` | estimate + CI + reference_group + model | 均差、OR、RR |
| `count` | count + population_or_denominator_context | 不要求 unit、不要求误差 |
| `proportion` | (numerator + denominator) 或 (proportion + n) | 不要求 unit |
| `p_value` | p_value + test + comparison | 不要求 n（n 挂在被比较的数据点上） |
| `correlation` | coefficient + n + method(Pearson/Spearman/…) | 不要求 unit |
| `time_to_event` | HR + CI + reference_group + model | 中位生存另计为 `continuous_summary` |
| `dose_response` | IC50/EC50 + unit + fitting_method + CI（原文报告时） | CI 未报告不降 extraction_confidence |
| `classification_metric` | metric_name + value + evaluation_set + threshold_or_averaging（相关时） | AUC/F1/准确率，无量纲 |
| `diagnostic_accuracy` | sensitivity + specificity + CI + reference_standard + 2×2 计数（可得时） | 单报一个指标即 incomplete |

**判定规则**

- 要素齐全 → `complete`。
- 缺要素 → `incomplete`，缺失项逐一列入 `missing_elements[]`（如 `["dispersion", "n"]`）。
- 该族不要求的要素缺失 → **不计入** `missing_elements`，不影响完整性。
- `canonical_observation` 为 `null` → 一律 `not_assessed`，`missing_elements: []`。

`reporting_completeness: "incomplete"` 是 **M4 的 finding 线索**，M1 只记录，不立 finding。

### 6.4 抽取置信度与报告完整性正交

| 场景 | extraction_confidence | reporting_completeness |
| --- | --- | --- |
| 图注明写 `IC50 = 12.4 μM (95% CI …)` + 拟合方法 | `high` | `complete` |
| 图注明写 `IC50 = 12.4 μM`，无 CI 无拟合方法 | `high`（确信读对了） | `incomplete`（缺 fitting_method） |
| 只能从对数坐标轴读出约 12–15 μM | `low`（估读） | 视原文报告要素另判 |
| 相关文本存在但表述矛盾 | 组 `status: ambiguous`（v1） | `not_assessed` |

---

## 7. pending 视觉解析生命周期

契约见 `00-contracts.md §4`。M1 的操作规则：

### 7.1 何时判 `unresolved`

**同时满足**才可判：

1. 该字段 `applicability = applicable`；
2. 文本来源（正文、表、图注文字）**完整检索后**未找到；
3. 稿件中**存在**一个可指认的视觉来源可能承载该值
   （正文写了 "as shown in Fig 2C"，或该图的类型按 `05-figures-and-charts.md`
   通常承载此类数值）。

```json
{
  "field_path": "key_results.ic50_compound_a",
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

`evidence_refs` 指向**交叉引用本身**（正文「见 Fig 2C」那句话）的 `present` 证据，
用于证明我们有理由期待该图承载此值。

### 7.2 三条禁令

1. **不得**判 `parse_failed` —— Stage 3 尚未尝试，谈不上失败。
2. **不得**填 `system_limitation_ref` —— 它不是系统限制。
3. **不得**出 `absence` 证据 —— 我们还没找完，不能声称缺失。

### 7.3 条件 3 不满足时怎么判

文本没有、且**没有任何可指认的视觉来源**（没有交叉引用、图型也不承载此类数值）
→ 正常判 `not_reported` + `absence` 证据。**不要**把所有找不到的字段都挂成 `unresolved`
—— 那会让 Stage 3b 收到一堆无法解析的挂载点，最终全部退化为 `parse_failed`，
虚假地压低覆盖率。

### 7.4 Stage 3b 的收敛义务

Stage 3b **必须**把每个 `unresolved` 解析为 `reported` / `not_reported` /
`ambiguous` / `conflicting` / `parse_failed` 之一。
**`structured_result_v2` 中不得残留 `unresolved`**（`00-contracts.md §11` lint 项）。

| Stage 3 结果 | v2 中的 status | 附带产物 |
| --- | --- | --- |
| 图中读出且与文本无冲突（或文本本无值） | `reported` | —— |
| 图中读出且与既有观测不兼容 | `conflicting` | `source_value_conflict` signal |
| 图可读，但确认图中并不承载该值 | `not_reported` | 补 `absence` 证据（检索范围含该图） |
| 图不可读 / 面板缺失 | `parse_failed` | `system_limitation`（`figure_unreadable`）+ `system_limitation_ref` |
| 模式以 v1 为终态，Stage 3 / 3b 均未执行 | 保留 `unresolved`（仅 v1 合法） | 计入 `coverage_breakdown.unresolved_required_fields[]` |

要求 v2 的模式中，若 scope 内存在 `unresolved`，则 scoped Stage 3 不可跳过。
Stage 3b 不得在未尝试 `expected_sources[]` 时将其收敛为 `not_reported` 或 `parse_failed`。

---

## 8. structured_result_v1 与 v2

| 版本 | 产出者 | 数据来源 | 可含 `unresolved` | 消费者 |
| --- | --- | --- | --- | --- |
| `structured_result_v1` | **M1（Stage 2）** | 仅文本：正文、表格、图注**文字** | ✅ | Stage 3（上下文）、Stage 3b；`structured_extraction` 无视觉需求时可直接输出 |
| `structured_result_v2` | **Stage 3b** | v1 + 图表解析结果，已消解冲突 | ❌ | **M2–M7 全部** |

**M1 不产出 v2。** M1 的职责在 v1 结束；合并是 Stage 3b 的职责。
**M2–M7 一律消费 v2** —— 直接读 v1 会漏掉全部图像来源数值，且可能撞上 `unresolved`。

v1 顶层必须带 `"version": "v1"` 与 `"stage_3b_executed": false`，
由输出装配步骤在 v2 时改写为 `"version": "v2"` / `true`。

---

## 9. extraction_signals

M1 产出的数组名为 **`m1_extraction_signals[]`**（阶段本地，Stage 5 聚合）。
**signal 不带 `severity`，不是结论。** 结构与当前全部十五种 type 见
`00-contracts.md §6.2`；本节只列 M1 核心抽取流程直接涉及的子集。

### 9.1 M1 可产出的五种 signal

| type | M1 触发条件 | 路由到 |
| --- | --- | --- |
| `source_value_conflict` | v1 阶段**不产出** —— 兼容性判定是 Stage 3b 的职责 | —— |
| `claim_without_resolved_evidence_link` | `claims[].supported_by` 解析不到任何 `key_data.id` 或 `evidence_ref` | M7 |
| `ambiguous_study_design` | 设计线索冲突、`primary_design.alternatives[]` 非空、或 family 判为 `other` | M2, M3, M4, M6 |
| `unresolved_cross_reference` | 正文引用的图/表/补充材料解析不到实体（引用了 Fig 6 但只有 5 张图） | M2, M5 |
| `partial_extraction` | 字段部分抽出：有 n 无分组归属、有剂量无单位、`replicate_type` 未写明 | M4, M5 |
| `ambiguous_extraction` | 字段 `status: ambiguous`，存在相关文本但读不出唯一解 | M2, M4 |

> **M1 不产出 `source_value_conflict`。** 摘要与正文不一致时，M1 把两个观测都投进
> 同一 `key_data` 组、组判 `ambiguous`，由 **Stage 3b** 按
> `00-contracts.md §5.4` 判定兼容性后决定是否升级为 `conflicting` 并出 signal。
> 这修正了旧契约「M1 直接出 source_value_conflict」与「兼容性判定归 Stage 3b」的矛盾。

### 9.2 示例

```json
{
  "id": "SIG-007",
  "type": "ambiguous_study_design",
  "target": "article_design.primary_design",
  "detail": "标题自述 'a prospective cohort study'，但 Methods §2.1 描述了按信封法分配干预；两种解读的证据强度相当。",
  "observation_refs": [],
  "evidence_refs": ["EV-003", "EV-009"],
  "routed_to": ["M2", "M3", "M4", "M6"],
  "produced_by": "stage_2"
}
```

**规则**：下游模块据 signal 立 finding 时，必须在该 finding 的 `evidence_refs[]` 中
**独立**给出稿件证据，不得仅引用 signal id（`00-contracts.md §6.1` 规则 5）。

---

## 10. 证据登记与系统限制

### 10.1 evidence_registry 使用

M1 **向** Stage 1 建立的 `evidence_registry` **追加**条目，`created_by: "stage_2"`。

**四条操作规则**

1. **先登记，后引用。** 任何 `evidence_refs` 中的 id 必须已存在于登记表。
2. **复用优先。** 同一 locator + 同一 quote 的证据复用既有条目，不新建
   —— 这是 Stage 5 跨模块聚簇能对齐主锚点的前提。
3. **不改既有条目。** id 一经分配，内容不可变；需要修正就新建一条。
4. **absence 证据也要登记。** 它是 `not_reported` 的唯一合法支撑，
   不登记则该字段状态无效。

### 10.2 stage2_system_limitations[]

抽取因技术原因失败时产出，结构与十二值枚举见 `00-contracts.md §6.3`。M1 常见触发：

| category | 场景 |
| --- | --- |
| `parse_failed` | 段落无法提取、编码错乱 |
| `table_unparseable` | 表格结构无法还原 |
| `supplement_inaccessible` | 引用了补充材料但无法获取 |
| `ocr_low_quality` | 扫描件 OCR 质量不足 |
| `input_truncated` | 输入被截断，部分章节缺失 |
| `section_missing_from_input` | 输入本身不含该章节（如只给了 Methods） |

**`supplement_inaccessible` 时，依赖补充材料的字段一律 `parse_failed`，
不得判 `not_reported`** —— 我们没看过，就不能说它没写。
且**必须**在该字段填 `system_limitation_ref` 指向这条限制。

---

## 11. evaluation_matrix

### 11.1 用途与限制

`evaluation_matrix` 是 M2–M7 的**路由与索引**工具，让下游无需重读全文即可
判断该跑哪些规则、去哪里找证据。

1. **可以**用它决定跑哪些规则集、定位相关证据。
2. **不得**仅凭它直接立 finding。M2–M7 必须回查 `evidence_refs` 指向的登记条目，
   在 finding 中独立给出 `evidence_refs[]`。
3. 实验级信息**不得**压缩为单一全局数字。

### 11.2 条目结构

每个条目是**状态感知对象**，不是裸布尔，且带完整三维度：

```json
"randomization": {
  "applicability": "applicable",
  "requiredness": "required",
  "status": "not_reported",
  "applies_to": ["EXP-01", "EXP-02"],
  "evidence_refs": ["EV-018"],
  "extraction_confidence": "high"
}
```

`status` 取 `00-contracts.md §3.1` 的七值枚举。`applies_to` 列出该判断覆盖的实验；
**不同实验状态不同时拆成多个条目，不取「或」**：

> **matrix 条目是纯索引，不是字段的副本。** 它**不得**携带 `value`、`na_reason`、
> `system_limitation_ref` —— 这三者是字段本身的属性，复制进 matrix 必然与字段漂移。
> 下游要看 `na_reason` 就顺着 `evidence_refs` 与字段路径回查原字段。
> 条目**必须**带 `applies_to`（这是它与 `extracted_field` 的形状分界）。

```json
"ethics_statement": [
  {"applicability": "applicable", "requiredness": "required", "status": "reported",
   "applies_to": ["EXP-02"], "evidence_refs": ["EV-031"], "extraction_confidence": "high"},
  {"applicability": "not_applicable", "requiredness": "optional", "status": "not_applicable",
   "applies_to": ["EXP-01"], "evidence_refs": [], "extraction_confidence": "high"}
]
```

### 11.3 条目清单

| 键 | 消费者 | 备注 |
| --- | --- | --- |
| `has_animal_experiment` | M3, M6 | |
| `has_human_subjects` | M6 | |
| `ethics_statement` | M6 | 可为数组（按实验拆分） |
| `informed_consent` | M6 | |
| `registration` | M6, M4 | |
| `randomization` | M3, M4 | |
| `allocation_concealment` | M4 | |
| `blinding` | M3, M4 | |
| `sample_size_justification` | M4 | |
| `multiple_comparison_correction` | M4 | |
| `has_ml_model` | M2, M4 | 触发 M2 数据泄露场景库 |
| `has_split_strategy` | M2 | 与 `has_ml_model` 联用；无划分描述是泄露高风险信号 |
| `has_external_validation` | M2, M4 | 取自 `validation_protocol` |
| `data_availability` | M2 | |
| `conflict_of_interest` | M2 | |
| `all_figures_cited_in_text` | M2, M5 | |
| `figure_count` / `table_count` | M5 | 计数字段，直接取整数 |
| `group_sizes` | M4 | **数组**，见 §11.4 |

### 11.4 group_sizes：保留实验级上下文

**取消旧版 `min_group_n` 单一整数** —— 它把所有实验压成一个数，丢掉了
「哪个实验的哪一组样本量小」这个 M4 真正需要的信息。

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

M4 自行按实验分组计算最小值与分布，**M1 不做聚合判断**。

---

## 12. 运维日志与覆盖率数据

### 12.1 gaps[] · 操作日志（非记录）

`gaps[]` 是**运维日志**，记录未解决抽取问题的排查线索，供调参与排障使用。
**它不是字段状态的表示方式**（状态由 §3 的 `status` 承载），
**不是 finding**，不进任何评分。

```json
{
  "field_path": "measurement.sample_size_justification",
  "status_assigned": "not_reported",
  "attempts": ["methods §2.6 全文检索", "supplement S1 检索", "figure captions 检索"],
  "search_terms": ["power", "sample size", "样本量", "效能"],
  "resolution": "confirmed_absent",
  "note": "M4 将依赖 EV-019 的 absence 证据评估"
}
```

`resolution` 枚举：`confirmed_absent` / `unresolved` / `resolved_in_stage3b` /
`blocked_by_system_limitation`。

### 12.2 coverage_inputs · 覆盖率原始数据

M1 输出计算 `extraction_coverage` 所需的**原始计数**，
由 Stage 5 装配为 `coverage_breakdown`（`00-contracts.md §7.2`）。

```json
"coverage_inputs": {
  "fields_in_scope": ["objective.research_question", "measurement.sample_size_justification"],
  "resolved": ["objective.research_question"],
  "unresolved": [
    {"field_path": "measurement.sample_size_justification", "status": "parse_failed",
     "reason_ref": "SYS-007"}
  ],
  "required_applicable_total": 2,
  "recommended_applicable_total": 5
}
```

**规则**

1. `fields_in_scope` 必须是 `execution_scope.fields` 的子集。
2. **只有 `applicability = applicable ∧ requiredness = required` 的字段进
   `required_applicable_total`**（主分母）。
3. `status ∈ {reported, not_reported}` 计为已解析；
   `{ambiguous, conflicting, parse_failed, unresolved, not_applicable}` 中，
   前四者计为未解析，`not_applicable` **不入分子也不入分母**。
4. `resolved` + `unresolved` 的长度之和必须等于 `required_applicable_total`。

---

## 13. TODO（一期）

- [ ] 补齐 §4.1 层级枚举的边界样例：`ex_vivo` 与 `organoid` 的区分、
      `preclinical_mixed` 的适用条件、`prediction_model` 与 `benchmark_study` 的分界
- [ ] 补齐单位归一化表（μM/µM/uM、mg/kg vs mg·kg⁻¹、log vs ln），
      供 `00-contracts.md §5.4` 第 1 步使用
- [ ] 补齐各字段 `search_scope` 的检索词表（中英双语），供 absence 取证使用
- [ ] 与 M5 确认 §7 `expected_sources` 的字段级对接清单：
      哪些 `metric_family` 应期待哪些图型承载
- [ ] 在 `datasets/` 的 10 篇语料上跑一遍，按 `primary_design.type` 分别统计
      `field_resolution_rate`，校准 §5.3 各表的 `requiredness` 是否过严
- [ ] 统计 `other_unclassified` 的使用率；超过 5% 则扩充 §4.1 枚举
- [ ] 为 §6.3 每个 `metric_family` 各写 1 个 complete + 1 个 incomplete 样例
- [ ] 为 §5.3 每张路由表各写 1 个「该判 not_applicable」+ 1 个「不该判」的对照样例

---

## 14. 一期联网增强：标识符真实性核验（X1 契约已落地，connector 未实现）

当前 `scripts/sequence_identifier_audit.py` 已离线检查常见登录号格式、HGVS 支持子集、
序列字母表，以及版本化完整参考序列上的范围与参考残基。序列缺 accession、版本或完整性声明时
只产 `partial_extraction`，不得把片段当完整参考序列。它**不能证明记录真实存在**。联网增强接入权威数据源后逐项核验
存在性与元数据。联网结果统一写 `external` evidence 与
`external_validation_candidate`（见 `00-contracts.md §1`、§6.2），不得修改 M1 provenance。

| 标识符 | 核验数据源 | 查出什么 | 结果解读归属 |
| --- | --- | --- | --- |
| 临床试验注册号 | ClinicalTrials.gov / ChiCTR / WHO ICTRP | 号码不存在、终点与注册不符、注册晚于入组 | **M6** |
| 细胞系名称 | Cellosaurus / ICLAC | 已知误认或交叉污染细胞系 | **M3** |
| 抗体 / 试剂 | RRID (Antibody Registry) | 货号不存在、抗体已被证实无特异性 | **M3** |
| 基因 / 蛋白符号 | HGNC / UniProt | 符号已废弃或写错、物种不匹配 | **M2** |
| 参考文献 | Crossref / PubMed / Retraction Watch | 文献不存在、已被撤稿或更正 | **M2** |
| 方案注册号 | PROSPERO | 综述方案未注册或与已注册方案偏离 | **M2** |

外部证据层只负责核验标识符事实并产无 severity signal，**不下审核结论**。
所有 connector 复用单一 type `external_validation_candidate`，不得新增
`identifier_verification` 平行类型。比较结果只取 `match/mismatch/not_comparable/needs_manual_review`；
网络或接口故障产 X1 `system_limitation`，不得当作 `not_found` 或 mismatch。
