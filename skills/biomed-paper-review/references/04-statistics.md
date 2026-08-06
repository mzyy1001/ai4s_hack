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
| **`test_statistic_p_mismatch`** | `skills/biomed-paper-review/scripts/statistical_forensics.py` | 是否构成 p 值报告错误 |
| **`ci_estimate_mismatch`** | 同上 | 是否构成区间报告错误 |
| **`count_percentage_mismatch`** | 同上 | 是否构成数据报告错误 |
| **`grim_incompatible_mean`** | 同上 | 是否构成汇总统计不可能 |
| **`table_total_mismatch`** | 同上 | 互斥穷尽分类的合计是否与声明分母矛盾 |

> **加粗的五种是一期已实现的确定性取证**
>（`skills/biomed-paper-review/scripts/statistical_forensics.py`），
> 不需要原始数据，只用论文自己印出来的数字。它们**已从二期提前到一期**
> —— 本文件旧版把它们列在「§5 二期扩展」，现已更正。
> 工具层只产 signal，**M4 决定是否构成 finding 以及 severity**。

### 2.1 统计取证 signal 的消费门

五种取证 signal 不能按 type 直接翻译为 finding。M4 必须逐条执行：

1. 确认 `produced_by = stage_2`、`forensics.ran = true`，并复算 `forensics` 中的输入与区间；
2. 用稿件证据确认所有输入属于**同一终点、同一比较、同一分析集和同一时间点**；无法绑定时不立 finding，产 `partial_extraction`；
3. `test_statistic_p_mismatch` 还须确认检验族、自由度和单/双尾；`count_percentage_mismatch`
   还须确认分母口径与 count 语义（受试者数、事件数或样本数）；
4. `grim_incompatible_mean` 还须确认原文报告的是等权整数得分的未调整算术均值，且 n 是该均值的实际分母；
5. `table_total_mismatch` 还须确认各分类互斥且穷尽、属于同一分析集/时间点，缺失值已单列或纳入合计；多选题、重叠事件类别和允许一人多事件的安全性表不得运行；
6. signal 的 `evidence_refs[]` 为空不构成违规；M4 立 finding 时必须另行加入报告这些数字的稿件内
   `present` evidence。`forensics.ran = false` 的 `partial_extraction` 只表示工具前提不足，
   **不得自动转成统计报告缺陷**。

---

## 3. 三步判定法（本模块核心）

### 3.1 第一步 · 归纳数据特征

先把每个 `statistical_methods[]` 项绑定到一个具体终点/比较，再从
`structured_result_v2` 抽出六个特征。只要求当前对照表行实际使用的特征：例如二分类结局
不要求 `distribution_evidence`，未做协变量调整的随机两组比较不要求抽出混杂变量。
**任一当前行必需特征无法确定时，见 §3.4。**

| 特征 | 取值 | 来源 |
| --- | --- | --- |
| `outcome_type` | `continuous` / `binary` / `count` / `ordinal` / `time_to_event` / `proportion` / `high_dimensional` | `key_data[].metric_family` + 终点描述 |
| `n_groups` | `1` / `2` / `>=3` | `design.arms[]` 或 `group_sizes[]` |
| `relatedness` | `independent` / `paired_or_repeated` / `clustered` | 设计描述（前后测、交叉、同一动物多细胞） |
| `design_shape` | `parallel` / `crossover` / `factorial` / `longitudinal` / `dose_response` | `article_design` + `arms[]` |
| `distribution_evidence` | `approximately_normal_supported` / `nonnormal_supported` / `not_assessed` | 模型残差图、Q-Q 图、离群与偏态描述；正式正态性检验只能作为其中一项证据，不能用原始结局不正态替代残差诊断 |
| `covariate_adjustment` | `yes` / `no` | 是否声明校正混杂 |

