# M7 · 结论与讨论合理性

**负责人：MY（敏怡）** · 状态：**一期规则库已填充**

全流程的**收口模块**。核心问题：论文的每一条主张，是否被它自己的数据支持？

**一期边界**：只判断 **claim ↔ evidence 的对齐关系**。不查外部证据、不判断创新性、
不做常识校验。违背基础常识的结论（如「面粉可治疗癌症」）标记为
`claim_beyond_evidence` 交人工复核即可。

**这三件事二期都要做**，本模块是它们的归属方，规则见 §9。一期先把 claim 抽取和对齐做扎实 ——
二期的三项能力全都建立在「已经准确抽出每一条 claim 及其支撑证据」之上，这一步做不好，
接外部数据库也只是把错误的 claim 拿去比对。

**本文件依赖 `00-contracts.md`。** finding 结构、`evidence_refs[]`、severity 枚举、
证据登记表的定义都在那里。M7 的 finding **必须**在 `evidence_refs[]` 中独立给出稿件证据，
不得仅引用 signal id。

---

## 1. 输入

| 来源 | 用途 |
| --- | --- |
| `structured_result_v2.conclusion.claims[]` | 主张全集，每条含 `claim_id` / `statement` / `scope` / `supported_by[]` / `evidence_refs[]` |
| `structured_result_v2.article_design` | **判定证据层级的主依据**（§3.1） |
| `structured_result_v2.key_data[]` | 核对 `supported_by` 指向的数值是否真的支持该主张 |
| `structured_result_v2.conclusion.limitations` | 判定 `limitations_evasive` |
| `figure_records[]` | claim 引用图时核对图是否真的展示了该结论 |
| `all_extraction_signals[]` 中 `claim_without_resolved_evidence_link` | 提示哪些 claim 的支撑链断了 |
| **M2–M6 的 findings** | 结论的可信度取决于底下几层有没有塌（§6） |

**M7 必须最后跑。** 它是唯一需要消费其他审核模块产物的模块。
Stage 4 的并行执行中，M7 的调度顺序排在 M2–M6 之后。

---

## 2. claim 的解析前提

### 2.1 一条 claim 必须先定四个属性

| 属性 | 取值 | 从哪里判 |
| --- | --- | --- |
| `claim_tier` | C0–C6，见 §3.2 | `statement` 的语义 |
| `assertion_mode` | `assertive` / `hedged` | `statement` 的措辞，见 §4 |
| `scope_qualified` | `true` / `false` | `scope` 字段是否写明物种/剂量/人群/时间窗限定 |
| `location` | `abstract` / `discussion` / `conclusion` | 该 claim 的 `evidence_refs[0]` 的 locator |

四者缺一不可 —— 越界判定（§5.1）同时依赖这四个属性。

### 2.2 claim 抽取的边界

M7 **不重新抽取** claim —— `claims[]` 由 M1 在 Stage 2 产出。
若 `claims[]` 为空数组而稿件明显有结论段，说明 M1 抽取失败，
M7 **不得**因此立 finding，应确认是否存在对应的 `system_limitation`；
没有则产出**一条** `discussion_hollow` 以外的观察交人工 —— 具体见 §7 的边界说明。

---

## 3. 证据层级与主张层级（本模块核心）

### 3.1 证据层级 evidence_tier

由 `article_design` 决定。一篇论文含多个 `design_components[]` 时，
**每条 claim 取其 `supported_by` 实际指向的那个实验的层级**，
而不是取全文最高层级 —— 这是最常见的误判来源。

| tier | 名称 | 对应 `design.type` |
| --- | --- | --- |
| `E0` | 计算 / 预测 | `bioinformatics`, `prediction_model`, `simulation` |
| `E1` | 分子 / 无细胞体系 | `in_vitro`（生化实验，无活细胞） |
| `E2` | 细胞 | `in_vitro`（细胞系或原代细胞） |
| `E3` | 类器官 / 离体组织 | `organoid`, `ex_vivo` |
| `E4` | 动物在体 | `in_vivo_animal` |
| `E5` | 人体观察性 | `cohort`, `case_control`, `cross_sectional`, `case_series`, `case_report` |
| `E6` | 人体干预非随机 | `nonrandomized_trial`, `single_arm_trial` |
| `E7` | 人体随机对照 | `randomized_controlled_trial` |
| `E8` | 证据合成 | `systematic_review`, `meta_analysis` |

