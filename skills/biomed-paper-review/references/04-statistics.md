# M4 · 统计学方法校验

**负责人：JY（蒋蕴）** · 状态：**一期规则库已填充**

> 本文件的领域判断部分并入了蒋蕴手写版 `04-statistics-edited`：
> §3.5 严重度分级原则、§4.10 回归与模型诊断、§5 样本量的风险标记口径、
> §8 多重检验情形枚举、§9 slug 表与分级依据、§6 的 REMARK。
> 框架侧补充的是三步判定法、acceptable 替代集与 undetermined 防误报机制。

对应会议纪要「第三层：统计学方法校验」。核心问题不是「算得对不对」，而是
**这个实验设计本该用什么检验，作者用的那个是否说得通**。

**本模块的判定分三步（§3）**：先由数据特征推出**应选检验**，
再与**实际所用检验**比对，最后判定**合理性等级**。
只有明确不匹配才立 `statistical_test_selection`；数据特征抽取不足时**不立 finding**，
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
| **`test_statistic_p_mismatch`** | `scripts/statistical_forensics.py`（相对 Skill 根目录） | 是否构成 p 值报告错误 |
| **`ci_estimate_mismatch`** | 同上 | 是否构成区间报告错误 |
| **`count_percentage_mismatch`** | 同上 | 是否构成数据报告错误 |
| **`grim_incompatible_mean`** | 同上 | 是否构成汇总统计不可能 |
| **`table_total_mismatch`** | 同上 | 互斥穷尽分类的合计是否与声明分母矛盾 |

> **加粗的五种是一期已实现的确定性取证**
>（`scripts/statistical_forensics.py`，相对 Skill 根目录），
> 不需要原始数据，只用论文自己印出来的数字。它们**已从二期提前到一期**
> —— 本文件旧版把它们列在「§5 二期扩展」，现已更正。
> 工具层只产 signal，**M4 决定是否构成 finding 以及 severity**。

### 2.1 统计取证 signal 的消费门

五种取证 signal 不能按 type 直接翻译为 finding。M4 必须逐条执行：

1. 确认 `produced_by = stage_2`、`forensics.ran = true`，并复算 `forensics` 中的输入与区间；
   `test_statistic_p_mismatch` 的 `forensics` 必须保留 `test_family`、`statistic`、
   `tail` 以及该检验族所需的 `df` 或 `df1/df2`，缺任一项不得转 finding；
2. 用稿件证据确认所有输入属于**同一终点、同一比较、同一分析集和同一时间点**；无法绑定时不立 finding，产 `partial_extraction`；
3. `test_statistic_p_mismatch` 还须确认检验族、自由度和单/双尾；`count_percentage_mismatch`
   还须确认分母口径与 count 语义（受试者数、事件数或样本数）；
4. `grim_incompatible_mean` 还须确认原文报告的是等权整数得分的未调整算术均值，且 n 是该均值的实际分母；
5. `table_total_mismatch` 还须确认各分类互斥且穷尽、属于同一分析集/时间点，缺失值已单列或纳入合计；多选题、重叠事件类别和允许一人多事件的安全性表不得运行；
6. Stage 2 调用统计脚本时应把输入数字对应的 `observation_refs[]` / `evidence_refs[]` 一并传入；
   旧产物的 refs 为空不构成稿件违规，但 M4 必须先重新绑定并在 finding 中加入报告这些数字的稿件内
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
| `design_shape` | `parallel` / `crossover` / `factorial` / `longitudinal` / `dose_response` / `matched_observational` | `article_design` + `arms[]`；匹配病例对照须有匹配变量与 matched set 证据 |
| `distribution_evidence` | `approximately_normal_supported` / `nonnormal_supported` / `not_assessed` | 模型残差图、Q-Q 图、离群与偏态描述；正式正态性检验只能作为其中一项证据，不能用原始结局不正态替代残差诊断 |
| `covariate_adjustment` | `yes` / `no` | 是否声明校正混杂 |

**终点绑定顺序**：先用 `statistical_methods[].applied_to` 精确匹配终点、时间点与比较；再用同段
或同表的 evidence locator 消歧。仍有两个以上候选时不得按距离最近或名称相似强配，输出
`ambiguous_extraction`。方法节只写“连续变量用 t 检验、分类变量用 χ²”而没有逐终点映射时，
只有所有适用终点共享同一设计与相关结构才可继续；否则为 `undetermined`。

