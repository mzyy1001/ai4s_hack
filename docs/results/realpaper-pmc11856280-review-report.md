# 论文审核报告 · Soluble RAGE enhances muscle regeneration after cryoinjury in aged and diseased mice

> DOI：10.1371/journal.pone.0318754 ｜ 期刊：PLOS ONE（PMC11856280, PMID 39999114）｜ 输入格式：`jats_xml`（另附 paper.pdf 与 figures/ 三张主图）

## 一、执行摘要

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。** 本 Skill 的任何评分均为筛查信号，不构成录用、退稿或发表决定。

### 本报告能回答什么

> 已执行 M2–M7；“未产出 finding”只表示本流程在已取得证据中未检出，不等于论文结论已被证实。

| 执行模式 | submode | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- |
| `full_review` | — | M2, M3, M4, M5, M6, M7 | — |

- 范围依据：动物体内研究 → M3/M6；统计报告密集 → M4；三张主图 → M5；结论外推显著 → M7；跨节候选 → M2 + Layer 4 校正。
- 已执行阶段：stage_1（发现）、stage_2（结构化抽取）、stage_3（图解析尝试+图像完整性审计）、stage_3b（观测组归并）、stage_3c_external_validation（X1 外部核验）、stage_4（跨节校正）、stage_5（契约归一）。

### 审稿人先看

- 稿件风险筛查分：`100/100`；分段：`major_revision_suggested`（≥50）。
- 评分边界：分段阈值未经实证验证，是初始经验值，不得表述为自动化的录用/退稿决定。分值由确定性权重算出（每簇 critical 25 / major 10 / minor 3 / info 0，每 category 上限 30），不是概率。
- findings：43 条（critical 0 ｜ major 20 ｜ minor 16 ｜ info 7）；复核动作：10 项（P0×7、P1×2、P2×1）。
- 抽取覆盖率计算值：`0.600`；必须结合第七节分子/分母解释，不是稿件质量概率。
- 审核置信度：`review_confidence = 0.600`。这是未经校准的证据支撑指数，不是 finding 正确概率，也不是稿件质量概率。（无像素/OCR 依赖；置信度被拉低的唯一原因是图像不可读与补充材料不可得导致的覆盖率损失。）

### 优先处理（最多三项）

- [ ] **[P0] 核对 Discussion/标题与 Results 的模型范围矛盾，逐句更正**（领域审稿人）
  - 关联判断：RF-01（major，Discussion ¶1 称 adult/aged/diseased 均显著 vs Results 成年无效应、db/db 仅趋势）；XF-01（major，'两套遗传系统结果相似' 与年龄对齐数据相反）；RF-02（major，标题 diseased 超证据）；RF-39（major，局限回避）。定位：[EV-001｜Discussion sec025 ¶1]
- [ ] **[P0] 统计重分析包：确切 n 与剔除、重复测量模型、2×2 交互、多重校正、确切 P/效应量/CI、样本量依据**（统计审稿人）
  - 关联判断：RF-20/RF-21/RF-19/RF-23/RF-24/RF-27（六条 major）+ RF-22/RF-25（minor）。定位：[EV-063｜缺失检索：全文无确切 P 值/统计量]
- [ ] **[P0] 复核主要终点 CSA 的选片偏倚与个体纤维原始数据**（领域审稿人）
  - 关联判断：RF-13（major，'中央核纤维最多'切片+最大损伤区旁视野的正向选片）；RF-41（info，阳性 CSA 主张支撑力备查）。定位：[EV-028｜Methods sec006]

## 二、结构化结果表

结构化结果版本：structured_result v2（Stage 2 抽取 + Stage 3b 归并）；`stage_3b_executed=true`（视觉解析尝试执行、因无图像输入能力失败项已转 parse_failed）。本节只展示条件必填、未解析/缺失及与 finding 证据相交的字段；另有 12 个已报告或不适用的 recommended/optional 字段保留在 `structured_result.json`。

| 字段 | 适用性 / 必填性 | 状态 | 值 / 单位 | 抽取置信度 | 原文定位 |
| --- | --- | --- | --- | --- | --- |
| `design.randomization` | applicable / required | `not_reported` | — | high | [EV-060｜缺失检索：Methods+declarations｜no_match] |
| `measurement.sample_size_justification` | applicable / required | `not_reported` | — | high | [EV-061｜缺失检索：Methods｜no_match] |
| `declarations.author_contributions` | applicable / required | `not_reported` | — | high | [EV-062｜缺失检索：全文｜no_match] |
| `population.inclusion_criteria` | applicable / recommended | `ambiguous` | 仅隐性性别/年龄匹配规则 | medium | [EV-019｜Methods sec004] |
| `design.interventions` | applicable / required | `reported` | AAV9-sRAGE 1e11 vg/鼠 眶后注射；cryoinjury/BaCl2 损伤；MuSC 移植 3000/6000 细胞 | high | [EV-007｜sec017]｜[EV-008｜Fig 1C] |
| `declarations.ethics_statement` | applicable / required | `reported` | Harvard IACUC #29-14 | high | [EV-033｜sec003] |
| `declarations.competing_interests` | applicable / required | `reported` | A.J.W.：Kate/Frequency Therapeutics 顾问；Elevian 联合创始人/SAB/持股；Elevian 资助 Wagers 实验室 | high | [EV-049｜author-notes fn] |

### 核心数据观测组摘要