`diagnostic_accuracy` 单列：其证据层级取决于受试者谱与参照标准，
按 `E5` 处理，但允许的诊断性能主张见 §3.3 脚注。

### 3.2 主张层级 claim_tier

| tier | 名称 | 典型措辞 |
| --- | --- | --- |
| `C0` | 描述性观察 | 「我们观察到 X 在 Y 条件下升高」 |
| `C1` | 关联 | 「X 与 Y 相关」「X 水平与 Y 风险呈正相关」 |
| `C2` | 机制 | 「X 通过 Z 通路调控 Y」 |
| `C3` | 因果 | 「X 导致 / 引起 / 驱动 Y」「敲除 X 消除了 Y」 |
| `C4` | 转化潜力 | 「X 是潜在治疗靶点 / 生物标志物」 |
| `C5` | 临床疗效 | 「X 治疗 Y 有效」「X 改善患者预后」 |
| `C6` | 临床推荐 | 「应当在临床使用 X」「推荐 X 作为一线方案」 |

### 3.3 允许对照表（一期判据核心）

**`max_assertive_tier`**：该证据层级下，可以**直陈**的最高主张层级。
**`max_hedged_tier`**：加上合规的限定措辞（§4）后，可以**提出**的最高主张层级。

| evidence_tier | max_assertive_tier | max_hedged_tier | 说明 |
| --- | --- | --- | --- |
| `E0` 计算 | `C1` 关联 | `C2` 机制 | 预测结果**不构成**机制证据，须有湿实验验证 |
| `E1` 分子 | `C2` 机制 | `C3` 因果 | 无细胞体系的因果限于该生化反应本身 |
| `E2` 细胞 | `C2` 机制 | `C4` 转化潜力 | **细胞实验不得直陈 C3 整体因果**；C4 必须限定「潜在」 |
| `E3` 类器官 | `C3` 因果 | `C4` 转化潜力 | 因果限于该模型体系 |
| `E4` 动物 | `C3` 因果 | `C4` 转化潜力 | **因果必须限定物种**；不得直陈 C5 临床疗效 |
| `E5` 人体观察 | `C1` 关联 | `C3` 因果 | 因果需满足 §5.3 的三项附加条件，否则仍限 C1 |
| `E6` 非随机干预 | `C3` 因果 | `C5` 临床疗效 | 无随机化，混杂无法排除 |
| `E7` RCT | `C5` 临床疗效 | `C6` 临床推荐 | 疗效**必须限定试验人群、剂量、随访时长** |
| `E8` 证据合成 | `C6` 临床推荐 | `C6` | 推荐强度受纳入研究质量制约（由 M4 的 `risk_of_bias` 结果调制） |

> `diagnostic_accuracy` 脚注：允许直陈的最高主张是「在本研究的受试者谱下，
> 指标试验相对该参照标准的敏感度/特异度为 X」（等价 `C1`）。
> 主张「可用于临床筛查」等价 `C5`，需要 `E6` 及以上的前瞻性验证队列。

### 3.4 层级差与 severity

```
Δ = claim_tier − 该证据层级允许的上限
    （assertive 模式用 max_assertive_tier，hedged 模式用 max_hedged_tier）

Δ ≤ 0          → 不构成 finding
Δ = 1          → major
Δ ≥ 2          → critical
```

**修正项**（先算 Δ，再依次应用）：

| 条件 | 修正 |
| --- | --- |
| `scope_qualified = true`（明确写了物种/剂量/人群限定） | Δ 减 1 |
| claim 出现在 **Abstract 的结论句**中 | Δ 加 1（摘要是传播面最大的位置） |
| claim 出现在 Discussion 的「未来方向」段且 hedged | Δ 减 1 |
| 支撑该 claim 的分析被 M4 判为 `critical` | 直接置 `unsupported_claim` (critical)，不再算 Δ |

---

## 4. 措辞强度判定（hedging）

### 4.1 限定动词白名单（判为 `hedged`）

命中**任一**即为 `hedged`：

```
英文：may / might / could / suggest(s) / indicate(s) that ... may /
      appear(s) to / seem(s) to / potential / potentially / possible /
      is associated with / warrants further study / merits investigation /
      these findings raise the possibility / preliminary evidence
中文：可能 / 提示 / 或可 / 有望 / 潜在 / 似乎 / 值得进一步研究 /
      初步提示 / 相关（用于描述关联而非因果时）
```

### 4.2 直陈动词（判为 `assertive`）

