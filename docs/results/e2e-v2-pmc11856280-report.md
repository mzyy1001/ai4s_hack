# 论文审核报告 · Soluble RAGE enhances muscle regeneration after cryoinjury in aged and diseased mice

> DOI：10.1371/journal.pone.0318754 ｜ 期刊：PLOS ONE ｜ 输入格式：`plain_text`

## 一、执行摘要

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。本 Skill 的任何评分均为筛查信号（screening / triage signal），不构成录用、退稿或发表决定。

### 本报告能回答什么

> 已执行 M2–M7；"未产出 finding"只表示本流程在已取得证据中未检出，不等于论文结论已被证实。

| 执行模式 | submode | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- |
| `full_review` | — | M2、M3、M4、M5、M6、M7 | —（full_review 无跳过） |

- 范围依据：full_review：整篇论文（AAV 基因治疗 + 遗传工程小鼠 + 肌肉损伤再生模型的动物实验），全部六个审核模块依路由开启（M2-M7）。
- 已执行阶段：stage_1、stage_2、stage_3、stage_3b、stage_3c_external_validation、stage_4、stage_5

### 审稿人先看

- 稿件风险筛查分：`100/100`；分段：**major_revision_suggested**（≥50 提示需要实质性修改层面的复核量）。
- 评分边界：分段阈值未经实证验证，是初始经验值，不得表述为自动化的录用/退稿决定。
- findings：96 条（critical 6 / major 45 / minor 36 / info 9）；聚簇后 71 簇；复核动作：P0 6 项、P1 45 项。
- 抽取覆盖率：`0.574`（字段解析 22/23；图像可读 0/6——本环境无图像输入；补充材料可得 0/4——S1-S3 与 PDF 未提供）。不是稿件质量概率。
- 审核置信度：`0.57`。这是未经校准的证据支撑指数，不是 finding 正确概率，也不是稿件质量概率。

### 优先处理（前三项）

- [ ] **[P0] 核对正式稿 Discussion 首段措辞；要求作者提供 年龄×系统×损伤模型 完整结果矩阵并改写该段；确认成年 AAV 阴性是否有任何限定性讨论。**（领域审稿人）
  - 关联判断：M2-001 [critical] Discussion 首段对主结果矩阵的系统性误述
- [ ] **[P0] 人工复核 Fig 3G/H 原图 KO 组数据与显著性标注；要求作者报告 -/-、s/-、+/- 全部基因型结果及 -/- vs s/s 的正式统计检验。**（领域审稿人）
  - 关联判断：M2-002 [critical] Fig 3G 含 knockout 组但 Ager-/- 等基因型冷冻伤结果在 Results 通篇未陈述
- [ ] **[P0] 要求作者报告 Ager-/- vs AGERs/s 头对头比较，或撤下'两套系统相互印证'表述并明确 s 等位基因的双重扰动；要求跨实验归一比较两系统循环 sRAGE 暴露水平。**（领域审稿人）
  - 关联判断：M2-003 [critical] 两套'互补'系统扰动不同构：s 等位基因即全长 RAGE-null

> 其余 P0/P1 动作见第八节；全部 70 条全局审阅（L0）条目的归宿见附录 B。

## 二、结构化结果表

结构化结果版本：`v2`；`stage_3b_executed=True`（图观测因无图像输入未产生，key_data 仅基于正文/图注文本）。

