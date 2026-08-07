# 论文审核报告 · 未署名两臂随机对照试验（fulltext.txt）

> DOI：— ｜ 期刊：— ｜ 输入格式：`plain_text`

## 一、执行摘要

> **边界声明**：本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查
> 与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。**
> 本 Skill 的任何评分均为筛查信号，不构成录用、退稿或发表决定。

### 本报告能回答什么

> 已执行 M2–M7；"未产出 finding"只表示本流程在已取得证据中未检出，不等于论文结论已被证实。
>
> 注：本次按路由实际执行 **M2 / M4 / M6 / M7** 四个模块（RCT 设计 + 候选类型触发）；
> M3 不适用（无动物/体外/细胞成分）、M5 不适用（无图像资产）。跳过二者是路由结果，
> 不等同于该两维度"无问题"。

| 执行模式 | submode | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- |
| `full_review` | — | M2, M4, M6, M7 | M3（无适用内容）, M5（无适用内容） |

- 范围依据：RCT 设计必开 M4/M6/M7；候选类型 `possible_reporting_omission` / `possible_internal_inconsistency` 触发 M2。
- 已执行阶段：stage_1, stage_2, stage_4, stage_5

### 审稿人先看

- 范围内问题权重合计：`100/100`；本次不作全稿分段。
  > ⚠️ 这是已执行模块范围内的局部筛查分，`comparable_to_full_review=false`。
  > 未执行模块没有被判定为"无问题"；本分数不得与任何其他报告的风险分横向比较或排序，
  > 包括不同定向核查范围的 partial 分数。
- 评分边界：分段阈值未经实证验证，是初始经验值，不得表述为自动化的录用/退稿决定。
- findings：critical 4 ／ major 11 ／ minor 3 ／ info 1（共 19 条，聚簇 19 个）；复核动作：P0×4，P1×2，P2×2。
- 抽取覆盖率计算值：`0.75`；必须结合第七节分子/分母解释，不是稿件质量概率。
- 审核置信度：`0.675`。这是未经校准的证据支撑指数，不是 finding 正确概率，也不是稿件质量概率。
  （extraction_coverage 0.75 × Q 1.0 × C 0.9；C 扣减来自 KD-001 受试者总数冲突组）

### 优先处理（最多三项）

- [ ] **[P0] 核对受试者流与核心计数：12+18=30 与 n=28 的差异来源**（统计审稿人）
  - 关联判断：`M4-001` [major] 分组人数合计 30 ≠ 声明总数 28（确定性计数错误）—— `Results ¶results-p1`
- [ ] **[P0] 核对试验核心方法学要素：干预内容、随机化、盲法**（领域审稿人）
  - 关联判断：`M2-001` [critical]、`M2-002` [critical]、`M2-004` [critical] —— `Methods ¶methods-p1`
- [ ] **[P0] 核对安全性结论与随访窗口的匹配**（领域审稿人）
  - 关联判断：`M7-001` [critical]、`M7-002` [major] —— `Conclusion ¶conclusion-p1`

## 二、结构化结果表

结构化结果版本：`structured_result_v2`；`stage_3b_executed=false`。本节只展示条件必填、未解析/缺失及与 finding 证据相交的字段；另有 0 个已报告或不适用的 recommended/optional 字段仅保留在 JSON。

