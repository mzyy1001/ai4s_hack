# M4 · 统计学方法校验

**负责人：JY（蒋运）** · 状态：**一期规则库已填充**

对应会议纪要「第三层：统计学方法校验」。核心问题不是「算得对不对」，而是
**这个实验设计本该用什么检验，作者用的那个是否说得通**。

**本模块的判定分三步（§3）**：先由数据特征推出**应选检验**，
再与**实际所用检验**比对，最后判定**合理性等级**。
只有明确不匹配才立 `wrong_test`；数据特征抽取不足时**不立 finding**，
产出 `partial_extraction` 交人工 —— 这是本模块最重要的防误报机制。

**本文件依赖 `00-contracts.md`。** finding 结构、`evidence_refs[]`、severity 枚举
的定义都在那里。M4 的 finding **必须**在 `evidence_refs[]` 中独立给出稿件证据。

---

## 1. 输入

| 来源 | 用途 |
| --- | --- |
| `structured_result_v2.measurement.statistical_methods` | **实际所用检验**（每项 `{test, applied_to, software, correction}`） |
| `structured_result_v2.article_design` | 设计族与类型，决定分领域规范（§6） |
| `structured_result_v2.design.arms[]` | 组数、配对关系、`replicate_type` |
| `structured_result_v2.key_data[]` | n、`uncertainty`、p 值、`metric_family`、`reporting_completeness` |
| `evaluation_matrix.group_sizes[]` | 逐实验逐组样本量（**不是**单一最小值） |
| `evaluation_matrix.multiple_comparison_correction` | 多重比较校正状态 |
| `figure_records[]` | 图中误差棒类型、显著性标记、坐标轴 |
| 路由到 M4 的 `extraction_signals[]` | 见 §2 |

**消费 `v2` 而非 `v1`** —— `v1` 不含图表来源数值。
`evaluation_matrix` 仅用于路由与定位证据，立 finding 前必须回查 `evidence_refs`。

## 2. 本模块消费的 signal

| signal type | 来源 | M4 要判定什么 |
| --- | --- | --- |
| `source_value_conflict` | Stage 3b | 数值矛盾是否影响统计结论 |
| `partial_extraction` | Stage 2 | 报告是否不完整（如有 n 无重复类型） |
| `ambiguous_extraction` | Stage 2 | 统计方法表述是否含糊到无法判定 |
| **`test_statistic_p_mismatch`** | `tools/statistical_forensics.py` | 是否构成 p 值报告错误 |
| **`ci_estimate_mismatch`** | 同上 | 是否构成区间报告错误 |
| **`count_percentage_mismatch`** | 同上 | 是否构成数据报告错误 |
| **`grim_incompatible_mean`** | 同上 | 是否构成汇总统计不可能 |

> **加粗的四种是一期已实现的确定性取证**（`tools/statistical_forensics.py`），
> 不需要原始数据，只用论文自己印出来的数字。它们**已从二期提前到一期**
> —— 本文件旧版把它们列在「§5 二期扩展」，现已更正。
> 工具层只产 signal，**M4 决定是否构成 finding 以及 severity**。

---

## 3. 三步判定法（本模块核心）

### 3.1 第一步 · 归纳数据特征

从 `structured_result_v2` 抽出六个特征。**任一特征无法确定时，见 §3.4。**

| 特征 | 取值 | 来源 |
| --- | --- | --- |
| `outcome_type` | `continuous` / `binary` / `count` / `ordinal` / `time_to_event` / `proportion` / `high_dimensional` | `key_data[].metric_family` + 终点描述 |
| `n_groups` | `1` / `2` / `>=3` | `design.arms[]` 或 `group_sizes[]` |
| `relatedness` | `independent` / `paired_or_repeated` / `clustered` | 设计描述（前后测、交叉、同一动物多细胞） |
| `design_shape` | `parallel` / `crossover` / `factorial` / `longitudinal` / `dose_response` | `article_design` + `arms[]` |
| `distribution_evidence` | `normal_reported` / `nonnormal_reported` / `not_reported` | 方法节是否报告正态性检验 |
| `covariate_adjustment` | `yes` / `no` | 是否声明校正混杂 |