| 字段 | 适用性 / 必填性 | 状态 | 值（摘要） | 原文定位 |
| --- | --- | --- | --- | --- |
| `objective.research_question` | `applicable` / `required` | `reported` | Does soluble RAGE (sRAGE), delivered via AAV9 gene therapy or endogenous Ager-locus genetic modification, enhance ske... | [EV-004｜introduction/¶intro-p4] |
| `objective.hypothesis` | `applicable` / `recommended` | `reported` | Increasing sRAGE levels in the blood and muscle microenvironment boosts muscle recovery after myo-trauma by sequester... | [EV-005｜results/¶results-sec022-p1] |
| `objective.primary_endpoint` | `applicable` / `required` | `reported` | Mean cross-sectional area (CSA) of regenerating (centrally nucleated) muscle fibers at 7 days post injury, quantified... | [EV-006｜methods/¶methods-sec006] |
| `objective.secondary_endpoints` | `applicable` / `recommended` | `reported` | Serum sRAGE kinetics (ELISA), body weight, inverted grid hang time, treadmill endurance, blood glucose, myofiber CSA ... | [EV-007｜figure/¶fig1-caption/Fig 1] |
| `population.subjects` | `applicable` / `required` | `reported` | Male mice only ('Only male animals were included'). Strains: C57BL/6J (Jackson Labs, 2-20 months old stated but oldes... | [EV-008｜methods/¶methods-sec003] [EV-009｜methods/¶methods-sec004] |
| `population.inclusion_criteria` | `applicable` / `required` | `reported` | Male mice, age-matched and sex-matched for each experiment; adult mice 7-8 months, aged 18 months, disease models 2-3... | [EV-008｜methods/¶methods-sec003] |
| `population.exclusion_criteria` | `applicable` / `required` | `not_reported` | — | [EV-010｜缺失检索：methods,results｜no_match] |
| `design.interventions` | `applicable` / `required` | `reported` | Retro-orbital injection of AAV9-sRAGE or formulation buffer vehicle (FFB: 1xPBS, 35mM NaCl and 0.001% Pluronic) at 1e... | [EV-011｜methods/¶methods-sec017] [EV-006｜methods/¶methods-sec006] [EV-002｜methods/¶methods-sec009] |
| `design.controls` | `applicable` / `required` | `reported` | AAV formulation buffer (FFB) vehicle controls for AAV experiments; wild-type littermate/strain controls for disease a... | [EV-011｜methods/¶methods-sec017] |
| `design.randomization` | `applicable` / `required` | `not_reported` | — | [EV-013｜缺失检索：methods｜no_match] |
| `design.allocation_concealment` | `applicable` / `recommended` | `not_reported` | — | [EV-013｜缺失检索：methods｜no_match] |
| `design.blinding` | `applicable` / `required` | `ambiguous` | — | [EV-014｜methods/¶methods-sec006-b] |
| `measurement.assays` | `applicable` / `required` | `reported` | Mouse RAGE Quantikine ELISA (R&D Systems #MRG00) on 50 uL tail-vein blood mixed with 50 uL RIPA buffer (described as ... | [EV-015｜methods/¶methods-sec011] |
| `measurement.statistical_methods` | `applicable` / `required` | `reported` | Two-tailed unpaired t-tests, one-way ANOVA with Tukey post hoc, two-way ANOVA with Tukey post hoc, Mann-Whitney U, Kr... | [EV-016｜methods/¶methods-sec020] |
| `measurement.sample_size_justification` | `applicable` / `required` | `not_reported` | — | [EV-017｜缺失检索：methods,results｜no_match] |
| `measurement.missing_data_handling` | `applicable` / `recommended` | `not_reported` | — | [EV-018｜缺失检索：methods｜no_match] |
| `conclusion.limitations` | `applicable` / `required` | `not_reported` | — | [EV-022｜缺失检索：conclusion,discussion｜no_match] |
| `conclusion.generalization_scope` | `applicable` / `required` | `reported` | Authors generalize from male mice (aged, ApoE-/-) with positive cryoinjury histology at one timepoint to therapeutic ... | [EV-021｜conclusion/¶sec026-p1] |
| `declarations.ethics_statement` | `applicable` / `required` | `reported` | The Harvard University Institutional Animal Care and Use Committee (IACUC) approved all animal protocols used in this... | [EV-023｜methods/¶methods-sec003-b] |
| `declarations.funding` | `applicable` / `required` | `reported` | NIDDK training grant 2T32DK007260 (NH); Paul F. Glenn Medical Foundation and NIH R01AG048917 (AJW); Burroughs Wellcom... | [EV-024｜funding/¶funding-statement1] |
| `declarations.conflict_of_interest` | `applicable` / `required` | `reported` | A.J.W. is a scientific advisor for Kate Therapeutics and Frequency Therapeutics, co-founder and scientific advisory b... | [EV-025｜declarations/¶author-notes] |
| `declarations.data_availability` | `applicable` / `required` | `reported` | The datasets and materials used and analyzed during the current study are available from Dryad repository under acces... | [EV-026｜data_availability/¶notes1] |

| 字段 | 适用性 / 必填性 | 状态 |
| --- | --- | --- |
| `design.blinding` | `applicable` / `required` | `ambiguous`（仅切片分析设盲；其余环节未说明，refs [EV-014｜methods/¶methods-sec006-b]） |

### 核心数据观测组摘要

| 观测组 / 指标 | 上下文 | 状态 | canonical | 报告完整性 / 缺失要素 |
| --- | --- | --- | --- | --- |
| `KD-001` · regenerating_fiber_mean_CSA_aged_cryo_7dpi (`continuous_summary`) | EXP-03·AAV9-sRAGE vs vehicle·7 dpi | `reported` | OBS-001；single_observation | `incomplete`；effect_size、exact_p_value、confidence_interval |
| `KD-002` · regenerating_fiber_mean_CSA_ApoE_cryo_7dpi (`continuous_summary`) | EXP-08·AAV9-sRAGE vs vehicle·7 dpi | `reported` | OBS-002；single_observation | `incomplete`；effect_size、exact_p_value、confidence_interval |
| `KD-003` · regenerating_fiber_mean_CSA_Ager_lines_cryo_7dpi (`continuous_summary`) | EXP-11·transgenic vs wild-type·7 dpi | `reported` | OBS-003；single_observation | `incomplete`；effect_size、exact_p_value、confidence_interval、genotype_result_for_knockout |

> 注：所有定量数值均在图内（本环境无图像输入、且全文无数值型表格），故观测组仅登记方向性文本结论，未产生 pixel/OCR 观测；缺失要素 exact_p_value / effect_size / confidence_interval 等由 M4 findings 承载。

## 三、图表解读与原图定位

> 本节记录只读事实。本环境**无图像输入能力**：figures/ 下 3 张主图 PNG（及降采样副本）存在但无法视觉解读；S1–S3 TIF 与一份无名 (PDF) 未提供。因此不进行图内解读，相关审核基于图注文本与正文交叉比对（见第四节），能力限制见第六节 SYS-001/SYS-002/SYS-006。

| 图 | 文件 | 面板结构（据图注） | 图注声明的统计 |
| --- | --- | --- | --- |
| Fig 1 | figures/pone.0318754.g001.png (+.small.png) | A 寿命 ELISA；B 载体设计；C 方案；D/G sRAGE 动力学；E/F 成年 cryo CSA；H/I 老龄 cryo CSA；J-M 体重/抓网/跑台/血糖 | one-way ANOVA+Tukey (A,D,G)；t test (E,H,J,K,L,M)；Mann-Whitney (F,I)；n≥7 / n=10 |
| Fig 2 | figures/pone.0318754.g002.png (+.small.png) | A-F db/db+WT；G-L ApoE-/-（方案含 WT，数据面板仅 ApoE-null，见 M5-001） | two-way ANOVA (B,C,D)；one-way ANOVA (E,H,I,J)；t test (K)；MW+KW (F,L)；n=6 |
| Fig 3 | figures/pone.0318754.g003.png (+.small.png) | A 基因座示意（s=full-length RAGE-null）；B ELISA；C WB；D 未损伤 CSA；E 方案；F 代表 H&E（3/6 基因型）；G/H cryo CSA；I/J 移植 | one-way ANOVA+Tukey 等（图注在输入中被截断，SYS-006）；n≥5/n=3/n≥3/n≥5 |
| S1-S3 | 未提供（TIF） | BaCl2 损伤各模型（核心阴性证据） | t test/ANOVA/KW（据图注） |

**像素完整性审计（figure_integrity_audit，确定性执行）**：扫描 6 个文件；检出的全部候选重复区块（48+49+209 处）均为每张主图与其 .small.png 降采样副本之间的跨文件比对（r>0.99，预期伪重复）；**未发现任何图内跨面板重复候选**（含 Fig 3F 各基因型 H&E、Fig 3C WB 条带之间）。方法局限：不覆盖旋转/缩放重复（SIG-501/502/503）。

## 四、审核发现

共 96 条 finding（critical 6 / major 45 / minor 36 / info 9），聚簇为 71 簇。簇代表取最高 severity；每条 finding 仅在其所属簇内展开一次。来源标注：global_review（L0 条目直接成案 1）/ specialist_rule / cross_section_reconciliation，详见附录 A。

### [critical] CL-001 · Discussion 首段对主结果矩阵的系统性误述

- 类别：internal_inconsistency、unsupported_claim
- 锚点：¶discussion-sec025-p1；成员：M2-001、M7-002
- 关联判断：
  - **M2-001** [critical] (M2) Discussion 首段对主结果矩阵的系统性误述
    - 详情：Discussion 首段称 'we observed significant increases in the mean fiber sizes 7 days after cryo-injury in adult, aged, and diseased mice ... two complementary animal model systems'，并称两套系统结果相似、'universal importance'。与 Results 三处冲突：(1) 成年（7-8 月龄）AAV 冷冻伤组 CSA 与载体对照无差异（sec022）；(2) db/db 仅趋势不显著（sec023）；(3) 年龄匹配的 7-8 月龄上 AAV 系统阴性而 knock-in 系统阳性（S3 图注确认遗传系为 7-8 月龄），无任何头对头比较支撑 'similar results'。
    - 判断置信度：high；规则：`02-macro-logic#internal_inconsistency`；复核（领域审稿人，P0）：核对正式稿 Discussion 首段措辞；要求作者提供 年龄×系统×损伤模型 完整结果矩阵并改写该段；确认成年 AAV 阴性是否有任何限定性讨论。
    - 证据：[EV-030｜discussion/¶discussion-p1] [EV-031｜results/¶results-sec022-p3] [EV-032｜results/¶results-sec023-p1] [EV-033｜results/¶results-sec024] [EV-058｜supplement/¶s3-caption]
  - **M7-002** [critical] (M7) Discussion 首段宣称成年/老龄/疾病小鼠在两套系统中均出现显著纤维增大，与自身成年 AAV 阴性数据方向相反
    - 详情：Discussion 首段断言 'significant increases ... in adult, aged, and diseased mice ... two complementary animal model systems'。但 Results 明确写成年 AAV 组与对照 CSA 'similar'（CL-03）；db/db 仅 trend 未达显著；遗传系统只在健康成年鼠测试、未在老龄/疾病鼠测试。该主张在成年 AAV 臂的直接支撑方向相反、在疾病臂无显著支撑，而它是 Discussion 中心结论句。与 M2-001 同一锚点（内部一致性 + 主张-证据对齐两个维度），聚簇处理。
    - 判断置信度：high；规则：`07-conclusions-discussion#unsupported_claim`；复核（领域审稿人，P0）：核对 Fig 1E（成年 AAV 臂）组间差异方向与显著性标记；确认 Discussion 首段是否有任何限定词覆盖 adult AAV 臂。
    - 证据：[EV-030｜discussion/¶discussion-p1] [EV-031｜results/¶results-sec022-p3] [EV-032｜results/¶results-sec023-p1]

### [critical] CL-002 · Fig 3G 含 knockout 组但 Ager-/- 等基因型冷冻伤结果在 Results 通篇未陈述

- 类别：methods_results_gap、caption_not_self_contained
- 锚点：Fig Fig 3G／¶results-sec024；成员：M2-002、M5-009、M5-015
- 关联判断：
  - **M2-002** [critical] (M2) Fig 3G 含 knockout 组但 Ager-/- 等基因型冷冻伤结果在 Results 通篇未陈述
    - 详情：Methods sec003 承诺 6 种基因型；Fig 3G 图注明写数据含 'wild-type, knockout and transgenic mice' 且已按 one-way ANOVA+Tukey 分析；但 Results sec024 只描述 AGERs/s 与 s/+ 相对 WT 的 ~30% CSA 增加，对 Ager-/-、s/-、+/- 的冷冻伤结果零陈述；Discussion p4 却对 KO 表型下结论（'未能复现再生延迟'）。缺失的恰是唯一能解除 'sRAGE 升高 vs 全长 RAGE 缺失' 混杂的比较（-/- vs s/s）。
    - 判断置信度：high；规则：`02-macro-logic#methods_results_gap`；复核（领域审稿人，P0）：人工复核 Fig 3G/H 原图 KO 组数据与显著性标注；要求作者报告 -/-、s/-、+/- 全部基因型结果及 -/- vs s/s 的正式统计检验。
    - 证据：[EV-033｜results/¶results-sec024] [EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-083｜缺失检索：results｜no_match] [EV-036｜discussion/¶discussion-p4]
  - **M5-009** [minor] (M5) AGERs/- 与 +/- 基因型结果在 Results 中从未描述，图注以 'indicated genotypes' 含糊带过
    - 详情：Fig 3 B/D/G/H/I/J 均写 'indicated genotypes' 而未枚举；Results sec024 通篇只描述 s/s 与 s/+（加 WT）。s/- 是检验 sRAGE 剂量逻辑的关键基因型（高 sRAGE 且无全长 RAGE 的单倍剂量对照），其缺失削弱 ELISA 与移植面板的可解释性。
    - 判断置信度：medium；规则：`05-figures-and-charts#caption_not_self_contained`；复核（作者，P2）：说明各面板实际包含的基因型并补描述 s/-、+/- 结果。
    - 证据：[EV-033｜results/¶results-sec024] [EV-034｜figure/¶fig3-caption-full/Fig 3]
  - **M5-015** [minor] (M5) Fig 3 图注 'indicated genotypes' 从未枚举，图注不自足
    - 详情：Fig 3 B/D/G/H/I/J 均以 'indicated genotypes' 指代分组但图注未列清单（Methods sec003 共 6 种基因型）；正文提示 D 可能仅含 WT、s/+、s/s 而 G-J 范围不明，脱离图像无法确认。图注亦未说明移植后分析时点（Methods sec009 为 3 周）。
    - 判断置信度：high；规则：`05-figures-and-charts#caption_not_self_contained`；复核（作者，P2）：图注应枚举各面板基因型并补移植分析时点。
    - 证据：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-002｜methods/¶methods-sec009]

### [critical] CL-003 · 两套'互补'系统扰动不同构：s 等位基因即全长 RAGE-null

- 类别：design_analysis_disconnect、abstract_main_text_inconsistency
- 锚点：Fig Fig 3A／¶abstract；成员：M2-003
- 关联判断：
  - **M2-003** [critical] (M2) 两套'互补'系统扰动不同构：s 等位基因即全长 RAGE-null
    - 详情：摘要/引言/讨论把遗传系统表述为对'提高 sRAGE'假设的独立验证，但 Fig 3A 图注自述 s 等位基因 'is a full-length RAGE-null'：AGERs/s 相对 AAV 系统叠加了第二个扰动（膜型 RAGE 完全缺失），而论文自己在 Discussion p4 引文献承认全长 RAGE 为损伤后干细胞激活所需。两系统检验的不是同一假设；又因 Ager-/- 对照结果缺失（M2-002），遗传臂阳性无法归因于 sRAGE。另：两套系统循环 sRAGE 水平从未同标尺直接定量比较（原 G-61），'结果相似'缺暴露可比性。
    - 判断置信度：high；规则：`02-macro-logic#design_analysis_disconnect`；复核（领域审稿人，P0）：要求作者报告 Ager-/- vs AGERs/s 头对头比较，或撤下'两套系统相互印证'表述并明确 s 等位基因的双重扰动；要求跨实验归一比较两系统循环 sRAGE 暴露水平。
    - 证据：[EV-035｜figure/¶fig3A-caption/Fig 3A] [EV-041｜abstract/¶abstract-p1] [EV-036｜discussion/¶discussion-p4] [EV-063｜methods/¶methods-sec003-c]

### [critical] CL-004 · 标题/摘要的 'accelerates/enhances regeneration' 仅由单一 7 dpi 时间点、单一偏倚取样的 CSA 终点支撑

- 类别：claim_beyond_evidence
- 锚点：¶methods-sec006；成员：M7-001
- 关联判断：
  - **M7-001** [critical] (M7) 标题/摘要的 'accelerates/enhances regeneration' 仅由单一 7 dpi 时间点、单一偏倚取样的 CSA 终点支撑
    - 详情：全文所有再生终点只在冷冻伤后第 7 天测量一次，且唯一终点是'最靠近损伤、中心核纤维最多'切片的中心核纤维平均 CSA（sec006，取样偏向再生最佳区域）。无再生时间序列、无中心核比例/再生区面积/eMyHC 等成熟度指标、无损伤后功能恢复数据。7 dpi CSA 偏大同样可由损伤程度差异、炎症/水肿或肥大解释，不能唯一推出'更快再生'这一时间过程结论。标题与摘要把单点静态测量写成动力学过程主张，属时间窗+终点双轴外推，是全文主要结论。
    - 判断置信度：high；规则：`07-conclusions-discussion#claim_beyond_evidence`；复核（领域审稿人，P0）：复核 Fig 1E/1H、Fig 2E/2K、Fig 3G 是否仅提供 7 dpi 单点 CSA；确认全文无任何时间序列或再生指数数据；评估 'accelerates' 是否可改为 'larger regenerating fibers at 7 dpi'。
    - 证据：[EV-006｜methods/¶methods-sec006] [EV-042｜title/¶title-p1] [EV-041｜abstract/¶abstract-p1]

### [critical] CL-005 · Cryoinjury 未标准化且组织学取样规则偏向再生最佳区域

- 类别：quantification_criteria_undefined
- 锚点：¶methods-sec006；成员：M3-001
- 关联判断：
  - **M3-001** [critical] (M3) Cryoinjury 未标准化且组织学取样规则偏向再生最佳区域
    - 详情：sec006 将 cryoinjury 仅定义为 'pressing a cold (cooled in dry-ice) flat metal rod to the muscle for 10 seconds'：金属棒材质/直径/接触面积、预冷温度验证、术后监测均未给出；无任何早期时间点损伤面积/坏死程度量化以确立组间等效性。取样规则进一步引入系统性偏倚：每张切片选 'the section showing the most centrally nucleated fibers nearest to the injury'、4 个 'adjacent to the largest areas of injury' 视野，即固定选取再生最好的区域；核心读数（平均 CSA）未对损伤面积归一化。切片分析盲法是唯一有效控制，不能抵消选择偏倚。
    - 判断置信度：high；规则：`03-experimental-methods#quantification_criteria_undefined`；复核（领域审稿人，P0）：复核 Fig 1/2/3 与 S1-S3 H&E 各组损伤区横截面积是否可比；要求作者提供金属棒规格、预冷标准化程序及损伤面积量化数据。
    - 证据：[EV-006｜methods/¶methods-sec006]

### [major] CL-006 · 移植机制结论建立在 sRAGE 无效背景上的 null result

- 类别：design_analysis_disconnect、missing_control、claim_beyond_evidence
- 锚点：¶results-sec024-p3；成员：M2-004、M7-006、M3-022
- 关联判断：
  - **M2-004** [major] (M2) 移植机制结论建立在 sRAGE 无效背景上的 null result
    - 详情：sec024 末段由移植 null result 推出 'sRAGE production in the micro-environment is likely key'。受体为 BaCl2 预损伤的 mdx——正是本文三个系统一致证明 sRAGE 完全无效的背景；六个基因型（含不产 sRAGE 的 -/-）engraftment 相同且无阳性对照；该结论从未在 cryoinjury（唯一阳性背景）中检验；且缺未移植 mdx 对照界定背景 dystrophin+ 纤维。
    - 判断置信度：high；规则：`02-macro-logic#design_analysis_disconnect`；复核（领域审稿人，P1）：要求作者在 cryoinjury 背景或同基因型受体中提供阳性对照数据与未移植对照，否则将'微环境是关键'降级为推测。
    - 证据：[EV-062｜results/¶results-sec024-p3] [EV-002｜methods/¶methods-sec009] [EV-038｜discussion/¶discussion-p5] [EV-056｜supplement/¶s1-caption]
  - **M7-006** [major] (M7) 移植 null result 推导微环境机制：无效背景、无 CI、RAGE 缺失混杂
    - 详情：sec024/结论前收束句：'did not differ ... sRAGE production in the micro-environment is likely key'。三重问题：(1) 受体为 BaCl2 预损伤——sRAGE 在全部 BaCl2 背景无效，在干预不生效的背景下做定位实验不能区分细胞内/外作用；(2) 'did not differ' 是不显著结果被读作无差异命题，无 CI、无预设等效界；(3) 供体基因型并非只改变 sRAGE：s/s、s/- 同时缺失全长 RAGE，'各基因型 engraft 相同'无法归因于 sRAGE。另若缺未移植对照成立，则该 claim 唯一直接支撑计量本身存疑。讨论中措辞为 likely/suggest（hedged），故不升 critical。
    - 判断置信度：high；规则：`07-conclusions-discussion#claim_beyond_evidence`；复核（领域审稿人，P1）：核对 Fig 3I/J 数据分布与变异度、是否存在未移植 mdx 对照的 background dystrophin+ 计数；评估 'microenvironment likely key' 是否需降为'不排除'表述。
    - 证据：[EV-062｜results/¶results-sec024-p3] [EV-002｜methods/¶methods-sec009] [EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-035｜figure/¶fig3A-caption/Fig 3A]
  - **M3-022** [major] (M3) 移植实验缺 mdx 未移植对照以界定背景 dystrophin+ 纤维
    - 详情：移植终点为 mdx 受体 TA 中 dystrophin+ 纤维计数，但未报告 mdx 未移植（及/或仅预损伤）对照组：mdx 随年龄累积 revertant dystrophin+ 纤维，受体鼠年龄/体重在 sec009 中完全未指明，背景水平无法估计与扣除。
    - 判断置信度：medium；规则：`03-experimental-methods#missing_control`；复核（作者，P1）：确认正式稿/补充材料是否包含未移植对照数据；要求补充受体鼠年龄。
    - 证据：[EV-089｜缺失检索：methods,results｜no_match] [EV-002｜methods/¶methods-sec009]

### [major] CL-007 · 标题/摘要选择性报告：阴性模型未披露、'diseased' 无限定

- 类别：abstract_main_text_inconsistency、selective_result_interpretation
- 锚点：¶abstract；成员：M2-005、M7-003
- 关联判断：
  - **M2-005** [major] (M2) 标题/摘要选择性报告：阴性模型未披露、'diseased' 无限定
    - 详情：论文并列测试三种疾病/状态背景，Results 中 db/db 冷冻伤仅趋势不显著、BaCl2 阴性；标题 'in aged and diseased mice' 与摘要只呈现阳性模型（aged、ApoE-/-），未披露糖尿病模型阴性与成年 AAV 阴性；对遗传系统的描述 'to favor production of sRAGE over transmembrane RAGE' 未披露 s 等位基因同时是全长 RAGE-null。
    - 判断置信度：high；规则：`02-macro-logic#abstract_main_text_inconsistency`；复核（编辑，P1）：摘要补入糖尿病模型阴性与成年 AAV 阴性；标题对 diseased 加限定（atherosclerotic）；核对正式稿是否已有修订。
    - 证据：[EV-042｜title/¶title-p1] [EV-041｜abstract/¶abstract-p1] [EV-032｜results/¶results-sec023-p1] [EV-031｜results/¶results-sec022-p3] [EV-035｜figure/¶fig3A-caption/Fig 3A]
  - **M7-003** [major] (M7) Discussion/Conclusion 以一律阳性口径概括结果，未披露成年 AAV、db/db、全部 BaCl2 臂的阴性结果
    - 详情：论文自身结果矩阵高度异质：成年 AAV 冷冻伤阴性、db/db 冷冻伤不显著、全部 BaCl2 臂均阴性。但 Discussion 首段 'That both genetic systems gave similar results highlight the universal importance of sRAGE'、Conclusion 'Our study demonstrates that... sRAGE also can serve as an accelerator of regeneration'，均未披露上述相反/阴性观察。'universal/similar results' 类全称命题存在多条可定位反例。
    - 判断置信度：high；规则：`07-conclusions-discussion#selective_result_interpretation`；复核（领域审稿人，P1）：确认 Discussion 任何段落是否披露成年 AAV 与 db/db 阴性结果；核对 'universal importance' 是否仍有保留价值。
    - 证据：[EV-030｜discussion/¶discussion-p1] [EV-021｜conclusion/¶sec026-p1] [EV-032｜results/¶results-sec023-p1] [EV-031｜results/¶results-sec022-p3]

### [major] CL-009 · microenvironment 是全文从未测量的对象

- 类别：conclusion_overreach
- 锚点：¶abstract；成员：M2-007
- 关联判断：
  - **M2-007** [major] (M2) microenvironment 是全文从未测量的对象
    - 详情：摘要结论句 'alter the skeletal muscle microenvironment'、Discussion p2/p5 的微环境机制均以肌肉局部 sRAGE 为对象，但全文所有 ELISA 均为血液样本（实为 RIPA 裂解全血）；载体特意加入 miR122t 抑制肝脏表达而肝脏是循环 sRAGE 主要来源之一；Methods sec011 描述了组织 ELISA 流程但无任何组织结果报告。结论对象在研究中未测，属形式层面的结论跳跃。
    - 判断置信度：high；规则：`02-macro-logic#conclusion_overreach`；复核（领域审稿人，P1）：要求提供肌肉/肝脏组织 sRAGE 或转基因表达数据；否则将 microenvironment 表述降级为推测。
    - 证据：[EV-041｜abstract/¶abstract-p1] [EV-043｜methods/¶methods-sec011-b] [EV-085｜缺失检索：results｜no_match] [EV-044｜methods/¶methods-sec013]

### [major] CL-010 · 'Serum sRAGE' 实为 RIPA 裂解尾静脉全血，样本类型与全文表述不符

- 类别：endpoint_proxy_questionable
- 锚点：¶methods-sec011；成员：M3-002
- 关联判断：
  - **M3-002** [major] (M3) 'Serum sRAGE' 实为 RIPA 裂解尾静脉全血，样本类型与全文表述不符
    - 详情：全文图注与结果均称 'serum sRAGE'，但 sec011 的样本是 50 μL 尾静脉血 + 50 μL RIPA buffer（裂解全血而非血清）。RIPA 会把血细胞膜结合型/胞内 RAGE 溶解进入样本，污染循环 sRAGE 定量；血细胞组成差异（年龄、db/db、ApoE-/-、Ager 基因型）成为未控制的混杂。该读数是全部 AAV 实验转基因诱导的首要验证终点，构造效度受损。
    - 判断置信度：high；规则：`03-experimental-methods#endpoint_proxy_questionable`；复核（领域审稿人，P1）：要求作者澄清样本类型并说明裂解全血中膜型 RAGE 的贡献；确认图中 'serum sRAGE' 单位与计算基准。
    - 证据：[EV-043｜methods/¶methods-sec011-b] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [major] CL-011 · ELISA（Quantikine MRG00）无方法学确证

- 类别：method_reporting_incomplete
- 锚点：¶methods-sec011；成员：M3-003
- 关联判断：
  - **M3-003** [major] (M3) ELISA（Quantikine MRG00）无方法学确证
    - 详情：sec011 未报告：试剂盒对 sRAGE vs 全长/膜型 RAGE 的特异性验证（RIPA 全血裂解基质中尤为关键）；标准曲线与样本基质不匹配且无 spike-recovery/平行性数据；BCA 定量后未说明按蛋白还是按体积上样；检测线性范围未给出；转基因 sRAGE 异构体未定义加剧特异性风险。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（领域审稿人，P1）：核对 R&D MRG00 说明书标准品身份与基质耐受性；要求作者提供回收率/稀释线性数据及上样归一化方式。
    - 证据：[EV-043｜methods/¶methods-sec011-b] [EV-044｜methods/¶methods-sec013]

### [major] CL-012 · 全文无随机化描述；多窝来源未作区组/统计因子处理

- 类别：study_design_randomization、random_assignment_missing、statistical_assumption
- 锚点：¶methods-sec003；成员：M6-001、M3-026、M4-008
- 关联判断：
  - **M6-001** [major] (M6) 全文无随机化描述；多窝来源未作区组/统计因子处理
    - 详情：全文检索 random/randomization/randomly 零命中：小鼠分配到 AAV9-sRAGE vs vehicle、各基因型组、各疾病模型组的方式均未说明（ARRIVE 2.0 Item 12）。sec003/sec004 自述多窝混用，但统计方法未将 litter 作为区组、随机效应或统计因子，窝效应可能膨胀假阳性。
    - 判断置信度：high；规则：`06-ethics-compliance#study_design_randomization`；复核（伦理委员会，P1）：向作者索取分组随机化方法与各实验 litter 来源数及是否按 litter 分层/入模型；若无法补充，要求在 Limitations 中声明。
    - 证据：[EV-013｜缺失检索：methods｜no_match] [EV-008｜methods/¶methods-sec003] [EV-016｜methods/¶methods-sec020]
  - **M3-026** [minor] (M3) 全部体内实验未报告分组随机化
    - 详情：AAV vs vehicle、损伤组、移植受体、基因型队列的分组随机化方法均未描述；仅报告切片分析盲法。ARRIVE 报告维度见 M6-001。
    - 判断置信度：high；规则：`03-experimental-methods#random_assignment_missing`；复核（作者，P2）：补充分组随机化方法或在 Limitations 中声明。
    - 证据：[EV-013｜缺失检索：methods｜no_match] [EV-011｜methods/¶methods-sec017]
  - **M4-008** [minor] (M4) 遗传学比较未控制窝别（litter）聚类
    - 详情：sec003/sec004 明确队列 'regularly consisted of mice from multiple litters'，Fig 3 各基因型组间比较（ELISA、CSA、移植）未将窝别作为随机效应或协变量，也未说明是否使用同窝对照；基因型在不同窝间分布不均时可产生窝别混杂。属风险证据而非已证实错误。
    - 判断置信度：medium；规则：`04-statistics#statistical_assumption`；复核（统计审稿人，P2）：向作者索取每只鼠的窝别归属；若基因型-窝别部分混杂，用含窝别随机效应的模型复核 Fig 3 结论。
    - 证据：[EV-008｜methods/¶methods-sec003] [EV-059｜methods/¶methods-sec004-b]

### [major] CL-013 · 设盲仅限组织切片分析，手术/注射操作者与功能学评估者未设盲

- 类别：study_design_blinding
- 锚点：¶methods-sec006；成员：M6-002
- 关联判断：
  - **M6-002** [major] (M6) 设盲仅限组织切片分析，手术/注射操作者与功能学评估者未设盲
    - 详情：全文 blinded/blinding 仅命中 sec006 一处（'Slides were coded'）。实施 cryoinjury、BaCl2 注射、AAV retro-orbital 注射的操作者，以及抓网计时、跑台记录、血糖、体重等功能/代谢终点评估者是否设盲均未说明（ARRIVE 2.0 Item 11）；上述终点均为主观或半主观测量。
    - 判断置信度：high；规则：`06-ethics-compliance#study_design_blinding`；复核（伦理委员会，P1）：向作者索取各操作与功能终点评估的设盲状态；若未设盲，要求评估对主要终点（老龄鼠 CSA、grid hang、treadmill、血糖）的潜在影响。
    - 证据：[EV-014｜methods/¶methods-sec006-b] [EV-080｜缺失检索：methods｜no_match] [EV-047｜methods/¶methods-sec018]

### [major] CL-014 · 仅用雄性小鼠且无单性别理由，未讨论 sex as a biological variable

- 类别：ETH-ANI-003
- 锚点：¶methods-sec003；成员：M6-003
- 关联判断：
  - **M6-003** [major] (M6) 仅用雄性小鼠且无单性别理由，未讨论 sex as a biological variable
    - 详情：sec003: 'Only male animals were included.'；sec004 同样仅纳入雄性；全文 female 零命中、无单性别理由；Discussion 未涉及 SABV。本研究 NIH 资助（SABV 政策适用），PLOS ONE 亦要求说明单性别设计理由；结论向 'aged and diseased mice' 与治疗外推时未作性别限定。工具层 ETH-ANI-003 'passed' 仅指基本要素已列出，不覆盖单性别无理由这一报告完整性问题。
    - 判断置信度：high；规则：`06-ethics-compliance#ETH-ANI-003`；复核（伦理委员会，P1）：要求作者补充单性别设计理由，并在 Discussion 中明确结论限于雄性、雌性反应待验证。
    - 证据：[EV-008｜methods/¶methods-sec003] [EV-079｜缺失检索：discussion,methods｜no_match] [EV-059｜methods/¶methods-sec004-b]

### [major] CL-015 · 多处有创操作的麻醉/镇痛未报告（报告缺口，非确认性福利违反）

- 类别：ETH-ANI-004
- 锚点：¶methods-sec006；成员：M6-004、M3-024
- 关联判断：
  - **M6-004** [major] (M6) 多处有创操作的麻醉/镇痛未报告（报告缺口，非确认性福利违反）
    - 详情：动物合规工具检出 surgery 伴 anesthesia=null（severity_hint critical），M6 人工定性：这是'部分操作有麻醉（sec017 retro-orbital：isoflurane + 眼部护理），而 cryoinjury 皮肤切口+干冰冷压（sec006）、50 μL BaCl2 肌注（sec006）、25 μL BaCl2 预损伤与细胞注射（sec009）无麻醉/镇痛报告'。不升 critical：报告缺失≠实际未给予，IACUC #29-14 批准依 PHS Policy/NRC Guide 可推定方案层面有麻醉计划；问题性质是 ETH-ANI-004/ARRIVE 报告义务未满足。升级条件：作者确认未给予时改 critical。
    - 判断置信度：high；规则：`06-ethics-compliance#ETH-ANI-004`；复核（伦理委员会，P1）：向作者逐项索取 cryoinjury/BaCl2 肌注/移植注射的麻醉与术后镇痛方案（或引证 #29-14 方案内容）；若实际已用而漏写，要求修订 Methods。
    - 证据：[EV-006｜methods/¶methods-sec006] [EV-002｜methods/¶methods-sec009] [EV-011｜methods/¶methods-sec017] [EV-076｜缺失检索：methods｜no_match]；工具信号：SIG-702、SIG-604
  - **M3-024** [minor] (M3) 损伤与移植操作的麻醉/镇痛未描述
    - 详情：sec006 的 BaCl2 TA 注射与 cryoinjury 皮肤切开、sec009 的预损伤与细胞注射均未说明麻醉与镇痛（仅 sec017 眶后注射提及 isoflurane）；造模麻醉剂种类未指明，无法评估对再生读数的潜在影响。伦理合规维度见 M6-004。
    - 判断置信度：high；规则：`03-experimental-methods#intervention_underspecified`；复核（作者，P2）：补充各操作的麻醉/镇痛方案。
    - 证据：[EV-006｜methods/¶methods-sec006] [EV-002｜methods/¶methods-sec009] [EV-076｜缺失检索：methods｜no_match]

### [major] CL-016 · 安乐死方法缺失；无退出/排除标准、剔除数与人道终点

- 类别：ETH-ANI-005
- 锚点：¶methods-sec006；成员：M6-005
- 关联判断：
  - **M6-005** [major] (M6) 安乐死方法缺失；无退出/排除标准、剔除数与人道终点
    - 详情：全文 euthan* 仅命中 sec006 'mice were euthanized' 且无方法；sec007/sec009 取材处死连 euthanized 字样均未出现。无退出/排除标准、无剔除数、无人道终点（humane endpoint/moribund/weight loss threshold 零命中），而 18 月龄老龄鼠接受皮肤切口手术、retro-orbital 注射与跑台力竭测试。不满足 AVMA 2020/ARRIVE 2.0 Item 5、15 与 PLOS ONE 动物报告要求。工具 SIG-605 partial 已由全文证据覆盖。
    - 判断置信度：high；规则：`06-ethics-compliance#ETH-ANI-005`；复核（伦理委员会，P1）：向作者索取安乐死方法、死亡/剔除动物数及原因、预设人道终点与术后监测频率（尤其老龄组）；请编辑核对 IACUC #29-14 方案是否涵盖上述要素。
    - 证据：[EV-074｜缺失检索：methods｜no_match] [EV-006｜methods/¶methods-sec006] [EV-081｜缺失检索：methods,results｜no_match]；工具信号：SIG-605

### [major] CL-017 · 无样本量依据；图注以 'n≥' 报告，实际组内 n 不可知

- 类别：power_and_sample_size
- 锚点：¶methods-sec020；成员：M4-002
- 关联判断：
  - **M4-002** [major] (M4) 无样本量依据；图注以 'n≥' 报告，实际组内 n 不可知
    - 详情：全文无任何样本量估算/功效/精度依据。Fig 1 D/E/F（n≥7）、Fig 3 B（n≥5）、G/H（n≥3）、I/J（n≥5）、S1（n≥7）、S3（n≥3）均以不等式报告 n，无法得知各组实际样本量，'≥' 暗示未说明的动物删减或亚组选取。Fig 3 六基因型 n≥3/组却同时支撑阳性（~30% 增大）与阴性（KO、移植）双向确证性结论。
    - 判断置信度：high；规则：`04-statistics#power_and_sample_size`；复核（统计审稿人，P1）：向作者索取逐组实际 n 与删减原因；对 Fig 3 阳性与阴性结论做功效/精度复核（报告效应量与 CI 后判断 n=3-5 能排除的最小效应）。
    - 证据：[EV-017｜缺失检索：methods,results｜no_match] [EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [major] CL-018 · 移植细胞身份矛盾：Methods CD29+ vs 图注 ItgB7+

- 类别：flow_break、internal_inconsistency、figure_terminology_inconsistency
- 锚点：Fig Fig 3I/J／¶methods-sec007；成员：M3-004、M2-009、M5-014、M3-025
- 关联判断：
  - **M3-004** [major] (M3) 移植细胞身份矛盾：Methods CD29+ vs 图注 ItgB7+
    - 详情：sec007 将卫星细胞定义为 CD29+（β1-integrin，克隆 HMβ1-1），panel 中不含任何 anti-integrin-β7 试剂；Fig 3I/3J 图注却写 'ItgB7+'。序列标识符审计确认 'ItgB7' 不符合小鼠命名惯例（应为 Itgb7）。无论命名笔误还是分子身份错误，所指 integrin β7 均与 Methods 定义的 CD29（Itgb1）为不同分子，所描述的分选无法产出该群体；移植实验输入细胞身份无法确认。
    - 判断置信度：high；规则：`03-experimental-methods#flow_break`；复核（领域审稿人，P1）：向作者索取移植细胞分选门控记录与 re-analysis 结果，确认实际使用的阳性标记（CD29/Itgb1 vs Itgb7）。
    - 证据：[EV-045｜methods/¶methods-sec007] [EV-034｜figure/¶fig3-caption-full/Fig 3]；工具信号：SIG-803
  - **M2-009** [major] (M2) Fig 3I/J 移植细胞标记（ItgB7+）与 Methods 门控定义（CD29+）冲突
    - 详情：Fig 3I/J 图注称移植 MuSC 为 'ItgB7+'，Methods sec007 定义为 CD29+（β1-Integrin，克隆 HMβ1-1），且抗体面板中根本没有 integrin β7 试剂。Itgb7 与 Itgb1 是不同基因；图注所述分选群体与 Methods 门控及试剂清单不能同时成立，移植物细胞身份产生实际映射歧义。
    - 判断置信度：high；规则：`02-macro-logic#internal_inconsistency`；复核（领域审稿人，P1）：核对 Fig 3 原图面板标注与 Dryad 源数据，确认实际分选标记（CD29 vs ItgB7）并更正图注或 Methods。
    - 证据：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-045｜methods/¶methods-sec007]
  - **M5-014** [major] (M5) Fig 3I/J 图注门控标记 'ItgB7+' 与 Methods 定义的 CD29（β1-integrin）冲突
    - 详情：Fig 3 I/J 图注将移植 MuSC 门控写为 'ItgB7+'，而 Methods sec007 定义为 CD29+（β1-Integrin，克隆 HMβ1-1），抗体清单中只有 anti-CD29-APC-Cy7，无任何 β7-integrin 抗体。Itgb7 与 Itgb1 是不同基因：若为图注笔误（应为 Itgb1/CD29）需更正；若确用 β7 则与 Methods 分选定义实质冲突，直接影响移植面板（核心证据 I/J）的细胞身份。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_terminology_inconsistency`；复核（领域审稿人，P1）：核对分选记录与抗体（HMβ1-1 为 anti-CD29）；更正图注 ItgB7→CD29/Itgb1 或修正 Methods。
    - 证据：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-045｜methods/¶methods-sec007]
  - **M3-025** [minor] (M3) 流式报告要素不全：采集事件数、门控图与补偿细节缺失
    - 详情：sec007 报告了完整 panel、live/dead 门控与单色/FMO 对照（符合规范），但未报告采集事件数、补偿方案，无门控策略图，无法复核 'CD11b-...CD29+CXCR4+' 门的设定（与 M3-004 联动）。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（作者，P2）：补充门控策略图与采集事件数。
    - 证据：[EV-045｜methods/¶methods-sec007]

### [major] CL-019 · 唯一显著的功能/代谢结果（老龄血糖下降，Fig 1M）在 Discussion 完全缺席；与 db/db 血糖无改善的矛盾未调和

- 类别：selective_result_interpretation、significance_overstated
- 锚点：Fig Fig 1M／¶results-sec022-p3；成员：M7-009、M7-010
- 关联判断：
  - **M7-009** [major] (M7) 唯一显著的功能/代谢结果（老龄血糖下降，Fig 1M）在 Discussion 完全缺席；与 db/db 血糖无改善的矛盾未调和
    - 详情：Results sec022 报告老龄鼠 sRAGE-AAV 组 'significant reduction in serum glucose levels'（Fig 1M，体重/力量/耐力均无差异情况下唯一显著的功能/代谢终点）。Discussion p3 通篇讨论 RAGE 与胰岛素抵抗文献并推测 sRAGE 改善胰岛素抵抗，却只字不提自己的 Fig 1M 数据，也不提 db/db 血糖不降（Fig 2D，Results 明确 'elevating sRAGE does not reverse the increase in blood glucose'）——同一论文内方向相反的自身代谢观察未披露或调和。另：血糖测定未说明空腹/时间点，'serum glucose' 实为全血 glucometer 读数（方法学部分归 M3）。
    - 判断置信度：high；规则：`07-conclusions-discussion#selective_result_interpretation`；复核（领域审稿人，P1）：核对 Fig 1M 与 Fig 2D 效应方向与显著性标记（本环境无图像）；确认 Discussion 任何位置是否提及血糖数据；要求作者调和两处矛盾观察。
    - 证据：[EV-065｜results/¶results-sec022-p4] [EV-032｜results/¶results-sec023-p1] [EV-039｜discussion/¶discussion-p3] [EV-084｜缺失检索：discussion｜no_match]
  - **M7-010** [major] (M7) Fig 1M 血糖'显著下降'被无保留地写成确证性发现，未提多终点未校正的假阳性风险
    - 详情：Results：'...did exhibit a significant reduction in serum glucose levels ... it can ... modulate glucose metabolism in aging skeletal muscle'。血糖是 4 个并列功能/代谢终点之一（全文未指定主要终点），M4-004 已指出多终点未校正、假阳性风险及全文无精确 P 值/效应量。该 secondary 终点以确证性口径进入结论性语句。
    - 判断置信度：medium；规则：`07-conclusions-discussion#significance_overstated`；复核（统计审稿人，P1）：与 M4-004 核对同一分析锚点；若 Fig 1M 报告精确 P 值与效应量/CI（图中），请人工读取确认；要求作者以校正后口径表述。
    - 证据：[EV-065｜results/¶results-sec022-p4] [EV-016｜methods/¶methods-sec020]

### [major] CL-020 · CSA 纤维分布检验以纤维为分析单元，忽略同鼠聚集（伪重复）

- 类别：replication_independence
- 锚点：¶methods-sec006；成员：M4-001
- 关联判断：
  - **M4-001** [major] (M4) CSA 纤维分布检验以纤维为分析单元，忽略同鼠聚集（伪重复）
    - 详情：处理在小鼠层级分配，但 Figs 1F/1I、2F/2L、3H 及 S1C/F、S2C/F、S3C 的纤维 CSA 分布用 Mann-Whitney/Kruskal-Wallis 比较多只小鼠 pooled 的纤维，未报告每鼠纤维数，也未用混合效应模型或按鼠汇总。纤维层级 n 远大于鼠数，有效样本量被放大，p 值系统性偏小；统计单元从未被明确声明。
    - 判断置信度：high；规则：`04-statistics#replication_independence`；复核（统计审稿人，P1）：若取得 Dryad 数据，按鼠汇总纤维 CSA 或以鼠为随机效应的混合模型重算各分布面板；向作者索取每鼠纤维数。
    - 证据：[EV-006｜methods/¶methods-sec006] [EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [major] CL-021 · 全文仅以 'P<0.05' 阈值报告显著性，无精确 P 值、检验统计量、df

- 类别：p_value_reporting
- 锚点：¶methods-sec020；成员：M4-003
- 关联判断：
  - **M4-003** [major] (M4) 全文仅以 'P<0.05' 阈值报告显著性，无精确 P 值、检验统计量、df
    - 详情：sec020 仅声明 P<0.05 阈值；Results 与图注无任何精确 P 值、t/F/U/H 统计量或自由度，显著性仅以叙述与图中括号传达。所有阳性结论（老龄 CSA、ApoE CSA、s/s 与 s/+ ~30%、血糖下降）均无法定量复核。statistical_forensics 五类确定性核验执行后均无对象可算，与阈值式报告互为印证（报告缺陷的确证，非核验失败）。
    - 判断置信度：high；规则：`04-statistics#p_value_reporting`；复核（统计审稿人，P1）：要求作者报告每个比较的精确 P 值与检验统计量/df；Dryad 数据若可取得可直接复算。
    - 证据：[EV-016｜methods/¶methods-sec020] [EV-055｜figure/¶fig2-caption-full/Fig 2]

### [major] CL-022 · 多终点重复检验未校正；Fig 1M 血糖为唯一显著结果，假阳性风险高

- 类别：multiple_testing_control
- 锚点：Fig Fig 1J-M／¶methods-sec020；成员：M4-004
- 关联判断：
  - **M4-004** [major] (M4) 多终点重复检验未校正；Fig 1M 血糖为唯一显著结果，假阳性风险高
    - 详情：老龄小鼠同一批（n=10/组）在 α=0.05 下分别检验体重、抓网、跑台、血糖（Fig 1J-M）4 个终点，无任何多重比较校正，唯一显著的血糖在该家族内假阳性概率约 19%；全文跨 5 个模型、多终点、多组比较均以未校正的逐检验 P<0.05 判定。另：唯一有再生增益的老龄 AAV 组恰是唯一血糖显著下降组，代谢效应与再生表型的关联/解耦从未被分析（原 G-65 收编）。
    - 判断置信度：high；规则：`04-statistics#multiple_testing_control`；复核（统计审稿人，P1）：将 Fig 1J-M 视为终点家族做 Holm/Bonferroni 校正复核；确认血糖下降是否被当作独立疗效主张；在有图像能力时核验显著性括号覆盖的对比集合。
    - 证据：[EV-065｜results/¶results-sec022-p4] [EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-016｜methods/¶methods-sec020]

### [major] CL-023 · 2×2 析因设计按单因素 one-way ANOVA 分析，交互项缺失；检验-面板映射不明

- 类别：statistical_test_selection
- 锚点：Fig Fig 2E／¶figure-2-caption；成员：M4-005
- 关联判断：
  - **M4-005** [major] (M4) 2×2 析因设计按单因素 one-way ANOVA 分析，交互项缺失；检验-面板映射不明
    - 详情：Fig 2E（db/db×sRAGE，4 组）与 S2B 的核心问题是 sRAGE 是否特异性挽救疾病小鼠再生缺陷，应做含交互项的 two-way ANOVA（同图 B/C/D 正是 two-way），却用 one-way ANOVA+Tukey 压平，无法检验 sRAGE 效应在 db/db 与 WT 间是否不同。Fig 2F/L 图注 'Mann-Whitney U test and Kruskal-Wallis test (F, L)' 未给检验-面板映射（F 为 4 组、L 为 2 组）；S2 C/F 同样歧义。Fig 3H、S3C 用 Kruskal-Wallis 总体检验但未说明事后两两方法而 Results 对分布作出具体组间结论。
    - 判断置信度：high；规则：`04-statistics#statistical_test_selection`；复核（统计审稿人，P1）：向作者确认各面板实际所用检验；在 Dryad 数据上对 Fig 2E/S2B 补做 two-way ANOVA 交互检验。
    - 证据：[EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-057｜supplement/¶s2-caption] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [major] CL-025 · 以 null 结果直接接受「无差异」结论，无效应量、CI 或等效性检验

- 类别：effect_size_reporting
- 锚点：¶results-sec022-p3；成员：M4-007
- 关联判断：
  - **M4-007** [major] (M4) 以 null 结果直接接受「无差异」结论，无效应量、CI 或等效性检验
    - 详情：多处关键结论建立在接受 H0 之上：Fig 1A（n=5/组）null ANOVA 即推出 'sRAGE 不随年龄升高'；Fig 3D 未损伤 CSA 以 n=3/组得出 'no differences'；Fig 3I/J 移植 null 结果支撑核心机制结论；db/db 'trend never reached significance' 被解读为糖尿病中无效。所有阴性结论均未报告效应量、95% CI，也未做等效性/最小效应排除分析，不能区分真无效应与检测不出。
    - 判断置信度：high；规则：`04-statistics#effect_size_reporting`；复核（统计审稿人，P1）：为每个阴性结论补算均差与 95% CI，评估能排除的最小效应量；移植与 db/db 结论改写为「未检出差异」并给出精度范围。
    - 证据：[EV-031｜results/¶results-sec022-p3] [EV-033｜results/¶results-sec024] [EV-062｜results/¶results-sec024-p3]

### [major] CL-026 · ApoE-/- 臂方案承诺 WT 对照，但 Fig 2H-L 与 S2 E-F 数据面板仅含 ApoE-null

- 类别：figure_text_contradiction
- 锚点：Fig Fig 2G-L／¶figure-2-caption；成员：M5-001
- 关联判断：
  - **M5-001** [major] (M5) ApoE-/- 臂方案承诺 WT 对照，但 Fig 2H-L 与 S2 E-F 数据面板仅含 ApoE-null
    - 详情：Fig 2G 图注明明方案纳入 'atherosclerotic (ApoE-null) and wild-type (WT) mice'，但 H/I/J/K/L 均只描述 ApoE-null 两组（K 用 t test）；S2D 方案同样写明 WT 而 E/F 只有 ApoE-null 数据。与 db/db 臂的不对称：db/db 臂 B-F 均含 WT、'再生受损' 有数据支撑；ApoE-/- 的再生受损前提因无同图 WT 对照从未被证明，无法判断 sRAGE 效应是否恢复至 WT 水平。（原 G-25 的 'as expected' 表述已核实仅用于 db/db 且有数据支撑。）
    - 判断置信度：high；规则：`05-figures-and-charts#figure_text_contradiction`；复核（领域审稿人，P1）：向作者索取 ApoE 臂 WT 数据或解释其移除原因；核对 Fig 2G/S2D 方案图是否因复用 db/db 臂模板而误带 WT。
    - 证据：[EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-057｜supplement/¶s2-caption] [EV-032｜results/¶results-sec023-p1]

### [major] CL-027 · 对照组基因型与遗传背景界定含糊

- 类别：confound_unreported
- 锚点：¶methods-sec003；成员：M3-006
- 关联判断：
  - **M3-006** [major] (M3) 对照组基因型与遗传背景界定含糊
    - 详情：db/db 实验的 'wild-type controls' 未说明是 db/+ 同窝鼠还是外购 +/+（B6.BKS(D)-Leprdb/J 为 C57BLKS/J 背景，若 WT 为 C57BL/6J 则存在背景品系混杂）；ApoE-/-（B6.129P2 混合背景）WT 对照与同窝状态未说明；Ager 六基因型队列 +/+ 来源未说明。另并入 G-28：KO（C. Lee/Brown）与 s（Lin-Perdue/NIA）为两个结构不同的 null 等位基因、来自不同实验室，回交代数、背景均一度与 2A-EGFP 盒潜在影响均未说明。
    - 判断置信度：high；规则：`03-experimental-methods#confound_unreported`；复核（领域审稿人，P1）：要求作者明确各实验对照组的确切基因型、来源与同窝状态；核查 db/db 与 WT 背景品系匹配；说明 Ager 两等位基因回交代数与遗传背景均一度。
    - 证据：[EV-032｜results/¶results-sec023-p1] [EV-063｜methods/¶methods-sec003-c] [EV-008｜methods/¶methods-sec003] [EV-059｜methods/¶methods-sec004-b]

### [major] CL-028 · 全部基因工程小鼠无基因分型方案

- 类别：method_reporting_incomplete
- 锚点：¶methods-sec004；成员：M3-007
- 关联判断：
  - **M3-007** [major] (M3) 全部基因工程小鼠无基因分型方案
    - 详情：Ager^s、Ager-、Leprdb、Apoe-、Dmdmdx 等位基因均未提供基因分型方法、引物序列或判定标准；sec003 的交配方案需从后代中鉴定 6 种基因型，分型是分组前提却完全缺失，遗传学实验无法评估与复现。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（作者，P1）：补充各等位基因的分型引物、产物大小与判定标准，或引用原始品系文献中的分型方案。
    - 证据：[EV-077｜缺失检索：methods｜no_match] [EV-063｜methods/¶methods-sec003-c]

### [major] CL-029 · AAV 转导的 sRAGE 转基因异构体未定义、无蛋白水平验证

- 类别：intervention_underspecified
- 锚点：¶methods-sec013；成员：M3-008
- 关联判断：
  - **M3-008** [major] (M3) AAV 转导的 sRAGE 转基因异构体未定义、无蛋白水平验证
    - 详情：sec013 仅称 sRAGE CDS 'amplified from sRAGE transgenic animals'：无引物序列（无法确认扩增长度与异构体）、无蛋白水平验证（表达、分泌、配体结合）、仅 'NGS verified for correct sequence and ITR integrity'；PCR 扩增可能捕获不同剪接变体。
    - 判断置信度：high；规则：`03-experimental-methods#intervention_underspecified`；复核（作者，P1）：提供扩增引物、测序覆盖范围与重组蛋白验证数据。
    - 证据：[EV-044｜methods/¶methods-sec013]

### [major] CL-030 · CSA 测量规程不足以支撑组间比较

- 类别：quantification_criteria_undefined
- 锚点：¶methods-sec006；成员：M3-009
- 关联判断：
  - **M3-009** [major] (M3) CSA 测量规程不足以支撑组间比较
    - 详情：每鼠仅选'最好'的一张切片、损伤区旁 4 个 20X 视野、手工 ImageJ（Fiji）勾画：无分割/排除标准、无每鼠纤维数、无对损伤面积归一化、软件版本未给出。切片分析盲法已报告（slides coded）缓解主观偏倚但无法缓解取样偏倚（见 M3-001）。
    - 判断置信度：high；规则：`03-experimental-methods#quantification_criteria_undefined`；复核（领域审稿人，P1）：复核各图 CSA 每鼠纤维数是否一致；要求作者提供量化规则细节与软件版本。
    - 证据：[EV-006｜methods/¶methods-sec006]

### [major] CL-031 · 移植供体细胞分选后质量未报告

- 类别：method_reporting_incomplete、replicate_type_unclear
- 锚点：¶methods-sec009；成员：M3-010、M3-023
- 关联判断：
  - **M3-010** [major] (M3) 移植供体细胞分选后质量未报告
    - 详情：sec007 自述分离+双分选共 5-8 小时；分选前 live/dead 门控与单色/FMO 对照已报告（部分缓解），但分选后活力、纯度复检、无菌状态、注射前细胞浓度与体外滞留时间均未报告；细胞以含 2% FBS 的 HBSS 20 μL 注射。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（作者，P1）：提供分选后 re-analysis（纯度/活力）数据或说明。
    - 证据：[EV-045｜methods/¶methods-sec007] [EV-088｜缺失检索：methods｜no_match] [EV-002｜methods/¶methods-sec009]
  - **M3-023** [major] (M3) 移植供体侧计量缺失：供体数目、混合方式与受体特征未报告
    - 详情：sec009/Fig 3 未说明：每种基因型的供体鼠数目、3000/6000 细胞是否来自多个供体混合、供体性别/年龄、受体 mdx 鼠的年龄/体重、同一细胞制备是否同时供给两个剂量组。供体身份与批次直接影响 '各基因型无差异' 阴性结论的解释与可重复性。
    - 判断置信度：medium；规则：`03-experimental-methods#replicate_type_unclear`；复核（作者，P1）：明确每基因型供体数与混合策略、受体年龄/体重。
    - 证据：[EV-090｜缺失检索：figure,methods｜no_match] [EV-045｜methods/¶methods-sec007]

### [major] CL-032 · 移植终点计量学缺陷：'averaged from at least 3 depths' 无校正且含糊

- 类别：quantification_criteria_undefined
- 锚点：¶methods-sec009；成员：M3-011
- 关联判断：
  - **M3-011** [major] (M3) 移植终点计量学缺陷：'averaged from at least 3 depths' 无校正且含糊
    - 详情：sec009 对 10-15 个冷冻深度中的 3 层成像计数 dystrophin+ 纤维：未对切片厚度（12 μm）、深度间隔、肌肉横截面积或 laminin+ 纤维总数做任何校正；'at least 3' 未定义。跨深度计数取平均不是对总植入纤维数的有效估计。
    - 判断置信度：high；规则：`03-experimental-methods#quantification_criteria_undefined`；复核（领域审稿人，P1）：要求作者明确深度选取规则与计数归一化方式；复核 Fig 3I/J 原始计数分布。
    - 证据：[EV-002｜methods/¶methods-sec009]

### [major] CL-033 · 功能实验方法学要素缺失

- 类别：method_reporting_incomplete
- 锚点：¶methods-sec019；成员：M3-012
- 关联判断：
  - **M3-012** [major] (M3) 功能实验方法学要素缺失
    - 详情：sec019：跑台力竭标准未定义（'run until they could no longer sustain'），电刺激参数缺失，仅 1 天 10 分钟适应。sec018：抓网悬挂无最长时限（天花板效应）、未按体重归一化；两项测试均在光照期 12-6pm（夜行动物休息期）进行；环境适应 30 min 与 ≥1h 间隔已报告（部分缓解）；测试顺序随机化未说明。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（作者，P1）：补充力竭判定标准、电刺激参数与悬挂时限；确认体重归一化是否适用。
    - 证据：[EV-047｜methods/¶methods-sec018] [EV-048｜methods/¶methods-sec019]

### [major] CL-034 · Western blot 验证证据薄弱且关键要素缺失

- 类别：method_reporting_incomplete、missing_loading_control
- 锚点：Fig Fig 3C／¶methods-sec010；成员：M3-013、M5-020
- 关联判断：
  - **M3-013** [major] (M3) Western blot 验证证据薄弱且关键要素缺失
    - 详情：Fig 3C 的 RAGE 验证仅用一种兔抗 RAGE（ab3611），无第二抗体或正交验证；无条带定量、生物学重复数未说明、WB 取材组织未指明；loading control GAPDH（sc-32233）跑在另一块胶；未见 sRAGE 蛋白本身的 blot；exon 2-7 缺失的 KO 是否产生抗体可识别的截短蛋白未讨论。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（领域审稿人，P1）：人工复核 Fig 3C 条带数目、重复与组织来源标注（本环境无图像输入）；要求作者补充 sRAGE 阳性对照。
    - 证据：[EV-046｜methods/¶methods-sec010] [EV-034｜figure/¶fig3-caption-full/Fig 3]
  - **M5-020** [minor] (M5) Fig 3C Western blot 的 loading control 无法从图注核验
    - 详情：Fig 3C 图注仅称 'Confirmation of C-terminal RAGE expression ... via Western blot'，未提及内参；Methods sec010 说明 GAPDH 在另一块平行胶上作为 loading control。figure_integrity_audit 未在 Fig 3C 条带区域检出重复候选（不构成拼接疑点证据，亦不能证明存在 loading control）；面板内是否有 GAPDH 与分子量标准仍需视觉核验。无图注的 '(PDF)'（疑似原始 blot 记录）亦未提供。
    - 判断置信度：low；规则：`05-figures-and-charts#missing_loading_control`；复核（领域审稿人，P2）：视觉核验 Fig 3C 是否展示 loading control 与 MW 标记；索取原始 blot PDF。
    - 证据：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-046｜methods/¶methods-sec010]

### [major] CL-035 · AAV 干预缺少空衣壳/杂质对照

- 类别：missing_paired_control
- 锚点：¶methods-sec017；成员：M3-014
- 关联判断：
  - **M3-014** [major] (M3) AAV 干预缺少空衣壳/杂质对照
    - 详情：sec017 比较 AAV9-sRAGE 与 FFB formulation buffer，无空衣壳对照组；衣壳蛋白剂量、残余宿主细胞蛋白/DNA 成为处理组独有混杂（AAVX 亲和树脂结合衣壳而与基因组含量无关，不能去除空壳）。作者未讨论该局限。（0.001% Pluronic 为常规赋形剂浓度，其生物活性担忧缺乏依据。）
    - 判断置信度：high；规则：`03-experimental-methods#missing_paired_control`；复核（领域审稿人，P1）：确认纯化后制剂的空壳比数据是否存在；要求作者在 Limitations 中讨论空衣壳/杂质对照缺失。
    - 证据：[EV-011｜methods/¶methods-sec017] [EV-051｜methods/¶methods-sec015]

### [major] CL-040 · Dystrophin 一抗种属标注与已知试剂身份及二抗配置矛盾

- 类别：antibody_validation_issue
- 锚点：¶methods-sec008；成员：M3-020
- 关联判断：
  - **M3-020** [major] (M3) Dystrophin 一抗种属标注与已知试剂身份及二抗配置矛盾
    - 详情：sec008 写 'primary mouse anti-Dystrophin (1:200; Sigma D8168)' 并配 goat anti-mouse AF555 二抗；Sigma D8168 的已知产品记录为兔源多克隆抗 dystrophin。若如此则种属标注错误、anti-mouse 二抗无法检测该一抗；若改用 anti-rabbit 二抗则与兔抗 laminin 通道冲突。按所写配置染色无法成立，直接威胁以 dystrophin+ 纤维计数为终点的移植实验有效性。待厂商页面与图像核验。
    - 判断置信度：medium；规则：`03-experimental-methods#antibody_validation_issue`；复核（领域审稿人，P1）：核查 Sigma D8168 产品页宿主种属；复核 Fig 3I/J dystrophin 通道图像染色是否成立；若错误要求作者提供替代验证。
    - 证据：[EV-049｜methods/¶methods-sec008]

### [major] CL-041 · 滴度引物靶点（bGHpA）与最终构件 polyA（SV40pA）疑似不匹配

- 类别：flow_break、method_reporting_incomplete
- 锚点：¶methods-sec016；成员：M3-021、M3-030
- 关联判断：
  - **M3-021** [major] (M3) 滴度引物靶点（bGHpA）与最终构件 polyA（SV40pA）疑似不匹配
    - 详情：按 sec013，CBh-miR122t-SV40pA 表达盒克隆入 scAAV-CMV-GFP-bGHpA 骨架 ITR 之间（置换 CMV-GFP-bGHpA 表达单元），最终构件应为 ITR-Cbh-miR122t-sRAGE-SV40pA-ITR；而 sec016 首选滴度引物靶向 bGH polyA（标准品为线性化 scAAV-EGFP DNA），Cmh 引物仅为 secondary verification。若最终构件不含 bGHpA，首选滴度方法无法计量载体基因组。取决于骨架酶切图谱，需核实。
    - 判断置信度：medium；规则：`03-experimental-methods#flow_break`；复核（领域审稿人，P1）：索取/重建 scAAV-CMV-GFP-bGHpA 骨架与最终构件的酶切图谱，确认 bGHpA 是否保留。
    - 证据：[EV-044｜methods/¶methods-sec013] [EV-052｜methods/¶methods-sec016]
  - **M3-030** [minor] (M3) bGHpA 滴度 qPCR 引物设计参数处于临界范围且无扩增效率验证
    - 详情：序列标识符审计候选信号：bGH-Forward（GCCAGCCATCTGTTGT, 16 nt）估算 Tm 45.9°C 低于常规 50-68°C；bGH-Reverse（GGAGTGGCACCTTCCA, 16 nt）GC 62.5% 超出常规 40-60%、估算 Tm 48.5°C。探针法可部分补偿，但对定量的直接影响未知；sec016 未报告标准曲线扩增效率。与 M3-021（引物靶点匹配性）叠加后 vg 定量链条方法学保证不足。
    - 判断置信度：low；规则：`03-experimental-methods#method_reporting_incomplete`；复核（领域审稿人，P2）：以 nearest-neighbor 法复核引物 Tm/GC；要求作者提供 qPCR 标准曲线斜率/扩增效率与 R²。
    - 证据：[EV-052｜methods/¶methods-sec016]；工具信号：SIG-801、SIG-802

### [major] CL-054 · 支撑核心结论（损伤模型特异性）的 BaCl2 阴性结果 S1-S3 全部置于补充材料且本审材料不可核验

- 类别：figure_should_be_main_text
- 锚点：¶sec027；成员：M5-018
- 关联判断：
  - **M5-018** [major] (M5) 支撑核心结论（损伤模型特异性）的 BaCl2 阴性结果 S1-S3 全部置于补充材料且本审材料不可核验
    - 详情：摘要与结论的核心主张是 'sRAGE 促 cryoinjury 再生但不促 BaCl2 再生'，Discussion 将两种损伤模型差异作为主要概念进展；但对应的 S1/S2/S3 三图全部在补充材料且 TIF 文件未随材料提供，Results 对它们的引用只剩残留面板字母。关键对照证据的证据权重与正文位置不匹配，且对审阅者与读者均不可核验。
    - 判断置信度：medium；规则：`05-figures-and-charts#figure_should_be_main_text`；复核（编辑，P1）：建议将至少一个 cryo-vs-BaCl2 汇总比较提升至正文，或确保补充文件随稿件公开可核验。
    - 证据：[EV-056｜supplement/¶s1-caption] [EV-057｜supplement/¶s2-caption] [EV-058｜supplement/¶s3-caption] [EV-041｜abstract/¶abstract-p1]

### [major] CL-064 · 无任何晚期结局数据，无法支持'更好的最终修复'类结论

- 类别：claim_beyond_evidence
- 锚点：¶results-sec022；成员：M7-004
- 关联判断：
  - **M7-004** [major] (M7) 无任何晚期结局数据，无法支持'更好的最终修复'类结论
    - 详情：所有再生终点止于 7 dpi（唯一更晚的 3 周时间点是移植 engraftment，测的是供体细胞贡献而非再生质量）。未评估晚期再生完成度、最终纤维大小、纤维化（对老龄与 db/db 模型尤为重要）或损伤后功能恢复（Fig 1J-M 为未损伤肌肉 30 天时全身指标）。标题/摘要/结论的 'enhances regeneration / accelerates repair' 隐含更好的最终修复，证据只覆盖伤后第 7 天的形态学中间指标。
    - 判断置信度：high；规则：`07-conclusions-discussion#claim_beyond_evidence`；复核（领域审稿人，P1）：确认是否存在任何 >7 dpi 的再生终点（含纤维化染色）；评估结论措辞是否需限定为'早期再生阶段'。
    - 证据：[EV-031｜results/¶results-sec022-p3] [EV-032｜results/¶results-sec023-p1] [EV-033｜results/¶results-sec024] [EV-006｜methods/¶methods-sec006]

### [major] CL-065 · 结论范围外推：degenerative disorders/aging muscle/microenvironment

- 类别：claim_beyond_evidence、conclusion_overreach
- 锚点：¶conclusion-sec026；成员：M7-005、M2-008
- 关联判断：
  - **M7-005** [major] (M7) 结论范围外推：degenerative disorders/aging muscle/microenvironment
    - 详情：sec026 将结果提升为治疗 'skeletal muscle injury, aging muscle, and degenerative disorders' 的潜在策略：(1) degenerative disorders 无对应疗效测量——mdx 仅作移植受体且未测其自身再生，db/db 冷冻伤不显著；(2) aging muscle 无未损伤老龄肌肉获益（体重/力量/耐力均无差异）；(3) skeletal muscle injury 泛化——唯一阳性损伤模型是冷冻伤，全部 BaCl2 臂阴性，且 AAV 为伤前 30 天预防性给药而非治疗后干预；(4) 摘要 microenvironment 全文从未测量；(5)  Discussion p4 自引全长 RAGE 为年轻动物再生必需，sRAGE 治疗干扰必需性 RAGE 信号的安全性张力在 Conclusion 未处理。（收编 G-20 机制推测的可立案部分与 G-60 血管/免疫假说——均为 hedged 表述，不单独立案。）
    - 判断置信度：high；规则：`07-conclusions-discussion#claim_beyond_evidence`；复核（领域审稿人，P1）：核对结论是否应限于'aged 与 ApoE-/- 小鼠冷冻伤后早期组织学再生'；确认全文是否有 microenvironment（肌肉局部 sRAGE/配体）测量；'diseased' 限定词由编辑复核。
    - 证据：[EV-021｜conclusion/¶sec026-p1] [EV-041｜abstract/¶abstract-p1] [EV-042｜title/¶title-p1] [EV-036｜discussion/¶discussion-p4] [EV-043｜methods/¶methods-sec011-b]
  - **M2-008** [major] (M2) 'degenerative disorders' 治疗潜力无对应疗效测量
    - 详情：sec026 结论称 sRAGE 可能治疗 'skeletal muscle injury, aging muscle, and degenerative disorders'；前两个对象有对应实验（冷冻伤、老龄），第三个无——唯一涉及退行性疾病的操作是向 mdx 受体移植 MuSC（engraftment 读出，各基因型无差异的 null result），mdx 从未作为疗效测试模型。
    - 判断置信度：high；规则：`02-macro-logic#conclusion_overreach`；复核（作者，P1）：删除或限定 'degenerative disorders'，除非补充相应疾病模型的疗效数据。
    - 证据：[EV-021｜conclusion/¶sec026-p1] [EV-062｜results/¶results-sec024-p3]

### [major] CL-066 · Discussion 对 Ager-/- 冷冻伤结果作'未能复现'推断，该比较在 Results 未被陈述且无 CI/等效性支撑

- 类别：negative_result_misread
- 锚点：¶discussion-sec025-p4；成员：M7-007
- 关联判断：
  - **M7-007** [major] (M7) Discussion 对 Ager-/- 冷冻伤结果作'未能复现'推断，该比较在 Results 未被陈述且无 CI/等效性支撑
    - 详情：Discussion p4：'we were not able to reproduce the regenerative delays characteristic of 2-3 month old RAGE KO animals in our older adult cohort ...'。问题：(1) Results sec024 从未描述 Ager-/-、Ager+/- 冷冻伤的组间结果，Discussion 却对未陈述比较下推断；(2) 'not able to reproduce' 把不显著/未见差异读作复现失败，无效应量、无 CI、无等效性检验，且跨年龄+跨实验室比较混杂未处理；(3) 'RAGE 仅在早期生命阶段必需'进一步放大该 null 推断。
    - 判断置信度：medium；规则：`07-conclusions-discussion#negative_result_misread`；复核（领域审稿人，P1）：读 Fig 3G/H 原始数据确认 Ager-/- 7 dpi CSA 组间差异与变异度（本环境无图像，需人工）；确认 Results 是否应补述 knockout 臂结果。
    - 证据：[EV-036｜discussion/¶discussion-p4] [EV-033｜results/¶results-sec024] [EV-083｜缺失检索：results｜no_match]

### [major] CL-067 · 全文无局限性陈述

- 类别：limitations_evasive
- 锚点：¶discussion-sec025；成员：M7-008
- 关联判断：
  - **M7-008** [major] (M7) 全文无局限性陈述
    - 详情：Discussion 七段与 Conclusion 中不存在任何局限性段落或语句（检索 limitation/caveat/underpowered 等同义表述零命中，仅见未来工作展望）。对照上游 major findings：样本量依据缺失未承认；多重比较未校正的假阳性风险未承认；关键对照缺失（空衣壳、未移植对照、-/- vs s/s）对归因的限制未承认；单时间点、仅雄性、无长期结局等均未自查。
    - 判断置信度：high；规则：`07-conclusions-discussion#limitations_evasive`；复核（领域审稿人，P1）：确认 Discussion/Conclusion 是否存在任何未被检出的局限性语句（近义表达）；要求作者补充 Limitations。
    - 证据：[EV-022｜缺失检索：conclusion,discussion｜no_match] [EV-030｜discussion/¶discussion-p1]

### [major] CL-069 · 全程单剂量且跨模型暴露量从未定量比较，阴性结论解释力受限

- 类别：power_and_sample_size、dose_rationale_missing
- 锚点：¶methods-sec017；成员：M4-009、M3-029
- 关联判断：
  - **M4-009** [major] (M4) 全程单剂量且跨模型暴露量从未定量比较，阴性结论解释力受限
    - 详情：（Layer 4 收编 G-38：原被 M4 refine 后无接收方）所有研究仅用 1e11 vg/mouse 单剂量、无剂量论证（并入 M3-029）；各模型间达到的循环 sRAGE 水平从未定量横向比较——db/db 阴性虽证实表达上升，仍无法区分生物学抵抗与暴露/动力学不足，'sRAGE 在糖尿病中无效' 的结论解释力受限。
    - 判断置信度：high；规则：`04-statistics#power_and_sample_size`；复核（统计审稿人，P1）：要求作者提供跨模型循环 sRAGE 暴露的定量比较；讨论单剂量设计对阴性结论解释的影响。
    - 证据：[EV-011｜methods/¶methods-sec017] [EV-032｜results/¶results-sec023-p1] [EV-043｜methods/¶methods-sec011-b]
  - **M3-029** [minor] (M3) AAV 单剂量使用且无剂量选择依据
    - 详情：所有队列统一使用 1e11 vg/mouse 眶后给药（全文剂量单位一致无内部矛盾），无剂量探索或剂量选择依据说明，也未讨论剂量-反应关系对结论的影响。
    - 判断置信度：high；规则：`03-experimental-methods#dose_rationale_missing`；复核（作者，P2）：补充剂量选择文献依据。
    - 证据：[EV-011｜methods/¶methods-sec017]

### [major] CL-071 · AAV 载体质控结果缺失且 HEK293 鉴定信息未报告

- 类别：validation_result_unreported、processing_underspecified
- 锚点：¶methods-sec014；成员：M3-005、M3-027
- 关联判断：
  - **M3-005** [major] (M3) AAV 载体质控结果缺失且 HEK293 鉴定信息未报告
    - 详情：sec014-016 描述了生产、HPLC 纯化与 qPCR 滴度方法，但未报告任何质控结果：实际滴度、空壳/实心比、内毒素/无菌、体外效力均缺失（唯一间接证据是体内 ~10 倍血清 sRAGE 诱导）。X1 将 HEK293 解析为 Cellosaurus CVCL_0045 无已知交叉污染标志，但稿件未报告其供应商、STR 鉴定、支原体状态与传代数。
    - 判断置信度：high；规则：`03-experimental-methods#validation_result_unreported`；复核（领域审稿人，P1）：要求作者提供载体 QC 数据（滴度、空壳比、纯度、无菌/内毒素）与 HEK293 细胞来源及支原体检测记录。
    - 证据：[EV-050｜methods/¶methods-sec014-b] [EV-086｜缺失检索：methods｜no_match] [EV-087｜缺失检索：methods｜no_match] [EV-901｜Cellosaurus CVCL_0045｜resolved｜2026-08-07]
  - **M3-027** [minor] (M3) AAV 生产关键参数含混
    - 详情：sec014：'mixed with 3 ml Triton-X 100'（原液体积 vs 终浓度不明）、'2.5 mg RNAse A at 1 mg/ml concentration'（量与浓度表述混淆）；HYPERFlask 接种密度未记录。影响裂解与澄清步骤可重复性。
    - 判断置信度：medium；规则：`03-experimental-methods#processing_underspecified`；复核（作者，P2）：澄清试剂添加量与终浓度。
    - 证据：[EV-050｜methods/¶methods-sec014-b]

### [minor] CL-008 · 摘要承诺评估 central nucleation 但全文从未量化

- 类别：abstract_main_text_inconsistency
- 锚点：¶abstract；成员：M2-006
- 关联判断：
  - **M2-006** [minor] (M2) 摘要承诺评估 central nucleation 但全文从未量化
    - 详情：摘要称 'We evaluated ... including central nucleation, and myofiber size'；实际终点仅为 centrally-nucleated 纤维的 CSA，Methods 以中央核作为挑选再生纤维的判据，全文（含 S1-S3 图注）无任何 central nucleation 比例/指数的量化。
    - 判断置信度：high；规则：`02-macro-logic#abstract_main_text_inconsistency`；复核（作者，P2）：摘要改为 'centrally-nucleated fiber size'，或补报 central nucleation 比例。
    - 证据：[EV-041｜abstract/¶abstract-p1] [EV-082｜缺失检索：methods,results,supplement｜no_match] [EV-006｜methods/¶methods-sec006]

### [minor] CL-024 · sRAGE 动力学（d0-d30）未说明是否同鼠重复采样

- 类别：statistical_test_selection
- 锚点：Fig Fig 1D/G／¶figure-1-caption；成员：M4-006
- 关联判断：
  - **M4-006** [minor] (M4) sRAGE 动力学（d0-d30）未说明是否同鼠重复采样
    - 详情：Fig 1D/G、2B/H 的多时间点用 one-way/two-way ANOVA 分析，方法与图注均未说明时间点是否为同一批鼠重复尾静脉采血：若重复采样则违反独立样本前提（应重复测量/混合模型），且反复采血（每次 50 μL）构成应激混杂；若独立亚群则与 'n≥7/n=10 per condition' 表述矛盾。Fig 2B 为基因型×处理×时间三因子却报 two-way ANOVA，因子结构未说明。若证实重复采样则升 major。
    - 判断置信度：medium；规则：`04-statistics#statistical_test_selection`；复核（统计审稿人，P2）：核对 Dryad 数据或向作者确认动力学是否同鼠纵向采样；若是，以重复测量模型复核。
    - 证据：[EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-043｜methods/¶methods-sec011-b]

### [minor] CL-036 · 多处笔误与术语错误

- 类别：method_reporting_incomplete、terminology_inconsistency、figure_terminology_inconsistency
- 锚点：¶multiple；成员：M3-015、M2-010、M5-003、M5-016、M3-019
- 关联判断：
  - **M3-015** [minor] (M3) 多处笔误与术语错误
    - 详情：sec013 'CBh' vs 'Cmh' 及 'SV4pA'（应 SV40pA）；sec008 'Hoescht 33342'；sec017 'isofluorane'；sec022 'vehicle controla'；sec010 'AnykD'；sec015 'AKTA Pure 25 liter'；Results '1e + 11' vs Methods '1e11'（同一数值，仅记法问题）；Introduction 'our bodies muscle repair ability'。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（编辑，P2）：逐条更正；核对正式发表版 S2 图注是否存在 '(N = 6' 截断。
    - 证据：[EV-044｜methods/¶methods-sec013] [EV-049｜methods/¶methods-sec008] [EV-031｜results/¶results-sec022-p3]
  - **M2-010** [minor] (M2) 编辑性不一致集群：FBB/FFB、Bacl2、SV4pA、'As expected27'
    - 详情：(1) vehicle 缩写 FFB（sec017 定义）与 FBB（Fig 1/2 方案面板、S1/S2 图注）混用；(2) S1、S3 图注 'Bacl2'；(3) sec013 'SV4pA'；(4) sec024 残留引文编号 'As expected27'（提供材料 References 为空，需以正式稿核对是否为提取伪影）。
    - 判断置信度：high；规则：`02-macro-logic#terminology_inconsistency`；复核（编辑，P2）：以正式发表版核对 'As expected27' 与 FBB/FFB 标注；统一对照命名。
    - 证据：[EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-044｜methods/¶methods-sec013] [EV-033｜results/¶results-sec024] [EV-056｜supplement/¶s1-caption]
  - **M5-003** [minor] (M5) vehicle 缓冲液命名 FFB/FBB 在图注间前后不一致
    - 详情：Methods sec017 定义 'vehicle (FFB...)'，sec022 正文亦用 FFB；但 Fig 1 C-F、Fig 2 首句与 G、S1 A/D、S2 A/D 的方案面板描述写作 'vehicle (FBB)'，同一批图注的其余面板写作 FFB。同一缓冲液两种拼写且无解释；方案面板内嵌标签需视觉核验定位错误源头。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_terminology_inconsistency`；复核（编辑，P2）：统一为 FFB 并核对方案示意图内嵌文字。
    - 证据：[EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-011｜methods/¶methods-sec017]
  - **M5-016** [minor] (M5) 图注/正文多处拼写与书写风格不一致
    - 详情：S1（E/F）与 S3 图注将 BaCl2 写作 'Bacl2'；Fig 2 图注 'one way ANOVA'（应 one-way）；Fig 2 I/J 'n = 6 male mice' 缺 'per condition'（同图其余面板均有）；Results sec022 'vehicle controla' 笔误；图注标记风格混杂（基因符号式 vs 蛋白名式）。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_terminology_inconsistency`；复核（编辑，P2）：统一术语与拼写。
    - 证据：[EV-056｜supplement/¶s1-caption] [EV-058｜supplement/¶s3-caption] [EV-055｜figure/¶fig2-caption-full/Fig 2]
  - **M3-019** [minor] (M3) qPCR 循环条件 '95°C holding 10 seconds' 不合常理
    - 详情：sec016 写 'After 95°C holding stage for 10 seconds'；聚合酶激活/初始变性 hold 通常为 30 秒至 10 分钟，10 秒疑为笔误；随后两步循环 95°C 5s / 60°C 5s ×40 亦异常短暂（快循环仪器上可行但不常见）。影响可重复性。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（作者，P2）：对照 NEB Luna Universal Probe (#M3004S) 说明书推荐循环条件核实。
    - 证据：[EV-052｜methods/¶methods-sec016]

### [minor] CL-037 · 行为学测试顺序未随机化

- 类别：randomization_blinding_unreported
- 锚点：¶methods-sec018；成员：M3-016
- 关联判断：
  - **M3-016** [minor] (M3) 行为学测试顺序未随机化
    - 详情：sec018/19 未说明同日测试动物的顺序随机化或操作者一致性；行为测试在 12-6pm 串行进行，存在顺序效应与操作者漂移风险。
    - 判断置信度：high；规则：`03-experimental-methods#randomization_blinding_unreported`；复核（作者，P2）：在补充材料中说明测试顺序与操作者安排。
    - 证据：[EV-047｜methods/¶methods-sec018] [EV-048｜methods/¶methods-sec019]

### [minor] CL-038 · sec015 柱体积描述自相矛盾且实际操作参数未指明

- 类别：method_reporting_incomplete
- 锚点：¶methods-sec015；成员：M3-017
- 关联判断：
  - **M3-017** [minor] (M3) sec015 柱体积描述自相矛盾且实际操作参数未指明
    - 详情：sec015 先称 'column volume ([CV]) was limited to 1mL for each purification'，随后给出 '1 ml resin ... or 4 ml resin' 两种条件，两者不能同时成立；作者亦未说明本研究实际使用的树脂体积/CV。矛盾文本位于带引号的照抄块内；实际纯化参数无法复现。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（作者，P2）：说明实际树脂体积与 CV，并核对引文来源。
    - 证据：[EV-051｜methods/¶methods-sec015]

### [minor] CL-043 · sec022 声称评估 'resting' 肌肉，但 AAV 队列无任何未损伤肌肉组织学

- 类别：figure_text_contradiction
- 锚点：¶results-sec022-p2；成员：M5-002
- 关联判断：
  - **M5-002** [minor] (M5) sec022 声称评估 'resting' 肌肉，但 AAV 队列无任何未损伤肌肉组织学
    - 详情：sec022 称 'assessed the effects on resting and regenerating skeletal muscle 30 days after the initial viral delivery'，但 Fig 1 A-M 与 S1 面板清单中没有任何未损伤肌肉组织学（resting 仅有体重/抓网/跑台/血糖等功能代谢读数）；全文唯一的 uninjured CSA 数据来自遗传系（Fig 3D，n=3，与 AAV 无关）。'resting' 声明仅被功能性读数部分支撑。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_text_contradiction`；复核（作者，P2）：明确 J-M 与 resting 评估的对应关系，或修改措辞为功能/代谢评估。
    - 证据：[EV-061｜results/¶results-sec022-p2]

### [minor] CL-044 · Methods 声称使用 2-20 月龄小鼠，但所有图注最老仅 18 月龄

- 类别：figure_text_contradiction
- 锚点：¶methods-sec004；成员：M5-004
- 关联判断：
  - **M5-004** [minor] (M5) Methods 声称使用 2-20 月龄小鼠，但所有图注最老仅 18 月龄
    - 详情：sec004 写 'Male mice (ranging from 2-20 months of age)'；全部图注上限为 18 月龄（Fig 1A/C、S1 D-F），下限 2-3 月龄（Fig 2、S2），无任何面板或结果出现 20 月龄。年龄范围上限与实际数据不符。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_text_contradiction`；复核（作者，P2）：修正年龄范围或补充 20 月龄数据说明。
    - 证据：[EV-059｜methods/¶methods-sec004-b] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [minor] CL-046 · Fig 1/Fig 2 及 S1/S2 主次要组织学终点均无代表性 H&E 图像

- 类别：micrograph_info_incomplete
- 锚点：¶figure-captions；成员：M5-006
- 关联判断：
  - **M5-006** [minor] (M5) Fig 1/Fig 2 及 S1/S2 主次要组织学终点均无代表性 H&E 图像
    - 详情：Fig 1(A-M) 与 Fig 2(A-L) 以及 S1/S2 面板全部为定量图，无一张代表性组织学图像；全文唯一代表性 H&E 为 Fig 3F，且仅覆盖 6 个基因型中的 3 个。figure_integrity_audit 未在 Fig 3F 各面板间检出重复候选，但形态学质量与标尺仍需视觉核验。
    - 判断置信度：medium；规则：`05-figures-and-charts#micrograph_info_incomplete`；复核（领域审稿人，P2）：建议为成年/老龄与疾病模型各补代表性 H&E；视觉核验 Fig 3F 质量。
    - 证据：[EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [minor] CL-047 · Fig 2 图注首句缺面板字母 'A)'

- 类别：panel_reference_broken
- 锚点：Fig Fig 2／¶figure-2-caption；成员：M5-007
- 关联判断：
  - **M5-007** [minor] (M5) Fig 2 图注首句缺面板字母 'A)'
    - 详情：Fig 2 图注以 'Experimental scheme for muscle regeneration assay...' 直接开头，缺 'A)'；Fig 1/3 与 S1-S3 均从 'A)' 起。纯标注遗漏，未造成引用断裂。
    - 判断置信度：high；规则：`05-figures-and-charts#panel_reference_broken`；复核（编辑，P2）：补 'A)' 标签。
    - 证据：[EV-055｜figure/¶fig2-caption-full/Fig 2]

### [minor] CL-049 · Fig 1/2/3 与 S1-S3 各队列的独立性未在图注或正文声明

- 类别：caption_not_self_contained
- 锚点：¶results-sec022；成员：M5-010
- 关联判断：
  - **M5-010** [minor] (M5) Fig 1/2/3 与 S1-S3 各队列的独立性未在图注或正文声明
    - 详情：sec022 称 'we repeated our viral infections...' 并转向 BaCl2 实验，但 S1/S2/S3 图注均未说明其 BaCl2 队列与 Fig 1/2/3 的 cryoinjury 队列是否独立、WT 对照是否复用；n 数相同（n≥7、n=10、n=6）既可能提示复用也可能巧合。
    - 判断置信度：medium；规则：`05-figures-and-charts#caption_not_self_contained`；复核（作者，P2）：声明队列独立性或共用关系。
    - 证据：[EV-031｜results/¶results-sec022-p3] [EV-093｜缺失检索：results,supplement｜no_match] [EV-056｜supplement/¶s1-caption]

### [minor] CL-050 · sec023 小节标题仅提动脉粥样硬化模型，实际首段为 db/db 糖尿病实验且结果为阴性趋势

- 类别：figure_text_contradiction
- 锚点：¶results-sec023-heading；成员：M5-011
- 关联判断：
  - **M5-011** [minor] (M5) sec023 小节标题仅提动脉粥样硬化模型，实际首段为 db/db 糖尿病实验且结果为阴性趋势
    - 详情：标题 '...in a mouse model of atherosclerosis' 与 Fig 2 内容不符：Fig 2 A-F 与首段文字是 db/db 糖尿病臂，其 sRAGE 效应仅为不显著趋势；标题遗漏该臂且 'enhances' 措辞对 db/db 臂不成立，易误导读者对该图证据强度的判断。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_text_contradiction`；复核（编辑，P2）：标题改为涵盖两种疾病模型并区分显著性。
    - 证据：[EV-073｜results/¶results-sec023-heading]

### [minor] CL-051 · 图注均未描述比例尺/放大倍数

- 类别：micrograph_info_incomplete
- 锚点：¶figure-captions；成员：M5-012
- 关联判断：
  - **M5-012** [minor] (M5) 图注均未描述比例尺/放大倍数
    - 详情：全部图注无 scale bar/放大倍数声明；Fig 3F 注明 H&E 与 3 个基因型但无比例尺；Methods sec006 仅说明定量图像为 20X 采集。图像上是否实际带 scale bar 需视觉核验（本环境无图像输入），故置信度低。
    - 判断置信度：low；规则：`05-figures-and-charts#micrograph_info_incomplete`；复核（领域审稿人，P2）：视觉核验 Fig 3F scale bar；建议图注补倍数。
    - 证据：[EV-094｜缺失检索：figure｜no_match] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [minor] CL-052 · Fig 1J-M 测量时间点相对 cryoinjury 的关系未说明

- 类别：caption_not_self_contained
- 锚点：¶figure-1-caption；成员：M5-013
- 关联判断：
  - **M5-013** [minor] (M5) Fig 1J-M 测量时间点相对 cryoinjury 的关系未说明
    - 详情：Fig 1 图注 J-M 仅写 'aged (18 months old) mice' 无时间点；sec022 只含糊称 'Thirty days after administration'。无法判断 J-M 在损伤前（则全文无任何损伤后功能评估）还是损伤后（则受伤 TA 与全身炎症混杂读数）测量；Fig 1C 方案图中时间轴需视觉核验。
    - 判断置信度：medium；规则：`05-figures-and-charts#caption_not_self_contained`；复核（作者，P2）：明确 J-M 相对损伤的测量时点。
    - 证据：[EV-054｜figure/¶fig1-caption-full/Fig 1] [EV-065｜results/¶results-sec022-p4]

### [minor] CL-053 · 图注未定义显著性符号标注约定

- 类别：significance_undefined
- 锚点：¶figure-captions；成员：M5-017
- 关联判断：
  - **M5-017** [minor] (M5) 图注未定义显著性符号标注约定
    - 详情：Fig 1 与 Fig 3 图注均未说明显著性符号（星号/括号）的含义；Fig 2 仅对面板 D 注明 'Black brackets are shown for those comparisons that are statistically significant'。Methods sec020 仅给出全局 P<0.05。各面板实际使用何种标注需视觉核验（本环境无图像输入）。
    - 判断置信度：medium；规则：`05-figures-and-charts#significance_undefined`；复核（领域审稿人，P2）：视觉核验各面板显著性标注并与图注对照。
    - 证据：[EV-095｜缺失检索：figure｜no_match] [EV-055｜figure/¶fig2-caption-full/Fig 2]

### [minor] CL-055 · 饲养与照护条件缺失

- 类别：ETH-ANI-003
- 锚点：¶methods-sec004；成员：M6-006
- 关联判断：
  - **M6-006** [minor] (M6) 饲养与照护条件缺失
    - 详情：全文无笼内密度、丰容、光周期、温湿度、垫料、饲料、屏障等级/SPF 状态、到达后适应期的任何描述；sec004 仅称 'handled, housed, and matched by age and sex as outlined above' 而无实质内容。属 ARRIVE 2.0 Item 7 与 PLOS ONE 动物报告要求项。
    - 判断置信度：high；规则：`06-ethics-compliance#ETH-ANI-003`；复核（作者，P2）：按 ARRIVE Item 7 补充饲养条件（设施等级、光周期、温湿度、笼内密度、丰容）。
    - 证据：[EV-075｜缺失检索：methods｜no_match] [EV-059｜methods/¶methods-sec004-b]

### [minor] CL-056 · 材料可得性声明与实际可分发途径不符（Dryad 不能分发小鼠品系/质粒）

- 类别：data_materials_availability
- 锚点：¶data-availability；成员：M6-007
- 关联判断：
  - **M6-007** [minor] (M6) 材料可得性声明与实际可分发途径不符（Dryad 不能分发小鼠品系/质粒）
    - 详情：Data Availability 称 datasets and materials 置于 Dryad（DOI: 10.5061/dryad.3j9kd51vx），但 Ager KO/sRAGE 敲入小鼠、mdx/ApoE-/-/db/db 品系及 scAAV-Cbh-sRAGE 质粒均属实体生物材料，无法经 Dryad 分发；未见质粒入库（如 Addgene）或 MTA 获取途径声明。X1 对 Dryad connector 沉默（not_addressed），不作反证。
    - 判断置信度：high；规则：`06-ethics-compliance#data_materials_availability`；复核（编辑，P2）：要求作者分别声明各小鼠品系与 AAV 质粒的获取途径（MTA/库藏）及限制条件。
    - 证据：[EV-026｜data_availability/¶notes1] [EV-063｜methods/¶methods-sec003-c] [EV-044｜methods/¶methods-sec013]

### [minor] CL-058 · 动物总数估计 >200，无样本量论证或 Reduction 说明（06b 红线 vs 06 cap 裁定维持 minor）

- 类别：ETH-ANI-002
- 锚点：¶figure-captions；成员：M6-009、M6-010
- 关联判断：
  - **M6-009** [minor] (M6) 动物总数估计 >200，无样本量论证或 Reduction 说明（06b 红线 vs 06 cap 裁定维持 minor）
    - 详情：伦理工具 SIG-602（sample_size_justification 未报告）与动物模型审计 SIG-701（Reduction not_justified）双重确认。按图注累计全研究总数粗估 200-400 只，形式上触发 06b 红线 4。裁定维持 minor：(1) 06 主规则防误报守则（缺样本量说明最高 minor）规范效力优先；(2) 纯报告缺口且有 IACUC 批准，不得由'没写'推定'未做'；(3) 单组 n=3-10 属正常偏小规模，不符合 excessive numbers 实质。升级条件：作者确认协议层面亦无数量论证。
    - 判断置信度：high；规则：`06b-animal-model-ethics-enhancement#ETH-ANI-002-redline4`；复核（伦理委员会，P2）：向作者索取样本量依据与总动物数汇总；依据回复决定是否升 major。
    - 证据：[EV-017｜缺失检索：methods,results｜no_match] [EV-054｜figure/¶fig1-caption-full/Fig 1]；工具信号：SIG-602、SIG-701
  - **M6-010** [minor] (M6) 无 3R 原则声明（SIG-701 确认三项均缺；裁定维持 minor）
    - 详情：SIG-701 确认 Replacement(not_discussed)/Reduction(not_justified)/Refinement(not_detailed)。06b 建议两项以上缺失为 major，与 06 主规则'仅报告缺口为 minor'冲突，裁定维持 minor：核心规范库明文 cap 优先；IACUC 批准可推定立项阶段经过 3R 评估；稿件含实质 Refinement 细节（miR122t 肝去靶向、眼部护理、软落床/训练适应），并非实质未实施。
    - 判断置信度：high；规则：`06b-animal-model-ethics-enhancement#ETH-ANI-002-three-rs`；复核（作者，P2）：补充一句 3R 声明（替代评估、数量控制与已实施的优化措施），非拒稿性要求。
    - 证据：[EV-078｜缺失检索：discussion,methods｜no_match]；工具信号：SIG-701

### [minor] CL-059 · 跑台电刺激与力竭终点、重复尾静脉采血的刺激参数/终止标准未报告

- 类别：animal_welfare_refinement
- 锚点：¶methods-sec019；成员：M6-011
- 关联判断：
  - **M6-011** [minor] (M6) 跑台电刺激与力竭终点、重复尾静脉采血的刺激参数/终止标准未报告
    - 详情：sec019 以电刺激驱赶小鼠跑至力竭，未报告电刺激强度/持续时间、力竭判定标准与恢复观察，受试含 18 月龄老龄与 db/db 肥胖鼠；Fig 1D/G 动力学需多时间点重复尾静脉采血（每次 50 μL），未报告采血方式/麻醉/间隔与累积采血量限制。属 ARRIVE Item 5 周边的 Refinement 报告缺口，非福利红线。
    - 判断置信度：medium；规则：`06b-animal-model-ethics-enhancement#animal_welfare_refinement`；复核（伦理委员会，P2）：补充电刺激参数、力竭判定标准与重复采血方案（含麻醉/最大采血量）。
    - 证据：[EV-048｜methods/¶methods-sec019] [EV-043｜methods/¶methods-sec011-b]

### [minor] CL-060 · 老龄动物（18 月龄）手术与多重操作的围术期监测缺失

- 类别：ETH-ANI-004
- 锚点：¶methods-sec006；成员：M6-012
- 关联判断：
  - **M6-012** [minor] (M6) 老龄动物（18 月龄）手术与多重操作的围术期监测缺失
    - 详情：18 月龄 C57BL/6J 接受皮肤切口 cryoinjury、retro-orbital AAV 注射、跑台力竭与双损伤模型，围术期风险高于成年鼠；全文无术后监测频率、疼痛评分或体重下降干预阈值的报告（体重仅作为实验终点 Fig 1J，非福利监测）。与 M6-005 关联但聚焦老龄特殊照护义务。
    - 判断置信度：medium；规则：`06b-animal-model-ethics-enhancement#geriatric_animal_care`；复核（伦理委员会，P2）：索取老龄组术后监测方案与是否有老龄鼠死亡/剔除（含剔除数）。
    - 证据：[EV-006｜methods/¶methods-sec006] [EV-011｜methods/¶methods-sec017] [EV-059｜methods/¶methods-sec004-b]

### [minor] CL-068 · 结论性章节多处措辞与自身数据/事实不符

- 类别：claim_magnitude_mismatch
- 锚点：¶discussion-sec025；成员：M7-011
- 关联判断：
  - **M7-011** [minor] (M7) 结论性章节多处措辞与自身数据/事实不符
    - 详情：逐项核实：(1) 摘要 'acute induction' 描述 AAV 表达，而 Fig 1D/1G 显示 d5 起持续至少 30 天；(2) Discussion p2 'RAGE ligands are chronically activated'——配体不能被 activated；(3) p3 'reduced vascular modeling'（应 remodeling）；(4) Results sec022 称 7-8 月龄为 young 而 Discussion p4 称同一队列 older adult cohort；(5) 摘要 'knockin supplementation strategies were developed' 但 s 品系取自 NIA、AGER+/- 取自 Brown（致谢佐证）；(6) sRAGE 'essentially functions as a soluble decoy' 忽略异构体差异（依赖引文，标注受限）；(7) Layer4 补充：转基因 BaCl2 队列实为 7-8 月龄（S3 图注），摘要却称 in aged or diseased mice；(8) 收编 G-56：'first study' 优先权声明绝对化且无支撑引文（ References 剥离使实质核验受限）。
    - 判断置信度：medium；规则：`07-conclusions-discussion#claim_magnitude_mismatch`；复核（编辑，P2）：编辑层面逐条修正措辞。
    - 证据：[EV-041｜abstract/¶abstract-p1] [EV-037｜discussion/¶discussion-p2] [EV-039｜discussion/¶discussion-p3] [EV-066｜introduction/¶intro-p3]

### [minor] CL-070 · 'in all mice ~10-fold' 无个体应答变异展示、无暴露-效应相关分析

- 类别：effect_size_reporting
- 锚点：Fig Fig 1D/G／¶results-sec022-p2；成员：M4-010
- 关联判断：
  - **M4-010** [minor] (M4) 'in all mice ~10-fold' 无个体应答变异展示、无暴露-效应相关分析
    - 详情：（Layer 4 收编 G-40：原被 M4 refine 后无接收方）sec022 的群体性断言未展示个体应答变异，若存在无应答亚群则组效应可能被应答者驱动；且没有任何个体水平循环 sRAGE 与 CSA 的相关分析。图内散点可核验性受图像输入限制；组级动力学已支持暴露建立，不动摇核心结论，故定 minor。
    - 判断置信度：medium；规则：`04-statistics#effect_size_reporting`；复核（统计审稿人，P2）：在有图像能力时核验 Fig 1D/1G 个体散点；建议作者补充 sRAGE 暴露与 CSA 的个体水平相关分析。
    - 证据：[EV-031｜results/¶results-sec022-p3] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [info] CL-039 · sec015 整段方法带引号照抄已发表方案，引文在提供文本中不可核

- 类别：method_reporting_incomplete
- 锚点：¶methods-sec015；成员：M3-018
- 关联判断：
  - **M3-018** [info] (M3) sec015 整段方法带引号照抄已发表方案，引文在提供文本中不可核
    - 详情：sec015 以 'In brief,' 开头并在整段 HPLC 流程外加引号，注明来自 'published protocols []'；提供文本中引用标记为空（References 被剥离，系统限制），无法核实引文目标与保真度。以通用方案替代实际执行参数损害可重复性。
    - 判断置信度：high；规则：`03-experimental-methods#method_reporting_incomplete`；复核（编辑，P2）：核对正式稿引用编号对应文献是否为该 HPLC 方案原始出处。
    - 证据：[EV-051｜methods/¶methods-sec015]

### [info] CL-042 · 小鼠血糖用临床人体血糖仪未做种属验证

- 类别：endpoint_proxy_questionable
- 锚点：¶methods-sec012；成员：M3-028
- 关联判断：
  - **M3-028** [info] (M3) 小鼠血糖用临床人体血糖仪未做种属验证
    - 详情：sec012 以 OneTouch Ultra 2 血糖仪直接测量小鼠尾静脉血，未说明针对小鼠样本的验证或校准；人体血糖仪用于小鼠存在已知准确性局限。db/db 组血糖为关键疾病表型读数。
    - 判断置信度：medium；规则：`03-experimental-methods#endpoint_proxy_questionable`；复核（作者，P2）：可作为透明度建议补充说明。
    - 证据：[EV-053｜methods/¶methods-sec012]

### [info] CL-045 · Fig 1-3 完整图注在提取全文中被逐字重复进 Results 正文（疑似提取伪影）

- 类别：redundant_presentation、panel_reference_broken
- 锚点：¶results-sec021；成员：M5-005、M5-019
- 关联判断：
  - **M5-005** [info] (M5) Fig 1-3 完整图注在提取全文中被逐字重复进 Results 正文（疑似提取伪影）
    - 详情：提取文本中 Fig 1/2/3 的 CAPTION 之后紧随一段与其逐字相同的段落（fulltext.txt 行 85-86、94-95、102-103）。该重复更像 PDF/HTML 转换时图注泄漏至正文流的提取伪影，而非已发表稿件的实际缺陷。
    - 判断置信度：low；规则：`05-figures-and-charts#redundant_presentation`；复核（编辑，P2）：对照已发表 PDF 确认正文是否真有重复段落；若无则归为提取伪影。
    - 证据：[EV-071｜results/¶results-sec021-repeat]
  - **M5-019** [info] (M5) 提供文本中图引用被剥离为残余括号，面板引用核对受限（疑似提取伪影）
    - 详情：Results/Discussion 多处图引用仅剩面板字母或完全为空：'( and )'、'( A–F)'（S1）、'( D–F)'（S2）、'( A–C)'（S2/S3）、'(– Fig )'（sec024）。图号缺失导致正文引用顺序与面板对应只能依赖图注面板清单推断；应核对已发表版本确认无真实引用断裂。
    - 判断置信度：medium；规则：`05-figures-and-charts#panel_reference_broken`；复核（编辑，P2）：对照已发表 PDF 复核图引用完整性。
    - 证据：[EV-072｜results/¶results-fig-refs]

### [info] CL-048 · 系统限制：无图像输入；确定性像素审计已执行且无可疑候选；S1-S3 TIF 与无名 PDF 未提供

- 类别：figure_unreadable
- 锚点：¶all-figures；成员：M5-008
- 关联判断：
  - **M5-008** [info] (M5) 系统限制：无图像输入；确定性像素审计已执行且无可疑候选；S1-S3 TIF 与无名 PDF 未提供
    - 详情：figure_integrity_audit 已对 6 个提供文件执行：检出的 48+49+209 处候选重复区块全部为同图不同分辨率副本（.png vs .small.png）间的跨文件比对（r>0.99、坐标一一对应），可完全用降采样副本解释；未检出任何图内跨面板重复候选，不构成稿件图像完整性疑点。保留局限：本会话无图像通道，条带身份、门控图、散点、标尺、形态学质量等视觉判据未覆盖；审计不覆盖旋转/缩放重复；S1-S3 TIF 与 sec027 无图注的 '(PDF)' 条目（疑似原始 WB 记录）supplement_inaccessible。
    - 判断置信度：high；规则：`05-figures-and-charts#figure_unreadable`；复核（领域审稿人，P2）：旋转/缩放重复检测能力未实现，如后续工具可用应补跑；S 图与 PDF 原件需另行索取。
    - 证据：[EV-097｜figure/¶fig-assets/Fig 1] [EV-056｜supplement/¶s1-caption]

### [info] CL-057 · 提供稿件中未见 Author Contributions（CRediT）声明

- 类别：reporting_completeness
- 锚点：¶front-matter；成员：M6-008
- 关联判断：
  - **M6-008** [info] (M6) 提供稿件中未见 Author Contributions（CRediT）声明
    - 详情：提供的全文材料（FRONT/Abstract/正文/Acknowledgments/Data Availability/Funding/Author Notes）中检索 author contribution/CRediT 零命中；PLOS ONE 要求 CRediT 作者贡献声明。可能为抽取/排版剥离，需以正式发表版核对，不作为确定缺陷。
    - 判断置信度：low；规则：`06-ethics-compliance#reporting_completeness`；复核（编辑，P2）：对照 PLOS ONE 正式发表版核对 Author Contributions 是否存在；若存在则撤销本条。
    - 证据：[EV-096｜references/¶ref-list1]

### [info] CL-061 · 遗传修饰动物品系的福利影响未评估说明

- 类别：animal_model_welfare_gm
- 锚点：Fig Fig 3A／¶methods-sec003；成员：M6-013
- 关联判断：
  - **M6-013** [info] (M6) 遗传修饰动物品系的福利影响未评估说明
    - 详情：Ager KO（exon 2-7 缺失）与 sRAGE 敲入（exon 10-11 替换+2A-EGFP）为全身性终身遗传修饰，需繁殖维持多窝系，未见对遗传修饰动物健康/福利影响的任何说明（ARRIVE 2.0 Item 10c）。两条品系为已发表品系，未见异常表型提示，风险低。X1 MGI 等位基因核验本会话无 connector，登记为受限。
    - 判断置信度：medium；规则：`06b-animal-model-ethics-enhancement#animal_model_welfare_gm`；复核（作者，P2）：说明 Ager 修饰品系是否存在已知健康表型及繁殖中的基因型筛选策略。
    - 证据：[EV-063｜methods/¶methods-sec003-c] [EV-035｜figure/¶fig3A-caption/Fig 3A]

### [info] CL-062 · AAV9 基因治疗生物安全声明未见，但适用性不构成缺口

- 类别：biosafety_aav_vector
- 锚点：¶methods-sec014；成员：M6-014
- 关联判断：
  - **M6-014** [info] (M6) AAV9 基因治疗生物安全声明未见，但适用性不构成缺口
    - 详情：研究后眶注射 scAAV9（1e11 vg/鼠，复制缺陷型、非病原）；病原微生物适用条件不成立。IBSC/IBC 类审查在美国通常并入 IACUC 方案（#29-14）。未见动物水平载体毒性监测，但 miR122t 肝去靶向属主动优化。仅备查。
    - 判断置信度：low；规则：`06b-animal-model-ethics-enhancement#biosafety_aav_vector`；复核（伦理委员会，P2）：无需作者行动；如编辑关注基因治疗合规，可确认 #29-14 方案是否含重组 DNA/IBC 审查。
    - 证据：[EV-011｜methods/¶methods-sec017]

### [info] CL-063 · 利益冲突披露存在且充分（预防误报记录）

- 类别：conflict_of_interest
- 锚点：¶author-notes；成员：M6-015
- 关联判断：
  - **M6-015** [info] (M6) 利益冲突披露存在且充分（预防误报记录）
    - 详情：Author Notes 已完整披露 AJW 任 Kate/Frequency Therapeutics 顾问、为 Elevian Inc. 联合创始人/SAB/持股、Elevian 赞助 Wagers 实验室；本研究主题（sRAGE 促再生、面向再生治疗）与 Elevian 商业方向高度相关，披露必要且已到位，符合 ICMJE/PLOS 要求。结论倾向性与商业利益的关联属编辑裁量（M7），非 M6。
    - 判断置信度：high；规则：`06-ethics-compliance#conflict_of_interest`；复核（编辑，P2）：无需行动；编辑可留意 Elevian 关联与结论倾向性。
    - 证据：[EV-025｜declarations/¶author-notes]

## 五、抽取信号

> 机器观察与路由轨迹，不是稿件问题，没有 severity，不直接进入风险分。共 13 条。

- `SIG-602` · `ethics_requirement_unmet` → ethics.ETH-ANI-002
  - [ETH-ANI-002] 3R 原则：规范要求稿件报告 three_rs_consideration，已完整检索确认 measurement.sample_size_justification 未报告。
  - 路由：M6；产出：`stage_2`；证据：[EV-017｜缺失检索：methods,results｜no_match]
- `SIG-604` · `partial_extraction` → ethics.ETH-ANI-004
  - [ETH-ANI-004] 麻醉、镇痛与人道终点：适用性事实（involves_pain_or_distress）无法从结构化结果可靠推出，工具未评估；M6 已据全文原文覆盖确认未报告（见 M6-004）。
  - 路由：M6；产出：`stage_2`；证据：[EV-006｜methods/¶methods-sec006] [EV-076｜缺失检索：methods｜no_match]
- `SIG-605` · `partial_extraction` → ethics.ETH-ANI-005
  - [ETH-ANI-005] 安乐死方法：适用性事实（animals_euthanized）无法从结构化结果可靠推出，工具未评估；M6 已据全文原文覆盖确认未报告（见 M6-005）。
  - 路由：M6；产出：`stage_2`；证据：[EV-074｜缺失检索：methods｜no_match] [EV-006｜methods/¶methods-sec006]
- `SIG-606` · `partial_extraction` → ethics.ETH-ANI-006
  - [ETH-ANI-006] 中国实验动物许可证制度：适用性事实（jurisdiction_hint）无法推出。本研究为美国哈佛大学动物实验，该条实际不适用；partial 反映工具保守性，不构成稿件问题。
  - 路由：M6；产出：`stage_2`
- `SIG-607` · `partial_extraction` → ethics.ETH-HGR-001
  - [ETH-HGR-001] 中国人类遗传资源：适用性事实无法推出；本研究无人类成分，实际不适用，不构成稿件问题。
  - 路由：M6；产出：`stage_2`
- `SIG-701` · `ethics_requirement_unmet` → ethics.ETH-ANI-002
  - [ETH-ANI-002] 3R Principle: Replacement(not_discussed); Reduction(not_justified); Refinement(not_detailed)
  - 路由：M6；产出：`stage_2`；证据：[EV-078｜缺失检索：discussion,methods｜no_match]
- `SIG-702` · `ethics_requirement_unmet` → ethics.animal_welfare.painful_procedure_no_anesthesia
  - animal_model_compliance 检出 surgery 而 anesthesia=null（welfare violation severity_hint=critical）。M6 人工定性：属『部分操作有麻醉（retro-orbital isoflurane）、多处有创操作（cryoinjury、BaCl2 肌注、移植注射）无麻醉/镇痛报告』，按报告缺口维持 major 不升 critical（M6-004）。
  - 路由：M6；产出：`stage_2`；证据：[EV-006｜methods/¶methods-sec006] [EV-011｜methods/¶methods-sec017] [EV-076｜缺失检索：methods｜no_match]
- `SIG-501` · `figure_integrity_candidate` → figure_integrity.pone.0318754.g001.png
  - 检出 48 处候选重复区块（64×64）：pone.0318754.g001.png ↔ pone.0318754.g001.small.png，最高像素相关 r=0.9991。全部候选为同一图像不同分辨率副本间的跨文件比对（预期伪重复），无图内跨面板重复候选。仅候选，须人工核对。
  - 路由：M5；产出：`stage_3`；证据：[EV-097｜figure/¶fig-assets/Fig 1]
- `SIG-502` · `figure_integrity_candidate` → figure_integrity.pone.0318754.g002.png
  - 检出 49 处候选重复区块：pone.0318754.g002.png ↔ pone.0318754.g002.small.png，最高 r=0.9991；同上为降采样副本伪重复，无图内跨面板重复候选。
  - 路由：M5；产出：`stage_3`；证据：[EV-097｜figure/¶fig-assets/Fig 1]
- `SIG-503` · `figure_integrity_candidate` → figure_integrity.pone.0318754.g003.png
  - 检出 209 处候选重复区块：pone.0318754.g003.png ↔ pone.0318754.g003.small.png，最高 r=0.9996；同上为降采样副本伪重复，Fig 3F 各基因型 H&E 与 Fig 3C WB 条带间均无重复候选。
  - 路由：M5；产出：`stage_3`；证据：[EV-097｜figure/¶fig-assets/Fig 1]
- `SIG-801` · `sequence_identifier_inconsistent` → bGH-Forward (AAV titration, Methods sec016)
  - 引物 GCCAGCCATCTGTTGT 的常规参数存在偏离：估算 Tm 45.9°C 超出常规 50–68°C（16 nt, GC 56.2%）。候选，交人工确认。
  - 路由：M3；产出：`stage_2`；证据：[EV-052｜methods/¶methods-sec016]
- `SIG-802` · `sequence_identifier_inconsistent` → bGH-Reverse (AAV titration, Methods sec016)
  - 引物 GGAGTGGCACCTTCCA 参数偏离：GC 62.5% 超出常规 40–60%；估算 Tm 48.5°C 超出 50–68°C（16 nt）。候选，交人工确认。
  - 路由：M3；产出：`stage_2`；证据：[EV-052｜methods/¶methods-sec016]
- `SIG-803` · `sequence_identifier_inconsistent` → ItgB7 vs Itgb1 (Fig 3 I/J caption vs Methods sec007)
  - 基因符号 'ItgB7' 的书写与小鼠命名惯例（MGI：首字母大写其余小写，如 Itgb7）不符。候选：可能是物种张冠李戴或引用直系同源基因——交人工确认。支持 M3-004（CD29 vs ItgB7 冲突）。
  - 路由：M2、M3；产出：`stage_2`；证据：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-045｜methods/¶methods-sec007]

## 六、系统限制

> 本节说明系统或输入"哪些地方没看清"。这些条目不是稿件问题，不得据此推断作者遗漏或违规。共 6 条。

- `SYS-001` · `figure_unreadable`：本环境无图像输入能力：figures/ 下 3 张主图 PNG（及降采样副本）存在但无法进行视觉解读。条带身份、FACS 门控图、散点分布、误差棒、显著性括号、scale bar、形态学质量等图内判据均未覆盖；所有图相关审核仅基于图注文字与正文交叉比对。不得据此推断图内数据无问题。
  - 受影响模块：M3、M4、M5、M7；目标：fig:1、fig:2、fig:3
  - 恢复动作：由具备图像判读能力的人工/系统复核 Fig 1-3（重点：Fig 3C WB、Fig 3I/J dystrophin 通道、各面板显著性标注与损伤面积可比性）。
  - 定位：[EV-097｜figure/¶fig-assets/Fig 1]
- `SYS-002` · `supplement_inaccessible`：S1-S3 TIF 文件与 sec027 一条无图注的 (PDF) 支持信息条目（疑似原始 WB 记录）未随材料提供。支撑核心结论（损伤模型二象性）的全部 BaCl2 阴性证据不可核验；Fig 3C loading control 核验缺少原始 blot。
  - 受影响模块：M2、M4、M5；目标：S1 Fig、S2 Fig、S3 Fig、S-PDF
  - 恢复动作：向期刊/作者索取 S1-S3 TIF 与原始 blot PDF 后重新审核相关主张。
  - 定位：[EV-056｜supplement/¶s1-caption] [EV-057｜supplement/¶s2-caption] [EV-058｜supplement/¶s3-caption]
- `SYS-003` · `section_missing_from_input`：提供材料中 References 节为空、正文引文标记被剥离为占位符（'[]'/'[,]''/[–]'）。所有依赖文献的核验（'first study' 优先权声明、RAGE-KO 表型引文、sec015 照抄方案的原始出处、decoy 异构体表述）不可行。这是输入材料限制，不是稿件缺陷；已按系统限制处理的条目：G-44、G-56、G-63、G-60/G-20 的引文依赖部分。
  - 受影响模块：M2、M7；目标：references
  - 恢复动作：以正式发表版（PDF/JATS 含完整参考文献）重跑引文相关核验。
  - 定位：[EV-096｜references/¶ref-list1]
- `SYS-004` · `external_source_unavailable`：X1 外部核验：Dryad connector 对 DOI 10.5061/dryad.3j9kd51vx 沉默（not_addressed），未产生外部事实。不得据此判定数据不可得或声明有误；仅降低数据可得性声明的外部核验覆盖。
  - 受影响模块：M6；目标：Dryad DOI: 10.5061/dryad.3j9kd51vx
  - 恢复动作：connector 恢复后重跑 Dryad 记录核验；或由人工访问数据集页面确认。
  - 定位：[EV-026｜data_availability/¶notes1]
- `SYS-005` · `external_source_unavailable`：X1 外部核验：animal_model_compliance 产出的 MGI 品系身份核验候选（C57BL/6J 及 Ager 等位基因）无可用 connector，未执行。不影响本轮任何 finding 定级；等位基因/品系身份外部核验留待恢复后补做。
  - 受影响模块：M3、M6；目标：ethics.animal_model_identity
  - 恢复动作：MGI connector 接入后补做等位基因身份核验。
- `SYS-006` · `input_truncated`：提供文本中 Fig 2 与 Fig 3 图注在约 2000 字符处被截断（'... (line truncated'）；图注统计方法清单的尾部内容（如 Fig 3 完整检验列表、Fig 2 'All mice were ...' 尾句）仅能部分核验。相关判定（M4-005/M5-017 等）均基于可见部分，置信度已相应调整。
  - 受影响模块：M4、M5；目标：fig:2 caption、fig:3 caption
  - 恢复动作：以完整版稿件（PLOS ONE 发表版）核对 Fig 2/Fig 3 图注全文。
  - 定位：[EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-034｜figure/¶fig3-caption-full/Fig 3]

## 七、覆盖率明细

| 子率 | 分子 / 分母（rate） |
| --- | ---: |
| 条件必填字段解析率 | 22/23（0.9565） |
| 图表可读率 | 0/6（0.0） |
| 补充材料可得率 | 0/4（0.0） |

- 已解析的条件必填字段（22）：`objective.research_question`、`objective.hypothesis`、`objective.primary_endpoint`、`objective.secondary_endpoints`、`population.subjects`、`population.inclusion_criteria`、`population.exclusion_criteria`、`design.interventions`、`design.controls`、`design.randomization`、`design.allocation_concealment`、`design.follow_up`、`measurement.assays`、`measurement.statistical_methods`、`measurement.sample_size_justification`、`measurement.missing_data_handling`、`conclusion.limitations`、`conclusion.generalization_scope`、`declarations.ethics_statement`、`declarations.funding`、`declarations.conflict_of_interest`、`declarations.data_availability`
- 未解析的条件必填字段：design.blinding（ambiguous，仅切片分析盲法被报告，其余环节未说明）
- 不可读图表：fig:1、fig:2、fig:3、S1 Fig、S2 Fig、S3 Fig（无图像输入能力 + S 图未提供）
- 不可得补充材料：S1 Fig、S2 Fig、S3 Fig、S-PDF

> `not_reported` 表示已完成规定范围检索并确认稿件未报告，属于"已解析"；`parse_failed` 表示系统没读出来，属于"未解析"。图像可读率 0/6 与补充材料可得率 0/4 直接把抽取覆盖率压到 0.574：这不是稿件质量差，而是本次审核的输入可及性差，结论应据此谨慎对待。

## 八、人工复核建议

| 优先级 | 排序依据 | 完成时点 |
| --- | --- | --- |
| P0 | 全部 critical；以及不先核对就无法可靠解释核心结论、伦理授权或数据完整性的 major | 形成审稿结论前 |
| P1 | 其他 major：会改变 finding 的成立、严重度或作者必须完成的分析/材料补充 | 给出修改要求前 |
| P2 | minor/info 的报告澄清、定位核对或编辑性修正 | 常规修订清单中 |

### [ ] [P0] 核对正式稿 Discussion 首段措辞；要求作者提供 年龄×系统×损伤模型 完整结果矩阵并改写该段；确认成年 AAV 阴性是否有任何限定性讨论。

- 执行者：领域审稿人
- 关联 finding：M2-001 [critical] Discussion 首段对主结果矩阵的系统性误述
- 证据起点：[EV-030｜discussion/¶discussion-p1] [EV-031｜results/¶results-sec022-p3]

### [ ] [P0] 人工复核 Fig 3G/H 原图 KO 组数据与显著性标注；要求作者报告 -/-、s/-、+/- 全部基因型结果及 -/- vs s/s 的正式统计检验。

- 执行者：领域审稿人
- 关联 finding：M2-002 [critical] Fig 3G 含 knockout 组但 Ager-/- 等基因型冷冻伤结果在 Results 通篇未陈述
- 证据起点：[EV-033｜results/¶results-sec024] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [ ] [P0] 要求作者报告 Ager-/- vs AGERs/s 头对头比较，或撤下'两套系统相互印证'表述并明确 s 等位基因的双重扰动；要求跨实验归一比较两系统循环 sRAGE 暴露水平。

- 执行者：领域审稿人
- 关联 finding：M2-003 [critical] 两套'互补'系统扰动不同构：s 等位基因即全长 RAGE-null
- 证据起点：[EV-035｜figure/¶fig3A-caption/Fig 3A] [EV-041｜abstract/¶abstract-p1]

### [ ] [P0] 复核 Fig 1/2/3 与 S1-S3 H&E 各组损伤区横截面积是否可比；要求作者提供金属棒规格、预冷标准化程序及损伤面积量化数据。

- 执行者：领域审稿人
- 关联 finding：M3-001 [critical] Cryoinjury 未标准化且组织学取样规则偏向再生最佳区域
- 证据起点：[EV-006｜methods/¶methods-sec006]

### [ ] [P0] 复核 Fig 1E/1H、Fig 2E/2K、Fig 3G 是否仅提供 7 dpi 单点 CSA；确认全文无任何时间序列或再生指数数据；评估 'accelerates' 是否可改为 'larger regenerating fibers at 7 dpi'。

- 执行者：领域审稿人
- 关联 finding：M7-001 [critical] 标题/摘要的 'accelerates/enhances regeneration' 仅由单一 7 dpi 时间点、单一偏倚取样的 CSA 终点支撑
- 证据起点：[EV-006｜methods/¶methods-sec006] [EV-042｜title/¶title-p1]

### [ ] [P0] 核对 Fig 1E（成年 AAV 臂）组间差异方向与显著性标记；确认 Discussion 首段是否有任何限定词覆盖 adult AAV 臂。

- 执行者：领域审稿人
- 关联 finding：M7-002 [critical] Discussion 首段宣称成年/老龄/疾病小鼠在两套系统中均出现显著纤维增大，与自身成年 AAV 阴性数据方向相反
- 证据起点：[EV-030｜discussion/¶discussion-p1] [EV-031｜results/¶results-sec022-p3]

### [ ] [P1] 要求作者在 cryoinjury 背景或同基因型受体中提供阳性对照数据与未移植对照，否则将'微环境是关键'降级为推测。

- 执行者：领域审稿人
- 关联 finding：M2-004 [major] 移植机制结论建立在 sRAGE 无效背景上的 null result
- 证据起点：[EV-062｜results/¶results-sec024-p3] [EV-002｜methods/¶methods-sec009]

### [ ] [P1] 摘要补入糖尿病模型阴性与成年 AAV 阴性；标题对 diseased 加限定（atherosclerotic）；核对正式稿是否已有修订。

- 执行者：编辑
- 关联 finding：M2-005 [major] 标题/摘要选择性报告：阴性模型未披露、'diseased' 无限定
- 证据起点：[EV-042｜title/¶title-p1] [EV-041｜abstract/¶abstract-p1]

### [ ] [P1] 要求提供肌肉/肝脏组织 sRAGE 或转基因表达数据；否则将 microenvironment 表述降级为推测。

- 执行者：领域审稿人
- 关联 finding：M2-007 [major] microenvironment 是全文从未测量的对象
- 证据起点：[EV-041｜abstract/¶abstract-p1] [EV-043｜methods/¶methods-sec011-b]

### [ ] [P1] 删除或限定 'degenerative disorders'，除非补充相应疾病模型的疗效数据。

- 执行者：作者
- 关联 finding：M2-008 [major] 'degenerative disorders' 治疗潜力无对应疗效测量
- 证据起点：[EV-021｜conclusion/¶sec026-p1] [EV-062｜results/¶results-sec024-p3]

### [ ] [P1] 核对 Fig 3 原图面板标注与 Dryad 源数据，确认实际分选标记（CD29 vs ItgB7）并更正图注或 Methods。

- 执行者：领域审稿人
- 关联 finding：M2-009 [major] Fig 3I/J 移植细胞标记（ItgB7+）与 Methods 门控定义（CD29+）冲突
- 证据起点：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-045｜methods/¶methods-sec007]

### [ ] [P1] 要求作者澄清样本类型并说明裂解全血中膜型 RAGE 的贡献；确认图中 'serum sRAGE' 单位与计算基准。

- 执行者：领域审稿人
- 关联 finding：M3-002 [major] 'Serum sRAGE' 实为 RIPA 裂解尾静脉全血，样本类型与全文表述不符
- 证据起点：[EV-043｜methods/¶methods-sec011-b] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [ ] [P1] 核对 R&D MRG00 说明书标准品身份与基质耐受性；要求作者提供回收率/稀释线性数据及上样归一化方式。

- 执行者：领域审稿人
- 关联 finding：M3-003 [major] ELISA（Quantikine MRG00）无方法学确证
- 证据起点：[EV-043｜methods/¶methods-sec011-b] [EV-044｜methods/¶methods-sec013]

### [ ] [P1] 向作者索取移植细胞分选门控记录与 re-analysis 结果，确认实际使用的阳性标记（CD29/Itgb1 vs Itgb7）。

- 执行者：领域审稿人
- 关联 finding：M3-004 [major] 移植细胞身份矛盾：Methods CD29+ vs 图注 ItgB7+
- 证据起点：[EV-045｜methods/¶methods-sec007] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [ ] [P1] 要求作者提供载体 QC 数据（滴度、空壳比、纯度、无菌/内毒素）与 HEK293 细胞来源及支原体检测记录。

- 执行者：领域审稿人
- 关联 finding：M3-005 [major] AAV 载体质控结果缺失且 HEK293 鉴定信息未报告
- 证据起点：[EV-050｜methods/¶methods-sec014-b] [EV-086｜缺失检索：methods｜no_match]

### [ ] [P1] 要求作者明确各实验对照组的确切基因型、来源与同窝状态；核查 db/db 与 WT 背景品系匹配；说明 Ager 两等位基因回交代数与遗传背景均一度。

- 执行者：领域审稿人
- 关联 finding：M3-006 [major] 对照组基因型与遗传背景界定含糊
- 证据起点：[EV-032｜results/¶results-sec023-p1] [EV-063｜methods/¶methods-sec003-c]

### [ ] [P1] 补充各等位基因的分型引物、产物大小与判定标准，或引用原始品系文献中的分型方案。

- 执行者：作者
- 关联 finding：M3-007 [major] 全部基因工程小鼠无基因分型方案
- 证据起点：[EV-077｜缺失检索：methods｜no_match] [EV-063｜methods/¶methods-sec003-c]

### [ ] [P1] 提供扩增引物、测序覆盖范围与重组蛋白验证数据。

- 执行者：作者
- 关联 finding：M3-008 [major] AAV 转导的 sRAGE 转基因异构体未定义、无蛋白水平验证
- 证据起点：[EV-044｜methods/¶methods-sec013]

### [ ] [P1] 复核各图 CSA 每鼠纤维数是否一致；要求作者提供量化规则细节与软件版本。

- 执行者：领域审稿人
- 关联 finding：M3-009 [major] CSA 测量规程不足以支撑组间比较
- 证据起点：[EV-006｜methods/¶methods-sec006]

### [ ] [P1] 提供分选后 re-analysis（纯度/活力）数据或说明。

- 执行者：作者
- 关联 finding：M3-010 [major] 移植供体细胞分选后质量未报告
- 证据起点：[EV-045｜methods/¶methods-sec007] [EV-088｜缺失检索：methods｜no_match]

### [ ] [P1] 要求作者明确深度选取规则与计数归一化方式；复核 Fig 3I/J 原始计数分布。

- 执行者：领域审稿人
- 关联 finding：M3-011 [major] 移植终点计量学缺陷：'averaged from at least 3 depths' 无校正且含糊
- 证据起点：[EV-002｜methods/¶methods-sec009]

### [ ] [P1] 补充力竭判定标准、电刺激参数与悬挂时限；确认体重归一化是否适用。

- 执行者：作者
- 关联 finding：M3-012 [major] 功能实验方法学要素缺失
- 证据起点：[EV-047｜methods/¶methods-sec018] [EV-048｜methods/¶methods-sec019]

### [ ] [P1] 人工复核 Fig 3C 条带数目、重复与组织来源标注（本环境无图像输入）；要求作者补充 sRAGE 阳性对照。

- 执行者：领域审稿人
- 关联 finding：M3-013 [major] Western blot 验证证据薄弱且关键要素缺失
- 证据起点：[EV-046｜methods/¶methods-sec010] [EV-034｜figure/¶fig3-caption-full/Fig 3]

### [ ] [P1] 确认纯化后制剂的空壳比数据是否存在；要求作者在 Limitations 中讨论空衣壳/杂质对照缺失。

- 执行者：领域审稿人
- 关联 finding：M3-014 [major] AAV 干预缺少空衣壳/杂质对照
- 证据起点：[EV-011｜methods/¶methods-sec017] [EV-051｜methods/¶methods-sec015]

### [ ] [P1] 核查 Sigma D8168 产品页宿主种属；复核 Fig 3I/J dystrophin 通道图像染色是否成立；若错误要求作者提供替代验证。

- 执行者：领域审稿人
- 关联 finding：M3-020 [major] Dystrophin 一抗种属标注与已知试剂身份及二抗配置矛盾
- 证据起点：[EV-049｜methods/¶methods-sec008]

### [ ] [P1] 索取/重建 scAAV-CMV-GFP-bGHpA 骨架与最终构件的酶切图谱，确认 bGHpA 是否保留。

- 执行者：领域审稿人
- 关联 finding：M3-021 [major] 滴度引物靶点（bGHpA）与最终构件 polyA（SV40pA）疑似不匹配
- 证据起点：[EV-044｜methods/¶methods-sec013] [EV-052｜methods/¶methods-sec016]

### [ ] [P1] 确认正式稿/补充材料是否包含未移植对照数据；要求补充受体鼠年龄。

- 执行者：作者
- 关联 finding：M3-022 [major] 移植实验缺 mdx 未移植对照以界定背景 dystrophin+ 纤维
- 证据起点：[EV-089｜缺失检索：methods,results｜no_match] [EV-002｜methods/¶methods-sec009]

### [ ] [P1] 明确每基因型供体数与混合策略、受体年龄/体重。

- 执行者：作者
- 关联 finding：M3-023 [major] 移植供体侧计量缺失：供体数目、混合方式与受体特征未报告
- 证据起点：[EV-090｜缺失检索：figure,methods｜no_match] [EV-045｜methods/¶methods-sec007]

### [ ] [P1] 若取得 Dryad 数据，按鼠汇总纤维 CSA 或以鼠为随机效应的混合模型重算各分布面板；向作者索取每鼠纤维数。

- 执行者：统计审稿人
- 关联 finding：M4-001 [major] CSA 纤维分布检验以纤维为分析单元，忽略同鼠聚集（伪重复）
- 证据起点：[EV-006｜methods/¶methods-sec006] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [ ] [P1] 向作者索取逐组实际 n 与删减原因；对 Fig 3 阳性与阴性结论做功效/精度复核（报告效应量与 CI 后判断 n=3-5 能排除的最小效应）。

- 执行者：统计审稿人
- 关联 finding：M4-002 [major] 无样本量依据；图注以 'n≥' 报告，实际组内 n 不可知
- 证据起点：[EV-017｜缺失检索：methods,results｜no_match] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [ ] [P1] 要求作者报告每个比较的精确 P 值与检验统计量/df；Dryad 数据若可取得可直接复算。

- 执行者：统计审稿人
- 关联 finding：M4-003 [major] 全文仅以 'P<0.05' 阈值报告显著性，无精确 P 值、检验统计量、df
- 证据起点：[EV-016｜methods/¶methods-sec020] [EV-055｜figure/¶fig2-caption-full/Fig 2]

### [ ] [P1] 将 Fig 1J-M 视为终点家族做 Holm/Bonferroni 校正复核；确认血糖下降是否被当作独立疗效主张；在有图像能力时核验显著性括号覆盖的对比集合。

- 执行者：统计审稿人
- 关联 finding：M4-004 [major] 多终点重复检验未校正；Fig 1M 血糖为唯一显著结果，假阳性风险高
- 证据起点：[EV-065｜results/¶results-sec022-p4] [EV-054｜figure/¶fig1-caption-full/Fig 1]

### [ ] [P1] 向作者确认各面板实际所用检验；在 Dryad 数据上对 Fig 2E/S2B 补做 two-way ANOVA 交互检验。

- 执行者：统计审稿人
- 关联 finding：M4-005 [major] 2×2 析因设计按单因素 one-way ANOVA 分析，交互项缺失；检验-面板映射不明
- 证据起点：[EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-057｜supplement/¶s2-caption]

### [ ] [P1] 为每个阴性结论补算均差与 95% CI，评估能排除的最小效应量；移植与 db/db 结论改写为「未检出差异」并给出精度范围。

- 执行者：统计审稿人
- 关联 finding：M4-007 [major] 以 null 结果直接接受「无差异」结论，无效应量、CI 或等效性检验
- 证据起点：[EV-031｜results/¶results-sec022-p3] [EV-033｜results/¶results-sec024]

### [ ] [P1] 要求作者提供跨模型循环 sRAGE 暴露的定量比较；讨论单剂量设计对阴性结论解释的影响。

- 执行者：统计审稿人
- 关联 finding：M4-009 [major] 全程单剂量且跨模型暴露量从未定量比较，阴性结论解释力受限
- 证据起点：[EV-011｜methods/¶methods-sec017] [EV-032｜results/¶results-sec023-p1]

### [ ] [P1] 向作者索取 ApoE 臂 WT 数据或解释其移除原因；核对 Fig 2G/S2D 方案图是否因复用 db/db 臂模板而误带 WT。

- 执行者：领域审稿人
- 关联 finding：M5-001 [major] ApoE-/- 臂方案承诺 WT 对照，但 Fig 2H-L 与 S2 E-F 数据面板仅含 ApoE-null
- 证据起点：[EV-055｜figure/¶fig2-caption-full/Fig 2] [EV-057｜supplement/¶s2-caption]

### [ ] [P1] 核对分选记录与抗体（HMβ1-1 为 anti-CD29）；更正图注 ItgB7→CD29/Itgb1 或修正 Methods。

- 执行者：领域审稿人
- 关联 finding：M5-014 [major] Fig 3I/J 图注门控标记 'ItgB7+' 与 Methods 定义的 CD29（β1-integrin）冲突
- 证据起点：[EV-034｜figure/¶fig3-caption-full/Fig 3] [EV-045｜methods/¶methods-sec007]

### [ ] [P1] 建议将至少一个 cryo-vs-BaCl2 汇总比较提升至正文，或确保补充文件随稿件公开可核验。

- 执行者：编辑
- 关联 finding：M5-018 [major] 支撑核心结论（损伤模型特异性）的 BaCl2 阴性结果 S1-S3 全部置于补充材料且本审材料不可核验
- 证据起点：[EV-056｜supplement/¶s1-caption] [EV-057｜supplement/¶s2-caption]

### [ ] [P1] 向作者索取分组随机化方法与各实验 litter 来源数及是否按 litter 分层/入模型；若无法补充，要求在 Limitations 中声明。

- 执行者：伦理委员会
- 关联 finding：M6-001 [major] 全文无随机化描述；多窝来源未作区组/统计因子处理
- 证据起点：[EV-013｜缺失检索：methods｜no_match] [EV-008｜methods/¶methods-sec003]

### [ ] [P1] 向作者索取各操作与功能终点评估的设盲状态；若未设盲，要求评估对主要终点（老龄鼠 CSA、grid hang、treadmill、血糖）的潜在影响。

- 执行者：伦理委员会
- 关联 finding：M6-002 [major] 设盲仅限组织切片分析，手术/注射操作者与功能学评估者未设盲
- 证据起点：[EV-014｜methods/¶methods-sec006-b] [EV-080｜缺失检索：methods｜no_match]

### [ ] [P1] 要求作者补充单性别设计理由，并在 Discussion 中明确结论限于雄性、雌性反应待验证。

- 执行者：伦理委员会
- 关联 finding：M6-003 [major] 仅用雄性小鼠且无单性别理由，未讨论 sex as a biological variable
- 证据起点：[EV-008｜methods/¶methods-sec003] [EV-079｜缺失检索：discussion,methods｜no_match]

### [ ] [P1] 向作者逐项索取 cryoinjury/BaCl2 肌注/移植注射的麻醉与术后镇痛方案（或引证 #29-14 方案内容）；若实际已用而漏写，要求修订 Methods。

- 执行者：伦理委员会
- 关联 finding：M6-004 [major] 多处有创操作的麻醉/镇痛未报告（报告缺口，非确认性福利违反）
- 证据起点：[EV-006｜methods/¶methods-sec006] [EV-002｜methods/¶methods-sec009]

### [ ] [P1] 向作者索取安乐死方法、死亡/剔除动物数及原因、预设人道终点与术后监测频率（尤其老龄组）；请编辑核对 IACUC #29-14 方案是否涵盖上述要素。

- 执行者：伦理委员会
- 关联 finding：M6-005 [major] 安乐死方法缺失；无退出/排除标准、剔除数与人道终点
- 证据起点：[EV-074｜缺失检索：methods｜no_match] [EV-006｜methods/¶methods-sec006]

### [ ] [P1] 确认 Discussion 任何段落是否披露成年 AAV 与 db/db 阴性结果；核对 'universal importance' 是否仍有保留价值。

- 执行者：领域审稿人
- 关联 finding：M7-003 [major] Discussion/Conclusion 以一律阳性口径概括结果，未披露成年 AAV、db/db、全部 BaCl2 臂的阴性结果
- 证据起点：[EV-030｜discussion/¶discussion-p1] [EV-021｜conclusion/¶sec026-p1]

### [ ] [P1] 确认是否存在任何 >7 dpi 的再生终点（含纤维化染色）；评估结论措辞是否需限定为'早期再生阶段'。

- 执行者：领域审稿人
- 关联 finding：M7-004 [major] 无任何晚期结局数据，无法支持'更好的最终修复'类结论
- 证据起点：[EV-031｜results/¶results-sec022-p3] [EV-032｜results/¶results-sec023-p1]

### [ ] [P1] 核对结论是否应限于'aged 与 ApoE-/- 小鼠冷冻伤后早期组织学再生'；确认全文是否有 microenvironment（肌肉局部 sRAGE/配体）测量；'diseased' 限定词由编辑复核。

- 执行者：领域审稿人
- 关联 finding：M7-005 [major] 结论范围外推：degenerative disorders/aging muscle/microenvironment
- 证据起点：[EV-021｜conclusion/¶sec026-p1] [EV-041｜abstract/¶abstract-p1]

### [ ] [P1] 核对 Fig 3I/J 数据分布与变异度、是否存在未移植 mdx 对照的 background dystrophin+ 计数；评估 'microenvironment likely key' 是否需降为'不排除'表述。

- 执行者：领域审稿人
- 关联 finding：M7-006 [major] 移植 null result 推导微环境机制：无效背景、无 CI、RAGE 缺失混杂
- 证据起点：[EV-062｜results/¶results-sec024-p3] [EV-002｜methods/¶methods-sec009]

### [ ] [P1] 读 Fig 3G/H 原始数据确认 Ager-/- 7 dpi CSA 组间差异与变异度（本环境无图像，需人工）；确认 Results 是否应补述 knockout 臂结果。

- 执行者：领域审稿人
- 关联 finding：M7-007 [major] Discussion 对 Ager-/- 冷冻伤结果作'未能复现'推断，该比较在 Results 未被陈述且无 CI/等效性支撑
- 证据起点：[EV-036｜discussion/¶discussion-p4] [EV-033｜results/¶results-sec024]

### [ ] [P1] 确认 Discussion/Conclusion 是否存在任何未被检出的局限性语句（近义表达）；要求作者补充 Limitations。

- 执行者：领域审稿人
- 关联 finding：M7-008 [major] 全文无局限性陈述
- 证据起点：[EV-022｜缺失检索：conclusion,discussion｜no_match] [EV-030｜discussion/¶discussion-p1]

### [ ] [P1] 核对 Fig 1M 与 Fig 2D 效应方向与显著性标记（本环境无图像）；确认 Discussion 任何位置是否提及血糖数据；要求作者调和两处矛盾观察。

- 执行者：领域审稿人
- 关联 finding：M7-009 [major] 唯一显著的功能/代谢结果（老龄血糖下降，Fig 1M）在 Discussion 完全缺席；与 db/db 血糖无改善的矛盾未调和
- 证据起点：[EV-065｜results/¶results-sec022-p4] [EV-032｜results/¶results-sec023-p1]

### [ ] [P1] 与 M4-004 核对同一分析锚点；若 Fig 1M 报告精确 P 值与效应量/CI（图中），请人工读取确认；要求作者以校正后口径表述。

- 执行者：统计审稿人
- 关联 finding：M7-010 [major] Fig 1M 血糖'显著下降'被无保留地写成确证性发现，未提多终点未校正的假阳性风险
- 证据起点：[EV-065｜results/¶results-sec022-p4] [EV-016｜methods/¶methods-sec020]

## 附录 A · 运行时遥测

```json
{
 "child_sessions": 9,
 "task_calls": 13,
 "continuations": 4,
 "modules_run": [
  "M2",
  "M3",
  "M4",
  "M5",
  "M6",
  "M7"
 ],
 "modules_skipped": {},
 "references_required": [
  "02-macro-logic",
  "03-experimental-methods",
  "04-statistics",
  "05-figures-and-charts",
  "06-ethics-compliance",
  "06b-animal-model-ethics-enhancement",
  "07-conclusions-discussion"
 ],
 "references_read": [
  "02-macro-logic",
  "03-experimental-methods",
  "04-statistics",
  "05-figures-and-charts",
  "06-ethics-compliance",
  "06b-animal-model-ethics-enhancement",
  "07-conclusions-discussion"
 ],
 "routing_recall": 1.0,
 "tool_execution_recall": 1.0,
 "global_findings_count": 70,
 "global_findings_confirmed": 70,
 "global_findings_refuted": 0,
 "global_findings_unresolved": 0,
 "additive_guarantee_held": true,
 "findings_added_beyond_global": 65,
 "finding_origin_breakdown": {
  "global_review": 59,
  "specialist_rule": 37,
  "deterministic_tool": 0,
  "external_validation": 0,
  "cross_section_reconciliation": 0,
  "multiple_sources": 0
 }
}
```

- 子会话架构：L0（全局审阅）∥ L0b（测绘路由）→ M2∥M3∥M4∥M5∥M6（并行专家，均读全文）→ M7（串行）→ L2 确定性工具（主会话）→ 4 个续接复议（M3/M4/M5/M6 并行）→ L4 校正 → L5 渲染。共 9 个子会话、13 次 task 调用、4 次续接。
- `additive_guarantee_held=true`：全部 70 条 L0 条目均有终态（58 promoted + 12 merged，0 rejected、0 无故消失），见附录 B。
- 来源分布解读：裸模型（global_review）贡献了全部 critical 中的 5/6 簇与大部分核心问题；专家规则层主要贡献了方法学细目（M3 系列、M4 统计报告、M6 ARRIVE/伦理）、以及 M7 结论维度的独立条目；确定性工具层贡献了引物 QC、命名惯例、图像完整性审计等机器核验面；X1 外部核验贡献 HEK293 身份确认。

**工具执行台账**（每次调用均落终态）：

| 工具 | 状态 | 结果摘要 |
| --- | --- | --- |
| statistical_forensics | executed | 五类检验均无可算对象（全文无精确 P/统计量/df/CI/计数表）——与 M4-003 互证，登记为 CAND-071 |
| ethics_compliance_check | executed | ETH-ANI-002 unmet（SIG-602）；ETH-ANI-004/005 partial 由 M6 以全文覆盖（SIG-604/605）；ETH-ANI-006/HGR-001 partial 属工具保守性（不适用） |
| animal_model_compliance | executed | SIG-701（3R not_justified）、SIG-702（painful procedure no anesthesia, severity_hint critical → M6 人工定性维持 major）、SIG-703（X1 MGI 候选，无 connector → SYS-005） |
| figure_integrity_audit | executed | 6 文件扫描；候选均为降采样副本伪重复；无图内重复候选（SIG-501/502/503） |
| sequence_identifier_audit | executed | bGH 引物 Tm/GC 临界候选（SIG-801/802）；ItgB7 命名惯例候选（SIG-803） |
| external_figure_validation (X1) | executed | HEK293=Cellosaurus CVCL_0045 resolved 无问题标志；Dryad DOI connector 沉默 → SYS-004 |
| normalize_biomed_units | executed | vg/mouse、% 为 unknown_unit（fail-closed）；μL 可比；全文剂量单位内部一致，未发现单位矛盾 |

## 附录 B · L0 全局审阅条目归宿台账（加法保证）

> 70 条 L0 条目全部结清：58 条 promoted_to_finding，12 条 merged（指向合并去向），0 条 rejected，0 条 unresolved。severity 调整 3 处并记录理由（G-31、G-40 下修；G-70 上调）。

| G 条目 | 终态 | 归宿 | 说明 |
| --- | --- | --- | --- |
| G-01 | promoted_to_finding | M2-003 | s 等位基因 full-length RAGE-null；摘要措辞淡化；Discussion p4 自认 lack en… |
| G-02 | promoted_to_finding | M2-002 | 簇内并入 M5-009/M5-015；Ager-/- 结局仅 Discussion p4 带过 |
| G-03 | promoted_to_finding | M7-001 | sec006 证实仅 7dpi 单时间点单 CSA 终点 |
| G-04 | promoted_to_finding | M2-001 | M7-002 同址重复条目并入 CL-001 |
| G-05 | promoted_to_finding | M3-001 | 与 M7-001 为方法缺陷与结论外推两个维度，分列 |
| G-06 | promoted_to_finding | M4-001 | 纤维为检验单元、同鼠聚集未处理 |
| G-07 | promoted_to_finding | M3-002 | sec011 证实 50 μl 全血 + 50 μl RIPA |
| G-08 | promoted_to_finding | M3-003 | ELISA 特异性/基质/回收/归一化均未确证 |
| G-09 | promoted_to_finding | M6-001 | M3-026 收编入簇；litter 聚类另见成员 M4-008 |
| G-10 | promoted_to_finding | M6-002 | 盲法仅限切片编码 |
| G-11 | promoted_to_finding | M6-003 | 仅雄性无 SABV 理由 |
| G-12 | promoted_to_finding | M6-004 | severity 维持 major 不升 critical：报告缺口≠确认未给予麻醉 |
| G-13 | promoted_to_finding | M6-005 | welfare 参数维度另由 M6-011/M6-012 记录 |
| G-14 | promoted_to_finding | M4-002 | 3R/伦理维度另见 M6-009/010 |
| G-15 | merged | M4-002 | 阴性结论接受 H0 的维度另见 M4-007 |
| G-16 | promoted_to_finding | M3-004 | M2-009/M5-014/M3-025 并入 CL-018；序列审计证实 ItgB7 不符命名惯例 |
| G-17 | promoted_to_finding | M2-004 | M7-006、M3-022 并入 CL-006 |
| G-18 | promoted_to_finding | M7-009 | M7-010 并入；多重检验维度见 M4-004 |
| G-19 | promoted_to_finding | M2-007 | 组织来源未鉴定；无组织 sRAGE 结果 |
| G-20 | merged | M7-005 | 机制推测为 hedged；可立案面已入 M7-005/M7-006 |
| G-21 | promoted_to_finding | M7-004 | 再生终点止于 7dpi |
| G-22 | promoted_to_finding | M3-005 | X1 将 HEK293 resolve 为 CVCL_0045 无问题；稿件报告缺口仍成立 |
| G-23 | promoted_to_finding | M4-003 | statistical_forensics 无对象可算与此互证 |
| G-24 | promoted_to_finding | M4-005 | Fig 2E 析因压平 one-way 原文证实 |
| G-25 | promoted_to_finding | M5-001 | 'as expected' 仅用于 db/db 且有数据支撑（表述修正） |
| G-26 | promoted_to_finding | M3-006 | G-28 亦并入本簇 |
| G-27 | promoted_to_finding | M3-007 | 全部基因工程小鼠无基因分型方案 |
| G-28 | merged | M3-006 | L4 自主裁定：M2 判 out_of_scope 转 M3 后无接收方；并入对照基因型/背景含糊簇 |
| G-29 | promoted_to_finding | M3-008 | AAV 表达 sRAGE 异构体未定义 |
| G-30 | promoted_to_finding | M3-009 | CSA 规程不足 |
| G-31 | promoted_to_finding | M5-002 | severity major→minor：限于单句声明；遗传队列有未损伤数据（Fig 3D）（major→minor，理由见台账） |
| G-32 | merged | M2-001 | 同龄成年两系统方向相反强化 Discussion p1 矛盾 |
| G-33 | promoted_to_finding | M3-010 | M3-023 并入 CL-031 |
| G-34 | promoted_to_finding | M3-011 | at least 3 depths 计量含糊 |
| G-35 | promoted_to_finding | M3-012 | welfare 维度另见 M6-011 |
| G-36 | promoted_to_finding | M3-013 | M5-020 并入为成员（loading control 因无图像不可核） |
| G-37 | promoted_to_finding | M7-005 | M2-008 并入 CL-065；安全性张力未讨论 |
| G-38 | promoted_to_finding | M4-009 | L4 新立条目：M4 refine 后无接收方；M3-029 收编为成员（M4 refine 后无接收方 → L4 新立 M4-009） |
| G-39 | promoted_to_finding | M3-014 | vehicle 组成原文证实；无空衣壳对照 |
| G-40 | promoted_to_finding | M4-010 | L4 新立条目；severity major→minor：组级动力学已支持暴露建立（major→minor，L4 新立 M4-010） |
| G-41 | promoted_to_finding | M2-005 | M7-003 并入 CL-007 |
| G-42 | merged | M3-015 | 原接收方 M5-003，并入编辑集群 CL-036 |
| G-43 | promoted_to_finding | M3-015 | 笔误集群原文证实 |
| G-44 | merged | M2-010 | References 为空属系统限制不作稿件缺陷；残留 As expected27 计入编辑集群 |
| G-45 | promoted_to_finding | M5-004 | 2-20 月龄 vs 实际 18 月龄 |
| G-46 | promoted_to_finding | M5-005 | 疑似提取伪影按 info 记录；M5-019 并入 |
| G-47 | promoted_to_finding | M4-006 | 动力学重复采样未说明 |
| G-48 | promoted_to_finding | M4-007 | null ANOVA 直接下无变化结论 |
| G-49 | promoted_to_finding | M6-006 | ARRIVE 饲养照护条件缺失 |
| G-50 | promoted_to_finding | M3-016 | 测试顺序未随机化 |
| G-51 | promoted_to_finding | M5-006 | 仅 Fig 3F 声明代表性 H&E |
| G-52 | promoted_to_finding | M5-007 | Fig 2 图注缺 A) |
| G-53 | promoted_to_finding | M5-008 | 系统限制记录；figure_integrity_audit 无图内重复候选 |
| G-54 | merged | M2-002 | M5-009/M5-015 并入 CL-002 |
| G-55 | promoted_to_finding | M7-011 | L4 补充：转基因 BaCl2 队列实为 7-8 月龄 vs 摘要 aged or diseased |
| G-56 | merged | M7-011 | L4 自主裁定：M2 转 X1 无接收方；绝对化措辞收入集群 |
| G-57 | promoted_to_finding | M6-007 | Dryad connector 沉默按 not_addressed 处理，不作反证 |
| G-58 | promoted_to_finding | M6-008 | 可能为提取遗漏，按 info 留档 |
| G-59 | promoted_to_finding | M5-010 | 队列独立性未声明 |
| G-60 | merged | M7-005 | hedged 假说随范围外推簇处理，不单独立案 |
| G-61 | merged | M2-003 | L4 自主裁定：M2 转 M4 后无 M4 判定；作为两套系统暴露不可比面并入 |
| G-62 | promoted_to_finding | M3-017 | sec015 CV 自相矛盾 |
| G-63 | promoted_to_finding | M3-018 | 引文核验受 References 剥离限制 |
| G-64 | merged | M3-015 | M3-019 承载；并入编辑集群 CL-036 |
| G-65 | merged | M4-004 | 代谢混杂并入多重终点/假阳性风险条目 |
| G-66 | promoted_to_finding | M5-011 | sec023 标题与内容不符 |
| G-67 | promoted_to_finding | M2-006 | central nucleation 从未量化比例 |
| G-68 | promoted_to_finding | M5-012 | 图注无比例尺；图像层面不可核验 |
| G-69 | promoted_to_finding | M5-013 | J-M 相对损伤时点不明 |
| G-70 | promoted_to_finding | M3-020 | severity minor(low)→major：一抗种属记录与已知兔源产品及二抗配置冲突（minor→major，依 M3 refine） |

工具层候选（CAND-071 至 CAND-079）归宿：CAND-071→merged(M4-003)、CAND-072→merged(M5-008)、CAND-073→merged(M3-030)、CAND-074→merged(M3-004)、CAND-075→promoted(M6-004)、CAND-076→promoted(M6-009)、CAND-077→merged(M3-005)、CAND-078/079→blocked_by_system_limitation（SYS-004/SYS-005）。

## 附录 C · 边界声明

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。本 Skill 的任何评分均为筛查信号（screening / triage signal），不构成录用、退稿或发表决定。
