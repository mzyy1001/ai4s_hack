# M2 · 宏观逻辑与格式完整性

**负责人：ZY（卓妍）** 

对应会议纪要"第一层：无依赖内部逻辑校验"。**一期不调用任何外部数据**，仅凭论文自身内容判断。
核心问题：抛开生物学专业性，这篇论文作为一篇论文，逻辑链是否闭环、各部分是否完整？

**重要边界**：M2 检查“是否报告、是否前后一致、是否存在形式逻辑断裂”；不把“未报告”自动当成“未实施”，也不替代 M3（实验惯例）、M4（统计方法）、M6（伦理规范）或 M7（证据强度与结论层级）的判断。

需要外部数据的检查（引用真实性、文献重复度）归本模块，二期实现，见 §5。

---

## 1. 输入

- `structured_result_v2`（M1 Stage 3b 产出；不得消费仍含 `unresolved` 的 v1），重点看 `article_design.primary_design`、`design_components[]`、`objective`、`conclusion.claims[]`、`evaluation_matrix`、`key_data[]` 与 `gaps[]`
- 全文分节结果与图表清单（阶段 ①）

### 1.1 适用性与证据门控

1. 章节要求按 `article_design.primary_design` 及每个 `design_components[]` 路由；混合研究不得压成单一 `study_type`。
2. “缺失”只有在适用范围内完成全文（含声明、补充材料可访问部分）检索后才能成立，必须使用 `absence` 证据记录检索范围、检索词和结果；不可读或不可访问的来源只能进入 `system_limitation`。
3. 明确报告了方法但没有证明其科学上最优，不由 M2 报警；明确写出存在但未按规定执行，才交 M3/M4/M6。
4. 证据不明确、设计分类含糊或来源冲突时，finding 的 `review_confidence` 最高为 `medium`，不得仅凭 `evaluation_matrix` 或 signal 立 finding。

## 2. 校验清单

### 2.1 章节完整性

逐项核对是否存在且非空：Abstract / Introduction / Methods / Results / Discussion / Conclusion /
Ethics statement / Funding / Conflict of interest / Data availability / References。

#### 2.1.1 不同刊型的必备章节表

下表只是常见格式的默认路由，不是完整的文章类型枚举。协议/注册报告、诊断与预后模型、数据资源、方法学论文、scoping/umbrella/network meta-analysis、定性研究和 AI benchmark 应按 `article_design` 及期刊作者指南另行路由；合并章节（例如 Discussion/Conclusion）视为已满足结构要求。

| 章节 | 研究论文 | 短报告 | 病例报告 | Meta分析 | 综述 | 缺失 severity |
| --- | --- | --- | --- | --- | --- | --- |
| Abstract（结构化格式） | 按期刊要求；信息要素必须存在 | 按期刊要求 | 按期刊要求 | 按期刊要求 | 推荐 | minor；核心结果缺失可 major |
| Introduction | 必须 | 必须 | 必须 | 必须 | 必须 | major |
| Methods | 必须 | 必须 | 可选 | 必须 | 必须 | critical |
| Results | 必须 | 必须 | 必须 | 必须 | N/A | critical |
| Discussion | 必须 | 可合并 | 必须 | 必须 | N/A | major |
| Conclusion（可并入 Discussion） | 推荐；仅在期刊格式要求时必须 | 推荐；可并入 Discussion | 推荐；可并入 Discussion | 推荐；可并入 Discussion | 推荐；可并入 Discussion | minor/major |
| Ethics statement | 必须* | 必须* | 必须* | 推荐 | N/A | major* |
| Informed consent | 必须** | 必须** | 必须 | N/A | N/A | major** |
| Funding | 必须 | 必须 | 必须 | 必须 | 必须 | minor |
| Conflict of interest | 必须 | 必须 | 必须 | 必须 | 必须 | major |
| Data availability | 必须 | 推荐 | 推荐 | 必须 | N/A | minor |
| References | 必须 | 必须 | 必须 | 必须 | 必须 | major |
| Trial registration / protocol registration*** | 临床试验：必须；系统综述：报告 PROSPERO/OSF 等方案注册（若有） | 临床试验：必须 | N/A | 方案注册：推荐/按期刊要求；不是“trial registration” | N/A | major；注册时序或核心终点冲突可升级 |

\* 仅当涉及人体受试者或动物实验时必须  
\*\* 仅当涉及人体受试者时必须  
\*\*\* 临床试验注册与系统综述方案注册是不同概念；不能因未注册试验而自动否定 Meta 分析。

#### 2.1.2 结构化摘要要素检查

若期刊或研究类型要求结构化摘要，摘要应至少包含：
- **Background/Objective** - 研究背景与目标
- **Methods** - 研究设计、样本量、主要方法
- **Results** - 关键数值结果（带统计量）
- **Conclusion** - 主要结论

缺失任一要素触发 `minor` finding（category: `incomplete_abstract`）；若为非结构化摘要，则检查同一信息是否以连续文本出现，不因缺少小标题报警。

#### 2.1.3 方法学报告清单

根据研究类型，检查是否符合相应报告规范。**每类研究必须报告的核心要素**如下：

##### 2.1.3.1 临床研究与流行病学

| 研究类型 | 报告规范 | 核心必备要素 | 缺失 severity |
| --- | --- | --- | --- |
| **随机对照试验 (RCT)** | CONSORT | 流程图、样本量计算、随机化方法、分配隐藏、盲法、试验注册号 | critical |
| **观察性研究** | STROBE | 研究设计类型、样本来源、纳排标准、暴露/结局定义、混杂因素调整 | major |
| **诊断准确性研究** | STARD | 流程图、参考标准、盲法评估、诊断阈值、敏感性/特异性 | major |
| **Meta分析/系统综述** | PRISMA | 流程图（文献筛选）、检索策略、纳排标准、质量评价、异质性分析 | critical |
| **队列研究** | STROBE-cohort | 随访时间、失访率、基线可比性、时间依赖性偏倚处理 | major |
| **病例对照研究** | STROBE-case-control | 病例与对照选择、匹配方式、回忆偏倚控制、OR值与CI | major |
| **横断面研究** | STROBE-cross-sectional | 抽样方法、应答率、患病率估计、因果推断限制说明 | minor |
| **非劣效/等效试验** | CONSORT-noninferiority | 非劣效界值预设、单侧/双侧检验、ITT与PP分析 | critical |

##### 2.1.3.2 遗传学与基因组学

| 研究类型 | 报告规范 | 核心必备要素 | 缺失 severity |
| --- | --- | --- | --- |
| **遗传关联研究 (GWAS)** | STREGA | SNP选择标准、基因分型方法、Hardy-Weinberg平衡检验、多重检验校正、人群分层控制 | critical |
| **全基因组/外显子测序** | —— | 测序平台、覆盖深度、比对参考基因组版本、变异calling算法、过滤标准 | major |
| **qPCR** | MIQE | 引物序列与验证、反应效率、参考基因选择、Cq值报告、技术重复数 | major |
| **基因表达谱 (RNA-seq)** | —— | 建库方法、测序深度、归一化方法、差异表达阈值（FDR < 0.05, \|log2FC\| > 1）、批次效应处理 | major |
| **CRISPR基因编辑** | —— | sgRNA序列、脱靶分析、编辑效率验证、供体序列（HDR）、基因型鉴定方法 | major |
| **单细胞测序** | —— | 细胞数、捕获方法、质控标准（线粒体%、基因数）、批次整合方法、细胞类型注释依据 | major |
| **表观遗传学 (ChIP-seq, ATAC-seq)** | —— | 抗体验证（ChIP）、文库复杂度、peak calling算法、重复样本相关性、motif富集分析 | major |

