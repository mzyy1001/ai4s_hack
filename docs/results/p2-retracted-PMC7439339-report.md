# 审稿辅助报告（full_review）

> **撤稿警示：本文已被撤稿。** RETRACTION: J Clin Lab Anal. 2026 Feb;40(3):e70169；DOI 10.1002/jcla.70169（PMC12888758 / PMID 41578707）。本报告中的外部证据均标注「通知陈述，非本审观察」。

## 论文信息

- **标题**：A long non-coding RNA OLBC15 promotes triple-negative breast cancer progression via enhancing ZNF326 degradation
- **作者**：Deng Chao; Zhang Bojuan; Zhang Yao; Xu Xiaogang; Xiong Deming; Chen Xiaoyan; Wu Jiaojiao
- **期刊**：Journal of Clinical Laboratory Analysis 2020;34(8):e23304
- **标识**：DOI 10.1002/jcla.23304 · PMID 32329931 · PMCID PMC7439339
- **研究类型**：分子生物学 + 细胞系（体外）+ 动物移植瘤/转移模型 + 人组织样本（观察性）
- **撤稿状态**：**RETRACTED** —— 作者+主编+出版社协议撤稿：关键结果无法重复；技术错误（pulldown条件不一致、细胞潜在交叉污染、ZNF326抗体验证不足）；原始数据差异（WB Fig4B/5A/5B、迁移定量、IHC评分一致性）；图像重复（Fig4D←Koo 2017、Fig5B←Shen 2019、Fig5E←Li 2018）

## 边界声明

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。本 Skill 的任何评分均为筛查信号，不构成录用、退稿或发表决定。

## 执行总览

- 模式：`full_review`（L0 全局审阅 + L0b 测绘 + M2–M7 六专家 + L2 确定性/外部核验 + L3 续接复议 + L4 校正 + L5 渲染）
- 子会话：9 个；task 调用 15 次（含 6 次续接）；L0∥L0b、M2∥M3∥M4∥M5∥M6、六续接均真实并行发起
- 规则库：02-macro-logic / 03-experimental-methods / 04-statistics / 05-figures-and-charts / 06-ethics-compliance / 06b-animal-model-ethics-enhancement / 07-conclusions-discussion —— routing_recall = 1.0
- 材料限制：无图像文件；补充材料 `JCLA-34-e23304-s001.docx` 未提供；正文 Table 内容缺失（登记为 SYS-001/002/003，不归责为「稿件没写」之外，相应条目挂 blocked）
- **风险分数：9.8 / 10**（筛查信号）——理由：本文已被撤稿（外部确证）；critical级finding 12条（撤稿与数据完整性1、方法缺失2、统计报告1、机制链4、抗体1、方法学+数据完整性1、主张层2）；风险分数仅作筛查信号
- 审核置信度：**high** —— 全文+XML双源审阅、六模块规则库全覆盖（routing_recall=1.0）、X1外部核验执行且关键结论（撤稿）有出版方通知全文支撑；主要不确定性：无图像文件（像素级结论依赖期刊调查）、补充材料不可得（Table S1-S4/Figure S1-S2不可核）

## 最终发现统计

| 严重度 | 条数 |
| --- | --- |
| critical | 12 |
| major | 31 |
| minor | 14 |
| info | 3 |
| **合计** | **60** |

来源分布：`multiple`(多来源合流) 31 · `specialist_rule` 23 · `external_validation` 3 · `cross_section_reconciliation` 3 · `global_review` 独有 0（裸模型 48 条全部被保留并经规则/外部证据增强；裸模型之外新增 13 条）

## Critical 级发现（12 条）

### F-01 · 论文已被撤稿：不可重复、技术错误、原始数据差异、跨论文图像重复