**检验名归一化**：先保留原文，再映射到方法 family；`unpaired t` / `independent-samples t`
映射为独立样本 t，`paired t` 不得与其合并，`mixed model` 必须继续抽取 outcome family、link、
random/cluster term，`ANOVA followed by Tukey` 必须拆成总体检验与事后对比。只写
`non-parametric test`、软件函数名或无法唯一还原 family 的缩写时为 `ambiguous_extraction`，
不得凭常见用法猜检验。表中未逐字列出但 family、estimand、相关结构与方差处理均相容的方法，
按 §3.4 交人工，不因字符串不在 `acceptable[]` 自动判 `mismatch`。

### 3.2 第二步 · 查应选检验（§4 对照表）

由 `(outcome_type, n_groups, relatedness, design_shape)` 查出：

- **`primary`** —— 该情形下与目标 estimand 相容的代表性首选，不表示唯一正确方法
- **`acceptable[]`** —— 同样站得住的替代方案（**不构成 finding**）
- **`conditional[]`** —— 需满足前提才成立，前提未报告则触发 `statistical_assumption`
- **`misuse[]`** —— 已知的典型误用

### 3.3 第三步 · 判定合理性等级

| 等级 | 条件 | 输出 |
| --- | --- | --- |
| `match` | 实际检验 ∈ `{primary} ∪ acceptable` | **无 finding** |
| `conditionally_acceptable` | 实际检验 ∈ `conditional`，且前提已报告 | **无 finding** |
| `assumption_unstated` | 实际检验 ∈ `conditional`，关键前提未评估，且 §3.4 的风险门成立 | `statistical_assumption`（默认 minor；满足 §9 升级条件才 major） |
| `mismatch` | 实际检验 ∈ `misuse`，或与 `outcome_type` 根本不兼容 | `statistical_test_selection`（默认 major；满足 §9 升级条件才 critical） |
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
才输出 `statistical_assumption`：①所用方法对该前提敏感；②样本量小或明显不均衡，且原始点、
残差图或文字描述提示强偏态/离群；③未见变换、稳健/置换敏感性分析或残差诊断。

### 3.5 严重度由「影响什么」决定，而不是由 slug 固定

同一个问题影响主要终点和只影响次要分析，严重度不同；§9 按问题家族给出分级依据。

| 等级 | 判据 | 典型情形 |
| --- | --- | --- |
| `critical` | 有证据表明错误作用于主要终点，且可能改变效应方向、显著性分类或有效分析单位 | 主要终点忽略删失、确认将亚样本计作独立 n、主要模型方向或结论分类会改变 |
| `major` | 可能降低结果可靠性，但影响尚未复算或不作用于主要终点 | 样本量依据不足、多重比较控制不足、关键统计假设有风险证据、缺失数据处理不充分 |
| `minor` | 主要影响报告透明性，不足以证明结论改变 | 效应量缺失、p 值表达不完整、误差线定义不清 |

**定级前先确认问题影响主要终点还是次要/探索性分析。** 终点归属抽取不确定时，
`severity` 上限为 `major`，并在 `manual_review.action` 写明须先确认终点归属。

---

## 4. 数据类型 × 设计 → 应选检验对照表

### 4.1 连续型结局