##### 2.1.3.3 分子生物学与生物化学

| 研究类型 | 核心必备要素 | 缺失 severity |
| --- | --- | --- |
| **Western blot** | 一抗/二抗信息、蛋白定量方法、内参选择、条带定量方法、完整膜图像（未裁剪）、生物学重复数≥3 | major |
| **流式细胞术** | 门控策略图、抗体克隆号、荧光补偿、阳性对照、细胞数≥10,000 events、FMO对照（多色） | major |
| **免疫组化/免疫荧光** | 抗体稀释度与孵育条件、抗原修复方法、阴性对照、定量方法（盲法评分/软件分析）、代表性视野数 | major |
| **显微成像** | 显微镜型号、物镜NA、激光波长/功率、曝光时间、Z-stack间隔、图像处理软件与参数、比例尺 | minor |
| **质谱蛋白组学** | 质谱仪型号、肽段鉴定FDR、定量方法（label-free/TMT）、蛋白数据库版本、生物信息学分析流程 | major |
| **酶活性测定** | 底物浓度、反应时间、线性范围验证、Km/Vmax值、抑制剂IC50与95% CI | major |
| **细胞增殖/毒性实验 (MTT/CCK-8)** | 细胞接种密度、孵育时间、剂量范围、生物学重复≥3、技术重复≥3、IC50计算方法 | minor |

##### 2.1.3.4 动物实验与体内研究

| 研究类型 | 报告规范 | 核心必备要素 | 缺失 severity |
| --- | --- | --- | --- |
| **动物实验（所有类型）** | ARRIVE 2.0 | 伦理批准号、动物品系/来源、性别、年龄/体重、样本量计算、随机化与盲法、人道终点 | critical |
| **肿瘤模型** | —— | 细胞系/PDX来源、接种细胞数、肿瘤测量方法与频率、终点肿瘤体积、动物排除标准 | major |
| **行为学实验** | —— | 驯化时间、测试时间段、实验者盲法、视频记录与分析软件、场地清洁消毒 | major |
| **药代动力学 (PK)** | —— | 给药途径/剂量、采样时间点、生物样本处理、定量方法（LC-MS）、PK参数计算软件 | major |

##### 2.1.3.5 毒理学

| 研究类型 | 核心必备要素 | 缺失 severity |
| --- | --- | --- |
| **急性毒性** | OECD指南编号、LD50/LC50与95% CI、剂量爬坡方案、观察期、死亡时间、临床症状记录、病理解剖 | major |
| **亚慢性/慢性毒性** | 给药期、恢复期、体重/摄食量监测频率、血液学/生化指标、器官重量、组织病理学、NOAEL/LOAEL | major |
| **遗传毒性** | Ames试验（菌株、剂量、S9）、微核试验（给药-取样间隔、细胞数）、彗星试验（尾矩、阳性对照） | major |
| **生殖发育毒性** | 交配方案、孕期给药窗口、活胎数/死胎数、骨骼/内脏畸形检查、F1代发育指标 | major |
| **剂量-响应曲线** | 至少5个剂量、跨2-3个数量级、曲线拟合模型（4参数logistic）、EC50/IC50与Hill系数 | major |

##### 2.1.3.6 生物工程与生物材料

| 研究类型 | 核心必备要素 | 缺失 severity |
| --- | --- | --- |
| **组织工程支架** | 材料组成/分子量、制备方法、孔隙率/孔径、表面形貌（SEM）、机械性能、降解速率、细胞相容性 | major |
| **纳米材料/纳米药物** | 粒径分布（DLS/TEM）、Zeta电位、包封率/载药量、体外释放曲线、稳定性、内毒素检测 | major |
| **3D生物打印** | 生物墨水组成、打印参数（速度/压力/温度）、打印精度验证、结构完整性、细胞活力（打印后） | major |
| **医疗器械性能** | ISO标准编号、生物相容性（ISO 10993）、灭菌方法验证、疲劳测试、临床前动物验证 | critical |
| **微流控芯片** | 通道尺寸、流速范围、芯片材质、表面处理、细胞/液体操控验证 | minor |

##### 2.1.3.7 生物信息学与计算生物学

| 研究类型 | 核心必备要素 | 缺失 severity |
| --- | --- | --- |
| **机器学习预测模型** | 特征选择方法、模型类型、超参数、训练-验证-测试集切分、性能指标（AUC/准确率/F1）、外部验证 | critical |
| **蛋白结构预测/对接** | 预测软件/力场、模板选择、对接评分函数、结合能、关键残基、MD模拟验证 | major |
| **通路富集分析** | 数据库版本（KEGG/GO/Reactome）、富集算法、背景基因集、多重检验校正、FDR阈值 | minor |
| **网络分析** | 网络构建方法、节点/边定义、拓扑参数、模块识别算法、关键节点验证 | minor |

##### 2.1.3.8 触发规则

**触发条件**：
- 研究类型明确属于上述任一类别，但适用部分未报告对应规范的核心要素；
- 报告规范要求流程图（CONSORT/PRISMA/STARD），但全文无流程图或流程图数字无法与正文闭合；
- 关键方法学参数缺失（如 Western blot 无内参、GWAS 无多重检验校正、动物实验无伦理批准）。

报告规范应记录名称、版本/年份、适用研究组件和缺失条目。缺失“建议性”条目默认 `minor`；缺失会改变可重复性、主要终点解释或伦理授权的条目才可为 `major/critical`。下列数值（例如技术重复数、流式 events、剂量点数、RNA-seq fold-change）均是复核提示，不是跨实验的硬性淘汰阈值。

**Severity 判定**：
- `critical`：缺失或明确违反会使主要结论不可解释、造成严重数据完整性风险或涉及未授权的人体/动物研究（如 RCT 未随机化、明确全数据特征筛选、动物实验无伦理批准）；
- `major`：影响主要结果的可重复性、可解释性或外部适用性；
- `minor`：编辑性或补充性报告缺口，不改变当前核心推断。

**AI/计算研究补充**：根据研究用途同时考虑 TRIPOD+AI/PROBAST-AI（预测模型）、CONSORT-AI/SPIRIT-AI（临床 AI 干预）、CLAIM 或 STARD-AI（医学影像/诊断）等要求。至少核对模型/软件版本、数据来源与时间窗、患者/切片/站点级切分、预处理是否在每个训练折内拟合、嵌套交叉验证或独立验证、随机种子、性能指标及 95% CI、校准、阈值预设、类别不平衡、亚组性能和临床效用。

**Category**: `missing_reporting_guideline_element`

**正例**（应报警）：
> 一篇GWAS论文报告了30个显著SNP（p < 5×10⁻⁸），但Methods未提及多重检验校正方法，未报告基因分型call rate，未进行Hardy-Weinberg平衡检验。