**终点绑定顺序**：先用 `statistical_methods[].applied_to` 精确匹配终点、时间点与比较；再用同段
或同表的 evidence locator 消歧。仍有两个以上候选时不得按距离最近或名称相似强配，输出
`ambiguous_extraction`。方法节只写“连续变量用 t 检验、分类变量用 χ²”而没有逐终点映射时，
只有所有适用终点共享同一设计与相关结构才可继续；否则为 `undetermined`。

### 3.2 第二步 · 查应选检验（§4 对照表）

由 `(outcome_type, n_groups, relatedness, design_shape)` 查出：

- **`primary`** —— 该情形下与目标 estimand 相容的代表性首选，不表示唯一正确方法
- **`acceptable[]`** —— 同样站得住的替代方案（**不构成 finding**）
- **`conditional[]`** —— 需满足前提才成立，前提未报告则触发 `assumption_unchecked`
- **`misuse[]`** —— 已知的典型误用

### 3.3 第三步 · 判定合理性等级

| 等级 | 条件 | 输出 |
| --- | --- | --- |
| `match` | 实际检验 ∈ `{primary} ∪ acceptable` | **无 finding** |
| `conditionally_acceptable` | 实际检验 ∈ `conditional`，且前提已报告 | **无 finding** |
| `assumption_unstated` | 实际检验 ∈ `conditional`，关键前提未评估，且 §3.4 的风险门成立 | `assumption_unchecked`（默认 minor；满足 §9 升级条件才 major） |
| `mismatch` | 实际检验 ∈ `misuse`，或与 `outcome_type` 根本不兼容 | `wrong_test`（默认 major；满足 §9 升级条件才 critical） |
| `undetermined` | 当前对照表行的必需特征无法确定 | **不立 finding**，出 `partial_extraction` |

**`mismatch` 的两条硬性前提**（缺一即降级为 `undetermined`）：

1. `outcome_type`、`n_groups` 及该误用判定实际依赖的 `relatedness` / `design_shape`
   必须是 `reported`（非 `ambiguous`/`parse_failed`）；
2. 实际所用检验的名称必须能唯一解析（「statistical analysis was performed using SPSS」
   这类表述**不足以**判定用了什么检验）。

### 3.4 防误报：什么时候不判

**统计方法的「正确」往往不唯一。** 下列情形一律 `undetermined`，交人工：

- 方法节只写软件不写检验名；
- 论文使用本表未收录的方法，或给出的理由涉及可识别但本表未编码的 estimand、抽样机制、
  稳健方差/惩罚估计；**仅写“参照既往研究”或“数据不正态”不构成自动免责**；
- 数据特征依赖图表读数，而读数来源为 `pixel_estimated`
  （`00-contracts.md §2.4`：像素估读**不得**用于任何统计判定）;
- 同一实验存在多个终点、各自适用不同检验，而抽取无法对应到具体终点。

**未报告正式正态性检验本身不构成 finding。** Shapiro-Wilk 等检验的 `p > 0.05`
只是“未拒绝正态性”，不能证明分布正态；小样本时检验效能尤其有限。只有同时满足以下条件，
才输出 `assumption_unchecked`：①所用方法对该前提敏感；②样本量小或明显不均衡，且原始点、
残差图或文字描述提示强偏态/离群；③未见变换、稳健/置换敏感性分析或残差诊断。

---

## 4. 数据类型 × 设计 → 应选检验对照表

### 4.1 连续型结局