| 字段 | 适用性 / 必填性 | 状态 | 值 / 单位 | 抽取置信度 | 原文定位 |
| --- | --- | --- | --- | --- | --- |
| `objective.primary_endpoint` | `applicable` / `required` | `not_reported` | — | `high` | [EV-013｜缺失检索：Methods+Results｜结果 no_match] |
| `population.subjects` | `applicable` / `required` | `reported` | 28 例 ASA I–III 拟手术患者 | `high` | [EV-001｜sec:methods¶methods-p1] |
| `design.study_design` | `applicable` / `required` | `reported` | randomised controlled trial（两臂） | `high` | [EV-001｜sec:methods¶methods-p1] |
| `design.randomization_method` | `applicable` / `required` | `not_reported` | — | `high` | [EV-011｜缺失检索：Methods｜结果 no_match] |
| `design.allocation_concealment` | `applicable` / `required` | `not_reported` | — | `high` | [EV-011｜缺失检索：Methods｜结果 no_match] |
| `design.blinding` | `applicable` / `required` | `not_reported` | — | `high` | [EV-012｜缺失检索：Methods+Results｜结果 no_match] |
| `design.interventions` | `applicable` / `required` | `not_reported` | — | `high` | [EV-015｜缺失检索：Methods+Results｜结果 no_match] |
| `design.registration` | `applicable` / `required` | `not_reported` | — | `high` | [EV-009｜缺失检索：全文｜结果 no_match] |
| `measurement.sample_size_justification` | `applicable` / `required` | `not_reported` | — | `high` | [EV-010｜缺失检索：Methods｜结果 no_match] |
| `measurement.statistical_methods` | `applicable` / `required` | `not_reported` | — | `high` | [EV-014｜缺失检索：Methods+Results｜结果 no_match] |
| `measurement.followup_duration` | `applicable` / `required` | `reported` | 48（hours after surgery） | `high` | [EV-002｜sec:methods¶methods-p2] |
| `declarations.ethics_statement` | `applicable` / `required` | `not_reported` | — | `high` | [EV-007｜缺失检索：全文｜结果 no_match] |
| `declarations.informed_consent` | `applicable` / `required` | `not_reported` | — | `high` | [EV-008｜缺失检索：全文｜结果 no_match] |
| `declarations.coi` | `applicable` / `required` | `not_reported` | — | `high` | [EV-019｜缺失检索：全文｜结果 no_match] |

### 核心数据观测组摘要

| 观测组 / 指标 | 上下文 | 状态 | canonical | 报告完整性 / 缺失要素 |
| --- | --- | --- | --- | --- |
| `KD-001` · participant_count_total (`participant_flow`) | EXP-01 · endpoint=enrolled_total | `conflicting` | —（冲突组无 canonical） | `not_assessed`；— |

### 需要回查来源的观测组

#### KD-001 · participant_count_total · `conflicting`

| observation | 值 / 单位 | 不确定度 / n / 重复类型 | 来源 | 置信度 | 人工核对 | 原文定位 |
| --- | --- | --- | --- | --- | --- | --- |
| `OBS-001` | 28 | — | `explicit_main_text`（Methods 声称入组数） | `high` | `false` | [EV-001｜sec:methods¶methods-p1] |
| `OBS-002` | 30（=12+18 求和推导） | — | `explicit_main_text`（Results 分组计数） | `high` | `true` | [EV-003｜sec:results¶results-p1] |

## 三、图表解读与原图定位

> 本节记录 Stage 3 的可见事实与只读解读，不是 M5 审核判断。

本模式未执行 Stage 3（全文无图像资产），且唯一被引用的 Table 1 表体未随输入提供（ SYS-001）；
不得解释为稿件图表均无问题。Table 1 仅存正文括号摘要：ASA II: 15、ASA III: 13（合计 28，无按组分列）。

## 四、审核发现

### [critical] CL-01 · 主要结论『No serious complications occurred』无任何事件层面支撑

- 类别：unsupported_claim
- 关联判断：
  - `M7-001` [critical] [M7] **主要结论无任何事件层面支撑**：全文无不良事件表、无 serious 定义、无事件计数，连显式 0 事件数据陈述也不存在；该句是 Conclusion 中唯一实质性主张。`review_confidence: high`；rule_ref: `07-conclusions-discussion#unsupported_claim`；manual_review: P0（领域审稿人）——要求提供事件层面数据，在获得前该安全性结论不可采信。来源：multiple（候选 CAND-13 + M7 规则库）。
    - 证据：[EV-006｜Conclusion ¶conclusion-p1]、[EV-016｜缺失检索：Methods+Results 事件数据｜no_match]、[EV-003｜Results ¶results-p1]、[EV-004｜Results ¶results-p2]