| 情形 | primary | acceptable | conditional（前提） | 典型误用 |
| --- | --- | --- | --- | --- |
| 单样本与固定参照值比较 | 单样本 t 或与 estimand 相符的置信区间 | 单样本置换/符号检验、Wilcoxon 符号秩 | 单样本 t（前提：差值分布与离群情况相容） | 把外部历史均值当作无误差常数却宣称完成同期组间比较 |
| 两组独立、近似正态 | Welch t | 置换检验、线性模型、bootstrap CI | Student t（前提：等方差有设计或诊断依据） | 用配对 t；把同一受试者/实验单位的重复观测当独立 |
| 两组配对/前后 | 配对 t | Wilcoxon 符号秩、配对置换、混合效应模型 | —— | **用独立样本 t**（丢失配对信息） |
| 两组、强偏态/离群或极小样本 | 与 estimand 匹配的置换/稳健方法 | 变换后 Welch t、bootstrap CI | Mann-Whitney（只有分布形状相近时才可解释为位置差异） | 未说明目标是均值、位置还是分布差异便把方法名机械互换；明显离群且无稳健性分析 |
| ≥3 组独立 | Welch ANOVA + Games-Howell，或与设计相符的线性模型 | 经典 ANOVA + Tukey/Dunnett、置换 ANOVA、稳健 ANOVA | 经典 ANOVA（前提：残差与方差结构足够相容） | **两两 t 检验不校正**；只报总体检验却下具体组间结论 |
| ≥3 组、强偏态/离群 | 置换或稳健的总体检验 + 校正后对比 | Kruskal-Wallis + Dunn、合适变换后的线性模型 | Kruskal-Wallis（各组分布形状不同时不能自动解释为中位数差） | 强偏态且小样本时套经典 ANOVA，又无残差诊断或稳健性分析 |
| ≥3 组配对/重复测量 | 线性混合效应模型 / GEE | Friedman + 校正后比较、重复测量 ANOVA | RM-ANOVA（前提：>2 个组内水平时评估球形性或使用 Greenhouse-Geisser/Huynh-Feldt 校正） | **当作独立样本**；逐时点两两比较不校正 |
| 两因素析因 | 含主效应与交互项的线性/广义线性模型 | two-way ANOVA、混合效应模型、稳健/置换的析因检验 | —— | 需要比较效应差异却不检验交互；拆成多个未校正的单因素检验 |
| 纵向多时点 | 线性混合效应模型 / GEE | 均衡完整数据的 RM-ANOVA、按预设时间点的校正后对比 | RM-ANOVA（前提：完整性与协方差/球形性条件相容） | 把同一对象各时点当独立；仅用 LOCF 后逐时点检验且无缺失机制敏感性分析 |
| 两处理两周期交叉 | 含 treatment、period、sequence 与 subject 内相关结构的线性模型 | 无可疑残留且设计简单时的受试者内差值分析、配对 t、混合效应模型 | 只分析第一周期（前提：方案预先指定或第二周期因不可逆残留而不可解释；须按平行设计报告） | 按两个独立平行组分析全部周期；先检验 carryover 再据 p 值临时决定丢弃第二周期 |
| 随机试验含基线测量 | ANCOVA（随访值为结局、基线值为协变量） | 含基线的混合模型、预设的变化值分析 | 变化值（随机化且目标确为平均变化；通常效率低于 ANCOVA） | 百分比变化未处理基线接近 0；以组内前后显著/不显著代替组间治疗效应 |
| 观察性研究含基线/混杂 | 与目标 estimand 相符的调整回归或加权模型 | 分层、匹配、标准化 | —— | 仅比较原始变化值便宣称独立处理效应 |
| 剂量-反应：估计 IC50/EC50/斜率 | 与反应形状相符的非线性回归 + 拟合诊断 | Emax、趋势模型、约束样条/其他预设曲线 | 四参数 logistic（前提：上下平台与单调 S 形有数据支持） | 用组间 ANOVA 的显著性代替曲线参数估计；外推超出实测剂量范围 |
| 剂量-反应：只问任一剂量是否不同于对照 | ANOVA/线性模型 + Dunnett 对比 | 趋势检验、置换检验 | —— | **不得仅因使用 ANOVA 就判错**；只有稿件同时声称 IC50/斜率而未拟合曲线才构成误用候选 |

> **小样本下的正态性检验本身效能不足。** `p>0.05` 不证明正态，但也不存在
> n<15 之类可自动切换参数/非参数方法的阈值。按 §3.4 的偏态、离群、组间不均衡、
> estimand 与稳健性证据共同判断；不得因“没做 Shapiro-Wilk”或“n 小”单独报警。