| 观测组 / 指标 | 上下文 | 状态 | canonical | 报告完整性 / 缺失要素 |
| --- | --- | --- | --- | --- |
| `KD-001` · 寿命期血清 sRAGE 浓度 (`biomarker_concentration`) | EXP-01，4/7/12/18 月龄 C57BL/6J | `parse_failed` | —（SYS-001/005：绝对值在 Fig 1A 图内，视觉解析失败） | `not_assessed`；轴值、个体点 |
| `KD-002` · 再生纤维 mean CSA（成年 cryoinjury 7 dpi） | EXP-02，AAV vs vehicle | `reported` | 无显著差异（方向性；绝对值在图内） | `incomplete`；确切 n（n≥7）、P 值、效应量 |
| `KD-003` · 再生纤维 mean CSA（老龄 cryoinjury 7 dpi） | EXP-03，n=10/组 | `reported` | sRAGE 组增大（方向性） | `incomplete`；P 值、效应量/CI |
| `KD-004` · 再生纤维 mean CSA（db/db cryoinjury） | EXP-05，n=6/组 | `reported` | 趋势不显著 | `incomplete`；P 值、CI |
| `KD-005` · 再生纤维 mean CSA（ApoE-/- cryoinjury） | EXP-06，n=6/组 | `reported` | sRAGE 组增大（方向性） | `incomplete`；P 值、效应量 |
| `KD-006` · AAV 后血清 sRAGE 动力学 | EXP-02/03/05/06 | `reported` | 约 10 倍升高，5–30 天维持 | `incomplete`；重复测量模型、确切 P |
| `KD-007` · db/db/ApoE 体重与血糖（AAV 后） | EXP-05/06 | `reported` | 无处理差异 | `incomplete`；P 值 |
| `KD-008` · BaCl2 损伤后 mean CSA（全队列） | EXP-04/05/06+转基因 | `reported` | 无处理效应 | `incomplete`；P 值、确切 n |
| `KD-009` · 转基因 s/s、s/+ cryoinjury CSA（效应量） | EXP-08 | `reported` | 约 +30%（相对表述） | `incomplete`；绝对值、P、CI |
| `KD-010` · 未损伤基线 CSA（转基因各基因型） | EXP-07，n=3/组 | `reported` | 无差异 | `incomplete`；n=3 功效 |
| `KD-011` · 移植后 dystrophin+ 纤维计数 | EXP-09，n≥5/组 | `reported` | 基因型间无差异 | `incomplete`；灵敏度/阳性对照 |
| `KD-012` · 老龄鼠血糖（AAV 后） | EXP-03 | `reported` | sRAGE 组下降 | `incomplete`；多重校正后稳健性未知 |
| `KD-013` · 老龄鼠体重/抓网/耐力 | EXP-03 | `reported` | 无差异 | `incomplete`；测试上限/截尾规则 |

### 需要回查来源的观测组

所有核心数据组均已得到单一来源的 canonical（正文+图注一致，无多来源冲突）；绝对数值位于图内，因 SYS-001 无法视觉读取，相关字段见上表的缺失要素列与第六节系统限制。

## 三、图表解读与原图定位

> 本节记录 Stage 3 的可见事实与只读解读，不是 M5 审核判断；图表问题只在第四节以 finding 展示。
> **重要限制**：本次运行所有通道（主会话与全部子会话）均无图像输入能力，以下解读基于图注与正文（caption/text 级），像素级内容未核验；`extraction_confidence` 一律 low。确定性像素审计（figure_integrity_audit）对三张原始图成功执行，0 信号（未检出≠无问题）。

### Fig 1 · statistical_plot（13 面板 A–M）

- 原图：figures/pone.0318754.g001.png（本地文件存在，视觉不可读｜SYS-001）；正文首次引用：sec022（Results）
- 科学问题：sRAGE 是否随年龄变化；AAV9-sRAGE 能否提高成年/老龄鼠冷冻损伤后的再生（CSA）及功能/代谢。
- 条件与坐标：4/7/12/18 月龄基线（A，n=5）；AAV9-sRAGE vs vehicle(FBB/FFB)，成年 7–8 月（n≥7）与老龄 18 月（n=10）；cryoinjury 后 7 天取材；J–M 为体重/抓网/耐力/血糖。
- 只读解读：Results 称成年 CSA 无效应、老龄 CSA 增大、四终点中仅血糖显著；统计：one-way ANOVA+Tukey (A,D,G)、t test (E,H,J,K,L,M)、MWU (F,I)。
- 定量观测：仅图注文本可得（n、检验名）；轴值/个体点不可读（SYS-001）。
- 抽取置信度：`low`；人工复核：`true`
- 解析限制：SYS-001（全图视觉不可读）

### Fig 2 · statistical_plot（12 面板 A–L）

- 原图：figures/pone.0318754.g002.png；正文首次引用：sec023
- 科学问题：sRAGE 能否改善糖尿病（db/db）与动脉粥样硬化（ApoE-/-）模型的再生。
- 条件与坐标：db/db+WT（A–F，n=6/组）与 ApoE-/- 臂（G–L，scheme 含 WT 但数据仅 ApoE-null，n=6）；均为 2–3 月龄；cryoinjury 7 dpi。
- 只读解读：db/db 仅趋势、ApoE-/- CSA 显著增大；B/C/D two-way ANOVA、E/H/I/J one-way ANOVA、K t test；F/L 的 MWU/KW 未逐面板绑定。
- 抽取置信度：`low`；人工复核：`true`
- 解析限制：SYS-001

### Fig 3 · mixed（示意/WB/H&E/统计，10 面板 A–J）

- 原图：figures/pone.0318754.g003.png；正文首次引用：sec024
- 科学问题：内源 Ager 基因座改造（KO/KI）对再生的影响；MuSC 内在 vs 微环境 sRAGE 的作用。
- 条件与坐标：6 种基因型；B ELISA（n≥5）；C WB 验证；D 未损伤 CSA（n=3）；G/H cryoinjury 7 dpi（n≥3，含 KO 组）；I/J 移植 3000/6000 MuSC 入 mdx（n≥5）；7–8 月龄。
- 只读解读：s/s 与 s/+ 再生 CSA +30%；移植无基因型差异；图注标记 ItgB7+ 与 Methods CD29+ 冲突（见 RF-04）。
- 抽取置信度：`low`；人工复核：`true`
- 解析限制：SYS-001（WB 条带、H&E 图未目检）

本文无表格（table_records 为空）；补充图 S1–S3 仅图注可见（SYS-002），不做图记录。

## 四、审核发现