### 3.2 第二步 · 查应选检验（§4 对照表）

由 `(outcome_type, n_groups, relatedness, design_shape)` 查出：

- **`primary`** —— 该情形下的首选/经典检验
- **`acceptable[]`** —— 同样站得住的替代方案（**不构成 finding**）
- **`conditional[]`** —— 需满足前提才成立，前提未报告则触发 `assumption_unchecked`
- **`misuse[]`** —— 已知的典型误用

### 3.3 第三步 · 判定合理性等级

| 等级 | 条件 | 输出 |
| --- | --- | --- |
| `match` | 实际检验 ∈ `{primary} ∪ acceptable` | **无 finding** |
| `conditionally_acceptable` | 实际检验 ∈ `conditional`，且前提已报告 | **无 finding** |
| `assumption_unstated` | 实际检验 ∈ `conditional`，但前提**未报告** | `assumption_unchecked`（major） |
| `mismatch` | 实际检验 ∈ `misuse`，或与 `outcome_type` 根本不兼容 | `wrong_test`（critical） |
| `undetermined` | §3.1 任一特征无法确定 | **不立 finding**，出 `partial_extraction` |

**`mismatch` 的两条硬性前提**（缺一即降级为 `undetermined`）：

1. `outcome_type` 与 `n_groups` 都必须是 `reported`（非 `ambiguous`/`parse_failed`）；
2. 实际所用检验的名称必须能唯一解析（「statistical analysis was performed using SPSS」
   这类表述**不足以**判定用了什么检验）。

### 3.4 防误报：什么时候不判

**统计方法的「正确」往往不唯一。** 下列情形一律 `undetermined`，交人工：

- 方法节只写软件不写检验名；
- 用了本表未收录的检验（贝叶斯方法、稳健估计、机器学习模型等）；
- 论文明确给出了选择该检验的理由，即使不是首选；
- 数据特征依赖图表读数，而读数来源为 `pixel_estimated`
  （`00-contracts.md §2.4`：像素估读**不得**用于任何统计判定）;
- 同一实验存在多个终点、各自适用不同检验，而抽取无法对应到具体终点。

---

## 4. 数据类型 × 设计 → 应选检验对照表

### 4.1 连续型结局

| 情形 | primary | acceptable | conditional（前提） | 典型误用 |
| --- | --- | --- | --- | --- |
| 两组独立、正态 | 独立样本 t 检验（**Welch 校正为默认更稳妥**） | Welch t、置换检验、Mann-Whitney（更保守） | Student t（前提：方差齐性已检验并报告） | 用配对 t；对同一数据做多次两两 t |
| 两组配对/前后 | 配对 t 检验 | Wilcoxon 符号秩、混合效应模型 | —— | **用独立样本 t**（丢失配对信息，最常见） |
| 两组、非正态或极小样本 | Mann-Whitney U | 置换检验、变换后 t、Welch t | —— | 直接用 t 且未报告正态性 |
| ≥3 组独立、正态 | one-way ANOVA + 事后多重比较（Tukey/Dunnett） | Welch ANOVA + Games-Howell、线性模型 | ANOVA（前提：正态性 + 方差齐性已检验） | **两两 t 检验不校正**；只报总体 ANOVA 的 p 却下组间结论 |
| ≥3 组独立、非正态 | Kruskal-Wallis + Dunn 事后 | 置换 ANOVA | —— | 强行 ANOVA 且未验前提 |
| ≥3 组配对/重复测量 | 重复测量 ANOVA 或线性混合效应模型 | Friedman + Nemenyi | RM-ANOVA（前提：球形性检验或 Greenhouse-Geisser 校正） | **当作独立样本**；逐时点两两比较不校正 |
| 两因素析因 | two-way ANOVA（含交互项） | 线性模型含交互 | —— | **拆成多个 one-way**（丢失交互，且放大 I 类错误） |
| 纵向多时点 | 线性混合效应模型 / GEE | RM-ANOVA（均衡且无缺失时） | —— | 逐时点独立 t 检验；用末次观测代替全轨迹 |
| 有基线协变量 | ANCOVA（以基线为协变量） | 混合模型含基线 | —— | 比较「变化值」而不校正基线（回归到均值偏倚） |
| 剂量-反应 | 非线性回归（四参数 logistic）+ 拟合优度 | Emax 模型、趋势检验 | —— | **用 ANOVA 比较各剂量组**而不拟合曲线；外推超出实测剂量范围 |

