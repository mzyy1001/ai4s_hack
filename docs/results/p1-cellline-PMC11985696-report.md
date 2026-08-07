# 论文审核报告 · Cancer-associated fibroblast heterogeneity in chordoma

> DOI：10.1002/path.6420 ｜ 期刊：The Journal of Pathology 2025;266(1):5-8 ｜ 输入格式：`jats_xml + plain_text（双版本）`
> PMID 40088426 ｜ PMC11985696 ｜ 作者：Jack C Henry; Angus J M Cameron（Barts Cancer Institute, QMUL）
> 文体：**Invited Commentary**（JATS article-type=article-commentary），评述 Zheng BW & Guo W, J Pathol 2025;265:69-83（ref [3]）

## 一、执行摘要

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。** 本 Skill 的任何评分均为筛查信号，不构成录用、退稿或发表决定。

### 本报告能回答什么

> 已执行 M2–M7；"未产出 finding"只表示本流程在已取得证据中未检出，不等于论文结论已被证实。

| 执行模式 | submode | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- |
| `full_review` | — | M2, M3, M4, M5, M6, M7 | 无 |

- 范围依据：评论文体无原始研究设计；路由触发全部来自内容与文体（系统性因果论证→M2；被评论论文体外/体内实验转述+指定细胞系核验→M3；转述的样本量与统计主张→M4；1 图 1 表→M5；COI/基金/被转述人体与动物研究→M6；结论外推与局限性→M7）。M3/M4/M6 以受限范围运行（评论自身无原始方法/统计/伦理批件可审）。
- 已执行阶段：L0 → L0b → L1(M2–M7) → L2(确定性工具+X1) → L3(续接复议×6) → L4(校正) → L5(归一渲染)

**⚠️ 文体与任务前提的重要更正**：任务描述称本文为「人体组织 + 体外细胞系 + 单细胞/免疫组化研究」，但本文实为**受邀评论**（4 页、约 2400 词、无原始实验，Data availability 明示 "no datasets were generated or analysed"）。所述人体组织、细胞实验、异种移植、116 例 QIF、scRNA-seq 等**均属被评论论文 [3] 的转述内容**，其原文（非 OA）不在本次材料中。相应地，**全文无任何具名细胞系**（穷举检索 + 专家独立复核，见六、系统限制与 EV-304）——细胞系核验的正确结果是 `not_applicable`，本报告如实登记而非虚构目标。

### 审稿人先看

- 稿件风险筛查分：`100/100`；分段：`major_revision_suggested`
- 评分边界：分段阈值未经实证验证，是初始经验值，不得表述为自动化的录用/退稿决定。计分以聚簇为单位（权重 critical 25 / major 10 / minor 3 / info 0，每 category 上限 30）；8 个 major 簇集中于宏观逻辑、统计与结论域。
- findings：**31**（critical 0 / major 8 / minor 17 / info 6）；复核动作：P1 ×7、P2 ×5。
- 抽取覆盖率计算值：`0.875`；分子分母见第七节。不是稿件质量概率。
- 审核置信度：`review_confidence = 0.875`。未经校准的证据支撑指数，不是 finding 正确概率。

### 优先处理（P1 前三项）

- [ ] **[P1] 核对并要求作者改写全部作者归属句**（编辑）
  - 关联判断：`M2-001` [major] "current study/authors"指代漂移与作者归属失实 —— PubMed 作者列表证伪 Henry/Cameron 在 refs [2][5] 中（定位：fulltext_reconstructed.txt L21）
- [ ] **[P1] 增加宿主免疫语境 caveat**（领域审稿人）
  - 关联判断：`M3-001` [major] 免疫缺陷异种移植 vs 免疫依赖机制的语境错配（定位：L17 机制句 + L25 异种移植句）
- [ ] **[P1] 回 [3]/[2] 原文核验统计结构**（统计审稿人）
  - 关联判断：`M4-002` [major] QIF 关联缺统计细节且发现-验证层级被转述颠倒（bulk 126 发现 → QIF 116 验证，评论只呈现后者并称之为主证据）（定位：L17）

## 二、结构化结果表

结构化结果版本：`v2`；`stage_3b_executed=true`（见 `structured_result_v2.json`）。本节只展示条件必填、未解析/缺失及与 finding 证据相交的字段；其余 reported/not_applicable 字段仅保留在 JSON。

| 字段 | 适用性 / 必填性 | 状态 | 值 / 单位 | 抽取置信度 | 原文定位 |
| --- | --- | --- | --- | --- | --- |
| `declarations.funding` | applicable / required | `reported` | CRUK C355/A25137、C7893/A26233；MRC MR/X018997/1（与 JATS award-group 精确一致） | `high` | L48 致谢 |
| `declarations.conflict_of_interest` | applicable / required | `reported` | "No conflicts of interest were declared."（自引 [8] 经 ICMJE 不构成需披露事项，见 M2-007） | `high` | fn path6420-note-0002 |
| `declarations.data_availability` | applicable / required | `reported` | "no datasets were generated or analysed during the current study" | `high` | L50-51 |
| `conclusion.limitations` | applicable / recommended | `not_reported` | 全文无局限性声明（absence 检索确认） | `high` | 检索：limitation/caveat；结果 no_match（EV-003） |