| 情形 | primary | acceptable | conditional（前提） | 典型误用 |
| --- | --- | --- | --- | --- |
| 两组独立、近似正态 | Welch t | 置换检验、线性模型、bootstrap CI | Student t（前提：等方差有设计或诊断依据） | 用配对 t；把同一受试者/实验单位的重复观测当独立 |
| 两组配对/前后 | 配对 t | Wilcoxon 符号秩、配对置换、混合效应模型 | —— | **用独立样本 t**（丢失配对信息） |
| 两组、强偏态/离群或极小样本 | 与 estimand 匹配的置换/稳健方法 | 变换后 Welch t、bootstrap CI | Mann-Whitney（只有分布形状相近时才可解释为位置差异） | 未说明目标是均值、位置还是分布差异便把方法名机械互换；明显离群且无稳健性分析 |
| ≥3 组独立 | Welch ANOVA + Games-Howell，或与设计相符的线性模型 | 经典 ANOVA + Tukey/Dunnett、置换 ANOVA、稳健 ANOVA | 经典 ANOVA（前提：残差与方差结构足够相容） | **两两 t 检验不校正**；只报总体检验却下具体组间结论 |
| ≥3 组、强偏态/离群 | 置换或稳健的总体检验 + 校正后对比 | Kruskal-Wallis + Dunn、合适变换后的线性模型 | Kruskal-Wallis（各组分布形状不同时不能自动解释为中位数差） | 强偏态且小样本时套经典 ANOVA，又无残差诊断或稳健性分析 |
| ≥3 组配对/重复测量 | 线性混合效应模型 / GEE | Friedman + 校正后比较、重复测量 ANOVA | RM-ANOVA（前提：>2 个组内水平时评估球形性或使用 Greenhouse-Geisser/Huynh-Feldt 校正） | **当作独立样本**；逐时点两两比较不校正 |
| 两因素析因 | 含主效应与交互项的线性/广义线性模型 | two-way ANOVA、混合效应模型、稳健/置换的析因检验 | —— | 需要比较效应差异却不检验交互；拆成多个未校正的单因素检验 |
| 纵向多时点 | 线性混合效应模型 / GEE | 均衡完整数据的 RM-ANOVA、按预设时间点的校正后对比 | RM-ANOVA（前提：完整性与协方差/球形性条件相容） | 把同一对象各时点当独立；仅用 LOCF 后逐时点检验且无缺失机制敏感性分析 |
| 随机试验含基线测量 | ANCOVA（随访值为结局、基线值为协变量） | 含基线的混合模型、预设的变化值分析 | 变化值（随机化且目标确为平均变化；通常效率低于 ANCOVA） | 百分比变化未处理基线接近 0；以组内前后显著/不显著代替组间治疗效应 |
| 观察性研究含基线/混杂 | 与目标 estimand 相符的调整回归或加权模型 | 分层、匹配、标准化 | —— | 仅比较原始变化值便宣称独立处理效应 |
| 剂量-反应：估计 IC50/EC50/斜率 | 与反应形状相符的非线性回归 + 拟合诊断 | Emax、趋势模型、约束样条/其他预设曲线 | 四参数 logistic（前提：上下平台与单调 S 形有数据支持） | 用组间 ANOVA 的显著性代替曲线参数估计；外推超出实测剂量范围 |
| 剂量-反应：只问任一剂量是否不同于对照 | ANOVA/线性模型 + Dunnett 对比 | 趋势检验、置换检验 | —— | **不得仅因使用 ANOVA 就判错**；只有稿件同时声称 IC50/斜率而未拟合曲线才构成误用候选 |

### 4.2 二分类 / 比例结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 两组独立 | χ² 或 Fisher 精确检验 | N−1 χ²、精确/Monte Carlo 方法、二项回归 | χ²（2×2 通常要求各格期望频数 ≥5；更大表要求无格 <1 且 <5 的格不超过 20%） | 稀疏表仍用渐近 χ² 且无精确/Monte Carlo 核查 |
| 两组配对 | McNemar 检验 | 精确 McNemar | —— | **用 χ²**（忽略配对） |
| ≥3 个配对条件 | Cochran Q + 校正后配对比较 | 二项 GEE、广义线性混合模型 | —— | 当作独立 r×c 表 |
| ≥3 个独立组 | r×c χ² + 校正后对比 | Fisher-Freeman-Halton/Monte Carlo 精确检验、二项/多项回归 | χ²（前提：稀疏度满足上行规则） | 多次 2×2 χ² 不校正 |
| 需校正混杂 | logistic 回归（报 OR + 95% CI） | 分层 Mantel-Haenszel、惩罚 logistic、标准化/加权模型 | 最大似然 logistic（前提：事件数、参数数、分离和非线性已评估） | 只做单因素比较即宣称独立效应；变量筛选后仍按未筛选模型解释 p 值 |
| 聚类/重复二分类 | 二项 GEE 或广义线性混合模型 | cluster-robust 方差、按独立实验单位汇总 | —— | 把同一对象/动物/中心内观测当独立 |
| 有序暴露的趋势 | Cochran-Armitage 趋势检验 | 有序 logistic | —— | 把有序暴露当无序分类 |