### [major] CL-001 · Discussion 称 adult/aged/diseased 均显著增大 CSA，与 Results 直接矛盾

- 类别：internal_inconsistency
- 关联判断：
  - **RF-01** ｜ major ｜ M2 ｜ review_confidence: high ｜ rule_ref: 02-macro-logic#cross-section-consistency ｜ 人工复核：P0/领域审稿人（逐句核对 Discussion ¶1 与 Results/Fig 1E/Fig 2E，删除或改写 adult 与 diabetic 的'显著'表述）
    Discussion ¶1 'significant increases ... in adult, aged, and diseased mice' vs Results：成年鼠 CSA 'similar'（Fig 1E）、db/db 'never reached statistical significance'。实际成立者仅老龄与 ApoE-/-。
- 证据包：[EV-001｜Discussion sec025 ¶1｜"we observed significant increases in the mean fiber sizes 7 days after cryo-injury in adult, aged, and diseased mice"]；[EV-002｜Results sec022 ¶2｜成年 CSA 'similar']；[EV-003｜Results sec023 ¶1｜db/db 'never reached statistical significance']

### [major] CL-002 · '两套遗传系统结果相似' 与年龄对齐数据相反（Layer 4 新发现）

- 类别：internal_inconsistency
- 关联判断：
  - **XF-01** ｜ major ｜ M2 ｜ review_confidence: high ｜ rule_ref: 02-macro-logic#cross-section-consistency ｜ 人工复核：P0/领域审稿人（核对 Fig 1E-F vs Fig 3G-H 年龄可比性，解释差异或更正表述）
    Discussion ¶1 'both genetic systems gave similar results'：同为 7–8 月龄，AAV 成年无效应（Fig 1E-F）vs 转基因 s/s、s/+ +30%（Fig 3G-H，图注 All mice 7–8 months）；转基因系统从未在老龄/疾病模型检验。
- 证据包：[EV-004｜Discussion ¶1]；[EV-002｜Results 成年]；[EV-016｜Results s/s、s/+ larger]；[EV-052｜Fig 3 图注尾句 7–8 months]

### [major] CL-003 · 标题 'aged and diseased mice' 超出证据范围

- 类别：claim_beyond_evidence
- 关联判断：
  - **RF-02** ｜ major ｜ M7 ｜ high ｜ 07-conclusions-discussion#claim-scope ｜ P0/编辑（标题改为 aged and atherosclerotic 或明示糖尿病模型无效）
    疾病模型中仅 ApoE-/- 阳性、db/db 无效应；Abstract 谨慎写 'aged and atherosclerotic'，标题应与之对齐。
- 证据包：[EV-005｜标题]；[EV-006｜Abstract 'aged and atherosclerotic animals']；[EV-003｜db/db 非显著]

### [major] CL-004 · vehicle 缩写 FFB/FBB 混用（FBB 从未定义）

- 类别：terminology_inconsistency
- 关联判断：
  - **RF-03** ｜ major ｜ M2 ｜ high ｜ 02-macro-logic#terminology ｜ P1/作者（全文统一为 FFB 或定义 FBB，图内标签同步）
    Methods/Results 定义 FFB（1xPBS, 35 mM NaCl, 0.001% Pluronic）；Fig 1 C–F 与 Fig 2 A/G scheme 写 'FBB'、其余面板 'FFB'；S1–S3 同。按队列分界出现，可被误读为两种 vehicle。
- 证据包：[EV-007｜sec017 FFB 定义]；[EV-008｜Fig 1C '(FBB)']；[EV-009｜Fig 1G '(FFB)']；[EV-013｜Fig 2G '(FBB)']；[EV-014｜Fig 2H '(FFB)']

### [major] CL-005 · Fig 3 移植细胞 ItgB7+ 与 Methods CD29+（β1-integrin）门冲突

- 类别：figure_methods_marker_conflict
- 关联判断：
  - **RF-04** ｜ major ｜ M3 ｜ high ｜ 03-experimental-methods#cell-identity ｜ P0/领域审稿人（出示移植实验实际分选记录，更正图注）
    Fig 3I-J 图注 'ItgB7+; CXCR4+' vs Methods sec007 'CD29+ (β1-Integrin); CD184+ (CXCR4)'；Itgb7≠Itgb1，且抗体面板无 anti-Itgb7。图注错误或实际分选与描述不符二选一；直接影响 CL-06 证据基础。
- 证据包：[EV-010｜Fig 3I-J 图注]；[EV-011｜sec007 MuSC 门定义]

### [major] CL-006 · ELISA 全血+RIPA 裂解检测却称 'serum sRAGE'

- 类别：method_reporting_incomplete
- 关联判断：
  - **RF-12** ｜ major ｜ M3 ｜ medium（试剂盒特异性外部不可核验，SYS-003）｜ 03-experimental-methods#assay-reporting ｜ P0/领域审稿人（澄清样本类型/稀释回算/试剂盒 sRAGE 亚型特异性）
    sec011：尾静脉血 50 µL + RIPA 50 µL 裂解，非血清制备；全文称 'serum sRAGE'。未报试剂盒特异性、检测范围与 1:2+1:10 稀释回算。sRAGE 是分组验证的核心读数。
- 证据包：[EV-027｜sec011 全血+RIPA]；[EV-043｜Results 'serum sRAGE' 表述]；[EV-021｜Fig 1D 图注]

### [major] CL-007 · 主要终点 CSA 的正向选片规则（偏倚风险）

- 类别：protocol_deviation_unexplained
- 关联判断：
  - **RF-13** ｜ major ｜ M3 ｜ high ｜ 03-experimental-methods#sampling-bias ｜ P0/领域审稿人（核对 Dryad 逐纤维数据；要求系统随机采样或敏感性分析）
    sec006：取'中央核纤维最多'切片 + '最大损伤区旁'4 视野——确定性正向挑选、非系统均匀采样、无理由。该读数为全部阳性 CSA 结论（CL-02/04/05）的主要终点。
- 证据包：[EV-028｜Methods sec006 选片规则原文]