本文已被撤稿（Retraction: J Clin Lab Anal 2026;40(3):e70169, DOI 10.1002/jcla.70169, PMC12888758）：(1)关键实验结果无法重复；(2)技术错误——RNA pulldown条件不一致、细胞实验潜在交叉污染、ZNF326抗体特异性验证不足；(3)原始数据差异——WB Fig 4B/5A/5B、迁移定量、临床IHC评分一致性；(4)图像重复认定——Fig 4D←Koo 2017 MCT(10.1158/1535-7163.MCT-17-0077)、Fig 5B←Shen 2019 JCLA(10.1002/jcla.23122)、Fig 5E←Li 2018 CMAR(10.2147/CMAR.S183355)。受损面板分别支撑互作、降解、rescue主线。撤稿理由不含伦理指控（不构成G-01/G-02升critical依据，但伦理追溯核验责任由作者转移至机构）。自有像素审计因无图像文件blocked（SYS-001）。

定位：Retraction notice PMID 41578707；fulltext.xml is-retracted=yes；Fig 4B/4D；Fig 5A/5B/5E；Fig 6A｜合并自：M3-034, M5-015, M7-015, M6-010｜G 条目：G-47

### F-02 · Methods实质缺失：≥10项已报告技术零方法学描述，体内臂不可重建


Methods仅5小节（细胞系/载体/试剂、人样本、迁移、CCK-8、统计）。Abstract承诺、Results报告的lncRNA profiling、qPCR、亚细胞分级、异种移植/肺转移动物模型（物种/品系/性别/周龄、每组n、接种数与途径、转移模型类型、体积公式、计数方法、随机化/设盲全缺）、pulldown、质谱、RIP、FISH、截短突变、WB、MG132、泛素化、ChIP样启动子占据、IHC、相关分析均无方法学描述；主张链最先断于体内环节。

定位：Methods sec0007-0011；Abstract；Results sec0013-0018；Fig 3｜合并自：M2-001, M3-001, M3-002｜G 条目：G-02, G-03

### F-06 · lncRNA profiling高维筛选无任何校正/阈值/平台/注册信息


profiling无平台、无配对n、无fold阈值、无FDR/BH多重校正、无工具、无GEO号、无data availability；73上调/126下调列表与候选选择标准不可审计；按规则库高维组学无多重校正→critical。候选名单可靠性与选OLBC15正当性不可评估（XML确证非转换问题）。

定位：Results sec0013；Fig 1A caption｜合并自：M2-006, M3-004, M4-009｜G 条目：G-05

### F-09 · 全文定量报告缺失：n/独立重复/精确P/效应量/CI/误差定义全无


所有实验均未报告n与独立重复次数，图注统计信息仅'**: P<.01'，无精确P/检验量/CI/效应量/误差棒定义/多重校正，单星阈值未定义，生物/技术重复未区分；系统性效应量措辞（profound/dramatically/strongly/markedly）与零效应估计并存。确定性取证因无可复算对象not_applicable，恰证报告缺口本身。

定位：Methods sec0011；Fig 1-6 captions；Results全节｜合并自：M4-002, M3-032, M5-008, M7-014｜G 条目：G-08

### F-16 · Transwell迁移实验方法学缺陷叠加外部数据完整性命中


Transwell缺孔径/血清梯度/定量方式/设盲，上下室同7%血清无趋化梯度，无Matrigel侵袭与EMT标志物；L3上调major→critical：撤稿通知陈述迁移定量原始数据差异且Fig 5E（rescue迁移面板）被认定为Li 2018重复图像（外部归因）。

定位：Methods sec0009；Results sec0014-0017；Fig 2E-F；Fig 5E-F｜合并自：M3-005｜G 条目：G-13

### F-24 · OLBC15-ZNF326互作三支柱同时受损，Discussion却称'directly interacts'


互作证据三支柱同时受损：Fig 4D FISH被撤稿调查认定为Koo 2017重复图像、Fig 4B pulldown WB原始数据差异、通知点名pulldown条件不一致；叠加本就缺失的直接结合验证（无EMSA/RNase敏感性/交联）——FISH共定位+pulldown/RIP均与复合物介导兼容。Discussion总结句'OLBC15 directly interacts with ZNF326...and interferes its post-translational modification'：'directly'超出证据（稿件内层）、互作证据线全灭（外部层）、泛素连接酶自认未知而称'干扰翻译后修饰'。