### 4.2 二分类 / 比例结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 两组独立 | χ² 检验（**期望频数均 ≥5**） | Fisher 精确检验、N−1 χ² | χ²（前提：期望频数已核查） | **期望频数 <5 仍用 χ²**（应改 Fisher） |
| 两组配对 | McNemar 检验 | 精确 McNemar | —— | **用 χ²**（忽略配对） |
| ≥3 组 | r×c χ² + 事后两两比较并校正 | —— | —— | 多次 2×2 χ² 不校正 |
| 需校正混杂 | logistic 回归（报 OR + 95% CI） | 分层 Mantel-Haenszel | logistic（前提：EPV ≥10，见 §5.3） | 只做单因素比较即宣称独立效应 |
| 有序暴露的趋势 | Cochran-Armitage 趋势检验 | 有序 logistic | —— | 把有序暴露当无序分类 |

### 4.3 计数型结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 计数、无过离散 | Poisson 回归 | 精确 Poisson 检验 | Poisson（前提：过离散已检查） | **未检查过离散**；直接对计数做 t 检验 |
| 计数、过离散 | 负二项回归 | 准 Poisson | —— | 坚持 Poisson 导致 SE 被低估、p 值虚小 |
| 零膨胀 | 零膨胀 Poisson/负二项 | 障碍模型 | —— | 忽略零膨胀 |
| 有暴露时间/人时 | 带 offset 的 Poisson（发生率） | —— | —— | 比较原始计数而不除以人时 |

### 4.4 有序型结局（如 Likert、分级评分）

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 两组 | Mann-Whitney U | 有序 logistic | 参数化处理（前提：作者论证了等距性） | 直接当连续量做 t 并报均值±SD（**争议做法，判 minor 不判 critical**） |
| ≥3 组 | Kruskal-Wallis | 有序 logistic（比例优势） | —— | 同上 |
| 需校正 | 比例优势模型 | —— | 比例优势（前提：比例优势假定已检验） | 未检验比例优势假定 |

### 4.5 生存 / 时间-事件结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 单因素组间比较 | Kaplan-Meier + log-rank | Gehan-Wilcoxon（早期差异敏感） | —— | **用 t 检验比较中位生存**；**用 χ² 比较事件数**（都忽略删失） |
| 多因素 | Cox 比例风险模型（报 HR + 95% CI） | 参数生存模型、Fine-Gray（竞争风险） | Cox（前提：**比例风险假定已检验**，如 Schoenfeld 残差） | 未检验 PH 假定；风险交叉时仍用 Cox |
| 有竞争风险 | 竞争风险模型（Fine-Gray / 累积发生函数） | —— | —— | 把竞争事件当删失，高估累积发生率 |
| 报告要求 | —— | —— | —— | KM 曲线**未附风险人数表**；未报随访时长 |

### 4.6 相关与一致性（高频误用区）

| 情形 | primary | acceptable | 典型误用 |
| --- | --- | --- | --- |
| 线性相关、双变量正态 | Pearson r（报 r、95% CI、n） | —— | 对有序或强偏态数据用 Pearson |
| 单调相关 / 有序 / 非正态 | Spearman ρ | Kendall τ | —— |
| **两种测量方法的一致性** | **Bland-Altman 分析**（偏倚 + 95% 一致性界限） | Lin 一致性相关系数、ICC | **用 Pearson r 证明「一致」**（经典错误：r 高只说明线性相关，不说明一致） |
| 分类评价者间一致性 | Cohen's κ（两评价者）/ Fleiss κ（多评价者） | 加权 κ（有序） | 用「符合率」代替 κ（未扣除偶然一致） |
| 连续评价者间一致性 | ICC（须写明 ICC 型号：单次/平均、一致性/绝对一致） | —— | 只写「ICC=0.9」不写型号 |