### [major] CL-008 · 动力学面板重复测量设计误用普通 ANOVA

- 类别：statistical_test_selection
- 关联判断：
  - **RF-19** ｜ major ｜ M4 ｜ medium（Fig 2C/D 时间结构因 SYS-001 未确证）｜ 04-statistics#test-selection ｜ P0/统计审稿人（重复测量/混合模型重分析）
    Fig 1D/G、Fig 2B/H 为同一批鼠连续尾静脉采血的组×时间重复测量，却用普通 one/two-way ANOVA，时点当独立、时间点多比较未校正。
- 证据包：[EV-053｜Fig 1 图注检验声明]；[EV-021｜Fig 1D kinetics n≥7]；[EV-024｜Fig 2 图注 two-way (B,C,D)]

### [major] CL-009 · 确切 n 缺失：'n≥' 记法混用、无剔除报告

- 类别：missing_data_handling
- 关联判断：
  - **RF-20** ｜ major ｜ M4 ｜ high ｜ 04-statistics#sample-size-reporting ｜ P0/统计审稿人（逐面板报告确切 n、剔除/脱落数与原因）
    'n ≥ 7/n ≥ 5/n ≥ 3' 与确切 'n=' 混用；无任何剔除/脱落说明；自由度不可还原、统计结论不可复核。
- 证据包：[EV-021｜Fig 1 n≥7]；[EV-052｜Fig 3 n≥3/n≥5]；[EV-015｜Fig 3G-H n≥3]

### [major] CL-010 · 确证性动物研究无样本量依据/功效分析（统计+伦理 3R 双视角）

- 类别：power_and_sample_size
- 关联判断：
  - **RF-21** ｜ major ｜ M4 ｜ high ｜ 04-statistics#power ｜ P0/统计审稿人（补事前样本量依据或事后功效/精度说明）
    确证性体内干预研究（主要终点 7 dpi CSA）作出明确疗效结论，却无任何样本量依据（含 ETH-ANI-002 3R-Reduction；伦理侧防误报上限 minor，合并取高）。多组仅 n=3–5。
- 证据包：[EV-061｜缺失检索：sample size / power analysis｜no_match]；[EV-054｜Fig 3D n=3]

### [major] CL-011 · Fig 2E 2×2 析因设计用 one-way ANOVA，无交互检验

- 类别：statistical_test_selection
- 关联判断：
  - **RF-23** ｜ major ｜ M4 ｜ high ｜ 04-statistics#test-selection ｜ P0/统计审稿人（two-way ANOVA 重分析并报告交互项）
    WT/db/db × vehicle/sRAGE（n=6/组）用 one-way ANOVA；交互恰是科学问题（sRAGE 是否仅在疾病背景有效）；同图 B/C/D 却用 two-way，策略自相矛盾。S2B 同样问题。
- 证据包：[EV-025｜Fig 2E 组结构]；[EV-024｜图注检验声明]

### [major] CL-012 · 全文无确切 P 值/检验统计量/CI，统计推断不可复核

- 类别：p_value_reporting
- 关联判断：
  - **RF-24** ｜ major ｜ M4 ｜ high ｜ 04-statistics#pvalue-reporting ｜ P0/统计审稿人（报告所有比较的确切 P、统计量与自由度）
    Results 仅 'significant/not significant' + 图内括号；确定性取证层（statistical_forensics 五项）因无任何确切数值统计量而全部 not_applicable——第三方无法复核。