### 4.3 计数型结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 计数、无过离散 | Poisson 回归 | 精确 Poisson 检验 | Poisson（前提：过离散已检查） | **未检查过离散**；直接对计数做 t 检验 |
| 计数、过离散 | 负二项回归 | 准 Poisson | —— | 坚持 Poisson 导致 SE 被低估、p 值虚小 |
| 零膨胀 | 零膨胀 Poisson/负二项 | 障碍模型 | —— | 忽略零膨胀 |
| 有暴露时间/人时 | 带 offset 的 Poisson（发生率） | —— | —— | 比较原始计数而不除以人时 |
| 聚类/重复计数 | Poisson/负二项混合模型或 GEE | cluster-robust 方差、条件模型 | —— | 把同一对象内多次计数当独立；漏掉 exposure offset |

### 4.4 有序型结局（如 Likert、分级评分）

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 两组 | Mann-Whitney U | 有序 logistic | 参数化处理（前提：作者论证了等距性） | 直接当连续量做 t 并报均值±SD（**争议做法，判 minor 不判 critical**） |
| ≥3 组 | Kruskal-Wallis | 有序 logistic（比例优势） | —— | 同上 |
| 配对/重复有序结局 | 累积链接混合模型 / ordinal GEE | 两时点 Wilcoxon 符号秩、≥3 时点 Friedman | —— | 当作独立组；忽略同一对象内相关 |
| 需校正 | 比例优势模型 | —— | 比例优势（前提：比例优势假定已检验） | 未检验比例优势假定 |

### 4.5 生存 / 时间-事件结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 单因素组间比较 | Kaplan-Meier + log-rank | Gehan-Wilcoxon（早期差异敏感） | —— | **用 t 检验比较中位生存**；**用 χ² 比较事件数**（都忽略删失） |
| 多因素 | Cox 比例风险模型（报 HR + 95% CI） | 参数生存模型、加速失效时间模型、时变效应模型 | Cox（前提：**比例风险假定已检验**，如 Schoenfeld 残差） | 未检验 PH 假定；风险交叉时仍用恒定 HR 概括且无时变/分层处理 |
| 有竞争风险 | 累积发生函数 + Gray 检验，或与 estimand 相符的 Fine-Gray / 原因别 Cox | 多状态模型 | Fine-Gray（解释亚分布 HR）；原因别 Cox（解释瞬时原因别 hazard） | 用普通 KM 估计某原因的累积发生率；把两种 HR 当成同一 estimand |
| 区间删失 | 区间删失生存模型 | Turnbull 非参数估计、离散时间模型 | —— | 用区间中点当精确事件时间且不做敏感性分析 |
| 复发事件 | Andersen-Gill / PWP / frailty 等与问题相符的模型 | GEE 计数模型、多状态模型 | —— | 只分析首次事件却下“总复发负担”结论；把同一对象的事件当独立 |
| 报告要求 | —— | —— | —— | KM 曲线**未附风险人数表**；未报随访时长 |

### 4.6 相关与一致性（高频误用区）