```
英文：demonstrate(s) / prove(s) / establish(es) / confirm(s) / shows that /
      causes / induces / drives / leads to / is effective / should be used /
      is recommended / therapeutic efficacy
中文：证明 / 证实 / 确立 / 表明……导致 / 引起 / 驱动 / 有效 /
      应当 / 推荐 / 具有疗效
```

### 4.3 三条判定规则

1. **同句中限定词与直陈词并存时，以直陈词为准。**
   「These results demonstrate that X may improve outcomes」判 `assertive`
   —— `demonstrate` 已经把不确定性收走了。
2. **限定词修饰的必须是主张本身，不是次要成分。**
   「X significantly reduced tumor volume, which may involve apoptosis」——
   主张「X 降低瘤体积」是 `assertive`（`may` 只修饰机制猜测）。
   拆成两条 claim 分别判定。
3. **`is associated with` 只有在描述 `C1` 时算限定。**
   用它描述 `C3` 及以上（「X is associated with causing Y」）判 `assertive`。

---

## 5. 规则库

每条规则给出：触发条件、severity、**证据要求**（M7 必须独立给出的稿件证据）。

### 5.1 `claim_beyond_evidence` · 外推超出实验条件

- **触发**：§3.4 的 Δ > 0，且不属于 §5.3 / §5.4 的专门情形。
- **severity**：按 §3.4（Δ=1 → major；Δ≥2 → critical）。
- **证据要求**：至少两条 `present` ——
  ①该 claim 的原文（`evidence_refs` 取自 `claims[].evidence_refs`）；
  ②确立证据层级的方法学原文（如「HepG2 cells were treated…」）。
  **只给结论原文不够** —— 必须让复核者看到「这篇论文实际做的是什么层级的实验」。
- **detail 必须写明**：实测证据层级、主张层级、允许上限、Δ 与修正项。

典型越界（保留敏怡原表并给出层级映射）：

| 越界模式 | 层级表达 |
| --- | --- |
| 细胞实验 → 直接主张临床疗效 | E2 → C5，Δ=3 → critical |
| 单一物种/品系 → 主张普适生物学机制 | E4 → C2 但无 scope 限定 → 见 §5.5 |
| 单中心小样本 → 主张人群层面推荐 | E5/E6 → C6，Δ≥1 → major 起 |
| 特定剂量/时间窗 → 主张任意条件下有效 | `scope_qualified = false` → 不得减 1 |
| 相关性研究 → 主张因果 | 见 §5.3 `causal_overreach` |

### 5.2 `unsupported_claim` · 主张无数据支撑

- **触发**（满足任一）：
  1. `claims[].supported_by` 为空数组；
  2. 存在指向该 `claim_id` 的 `claim_without_resolved_evidence_link` signal
     （`supported_by` 解析不到任何 `key_data.id` 或证据）；
  3. `supported_by` 指向的 `key_data` 组 `status ∈ {conflicting, ambiguous, parse_failed}`
     —— 支撑数值本身没定下来，主张就谈不上被支持；
  4. 支撑数值与主张**方向相反或量级不符**（如主张「亚微摩尔级」但数值为两位数微摩尔）。
- **severity**：`critical`。
- **证据要求**：claim 原文 + 检索支撑的 `absence` 证据（情形 1、2），
  或指向该 `key_data` 全部观测的 `present` 证据（情形 3、4）。
- **注意**：情形 2 **不得**仅引用 signal id 结案 —— 必须自行确认
  `supported_by` 中每一项确实无法解析，并把检索过程写成 `absence` 证据。

### 5.3 `causal_overreach` · 相关性表述为因果

- **触发**：`evidence_tier = E5`（人体观察性）且 `claim_tier ≥ C3`，
  且**未同时满足**下列三项附加条件：
  1. 明确的**时序**（暴露先于结局，`follow_up` 字段为 `reported` 且为纵向设计）；
  2. **混杂控制**（`confounders` 字段为 `reported`，且 `statistical_methods` 含多因素校正）；
  3. **剂量-反应关系**或工具变量/孟德尔随机化等因果推断设计。
- **severity**：三项全不满足 → `critical`；满足 1–2 项 → `major`。
- **证据要求**：claim 原文 + 设计描述原文 + 缺失项的 `absence` 证据。
- **不触发的情形**：`cross_sectional` 研究若使用了明确的因果推断框架并自陈局限，
  且 claim 为 `hedged`，则 Δ 计算已覆盖，不另立本条。