- 证据包（expanded）：
  - EV-006（present）：`Conclusion ¶conclusion-p1` — "No serious complications occurred."
  - EV-016（absence）：检索 Methods/Results，检索词 [adverse event, complication rate, complication count, event table, safety data]，结果 no_match；并发症一词仅出现于 Conclusion 主张句。
  - EV-003（present）：`Results ¶results-p1` — "Group A comprised 12 patients and Group B comprised 18 patients."
  - EV-004（present）：`Results ¶results-p2 (Table 1)` — "Baseline characteristics are shown in Table 1 (ASA II: 15, ASA III: 13)."

### [critical] CL-02 · 干预措施完全未描述

- 类别：missing_reporting_guideline_element
- `M2-004` [critical] [M2]：全文无任何 Group A/B 干预内容，两臂比较失去实质含义，主要结论不可解释。已核实为稿件未写而非材料缺失。rule_ref: `02-macro-logic#missing_reporting_guideline_element`；manual_review: P0（领域审稿人）。来源：multiple（CAND-14）。
  - 证据：EV-015（absence：检索词 intervention/treatment/drug/surgical technique/procedure/control group，no_match）、EV-001、EV-003。

### [critical] CL-03 · 随机化核心要素缺失（序列产生/分配隐藏/分配比例）

- 类别：missing_reporting_guideline_element
- `M2-001` [critical] [M2]：声称 randomised，但序列产生、分配隐藏、分配比例均未描述；SIG-101 证实 12+18=30≠28，使分组与 n=28 下任何合理分配方案均无法对账。rule_ref: `02-macro-logic#missing_reporting_guideline_element`；manual_review: P0（统计审稿人）。来源：multiple（CAND-07 + SIG-101）。
  - 证据：EV-001、EV-011（absence：random sequence/allocation concealment/allocation ratio，no_match）、EV-003。

### [critical] CL-04 · 盲法报告完全缺失

- 类别：missing_reporting_guideline_element
- `M2-002` [critical] [M2]：全文未提及任何角色是否设盲，也未说明为何无法设盲；干预未描述致盲法可行性无法评估。rule_ref: `02-macro-logic#missing_reporting_guideline_element`；manual_review: P0（领域审稿人）。来源：multiple（CAND-08）。
  - 证据：EV-012（absence：blind/masking/double-blind/open-label，no_match）、EV-001。

### [major] CL-05 · 分组人数合计 30 ≠ 声明总数 28（确定性计数错误）

- 类别：table_total_mismatch
- `M4-001` [major] [M4]：Results 分组计数 12+18=30，与 Methods/Conclusion/Table 1 三处一致的 28 不符；SIG-101（difference=2，ran=true）确认。跨节三源对账确认 28 为可靠总数，错误定位于分组计数或存在未报告的脱落/交叉；直接动摇受试者流与安全性分母。按规则库该类不得 critical。rule_ref: `04-statistics#table_total_mismatch`；manual_review: P0（统计审稿人）。来源：multiple（CAND-01/02/04 + SIG-101 + 校正层 XREC-01 并入）。
  - 证据：EV-003、EV-001、EV-005（"All 28 patients were accounted for."）、EV-004。

### [major] CL-06 · 安全性主张未限定于 48 小时观察窗（范围扩张）

- 类别：claim_beyond_evidence
- `M7-002` [major] [M7]：『No serious complications occurred』为无限定直陈，未绑定时间窗，而唯一观察窗为术后 48 小时；短窗不能排除迟发性严重并发症。rule_ref: `07-conclusions-discussion#claim_beyond_evidence`；manual_review: P0（领域审稿人）。来源：multiple（CAND-05）。
  - 证据：EV-006、EV-002（"Follow-up was 48 hours after surgery."）。

### [major] CL-07 · 伦理委员会审批与批件号未报告

- 类别：ETH-HUM-001
- `M6-001` [major] [M6]：人体干预性 RCT 未见伦理审批声明（SIG-601 确认）。定性为报告缺口，不推定未获审批。规范依据：赫尔辛基 2024 ¶23、45 CFR 46.109、21 CFR 56.109、中国 2023 办法第 29 条（citation_confidence high）。rule_ref: `ethics_rules.json#ETH-HUM-001`；manual_review: P0（伦理委员会）。来源：multiple（CAND-09 + SIG-601）。
  - 证据：EV-001、EV-007（absence：ethics/IRB/approval/Helsinki 等检索词，no_match）。