### 4.2 二分类 / 比例结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 单样本比例与固定值比较 | 精确二项检验或二项比例 CI | score/Wilson 方法 | 正态近似（前提：成功与失败期望数足够） | 极稀有事件仍用未校正正态近似 |
| 两组独立 | χ² 或 Fisher 精确检验 | N−1 χ²、精确/Monte Carlo 方法、二项回归 | χ²（2×2 通常要求各格期望频数 ≥5；更大表要求无格 <1 且 <5 的格不超过 20%） | 稀疏表仍用渐近 χ² 且无精确/Monte Carlo 核查 |
| 两组配对 | McNemar 检验 | 精确 McNemar | —— | **用 χ²**（忽略配对） |
| 匹配病例对照 | 条件 logistic 回归 | matched-set 条件方法；仅 1:1 且无协变量时 McNemar 可检验暴露差异 | 无条件 logistic（前提：明确纳入全部匹配因子并证明 estimand 相容） | 把 matched set 当独立样本；把频数匹配误当个体配对后机械使用 McNemar |
| 两处理交叉二分类 | 保留 sequence/period 与受试者内相关的边际或条件模型 | 简单 2×2 交叉在前提满足时的 Mainland-Gart 类方法、二项 GEE/GLMM | —— | 把各周期观测当独立 2×2 表 |
| ≥3 个配对条件 | Cochran Q + 校正后配对比较 | 二项 GEE、广义线性混合模型 | —— | 当作独立 r×c 表 |
| ≥3 个独立组 | r×c χ² + 校正后对比 | Fisher-Freeman-Halton/Monte Carlo 精确检验、二项/多项回归 | χ²（前提：稀疏度满足上行规则） | 多次 2×2 χ² 不校正 |
| 需校正混杂 | logistic 回归（报 OR + 95% CI） | 分层 Mantel-Haenszel、惩罚 logistic、标准化/加权模型 | 最大似然 logistic（前提：事件数、参数数、分离和非线性已评估） | 只做单因素比较即宣称独立效应；变量筛选后仍按未筛选模型解释 p 值 |
| 聚类/重复二分类 | 二项 GEE 或广义线性混合模型 | cluster-robust 方差、按独立实验单位汇总 | —— | 把同一对象/动物/中心内观测当独立 |
| 二分类结局对有序暴露的趋势 | Cochran-Armitage 趋势检验 | 以预设 ordinal score 入模的 binary logistic / log-binomial 回归 | —— | 数据后试多个编码只报告最显著趋势；“有序 logistic”适用于有序**结局**，不适用于本行二分类结局 |
| 每单位有分子/分母的聚合比例 | 二项回归（保留分母） | quasi-binomial、beta-binomial、分层/混合二项模型 | 把比例当连续结局（前提：分母大、远离 0/1 且方差处理与权重有依据） | 丢弃不同分母后对裸百分比做等权 t 检验；把事件比例与可多人多事件的发生率混用 |

### 4.3 计数型结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 计数、无过离散 | Poisson 回归 | 精确 Poisson 检验、离散度相容时的准似然/稳健方差 | Poisson（前提：均值—方差与暴露结构已检查） | 有明显稀疏、偏态或大量零仍直接对原始计数做 t 检验；不得仅因大计数经诊断后使用近似正态模型就自动判错 |
| 计数、过离散 | 负二项回归 | 准 Poisson | —— | 坚持 Poisson 导致 SE 被低估、p 值虚小 |
| 结构性零与抽样零混合 | 与生成机制相符的零膨胀或障碍模型 | 能解释零机制的两部分模型 | —— | 仅因“零很多”机械指定零膨胀；未证明结构性零时，普通负二项也可能合理 |
| 有暴露时间/人时 | 带 offset 的 Poisson（发生率） | —— | —— | 比较原始计数而不除以人时 |
| 聚类/重复计数 | Poisson/负二项混合模型或 GEE | cluster-robust 方差、条件模型 | —— | 把同一对象内多次计数当独立；漏掉 exposure offset |

### 4.4 有序型结局（如 Likert、分级评分）

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 单个有序题项、两组 | Mann-Whitney U | 有序 logistic | 参数化处理（前提：等级足够多、estimand 与敏感性分析有依据） | 未论证便把少等级单题当连续量；最高只作 `statistical_assumption`，不得仅凭方法名判 `statistical_test_selection` |
| 单个有序题项、≥3 组 | Kruskal-Wallis | 有序 logistic（比例优势）、校正后有序对比 | 参数化处理（前提同上） | 同上 |
| 多题合成/验证量表总分 | 与量表构造和 estimand 相符的线性、稳健或有序模型 | t/ANOVA、置换、混合模型 | 参数模型（前提：总分等级、残差与边界效应相容） | **不得因原始题项是 Likert 就自动判 t/ANOVA 错**；先确认分析对象是单题还是合成分数 |
| 配对/重复有序结局 | 累积链接混合模型 / ordinal GEE | 两时点 Wilcoxon 符号秩、≥3 时点 Friedman | —— | 当作独立组；忽略同一对象内相关 |
| 需校正 | 比例优势模型 | —— | 比例优势（前提：比例优势假定已检验） | 未检验比例优势假定 |

### 4.5 生存 / 时间-事件结局