定位：Results sec0016；Fig 4；Discussion末段｜合并自：M3-012, M7-010｜G 条目：G-21

### F-25 · 'destabilization'无CHX半衰期实验，降解锚点面板受损


标题级'destabilization'无CHX追踪半衰期实验，仅稳态水平+MG132不足以证明稳定性改变；L3上调：Fig 5B（MG132面板，降解主张支柱之一）被认定重复自Shen 2019、Fig 5A有原始数据差异。

定位：Results sec0017；Fig 5A-B｜合并自：M3-014｜G 条目：G-23

### F-28 · rescue链崩溃：仅覆盖迁移、唯一rescue面板被认定重复


rescue仅覆盖迁移，活性与体内均无ZNF326回复臂；KLF17双敲低仅部分回复，提示ZNF326非依赖组分未讨论；L3上调：Fig 5E（唯一rescue面板）被认定重复自Li 2018、迁移定量有原始数据差异——机制链rescue证据全灭。

定位：Results sec0017；Fig 5E-G｜合并自：M3-017, M7-002｜G 条目：G-26

### F-30 · anti-ZNF326抗体横跨四条证据线、有效性被撤稿通知否定


anti-ZNF326抗体横跨pulldown/RIP/WB/IHC四条证据线：撤稿通知明确将'ZNF326抗体特异性验证不足'列为技术错误（作者经通知自认），Fig 4B另有原始数据差异——中心测量试剂失效级问题；叠加无敲除对照条带。全文所有抗体（anti-ZNF326/anti-Flag/anti-ubiquitin）零信息：无厂商/货号/克隆号/稀释比/RRID/批号，外部RRID验证无从入手。

定位：Fig 4B；Fig 5；Fig 6A；Methods｜合并自：M3-023, M3-028｜G 条目：G-32

### F-44 · 治疗性'putative target'结论零干预实验支撑、唯一在体支撑失效


摘要结论'putative target for therapeutic anti-breast cancer intervention'：全文零靶向干预实验，唯一在体支撑（体内臂）因撤稿判定整体失效；L3升major→critical，措辞hedge不豁免支撑全灭。

定位：Abstract-Conclusions；Discussion para3｜合并自：M7-001｜G 条目：G-46

### F-54 · 标题级因果主张'promotes...via enhancing ZNF326 degradation'超出证据


标题级因果主张无CHX、仅敲低方向、rescue不全（稿件内层）；L3：降解锚点Fig 5A差异/Fig 5B重复、互作锚点Fig 4B差异/Fig 4D重复、pulldown条件不一致、抗体验证不足——全部直接支撑失效。

定位：TITLE；Results sec0016-0017｜合并自：M7-009｜G 条目：—

### F-55 · 体内促瘤/促转移直陈主张不可审计、推定失效


体内促瘤/促转移直陈主张：动物方法全缺不可审计；整篇撤稿+'关键结果无法重复'+细胞交叉污染波及MDA-MB-231接种物→推定失效。保留意见：通知未逐字点名Fig 3，其失效由整篇撤稿+不可重复+污染波及接种物推定。

定位：Results sec0015；Fig 3；Abstract-Methods｜合并自：M7-012｜G 条目：—

## Major 级发现（31 条，摘要）