### 4.7 诊断准确性

| 项目 | 要求 | 典型误用 |
| --- | --- | --- |
| 基本指标 | 敏感度、特异度**均附 95% CI**；给出 2×2 表 | 只报一个指标；无 CI |
| 汇总指标 | ROC 曲线 + AUC（附 CI） | 报 AUC 无 CI |
| 两个模型比较 | DeLong 检验（配对 ROC） | 分别报 AUC 却不做统计比较 |
| 最佳截断值 | 须在**独立数据集**上验证 | **在同一数据上选截断并报告性能**（过度乐观） |
| 预测值 | PPV/NPV 须说明所依患病率 | 在低患病率人群直接套用研究样本的 PPV |

### 4.8 高维 / 组学

| 项目 | 要求 | 典型误用 |
| --- | --- | --- |
| 多重检验 | **必须**报告校正后 p（FDR-BH 的 q 值或 adjusted p） | **只报原始 p**；只用 fold-change 筛选不做统计检验 |
| 差异分析 | 用领域标准工具（limma / DESeq2 / edgeR）并写明版本 | 对计数数据直接做 t 检验 |
| 批次效应 | 说明是否检查并校正 | 完全不提批次 |
| 富集分析 | 说明背景基因集与校正方法 | 用全基因组作背景却不校正 |
| 特征筛选与建模 | 筛选须在**训练集内**完成 | **在全数据上筛特征再交叉验证**（信息泄露，归 M2 联动） |

### 4.9 聚类数据与伪重复（生物医药高发）

| 情形 | primary | 典型误用 |
| --- | --- | --- |
| 同一动物取多个细胞/切片/视野 | 混合效应模型（动物为随机效应）或先按动物汇总 | **把细胞数当 n**（伪重复，人为放大样本量、p 值虚小） |
| 同一受试者多个病灶/牙位/眼 | 广义估计方程 GEE 或混合模型 | 把病灶数当独立样本 |
| 整群随机试验 | 考虑设计效应的分析 | 按个体分析，忽略群内相关 |
| 多批次重复实验 | 批次为随机效应 | 合并所有批次当独立重复 |

> **伪重复是本模块最值得抓的问题之一**：它不需要复杂判断，只要
> `arms[].replicate_type = technical` 却被当作统计学 n 使用，即高度可疑。
> 但 `replicate_type = unspecified` 时**不得**推定为技术重复，应出 `partial_extraction`。

---

## 5. 样本量

### 5.1 判定口径（会议纪要已定）

样本量属「无明确统一标准的模糊场景」。本模块的输出一律是
**「低于领域惯例，建议人工确认」**，而**不是**「样本量不足，结论无效」。
`severity` 上限为 `major`，且 `manual_review.who = statistical_reviewer`。

### 5.2 分研究类型的经验下限

**这些是提示阈值，不是判定阈值。** 低于阈值只触发人工复核建议。

| 研究类型 | 经验下限 | 说明 |
| --- | --- | --- |
| `in_vitro` | ≥3 个**独立生物学重复** | 技术重复不计入；n=3 是下限不是标准 |
| `in_vivo_animal` | 连续终点每组 ≥5–6 | 应有效能分析；ARRIVE 2.0 要求说明样本量确定依据 |
| `randomized_controlled_trial` | **必须**有效能分析 | 无效能分析本身即为缺陷，与实际 n 无关 |
| `cohort` / `case_control` | 每个自变量 ≥10 个事件（EPV） | 用于 logistic/Cox；EPV <10 时估计不稳 |
| `diagnostic_accuracy` | 病例组与对照组各 ≥30–50 | 低于此值敏感度/特异度 CI 极宽 |
| 组学 | 每组 ≥3，建议 ≥5 | n=3 时 FDR 检验效能极低 |
| `case_report` / `case_series` | 不适用 | **不得**对病例报告提样本量要求 |