| 情形 | primary | acceptable | conditional | 典型误用 |
| --- | --- | --- | --- | --- |
| 单因素组间比较 | Kaplan-Meier + log-rank | 预设权重的 log-rank、限制平均生存时间（RMST）差、与 estimand 相符的参数模型 | —— | **用 t 检验比较中位生存**；**用 χ² 比较事件数**（都忽略删失） |
| 多因素 | Cox 比例风险模型（报 HR + 95% CI） | 参数/灵活参数生存模型、加速失效时间模型、RMST 回归、时变效应模型 | Cox（前提：**比例风险假定已评估**，如 Schoenfeld 残差与时变效应） | 有风险交叉或明显时变效应仍用单一恒定 HR 概括且无补充 estimand；不得仅因未写某个正式 PH 检验名就报警 |
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
| 连续评价者间一致性 | 与目标相符的 ICC（须写明单次/平均、一致性/绝对一致） | 重复性/再现性标准差、变异系数、Lin CCC | 只写「ICC=0.9」不写型号；将 consistency ICC 当 absolute agreement |
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
| 多批次重复实验 | 批次随机效应、固定阻断效应，或先按独立批次汇总 | 合并所有批次内技术孔当独立重复；**不得因批次未设为随机效应就自动判错** |

> **伪重复是本模块最值得抓的问题之一**：它不需要复杂判断，只要
> 同一独立分配的实验单位内多个细胞、切片、视野或技术孔被当作独立 n，即高度可疑。
> `arms[].replicate_type = technical` 只能触发候选；还必须从稿件证据确认干预分配层级、
> 推断目标和实际进入模型的 n。offspring、病灶等可能是生物学亚样本而非 technical replicate，
> 同样可能构成聚类；仅靠 `replicate_type` 二值标签不能排除。实验单位无法确定时输出
> `partial_extraction`，不得立 `replication_independence`。

---

### 4.10 回归与模型诊断（`model_specification`）

**这是原框架版完全缺失的一类。** 前面各表管的是「选了哪个检验」，
这一节管的是「模型建得对不对」—— 回归、生存、预测模型的设定错误
可能让效应估计偏倚，但**未报告某个诊断名本身不等于模型错误**。

| 模型 | 风险证据与可接受处理 | 输出门 |
| --- | --- | --- |
| 线性回归 | 残差提示非线性/异方差/强影响点时，使用变换、样条、稳健 SE/回归或敏感性分析；只有多个高度相关预测量且解释依赖单个系数时才要求共线性评估，VIF 不是唯一方法 | 风险证据存在且无处理 → `statistical_assumption`；仅未写 VIF/正态性检验不报 |
| Logistic 回归 | 检查连续变量函数形式、稀疏/完全分离、候选参数自由度与 shrinkage；惩罚估计、预设降维可接受 | 不能用固定 EPV 阈值判错；确认分离或明显过拟合且未处理才为 `model_specification` |
| Cox 回归 | PH 风险由 Schoenfeld、log-minus-log、时变效应或曲线形态评估；不满足时可用时变系数、分层、RMST/AFT | 只有 PH 风险证据与恒定 HR 结论同时存在且无处理才报警 |
| 混合效应 / GEE | 随机/工作相关结构须与分配和重复层级相容；收敛警告、singular fit 或极少 cluster 需处理 | 结构无法抽取为 `partial_extraction`；不能因未报告软件收敛日志就立 finding |
| 预测模型 | 报告内部验证、校准与区分度，并防止筛选/调参泄漏；外部验证按研究目标要求 | 仅开发研究缺外部验证不自动判错；把开发性能当外部性能才为 `model_specification` |
| 生存模型 | 说明 time origin、删失、竞争风险与 estimand；方法须与目标相容 | 缺字段先按报告不足；明确用普通 KM 估计原因别累积发生率才立方法 finding |

**判据**：确认模型错误直接作用于主要终点，并有理由认为会改变效应方向、显著性分类或
有效分析单位时才可 `critical`；仅有风险证据但影响未复算为 `major`，单纯未报告诊断名为
minor 或不立项。模型 family/estimand/分析集绑定不清时按 §3.4 `undetermined`。

---

## 5. 样本量

### 5.1 判定口径：目标与精度，而非硬阈值

样本量属「无明确统一标准的模糊场景」。必须先分开两个问题：

1. 稿件是否在适用场景报告了**与主要目标对应的样本量/精度依据**；
2. 稿件给出的输入与计划 n 是否能复算，或实际信息量是否支持其确证性表述。