### [major] CL-08 · 知情同意获取过程未报告

- 类别：ETH-HUM-002
- `M6-002` [major] [M6]：前瞻性手术 RCT 无任何知情同意表述（SIG-602 确认）；若主张豁免须按 ETH-HUM-003 说明依据。规范依据：赫尔辛基 2024 ¶25–32、45 CFR 46.116、21 CFR 50.25、CIOMS 2016 G9、中国办法第 33–38 条。rule_ref: `ethics_rules.json#ETH-HUM-002`；manual_review: P0（伦理委员会）。来源：multiple（CAND-11 + SIG-602）。
  - 证据：EV-001、EV-008（absence：consent/informed，no_match）。

### [major] CL-09 · 临床试验前瞻性注册缺失（无任何注册号）

- 类别：ETH-HUM-005
- `M6-003` [major] [M6]：全文无任何注册号（SIG-605 确认），无法核对预注册结局与分析计划；注册号时序核验 not_applicable（无输入，非工具失败）。规范依据：赫尔辛基 2024 ¶35、ICMJE、CIOMS 2016 G24。rule_ref: `ethics_rules.json#ETH-HUM-005`；manual_review: P0（伦理委员会）。来源：multiple（CAND-10 + SIG-605）。
  - 证据：EV-001、EV-009（absence：registration/NCT/ChiCTR 等，no_match）。

### [major] CL-10 · 未定义主要/次要结局，无统计方法描述

- 类别：missing_reporting_guideline_element
- `M2-003` [major] [M2]：Methods 未定义任何结局指标，全文无统计方法；结论因此悬空于未测量指标之上。rule_ref: `02-macro-logic#missing_reporting_guideline_element`；manual_review: P1（统计审稿人）。来源：multiple（CAND-12）。
  - 证据：EV-013、EV-014（均为 absence，no_match）、EV-001。

### [major] CL-11 · Introduction 与 Discussion 完全缺失

- 类别：missing_section
- `M2-005` [major] [M2]：研究问题/假设与结果解读均不存在；无局限性讨论，结论边界无人限定。rule_ref: `02-macro-logic#missing_section`；manual_review: P1（作者）。来源：specialist_rule。
  - 证据：EV-020（absence：全文结构检索，no_match）。

### [major] CL-12 · Abstract 完全缺失

- 类别：missing_section
- `M2-006` [major] [M2]：无结构化摘要。rule_ref: `02-macro-logic#missing_section`；manual_review: P1（作者）。来源：specialist_rule。证据：EV-020。

### [major] CL-13 · References 完全缺失

- 类别：missing_section
- `M2-007` [major] [M2]：全文无任何引用文献。rule_ref: `02-macro-logic#missing_section`；manual_review: P1（作者）。来源：specialist_rule。证据：EV-020。

### [major] CL-14 · 利益冲突声明缺失

- 类别：missing_section
- `M2-008` [major] [M2]：人类受试者 RCT 应报告 COI 声明，全文检索无匹配。伦理/同意/注册的重复条目已并入 M6-001/002/003。rule_ref: `02-macro-logic#missing_section`；manual_review: P1（作者）。来源：specialist_rule。证据：EV-019。

### [major] CL-15 · 无 CONSORT 受试者流向图

- 类别：missing_reporting_guideline_element
- `M2-010` [major] [M2]：RCT 应报告受试者流向；全文无图，叠加 28 vs 30 计数矛盾，受试者流完全无法闭合。样本量计算缺失部分已并入 M4-002。rule_ref: `02-macro-logic#missing_reporting_guideline_element`；manual_review: P1（作者）。来源：specialist_rule。证据：EV-020、EV-010。

### [minor] CL-16 · 资助与数据可得性声明缺失

- 类别：missing_section
- `M2-009` [minor] [M2]：无资助声明、无数据可得性声明；作者贡献亦未报告。rule_ref: `02-macro-logic#missing_section`；manual_review: P2（作者）。来源：specialist_rule。证据：EV-017、EV-018。