### 5.4 `negative_result_misread` · 不显著误读为无差异

- **触发**：claim 表述为「无差异 / 无影响 / 与对照相当 / X does not affect Y」，
  且**未满足**下列任一：
  1. 报告了效能分析或等效性/非劣效性边界（`sample_size_justification` 为 `reported`
     且明确为等效性设计）；
  2. 报告了效应量的置信区间且区间落在预设等效界内。
- **severity**：`major`。
- **证据要求**：claim 原文 + 该比较的统计结果原文 + 效能/等效界的 `absence` 证据。
- **常见形态**：`p = 0.21` → 「两组无显著差异，说明 X 不影响 Y」。
  **不显著只说明没有证据支持有差异，不等于有证据支持无差异。**

### 5.5 `significance_overstated` · 夸大统计显著性

- **触发**（满足任一）：
  1. `p` 位于 0.01–0.05 且被描述为「显著改善 / 强效 / 明显优于」而未报效应量；
  2. 报告了 `p` 但主张的是**临床意义**（`C5` 及以上）而未讨论最小临床重要差值（MCID）；
  3. 多重比较未校正（M4 已报出 `multiple_comparison_correction`）却仍称某个亚组结果「显著」。
- **severity**：`major`。
- **证据要求**：claim 原文 + `p` 值与效应量所在位置的 `present` 证据
  （或效应量的 `absence` 证据）。

### 5.6 `limitations_evasive` · 回避核心局限

- **触发**：M2–M6 中存在 `severity ≥ major` 的 finding，
  而 `conclusion.limitations` 满足任一：
  1. `status = not_reported`；
  2. `status = reported` 但其文本**未覆盖**任何一条 major finding 所指的问题域。
- **覆盖判定**：把每条 major finding 的 `category` 映射到局限性关键词集
  （如 `sample_size_reporting` → {样本量, sample size, underpowered, 样本较少}），
  局限性文本命中该集合中任一词即视为已覆盖该条。
- **severity**：全部未覆盖 → `major`；部分覆盖 → `minor`。
- **证据要求**：`limitations` 原文（或其 `absence` 证据）+ 被回避的那条 finding 的锚点证据。
- **注意**：这是 M7 唯一一条**以其他模块 finding 为触发条件**的规则，
  但证据仍须独立给出 —— 不得只写「M4 报了问题而作者没提」。

### 5.7 `selective_citation` · 选择性引用文献

- **一期能做的部分**：只判**论文自身内部**的选择性，不查外部文献。
  - **触发**：Discussion 中出现「与既往研究一致」类表述，
    但该论文自身的某个结果与该表述矛盾（如某亚组结果方向相反却未被讨论）。
- **severity**：`major`。
- **证据要求**：Discussion 原文 + 被回避的自身结果的 `present` 证据。
- **一期不做**：判断作者是否漏引了外部反证文献 —— 那需要文献库，归 §9.1。

### 5.8 `discussion_hollow` · 讨论仅复述结果

- **触发**：Discussion 段落中，**未出现**下列任一要素：
  与既往文献的比较、替代解释、机制推测、局限性、临床或研究意义。
  即讨论内容与 Results 高度重合。
- **severity**：`minor`。
- **证据要求**：Discussion 原文。
- **判定要谨慎**：短报告（brief report）与病例报告的讨论天然简短，
  `primary_design.type ∈ {case_report, case_series}` 时**不触发本条**。

---

## 6. 与下层模块联动（降级规则表）

M7 消费 M2–M6 的 findings。**联动只影响 M7 自己 finding 的 severity 与
`review_confidence`，不改写其他模块的 finding。**

| 上游 finding | 触发条件 | 对 M7 的影响 |
| --- | --- | --- |
| M4 `wrong_statistical_test` (critical) | claim 的 `supported_by` 指向该分析 | 该 claim 直接判 `unsupported_claim` (critical)，不再算 Δ |
| M4 `sample_size_reporting` (critical) | 同上 | 同上 |
| M4 `multiple_comparison_correction` | claim 引用了未校正的亚组结果 | 触发 §5.5 情形 3 |
| M3 `missing_control` | claim 为 `C3` 及以上 | Δ 加 1（无对照则因果主张再降一级） |
| M3 `unnecessary_animal_use` | —— | 不影响 M7（属伦理与设计，不影响结论成立性） |
| M5 `figure_text_contradiction` | claim 引用该图 | 该 claim 判 `unsupported_claim` (critical)，detail 标注图文矛盾 |
| M5 `chart_type_mismatch` | claim 引用该图 | 该 claim 的 finding `review_confidence` 降一级 |
| M5 `figure_should_be_main_text` | claim 引用该 supplement 图 | 不改 severity，在 detail 中提示核心证据位置不当 |
| M2 `internal_inconsistency` | claim 引用了冲突数值 | 触发 §5.2 情形 3 |
| M6 任何 finding | —— | 不影响 M7（伦理合规不改变结论是否成立） |
| **（二期）** M5 `duplicate_region_within_paper` / `splice_artifact_suspected` | claim 引用该图 | 相关 claim 标 `critical`，`manual_review.who = editor`，直送编辑 |