| 情形 | primary | acceptable | 典型误用 |
| --- | --- | --- | --- |
| 线性相关、双变量正态 | Pearson r（报 r、95% CI、n） | —— | 对有序或强偏态数据用 Pearson |
| 单调相关 / 有序 / 非正态 | Spearman ρ | Kendall τ | —— |
| **两种测量方法的一致性** | **Bland-Altman 分析**（偏倚 + 95% 一致性界限） | Lin 一致性相关系数、ICC | **用 Pearson r 证明「一致」**（经典错误：r 高只说明线性相关，不说明一致） |
| 分类评价者间一致性 | Cohen's κ（两评价者）/ Fleiss κ（多评价者） | 加权 κ（有序） | 用「符合率」代替 κ（未扣除偶然一致） |
| 连续评价者间一致性 | ICC（须写明 ICC 型号：单次/平均、一致性/绝对一致） | —— | 只写「ICC=0.9」不写型号 |
| 同一对象重复测量间相关 | 重复测量相关或混合效应模型 | GEE、对象内/对象间效应分解 | 把全部点合并做 Pearson/Spearman，忽略对象内聚类 |

### 4.7 诊断准确性

| 项目 | 要求 | 典型误用 |
| --- | --- | --- |
| 基本指标 | 敏感度、特异度**均附 95% CI**；给出 2×2 表 | 只报一个指标；无 CI |
| 汇总指标 | ROC 曲线 + AUC（附 CI） | 报 AUC 无 CI |
| 两个模型比较 | 配对 ROC 可用 DeLong 或配对 bootstrap；敏感度/特异度差异用配对二分类方法 | 分别报 AUC 却不检验差值；把同一受试者的两个模型当独立 |
| 最佳截断值 | 开发集内选择后须用 bootstrap/交叉验证校正乐观度；确认性主张须外部验证 | **在同一数据上选截断并把表观性能当验证性能** |
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
> 同一独立分配的实验单位内多个细胞、切片、视野或技术孔被当作独立 n，即高度可疑。
> `arms[].replicate_type = technical` 只能触发候选；还必须从稿件证据确认干预分配层级、
> 推断目标和实际进入模型的 n。offspring、病灶等可能是生物学亚样本而非 technical replicate，
> 同样可能构成聚类；仅靠 `replicate_type` 二值标签不能排除。实验单位无法确定时输出
> `partial_extraction`，不得立 `pseudoreplication`。

---

## 5. 样本量

### 5.1 判定口径（会议纪要已定）

样本量属「无明确统一标准的模糊场景」。本模块的输出一律是
**「样本量/精度依据无法核验，建议人工确认」**，而**不是**「样本量不足，结论无效」。
`severity` 上限为 `major`，且 `manual_review.who = statistical_reviewer`。

### 5.2 分研究类型的复核入口

**不存在可跨效应量、方差、终点、模型复杂度和研究目的使用的统一 n 下限。** 旧版
`in_vivo_animal ≥5–6`、`diagnostic_accuracy 各 ≥30–50` 和 `EPV ≥10` 均不得作为
finding 判据；它们会误伤合理的小样本探索研究，也可能放过效应小、变异大或参数多的研究。
按下表决定是否进入人工复核：

| 研究类型 | 进入复核的可执行条件 | 不得据此下的结论 |
| --- | --- | --- |
| `in_vitro` | 独立实验单位少于 3，或只见技术孔/同批次亚样本，且稿件作可推广的推断性结论 | 不得把“3 次”自动当充分；也不得把 n=2 的探索/方法开发自动判无效 |
| `in_vivo_animal` | 未报告样本量确定依据；或独立实验单位、预期效应、变异、α/power/精度目标任一无法核验 | 不得使用“每组 5–6”作为充分或不足的分界 |
| `randomized_controlled_trial` | 确证性试验未给主要 estimand 对应的效能/精度依据，或实际入组/事件数明显低于计划且无处理说明 | pilot/feasibility 试验按可行性目标与 progression criteria 审，不要求为疗效检验配置效能 |
| `cohort` / `case_control` | 事件数、候选参数自由度、非线性项/交互、分离、缺失与 shrinkage 无法核验 | `EPV <10` 只能提示风险；`EPV ≥10` 也不能证明模型不过拟合 |
| `diagnostic_accuracy` | 未按预期敏感度/特异度、患病率与目标 CI 宽度确定病例/非病例数，或关键亚组 CI 过宽 | 不得用每组 30–50 代替精度计算；小型 pilot 可用于参数预估 |
| 组学 | 独立生物学重复、离散度/方差估计、检验 family 与 FDR 控制无法核验，或模型参数数接近/超过独立单位数 | 不得把“每组 ≥3/≥5”当充分条件 |
| `case_report` / 描述性 `case_series` | 不适用 | **不得**对不作群体推断的病例报告提样本量 finding |