### 5.3 必查项

- 是否有效能分析或样本量依据？（`sample_size_justification`）
- 按 `group_sizes[]` **逐实验逐组**检查，**不要**压成一个全局最小值。
- n 是生物学重复还是技术重复？`replicate_type = technical` 而当作 n 使用 → §4.9。
- 临床试验：计划入组 vs 实际入组、失访率、是否 ITT/PP 分析并说明差异。
- 效能分析的参数（预期效应量、α、power）是否给出？只写「power=0.8」而无预期效应量
  → `sample_size`（minor），因为无法核验。

---

## 6. 分领域报告规范索引

立 finding 时在 `rule_ref` 中引用对应规范，让作者知道依据。

| 研究类型 | 规范 | 本模块最关心的条目 |
| --- | --- | --- |
| 随机对照试验 | **CONSORT 2010**（及后续更新）；**ICH E9** 统计学原则；**ICH E9(R1)** estimand 框架 | 流程图、随机化方法、样本量依据、主要终点分析、ITT |
| 观察性研究 | **STROBE** | 混杂控制、缺失数据、敏感性分析 |
| 动物实验 | **ARRIVE 2.0** | Essential 10 的样本量、随机化、盲法、统计方法 |
| 诊断准确性 | **STARD 2015** | 2×2 表、CI、截断值来源、盲法判读 |
| 预测模型 | **TRIPOD**（2015）/ **TRIPOD+AI**（2024） | 内部/外部验证、校准度、EPV |
| 系统评价与荟萃分析 | **PRISMA 2020** | 异质性度量（I²）、效应模型选择、发表偏倚 |
| qPCR | **MIQE** | 内参基因选择与验证、扩增效率 |
| 高通量组学 | **MIAME / MINSEQE** | 数据可及性、标准化方法 |
| 病例报告 | **CARE** | —— |
| 临床 AI/ML | **CONSORT-AI / SPIRIT-AI / DECIDE-AI** | 数据划分、外部验证、性能指标 |

---

## 7. 报告完整性检查

| 项目 | 要求 | 触发 slug |
| --- | --- | --- |
| p 值 | 报精确值（如 `p = 0.032`），而非只写 `p < 0.05`；`p < 0.001` 可接受 | `p_value_incomplete`（minor） |
| 检验统计量与自由度 | 应报告（如 `t(18) = 2.31`），使 p 值可复核 | `p_value_incomplete`（minor） |
| 误差类型 | SD / SEM / 95% CI 必须明确标注；**图中用 SEM 而正文称 SD 是常见错误** | `error_bar_ambiguous`（minor；图文矛盾时升 major） |
| 效应量 | 组间比较应报效应量（Cohen's d、均差 + CI、OR/RR/HR + CI） | `no_effect_size`（minor） |
| 缺失数据 | 说明缺失比例与处理方法（完整病例 / 多重填补 / LOCF） | `missing_data_unhandled`（minor） |
| 检验方向 | 单尾检验必须事先说明理由 | `one_sided_unjustified`（major） |
| 精确度 | 报告位数应与测量精度相称 | `over_precision`（info） |

> **误差棒类型与图的联动**：`figure_records[].significance_markers` 与
> `experimental_conditions` 提供图内信息。图注写 SEM 而正文写 SD 属
> **稿件内部矛盾**，主责在 M2；M4 只在它影响统计解读时补一条 finding，
> 两者会在 Stage 5 聚簇为同一个 issue（`00-contracts.md §9.3`）。

---

## 8. 多重比较