| ID | 发现 | G 条目 | 来源 |
| --- | --- | --- | --- |
| F-03 | 体内臂设计报告缺口：单细胞系、队列结构/n/功效/随机化不明 | G-39 | multiple |
| F-04 | 动物伦理批准/IACUC/ARRIVE/3R声明缺失 | G-01 | multiple |
| F-05 | qPCR MIQE要素缺失，引物表位于不可得补充材料 | G-04 | specialist_rule |
| F-07 | 候选筛选链选择偏倚：73→2 novel→仅以fold选OLBC15 | G-06 | multiple |
| F-08 | 统计声明与实际使用不匹配 | G-07 | multiple |
| F-10 | Fig 2C-D/F四水平（敲低+过表达）混入单因素ANOVA+LSD | G-09 | specialist_rule |
| F-11 | Fig 6B-C相关分析：Pearson误用于等级H-score、无n/正态性、呈现不完整 | G-10 | multiple |
| F-12 | Fig 1C四亚型比较6个成对LSD不控FWER | — | specialist_rule |
| F-13 | 人样本知情同意/批件编号/纳排标准缺失，伦理授权表述被[15]语境失配掏空 | G-11 | multiple |
| F-15 | 临床关联分析（TNM/大小/转移）依据表缺失、检验未描述 | G-12 | specialist_rule |
| F-17 | 细胞系鉴定/支原体声明缺失，撤稿点名潜在交叉污染 | G-14 | multiple |
| F-20 | 慢病毒体系参数缺失、递送方式不自洽 | G-17 | specialist_rule |
| F-21 | shRNA构件使用不一致、靶序列全部未披露 | G-18 | multiple |
| F-22 | pulldown→MS→ZNF326候选收敛不可审计 | G-19 | multiple |
| F-23 | RIP对照不全、阴性对照无理由、pulldown条件不一致（通知） | G-20 | multiple |
| F-27 | 泛素化实验局限：过表达体系、单方向、非变性条件未声明 | G-25 | specialist_rule |
| F-29 | 截短体仅按预测二级结构设计、无结合缺陷突变体回复 | G-22 | specialist_rule |
| F-31 | KLF17终点数据位于不可得补充材料、ChIP样方法缺失、无蛋白验证 | G-27, G-31 | multiple |
| F-34 | 核质分离无方法/标志物对照/定量 | G-30 | multiple |
| F-35 | 无任何生存/预后/诊断效能分析，'clinical relevance'空心 | G-35 | specialist_rule |
| F-36 | Fig 6相关队列构成未定义、混合亚型构成混杂 | G-36 | specialist_rule |
| F-37 | IHC评分细节缺失、评分一致性被撤稿点名 | G-37 | multiple |
| F-38 | 移植瘤无残余表达验证、无ZNF326/机制读出 | G-38 | specialist_rule |
| F-41 | 全文表格（Table S1/S3/S4）位于不可得补充材料 | G-42 | specialist_rule |
| F-47 | 人组织样本分母不闭合、分析人群无法识别 | — | specialist_rule |
| F-48 | TNBC特异性仅表达富集、无非TNBC功能对比，主张超证据 | G-34 | multiple |
| F-49 | ZNF326定性矛盾与过度：'well-characterized' vs 'novel'+自引促癌证据 | G-33 | multiple |
| F-53 | 局限披露不足：仅两条未来方向式'局限' | — | specialist_rule |
| F-56 | 横断面临床相关被表述为因果 | — | specialist_rule |
| F-57 | 图像呈现规范缺失：scale bar/通道/时间轴/误差线定义 | — | specialist_rule |
| XS-02 | Methods人样本小节未声明分型与临床资料收集，Results却报告患者特征关联 | — | cross_section_reconciliation |

## Minor / Info 级发现（摘要）