只有在全文按 `absence` 证据规则检索方法、方案/注册和补充材料后，仍未见适用依据，才可立
`power_and_sample_size`（默认 minor）。**n 小本身不立 finding**；无法提取目标、独立单位、事件数或
模型自由度时产 `partial_extraction`，不得把“无法核验”改写成“样本量不足”。只有可复算的
计划—报告矛盾，或确证性主结论明确依赖极宽且跨越临床决策界值的区间，才可升 major。
`severity` 上限为 `major`，且 `manual_review.who = statistical_reviewer`。

### 5.2 分研究类型的复核入口

**不存在可跨效应量、方差、终点、模型复杂度和研究目的使用的统一 n 下限。** 旧版
`in_vivo_animal ≥5–6`、`diagnostic_accuracy 各 ≥30–50` 和 `EPV ≥10` 均不得作为
finding 判据；它们会误伤合理的小样本探索研究，也可能放过效应小、变异大或参数多的研究。
按下表决定是否进入人工复核：

| 研究类型 | 进入复核的可执行条件 | 不得据此下的结论 |
| --- | --- | --- |
| `in_vitro` | 稿件作确证性或可推广推断，却未说明独立实验单位、重复层级与不确定性；若只见技术孔被当 n，改按 §4.9 审核 | 不得使用 n=2、n=3 等固定边界；方法开发/探索研究只按其声明目标审核 |
| `in_vivo_animal` | 对确证性主要终点全文未见样本量确定理由；作者若声称按 power 设计，才要求其效应、变异、α、power 与失访/排除输入可复算 | 不得使用“每组 5–6”作为充分或不足的分界；ARRIVE 的报告缺失不证明实验无效 |
| `randomized_controlled_trial` | 确证性试验未给主要 estimand 对应的效能/精度依据；或计划与实际入组/事件数不符且未解释对分析的影响 | pilot/feasibility 按可行性目标与 progression criteria 审，不要求为疗效检验配置效能 |
| `cohort` / `case_control` | **预测模型**未报告总样本、事件/非事件与候选参数自由度；**病因关联模型**按估计精度、稀疏/分离与预设协变量审，不套预测模型阈值 | `EPV <10` 只能触发人工检查；`EPV ≥10` 也不能证明不过拟合，不得把所有协变量都算成 1 df |
| `diagnostic_accuracy` | 确证性准确度研究未给敏感度/特异度、患病率与目标 CI 精度依据；或主要指标 CI 跨越预设临床可接受界值 | 不得用每组 30–50 代替精度计算；小型 pilot 可用于参数预估 |
| 组学 | 作确认性差异/预测主张却未说明独立生物学重复、检验 family 与 FDR 计划；参数数超过独立单位数只触发模型稳定性复核 | 不得把“每组 ≥3/≥5”当充分条件；缺离散度细节不自动等于样本量错误 |
| `case_report` / 描述性 `case_series` | 不适用 | **不得**对不作群体推断的病例报告提样本量 finding |

低于历史惯例但同时满足以下三项时，不立 `power_and_sample_size`：研究明确标为探索性/可行性；
主要目标不是确证疗效或精确估计；报告了与该目标对应的不确定性、停止/进展规则或样本量理由。
若稿件借“pilot”标签作确证性疗效结论，问题应落在结论越界或目标错配，而不是仅凭 n 小。

### 5.3 必查项

- 是否有效能分析或样本量依据？（`sample_size_justification`）
- 按 `group_sizes[]` **逐实验逐组**检查，**不要**压成一个全局最小值。
- n 是生物学重复还是技术重复？`replicate_type = technical` 而当作 n 使用 → §4.9。
- 临床试验：计划入组 vs 实际入组、失访率、是否 ITT/PP 分析并说明差异。
- **只有作者声称做过 power/precision 计算时**，才检查其输入是否完整。确证性优效试验核对预期效应量、α、power、分配比与
  失访；精度导向研究核对目标 CI 宽度；pilot/feasibility 核对可行性目标与 progression
  criteria。只写「power=0.8」而无效应量/方差 → `power_and_sample_size`（minor），因为无法核验。

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
| 肿瘤标志物研究 | **REMARK** | 标志物验证、模型建立与报告 |
| qPCR | **MIQE** | 内参基因选择与验证、扩增效率 |
| 高通量组学 | **MIAME / MINSEQE** | 数据可及性、标准化方法 |
| 病例报告 | **CARE** | —— |
| 临床 AI/ML | **CONSORT-AI / SPIRIT-AI / DECIDE-AI** | 数据划分、外部验证、性能指标 |