**反例**（不应报警）：
> 一篇GWAS论文Methods明确写明："SNP call rate > 95%，Hardy-Weinberg平衡 p > 0.001，使用Bonferroni校正后显著性阈值 p < 5×10⁻⁸。"

### 2.2 逻辑链闭环

沿 `研究问题 → 假设 → 实验设计 → 结果 → 结论` 逐段追踪，检查四类断裂：

#### 2.2.1 Objective Drift

**定义**：Introduction 提出的研究问题在 Results 中没有对应实验数据回答。

**检查步骤**：
1. 从 Introduction 最后一段或 Abstract 的 Objective 提取核心研究问题（通常以"we aimed to..."、"the objective was..."、"we hypothesized that..."引出）
2. 在 Results 中逐节检查是否有实验/分析直接回答该问题
3. 若某个声称的主要目标在结果中无对应数据，触发 finding

**触发条件**：
- Abstract 或 Introduction 明确列出 2+ 研究目标，但 Results 只涵盖其中部分
- Introduction 提出具体假设（如"我们假设药物 X 可降低炎症因子 Y"），但 Results 未测量因子 Y
- 研究声称"探讨机制"，但只给了表型数据，无分子机制实验

**Severity**: `major`  
**Category**: `objective_drift`

**正例**（应报警）：
> Introduction: "We aimed to (1) evaluate the efficacy of compound X in tumor growth inhibition and (2) investigate its mechanism via the MAPK pathway."
> Results 只报告了肿瘤生长曲线，未做任何 MAPK 通路检测（Western blot、磷酸化分析等）。

**反例**（不应报警）：
> Introduction 同上，Results 包含：§3.1 肿瘤生长抑制实验，§3.2 MAPK 通路蛋白表达分析。

---

#### 2.2.2 Orphan Results

**定义**：Results 中的实验在 Introduction 中无动机铺垫，或在 Discussion 中无解读。

**检查步骤**：
1. 列出 Results 中所有实验/数据块（通常按小节或图表组织）
2. 回溯 Introduction：该实验的目的是否被提及？是否从假设/背景自然引出？
3. 前瞻 Discussion：该实验的结果是否被解读？是否与文献对比或给出生物学意义？
4. 若某实验"突然出现"且后续无讨论，触发 finding

**触发条件**：
- Results 包含的某个实验在 Introduction 中从未提及相关背景
- Results 的某组数据在 Discussion 中完全未被讨论（仅在 Results 中描述一遍）
- 补充材料中的关键实验未在正文 Discussion 中整合

**Severity**: `major`（前向孤儿）/ `minor`（后向孤儿，即 Discussion 未充分解读）  
**Category**: `orphan_results`

**正例**（应报警）：
> Introduction 聚焦于药物对肝癌的作用，Results 突然出现"§3.5 Drug X reduces anxiety-like behavior in mice"（焦虑行为实验），但 Introduction 从未提及行为学或神经保护，Discussion 也未解释为何做此实验。

**反例**（不应报警）：
> Introduction 提到"除抗肿瘤作用外，初步证据表明 X 可能影响神经系统"，Results §3.5 给出行为学数据，Discussion §4.3 讨论"意外发现的神经保护作用及可能机制"。

---

#### 2.2.3 Conclusion Overreach

**定义**：Conclusion 的主张范围、因果强度或推广对象超出实验设计能支持的范围。

**注**：本条与 M7（结论与讨论模块）有职责交叉。**边界划分**：
- **M2 负责**：形式逻辑断裂——结论提到的对象/指标在实验中根本未测（如体外实验得出体内结论、动物实验得出人类结论且无任何桥接讨论）
- **M7 负责**：证据强度判定——实验做了但证据层级不足以支撑结论的因果/疗效主张

**M2 触发条件**（仅限形式逻辑跃迁）：
- 仅有**体外细胞**实验，结论写"compound X is a potential therapeutic agent for patients"（直接跳到患者，无体内数据）
- 仅有**动物模型**数据，结论写"X improves clinical outcomes in human disease"（无任何人类数据或临床试验注册）
- 仅测了**单一指标**（如某一促炎因子），结论写"X comprehensively modulates the immune response"（全面调控，但只测了一个分子）
- **小样本探索性研究**（n < 30），结论写"X is effective and safe"（确证性结论，应为"preliminary evidence suggests..."）

**Severity**: `major`  
**Category**: `conclusion_overreach`

**正例**（应报警）：
> 实验：仅在 HepG2 细胞系中测试化合物 X 的细胞毒性（MTT assay）。
> 结论："Compound X represents a promising treatment for hepatocellular carcinoma patients and warrants clinical trials."
> ——缺失：体内药代动力学、动物模型疗效、毒理学。

**反例**（不应报警）：
> 实验同上。
> 结论："Compound X shows cytotoxic effects in HepG2 cells in vitro. Further studies in animal models and human tissues are needed to evaluate its therapeutic potential."

---

#### 2.2.4 Circular Reasoning

**定义**：用待证明的结论作为方法设计或结果解读的前提。

**常见模式**：
- **方法中预设结论**："为验证 X 蛋白促进肿瘤生长，我们在 X 高表达的肿瘤细胞中..."（预设 X 促进生长 → 选择 X 高表达细胞 → 观察到生长 → 声称证明了 X 的作用）
- **用结果解释结果**："化合物 X 降低了炎症因子 Y，这证明 X 具有抗炎作用，因此炎症因子 Y 的降低是合理的。"
- **选择性亚组分析**：先看数据，再定义"响应者"，然后声称"在响应者中药物有效"

**触发条件**：
- Methods 中关键分组/筛选标准依赖于待证结论
- Discussion 用结论本身解释观察到的现象，无独立机制假设
- 事后分层分析（post-hoc subgroup）未明确标注为探索性

**Severity**: `major`  
**Category**: `circular_reasoning`

**正例**（应报警）：
> Methods: "为研究化合物 X 的降糖机制，我们选择了对 X 敏感的糖尿病小鼠模型..."
> （"对 X 敏感"需要先知道 X 有降糖作用，但这正是研究要证明的结论）

**反例**（不应报警）：
> Methods: "我们使用 db/db 小鼠模拟 2 型糖尿病，以评估化合物 X 的降糖效果。"
> （模型选择基于疾病类型，不预设化合物有效性）

#### 2.2.5 预设终点、分析人群与选择性报告

**定义**：注册/方案、Methods、Results、Abstract 或 Conclusion 对主要终点、分析人群、时间点或关键亚组的定义发生未解释变化，或只呈现有利结果。

**触发条件**：
- 方案/注册记录（若可得）与稿件的 primary endpoint、time point、分析人群或主要亚组不一致，且未说明修订理由；
- Methods 预设的主要/安全性终点在 Results 中缺失，或 Results 新增的主要终点在 Introduction/Methods 中没有动机；
- 仅报告显著的模型、亚组、时间点或图表，未交代其余预先说明的分析。

**Severity**：核心终点更换或选择性报告为 `critical`；未解释的次要终点/分析人群变化为 `major`。仅有注册信息不可访问时不得判定不一致，改记 `system_limitation`。

**Category**：`selective_reporting` / `endpoint_switching` / `analysis_population_mismatch`。