| ID | 严重度 | 发现 | G 条目 |
| --- | --- | --- | --- |
| F-14 | minor | 引文语境失配与跨适应证引用：[18]/[19]/[20]张冠李戴、[27]心血管ASO类比抗肿瘤 | G-45 |
| F-18 | minor | 6细胞系统一DMEM+7%FBS偏离常规培养条件 | G-15 |
| F-19 | minor | MCF-10A'transformed'实体误报 | G-16 |
| F-26 | minor | MG132剂量/时长未给、仅一种蛋白酶体抑制剂 | G-24 |
| F-32 | minor | OLBC15序列/CPAT面板=Fig S1不可得、无登录号/RACE/Northern | G-28 |
| F-33 | minor | 编码潜能仅CPAT单工具、无阈值声明 | G-29 |
| F-39 | minor | 体积曲线重复测量结构未声明分析方法 | G-40 |
| F-40 | minor | CCK-8密度过高、无时间点/复孔、viability未区分机制 | G-41 |
| F-42 | minor | 文字/交叉引用错误：真实笔误与Fig 3E,F错引（空引用判转换伪影） | G-43 |
| F-43 | minor | ceRNA假说与核定位证据张力未讨论 | G-44 |
| F-50 | minor | 背景引文[13]（RMST）本身已被撤稿 | — |
| F-51 | minor | 转录本命名与公共数据库脱节、基因符号问题 | — |
| F-52 | minor | 《赫尔辛基宣言》引用版本过时、伦理声明模板化 | — |
| XS-01 | minor | 机制链全部限定于MDA-MB-231单系，与'TNBC progression'普适主张不匹配 | — |
| F-45 | info | 图像完整性自审受阻（无图像文件） | G-47 |
| F-46 | info | COI/数据可用性声明材料中未见（转换丢失vs原文缺失待核） | G-48 |
| XS-03 | info | 受阻核对登记：Results↔Tables与Methods↔基线表 | — |

## 问题簇（防级联抬分）

- **C-RET 撤稿与数据完整性**（critical）：成员 F-01。唯一的外部证据根因cluster：图像重复、原始数据差异、不可重复、污染、pulldown条件、抗体问题全部聚合于此，按一个critical根因计一次。下游F-16/F-24/F-25/F-28/F-30/F-44/F-54/F-55的critical定级部分依赖本cluster的外部信号（L3上调），已在各条记录'通知陈述，非本审观察'，不将同一外部证据在多个cluster重复计权。
- **C-METH 方法与可重复性报告**（critical）：成员 F-02, F-03, F-05, F-06, F-09, F-16, F-20, F-21。F-02/F-06/F-09/F-16为本cluster的critical成员，均为独立可指认的报告/设计根因（Methods缺失、高维无校正、定量报告缺失、Transwell缺陷），非由同一证据反复升级；F-06的critical来自M4-009规则判定与G-05同址合并（最高值取一次）。
- **C-MECH OLBC15-ZNF326机制链**（critical）：成员 F-22, F-23, F-24, F-25, F-26, F-27, F-28, F-29, F-30, F-31, F-34。F-24/F-25/F-28/F-30四条critical同根因（互作→降解→rescue证据链），按一个critical cluster计一次；各条finding保留独立身份以服务G条目归宿映射，但报告呈现时不得作为4个独立critical累加风险分。F-54（标题级因果主张）为该cluster的主张层投影。
- **C-CLAIM 主张-证据落差**（critical）：成员 F-44, F-54, F-55, F-56, F-48, F-49。F-44/F-54/F-55为critical，分别对应治疗靶点、标题机制因果、体内主张三个不同主张，均受C-RET/C-METH崩塌传导；按主张cluster计一次，不与上游cluster叠加重复计权。F-48/F-49/F-56为major层主张问题。
- **C-INVT 体内臂**（critical）：成员 F-02(体内部分), F-03, F-04, F-38, F-55。方法缺失（critical）、设计报告缺口（major）、伦理声明（major）、机制读出（major）、主张失效（critical）分层记录；G-01的critical→major降档与G-02的critical维持均在此cluster内裁决，伦理子项不与可重建性根因重复加权。
- **C-SUPP 补充材料受阻**（major）：成员 F-31, F-32, F-41, F-05(引物表), F-15。共享SYS-002根因（补充docx未提供），属blocked而非稿件缺陷；F-31另有独立的'关键数据应入正文'呈现批评。不计入critical统计。

## 加法保证与 G 条目审计（§6.2）