低于历史惯例但同时满足以下三项时，不立 `sample_size`：研究明确标为探索性/可行性；
主要目标不是确证疗效或精确估计；报告了与该目标对应的不确定性、停止/进展规则或样本量理由。
若稿件借“pilot”标签作确证性疗效结论，问题应落在结论越界或目标错配，而不是仅凭 n 小。

### 5.3 必查项

- 是否有效能分析或样本量依据？（`sample_size_justification`）
- 按 `group_sizes[]` **逐实验逐组**检查，**不要**压成一个全局最小值。
- n 是生物学重复还是技术重复？`replicate_type = technical` 而当作 n 使用 → §4.9。
- 临床试验：计划入组 vs 实际入组、失访率、是否 ITT/PP 分析并说明差异。
- 样本量方法的输入是否完整？确证性优效试验至少核对预期效应量、α、power、分配比与
  失访；精度导向研究核对目标 CI 宽度；pilot/feasibility 核对可行性目标与 progression
  criteria。只写「power=0.8」而无效应量/方差 → `sample_size`（minor），因为无法核验。

---

## 6. 分领域报告规范索引

立 finding 时在 `rule_ref` 中引用对应规范，让作者知道依据。

| 研究类型 | 规范 | 本模块最关心的条目 |
| --- | --- | --- |
| 随机对照试验 | **CONSORT 2010**（及后续更新）；**ICH E9** 统计学原则；**ICH E9(R1)** estimand 框架 | 流程图、随机化方法、样本量依据、主要终点分析、ITT |
| 观察性研究 | **STROBE** | 混杂控制、缺失数据、敏感性分析 |
| 动物实验 | **ARRIVE 2.0** | Essential 10 的样本量、随机化、盲法、统计方法 |
| 诊断准确性 | **STARD 2015** | 2×2 表、CI、截断值来源、盲法判读 |
| 预测模型 | **TRIPOD**（2015）/ **TRIPOD+AI**（2024） | 内部/外部验证、校准度、事件数与参数复杂度 |
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
| `wrong_test` | 检验方法与数据类型/设计根本不匹配 | major / critical | §3.3 `mismatch`；按下述算法升级 |
| `pseudoreplication` | 独立实验单位内的重复测量/亚样本被当作独立 n | major / critical | §4.9；按下述算法升级 |
| `assumption_unchecked` | 有风险证据时仍未评估关键模型前提 | minor / major | §3.3–§3.4；按下述算法升级 |
| `no_multiple_comparison_correction` | 多重比较未校正 | major | §8 |
| `sample_size` | 样本量/精度依据缺失或与确证性目标不相容 | minor / major | §5 |
| `agreement_by_correlation` | 用相关系数证明测量一致性 | major | §4.6 |
| `censoring_ignored` | 生存数据忽略删失 | critical | §4.5 |
| `cutoff_not_validated` | 数据内选择截断后未校正乐观度，或把开发性能当确认性验证 | major | §4.7 |
| `one_sided_unjustified` | 单尾检验无事先说明 | major | §7 |
| `error_bar_ambiguous` | 误差类型未标注或图文不一致 | minor | §7 |
| `p_value_incomplete` | 仅 `p<0.05`，无精确值/统计量 | minor | §7 |
| `no_effect_size` | 未报告效应量 | minor | §7 |
| `missing_data_unhandled` | 缺失数据处理未说明 | minor | §7 |
| `over_precision` | 报告位数超出测量精度 | info | §7 |
| `selective_reporting` | 疑似选择性报告 / 终点更换 | critical | 与 M2 联动 |
| **`p_value_inconsistent`** | p 与统计量/自由度对不上 | major；满足下述升级条件才为 critical | 由 `test_statistic_p_mismatch` signal 判定 |
| **`ci_self_inconsistent`** | 点估计与自身 CI 不自洽 | major | 由 `ci_estimate_mismatch` signal 判定 |
| **`percentage_mismatch`** | 百分比与分子分母算不出来 | minor；改变关键分母或主要效应量时为 major | 由 `count_percentage_mismatch` signal 判定 |
| **`grim_violation`** | 均值在给定 n 下数学上不可能 | major；人工排除口径差异后才可升级 critical | 由 `grim_incompatible_mean` signal 判定 |
| **`table_total_mismatch`** | 互斥穷尽分类合计与声明分母不一致 | minor；影响主要终点、受试者流或安全性分母时为 major | 由同名 signal 判定 |