---

## 7. 报告完整性检查

| 项目 | 要求 | 触发 slug |
| --- | --- | --- |
| p 值 | 报精确值（如 `p = 0.032`），而非只写 `p < 0.05`；`p < 0.001` 可接受 | `p_value_reporting`（minor） |
| 检验统计量与自由度 | 应报告（如 `t(18) = 2.31`），使 p 值可复核 | `p_value_reporting`（minor） |
| 误差类型 | SD / SEM / 95% CI 必须明确标注；**图中用 SEM 而正文称 SD 是常见错误** | `error_bar_reporting`（minor；图文矛盾时升 major） |
| 效应量 | 组间比较应报效应量（Cohen's d、均差 + CI、OR/RR/HR + CI） | `effect_size_reporting`（minor） |
| 临床意义 | **统计学显著 ≠ 临床意义显著。** 应查该类指标常用的临床显著标准（MCID）并与之比较 | `effect_size_reporting`（major，当仅凭 p 值支撑关键结论时） |
| 缺失数据 | 说明缺失比例与处理方法（完整病例 / 多重填补 / LOCF） | `missing_data_handling`（minor） |
| 检验方向 | 单尾检验必须事先说明理由 | `one_sided_unjustified`（major） |
| 精确度 | 报告位数应与测量精度相称 | `p_value_reporting`（info） |

> **误差棒类型与图的联动**：`figure_records[].significance_markers` 与
> `experimental_conditions` 提供图内信息。图注写 SEM 而正文写 SD 属
> **稿件内部矛盾**，主责在 M2；M4 只在它影响统计解读时补一条 finding，
> 两者会在 Stage 5 聚簇为同一个 issue（`00-contracts.md §9.3`）。

---

## 8. 多重比较

| 检查 | 判据 |
| --- | --- |
| 同一数据集做了多少次检验？ | 由 `statistical_methods[].applied_to` 与 `key_data[]` 的比较数推算。**属于多重检验的情形**：多基因分析、多蛋白检测、多终点分析、亚组分析、多次两两比较 |
| 是否校正？ | `correction` 字段；Bonferroni / Holm / Šidák / FDR-BH 均可接受 |
| 组学是否报 adjusted p / q？ | §4.8 |
| ≥3 组的事后比较是否校正？ | Tukey / Dunnett / Games-Howell 本身已含校正 |
| 是否只报显著结果？ | 与 M2 联动（选择性报告） |

**不触发的情形**：作者明确声明次要终点为**探索性分析**且不做推断性结论时，
不校正是可接受的 —— 此时应检查结论是否越界（交 M7），而不是判 M4 的 finding。

---

## 9. category slug

**命名以蒋蕴版为准**（更成体系）。severity 不写死 —— 按 §3.5，
同一 slug 影响主要终点是 `critical`，只影响次要/探索性分析是 `major`。

| slug | 可能原因举例 | 分级依据 |
| --- | --- | --- |
| `statistical_test_selection` | 检验方法与数据类型/设计不匹配（§4.1–4.9） | 影响主要终点分析 → critical；次要分析方法不合理 → major |
| `model_specification` | 回归、生存、预测模型的设定或建立错误（§4.10） | 导致主要效应估计可能偏倚 → critical；模型解释或调整不足 → major |
| `statistical_assumption` | 未验证正态性/方差齐性/球形性/比例风险/过离散 | 严重影响结果可信度 → major；仅报告不足 → minor |
| `power_and_sample_size` | 适用的样本量/精度依据缺失，或作者声称的计算不可复算（§5） | 确证性主要目标无依据或计划—实际明显矛盾 → major；探索性研究不因未做疗效 power 自动报警 |
| `multiple_testing_control` | 多重比较未校正（§8） | 高维组学数据无校正 → critical；普通多重比较未校正 → major |
| `replication_independence` | 独立分配单位内的亚样本/技术重复被当独立 n（§4.9） | 默认 major；分配层、分析层与主要结论影响均有证据时才 critical |
| `selective_reporting` | 疑似选择性报告 / 终点事后更换 | critical |
| `error_bar_reporting` | 误差类型未标注或图文不一致（§7） | 影响结果解释 → major；仅格式不规范 → minor |
| `p_value_reporting` | 仅报 `p<0.05`，无精确值或统计量（§7） | 影响结果解释 → major；仅格式不规范 → minor |
| `effect_size_reporting` | 未报告效应量；或仅凭 p 值支撑关键结论而未对照临床显著标准（§7） | 仅 p 值支撑关键结论 → major；次要指标缺失 → minor |
| `missing_data_handling` | 缺失数据处理未说明（§7） | major |