#### 2.2.6 受试者流、分母与时间线闭合

将筛选、随机化、分组、随访、排除、失访和最终分析人数按研究组件逐一对账；同时核对表格、图注、正文、Abstract 的分母、单位、时间点和组名。无法由现有证据解释的冲突触发 `participant_flow_inconsistency`（主要终点/安全性分母为 `major`，编辑性差异为 `minor`）。

### 2.3 数据泄露场景库

**本节仅适用于含机器学习/预测模型的论文**（由 `evaluation_matrix.has_ml_model` 判定）。

#### 2.3.1 训练-测试集污染

**场景 1：重复样本跨训练/测试集**

**定义**：同一生物样本、同一患者或同一实验批次的数据同时出现在训练集和测试集。

**检测线索**：
- Methods 未明确说明如何防止样本泄露（如"患者层面切分"、"独立队列"）
- 使用随机切分但涉及配对数据（如同一患者的多个时间点、同一组织的多个切片）
- 补充材料的样本 ID 列表中出现重复
- 声称"独立验证集"但样本采集时间/地点与训练集重叠

**触发条件**：
- 明确使用随机切分 + 数据具有内在层级结构（患者→样本→测量）且未按顶层单元切分
- 明确存在同一患者、同一组织块、同一实验批次或其衍生样本跨训练/验证/测试集；仅“同一医院/同一批次/同一队列且未说明独立性”只能触发报告缺口，不能单独证明泄露
- 时间序列预测中，训练集和测试集的时间窗口有重叠

**Severity**：已确认样本/衍生样本重叠为 `critical`；仅未报告切分层级为 `major`，类别为 `data_split_not_reported`。
**Category**：`data_leakage_sample_overlap` / `data_split_not_reported`

**正例**（应报警）：
> Methods: "我们收集了 500 名患者的血液样本，每名患者采集 3 个时间点。数据随机分为训练集（70%）和测试集（30%）。"
> ——问题：1500 个样本点随机切分，同一患者的不同时间点数据会分散到训练和测试集，导致模型在训练时已"见过"测试集患者的特征。

**反例**（不应报警）：
> Methods: "我们在患者层面进行切分，350 名患者用于训练，150 名患者用于测试，确保测试集患者在训练时完全未见。"

---

**场景 2：数据增强后的合成样本泄露**

**定义**：对原始图像/数据进行增强（旋转、裁剪、加噪等）生成合成样本，在切分前未去重，导致同一原始样本的不同增强版本分布在训练和测试集。

**检测线索**：
- Methods 描述了数据增强操作（rotation, flipping, cropping）
- 数据增强在数据集切分**之前**执行
- 未明确说明"先切分后增强"或"增强仅应用于训练集"

**触发条件**：
- 明确写明"数据增强后得到 X 个样本，随机分为训练集和测试集"

**Severity**: `critical`  
**Category**: `data_leakage_augmentation`

**正例**（应报警）：
> Methods: "原始数据集包含 200 张病理图像。我们对每张图像进行旋转（0°、90°、180°、270°）和翻转，生成 1600 张图像，然后随机分为训练集（1280 张）和测试集（320 张）。"

**反例**（不应报警）：
> Methods: "200 张图像在患者层面切分为训练集（160 张）和测试集（40 张）。数据增强（旋转、翻转）仅应用于训练集。"

---

#### 2.3.2 特征工程与预处理泄露

**场景 3：全局归一化/标准化在切分前**

**定义**：使用全部数据（训练+测试）计算归一化参数（均值、标准差、最小值、最大值），再应用到训练和测试集。

**检测线索**：
- Methods 提到 normalization / standardization / min-max scaling
- 未明确说明"仅用训练集计算参数"或"在训练集上 fit，在测试集上 transform"
- 写"数据标准化后分为训练集和测试集"（顺序错误）

**触发条件**：
- 明确写明归一化/标准化在数据切分**之前**
- 描述为"全局归一化"或"对整个数据集进行 z-score 标准化"

**Severity**: `major`  
**Category**: `data_leakage_normalization`

**正例**（应报警）：
> Methods: "我们首先对所有基因表达数据进行 z-score 标准化（均值 0，标准差 1），然后将数据随机分为训练集和测试集。"
> ——测试集的分布信息已泄露到标准化参数中。

**反例**（不应报警）：
> Methods: "数据在患者层面切分后，我们使用训练集计算均值和标准差，并将相同参数应用于测试集。"

---

**场景 4：特征选择使用全部数据**

**定义**：在全部数据上进行特征选择（如差异基因筛选、相关性排序、递归特征消除），然后用选出的特征在切分后的训练集上建模。

**检测线索**：
- Methods 提到 feature selection / differential expression analysis / correlation filtering
- 特征选择步骤在数据切分之前，或未明确说明顺序
- 写"我们筛选出与结局相关的 X 个特征，然后训练模型"（未说明筛选时是否包含测试集）

**触发条件**：
- 明确在全数据集上做特征选择，之后才切分或建模
- 特征选择标准直接使用结局变量（如"选择与生存显著相关的基因"），且测试集参与了这一步

**Severity**: `critical`  
**Category**: `data_leakage_feature_selection`

**正例**（应报警）：
> Methods: "我们对 500 名患者的 20,000 个基因进行差异表达分析，筛选出与疾病状态显著相关的 100 个基因（p < 0.05）。随后将这 100 个基因的表达谱用于构建预测模型，并在训练集和测试集上评估。"
> ——特征选择时已使用全部样本的标签信息。

**反例**（不应报警）：
> Methods: "数据切分后，我们在训练集上进行差异表达分析，筛选出 100 个基因，并在测试集上使用相同基因集评估模型性能。"

---

**场景 5：降维方法（PCA/t-SNE/UMAP）在全数据上拟合**

**定义**：在全部数据上拟合降维模型（如 PCA），得到的主成分或嵌入用于后续建模。

**检测线索**：
- Methods 提到 PCA / t-SNE / UMAP / autoencoder
- 未说明降维是"仅在训练集上 fit"
- 结果中展示的降维图包含训练集和测试集（说明测试集参与了降维拟合）

**触发条件**：
- 明确在数据切分前或全数据集上进行降维
- 降维后的表示用于模型训练

**Severity**: `major`  
**Category**: `data_leakage_dimensionality_reduction`

**正例**（应报警）：
> Methods: "我们对全部 500 个样本的高维特征进行 PCA，提取前 50 个主成分，解释了 90% 的方差。然后将这些主成分输入随机森林模型，并在 7:3 切分的训练集和测试集上评估。"

**反例**（不应报警）：
> Methods: "训练集上拟合 PCA 模型并提取 50 个主成分，将相同的 PCA 变换应用于测试集。"

---

#### 2.3.3 模型选择与超参数调优泄露

**场景 6：用测试集选择模型或调超参数**

**定义**：在多个候选模型或超参数配置中，通过测试集性能选择最优配置。

**检测线索**：
- Methods 比较了多个模型（SVM、随机森林、神经网络等），最终"选择了在测试集上表现最好的模型"
- 超参数调优提到"在测试集上网格搜索"或"根据测试集准确率选择学习率"
- 未提到验证集或交叉验证，直接用测试集指导模型迭代

