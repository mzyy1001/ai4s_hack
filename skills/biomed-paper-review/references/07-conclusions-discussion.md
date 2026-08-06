# M7 · 结论与讨论合理性

**负责人：MY（敏怡）** · 状态：**一期规则库已填充**

全流程的**收口模块**。核心问题：论文的每一条主张，是否被它自己的数据支持？

**当前交付边界**：只判断 **claim ↔ evidence 的对齐关系**。不查外部证据、不判断创新性、
不做常识校验。违背基础常识的结论（如「面粉可治疗癌症」）标记为
`claim_beyond_evidence` 交人工复核即可。

这三件事可作为一期联网增强，本模块是它们的归属方，规则见 §11。它们当前均未实现，
且全都建立在「已经准确抽出每一条 claim 及其支撑证据」之上；这一步做不好，
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
| `location` | `abstract` / `discussion` / `conclusion` | 在 `evidence_refs[]` 中选择 `quote` 覆盖该 claim 原文的证据，再读取其 locator；不得默认取数组首项 |

四者缺一不可 —— 越界判定（§5.1）同时依赖这四个属性。

### 2.2 claim 抽取的边界

M7 **不重新抽取** claim —— `claims[]` 由 M1 在 Stage 2 产出。
若 `claims[]` 为空数组而稿件明显有结论段，说明 M1 抽取失败。
M7 **不得**因此立 finding，也不得自创“观察”记录；终止 M7、要求 Stage 2 重跑，
并确认 Stage 2 是否已有 `parse_failed` 类 `system_limitation`。Stage 4 无权补写
`system_limitation`，因此缺少该记录时应作为流水线输入契约错误返回给编排器。

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
| `E2` 细胞 | `C3` 因果* | `C4` 转化潜力 | C3 仅限被操纵的细胞体系；C4 必须明确为待动物/人体验证的候选 |
| `E3` 类器官 | `C3` 因果 | `C4` 转化潜力 | 因果限于该模型体系 |
| `E4` 动物 | `C3` 因果 | `C4` 转化潜力 | **因果必须限定物种**；不得直陈 C5 临床疗效 |
| `E5` 人体观察 | `C1` 关联 | `C1` 关联** | 观察性因果推断走 §5.3 专门路径，不由“用了温和措辞”自动升级 |
| `E6` 非随机对照干预 | `C3` 因果 | `C5` 临床疗效 | C5 仅限有并行对照、明确时间零点与混杂控制的目标人群 |
| `E6` 单臂干预 | `C0` 描述 | `C4` 转化潜力 | 可直陈观察到的缓解率/变化，不得把自然病程或回归均值当疗效 |
| `E7` RCT | `C5` 临床疗效 | `C5` 临床疗效 | 疗效必须限定试验人群、干预/对照、终点与随访时长；单个 RCT 不自动支持推荐 |
| `E8` 证据合成 | `C5` 临床疗效 | `C6` 临床推荐*** | 普通 meta-analysis 不得直陈推荐；C6 还需证据确定性、获益-伤害与适用性评估 |

\* `E2 → C3` 必须同时具备干预、匹配对照、直接终点，以及 rescue 或第二种正交干预；
只有表达相关、单一药物处理或单一 siRNA 时仍限 `C1/C2`。

\** 孟德尔随机化、自然实验、目标试验模拟等不套用单一三项清单；按 §5.3 核对
该设计自己的识别假设，假设无法从稿件确认时交人工，不自动定 `critical`。

\*** `E8 → C6` 只有在系统综述同时报告证据确定性、绝对获益与伤害、适用人群，
且推荐措辞与这些结果一致时成立；否则最高为 `C5`。

> `diagnostic_accuracy` 脚注：不得把诊断主张硬塞进“关联→疗效”轴。
> 「在本研究受试者谱和参照标准下，敏感度/特异度为 X」按 `C0`；
> 外部队列复现后主张可泛化的诊断性能按 `C4`；证明使用该检测改善患者结局按 `C5`；
> 推荐用于筛查按 `C6`，还必须有目标筛查人群中的获益-伤害证据。