- 证据包：[EV-063｜缺失检索：exact p / t( / F( / df / CI｜no_match]；[EV-023｜sec020 仅声明 P<0.05 阈值]

### [major] CL-013 · Fig 1J-M 四终点独立 t 检验无多重校正

- 类别：multiple_testing_control
- 关联判断：
  - **RF-27** ｜ major ｜ M4 ｜ high ｜ 04-statistics#multiplicity ｜ P0/统计审稿人（终点家族校正或声明探索性）
    体重/抓网/耐力/血糖 4 终点各做独立 t 检验（n=10/组）无校正；唯一显著的血糖结论在校正后稳健性存疑。
- 证据包：[EV-022｜Fig 1J-M 图注]；[EV-023｜sec020]

### [major] CL-014 · 多处阴性结果被写成 '零效应/等效' 命题

- 类别：negative_result_misread
- 关联判断：
  - **RF-30** ｜ major ｜ M7 ｜ high ｜ 07-conclusions-discussion#negative-results ｜ P0/统计审稿人（改'未检出差异'表述 + CI/功效说明）
    BaCl2 系列（Abstract 'had no impact'）、功能终点、移植（CL-06 基础）、寿命 ELISA（n=5 被肯定式解读为'不随年龄变化'）、基线 CSA（n=3）——均无等效界值/CI/确切 P。
- 证据包：[EV-044｜Abstract BaCl2 表述]；[EV-041｜移植 'did not differ']；[EV-043｜寿命 ELISA 解读]；[EV-042｜Discussion ¶5 移植表述]

### [major] CL-015 · 疼痛操作无麻醉/术后镇痛/人道终点报告

- 类别：ethics_compliance
- 关联判断：
  - **RF-33** ｜ major ｜ M6 ｜ high ｜ 06-ethics-compliance#analgesia ｜ P0/伦理委员会（补充各疼痛操作麻醉/镇痛方案与人道终点）
    cryoinjury（皮肤切口+干冰冷压 10 秒）、BaCl2 肌注、TA 内移植、电刺激力竭跑台均无麻醉/镇痛；7 天恢复期无镇痛；全文无人道终点。仅眶后注射有异氟烷+眼表麻醉。违反 ETH-ANI-004。
- 证据包：[EV-065｜缺失检索：analgesia/humane endpoint｜no_match]；[EV-031｜cryoinjury 描述]；[EV-046｜BaCl2 预损伤]；[EV-047｜仅眶后注射有麻醉]

### [major] CL-016 · 安乐死方法未报告

- 类别：ethics_compliance
- 关联判断：
  - **RF-34** ｜ major ｜ M6 ｜ high ｜ 06-ethics-compliance#euthanasia ｜ P0/伦理委员会（补充方法与死亡确认手段）
    全文仅 'After 7 days, mice were euthanized'，未指明任何方法（CO2/颈椎脱臼/过量麻醉）与二次确认，无法对照 AVMA 指南。
- 证据包：[EV-064｜缺失检索：euthanasia method｜no_match]；[EV-045｜sec006 'mice were euthanized']

### [major] CL-017 · Fig 3C WB 面板无 n/无定量/图内未呈现内参

- 类别：missing_loading_control
- 关联判断：
  - **RF-31** ｜ major ｜ M5 ｜ medium（条带目检受 SYS-001 限制）｜ 05-figures-and-charts#western-blot ｜ P1/领域审稿人（报告生物重复 n、内参呈现、分子量标注；Dryad 原始膜图可复核）
    基因型验证的关键 WB：未报 n、无定量、无分子量标注，图注/图内均未呈现内参；Methods 明示 GAPDH 在另一块胶。
- 证据包：[EV-038｜Fig 3C 图注]；[EV-039｜sec010 GAPDH separate gel]

### [major] CL-018 · Conclusion 治疗外推超出证据范围

- 类别：claim_beyond_evidence
- 关联判断：
  - **RF-37** ｜ major ｜ M7 ｜ high ｜ 07-conclusions-discussion#generalization ｜ P0/编辑（收窄表述，限定损伤模型与证据层级）
    'potential therapeutic strategy for skeletal muscle injury, aging muscle, and degenerative disorders'：证据限于小鼠单一损伤模型、BaCl2 无效应、糖尿病模型无效应、仅雄性、主要终点有选片偏倚与统计不可复核。
- 证据包：[EV-040｜Conclusion 原文]；[EV-003｜db/db 无效应]

### [major] CL-019 · CL-06 '微环境 sRAGE 是关键' 推断超支撑

- 类别：claim_beyond_evidence
- 关联判断：
  - **RF-38** ｜ major ｜ M7 ｜ high ｜ 07-conclusions-discussion#null-inference ｜ P0/领域审稿人（提供移植检测灵敏度/阳性对照，解决 RF-04 后再主张机制）
    (a) 唯一证据是一次阴性移植实验（n≥5/组），无 no-cell/阳性对照；(b) 供体细胞身份冲突（RF-04）。阴性结果不能证明 'MuSC 内在 sRAGE 无关'。
- 证据包：[EV-041｜'did not differ']；[EV-042｜Discussion ¶5]；[EV-010｜ItgB7+ 图注]

### [major] CL-020 · 无相应 Limitations 承认方法学局限

- 类别：limitations_evasive
- 关联判断：
  - **RF-39** ｜ major ｜ M7 ｜ high ｜ 07-conclusions-discussion#limitations ｜ P1/编辑（Limitations 明示小样本/无功效/n≥/选片/仅雄性/单时间点）
    RF-20/21/24 已成立，但 Discussion 全七段与 Conclusion 均未承认样本量/功效/选片等任何方法学局限。
- 证据包：[EV-061｜缺失检索：sample size/power]；[EV-069｜缺失检索：Discussion+Conclusion limitation｜no_match]

### [minor] CL-021 · AAV→损伤间隔未显式报告（~23 天仅可推算）

- 类别：timeline_reporting_gap
- 关联判断：**RF-05** ｜ minor ｜ M2 ｜ high ｜ P2/作者。AAV 后 30 天评估 + 7 dpi，间隔只能推算。
- 证据包：[EV-012｜Results sec022 ¶2]

### [minor] CL-022 · Fig 2G scheme 含 WT，数据面板与正文无 WT 组

- 类别：internal_inconsistency
- 关联判断：**RF-06** ｜ minor ｜ M2 ｜ high ｜ P2/领域审稿人。ApoE 臂 WT 是否存在不明。
- 证据包：[EV-013｜Fig 2G scheme]；[EV-014｜Fig 2H 仅 ApoE-null]

### [minor] CL-023 · Fig 3G-H 含 KO 组但 Results 未报告 KO 臂

- 类别：figure_text_reporting_gap
- 关联判断：**RF-07** ｜ minor ｜ M2 ｜ high ｜ P2/领域审稿人。Discussion ¶4 对 7–8 月 KO 的讨论在 Results 无据。
- 证据包：[EV-015｜Fig 3G-H 图注]；[EV-016｜Results 只述 s/s、s/+]；[EV-017｜Discussion ¶4]

### [minor] CL-024 · Methods '2–20 月龄' vs 实际最大 18 月龄

- 类别：internal_inconsistency
- 关联判断：**RF-09** ｜ minor ｜ M2 ｜ high ｜ P2/作者。无 20 月龄实验。
- 证据包：[EV-019｜sec004]；[EV-020｜Fig 1A 4–18 月]；[EV-050｜Fig 2 图注 2–3 月]

### [minor] CL-025 · 小鼠基因符号不规范/混用（AGER、Cd45/CD45、CXCR4、Hoescht）

- 类别：gene_symbol_nonstandard
- 关联判断：**RF-10** ｜ minor ｜ M3 ｜ high ｜ P2/作者。确定性工具产 gene_symbol_species_mismatch 候选 3 条（SIG-101/102/103）。
- 证据包：[EV-010｜Fig 3I-J 图注]；[EV-011｜sec007]

### [minor] CL-026 · 随机化未报告、盲法仅覆盖切片分析

- 类别：randomization_blinding_unreported
- 关联判断：**RF-11** ｜ minor ｜ M3 ｜ high ｜ P2/作者。注射/移植/行为学未设盲说明。
- 证据包：[EV-060｜缺失检索：randomization｜no_match]；[EV-034｜sec006 'Slides were coded']

### [minor] CL-027 · AAV QC 仅 qPCR 滴度（无纯度/无菌/空实比/效力）

- 类别：method_reporting_incomplete
- 关联判断：**RF-14** ｜ minor ｜ M3 ｜ high ｜ P2/领域审稿人。工具信号：bGH-F/R 引物 Tm/GC 偏离常规（候选级，SIG-001/002）。
- 证据包：[EV-029｜sec016 滴度方法]

### [minor] CL-028 · HEK293 无来源/鉴定/支原体声明（外部核验未见误认）

- 类别：cell_line_unauthenticated
- 关联判断：**RF-15** ｜ minor ｜ M3 ｜ high ｜ P2/作者。Cellosaurus CVCL_0045 resolved、无 problematic flag——报告缺失而非身份错误。
- 证据包：[EV-030｜sec014 HEK293]；[EV-902｜Cellosaurus resolved 2026-08-07]

### [minor] CL-029 · cryoinjury 参数欠报告（探头规格/压力/损伤面积归一化）

- 类别：method_reporting_incomplete
- 关联判断：**RF-16** ｜ minor ｜ M3 ｜ high ｜ P2/作者。
- 证据包：[EV-031｜sec006]

### [minor] CL-030 · 小样本参数检验无前提检验；参数/非参数并行无理由

- 类别：statistical_assumption
- 关联判断：**RF-22** ｜ minor ｜ M4 ｜ medium（偏态/离群目检受 SYS-001 限制，升级与否待有图像运行）｜ P2/统计审稿人。
- 证据包：[EV-023｜sec020]；[EV-026｜Fig 2 分布检验]

### [minor] CL-031 · 无效应量/CI，仅相对表述（~30%、~10-fold）

- 类别：effect_size_reporting
- 关联判断：**RF-25** ｜ minor ｜ M4 ｜ high ｜ P2/统计审稿人。
- 证据包：[EV-016｜'~30% greater' 语境]；[EV-022｜Fig 1J-M]

### [minor] CL-032 · Fig 2 图注 MWU/KW 合并写 '(F, L)' 未逐面板绑定

- 类别：statistical_test_selection
- 关联判断：**RF-26** ｜ minor ｜ M4 ｜ high ｜ P2/作者。S2/S3 图注同类歧义。
- 证据包：[EV-026｜Fig 2 图注]

### [minor] CL-033 · 多窝混合入组但窝效应未报告/未纳入分析

- 类别：statistical_assumption
- 关联判断：**RF-28** ｜ minor ｜ M4 ｜ high ｜ P2/统计审稿人。
- 证据包：[EV-035｜sec003 'multiple litters']

### [minor] CL-034 · 抓网/跑台无测试上限与截尾规则

- 类别：statistical_assumption
- 关联判断：**RF-29** ｜ minor ｜ M4 ｜ medium（截尾值核验受 SYS-001 限制）｜ P2/统计审稿人。
- 证据包：[EV-036｜sec018]；[EV-037｜sec019]

### [minor] CL-035 · 饲养/光周期/饮食/健康状态报告不全

- 类别：ethics_compliance
- 关联判断：**RF-35** ｜ minor ｜ M6 ｜ high ｜ P2/作者。
- 证据包：[EV-036｜sec018 '12–6pm']；[EV-068｜缺失检索：housing/light cycle/diet/SPF｜no_match]

### [minor] CL-036 · 仅雄性、无理由、无 SABV 讨论

- 类别：ethics_compliance
- 关联判断：**RF-36** ｜ minor ｜ M6 ｜ high ｜ P2/领域审稿人（给理由或在 Limitations 明示外推限制）。
- 证据包：[EV-032｜sec003 'Only male animals']；[EV-067｜缺失检索：SABV/female/why males｜no_match]

### [info] CL-037 · 排版缺陷：'As expected27' 裸上标 + 'controla' 拼写

- 类别：production_artifact
- 关联判断：**RF-08** ｜ info ｜ M5 ｜ high ｜ P2/编辑。空引用括号经源 XML 核验为本次转换伪影（早期判断已更正）。
- 证据包：[EV-018｜sec024 ¶1]

### [info] CL-038 · 抗体厂商名个别缺失（ab3611、sc-32233）

- 类别：reagent_traceability_incomplete
- 关联判断：**RF-17** ｜ info ｜ M3 ｜ high。RRID 缺失本身按规则不落 finding；其余抗体报告质量好（含克隆号/FMO/单染对照）。
- 证据包：[EV-039｜sec010]

### [info] CL-039 · 数据可用性经外部核验基本闭合（Dryad 34.26 GB）

- 类别：data_availability_resolved
- 关联判断：**RF-18** ｜ info ｜ M3 ｜ high。WB 原始膜图（Fig3C）、ELISA 原始吸光度、个体水平 CSA/移植计数均已存仓；Fig1B/C 为示意图；全文仅一例 WB。残余：pzfx 逐只值不可核验（SYS-006）。
- 证据包：[EV-048｜Data Availability 原文]；[EV-910｜Dryad API resolved｜2026-08-07｜sha256 3d605f42…]

### [info] CL-040 · 伦理批准合规（IACUC #29-14）

- 类别：ethics_compliance
- 关联判断：**RF-32** ｜ info ｜ M6 ｜ high。ETH-ANI-001 满足。
- 证据包：[EV-033｜sec003]

### [info] CL-041 · CL-04 机制表述 'sponging ligands' 属 hedged 假说，层级合规

- 类别：claim_beyond_evidence
- 关联判断：**RF-40** ｜ info ｜ M7 ｜ high。possibly-hedged C2 假说、锚定外部文献；本研究未测配体/斑块/血管。备查。
- 证据包：[EV-055｜Discussion ¶3]

### [info] CL-042 · 阳性 CSA 主张支撑力备查（选片偏倚+统计不可复核叠加）

- 类别：claim_beyond_evidence
- 关联判断：**RF-41** ｜ info ｜ M7 ｜ medium（SYS-001）。非违规判定；交人工核对 Dryad 原始数据后评估。
- 证据包：[EV-028｜sec006]；[EV-063｜无确切 P]

### [info] CL-043 · 无 Author Contributions 小节（PLOS 政策要求 CRediT）

- 类别：editorial_reporting_gap
- 关联判断：**RF-42** ｜ info ｜ M6 ｜ high。期刊政策缺口，非科学/伦理缺陷。
- 证据包：[EV-062｜缺失检索：Author Contributions/CRediT｜no_match]

## 五、抽取信号

> 本节是机器观察与下游路由轨迹，不是稿件问题，不是稿件 finding，没有 severity，也不直接进入风险分。共 9 条。

- `SIG-602` · `ethics_requirement_unmet`：规范要求 three_rs_consideration/样本量论证，检索确认未报告。目标：ethics.ETH-ANI-002；路由：M6；产出：stage_2。证据：[EV-061]
- `SIG-604` · `partial_extraction`：ETH-ANI-004 适用性事实工具不可自动推出，M6 已用原文补判。路由：M6；stage_2。证据：[EV-065]
- `SIG-605` · `partial_extraction`：ETH-ANI-005 同上，M6 已补判。路由：M6；stage_2。证据：[EV-064]
- `SIG-001` · `sequence_identifier_inconsistent`：bGH-Forward 16 nt，估算 Tm 45.9°C 低于常规（候选级）。路由：M3；stage_2。证据：[EV-029]
- `SIG-002` · `sequence_identifier_inconsistent`：bGH-Reverse GC 62.5%/Tm 48.5°C（候选级）。路由：M3；stage_2。证据：[EV-029]
- `SIG-101` · `sequence_identifier_inconsistent`：'AGER' 书写与小鼠惯例不符（候选，交人工）。路由：M2/M3；stage_2。证据：[EV-010]
- `SIG-102` · `sequence_identifier_inconsistent`：'ItgB7'（候选；与 RF-04 并审）。路由：M2/M3；stage_2。证据：[EV-010]
- `SIG-103` · `sequence_identifier_inconsistent`：'CXCR4' 人类式大写（候选）。路由：M2/M3；stage_2。证据：[EV-010]
- `SIG-X1-HEK` · `external_validation_candidate`：HEK293=Cellosaurus CVCL_0045，resolved，无 problematic flag。路由：M3；stage_3c。证据：[EV-030][EV-902]

## 六、系统限制

> 本节说明系统或输入“哪些地方没看清”。这些条目不是稿件问题，不得据此推断作者遗漏或违规。共 6 条；有受影响目标时，相关“未发现问题”表述一律无效。

- `SYS-001` · figure_unreadable：本次运行主会话与全部子会话均无图像输入能力，Fig 1/2/3（含 S1–S3）无法视觉解读。M5 图内观测、M4 面板结构/个体点核验（RF-19 扩展、RF-22 升级、RF-29 截尾、RF-31 条带）未执行。像素级完整性审计为代码级计算，成功执行且 0 信号（未检出≠无问题，该方法仅覆盖网格对齐重复）。
  - 受影响模块：M4, M5；目标：fig:1, fig:2, fig:3, S1–S3；字段：key_data.KD-001
  - 恢复动作：在具备视觉能力的运行中重新解析；在此之前依赖图内像素的“未发现问题”表述无效。
- `SYS-002` · supplement_inaccessible：S1/S2/S3 Fig（TIF）与 S1 Raw Images（PDF）未随材料提供，仅图注可见；ARRIVE checklist 是否作为附件提交（CAND-16）不可核验。
  - 受影响模块：M5, M6；恢复动作：获取期刊补充材料后复核。
- `SYS-003` · external_source_unavailable：MRG00 ELISA datasheet 特异性/检测范围无法经 X1 核验（无对应端点）；不推断试剂盒无问题或稿件有误。受影响：M3（RF-12）。
- `SYS-004` · external_source_unavailable：50 篇参考文献中 7 篇无 DOI，外部核验（存在性/撤稿）未覆盖；其余 43 篇全部 resolved 且无撤稿。受影响：M2。
- `SYS-005` · parse_failed：KD-001（寿命期 sRAGE 绝对浓度）Stage 3 尝试后因 SYS-001 失败，按契约转 parse_failed。受影响：fig:1A, RF-41 相关。
- `SYS-006` · external_source_unavailable：Dryad 功能学数据以 Prism pzfx 存放，内部是否含逐只原始值不可核验；不推断缺失也不推断已含。受影响：RF-18 残余。

## 七、覆盖率明细

| 子率 | 分子 / 分母（rate） |
| --- | ---: |
| 条件必填字段解析率 | 16/16（1.000） |
| 图表可读率 | 0/3（0.000） |
| 补充材料可得率 | 0/4（0.000） |
| 推荐字段覆盖率（不进加权） | 9/10（0.900） |

- 已解析的条件必填字段：objective.research_question, objective.primary_endpoint, population.subjects, measurement.statistical_methods, claims, design.interventions, design.controls, measurement.assays, design.arms, declarations.ethics_statement, design.randomization（not_reported）, measurement.sample_size_justification（not_reported）, declarations.data_availability, declarations.competing_interests, declarations.funding, declarations.author_contributions（not_reported）
- 未解析的条件必填字段：无
- 不可读图表：fig:1, fig:2, fig:3（SYS-001）
- 不可得补充材料：S1_Fig, S2_Fig, S3_Fig, S1_Raw_Images（SYS-002）

> `not_reported` 表示已完成规定范围检索并确认稿件未报告，属于“已解析”；`parse_failed` 表示系统没读出来，属于“未解析”。两者不得互换。extraction_coverage = 0.60×1.000 + 0.25×0.000 + 0.15×0.000 = **0.600**。

## 八、人工复核建议

优先级固定解释：P0=不先核对就无法可靠解释核心结论/伦理授权/数据完整性（形成审稿结论前完成）；P1=会改变 major finding 的成立或严重度（给出修改要求前完成）；P2=minor/info 的报告澄清（常规修订清单）。同一优先级内按 finding severity 降序、finding id 升序。

### [ ] [P0] 核对 Discussion/标题与 Results 的模型范围矛盾，逐句更正

- 执行者：领域审稿人
- 排序依据：全部 major 且直接阻断核心结论解释。
- 逐 finding 核对包：
  - **RF-01**（major）：Discussion ¶1 与 Results 矛盾。证据：[EV-001][EV-002][EV-003]
  - **XF-01**（major）：'两套系统 similar' vs 年龄对齐数据相反。证据：[EV-004][EV-002][EV-016][EV-052]
  - **RF-02**（major）：标题 diseased 超证据。证据：[EV-005][EV-006][EV-003]
  - **RF-39**（major）：局限回避。证据：[EV-061][EV-069]

### [ ] [P0] 统计重分析包：确切 n、重复测量、2×2 交互、多重校正、确切 P/效应量/CI、样本量依据

- 执行者：统计审稿人
- 排序依据：六条 major 使全文统计推断不可复核。
- 逐 finding 核对包：RF-20 [EV-021][EV-052][EV-015]；RF-21 [EV-061][EV-054]；RF-19 [EV-053][EV-021][EV-024]；RF-23 [EV-025][EV-024]；RF-24 [EV-063][EV-023]；RF-27 [EV-022][EV-023]；RF-25 [EV-016][EV-022]；RF-22 [EV-023][EV-026]

### [ ] [P0] 复核主要终点 CSA 的选片偏倚与个体纤维原始数据

- 执行者：领域审稿人
- 排序依据：全部阳性 CSA 主张的共同基础（major）。
- 逐 finding 核对包：RF-13 [EV-028]；RF-41 [EV-028][EV-063]

### [ ] [P0] 确认移植实验供体细胞身份（ItgB7 vs CD29）与阴性检测灵敏度

- 执行者：领域审稿人
- 排序依据：CL-06 机制结论的证据基础（major）。
- 逐 finding 核对包：RF-04 [EV-010][EV-011]；RF-38 [EV-041][EV-042][EV-010]

### [ ] [P0] 澄清 sRAGE 检测的样本类型、稀释回算与试剂盒特异性

- 执行者：领域审稿人
- 排序依据：核心分组读数方法与表述不符（major）。
- 逐 finding 核对包：RF-12 [EV-027][EV-043][EV-021]

### [ ] [P0] 补充动物福利报告：疼痛操作麻醉/镇痛/人道终点与安乐死方法

- 执行者：伦理委员会
- 排序依据：ETH-ANI-004/005 伦理合规（major）。
- 逐 finding 核对包：RF-33 [EV-065][EV-031][EV-046][EV-047]；RF-34 [EV-064][EV-045]

### [ ] [P0] 收窄治疗外推表述并补齐阴性结论的统计依据

- 执行者：编辑
- 排序依据：面向读者的结论表述（major）。
- 逐 finding 核对包：RF-37 [EV-040][EV-003]；RF-30 [EV-044][EV-041][EV-043][EV-042]

### [ ] [P1] 统一 vehicle 缩写（FFB/FBB）

- 执行者：作者
- 排序依据：major 但可编辑性更正，不阻断核心结论。
- 逐 finding 核对包：RF-03 [EV-007][EV-008][EV-009][EV-013][EV-014]

### [ ] [P1] 完善 Fig 3C WB 面板报告（n/内参/分子量）

- 执行者：领域审稿人
- 排序依据：二级验证面板呈现完整性（major）。
- 逐 finding 核对包：RF-31 [EV-038][EV-039]

### [ ] [P2] 报告澄清与编辑性更正包

- 执行者：作者
- 排序依据：minor/info 报告澄清，不改变当前核心推断。
- 逐 finding 核对包：RF-05 [EV-012]；RF-06 [EV-013][EV-014]；RF-07 [EV-015][EV-016][EV-017]；RF-08 [EV-018]；RF-09 [EV-019][EV-020][EV-050]；RF-10 [EV-010][EV-011]；RF-11 [EV-060][EV-034]；RF-14 [EV-029]；RF-15 [EV-030][EV-902]；RF-16 [EV-031]；RF-26 [EV-026]；RF-28 [EV-035]；RF-29 [EV-036][EV-037]；RF-35 [EV-036][EV-068]；RF-36 [EV-032][EV-067]；RF-42 [EV-062]

---

## 附：候选生命周期台账（39 条候选全部结清）

promoted_to_finding 31 ｜ merged 4 ｜ rejected 3（均附理由：CAND-17 RRID 缺失本身非缺陷；CAND-18 Dryad 外部核验数据已存仓；CAND-22 点值落在范围内非矛盾）｜ blocked_by_system_limitation 1（CAND-16：ARRIVE checklist 附件不可得，SYS-002）｜ unresolved 0。

## 附：运行时遥测

```json
{"runtime_utilization":{
 "child_sessions":13, "child_sessions_interrupted":1, "task_calls":14, "continuations":4,
 "modules_run":["M2","M3","M4","M5","M6","M7"], "modules_skipped":{},
 "references_required":["01","02","03","04","05","06","07"],
 "references_read":["00-contracts","00-routing","00-runtime-contract","01","02","03","04","05","06","07"],
 "routing_recall":1.0, "tool_execution_recall":1.0,
 "candidate_count_discovery":39, "candidate_count_promoted":35,
 "finding_origin_breakdown":{"discovery":20,"multiple":12,"specialist_rule":7,"cross_section_reconciliation":3,"external_validation":1}}}
```

工具终态：figure_integrity_audit=executed（0 信号）；statistical_forensics=executed（5 项 not_applicable）；sequence_identifier_audit=executed（2+3 候选）；normalize_biomed_units=executed（无冲突；vg/mouse、U/mg 未登记）；ethics_compliance_check=executed（1 信号+4 partial）；external_figure_validation=executed（87 查询全部 resolved，0 信号）。

*机器可读完整产物：`review_report.json`、`.review_work/`（discovery.json、structured_result.json、m2–m7_provisional.json、reconciliation.json、evidence_registry.json、全部工具输出）。*