**触发条件**：
- 明确写明测试集用于模型选择或超参数调优
- 训练过程中多次在测试集上评估并据此调整

**Severity**: `critical`  
**Category**: `data_leakage_model_selection`

**正例**（应报警）：
> Methods: "我们训练了 5 种机器学习模型（逻辑回归、SVM、随机森林、XGBoost、神经网络），在测试集上评估每个模型的 AUC，最终选择 XGBoost（AUC = 0.89）作为最终模型。"
> ——测试集性能已指导模型选择，报告的 AUC 高估真实泛化能力。

**反例**（不应报警）：
> Methods: "我们在训练集上用 5 折交叉验证比较 5 种模型，XGBoost 在验证集上的平均 AUC 最高（0.87），因此选择该模型。最终在独立测试集上评估一次，得到 AUC = 0.85。"

---

**场景 7：迭代模型训练中多次查看测试集**

**定义**：在模型迭代开发过程中，反复在测试集上评估，根据测试集表现调整特征、算法或流程，最终报告的测试集性能已不再独立。

**检测线索**：
- 补充材料或代码显示测试集被多次加载和评估
- Methods 描述了多轮模型改进，每轮都"在测试集上评估"
- 测试集性能异常高，且未提供真正的外部验证

**触发条件**：
- 代码或文本证据表明测试集参与了多次迭代决策
- 声称"最终测试集准确率"，但未说明该测试集在整个开发过程中是否被多次使用

**Severity**: `major`  
**Category**: `data_leakage_test_set_reuse`

---

#### 2.3.4 时间序列与纵向数据泄露

**场景 8：时间序列随机切分（未来信息泄露）**

**定义**：对有时间顺序的数据进行随机切分，导致模型在训练时看到"未来"数据。

**检测线索**：
- 数据具有时间戳或明确的时间序列结构（股价、患者监测、疾病进展）
- Methods 写"随机分为训练集和测试集"，未提及按时间切分
- 预测任务是时序预测（如"预测 ICU 患者未来 24 小时的病情恶化"），但切分方式不考虑时间

**触发条件**：
- 明确存在训练窗口与测试窗口的时间重叠，或训练特征包含预测时点之后的信息；
- 仅“时间序列数据 + 随机切分”且未说明时间策略时，触发 `data_split_not_reported`，不自动判定未来信息泄露。

**Severity**：确认时间/信息泄露为 `critical`；仅切分策略未报告为 `major`。
**Category**：`data_leakage_temporal` / `data_split_not_reported`

**正例**（应报警）：
> Methods: "我们收集了 2020-2023 年的患者电子病历数据，随机选择 70% 用于训练，30% 用于测试。模型预测住院后 48 小时内的再入院风险。"
> ——2023 年的患者可能在训练集，2020 年的患者在测试集，模型训练时已知未来。

**反例**（不应报警）：
> Methods: "我们使用 2020-2022 年数据训练模型，2023 年数据作为时序独立的测试集。"

---

**场景 9：使用滞后特征但未正确对齐时间窗**

**定义**：构造滞后特征（如"过去 7 天平均值"）时，测试集样本的滞后窗口包含了训练集中不应可见的未来数据。

**检测线索**：
- 特征工程包含滑动窗口统计（moving average, lagged features）
- 未明确说明训练集和测试集的时间边界如何处理

**触发条件**：
- 特征窗口跨越训练-测试分割点

**Severity**: `major`  
**Category**: `data_leakage_lagged_features`

---

#### 2.3.5 目标泄露（Target Leakage）

**场景 10：特征包含结局信息**

**定义**：用于预测的特征实际上是结局的代理变量，或在结局发生后才可获得。

**检测线索**：
- 特征中包含"治疗后"、"术后"、"出院时"等明确在结局之后的信息
- 预测死亡风险，但特征包含"ICU 住院天数"（死亡患者的 ICU 天数是已知结局后的信息）
- 预测疾病诊断，但特征包含"诊断后的实验室指标"

**触发条件**：
- 特征的时间属性晚于或等于预测目标的时间属性
- 特征在实际预测场景中不可获得（如用"手术成功与否"预测"术后并发症"）

**Severity**: `critical`  
**Category**: `target_leakage`

**正例**（应报警）：
> Methods: "我们构建模型预测患者 30 天死亡率，特征包括入院时生命体征、实验室指标和住院天数。"
> ——"住院天数"是结局发生后才能完整统计的，死亡患者的住院天数短是结果，不是原因。

**反例**（不应报警）：
> Methods: "我们使用入院后 24 小时内的数据预测 30 天死亡率，确保所有特征在预测时点之前可获得。"

---

#### 2.3.6 交叉验证流水线与层级泄露

除“训练集/测试集”字面切分外，还要检查每个交叉验证折内的完整流水线：插补、批次校正、标准化、特征选择、降维、类别重采样（SMOTE/欠采样）、阈值选择和 early stopping 均只能在训练折拟合；测试折只能执行固定的 transform。多张来自同一患者/切片/视野的 patch、左右眼、连续切片、同一细胞系传代或同一采集站点不得被当作独立样本随机分散。

**触发条件**：明确在全数据或含验证折的数据上拟合上述步骤，或明确同一顶层实体跨折；若仅未报告流水线顺序，立 `data_split_not_reported`（`major`），不直接判定已泄露。

**Severity**：已确认流水线/层级泄露为 `critical`；仅报告不足为 `major`。
**Category**：`data_leakage_pipeline`。

#### 2.3.7 其他常见泄露模式

**场景 11：测试集包含训练集样本的衍生数据**

- 同一患者的左眼和右眼图像分别在训练集和测试集
- 同一组织块的连续切片分散在训练和测试集
- 同一细胞系的不同传代被随机分配

**场景 12：外部数据预处理时使用了本研究的统计信息**

- 声称使用"公开数据集作为外部验证"，但该数据集与训练集合并预处理（如共同归一化）
- 批次效应校正时将测试集作为批次之一，与训练集联合校正

**场景 13：标签泄露**

- 半监督学习中，未标注数据的伪标签基于测试集分布生成
- 主动学习迭代中，每轮从测试集中挑选样本加入训练集（测试集不再独立）

**场景 14：评估指标计算错误导致的"虚假泄露"**

- 虽非真正泄露，但结果不可信：在全数据集上计算类别权重后评估测试集（类别分布已知）
- 使用测试集的类别分布调整分类阈值

场景 11–13 只有在正文、样本 ID、代码或补充材料中存在明确重叠证据时才升级为 `critical`；只有“未说明是否去重/是否保持测试集独立”时，触发 `data_split_not_reported`（`major`）。场景 14 不属于样本泄露，交 M4 作为阈值/指标估计偏倚检查，不在 M2 单独立泄露 finding。

### 2.4 前后一致性

#### 2.4.0 稿件内部数值/单位/方向冲突

对同一 `grouping_key`（实验、组别、时间点、终点、单位）合并 Abstract、正文、表格、图注和补充材料的候选观测。先按单位归一化、分母、舍入和分析人群排除可解释差异；仍无法同时成立时触发 `internal_inconsistency`，并保留所有候选证据。仅有一个来源可读、其他来源不可访问时不得判矛盾。