### 3.4 层级差与 severity

```
Δ = claim_tier − 该证据层级允许的上限
    （assertive 模式用 max_assertive_tier，hedged 模式用 max_hedged_tier）

Δ ≤ 0          → 不构成 finding
Δ = 1          → major
Δ ≥ 2          → major；仅满足下述 critical 条件时升级
```

**critical 条件**（满足任一）：

1. `E0–E4` 证据被用于直陈 `C5/C6`，且该句是摘要或正文的主要结论；
2. claim 的全部直接支撑经 §6 的同锚点核对后均被证明不能用于该推断，且 claim 仍被直陈为主要结论。

**修正项**（先算 Δ，再依次应用）：

| 条件 | 修正 |
| --- | --- |
| `scope_qualified = false`，且 claim 确实删除了支撑证据中的细胞系/物种/人群/剂量/时间窗/终点限定 | Δ 加 1，最多加一次 |
| claim 位于 Abstract 结论句 | 不改 Δ；`manual_review.priority` 提升一级，最高 `P0` |
| claim 位于未来方向段且 `hedged` | 不改 Δ；`hedged` 已在上限中计入，禁止重复减分 |
| 存在同锚点上游 finding | 不直接改 Δ；按 §6 逐条判断该 finding 是否使直接支撑失效 |

`scope_qualified = true` 只表示没有额外的范围越界，**不得**把机制、因果、疗效或推荐层级
自动降低一级。位置影响传播风险和人工复核优先级，不改变主张在科学上是否成立。

---

## 4. 措辞强度判定（hedging）

### 4.1 限定动词白名单（判为 `hedged`）

只有限定词在依存关系上修饰 **claim 的核心谓词** 时才判 `hedged`；字符串命中本身不够：