**实现约束**：联动依据是上游 finding 的 `evidence_refs[]` 与 claim 的
`supported_by` / `evidence_refs[]` 是否指向同一锚点（同一 `figure`+`panel`、
`table`、或 `paragraph_id`）。锚点对不上就不联动 —— **不得**因为「M4 报了个问题」
就把全文所有 claim 降级。

---

## 7. 与 M2 的边界

两个模块都看「逻辑」，分界如下：

| 情形 | 归属 | 理由 |
| --- | --- | --- |
| 正文两处数值不一致 | **M2** | 稿件内部矛盾，与结论层级无关 |
| Results 说 A，Discussion 说 B | **M2** | 章节间陈述矛盾 |
| 结果成立但结论跳到更高层级 | **M7** | 层级跃迁 |
| 摘要结论与正文结果不符 | **M2**（矛盾）+ **M7**（若同时越界） | 可同属一个 issue_cluster |
| 章节缺失（无 Discussion） | **M2** | 结构完整性 |
| Discussion 存在但空转 | **M7** | 内容质量 |
| claim 的 `supported_by` 断链 | **M7** | signal 明确路由到 M7 |
| 引用了不存在的 Figure 6 | **M2 / M5** | `unresolved_cross_reference` 不路由到 M7 |

**一句话分界**：M2 管「说的话之间是否自洽」，M7 管「说的话是否被数据撑得住」。

---

## 8. category slug

| slug | 说明 | severity | 规则 |
| --- | --- | --- | --- |
| `unsupported_claim` | 主张无数据支撑 | critical | §5.2 |
| `claim_beyond_evidence` | 外推超出实验条件 | major / critical（按 Δ） | §5.1 |
| `causal_overreach` | 相关性表述为因果 | major / critical | §5.3 |
| `negative_result_misread` | 不显著误读为无差异 | major | §5.4 |
| `significance_overstated` | 夸大统计显著性 | major | §5.5 |
| `limitations_evasive` | 回避核心局限 | major / minor | §5.6 |
| `selective_citation` | 选择性引用（一期限论文内部） | major | §5.7 |
| `discussion_hollow` | 讨论仅复述结果 | minor | §5.8 |
| `claim_magnitude_mismatch` | 主张的量级与自身数据不符 | major | §5.2 情形 4 |

**二期新增**（一期不得使用）：`claim_contradicted_by_literature`、
`claim_unreplicated`、`violates_domain_common_sense`。

---

## 9. 正例 / 反例

每条规则至少一个「该报警」与一个「不该报警」。

### 9.1 `claim_beyond_evidence`

**该报警**：HepG2 细胞实验（E2），Discussion 直陈
「Compound A is an effective therapy for hepatocellular carcinoma」。
→ C5，`assertive`，E2 允许直陈上限 C2，Δ=3 → **critical**。

**不该报警**：同一实验，Discussion 写
「These in vitro findings suggest that Compound A may warrant further
evaluation as a potential therapeutic candidate in HCC models」。
→ C4，`hedged`（`suggest` + `may` + `potential`），E2 的 `max_hedged_tier` = C4，
Δ=0 → **不报**。

### 9.2 `causal_overreach`

**该报警**：横断面研究（E5）发现血清 MHR 与子痫前期相关，
结论写「Elevated MHR causes preeclampsia」。
→ 无时序、无多因素校正、无剂量反应 → **critical**。

**不该报警**：前瞻队列（E5）中早孕期 MHR 测定先于子痫前期发生（时序 ✓），
多因素 logistic 校正 BMI/年龄/血压（混杂 ✓），且报告了限制性立方样条剂量反应（✓），
结论写「Higher early-pregnancy MHR was independently associated with increased
risk of preeclampsia」→ 仍是 C1 表述，三项条件齐备 → **不报**。