主要终点、样本流、安全性分母或结论方向冲突为 `major`；次要数值或编辑性冲突为 `minor`。该规则是 `source_value_conflict` signal 的主要消费者，与 M4/M5 的方法或图像判断聚簇，不重复抬高风险。

#### 2.4.1 摘要与正文数值不一致

**定义**：Abstract 中报告的数值（样本量、p 值、效应量、百分比）与 Results 正文或表格中的对应数值不匹配。

**检测策略**：
- M1/Stage 3b 通过 `source_value_conflict` signal 提供候选观测组；M2 必须回查 Abstract、Results、表格和图注的稿件证据
- M2 负责判定不一致的性质与 severity；不得把 `abstract_text_mismatch` 作为未经定义的 evaluation-matrix 字段

**触发条件**：
- 关键数值不一致（样本量、主要终点的 p 值、核心疗效指标）→ `major`
- 次要数值轻微差异（置信区间边界舍入差异 ≤ 0.1 单位，或百分比因分母不同产生的 ≤ 1% 差异）→ `minor`
- 描述性统计的措辞差异但数值相同（Abstract 写"显著降低"，Results 写"下降"）→ 不报警

**Severity**: `major`（关键数值）/ `minor`（次要数值）  
**Category**: `abstract_main_text_inconsistency`

**正例**（应报警）：
> Abstract: "Treatment reduced tumor volume by 65% (p < 0.001, n = 30 per group)."
> Results Table 2: 治疗组 n = 25，对照组 n = 28；肿瘤体积降低 58%（p = 0.003）。

**反例**（不应报警）：
> Abstract: "Treatment reduced tumor volume by 65% (95% CI: 52-78%, p < 0.001)."
> Results: "Tumor volume was reduced by 65.3% (95% CI: 52.1-77.8%, p = 0.0008)."
> ——合理的舍入差异。

---

#### 2.4.2 图表引用完整性

**场景 1：正文引用不存在的图表**

**定义**：Results 或 Discussion 提到"见图 5"或"表 3"，但该图表不存在或编号不连续。

**触发条件**：
- 引用的图表编号在全文图表清单中不存在
- 图表编号跳号（有图 1、2、4，缺图 3）且正文从未引用图 3

**Severity**: `major`（主要发现的图表缺失）/ `minor`（补充图表引用错误）  
**Category**: `missing_figure_reference`

---

**场景 2：孤儿图表（未被正文引用）**

**定义**：某图表在 Results 或 Discussion 中从未被引用，读者无法知道该图的作用。

**触发条件**：
- 图表存在，但全文检索其编号（"Figure 3"、"Fig. 3"、"图 3"）零命中
- 补充材料的图表未在正文中交代

**例外**：
- 纯展示性的图（如 Graphical Abstract、TOC 图）不要求正文引用
- 补充图表在正文中集体引用（"见补充图 S1-S5"）算已引用

**Severity**: `minor`  
**Category**: `orphan_figure`

---

#### 2.4.3 术语与缩写一致性

**场景 1：缩写首次出现未定义**

**定义**：缩写（如 MAPK、IC50、RCT）在 Abstract 或 Introduction 首次出现时未给出全称。

**触发条件**：
- 缩写首次出现的形式为裸缩写，如"我们测定了 MAPK 的表达"
- 应为"mitogen-activated protein kinase (MAPK)"

**例外**：
- 极常见的单位（kg、mL、°C、DNA、RNA、ATP）不要求定义
- 期刊约定俗成的缩写（如临床期刊的 HR、OR、CI）可不定义

**Severity**: `minor`  
**Category**: `abbreviation_undefined`

---

**场景 2：同一概念多种写法**

**定义**：同一生物学实体、药物、实验条件在不同章节用不同术语或拼写，导致读者混淆。

**常见错误**：
- 组名不一致："Vehicle 组" vs "对照组" vs "Placebo 组"（应统一）
- 剂量表述切换："10 mg/kg" vs "10 mg·kg⁻¹"（选一种坚持用）
- 基因/蛋白名称大小写混乱：p53 vs P53 vs p-53（应遵循 HUGO 命名）
- 细胞系名称：HepG2 vs HepG-2 vs Hep G2（应统一为数据库登记名）

**触发条件**：
- M1 的 `evaluation_matrix` 或 key_data 中检测到同一实体的多种拼写
- 正文与图注中组名、时间点或剂量的表述不一致

**Severity**: `minor`  
**Category**: `terminology_inconsistency`

---

#### 2.4.4 时间点与实验流程一致性

**定义**：Methods 描述的实验时间线与 Results 报告的时间点不匹配，或流程图与正文矛盾。

**检测线索**：
- Methods: "小鼠在给药后第 7、14、21 天处死"
- Results Figure 2: 展示第 3、7、10、14 天的数据（10 天在 Methods 中未提及）
- CONSORT 流程图显示"200 名患者随机化"，但 Results Table 1 显示基线 n = 195

**触发条件**：
- 时间点、样本量、分组数在不同章节/图表间不可调和
- 流程图的数字与正文 n 值不一致且未解释（如排除标准变更）

**Severity**: `major`（影响可重复性）  
**Category**: `timeline_inconsistency`

---

#### 2.4.5 统计方法与报告结果的匹配性

**定义**：Methods 声称使用某统计检验，但 Results 报告的统计量与该检验不匹配。

**常见不匹配**：
- Methods 说"Student's t-test"，Results 报告"χ² = 5.3, p = 0.02"（χ² 是卡方检验）
- Methods 说"非参数 Mann-Whitney U 检验"，Results 报告均值±标准差与 t 值（应报中位数与 U 值）
- Methods 说"单因素方差分析"，Results 只报告两组间 p 值（ANOVA 应给 F 值）
- Methods 未提及多重比较校正，但 Results 有 Bonferroni 校正后的 p 值

**触发条件**：
- 统计量类型（t / F / χ² / U / H）与 Methods 声称的检验不对应
- Methods 未声明的后处理（如多重比较校正、协变量调整）出现在 Results

**Severity**: `major`  
**Category**: `statistical_method_mismatch`

**注**：此条与 M4（统计学模块）有交集。**职责划分**：
- M2 检测"Methods 说 A、Results 报告 B"的**形式矛盾**
- M4 检测"该场景应该用 C 而非 A"的**方法学错误**

---

#### 2.4.6 引用编号连续性

**定义**：参考文献编号不连续（如出现 [1, 2, 5, 7]，缺 3、4、6），或正文引用编号超出文献列表范围。

**触发条件**：
- References 列表有 50 条，但正文出现 [52]
- 引用编号序列有缺失且无明显理由（如删除了某些引用但未重新编号）

**Severity**: `minor`  
**Category**: `reference_numbering_error`

仅对已识别为数字顺序制（如 Vancouver）的稿件执行；作者–年份、脚注制或期刊自定义引用不得套用连续编号规则。

## 3. category slug（完整版）