| 检查 | 判据 |
| --- | --- |
| 同一数据集做了多少次检验？ | 由 `statistical_methods[].applied_to` 与 `key_data[]` 的比较数推算 |
| 是否校正？ | `correction` 字段；Bonferroni / Holm / Šidák / FDR-BH 均可接受 |
| 组学是否报 adjusted p / q？ | §4.8 |
| ≥3 组的事后比较是否校正？ | Tukey / Dunnett / Games-Howell 本身已含校正 |
| 是否只报显著结果？ | 与 M2 联动（选择性报告） |

**不触发的情形**：作者明确声明次要终点为**探索性分析**且不做推断性结论时，
不校正是可接受的 —— 此时应检查结论是否越界（交 M7），而不是判 M4 的 finding。

---

## 9. category slug

| slug | 说明 | severity | 规则 |
| --- | --- | --- | --- |
| `wrong_test` | 检验方法与数据类型/设计根本不匹配 | critical | §3.3 `mismatch` |
| `pseudoreplication` | 技术重复/亚样本被当作统计学 n | critical | §4.9 |
| `assumption_unchecked` | 未验证正态性/方差齐性/球形性/比例风险/过离散 | major | §3.3 `assumption_unstated` |
| `no_multiple_comparison_correction` | 多重比较未校正 | major | §8 |
| `sample_size` | 低于领域惯例或无效能分析 | major | §5 |
| `agreement_by_correlation` | 用相关系数证明测量一致性 | major | §4.6 |
| `censoring_ignored` | 生存数据忽略删失 | critical | §4.5 |
| `cutoff_not_validated` | 最佳截断值未在独立数据验证 | major | §4.7 |
| `one_sided_unjustified` | 单尾检验无事先说明 | major | §7 |
| `error_bar_ambiguous` | 误差类型未标注或图文不一致 | minor | §7 |
| `p_value_incomplete` | 仅 `p<0.05`，无精确值/统计量 | minor | §7 |
| `no_effect_size` | 未报告效应量 | minor | §7 |
| `missing_data_unhandled` | 缺失数据处理未说明 | minor | §7 |
| `over_precision` | 报告位数超出测量精度 | info | §7 |
| `selective_reporting` | 疑似选择性报告 / 终点更换 | critical | 与 M2 联动 |
| **`p_value_inconsistent`** | p 与统计量/自由度对不上 | critical | 由 `test_statistic_p_mismatch` signal 判定 |
| **`ci_self_inconsistent`** | 点估计与自身 CI 不自洽 | major | 由 `ci_estimate_mismatch` signal 判定 |
| **`percentage_mismatch`** | 百分比与分子分母算不出来 | major | 由 `count_percentage_mismatch` signal 判定 |
| **`grim_violation`** | 均值在给定 n 下数学上不可能 | critical | 由 `grim_incompatible_mean` signal 判定 |

> 加粗四项由 §2 的一期取证 signal 触发。**据 signal 立 finding 时，
> 必须在 `evidence_refs[]` 中独立给出稿件证据**（报告该数值的原文位置），
> 不得仅引用 signal id（`00-contracts.md §6.1` 规则 5）。

---

## 10. 正例 / 反例

### 10.1 `wrong_test`

**该报警**：同一批小鼠给药前后各测一次血糖（配对设计，`relatedness = paired`），
方法节写「independent samples t-test」→ `mismatch` → **critical**。

**不该报警**：两组独立小鼠比较，作者用 Welch t 而非 Student t，并说明方差不齐
→ Welch 在 `acceptable` 集内 → **不报**。

### 10.2 `pseudoreplication`

**该报警**：6 只小鼠，每只取 10 个视野计数，统计写 `n = 60`，
`arms[].replicate_type = technical` → **critical**。

**不该报警**：6 只小鼠，每只取 10 个视野，**先按动物求均值**再比较，`n = 6`
→ 正确做法 → **不报**。
`replicate_type = unspecified` 时也**不报**，改出 `partial_extraction`。

### 10.3 `assumption_unchecked`

**该报警**：4 组比较用 one-way ANOVA，方法节与结果节均未见任何正态性或方差齐性检验
→ ANOVA 在 `conditional` 集内且前提未报告 → **major**。