### [minor] CL-17 · 纳入标准（ASA I–III）与基线表（仅 ASA II/III）跨节不符

- 类别：internal_inconsistency
- `M2-011` [minor] [M2]：Methods 声明 ASA I–III 可入组，Table 1 摘要仅 ASA II 15 / ASA III 13，无 1 例 ASA I——要么确实未招到 ASA I（需说明），要么标准或表格报告有误。**此为跨节对账新发现（校正层 XREC-02），分块专家结构上不可见。** Table 1 表体缺失限制进一步定位（SYS-001）。rule_ref: `cross_section_reconciliation`；review_confidence: medium；manual_review: P2（作者）。来源：cross_section_reconciliation（CAND-03）。
  - 证据：EV-001、EV-004。

### [minor] CL-18 · N=28 无任何样本量/功效依据

- 类别：power_and_sample_size
- `M4-002` [minor] [M4]：无样本量估算/功效/精度依据，亦无计划入组数；因结局未定义，estimand 也无从谈起。无可复算矛盾、无确证性区间主张，按规则默认 minor。rule_ref: `04-statistics#power_and_sample_size`；manual_review: P1（统计审稿人）。来源：multiple（CAND-06）。证据：EV-001、EV-010。

### [info] CL-19 · 赫尔辛基宣言遵循声明缺失

- 类别：ETH-HUM-004
- `M6-004` [info] [M6]：SIG-604 收编；核心缺口已由 M6-001 覆盖，不叠加定级。rule_ref: `ethics_rules.json#ETH-HUM-004`；manual_review: P2（作者）。来源：deterministic_tool。证据：EV-001、EV-007。

## 五、抽取信号

> 本节是机器观察与下游路由轨迹，不是稿件问题，没有 severity，也不直接进入风险分。共 10 条。

- `SIG-050` · `source_value_conflict`：受试者总数两来源不兼容（28 vs 30），差 2 超出舍入容差。
  - 目标：`key_data.KD-001`；路由：M2, M4；产出阶段：`stage_2`
  - 证据：EV-001、EV-003
- `SIG-101` · `table_total_mismatch`：12+18=30 ≠ 28，difference=2（ran=true, rule_version 2026-08-07）→ 被 M4-001 消费。
  - 目标：Group allocation (Results)；路由：M4, M2；产出阶段：`stage_2`
  - 证据：EV-003、EV-001、EV-005
- `SIG-601` · `ethics_requirement_unmet`（ETH-HUM-001 伦理审批）→ M6-001。证据：EV-001、EV-007。
- `SIG-602` · `ethics_requirement_unmet`（ETH-HUM-002 知情同意）→ M6-002。证据：EV-001、EV-008。
- `SIG-604` · `ethics_requirement_unmet`（ETH-HUM-004 赫尔辛基声明）→ M6-004。证据：EV-001、EV-007。
- `SIG-605` · `ethics_requirement_unmet`（ETH-HUM-005 前瞻注册）→ M6-003。证据：EV-001、EV-009。
- `SIG-607` · `ethics_requirement_unmet`（ETH-CELL-001）：**被 M6 复议驳回**——'patient' 命中 human-derived 标记的词面误报，本研究无离体人源材料，规则适用对象不存在；患者层面缺口已由 SIG-601/602 覆盖。
- `SIG-603` · `partial_extraction`（ETH-HUM-003 豁免依据）：事实不可得，未评估，不立 finding。
- `SIG-606` · `partial_extraction`（ETH-HUM-008 可识别数据）：事实不可得，未评估，不立 finding。
- `SIG-608` · `partial_extraction`（ETH-HGR-001 中国人类遗传资源）：事实不可得，未评估，不立 finding。

## 六、系统限制

> 本节说明系统或输入"哪些地方没看清"。这些条目不是稿件问题，不得据此推断作者遗漏或违规。共 1 条；有受影响目标时，相关"未发现问题"表述一律无效。