### 9.3 `negative_result_misread`

**该报警**：`p = 0.31`，n=8/组，无效能分析，结论写
「X 对肿瘤生长无影响」→ **major**。

**不该报警**：预设非劣效界 Δ=10%，实测差值 95% CI 为 (−3.2%, 4.1%)，全部落在界内，
结论写「X 在预设非劣效界内不劣于 Y」→ **不报**。

### 9.4 `limitations_evasive`

**该报警**：M4 报出 `sample_size_reporting` (major)，`limitations` 只写
「本研究为单中心研究」，未提样本量或效能 → **major**。

**不该报警**：同样情形，`limitations` 写「样本量偏小，效能不足以检出小效应，
结果需在更大队列中验证」→ 命中关键词集 → **不报**。

### 9.5 `discussion_hollow`

**该报警**：Discussion 三段全部为 Results 数值的复述，无文献比较、无机制、无局限。

**不该报警**：`case_report` 的简短讨论 —— §5.8 明确不触发。

---

## 10. TODO（一期）

- [x] 填充 §3.3 实验层级-主张层级对照表（本模块最高优先级）
- [x] 定义 §6 联动降级的具体触发规则表
- [x] 与 M2 划清边界（§7）
- [x] 明确「温和措辞」白名单（§4）
- [ ] 在 `datasets/` 的 10 篇语料上逐篇标注 claim_tier 与 evidence_tier，
      校准 §3.3 对照表与 §3.4 的 Δ 阈值是否过严
- [ ] 补齐 §5.6 的 category → 局限性关键词映射表（现只给了 `sample_size_reporting` 一例）
- [ ] 与 M4 确认 §6 中 `wrong_statistical_test` 与 `sample_size_reporting`
      的准确 slug 名（M4 reference 填完后核对）
- [ ] 为 §4.1/§4.2 的中英措辞表补充实际语料中出现过的变体

---

## 11. 二期扩展（本期不实现，规则先写下）

三项能力都归本模块。**现在只写判据，不写实现**；数据源统一走 MCP 接口，
本节只声明「需要什么数据」，不要自行实现调用方式。

### 11.1 结论科学真伪核验

- 数据源：PubMed / Europe PMC 文献库 MCP
- 判据草案：抽出每条 claim 的核心断言 → 检索同主题既往研究 → 分类为
  `consistent` / `contradicted` / `novel_unreplicated` / `insufficient_evidence`
- 输出 category：`claim_contradicted_by_literature`(critical) / `claim_unreplicated`(info)
- **风险**：检索召回不全会造成「查无反证 = 结论正确」的假阴性。二期必须要求
  `review_confidence: low` 起步，且此类 finding 一律强制人工复核。

### 11.2 领域创新性 / 重要性

- 数据源：文献库 + 引用网络
- 前置：**先定义可量化的新颖度判据**，否则会退化成主观打分。候选方向：
  claim 与既有文献的语义距离、方法组合是否首次出现、研究对象是否为空白领域
- 输出定位：不给「创新性高/低」的结论，只给「该主张在检索范围内未见同类报道」
  这类**事实性描述**，由人工判断价值 —— 这条边界二期也不要越。

### 11.3 基础常识校验

- 数据源：领域常识规则库（需自建）
- 建库方式：**先积累一期人工复核环节的误判样本**，把真实出现过的常识性错误沉淀成规则，
  而不是先验地枚举常识。一期的人工复核记录就是二期的训练材料。
- 输出 category：`violates_domain_common_sense`(critical)

### 11.4 外部证据的契约扩展

二期引入外部证据后，**扩展而非重构**现有契约（`SKILL.md §0.2`）：
在 `evidence_registry` 中新增第三种证据型 `external`：

```json
{
  "id": "EV-101",
  "type": "external",
  "database": "pubmed",
  "record_id": "PMID:12345678",
  "query": "compound A hepatocellular carcinoma IC50",
  "retrieval_date": "2026-09-01",
  "version": "2024-03-11",
  "retraction_or_correction_status": "none",
  "relation_to_claim": "contradicts",
  "created_by": "M7"
}
```

**规则**：引入 `external` 证据的 finding，其 `evidence_refs[]` 中**必须同时**
含至少一条 `present` 型稿件内证据 —— 论文内定位不可省略。
`00-contracts.md §1.2` 的两型表届时扩为三型，`evidence.schema.json` 增加对应分支。