- **additive_guarantee_held = true**
- L0 裸模型产出 **48 条 G 条目**；48/48 均有终态：**无 rejected**（未凭空减去任何一条）；promoted_to_finding × 47、merged × 1（G-31→F-31）。
- 专家 verdict（含同一条目多模块判定）：confirm 47 / refine 13 / refute 0 / out_of_scope 0。
- severity 变化 10 条，全部附理由：
  - G-01：critical → major（F-04）—— M6 refine：'未报告≠未获批'，按规则维持报告缺口级major；升级触发器（机构核实从未获批）未触发；撤稿通知不含伦理指控，外部升级路径未触发
  - G-05：major → critical（F-06）—— 与M4-009（规则库：高维组学无多重校正→critical）同址合并，按'最高值取一次'定为critical
  - G-08：major → critical（F-09）—— L3上调（M4）：确定性取证因无可复算对象not_applicable恰证报告缺口；撤稿通知认定关键结果无法重复并点名迁移定量差异
  - G-13：major → critical（F-16）—— L3上调（M3）：撤稿通知陈述迁移定量原始数据差异，Fig 5E rescue迁移面板被认定重复自Li 2018
  - G-21：major → critical（F-24）—— L3上调（M3）：FISH Fig 4D被认定重复自Koo 2017、Fig 4B原始数据差异、pulldown条件不一致被点名，三支柱同时受损
  - G-23：major → critical（F-25）—— L3上调（M3）：Fig 5B被认定重复自Shen 2019、Fig 5A原始数据差异
  - G-26：major → critical（F-28）—— L3上调（M3/M7）：Fig 5E唯一rescue面板被认定重复自Li 2018、迁移定量被点名；KLF17部分回复提示ZNF326非依赖组分未讨论
  - G-32：major → critical（F-30）—— L3上调（M3）：撤稿通知明确点名'ZNF326抗体特异性验证不足'（作者经通知自认）
  - G-37：minor → major（F-37）—— L3上调（M4）：撤稿通知点名临床样本IHC评分一致性原始数据差异，报告缺口风险成现实
  - G-46：major → critical（F-44）—— L3上调（M7）：全文零靶向干预实验，唯一在体支撑因撤稿整体失效，hedge不豁免

## L2 确定性核验与 X1 外部核验台账

| 工具 | 终态 | 结果 |
| --- | --- | --- |
| external_figure_validation(X1) | executed | executed（85+6项；signals 9；含本文撤稿确认与bib-0013撤稿） |
| ethics_compliance_check | executed | executed（SIG-602 unmet；SIG-604/605/606/607 partial_extraction） |
| animal_model_compliance | executed | executed（SIG-701 3R缺失；SIG-702 无必要性论证） |
| normalize_biomed_units | executed | executed（剂量单位对维度自洽，无信号） |
| statistical_forensics | not_applicable | not_applicable（无计数表/无检验量+df+p/无CI/无mean+n+整数量表；理由已登记） |
| figure_integrity_audit | not_applicable | not_applicable（无图像文件→SYS-001；期刊调查外部结论经X1通道承接） |
| sequence_identifier_audit | not_applicable | not_applicable（ENSG前缀不在工具支持范围；由Ensembl REST ad hoc核验替代，EV-205） |
| 试剂厂商货号核验 | skipped | skipped（无工具端点，SYS-006；M3-030存unresolved） |
| LINC00501表达查询 | skipped | skipped（无表达谱端点，SYS-006） |

**X1 关键外部结论**

1. **本文已被撤稿**：Europe PMC pubType=`Retracted Publication`；JATS 元数据 `is-retracted=yes` + retraction-forward；撤稿通知全文（PubMed PMID 41578707）取回并 hash 存档。理由四项见头部警示。
2. **被撤引文**：参考文献 [13]（RMST，10.1002/jcp.26311，Introduction 引用）已被撤稿（F-50）。其余 26 条未检撤稿。
3. **参考文献存在性**：27/27 DOI 经 Crossref 解析成功 —— 无幻觉/纸厂引文特征。
4. **细胞系**：8 个名称在 Cellosaurus 均无 Problematic（污染/错鉴）标注；撤稿通知所述「潜在交叉污染」指本研究培养过程，与库记录并存不悖（F-17）。
5. **基因符号**：OLBC15/LIMT/BORG/LDAC7/RP11-597D13.9/Cox2 非 HGNC 批准符号；DBC1 为旧符号（现行 BRINP1）；LDAC7 判定为 HDAC7 笔误（HGNC + ref-18 题录双证，F-51）。
6. **序列**：ENSG00000259457 → Ensembl 现行符号 **LINC03137**，chr15、lncRNA —— 稿件 chr15 定位主张与数据库一致，但全文未给 GenBank 登录号、命名无法对接公共库（F-51）。
7. **伦理/动物工具信号**：ETH-ANI-002（3R 未报告，ethics_requirement_unmet）；ARRIVE 2.0 4a 体内必要性未论证；麻醉/安乐死/许可条款因动物方法零描述不可评估（partial_extraction，不误判为违规）。