> 加粗五项由 §2 的一期取证 signal 触发。**据 signal 立 finding 时，
> 必须在 `evidence_refs[]` 中独立给出稿件证据**（报告该数值的原文位置），
> 不得仅引用 signal id（`00-contracts.md §6.1` 规则 5）。

**五类取证 finding 的 severity 算法**：

1. `p_value_inconsistent` 默认 `major`。仅当它属于预设主要终点、反算 p 与报告 p 位于
   预设 α 的两侧，且正文结论明确依赖“显著 / 不显著”分类时，才标 `critical`。
2. `ci_self_inconsistent` 固定为 `major`；当前工具只能证明内部不自洽，不能确定点估计还是
   CI 哪一个抄错，因此不得自动升级 `critical`。
3. `percentage_mismatch` 默认 `minor`。只有舍入区间不相交，且更正后会改变主要终点的事件
   分母、效应量或受试者流判断时，才标 `major`；不得自动标 `critical`。
4. `grim_violation` 默认 `major`。只有人工回查确认它是主要结果、原文确为等权整数原始均值、
   n 与报告精度均无抄录歧义，且该结果是核心结论的必要支撑时，才标 `critical`。
5. `table_total_mismatch` 默认 `minor`。只有分类互斥且穷尽的前提有稿件证据，且差异改变主要终点、
   CONSORT 受试者流或安全性分析分母时，才标 `major`；不得自动标 `critical`。

**检验选择与模型前提的 severity 算法**：

1. `wrong_test` 默认 `major`。只有错误分析直接作用于预设主要终点，且会改变效应方向、
   显著性分类或有效分析单位（如忽略删失、把亚样本当独立 n），才标 `critical`。
   将配对数据按独立样本分析通常损失效率，不能仅凭方法名称自动判 `critical`。
2. `assumption_unchecked` 默认 `minor`。只有满足 §3.4 三项风险门，且该模型支撑主要结论时，
   才标 `major`；不得因未报告 Shapiro-Wilk 检验单独立项。
3. `pseudoreplication` 默认 `major`。只有稿件证据明确给出独立分配层级，确认分析把同一实验
   单位内亚样本计作独立 n，且该分析支撑主要结论或重算会改变显著性分类时，才标
   `critical`。仅有 `replicate_type = technical` 或层级描述不清时不得立 finding。

---

## 10. 正例 / 反例

### 10.1 `wrong_test`

**该报警**：同一批小鼠给药前后各测一次血糖（配对设计，`relatedness = paired`），
方法节写「independent samples t-test」→ `mismatch` → 默认 **major**；只有重算证明其改变
主要结论方向或显著性分类时才升 `critical`。

**不该报警**：两组独立小鼠比较，作者用 Welch t 而非 Student t，并说明方差不齐
→ Welch 在 `acceptable` 集内 → **不报**。

### 10.2 `pseudoreplication`