### 核心数据观测组摘要

本文自身无原始数据（受邀评论）。转述的被评论研究数字（87,693 细胞、126 例 bulk、116 例 QIF、105 例 QIF、3v3 ERS-CAF、"20% fibroblasts" 等）经外部摘要/工具核验的结论并入第四节相应 finding（M4-001/002/003、M2-002）。

## 三、图表解读与原图定位

> 本节记录只读解读，不是 M5 审核判断；图表问题见第四节。

- **Figure 1**（path6420-fig-0001，BioRender 机制示意图）：**无图像文件**，仅图注可审（SYS-1，figure_integrity_audit images_scanned=0）。图注主张：ERS 与能量代谢 CAF 贴邻肿瘤细胞、iCAF 不贴邻（[2,3]）；ERS-CAF 几乎仅见复发脊索瘤；BioRender 许可链接 https://BioRender.com/a94t585。图内元素核验被材料限制阻断。
- **Table 1**（path6420-tbl-0001）：4 行 × 5 列（CAF subtypes / Selected markers / Biological functions / Samples / References），汇编 [3][1][10][2] 四项脊索瘤单细胞研究的 CAF 亚型。完整可读；计数对账零不一致（table_total ×5）；呈现与内容问题见 M2-003、M5-002~M5-005、M3-003、M4-003。
- 无补充材料（pmc-prop-has-supplement=no）。

## 四、审核发现

> 共 31 条（8 major / 17 minor / 6 info，0 critical），按聚簇组织；证据以 `[EV-xxx｜定位]` 简写，完整条目在 `review_report.json` 的 evidence_registry。

### [major] CL-01 · M2-001 "current study/authors"指代漂移与作者归属失实