- `SYS-001` · `table_unparseable`：Table 1 表格本体未随输入提供，仅有正文括号摘要（ASA II: 15, ASA III: 13）。
  - 受影响模块：M2, M4；目标：`table:1`；字段：—
  - 影响：无法完成按组基线对账、28 vs 30 矛盾在表内的精确定位、其他基线变量核对。
  - 恢复动作：调取 Table 1 表体（或稿件 PDF）后复核；在此之前 28 vs 30 只能维持"错误定位于分组计数或存在未报告脱落"的结论。
  - 定位：[EV-004｜sec:results¶results-p2]

## 七、覆盖率明细

| 子率 | 分子 / 分母（rate） |
| --- | ---: |
| 条件必填字段解析率 | 14 / 14（1.0） |
| 图表可读率 | 0 / 1（0.0） |
| 补充材料可得率 | 不适用（0/0；契约哨兵 rate=1.0） |
| 推荐字段覆盖率（不进加权） | 2 / 2（1.0） |

- 已解析的条件必填字段：objective.primary_endpoint、population.subjects、design.study_design、design.randomization_method、design.allocation_concealment、design.blinding、design.interventions、design.registration、measurement.sample_size_justification、measurement.statistical_methods、measurement.followup_duration、declarations.ethics_statement、declarations.informed_consent、declarations.coi（`not_reported` 属"已解析"：已完成全文检索并确认稿件未报告）
- 未解析的条件必填字段：无
- 不可读图表：`table:1`（SYS-001）
- 不可得补充材料：无
- `extraction_coverage = 0.60×1.0 + 0.25×0.0 + 0.15×1.0 = 0.75`

> `not_reported` 表示已完成规定范围检索并确认稿件未报告，属于"已解析"；
> `parse_failed` 表示系统没读出来，属于"未解析"。两者不得互换。
> 分母为 0 时 schema 内的 `rate=1.0` 只是计算哨兵，报告显示"不适用"，不得解释为 100% 完成。

## 八、人工复核建议

| 优先级 | 排序依据 | 完成时点 |
| --- | --- | --- |
| P0 | 全部 critical；以及不先核对就无法可靠解释核心结论、伦理授权或数据完整性的 major | 形成审稿结论前 |
| P1 | 其他 major：会改变 finding 的成立、严重度或作者必须完成的分析/材料补充 | 给出修改要求前 |
| P2 | minor/info 的报告澄清、定位核对或编辑性修正，不改变当前核心推断 | 常规修订清单中 |

### [ ] [P0] 核对受试者流与核心计数（统计审稿人）

- 排序依据：M4-001 为 major 且直接阻断安全性分母与"28 例均 accounted for"的解释（major+P0）。
- `M4-001` [major]：12+18=30≠28；证据 EV-003/EV-001/EV-005/EV-004（expanded 见 CL-05）。

### [ ] [P0] 核对试验核心方法学要素（领域审稿人）

- 排序依据：critical → P0（M2-001、M2-002、M2-004）。
- `M2-001` [critical]：随机序列/分配隐藏/比例缺失；证据 EV-001/EV-011/EV-003。
- `M2-002` [critical]：盲法缺失；证据 EV-012/EV-001。
- `M2-004` [critical]：干预未描述；证据 EV-015/EV-001/EV-003。

### [ ] [P0] 核对安全性结论（领域审稿人）

- 排序依据：critical → P0（M7-001）；M7-002 major 同锚关联。
- `M7-001` [critical]：主要结论无事件层面支撑；证据 EV-006/EV-016/EV-003/EV-004。
- `M7-002` [major]：未限定 48h 观察窗；证据 EV-006/EV-002。

### [ ] [P0] 核对伦理授权链（伦理委员会）

- 排序依据：不先核对就无法确认伦理授权 → major+P0（M6-001/002/003）。
- `M6-001` [major]：伦理审批未报告；证据 EV-001/EV-007。
- `M6-002` [major]：知情同意未报告；证据 EV-001/EV-008。
- `M6-003` [major]：注册缺失；证据 EV-001/EV-009。

### [ ] [P1] 补交结局定义、统计方法、样本量依据与 CONSORT 图（统计审稿人）

- 排序依据：major（M2-003、M2-010）与 minor（M4-002）→ P1。
- `M2-003` [major]、`M2-010` [major]、`M4-002` [minor]（证据见对应簇）。