```
英文：may / might / could / suggest(s) / indicate(s) that ... may /
      appear(s) to / seem(s) to / potential / potentially / possible /
      warrants further study / merits investigation /
      these findings raise the possibility / preliminary evidence
中文：可能 / 提示 / 或可 / 有望 / 潜在 / 似乎 / 值得进一步研究 /
      初步提示
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

1. **按限定词的作用域判，不按词表优先级判。**
   「These results demonstrate that X may improve outcomes」对“改善结局”判 `hedged`；
   「These results demonstrate a 30% reduction」判 `assertive`。`did not demonstrate`、
   `failed to establish` 中的否定必须与动词一起解析，不得命中 `demonstrate/establish` 后判直陈。
2. **限定词修饰的必须是主张本身，不是次要成分。**
   「X significantly reduced tumor volume, which may involve apoptosis」——
   主张「X 降低瘤体积」是 `assertive`（`may` 只修饰机制猜测）。
   拆成两条 claim 分别判定。
3. **`is associated with` 是 `C1` 的直陈，不是 hedging。**
   「X is associated with Y」判 `C1 + assertive`；「X may be associated with Y」才判
   `C1 + hedged`。若宾语本身含因果谓词（「associated with causing Y」），把因果子句另拆一条 claim。

---

## 5. 规则库

每条规则给出：触发条件、severity、**证据要求**（M7 必须独立给出的稿件证据）。

### 5.1 `claim_beyond_evidence` · 外推超出实验条件

- **触发**：§3.4 的 Δ > 0，或 claim 把支撑证据明确限定的细胞系/物种/人群/
  剂量/时间窗/终点扩成更宽范围；且不属于 §5.3 / §5.4 的专门情形。
- **severity**：按 §3.4；仅有范围扩张而层级未越界时为 `major`。
- **证据要求**：至少两条 `present` ——
  ①该 claim 的原文（`evidence_refs` 取自 `claims[].evidence_refs`）；
  ②确立证据层级的方法学原文（如「HepG2 cells were treated…」）。
  **只给结论原文不够** —— 必须让复核者看到「这篇论文实际做的是什么层级的实验」。
- **detail 必须写明**：实测证据层级、主张层级、允许上限、Δ 与修正项。

典型越界（保留敏怡原表并给出层级映射）：

| 越界模式 | 层级表达 |
| --- | --- |
| 细胞实验 → 直接主张临床疗效 | E2 → C5，Δ=2 且命中 critical 条件 1 → critical |
| 单一物种/品系 → 主张人类或普适机制 | 层级可未越界，但范围轴扩张 → major |
| 单中心小样本 → 主张人群层面推荐 | E5/E6 → C6，Δ≥1 → major 起 |
| 特定剂量/时间窗 → 主张任意条件下有效 | `scope_qualified = false` 且范围确实扩大 → Δ 加 1 |
| 相关性研究 → 主张因果 | 见 §5.3 `causal_overreach` |

### 5.2 `unsupported_claim` · 主张无数据支撑

- **触发**（满足任一）：
  1. `claims[].supported_by` 为空数组，且按 `00-contracts.md §1.2` 完成目标章节与图表范围检索后
     仍找不到任何直接支撑；
  2. 存在指向该 `claim_id` 的 `claim_without_resolved_evidence_link` signal，且 M7 复核
     `supported_by` 中每一项后确认全部无法解析；
  3. `supported_by` 指向 `conflicting` 组，且**每个**候选 observation 都与 claim 的方向不相容；
  4. 支撑数值与主张方向相反。
- **不触发**：`ambiguous` / `parse_failed` 表示抽取或能力限制，不是“稿件无证据”；
  M7 应跳过该 claim 的自动判定并要求人工读取原文。`conflicting` 组只要存在一个候选值
  可支持 claim，也不得自动立本条。
- **severity**：默认 `major`；claim 是摘要或正文主要结论，且全部直接支撑均不存在或方向相反时为 `critical`。
- **证据要求**：claim 原文 + 检索支撑的 `absence` 证据（情形 1、2），
  或指向该 `key_data` 全部观测的 `present` 证据（情形 3、4）。
- **注意**：情形 2 **不得**仅引用 signal id 结案 —— 必须自行确认
  `supported_by` 中每一项确实无法解析，并把检索过程写成 `absence` 证据。

数值量级与措辞不符（如“亚微摩尔级”对应 15 μM）使用
`claim_magnitude_mismatch` (`major`)，不得升级成 `unsupported_claim` (`critical`)。

### 5.3 `causal_overreach` · 相关性表述为因果

- **触发**：`evidence_tier = E5`（人体观察性）且 `claim_tier ≥ C3`，并且下列
  A/B 两条路径均不成立：
  - **A · 常规纵向观察路径**：暴露先于结局；预先定义混杂因素并作适当控制；
    报告至少一项针对未测量混杂/反向因果的敏感性分析；claim 明确限定目标人群、
    暴露、对照、结局与时间窗。剂量-反应只作增强证据，不是必填替代项。
  - **B · 专门因果设计路径**：稿件明确使用孟德尔随机化、自然实验、工具变量、
    断点回归、差分中的差分或目标试验模拟，并逐项报告该设计的识别假设与敏感性分析。
- **severity**：横断面或病例对照资料直陈因果且无专门因果设计 → `critical`；
  纵向研究或专门因果设计缺关键识别假设、敏感性分析或范围限定 → `major`。
- **证据要求**：claim 原文 + 设计描述原文 + 缺失项的 `absence` 证据。
- **不触发的情形**：claim 只陈述 `associated with` / `predicts`，不含干预反事实含义；
  或 B 路径完整且 M4 未指出识别假设/分析失效。仅“自陈局限”或使用 `may` 不足以豁免。

### 5.4 `negative_result_misread` · 不显著误读为无差异

- **触发**：主分析未达到优效性显著阈值，而 claim 把结果写成「无差异 / 无影响 /
  无获益 / 相似 / 相当 / 不劣于 / 未显示优于 / does not affect / no benefit /
  similar / comparable / not inferior / not superior」，且未满足下列任一：
  1. 预先设定等效界，双侧置信区间完整落入等效界；
  2. 预先设定非劣效界，采用与设计一致的分析集和置信区间，且区间未跨越该界；
  3. claim 明确写成“未发现支持差异/获益的证据”，并同时报告效应估计与置信区间，
     没有把证据不足改写为效果为零。
- **severity**：`major`。
- **证据要求**：claim 原文 + 该比较的统计结果原文 + 效能/等效界的 `absence` 证据。
- **常见形态**：`p = 0.21` → 「两组无显著差异，说明 X 不影响 Y」。
  **不显著只说明没有证据支持有差异，不等于有证据支持无差异。**

事后效能或“样本量依据”不能证明等效，禁止把它们当作不触发条件。

### 5.5 `significance_overstated` · 夸大统计显著性

- **触发**（满足任一）：
  1. 仅凭 `p` 值使用「强效 / 大幅改善 / substantial / large effect」等**效应量**措辞，
     但未报告对应效应估计与置信区间；“统计学显著”本身不触发；
  2. 对存在公认 MCID 的连续量表或患者报告结局，claim 直陈**临床重要改善**，
     但未把效应估计/置信区间与预设 MCID 对照；死亡、住院等硬终点不得机械要求 MCID，
     应核对绝对风险差、置信区间及获益-伤害；
  3. M4 已报出同一分析的 `no_multiple_comparison_correction`，claim 却把探索性亚组/
     次要终点写成确证性“显著”结果。
- **severity**：`major`。
- **证据要求**：claim 原文 + `p` 值、效应估计与区间所在位置的 `present` 证据
  （或效应估计/MCID 的合规 `absence` 证据）；情形 3 还须引用 M4 finding 的稿件锚点证据。

### 5.6 `limitations_evasive` · 回避核心局限

- **触发**：M2–M6 中存在下表列出的、与推断边界直接相关且 `severity ≥ major` 的 finding，
  而 `conclusion.limitations` 满足任一：
  1. `status = not_reported`；
  2. `status = reported`，但文本未按下表同时承认**问题域**与它对精度、归因或
     假阳性风险的影响。

| 上游 category | 问题域（至少命中一项） | 影响（至少命中一项） |
| --- | --- | --- |
| M4 `sample_size` | 样本量 / sample size / underpowered | 精度或 CI / 检出能力 / 不确定性 / 可推广性 |
| M3 `missing_control` | 对照 / comparator / placebo / control | 无法归因 / 替代解释 / 因果受限 |
| M4 `no_multiple_comparison_correction` | 多重比较 / 亚组 / exploratory / multiplicity | 假阳性 / 偶然发现 / 需独立验证 |

只出现关键词不算覆盖：「样本量足够」含“样本量”但否认问题；「使用多个对照」含“对照”
但未承认缺失。否定范围必须解析。作者若说明缓解措施，还必须陈述措施后的剩余限制。
未在表中的 category（如统计检验错误、图文矛盾、伦理声明缺失）是应修正的错误或合规问题，
不是靠 Limitations 披露即可解决的研究边界，**不得**触发本条。
- **severity**：全部未覆盖 → `major`；部分覆盖 → `minor`。
- **证据要求**：`limitations` 原文；若判未覆盖，还须给出以表中问题域词与影响词为
  `search_terms[]` 的 `absence` 证据；另引用被回避 finding 的稿件锚点证据。
- **注意**：这是 M7 唯一一条**以其他模块 finding 为触发条件**的规则，
  但证据仍须独立给出 —— 不得只写「M4 报了问题而作者没提」。

### 5.7 `selective_result_interpretation` · 选择性解读自身结果

- **触发**：Discussion 用一个方向概括论文结果，但同一预设终点或同一总体中的
  结果存在方向相反、明确不相容的 observation，且 Discussion 未披露该异质性。
  探索性亚组与主要总体方向不同，只能提示人工，不自动触发。
- **severity**：`major`。
- **证据要求**：Discussion 原文 + 被回避的自身结果的 `present` 证据。
- **当前不做**：判断作者是否漏引外部反证文献 —— 那需要文献库，归 §11.1；
  因此不得使用 `selective_citation` 这个会暗示外部检索已完成的 slug。

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
| M4 `wrong_test` (critical) | 同一分析是 claim 的全部直接支撑，且 M4 明确说明估计/检验不可解释 | `unsupported_claim`；主要结论可为 critical，否则 major |
| M4 `sample_size` (major) | claim 引用该分析 | 不自动判 unsupported；只进入 §5.6 的局限披露核对 |
| M4 `no_multiple_comparison_correction` | claim 引用了同一未校正的探索性亚组/次要终点 | 触发 §5.5 情形 3 |
| M3 `missing_control` | 同一实验是 `C3+` claim 的全部直接支撑 | `claim_beyond_evidence`；默认 major，禁止机械给 Δ 加分 |
| M3 `animal_use_unjustified` | —— | 不影响 M7（属伦理与设计，不直接改变数据方向） |
| M5 `figure_text_contradiction` | claim 引用该图，且矛盾涉及 claim 所用方向/数值 | 无其他支撑时判 `unsupported_claim`；默认 major，主要结论且方向相反时 critical |
| M5 `chart_type_mismatch` | claim 引用该图 | 不自动改变 M7；只有该问题使数值无法唯一读取时才把新 M7 finding 的 `review_confidence` 上限设为 medium |
| M5 `figure_should_be_main_text` | claim 引用该 supplement 图 | 不改 severity，在 detail 中提示核心证据位置不当 |
| M2 `internal_inconsistency` | claim 引用了冲突数值 | 按 §5.2 情形 3 检查全部候选值；禁止见冲突即判 unsupported |
| M6 任何 finding | —— | 不影响 M7（伦理合规不改变结论是否成立） |
| **（未实现）** M5 `duplicate_region_within_paper` / `splice_artifact_suspected` | claim 引用该图 | 只生成编辑人工复核候选；取证未经人工确认前不得自动生成 M7 critical finding |

**实现约束**：只有同时满足四项才联动：①上游 finding 与 claim 指向同一 `figure+panel`、
`table` 或 `paragraph_id`；②该锚点是 `supported_by` 的直接支撑，不只是同段背景；
③上游 finding 的 `review_confidence ∈ {high, medium}`；④检查 claim 的其他
`supported_by` 后确认没有独立直接支撑。任一项不满足就不联动。M7 finding 必须重新引用
稿件证据并写明推理，不得把上游 severity 复制过来。

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
| `unsupported_claim` | 主张无数据支撑 | major / critical | §5.2 |
| `claim_beyond_evidence` | 外推超出实验条件 | major / critical（按 Δ） | §5.1 |
| `causal_overreach` | 相关性表述为因果 | major / critical | §5.3 |
| `negative_result_misread` | 不显著误读为无差异 | major | §5.4 |
| `significance_overstated` | 夸大统计显著性 | major | §5.5 |
| `limitations_evasive` | 回避核心局限 | major / minor | §5.6 |
| `selective_result_interpretation` | 选择性解读论文自身结果 | major | §5.7 |
| `discussion_hollow` | 讨论仅复述结果 | minor | §5.8 |
| `claim_magnitude_mismatch` | 主张的量级与自身数据不符 | major | §5.2 |

**外部增强新增**（完成 schema 迁移前不得使用）：`claim_contradicted_by_literature`、
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
risk of preeclampsia」→ 是 `C1 + assertive`，没有因果反事实含义 → **不报**。

### 9.3 `negative_result_misread`

**该报警**：`p = 0.31`，n=8/组，无效能分析，结论写
「X 对肿瘤生长无影响」→ **major**。

**不该报警**：预设等效界 (−10%, 10%)，实测差值 95% CI 为 (−3.2%, 4.1%)，
按预设分析集完成等效性检验，结论写「X 在预设等效界内与 Y 等效」→ **不报**。

### 9.4 `significance_overstated`

**该报警**：`p=0.04`，只报告 p 值，摘要写「X produced a large clinically meaningful
improvement」→ 未给效应量/CI，且把显著性当效应大小 → **major**。

**不该报警**：摘要写「X reduced mean score by 6.2 points (95% CI 3.1–9.3), exceeding
the prespecified 5-point MCID」→ 效应大小、精度与 MCID 均可核对 → **不报**。

### 9.5 `unsupported_claim`

**该报警**：主要结论宣称 X 降低死亡率，但 `supported_by=[]`；全文以
{mortality, death, survival, X} 检索正文、表格与图注均无结果 → 有合规 absence 证据，**critical**。

**不该报警**：唯一 key_data 组为 `parse_failed`，对应低分辨率 supplement；这是系统能力限制，
不是稿件无支撑 → 跳过自动判断并交人工，**不报 M7 finding**。

### 9.6 `limitations_evasive`

**该报警**：M4 报出 `sample_size` (major)，`limitations` 只写
「本研究为单中心研究」，未提样本量或效能 → **major**。

**不该报警**：同样情形，`limitations` 写「样本量偏小，效能不足以检出小效应，
结果需在更大队列中验证」→ 命中关键词集 → **不报**。

### 9.7 `selective_result_interpretation`

**该报警**：预设主要终点在两个时间点方向相反，Discussion 只概括有利时间点并写
「all analyses consistently favored X」→ 自身结果并不一致 → **major**。

**不该报警**：一个事后探索亚组方向相反，Discussion 将其标为 exploratory 并要求独立验证
→ 已披露异质性，且未把总体结果写成“所有亚组一致” → **不报**。

### 9.8 `discussion_hollow`

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
- [x] §5.6 只纳入可由 Limitations 合理披露的三类问题，并定义“问题域 + 影响”双条件
- [x] §6 已按 M3/M4/M5 当前 reference 核对 category slug；未登记 slug 不得用于联动
- [ ] 为 §4.1/§4.2 的中英措辞表补充实际语料中出现过的变体

---

## 11. 一期联网增强（当前未实现，规则先写下）

三项能力都归本模块。**现在只写判据，不写实现**；数据源统一走外部证据层，
本节只声明「需要什么数据」，不要自行实现调用方式。

### 11.1 结论科学真伪核验

- 数据源：PubMed / Europe PMC
- 判据草案：抽出每条 claim 的核心断言 → 检索同主题既往研究 → 分类为
  `consistent` / `contradicted` / `novel_unreplicated` / `insufficient_evidence`
- 输出 category：`claim_contradicted_by_literature`(critical) / `claim_unreplicated`(info)
- **风险**：检索召回不全会造成「查无反证 = 结论正确」的假阴性。实现时必须要求
  `review_confidence: low` 起步，且此类 finding 一律强制人工复核。

### 11.2 领域创新性 / 重要性

- 数据源：文献库 + 引用网络
- 前置：**先定义可量化的新颖度判据**，否则会退化成主观打分。候选方向：
  claim 与既有文献的语义距离、方法组合是否首次出现、研究对象是否为空白领域
- 输出定位：不给「创新性高/低」的结论，只给「该主张在检索范围内未见同类报道」
  这类**事实性描述**，由人工判断价值 —— 联网增强也不得越过这条边界。

### 11.3 基础常识校验

- 数据源：领域常识规则库（需自建）
- 建库方式：**先积累当前人工复核环节的误判样本**，把真实出现过的常识性错误沉淀成规则，
  而不是先验地枚举常识。人工复核记录是后续规则的训练材料。
- 输出 category：`violates_domain_common_sense`(critical)

### 11.4 外部证据的契约扩展

引入外部证据时，**扩展而非重构**现有契约（`SKILL.md §0.2`）：
在 `evidence_registry` 中新增第三种证据型 `external`，至少保存 `database`、`record_id`、
`query`、`retrieval_date`、`version`、`retraction_or_correction_status`、
`relation_to_claim` 与外部验证阶段的 `created_by`。当前 schema 尚无 `external` 分支，
因此本节不提供一个无法通过现有 schema 的 JSON 示例。M7 不得自行创建 external evidence；
唯一产出者必须在共享契约中先登记。

**规则**：引入 `external` 证据的 finding，其 `evidence_refs[]` 中**必须同时**
含至少一条 `present` 型稿件内证据 —— 论文内定位不可省略。
`00-contracts.md §1.2` 的两型表届时扩为三型，`evidence.schema.json` 增加对应分支。