**框架侧补充的四条**（蒋蕴版未覆盖，保留）：

| slug | 说明 | 分级依据 |
| --- | --- | --- |
| `agreement_by_correlation` | 用相关系数证明两种测量方法一致（应做 Bland-Altman，§4.6） | major |
| `censoring_ignored` | 生存数据忽略删失（如用 t 检验比中位生存，§4.5） | 默认 major；直接作用于主要时间结局并可能改变结论时 critical |
| `cutoff_not_validated` | 数据内选截断后未校正乐观度，或把开发性能当确认性验证（§4.7） | major |
| `one_sided_unjustified` | 单尾检验无事先说明（§7） | major |

**由一期确定性取证 signal 触发的五条**（§2）：

| slug | 触发 signal | 分级依据 |
| --- | --- | --- |
| `p_value_inconsistent` | `test_statistic_p_mismatch` | 默认 major；主要终点且报告/反算 p 位于预设 α 两侧并影响结论时 critical |
| `ci_self_inconsistent` | `ci_estimate_mismatch` | major |
| `percentage_mismatch` | `count_percentage_mismatch` | 默认 minor；改变主要终点分母、效应量或受试者流时 major |
| `grim_violation` | `grim_incompatible_mean` | 默认 major；人工排除调整均值、分母与舍入歧义且影响核心结论时才 critical |
| `table_total_mismatch` | 同名 signal | 默认 minor；影响主要终点、受试者流或安全性分母时 major，不得 critical |

> 据 signal 立 finding 时，**必须**在 `evidence_refs[]` 中独立给出稿件证据
>（报告该数值的原文位置），不得仅引用 signal id（`00-contracts.md §6.1` 规则 5）。

### 9.1 旧 slug 迁移

框架侧早期用过的名字一律改写为上表：

```
wrong_test                        -> statistical_test_selection
pseudoreplication                 -> replication_independence
assumption_unchecked              -> statistical_assumption
sample_size                       -> power_and_sample_size
no_multiple_comparison_correction -> multiple_testing_control
multiple_comparison_correction    -> multiple_testing_control
sample_size_reporting             -> power_and_sample_size
error_bar_ambiguous               -> error_bar_reporting
p_value_incomplete                -> p_value_reporting
no_effect_size                    -> effect_size_reporting
missing_data_unhandled            -> missing_data_handling
over_precision                    -> （并入 p_value_reporting 的 minor 档）
```

---

## 10. 正例 / 反例

### 10.1 `statistical_test_selection`

**该报警**：同一批小鼠给药前后各测一次血糖（配对设计，`relatedness = paired`），
方法节写「independent samples t-test」→ `mismatch` → 默认 **major**；只有重算证明其改变
主要结论方向或显著性分类时才升 `critical`。

**不该报警**：两组独立小鼠比较，作者用 Welch t 而非 Student t，并说明方差不齐
→ Welch 在 `acceptable` 集内 → **不报**。

### 10.2 `replication_independence`

**该报警**：6 只小鼠，每只取 10 个视野计数，统计写 `n = 60`，
稿件明确处理分配在小鼠层级却把 60 个视野作为独立样本 → `replication_independence`；若它支撑
主要结论并改变显著性分类则 **critical**，否则默认 **major**。

**不该报警**：6 只小鼠，每只取 10 个视野，**先按动物求均值**再比较，`n = 6`
→ 正确做法 → **不报**。
`replicate_type = unspecified` 时也**不报**，改出 `partial_extraction`。

### 10.3 `statistical_assumption`

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

### 10.6 `power_and_sample_size`（体现口径）

**该报警（但措辞克制）**：确证性小鼠肿瘤实验每组 n = 3，未给样本量依据、预期效应、
变异或不确定性区间，却据单次显著性检验下强效治疗结论
→ `power_and_sample_size`（major），detail 写「独立实验单位很少，且未见与主要终点对应的样本量/
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
- [x] 填充 §5.2 分研究类型复核入口，并明确禁止固定 n 下限
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