## 系统限制（all_system_limitations）

| ID | 类别 | 影响 |
| --- | --- | --- |
| SYS-001 | no_image_channel | Figure 1-6无图像文件：WB条带重复/拼接、FISH/IHC/迁移染色/大体照片像素级审查不可执行；措辞一律'无法排除/无法确认'；期刊调查外部结论由external_validation通道承接 |
| SYS-002 | supplement_unavailable | JCLA-34-e23304-s001.docx未提供：Figure S1/S2、Table S1-S4不可核验；引物序列、5个MS候选蛋白身份、患者特征、KLF17/启动子占据面板受阻 |
| SYS-003 | conversion_artifacts | fulltext.txt：内联引用编号剥离、长行截断、REFERENCES空——以fulltext.xml为准；空引用判转换伪影 |
| SYS-004 | external_source_transient_failure | 3条DOI（bib-0011/0012/0013）首轮Crossref/EPMC查询超时，重试成功关闭；无遗留 |
| SYS-005 | external_source_unavailable | IACUC/伦理批件号真伪无公开核验接口：动物伦理批准与人样本批件号只能报'无法核验' |
| SYS-006 | tool_scope_gap | 试剂厂商货号、细胞系表达谱（LINC00501）、CPAT阈值、Ensembl以外登录号无工具端点→相应请求skipped并维持unresolved表述 |
| SYS-007 | pipeline_correction | 主会话首轮DOI抽取regex缺陷导致误判'参考文献无DOI'，经M2 XML回查+主会话复验更正；未产生错误finding |

## 人工复核优先级

- **P0**（编辑/诚信办公室）：记录并维持撤稿状态：本记录已由Retraction(10.1002/jcla.70169)覆盖；若为撤稿后复核，直接对照通知四项理由即可闭合
- **P1**（图像取证+学科审稿人）：如仍需内容级复核：索取未裁剪原始WB/显微图像并运行figure_integrity_audit；索取JCLA-34-e23304-s001.docx以解除SYS-002对Table S1-S4/Figure S1-S2的阻塞
- **P2**（伦理委员会）：向重庆三峡中心医院及机构伦理委员会索取：动物实验伦理批件（IACUC）、人样本知情同意与HREC批准档案（覆盖2017.01-2018.11及全部下游用途）——撤稿后核验对象应为机构而非作者
- **P3**（统计师）：统计复核：每组n、独立重复、精确P/效应量、profiling的FDR与阈值（当前报告缺口使任何定量不可复核）
- **P4**（实验方法审稿人）：细胞系STR/支原体记录与全部抗体（anti-ZNF326等）验证数据、慢病毒体系参数（撤稿通知已点名污染与抗体验证问题）

## 管线完整性记录