| slug | 说明 | severity | 对应章节 |
| --- | --- | --- | --- |
| `missing_section` | 适用且必需的章节缺失 | major / critical | §2.1.1；Methods/Results/授权缺失仅在确实适用且阻断解释时升级 |
| `incomplete_abstract` | 结构化摘要要素不完整 | minor | §2.1.2 |
| `missing_reporting_guideline_element` | 缺失报告规范核心要素（如 CONSORT 流程图） | major / critical | §2.1.3 |
| `objective_drift` | 研究目标在结果中未被回答 | major | §2.2.1 |
| `orphan_results` | 实验结果无动机或无解读 | major / minor | §2.2.2 |
| `conclusion_overreach` | 结论跃迁（形式逻辑断裂） | major | §2.2.3 |
| `circular_reasoning` | 循环论证 | major | §2.2.4 |
| `selective_reporting` | 选择性报告或预设终点未报告 | critical / major | §2.2.5 |
| `endpoint_switching` | 主要终点、时间点或分析人群发生未解释变化 | major / critical | §2.2.5 |
| `analysis_population_mismatch` | ITT/PP/安全性或主要分析人群前后不一致 | major | §2.2.5 |
| `participant_flow_inconsistency` | 筛选、随机化、失访、排除与分析分母无法闭合 | major / minor | §2.2.6 |
| `internal_inconsistency` | 同一观测在正文、表格、图注或补充材料间冲突 | major / minor | §2.4.0 |
| `data_leakage_sample_overlap` | 训练-测试集样本重复 | critical | §2.3.1 |
| `data_split_not_reported` | 未报告患者/样本/站点/时间层级的独立切分 | major | §2.3.1、§2.3.4、§2.3.6 |
| `data_leakage_augmentation` | 数据增强后未正确切分 | critical | §2.3.1 |
| `data_leakage_normalization` | 归一化/标准化在切分前 | major | §2.3.2 |
| `data_leakage_feature_selection` | 特征选择使用全部数据 | critical | §2.3.2 |
| `data_leakage_dimensionality_reduction` | 降维在全数据上拟合 | major | §2.3.2 |
| `data_leakage_model_selection` | 用测试集选择模型或调超参 | critical | §2.3.3 |
| `data_leakage_test_set_reuse` | 测试集被多次迭代使用 | major | §2.3.3 |
| `data_leakage_temporal` | 时间边界/预测时点泄露 | critical / major | §2.3.4 |
| `data_leakage_lagged_features` | 滞后特征窗口未正确对齐 | major | §2.3.4 |
| `target_leakage` | 特征包含结局信息 | critical | §2.3.5 |
| `data_leakage_pipeline` | 交叉验证流水线或层级实体跨折泄露 | critical / major | §2.3.6 |
| `data_leakage_derived_samples` | 衍生数据跨训练-测试集 | critical / major | §2.3.7 场景11 |
| `data_leakage_joint_preprocessing` | 训练集与测试集联合预处理 | major | §2.3.7 场景12 |
| `data_leakage_label` | 标签泄露（半监督/主动学习） | critical | §2.3.7 场景13 |
| `abstract_main_text_inconsistency` | 摘要与正文数值不一致 | major / minor | §2.4.1 |
| `missing_figure_reference` | 引用不存在的图表 | major / minor | §2.4.2 |
| `orphan_figure` | 图表未被正文引用 | minor | §2.4.2 |
| `abbreviation_undefined` | 缩写首次出现未定义 | minor | §2.4.3 |
| `terminology_inconsistency` | 术语不统一 | minor | §2.4.3 |
| `timeline_inconsistency` | 时间点/流程不一致 | major | §2.4.4 |
| `statistical_method_mismatch` | 统计方法与报告结果不匹配 | major | §2.4.5 |
| `reference_numbering_error` | 参考文献编号错误 | minor | §2.4.6 |

## 3.1 接住 X1 外部核验的 signal（**待卓妍确认 severity**）

`scripts/external_figure_validation.py`（Stage 3c）已交付，把下列 `check_type`
路由给 M2。它们是 `external_validation_candidate`，**没有 severity** ——
X1 只做「稿件事实 vs 外部权威事实」的可复算比较，是否成立由 M2 回查稿件后决定。

| X1 `check_type` | 数据库 | 比较结果 | 建议 M2 category |
| --- | --- | --- | --- |
| `cited_work_retracted` | Europe PMC | `mismatch` | `cites_retracted_work` |
| `reference_doi_resolves` | Crossref | `mismatch` | `reference_not_resolvable` |
| `gene_symbol_excel_corruption` | HGNC | `mismatch` | `gene_symbol_data_corruption` |
| `gene_symbol_outdated` | HGNC | `mismatch` | `gene_symbol_outdated` |
| `gene_symbol_unrecognized` | HGNC | `needs_manual_review` | `gene_symbol_unrecognized` |
| `variant_position_range` / `variant_reference_residue` | UniProt | `mismatch` | `variant_inconsistent_with_reference` |

**判据要点**

- `cited_work_retracted`：**引用已撤稿文献本身不一定是错误。** 论文讨论撤稿事件本身、
  或已写明该文献已撤稿，都是做对了，**不得立 finding**。只有当该文献被当作
  立论依据、且论文未提及其撤稿状态时才立；支撑主要结论时取 `critical`。
- `reference_doi_resolves`：格式完美但无法解析的 DOI 是幻觉引文与纸厂引文的典型特征。
  须先排除排版错误（多余空格、全角字符）再定性。
- `gene_symbol_excel_corruption`：符号被 Excel 转成日期（`2-Sep`、`1-Mar`）。
  这是**数据处理污染**的信号，须提示作者回原始数据核对该列究竟是哪个基因。
- `gene_symbol_outdated`：旧符号本身不算错误，但与现行文献比对时易张冠李戴，取 `minor`。

`statistical_forensics.py` 另把 `count_percentage_mismatch` 与 `table_total_mismatch`
同时路由给 M2（数值本身归 M4，**表格与正文数据不一致**归 M2 的完整性范畴）。

---

## 4. TODO（一期）

### 4.1 已完成
- [x] 填充 §2.1 刊型-必备章节对照表（含 5 种刊型 × 13 类章节）
- [x] 填充 §2.1 结构化摘要要素与方法学报告清单
- [x] 填充 §2.2 逻辑链闭环四类断裂的详细判定标准
- [x] 填充 §2.3 数据泄露场景库（14 个场景，覆盖 6 大类）
- [x] 填充 §2.4 前后一致性检查（6 个子场景）
- [x] 完成 category slug 表（核心规则与二期规则均登记；当前共 39 个 slug，需由 categories.json/validator 交叉核对）

### 4.2 与 M1 的集成要求（一期必需）
- [x] `evaluation_matrix.has_ml_model` / `has_split_strategy` 已由 M1 定义；M2 仅用其路由，不将布尔值直接当 finding 证据。
- [ ] M1/Stage 3b 应提供 `source_value_conflict` 的观测组与 `evidence_refs`；不再新增未经 schema/契约定义的 `evaluation_matrix.abstract_text_mismatch`。
- [ ] M2 应直接消费 `article_design.primary_design` 与 `design_components[]`，不再用 Methods 长度或 PRISMA 图存在性启发式猜测 `study_type`。
- [ ] M1 应为每个 prediction/benchmark 组件抽取 split unit、split strategy、validation protocol、preprocessing order、external validation 与 dataset/site/time metadata，供 §2.3 逐场景判定。