### [ ] [P1] 补齐缺失章节与 COI 声明（作者）

- 排序依据：major（M2-005/006/007/008）→ P1。
- `M2-005` [major]、`M2-006` [major]、`M2-007` [major]、`M2-008` [major]（证据：EV-020、EV-019）。

### [ ] [P2] 核实 ASA I–III 标准与 Table 1 无 ASA I 的不符（作者）

- 排序依据：minor → P2。`M2-011` [minor]；证据 EV-001/EV-004；受 SYS-001 限制，建议同时调取表体。

### [ ] [P2] 补交资助/数据可得性声明与赫尔辛基表述（作者）

- 排序依据：minor/info → P2。`M2-009` [minor]、`M6-004` [info]；证据 EV-017/EV-018/EV-007。

---

## 附：候选生命周期台账（15 个发现候选全部结清）

| 候选 | 归宿 | 说明 |
| --- | --- | --- |
| CAND-01 | promoted_to_finding → M4-001 | SIG-101 确定性确认 |
| CAND-02 | merged → M4-001；按组部分 blocked_by_system_limitation（SYS-001） | 15+13=28 佐证总数；表体缺失部分挂起 |
| CAND-03 | promoted_to_finding → M2-011 | Layer 4 跨节对账新发现 |
| CAND-04 | merged → M4-001（CONSORT 面 → M2-010） | |
| CAND-05 | promoted_to_finding → M7-002 | |
| CAND-06 | promoted_to_finding → M4-002 | |
| CAND-07 | promoted_to_finding → M2-001 | M4 以无对应 slug 移交 M2 |
| CAND-08 | promoted_to_finding → M2-002 | |
| CAND-09 | promoted_to_finding → M6-001 | M2-P08 重复条目并入 |
| CAND-10 | promoted_to_finding → M6-003 | M2-P09 重复条目并入 |
| CAND-11 | promoted_to_finding → M6-002 | M2-P08 重复条目并入 |
| CAND-12 | promoted_to_finding → M2-003 | M4 判零检验无法绑定统计结论 |
| CAND-13 | promoted_to_finding → M7-001 | |
| CAND-14 | promoted_to_finding → M2-004 | |
| CAND-15 | blocked_by_system_limitation（SYS-001） | 表体未随输入提供；非稿件问题，不得记 rejected |

## 附：运行时遥测

```json
{
  "child_sessions": 6,
  "task_calls": 9,
  "continuations": 3,
  "modules_run": ["M2", "M4", "M6", "M7"],
  "modules_skipped": {"M3": "无动物/体外/细胞成分与湿实验标识符", "M5": "无图像资产"},
  "references_required": ["02-macro-logic", "04-statistics", "06-ethics-compliance", "07-conclusions-discussion"],
  "references_read": ["02-macro-logic", "04-statistics", "06-ethics-compliance", "07-conclusions-discussion"],
  "routing_recall": 1.0,
  "tool_execution_recall": 1.0,
  "candidate_count_discovery": 15,
  "candidate_count_promoted": 12,
  "finding_origin_breakdown": {"multiple": 10, "specialist_rule": 7, "deterministic_tool": 1, "cross_section_reconciliation": 1, "external_validation": 0}
}
```

工具执行台账（每项均落终态）：`table_total`×2 = executed（SIG-101；ASA 检查一致无信号）；`ethics_compliance_check` = executed（SIG-601…608）；`count_percentage` / `grim` / `test_statistic_p` / `ci_estimate` / 外部标识符核验（cell_line、trial_registration、DOI、gene_symbol）/ `figure_integrity_audit` / `normalize_biomed_units` = not_applicable（全文无对应可解析对象，理由逐项见 review_report.json.runtime_utilization.tool_execution_ledger）。

> 规则库贡献观察：19 条 finding 中仅 1 条纯由确定性工具产生（M6-004），10 条为候选+规则库+工具互证（multiple），
> 7 条纯由模块规则库产生，1 条为跨节校正新发现 —— 规则库贡献显著，无需裁剪。