- 跨专家定级冲突1：G-02在M3(critical)与M6(major)间分歧未经L3仲裁，L4已裁决（维持critical，理由见global_audit）
- 跨专家定级冲突2：同一事实[13]被撤引文，M2-014给major、M7-016给info，无L3冲突消解记录，L4协调为minor（F-50，理由：仅背景罗列、[14]部分支撑）
- 跨专家定级冲突3：Fig 3E,F错引，M2-002给major、M5-016给minor，L4取minor（内容可由Fig 3E覆盖）并并入F-42
- 跨专家定级冲突4：G-48终态M2-013给minor、M6-008给info，L4取info（理由见global_audit）
- M3-030（PFA货号疑误）此前无终态登记：既不满足finding证据门槛也无候选处置记录，L4补登记为unresolved（SYS-006）
- M3-032横跨G-08与G-40范围（含重复测量子项），存在与F-09/F-39的潜在重复计数；L4划分：主体归F-09，G-40面向归F-39，已注明不重复加权
- 依赖声明：Discussion para2在fulltext.txt中被截断（SYS-003），'may possibly be a tumor-specific lncRNA in TNBC'等措辞核对依赖M7的XML核验结论，L4无法独立复验截断段原文——以XML为准的纪律下接受，如实注明
- 无G条目消失：48/48均有专家verdict覆盖且均有明确终态；加法保证成立（无rejected条目，故无减法；全部为promoted/merged）
- 无证据悬空finding：每条F条目均可回溯至专家产物与稿件位置或外部记录；F-45/F-31/F-32/F-41/F-15的不可核验部分已明确挂接SYS-001/SYS-002而非伪装为稿件缺陷

## 运行时遥测

```json
{
 "child_sessions": 9,
 "task_calls": 15,
 "continuations": 6,
 "modules_run": [
  "M2",
  "M3",
  "M4",
  "M5",
  "M6",
  "M7"
 ],
 "modules_skipped": {},
 "modules_skip_reason": "无跳过：研究设计含体外细胞(M3)+动物(M3/M6)+人样本(M6)+统计(M4)+图表(M5)+结论(M7)，M2为默认接收方",
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
 "tool_terminal_states": {
  "external_figure_validation(X1)": "executed（85+6项；signals 9；含本文撤稿确认与bib-0013撤稿）",
  "ethics_compliance_check": "executed（SIG-602 unmet；SIG-604/605/606/607 partial_extraction）",
  "animal_model_compliance": "executed（SIG-701 3R缺失；SIG-702 无必要性论证）",
  "normalize_biomed_units": "executed（剂量单位对维度自洽，无信号）",
  "statistical_forensics": "not_applicable（无计数表/无检验量+df+p/无CI/无mean+n+整数量表；理由已登记）",
  "figure_integrity_audit": "not_applicable（无图像文件→SYS-001；期刊调查外部结论经X1通道承接）",
  "sequence_identifier_audit": "not_applicable（ENSG前缀不在工具支持范围；由Ensembl REST ad hoc核验替代，EV-205）",
  "试剂厂商货号核验": "skipped（无工具端点，SYS-006；M3-030存unresolved）",
  "LINC00501表达查询": "skipped（无表达谱端点，SYS-006）"
 },
 "global_findings_count": 48,
 "global_findings_confirmed": 48,
 "global_findings_refined": 13,
 "global_findings_refuted": 0,
 "global_findings_unresolved": 0,
 "additive_guarantee_held": true,
 "additive_guarantee_note": "48/48 G条目有终态（promoted_to_finding×47、merged×1[G-31→F-31]）；rejected=0，即未从裸模型结果中减去任何条目；所有severity变化（G-01 critical→major；G-05/08/13/21/23/26/32/37/46升档；G-43/48 refine）均带理由记录",
 "findings_added_beyond_global": 13,
 "finding_origin_breakdown": {
  "external_validation": 3,
  "multiple": 31,
  "specialist_rule": 23,
  "cross_section_reconciliation": 3
 },
 "origin_note": "multiple=多来源合流；global_review独有=0（全部G条目经专家规则/外部证据增强后入册）；deterministic_tool信号以吸收方式进入F-04/F-09/F-17/F-46/F-51，未单独立项",
 "global_findings_refined_unique": [
  "G-01",
  "G-11",
  "G-15",
  "G-17",
  "G-19",
  "G-39",
  "G-40",
  "G-43",
  "G-46",
  "G-48"
 ],
 "verdict_note": "专家verdict条目共60条（47 confirm/13 refine，含同一条G由多个模块分别判定）；按G条目去重：48条全部保留，10条经refine修正表述或定级，0条refuted/out_of_scope/unresolved"
}
```