**该报警**：6 只小鼠，每只取 10 个视野计数，统计写 `n = 60`，
稿件明确处理分配在小鼠层级却把 60 个视野作为独立样本 → `pseudoreplication`；若它支撑
主要结论并改变显著性分类则 **critical**，否则默认 **major**。

**不该报警**：6 只小鼠，每只取 10 个视野，**先按动物求均值**再比较，`n = 6`
→ 正确做法 → **不报**。
`replicate_type = unspecified` 时也**不报**，改出 `partial_extraction`。

### 10.3 `assumption_unchecked`

**该报警**：4 个极小且不均衡组使用经典 one-way ANOVA；原始点显示强偏态与离群，
全文未见残差诊断、变换、Welch/稳健分析或置换敏感性分析 → 满足 §3.4 风险门 → **major**。

**不该报警**：同样 4 组，未报告正式正态性检验，但残差 Q-Q 图无明显偏离，组间方差相近，
并用 Welch ANOVA 或置换分析得到一致结论 → 有充分诊断与稳健性证据 → **不报**。

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

**该报警（但措辞克制）**：确证性小鼠肿瘤实验每组 n = 3，未给样本量依据、预期效应、
变异或不确定性区间，却据单次显著性检验下强效治疗结论
→ `sample_size`（major），detail 写「独立实验单位很少，且未见与主要终点对应的样本量/
精度依据，**建议人工确认**估计稳定性与结论范围」；不得引用 5–6 的固定下限。

**不该报警**：方法开发型 `in_vitro` pilot 使用 2 个独立批次，明确目标是估计流程变异并
报告全部原始点与宽区间，未作确证性生物学结论 → 不以固定 n 下限立 finding；可在报告中
保留探索性范围说明。

### 10.7 `table_total_mismatch`

**该报警**：同一分析集的 Table 1 明确把受试者分为互斥且穷尽的轻/中/重三类，计数为
12、18、9，表头声明 `n = 42`，且无缺失类别 → 合计 39 与分母 42 矛盾 → 默认 **minor**；
若该分母用于主要终点或安全性发生率则为 **major**。

**不该报警**：不良事件表按事件类型列数，同一受试者可出现多个事件 → 类别不互斥，
即使各行合计超过受试者总数也**不运行**，只在语义无法确认时产 `partial_extraction`。

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

## 12. 后续增强（当前未实现，规则先写下）

当前已实现「不依赖原始数据」的取证（§2）。本节能力不再按网络或 12 小时超时划为二期；
原始数据或外部记录可取得时可纳入一期可选增强，取不到时按契约降级。

### 12.1 依赖原始数据的复算

- 前置：论文提供原始数据（`data_availability` 为 `reported` 且数据可取）
- 范围：按论文声明的方法重跑主要分析，比对统计量与 p 值
- 输出 category：`recomputation_mismatch`（critical）
- **风险**：软件版本、默认参数、缺失值处理差异都会造成数值不一致而非真实错误。
  实现时必须区分「数值有出入」（minor）与「结论方向不同」（critical）。

### 12.2 从图表反推数据后复算

与 M5 联动：从 `figure_records[].observations[]` 拿到读数再做一致性检验。
**硬性约束**：`source_type = pixel_estimated` 的数值**不得**用于复算
（`00-contracts.md §2.4`）。只有 `explicit_figure_caption` / `axis_readable`
来源的数值可以进入。

### 12.3 SPRITE / GRIMMER 扩展

GRIMMER（针对 SD）与 SPRITE（重构可能的原始分布）比 GRIM 的假设更多、
可行解更多。实现时**只输出候选并强制人工复核**，不得直接下稿件判断。

### 12.4 需要外部数据的检查

| 检查 | 数据源 | 归属 |
| --- | --- | --- |
| 注册终点与论文主要终点是否漂移 | ClinicalTrials.gov / ChiCTR | M4 + M6 |
| 效应量是否与既往荟萃分析量级相符 | Europe PMC | M4 + M7 |
| 报告的统计软件版本是否存在已知缺陷 | 软件发布记录 | M4 |