- [ ] **M1 应提供**：术语/缩写的多种拼写候选（可选增强）
  - 辅助 §2.4.3 术语一致性检查
  - 若 M1 未实现，M2 在 key_data 与图注中自行检测常见变体（p53/P53、HepG2/HepG-2 等）

### 4.3 待测试回归（一期必需）
- [ ] 用 `datasets/rct_clinical` 测试 §2.1（CONSORT 清单）与 §2.2.1（目标漂移）
- [ ] 用 `datasets/small_sample_pilot` 测试 §2.2.3（结论跃迁）
- [ ] 用 `datasets/animal_invivo` 测试 §2.1（伦理声明必备性）与 §2.4.4（时间线一致性）
- [ ] 模拟 ML 数据泄露论文，测试 §2.3 的 14 个场景触发（需自行构造或从其他数据源补充）
- [ ] 用 `datasets/meta_analysis` 测试 §2.1（PRISMA 流程图）与 §2.4.2（图表引用完整性）
- [ ] 为每条 critical/major 规则增加 confirmed / not-reported / inaccessible / false-positive 四类回归样例；至少覆盖患者级、切片级、站点级和时间级 ML 切分。
- [ ] 增加混合设计（体外+动物+人体）、非结构化摘要、合并 Discussion/Conclusion、作者-年份引用格式和无补充材料权限的回归样例。

### 4.4 与其他模块边界确认（一期必需）
- [ ] **M2 vs M7 边界**（§2.2.3）：
  - M2 负责：形式逻辑跃迁（体外→人类、单指标→全面调控，实验根本未做但结论提到）
  - M7 负责：证据强度不足（实验做了但层级低、因果链弱、外推不当）
  - 灰色地带判定规则：若 Results 中有任何相关实验，交给 M7；若 Results 完全无对应数据，归 M2

- [ ] **M2 vs M4 边界**（§2.4.5）：
  - M2 负责：Methods 说 A、Results 报 B 的**形式矛盾**（统计量类型不匹配）
  - M4 负责：Methods 说 A、但该场景应该用 C 的**方法学错误**（检验选择不当）
  - 示例：Methods 说"t-test"、Results 报"χ²" → M2 报矛盾；Methods 说"t-test"但数据非正态 → M4 报方法错

### 4.5 二期扩展（本期不实现）
见 §5（引用与重复度核验），已列出规则骨架，待二期实现时补充连接器与缓存策略。

## 5. 二期扩展：引用与重复度核验（本期不实现，规则先写下）

### 5.1 引用真实性

**依赖**：外部数据源 Crossref / PubMed API（通过 X1 外部验证层调用）

#### 5.1.1 撤稿引用检测（二期优先级最高）

**定义**：论文引用了已被期刊撤回（retracted）的文献，且将其作为有效证据支持自己的结论。

**检测策略**：
1. M1 提取 References 列表中的全部 DOI 或 PMID
2. X1 向 Crossref / PubMed / Retraction Watch Database 查询每个标识符的状态
3. 对标记为 `retracted`、`withdrawn`、`expression of concern` 的文献，检查正文中的引用上下文
4. 若该撤稿文献被用于支持核心方法学、主要结果或结论，触发 critical finding

**触发条件**：
- 引用文献的官方状态为 `retracted` 或 `withdrawn`
- 该引用在正文中被用于方法学依据、结果对比或结论支撑（非仅列在 References 中未被引用）
- 撤稿日期早于本稿件的投稿日期（排除同期撤稿的边缘情况）

**Severity**: `critical`（核心引用）/ `major`（次要引用）  
**Category**: `cites_retracted_work`

**正例**（应报警）：
> 某论文在 Methods 中写："我们采用 Smith et al. (2018) 的方法进行基因表达分析。"
> X1 查询发现：Smith et al. (2018, DOI: 10.1234/example) 于 2020 年因数据造假被撤稿。
> 本稿件投稿时间：2022 年。

**反例**（不应报警）：
> 引用列表包含一篇撤稿文献，但正文从未引用该文献（孤立文献条目，可能是作者疏忽未删除）。

---

#### 5.1.2 引用不存在检测

**定义**：正文中引用了某文献，但该 DOI/PMID 在数据库中查询不到。

**检测策略**：
- X1 查询返回 404 或明确零记录
- 排除数据库暂时不可用、网络超时等情况（这些记为 `system_limitation`）

**触发条件**：
- DOI/PMID 格式合法
- Crossref/PubMed 返回权威 404
- 该标识符在正文中被明确引用

**Severity**: `major`  
**Category**: `citation_not_found`

---

#### 5.1.3 引用失真检测（二期挑战性高，可选）

**定义**：正文对某文献的引用内容与该文献的实际结论不符。

**检测策略**：
1. 提取正文中引用该文献时的陈述（如"Zhang et al. 报告化合物 X 显著抑制肿瘤生长"）
2. X1 获取被引文献的摘要或全文结论
3. 用语义比对判断是否一致

**挑战**：
- 需要深度语义理解，假阳性风险高
- 被引文献可能有多个结论，引用者选择其一未必失真
- 二期若实现，需要高置信度阈值 + 人工复核建议

**Severity**: `major`（若实现）  
**Category**: `citation_misrepresented`

---

### 5.2 文本重复度

**依赖**：文献全文库或第三方查重服务（iThenticate / Turnitin API）

**风险与边界**：
- 方法学描述天然高度雷同（如"Western blot 按标准流程操作"），直接按相似度报警会产生大量假阳性
- 同一作者的合理自我复用（如同一实验室的多篇论文复用相同的动物模型描述）不应报警
- 二期需实现**段落级分类**：Methods 段落容忍高相似度，Results/Discussion 段落严格检查

#### 5.2.1 实质性文本重复

**定义**：Results 或 Discussion 的连续段落与已发表文献高度重复（≥ 80% 相似度，≥ 150 字），且未标注引用或明确说明复用。

**触发条件**：
- 重复段落在 Results、Discussion 或 Introduction 的核心论述部分
- 相似度 ≥ 80% 且连续匹配长度 ≥ 150 字
- 被匹配文献非本稿作者的既往论文（自我复用单独判定）

**Severity**: `major`  
**Category**: `text_overlap`

---

#### 5.2.2 方法段落合理复用（不报警）

**例外场景**：
- Methods 中标准操作的逐字复用（如试剂目录号、仪器型号、统计软件版本）
- 同一作者在多篇论文中复用相同的实验流程描述，且在首次发表时已详细说明
- 伦理声明、数据可用性声明等格式化段落的复用

---

### 5.3 二期新增 category

| slug | 说明 | severity |
| --- | --- | --- |
| `cites_retracted_work` | 引用已撤稿文献 | critical |
| `citation_not_found` | 引用文献不存在 | major |
| `citation_misrepresented` | 引用内容与原文结论不符 | major |
| `text_overlap` | 与已发表文献重复（非方法段） | major |

---

### 5.4 二期实现优先级

1. **撤稿引用检测**（最高）—— 判定确定、无歧义、后果严重，且现有大模型普遍查不出来
2. **引用不存在检测**（高）—— 技术实现简单，价值明确
3. **方法段落分类 + 结果段落查重**（中）—— 需要段落分类器，避免假阳性
4. **引用失真检测**（低）—— 语义理解难度大，二期末期或三期考虑