**不该报警**：同样 4 组，作者写「Shapiro-Wilk 检验确认正态性（均 p > 0.05），
Levene 检验确认方差齐性」→ 前提已报告 → **不报**。

### 10.4 `agreement_by_correlation`

**该报警**：比较新型血压计与水银柱血压计，结论「两法高度一致（r = 0.95，p < 0.001）」
→ 用相关证明一致性 → **major**，建议改做 Bland-Altman。

**不该报警**：同样两法，作者做了 Bland-Altman 并报偏倚与 95% 一致性界限，
另附 r 作为补充描述 → **不报**。

### 10.5 `censoring_ignored`

**该报警**：比较两组总生存，用「中位生存期 18.2 vs 14.6 个月，t 检验 p = 0.03」
→ 对时间-事件数据用 t 检验、忽略删失 → **critical**。

**不该报警**：KM + log-rank，并附风险人数表 → **不报**。

### 10.6 `sample_size`（体现口径）

**该报警（但措辞克制）**：小鼠肿瘤实验每组 n = 3，无效能分析
→ `sample_size`（major），detail 写「每组 n=3 低于 in_vivo_animal 的经验下限 5–6，
且未见样本量依据，**建议人工确认**是否足以支持所报效应」。

**不该报警**：`in_vitro` 实验 3 个独立生物学重复，明确写明为生物学重复
→ 达到该类型下限 → **不报**。

---

## 11. TODO（一期）

- [x] 填充 §4 检验选择对照表（本模块最高优先级）
- [x] 填充 §5.2 分研究类型 n 下限建议值
- [x] 填充 §6 分领域官方指南索引
- [x] 把无需原始数据的一致性检验从二期提前到一期并接入 signal（§2、§9）
- [ ] 在 `datasets/` 十篇语料上逐篇标注 §3.1 的六个特征，
      统计 `undetermined` 的比例 —— 若超过 50%，说明 M1 的
      `statistical_methods` 抽取粒度不够，需与 M1 对齐字段
- [ ] 与 M5 确认误差棒类型的抽取字段（§7 图文矛盾判定依赖它）
- [ ] 与 M2 划清「选择性报告」的边界：终点更换归 M2，只报显著结果归 M4
- [ ] 补充贝叶斯方法与稳健估计的判定规则（当前一律 `undetermined`）

---

## 12. 二期扩展（本期不实现，规则先写下）

一期已实现「不依赖原始数据」的取证（§2）。二期做需要**外部数据或原始数据**的部分。

### 12.1 依赖原始数据的复算

- 前置：论文提供原始数据（`data_availability` 为 `reported` 且数据可取）
- 范围：按论文声明的方法重跑主要分析，比对统计量与 p 值
- 输出 category：`recomputation_mismatch`（critical）
- **风险**：软件版本、默认参数、缺失值处理差异都会造成数值不一致而非真实错误。
  二期必须区分「数值有出入」（minor）与「结论方向不同」（critical）。

### 12.2 从图表反推数据后复算

与 M5 联动：从 `figure_records[].observations[]` 拿到读数再做一致性检验。
**硬性约束**：`source_type = pixel_estimated` 的数值**不得**用于复算
（`00-contracts.md §2.4`）。只有 `explicit_figure_caption` / `axis_readable`
来源的数值可以进入。

### 12.3 SPRITE / GRIMMER 扩展

GRIMMER（针对 SD）与 SPRITE（重构可能的原始分布）比 GRIM 的假设更多、
可行解更多。二期实现时**只输出候选并强制人工复核**，不得直接下稿件判断。

### 12.4 需要外部数据的检查

| 检查 | 数据源 | 归属 |
| --- | --- | --- |
| 注册终点与论文主要终点是否漂移 | ClinicalTrials.gov / ChiCTR | M4 + M6 |
| 效应量是否与既往荟萃分析量级相符 | Europe PMC | M4 + M7 |
| 报告的统计软件版本是否存在已知缺陷 | 软件发布记录 | M4 |