- 类别：macro_logic；证据包：`[EV-101｜L21 'lead author of the current study'…]` `[EV-102｜L21 'the current authors previously reported [5]'…]` `[EV-103｜L12 'this and other groups'…]` `[EV-201｜PubMed ref[2] 作者列表：Zhang TL, Xia C, Zheng BW…无 Henry/Cameron]` `[EV-202｜PubMed ref[5] 15 人作者列表无 Henry/Cameron]`
- `M2-001` [major｜M2｜confidence high｜复核：编辑 P1｜rule 02-macro-logic#attribution-consistency]
  全文以 the current study/authors 指称被评论论文[3]，字面主语却是评论作者，构成系统性指代漂移（L12/L17/L21/L25）。两处归属被 PubMed 完整作者列表证伪：(1) "the lead author of the current study helped define... ERS-CAF [2]" —— [2] 第一作者为 Zhang TL，评论第一作者 Henry 不在 [2] 作者列表，即便按意图读法（指 [3] 第一作者 Zheng BW），Zheng BW 在 [2] 中仅第三作者，两种读法均不成立；(2) "the current authors previously reported tumour-stroma ratio [5]" —— [5] 作者列表无 Henry/Cameron，自然读法构成误导性归属披露。摘要 "by this and other groups" 先行词不明。ref[2] 另有更正记录（PMID40719554）未抓取（SYS-8）。
  处置：涉 [3] 处显式写 "Zheng and Guo"；ERS-CAF 句改 "Zhang et al. [2]"；tumour-stroma ratio 句改 "Zou et al. [5]"；摘要指明先行词。

### [major] CL-02 · M2-002 "same tumour cohorts"表述过宽、证据基础非独立

- 类别：macro_logic；证据包：`[EV-104｜L21]` `[EV-105｜Table 1 队列列]` `[EV-203｜ref[2] 摘要：3+3+3、QIF 105 additional]` `[EV-204｜ref[3] 摘要：7+4、bulk 126、QIF 116 additional]`
- `M2-002` [major｜M2｜high｜编辑 P1｜rule 02-macro-logic#independence-of-evidence]
  L21 断言 [2] 与 [3] "used the same tumour cohorts as the current study"；外部对比两队列构成不同（[2]: 3 primary+3 recurrent+3 NP、QIF n=105；[3]: 7 primary sacral+4 NP、bulk n=126、QIF n=116），bulk 126 对 126 仅提示部分复用可能，scRNA-seq 与 QIF 数目均不吻合；重叠度未量化。评论未推导该前提的后果：ERS-CAF 与 iCAF 两套预后主张证据基础非独立，对因果归因与整合共识主张（M7-001）的影响未讨论。
  处置：作者说明队列实际复用范围，改精确表述并补非独立性含义。

### [major] CL-03 · M3-001 免疫缺陷异种移植 vs 免疫依赖机制的语境错配

- 类别：experimental_methods；证据包：`[EV-106｜L17 'predominated by reciprocal paracrine interactions with immune cells']` `[EV-107｜L25 'subcutaneous xenograft model; normal fibroblasts...']` `[EV-204｜ref[3] 摘要：in vivo/in vitro 确认]` `[EV-205｜Krishnamurty OA 全文：KPR 免疫健全同源模型]`
- `M3-001` [major｜M3｜high｜领域审稿人 P1｜rule 03-experimental-methods#model-context-matching]
  iCAF 核心机制主张是免疫依赖的（L17），但 [3] 的体内证据为人肿瘤皮下异种移植（L25），宿主必然免疫缺陷，原理上无法检验免疫介导旁分泌机制；评论将其与免疫健全 PDAC 模型（[7] 自发胰腺癌、[9] KPR+CD8 依赖验证，均经外部原文坐实）并置而未提示宿主免疫状态差异；同句 in vivo/in vitro 混排；该遗漏同时动摇 sec-0002 因果讨论与 sec-0003 L29 免疫治疗含义。评论的 caveat 只覆盖遗传模型转化，未点破宿主免疫失能这一最致命边界。
  处置：增加显式 caveat；分开表述 in vitro 与 in vivo 证据；免疫治疗含义处标注限制；回 [3] 原文确认宿主机型。

### [major] CL-04 · M2-003 引文括注 [1,2,10,11] 与 Table 1 行 [3,1,10,2] 直接矛盾

- 类别：macro_logic；证据包：`[EV-108｜L29]` `[EV-109｜Table 1 References 列]` `[EV-210｜ref[11] 确为 scRNA-seq 免疫聚焦研究]`
- `M2-003` [major｜M2｜high｜编辑 P1｜rule 02-macro-logic#citation-figure-table-agreement]
  [3] 在表内却缺席正文括注，[11] 在括注却不在表内；计数（四项）、引文括注、表行三者无法同时对平（[11] 归入 "alongside immune-cell focussed studies" 从句文体上可通，但矛盾仍在）。"至少四项"的外部完备性未做穷举检索（unresolved）。作者意图最可能是将 [3] 误写为 [11]。
  处置：决定集合并统一括注与表行。

### [major] CL-05 · M4-001 "almost exclusively in recurrent chordomas" 三处无限定复用且统计基础薄弱

- 类别：statistics；证据包：`[EV-110｜L23/L29/L45 三处]` `[EV-302｜scipy 复核：Fisher 3v3 双侧 p=0.10；CP 3/3 95%CI [0.2924,1.0000]]` `[EV-203｜ref[2] 摘要]`
- `M4-001` [major｜M4｜high｜统计审稿人 P1｜rule 04-statistics#small-sample-generalization]
  依据仅为 [2] 的 3 primary vs 3 recurrent：患者层级最极端分裂 Fisher p=0.10，达不到 p<0.05；3/3 的 95%CI [0.2924,1.0]。分析单位未知：细胞层级=伪重复，患者层级 n=3+3 不足（[2] 全文不可得，SYS-6）。[2] 复发样本治疗史未标注，而 L23 正以该分裂推导 "prior therapy 驱动 ERS 表型" 因果假说，关键混杂缺失。
  处置：回 [2] 原文核验分析单位与检验方法；三处表述改为 "在一个 n=3+3 的研究中富集于复发样本（未校正）"。

### [major] CL-06 · M4-002 QIF 关联缺统计细节且发现-验证证据层级被转述颠倒

- 类别：statistics；证据包：`[EV-111｜L17 全句]` `[EV-204｜ref[3] 摘要：bulk 126 发现 → QIF 116 验证]`
- `M4-002` [major｜M4｜high｜统计审稿人 P1｜rule 04-statistics#analysis-reporting-fidelity]
  L17 将 QIF n=116 关联作主证据呈现，但缺截断值确定方式、单/多因素结构、多重比较校正、效应量与 CI、评分盲法；[3] 实际结构为 bulk n=126 发现集 → QIF n=116 追加验证集，评论将方向颠倒且从未提及 126；bulk 签名验证局限（组成、推导队列、对免疫细胞的特异性——iCAF 标志物 IL1B/HLA-DRA 等与免疫细胞表达重叠，bulk 评分受细胞组成混杂）未提示。细目因 SYS-4 不可核验，但转述缺陷成立，且评述主题恰为相关 vs 因果。
  处置：回原文核验统计细目；恢复发现-验证方向并补 n=126；bulk 签名验证加局限说明。

### [major] CL-07 · M2-004 pseudotime 被表述为谱系事实，NP 对照局限未讨论

- 类别：macro_logic；证据包：`[EV-112｜L23 'differentiate... progressively evolve... eventually emerge']` `[EV-113｜L29 'are shown to appear late']` `[EV-204｜ref[3] 摘要用 'suggested']`
- `M2-004` [major｜M2｜high｜领域审稿人 P1｜rule 02-macro-logic#evidence-strength-matching]
  计算推断被写成谱系事实，轨迹出处未注明（[2] 还是 [3]？）；nucleus pulposus 为脊索来源组织而非真正正常对照，仅 3–4 例（Table 1），匹配未讨论；"little overlap" 观察与连续性轨迹结论有张力；L29 "are shown to appear late" 同样实体化。该链条是 "drivers vs passengers" 论证的主要支柱。
  处置：改为 "pseudotime analysis in [2,3] suggests..."；补 NP 对照 caveat；"are shown" → "are inferred"。

### [major] CL-08 · M7-001 整合共识处方性主张未处理可比性前提，全文无局限性声明

- 类别：conclusions_discussion；证据包：`[EV-114｜L29/L38]` `[EV-115｜L38 'No doubt...']` `[EV-116｜L33 vs L35 iCAF 标志物几乎无重叠]` `[EV-003｜absence：全文无局限性声明]`
- `M7-001` [major｜M7｜high｜领域审稿人 P1｜rule 07-conclusions-discussion#scope-premises]
  中心处方性主张（整合各研究达成共识、跨肿瘤比较、整合框架）未处理任何可比性前提，而反证在稿件内可见并获外部补强：①同队列非独立（M2-002）；②跨研究作者网络交叠（[2][3][5][11] 共享 Zheng BW/Zheng BY/Zou MX 等）；③iCAF 标志物集跨研究无重叠而无映射（M5-003）；④解剖部位混杂未讨论（[3] 全骶骨、[1] 全颅底、[10] 混合、[2] 未注明）；⑤四队列极小且半数无对照未讨论统计局限（M4-001/003）；⑥CAF 可塑性（myCAF↔iCAF 互转，综述 [4] 覆盖）未讨论，直接消解 drivers/passengers 二元框架；⑦"No doubt... would share significant overlap" 无证据直陈转化期望；全文无局限性声明。
  处置：增加可比性前提与局限性段落；"No doubt" 改条件式。

### [minor] CL-09 · M7-002 sec-0003 标题承诺与内容分布错位

- `M7-002` [minor｜M7｜high｜作者 P2｜rule 07-conclusions-discussion#claim-content-alignment]
  题为 "Can targeting the stroma in chordoma provide clinical benefit?" 但全节无靶向策略/临床试验证据；设问未答、自问未答；sec-0002 末尾的 PDAC 警示（[7] 消融反促侵袭、"separate correlation from causation"）未回接至展望。实质间质靶向证据全部位于 sec-0002。（证据：EV-108、EV-132）

### [minor] CL-10 · M3-002 LRCC15 应为 LRRC15（基因符号拼写错误）

- `M3-002` [minor｜M3｜high｜作者 P2｜derived_from SIG-902｜rule 03-experimental-methods#reagent-identifier-accuracy]
  HGNC 核验 LRCC15 既非批准符号也非旧符号，LRRC15 为现行批准符号；refs[6][9] 标题均作 LRRC15，内外部双重确认。错误位于因果论证关键例证的靶点符号上，确定性更正。（证据：EV-117、EV-118、EV-207）

### [minor] CL-11 · M2-005 "powerful longitudinal studies [6]" 研究类型失准

- `M2-005` [minor｜M2｜high｜编辑 P2｜rule 02-macro-logic#citation-characterization]
  Dominguez 2020 [6] 设计为动物模型跨阶段基质演化图谱 + 横断面人源证据（22 例 scRNA-seq、70 例 IHC）+ >600 例试验数据回顾，并非患者纵向随访研究；"powerful" 为主观加码。（证据：EV-119、EV-206）

### [info] CL-12 · M5-001 材料限制与转换伪影汇总（非稿件缺陷）

- `M5-001` [info｜M5｜high｜编辑 P2｜derived_from SIG-601]
  SYS-1 Figure 1 无图像；SYS-2 fulltext.txt 有损转换（缺 Abstract/引言两段/图注/致谢/基金/引用编号，Table 1 双份输出）；SYS-3 重建伪影（"Figure Figure 1" 为脚本前缀重复，JATS 源无重复词；表头行丢失）；SYS-4 [3] 非 OA；SYS-5 Duan 全文被出版商封锁；SYS-6 refs[1][2][10][11] 全文不在材料；SYS-7 BioRender 许可等级不可核；SYS-8 ref[2] 更正未抓取。（证据：EV-121、EV-303）

### [minor] CL-13 · M5-002 Table 1 题注 "scRNA-seq studies" 低估 [2][3] 证据模态

- `M5-002` [minor｜M5｜high｜作者 P2]
  [2] 标题明含 "Integrating single-cell and spatial transcriptomics"，[3] 为 multi-omics（含 ST+QIF，外部摘要证实），表内 function 列本身承载空间定位结论。题注改 "single-cell and/or spatial transcriptomic studies"。（证据：EV-122、EV-137、EV-204）

### [minor] CL-14 · M5-003 CAF 亚型同名异质/异名同质，缺跨研究映射列

- `M5-003` [minor｜M5｜high｜作者 P2]
  iCAF 跨研究同名异质（[3] IL1B/HLA-DRA/MMP9/CCL4 vs [10] IL1RL1/CCL3/CCL4l2/CCL8 几乎无重叠），myCAF/mCAF 异名同质；正文呼吁 consensus 但表无映射列。（证据：EV-116）

### [minor] CL-15 · M5-004 "EMT/TGFβ pathway targeted" 指代悬空

- `M5-004` [minor｜M5｜high｜作者 P2]
  Zhang 2022 行 targeted 无施事与对象，单元格不可自足；结合 [1] 标题疑指 p-EMT 靶向试验，改写为 "findings informed a p-EMT-targeted clinical trial [1]"。（证据：EV-123）

### [minor] CL-16 · M3-003 CCL4l2/Col1a2 小鼠式写法出现在人队列研究行

- `M3-003` [minor｜M3｜medium｜作者 P2→人工对照 doi:10.1007/s00262-022-03152-1]
  HGNC 大小写不敏感解析到 CCL4L2/COL1A2（人源批准符号），故非确定性误植，但在人研究行构成命名规范/物种歧义，且与同行人类全大写风格混杂；Duan 原文被出版商封锁（SYS-5），写法出处 unresolved。（证据：EV-124、EV-208）

### [minor] CL-17 · M4-003 Table 1 缺细胞数/QC；"20%" 无分母；rare clusters 未命名

- `M4-003` [minor｜M4｜high｜作者 P2]
  各行未列捕获细胞数/QC；"20% of cells are fibroblasts" 无分母（[10] 全文封锁，unresolved）；Zhang 2024 行 3+3 样本列 "2 rare CAF clusters" 未命名。簇数对账工具核验零不一致，属信息完整性问题。（证据：EV-125、EV-301、EV-302）

### [info] CL-18 · M5-005 Table 1 书写规范不一致/行序/呈现清晰度

- `M5-005` [info｜M5｜high｜编辑 P2]
  大小写/分隔符/断段/斜体不一致；行序 [3]→[1]→[10]→[2] 非引用序/时间序；无计数错误（table_total ×5 零信号）。（证据：EV-109、EV-301）

### [minor] CL-19 · M5-006 图注 "energy metabolism CAF 贴邻肿瘤细胞" 缺稿件内支撑

- `M5-006` [minor｜M5｜medium｜领域审稿人 P2]
  ERS 贴邻有表行/正文支撑，但 energy metabolism CAF 的空间定位在正文与 Table 1 均无描述；外部摘要仅证实 iCAF 远离部分，贴邻出处 unresolved（SYS-6）；[2,3] 单括号混合多来源子主张。（证据：EV-126、EV-204）

### [minor] CL-20 · M5-007 空间定位与因果表述的强度漂移

- `M5-007` [minor｜M5｜high｜作者 P2]
  "largely distal"（L17）→ "Localised distant"（L33）→ "not found in close proximity"（L45）三级渐强；评论摘要 "play a causative role in driving an invasive poor prognosis tumour phenotype" 较 [3] 摘要 "accelerate the malignant progression" 明显更强（外部确认强度差）。（证据：EV-127、EV-120、EV-204、EV-103）

### [minor] CL-21 · M3-004 功能实验模型与对照局限未提示

- `M3-004` [minor｜M3｜high｜领域审稿人 P2]
  皮下部位非骨性微环境；normal fibroblast 对照来源/部位匹配未说明；无 myCAF/ERS-CAF 平行对照，促瘤效应无法特异归因于 iCAF；评论层面亦无 iCAF 制备可重复性信息（细节回 [3] 原文，SYS-4）。（证据：EV-107、EV-204）

### [minor] CL-22 · M2-006 CAF 亚型丰度共线性断言无引文

- `M2-006` [minor｜M2｜high｜作者 P2]
  L21 "myofibroblast CAF-rich tumours tend to also be rich in iCAFs and immune cells" 为承重前提但句内无引文。（证据：EV-129）

### [info] CL-23 · M7-003 背景/临床主张缺引文

- `M7-003` [info｜M7｜high｜作者 P2]
  L15 "high levels of TGFβ pathway activation" 无引文（且为 L29 共识主张承重前提）；L29 "immunotherapy is emerging as a promising option" 无引文（脊索瘤 ICI 证据基线待外部检索，unresolved）。（证据：EV-130）

### [info] CL-24 · M2-007 PDAC "consensus" 支撑单薄且含自引

- `M2-007` [info｜M2｜high｜编辑 P2]
  "consensus... [4],[8]" 仅综述+单研究支撑；[8] 含评论第一作者 Henry JC（自引，按 ICMJE 不构成需披露事项，与 COI 声明无矛盾，仅引用平衡提示）。"consensus" 弱化为 "reported by"。（证据：EV-131）

### [minor] CL-25 · M2-008 Dominguez/Krishnamurty 概括与 [6]/[9] 归属边界

- `M2-008` [minor｜M2｜medium｜编辑 P2]
  括注归属位置总体正确（KPR 基因型串与 [9] 逐字一致、靶向为 Lrrc15-DTR 遗传消融），但两项研究被并入单一叙事，归属边界模糊；建议拆句显式署名。（证据：EV-132、EV-205）

### [minor] CL-26 · M7-004 语法/措辞问题集

- `M7-004` [minor｜M7｜high｜编辑 P2]
  "Evidence for iCAFs populations... have been described"；"predominated by"；"both clinicopathological features, including..."（both...including 矛盾，且不良预后非 clinicopathological feature）；"beg the question" 误用；L25 长句 in vivo/in vitro 混排。（证据：EV-133）

### [minor] CL-27 · M4-004 队列性别/年龄信息缺失（2:1 男性偏倚混杂）

- `M4-004` [minor｜M4｜medium｜作者 P2]
  Table 1 与 116 例 QIF 队列均未转述性别/年龄；脊索瘤约 2:1 男性偏倚是跨研究比较潜在混杂。（证据：EV-105、EV-203）

### [info] CL-28 · M6-001 伦理合规无问题项汇总（受邀评论适用性裁定）

- `M6-001` [info｜M6｜high｜编辑 P2]
  ETH-HUM/ETH-ANI/ETH-CELL 全部 not_applicable（二次文献反向豁免）。已核验：COI 脚注存在；基金与 JATS award-group 精确一致；受邀评论脚注、ORCID、CC-BY、BioRender 署名、数据可用性声明完整；ethics_compliance_check 唯一信号 SIG-601（ETH-HGR-001 适用性不可推出）经 M6 裁定 not_applicable（评论无任何样本/数据行为；被引中方队列研究 HGR/伦理责任在原文）；animal_model_compliance 零信号；cell_line 穷举检索零具名细胞系（not_applicable）；rrid/accession/注册号未检出；X1 核验 12 条 DOI 全解析、11 条引文无撤稿。例外见 M2-001/M2-002。Zheng BY 与 Zheng BW 为两位真实作者（refs[2][11]），参考文献著录无误，仅同号辨识提示。（证据：EV-001/002/004/005、EV-304/305/306、EV-209/210）

### [minor] CL-29 · M2-009 "All studies concur" 与 Table 1 摘要不匹配

- `M2-009` [minor｜M2｜medium｜作者 P2]
  Table 1 仅 [1][10] 行涉 TGFβ、无行提 TBXT；"All studies" 量化域歧义；逐篇核验被 SYS-6 阻断。（证据：EV-136、EV-210）

### [minor] CL-30 · M7-005 "10-year outcome data" 为评论独有细节，外部摘要无对应

- `M7-005` [minor｜M7｜medium｜作者 P2]
  全文仅此一见（L17），[3] Europe PMC 摘要未提 10 年随访；SYS-4 阻断全文核验，unresolved。请作者注明出处或删除。（证据：EV-138、EV-204）

### [info] CL-31 · M6-002 作者贡献声称与产出缺陷的责任归属

- `M6-002` [info｜M6｜high｜编辑 P2]
  作者贡献声明（L42）明示 "compiled the table, and designed the figure"；本次确认的系统性缺陷恰集中于这两件产物，责任归属明确，修改指令可直接定向作者；贡献声明本身无事实矛盾。（证据：EV-134）

## 五、抽取信号

> 机器观察与路由轨迹，不是稿件问题，无 severity。共 2 条。

- `SIG-601` · `partial_extraction`：ETH-HGR-001（中国人类遗传资源审批/备案）适用性事实无法从结构化结果推出，未评估。目标：ethics.ETH-HGR-001；路由：M6；产出：ethics_compliance_check.py。**处置：M6 裁定 not_applicable** —— 受邀评论无任何样本采集/数据生成行为，不触发 HGR 义务；被引中方队列研究的责任在被引原文（SYS-6）。
- `SIG-902` · `external_validation_candidate`：基因符号 LRCC15 既非 HGNC 批准符号也非旧符号（gene_symbol_unrecognized）。目标：L25 "LRCC15+ CAFs"；路由：M2/M3；产出：external_figure_validation.py（HGNC）。**处置：并入 M3-002**，内部（refs[6][9] 标题）+外部双重确认为拼写错误。

## 六、系统限制

> 本节说明系统或输入"哪些地方没看清"。这些条目不是稿件问题，不得据此推断作者遗漏或违规。共 8 条；有受影响目标时，相关"未发现问题"表述一律无效。

- `SYS-1` · figure_unreadable：Figure 1 无图像文件（JATS 指向 PATH-266-5-g001.jpg 未提供；figure_integrity_audit images_scanned=0），图内元素不可核验，仅图注可审。受影响：M5；恢复动作：提供图像后补审。
- `SYS-2` · conversion_artifact：用户提供的 fulltext.txt 为有损转换（缺 Abstract、引言两段、图注、致谢/基金、ORCID/COI 脚注；引用编号全丢失；Table 1 双份输出）。据此版做合规筛查会将 COI/基金/BioRender 署名误判为 not_reported。恢复动作：以 fulltext_reconstructed.txt / fulltext.xml 为准。
- `SYS-3` · conversion_artifact：本次重建脚本伪影 —— "Figure Figure 1"/"Table Table 1"（JATS 源无重复词，xref 文本仅 "1"）、Table 1 表头行丢失。已修正解释（G-28 据此驳回），不得当稿件缺陷。
- `SYS-4` · external_source_unavailable：被评论论文 [3]（doi:10.1002/path.6369）非 OA、无 PMC 全文，仅摘要可得 —— QIF 统计细目、异种移植宿主机型、10-year outcome 出处、bulk 签名组成不可核验。受影响：M3-001、M4-002、M7-005。
- `SYS-5` · external_source_blocked：Duan 2022（doi:10.1007/s00262-022-03152-1）全文 XML 被出版商明确禁止下载 —— CCL4l2/Col1a2 原始写法、"20%" 分母不可核验。受影响：M3-003、M4-003。
- `SYS-6` · external_source_unavailable：refs [1][2][10][11] 全文不在材料（[2][6][11] 摘要已抓取）——"All studies concur" 逐篇匹配、energy metabolism CAF 空间证据出处、[2] 分析单位不可核验。受影响：M2-009、M4-001、M5-006。
- `SYS-7` · external_source_unavailable：BioRender 账户许可等级离线不可核验。恢复动作：作者提供许可凭证。
- `SYS-8` · external_source_unavailable：ref [2] 存在更正（PMID 40719554, Neuro Oncol 2026;28(5):e17），内容未抓取；当前 PubMed 作者列表已反映更正后元数据（仍无 Henry/Cameron），不影响 M2-001 判定。

## 七、覆盖率明细

| 子率 | 分子 / 分母（rate） |
| --- | ---: |
| 条件必填字段解析率 | 3 / 3（1.000） |
| 图表可读率 | 1 / 2（0.500）—— Table 1 可读；Figure 1 无图像 |
| 补充材料可得率 | 0 / 0（不适用，哨兵 1.0）—— 本文无补充材料 |

- 加权：extraction_coverage = 0.60×1.000 + 0.25×0.500 + 0.15×1.000 = **0.875**
- 已解析的条件必填字段：declarations.funding、declarations.conflict_of_interest、declarations.data_availability（均 reported）
- 不可读图表：Figure 1（caption-only）；不可得补充材料：无
- 推荐字段覆盖率（不进加权）：2 / 3（research_question、generalization_scope reported；limitations not_reported）
- review_confidence = 0.875 × Q(0.997) × C(1.0) ≈ **0.875**（无 pixel/OCR 依赖；低置信 finding 占比 1/31）

> `not_reported` 表示已完成规定范围检索并确认稿件未报告，属于"已解析"；`parse_failed` 表示系统没读出来。分母为 0 时 rate=1.0 只是计算哨兵，不得解释为 100% 完成。

## 八、人工复核建议

优先级固定解释：P0=全部 critical 及阻断核心解释的 major（本次无）；P1=其他 major，会改变 finding 成立/严重度或作者必须补材料；P2=minor/info 的澄清与编辑性修正。

| 优先级 | 动作 | 执行者 | 关联 finding |
| --- | --- | --- | --- |
| P1 | 核对并要求作者改写全部作者归属句；若主张另有共同发表关系须举证 | 编辑 | M2-001 |
| P1 | 要求增加宿主免疫语境 caveat（异种移植=免疫缺陷，不能验证免疫介导机制）；分开表述 in vitro/in vivo；回 [3] 确认宿主机型 | 领域审稿人 | M3-001 |
| P1 | 回 [3] 原文核验 QIF 截断值/单多因素/多重比较/效应量与 126→116 发现-验证结构；回 [2] 核验 ERS-CAF 分析单位（患者 vs 细胞）与检验方法 | 统计审稿人 | M4-002, M4-001, M7-005 |
| P1 | 要求作者澄清 [2]/[3] 队列复用范围（"same tumour cohorts"），补非独立性含义 | 编辑 | M2-002 |
| P1 | 统一"四项研究"集合：引文括注 [1,2,10,11] 与 Table 1 行 [3,1,10,2] 取一并说明 | 编辑 | M2-003, M2-009, M5-002 |
| P1 | 要求增加局限性与可比性段落（重叠、部位、样本量、标志物不一致、可塑性）；"No doubt" 改条件式 | 领域审稿人 | M7-001 |
| P1 | pseudotime 表述改谱系对冲（标明轨迹出处、NP 对照 caveat；"are shown" → "are inferred"） | 领域审稿人 | M2-004 |
| P2 | Table 1 修订包（细胞数/QC/分母、rare clusters、映射列、"targeted" 补主语、CCL4L2/COL1A2、书写规范、行序） | 作者 | M4-003, M5-003, M5-004, M5-005, M3-003, M6-002 |
| P2 | 图注与强度统一包（energy metabolism 贴邻给出处或删除；回归 "largely"；摘要 "causative role" 对齐；LRCC15→LRRC15；"longitudinal studies [6]" 改写） | 作者 | M5-006, M5-007, M3-002, M2-005 |
| P2 | 引文与语言包（L21 共线性句、L15 TGFβ、L29 免疫治疗补引文；"consensus" 弱化；Dominguez/Krishnamurty 拆句；语法润色；"10-year outcome" 注明出处） | 作者 | M2-006, M7-003, M2-007, M2-008, M7-004, M7-005 |
| P2 | sec-0003 标题/内容对齐（回接 PDAC 警示或改标题）；功能实验模型局限表述 | 作者 | M7-002, M3-004 |
| P2 | 材料恢复后再审：Figure 1 图像（SYS-1）、[3] 全文（SYS-4）、Duan 原文（SYS-5）、ref[2] 更正（SYS-8）；合规汇总留档 | 编辑 | M5-001, M6-001 |

## 九、加法保证与运行时遥测

### 加法保证（§6.2 自检）

- L0 全局审阅产出 **39 条 G 条目**；最终每一条均有明确终态：**34 条晋升/并入** 31 条聚簇 finding（含 2 条 L4 跨节新发现 X-01/X-02），**3 条带理由驳回**（G-22：KPR 基因型串与 Krishnamurty Nature 2022 OA 全文逐字一致；G-28：JATS 源无重复词，为重建伪影；G-29：Zheng BY 为真实独立作者，refs[2][11] 均同时列出 Zheng BY 与 Zheng BW），**2 条归入系统限制**（G-20→SYS-1 无图像；G-37→SYS-2 有损转换）。**0 条不明不白消失。**
- `additive_guarantee_held = true`。最终 finding 数（31）少于 G 条目数（39）的差额全部可解释：28 条 G 合并入聚簇、6 条单独晋升、3 条驳回（附反驳依据）、2 条材料限制 —— 见 `review_report.json` 的 `global_audit[]` 与 `candidate_resolution_log[]`。
- severity 被下调或证伪的条目均记录理由：G-16（HGNC 大小写不敏感解析，"物种误植"→"命名规范歧义"，confidence high→medium）；G-22/G-28/G-29（外部证据证伪）；S7-06（外部核验证明转述与原文同档，minor→info 级子项）。

### 运行时遥测（§7.1）

```json
{
  "child_sessions": 9, "task_calls": 15, "continuations": 6,
  "modules_run": ["M2","M3","M4","M5","M6","M7"], "modules_skipped": {},
  "references_required": ["02-macro-logic","03-experimental-methods","04-statistics","05-figures-and-charts","06-ethics-compliance","06b-animal-model-ethics-enhancement","07-conclusions-discussion"],
  "references_read": ["02-macro-logic","03-experimental-methods","04-statistics","05-figures-and-charts","06-ethics-compliance","06b-animal-model-ethics-enhancement","07-conclusions-discussion"],
  "routing_recall": 1.0, "tool_execution_recall": 1.0,
  "global_findings_count": 39, "global_findings_confirmed": 36,
  "global_findings_refuted": 3, "global_findings_unresolved": 0,
  "additive_guarantee_held": true,
  "findings_added_beyond_global": 26,
  "finding_origin_breakdown": {"global_review":4,"specialist_rule":14,"external_validation":5,"deterministic_tool":3,"cross_section_reconciliation":2,"multiple":3}
}
```

- 分层真实发生：L0、L0b 并行发起；M2–M6 五路并行；M7 串行消费；L2 工具主会话并发；L3 六个续接复议同批发出；L4 校正、L5 渲染。
- 增益结构：仅来自 global_review 的 finding 4 条；specialist_rule / external_validation / deterministic_tool / cross_section_reconciliation 独有或主导 27 条（占 87%）。增益最大的来源：外部文献核验（PubMed/Europe PMC/HGNC/Crossref，坐实归属证伪、队列构成矛盾、证据层级倒置、LRCC15 无效符号、KPR 基因型一致）与统计重算（3v3 Fisher/CI）。
- 确定性工具台账：executed —— gene_symbol×25（1 信号）、reference_exists×12（0 信号）、cited_retracted×11（0 信号）、table_total×5（0 信号）、Fisher/CP 复核、ethics_compliance_check（SIG-601）、animal_model_compliance（0 信号）、figure_integrity_audit（images_scanned=0）；not_applicable（带理由）—— cell_line（全文零具名细胞系，检索词清单登记为 absence 证据）、rrid/accession/trial_registration/compound、count_percentage（"20%" 无分母）、grim、test_statistic_p、ci_estimate、normalize_biomed_units、sequence_identifier_audit。

## 十、边界声明

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。** 本 Skill 的任何评分均为筛查信号，不构成录用、退稿或发表决定。

---
*报告由 biomed-paper-review skill 生成（full_review 模式）；机器可读版见 `review_report.json`（含完整 evidence_registry、candidate_resolution_log、global_audit、tool_execution_ledger）。辅助材料：`fulltext_reconstructed.txt`（规范全文重建）、`structured_result_v2.json`、工具输出 `x1_gene_symbols.json` / `x1_dois.json` / `forensic_table.json` / `ethics_check.json` / `animal_check.json` / `figure_audit.json`、外部全文 `krishnamurty_full.xml`。*
