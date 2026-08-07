# M2 · 宏观逻辑与格式完整性

核心问题：抛开生物学专业性，这篇论文作为一篇论文，研究问题、设计、样本、方法承诺、分析、结果和结论是否形成可审计的闭环，各部分是否完整且前后一致？

判断稿件内部的形式逻辑和报告闭合，不判断生物学机制是否正确，也不把“未报告”自动解释为“未实施”。

---

## 1. 职责边界

### 1.1 M2 负责

- 适用章节和声明是否存在，核心信息是否可定位；
- Objective、Methods、Results、表图、Discussion 和 Conclusion 是否互相承接；
- 人群、样本、实验材料、分组、时间线和分析分母能否闭合；
- Methods 明确承诺的关键测量或分析是否在 Results 中得到交代；
- 研究设计、抽样方式、分析描述和主张类型是否形成同一套可执行契约；
- 摘要、正文、表格、图注和补充材料中的同一数值、单位、方向、组名是否一致；
- ML/预测模型中可由稿件内部流程确认的数据泄漏或切分报告缺口；
- X1 已生成的参考文献和标识符外部核验候选是否能由稿件上下文成立。

### 1.2 转交而不越界

| 问题 | 主模块 | M2 的处理 |
| --- | --- | --- |
| 实验条件、试剂、重复数、动物或组学方法是否符合领域惯例 | M3 | 只在 Methods 与 Results 自相矛盾时保留 M2 finding；方法不足转 M3 |
| 检验选择、模型估计、多重比较、样本量是否统计合理 | M4 | M2 只判断“Methods 说 A、Results 报 B”或关键分析说明缺失 |
| 图像质量、重复、裁剪和图表表达 | M5 | M2 只判断图表是否存在、被引用、与正文数值或方向是否一致 |
| 伦理审批、同意、注册或动物授权是否合规 | M6 | M2 只做适用性与声明存在性路由，不代替伦理判定 |
| 因果强度、证据等级、外推和临床建议是否过度 | M7 | M2 仅处理“结论对象在研究中根本未测”的形式跳跃，其余生成 M7 候选 |

同一问题只能选一个最能表达根因的 primary category。不得输出“category A / category B”。如同时涉及其他模块或次级现象，写入 related_categories 或 suggested_modules，由 Layer 4 合并。

---

## 2. 输入与证据门控

### 2.1 输入

- structured_result_v2，重点使用 article_design.primary_design、design_components、objective、claims、key_data、gaps 和 evidence_refs；
- 跨节包、参考文献包、声明包及轻量全局上下文；
- 正文分节、表图清单和可访问补充材料；
- 确定性工具或 X1 候选；候选和 signal 不能直接当 finding。

若 structured_result 仍含 unresolved，先交回 M1 解析，不自行猜测关键字段。

### 2.2 稿件来源过滤

只有作者稿件内容可以证明“论文报告了什么”：

- 接受：JATS article 的 front、body、back，正文直接链接且可访问的 supplement，以及 PDF 中属于论文的正文、表图、声明和参考文献；
- 默认排除：sub-article、response、decision letter、peer-review、reviewer report、editor report、author response、acceptance letter、production query、correction request，以及其嵌套内容；
- 只有研究对象本身是审稿材料，或用户明确要求分析审稿过程时，才把这些来源纳入证据；
- 编辑或审稿人要求作者增加某内容，只能证明“有人提出过要求”，不能证明正文已经包含或缺少该内容；
- 作者回复声称“已修改”时，仍必须回到最终正文定位修改结果。

解析 JATS 时先按 XML 元素边界过滤，不得仅把整个 XML 转为纯文本后全文搜索。若解析器无法区分正文与审稿附件，登记 system_limitation，不对受影响的缺失或矛盾作高置信度判断。

### 2.3 缺失与不可访问

“未报告”必须有 absence 证据：

1. 说明适用的研究组件；
2. 列出检索范围，包括正文、表格、图注、声明及可访问补充材料；
3. 列出概念及同义检索词；
4. 记录零命中或只命中无关来源；
5. 排除合并章节、替代标题和交叉引用。

来源不可读、补充材料不可访问、注册页面不可达或解析失败时，只能登记 system_limitation。不得把系统能力限制算作论文缺陷。

### 2.4 置信度

- confirmed：稿件中的正向证据或可审计的 absence 证据足以支持；
- likely：多处线索一致，但仍缺一项关键定位；
- uncertain：设计分类、来源归属或文本含义存在歧义。

likely 或 uncertain 的 review_confidence 最高为 medium。单个 extraction signal、目录名、文件夹名或数据集 slot 名不能决定研究设计。

---

## 3. 先按研究组件路由

先识别 design_components，再逐组件审查，最后检查组件间如何汇合到总目标和总论断。混合研究不得压成单一 study_type，也不得共用一个不加说明的分母。

| 组件 | M2 最小闭环 |
| --- | --- |
| RCT/干预研究 | 招募 → 随机化/分配 → 干预 → 随访 → 分析人群 → 预设终点 → 结果 |
| 队列/横断面/病例对照 | 源人群 → 纳排/抽样/匹配 → 暴露与结局 → 分母 → 分析 → 关联主张 |
| 诊断研究 | 入组 → 指标检测 → 参考标准 → 可判定样本 → 诊断指标 |
| 系统综述/aggregate meta | 问题框架 → 检索 → 筛选 → 纳入研究 → 合成 → 结论 |
| IPD meta-analysis | 队列识别 → IPD 获得/协调 → 个体纳排 → 各队列与总分母 → 一阶段或二阶段分析 → 合成 |
| Scoping/rapid review | 范围问题 → 检索来源 → 筛选/图表化 → 证据地图；不强制套用效应量 meta 要求 |
| 公共数据库二次分析 | 数据库/版本/时间窗 → 变量定义 → 纳排 → 最终队列 → 分析 → 数据库人群内结论 |
| 动物/实验室/组学/in-silico | 材料或数据来源 → 组别/处理 → 明确测量 → 分析产物 → 对应结果 |
| ML/预测模型 | 样本与标签 → 切分单元 → 折内预处理/选择 → 训练与调参 → 独立评估 → 性能主张 |
| 混合研究 | 每个组件各自闭合，并明确组件间接口；一个组件的结果不得冒充另一个组件的验证 |

路由护栏：

- IPD meta-analysis 不是普通 aggregate meta，不得仅因未见传统 forest plot、汇总效应或统一 PRISMA 要素而报警；
- rapid/scoping review 与 pilot study 并存时，分别建立检索筛选账和参与者流程账；
- 公共、去标识数据库研究不因未见逐例知情同意自动报警，转 M6 按数据库政策和豁免语境判断；
- 纯 in-silico 研究不适用人体同意或动物审批；
- 动物、实验和计算组件的方法参数是否充分由 M3/M4 判断，M2 不运行 Western blot、流式、IHC、RNA-seq、毒理或剂量点数的硬阈值清单；
- 无 ML/预测组件时，在 coverage 中只记一次 not_applicable，不逐条枚举所有泄漏类型。

---

## 4. 强制的四张对账表

不得从缩写、章节小标题或格式清单开始。第一遍先建以下四张轻量 ledger；预算不足时优先保留 ledger 和 critical/major finding。

### 4.1 人群、材料与分母账

按组件记录：

| 阶段 | 对象/来源 | 纳入或选择规则 | n | 排除/缺失 | 下游用途 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| 源集合 |  |  |  |  |  |  |
| 筛查/质控 |  |  |  |  |  |  |
| 分组/匹配/验证 |  |  |  |  |  |  |
| 最终分析 |  |  |  |  |  |  |

人体研究追踪筛查、诊断验证、随机化、失访和分析集；实验研究追踪样本/动物/切片/细胞或数据集及其层级；综述追踪记录、全文、研究、队列和个体，不能混用这些分母。

### 4.2 Methods→Results 承诺账

提取 Methods 中已完成式承诺，如 was measured、was assessed、was performed、was determined、we evaluated、variables entered into the model。为每项记录：

- 对象、时间点和分析层级；
- 与主要目标、分组、主要结论或安全性的关系；
- Results、表图或补充材料的对应位置；
- 若未报告，是否明确解释取消、缺失或质控失败。

宽泛的“可收集变量”列表不等于承诺全部报告；只有明确完成且关系到目标、分组、解释或主张的项目才进入核心账。

### 4.3 分析→主张账

把主张映射到实际结果和分析层级：

| 主张类型 | 必须定位的稿件内部接口 |
| --- | --- |
| frequency/prevalence/incidence | 源人群、观察窗、分子和分母是否来自同一抽样框 |
| associated factor | 对应比较或模型、效应方向与人群 |
| independent predictor | 调整模型存在，变量与调整层级可识别 |
| diagnostic performance | 指标检测、参考标准和同一可判定样本 |
| causes/reduces/improves | 是否有对应干预/时间顺序；证据强度交 M7 |
| safe/effective | 对应疗效和安全性终点是否实际测量并报告 |

### 4.4 跨来源数值账

对主要样本量、分母、终点、效应量、P 值、CI、单位、时间点和方向，合并 Abstract、Results、表格、图注及补充材料候选值。先检查：

- 是否属于不同分析人群、时间点或单位；
- 是否只是合理舍入；
- 百分比是否使用不同但已说明的分母；
- 表中总体值是否能由互斥分组值合理推出；
- 点估计是否落在其置信区间内。

无法解释的候选冲突才进入 finding。

---

## 5. 主链规则

### 5.1 目标未闭合

Category：objective_drift

当 Abstract/Introduction 明确提出的主要目标或假设，在 Results、表图和可访问补充材料中没有对应测量或分析时成立。

不成立：

- 结果存在但证据强弱存疑，转 M7；
- 次要背景问题没有单独结果；
- 合理修改目标且稿件已说明原因。

Severity：

- major：一个主要目标完全未回答；
- critical：唯一主要目标完全没有结果，导致论文核心不可解释；
- minor：明确列出的次要探索目标未交代。

### 5.2 Methods 承诺未交代

Category：methods_results_gap

Methods 明确声称已完成的关键测量、终点、敏感性分析、模型、分组验证或安全性评估，在任何 Results 来源中均无结果，也未说明原因。

正例：Methods 写明已按 GOLD 判定严重度并完成肺功能检测，Results 完全不报告分级、肺功能或缺失原因，而这些信息关系到研究人群和主要风险主张。

反例：Methods 说明收集既往用药，Results 明确报告完整度不足并在 supplement 给出可用分布。

Severity：

- critical：主要终点或唯一核心验证完全缺失，结论无从解释；
- major：关键分组、主要安全性、核心协变量或预先说明分析缺失；
- minor：不改变主要推断的次要探索承诺缺失。

### 5.3 结果成为孤岛

Category：orphan_results

Material orphan result 是 Results 中足以改变论文主题或支撑主要结论的数据块，却在研究目标/Methods 中没有来源、动机或分析计划。仅仅 Discussion 未逐项复述结果不构成 major finding。

- major：突然出现的新人群、实验组件、主要终点或分析，且被用于核心结论；
- minor：次要结果未被解释，影响可读性但不改变主链。

### 5.4 设计→抽样→分析→主张断裂

Category：design_analysis_disconnect

在稿件自身描述中，研究设计、样本形成、验证路径、分析或主张无法同时成立。例如：

- 一方面称 census/连续纳入全部患者，另一方面从更大源人群按固定比例选择病例或对照，却没有给出源人群；
- 用病例-对照式或匹配式分析样本直接计算人群 frequency/prevalence；
- 诊断结果只在高度怀疑者中验证，却把其分母表述为全部人群；
- matched/paired/clustered/repeated 设计没有说明分析如何承接该结构；
- 一个混合研究组件的样本或结果被当作另一个组件的验证；
- IPD meta 把队列数、个体数和分析可用个体混为同一分母。

如果设计链完整，只是统计方法可能不合适，转 M4。若主要问题是调整模型关键字段未报告，可选 analysis_reporting_gap 作为 primary category，不再同时立 design_analysis_disconnect。

### 5.5 参与者流、样本流或分母不闭合

Category：participant_flow_inconsistency

筛查、纳入、分组、匹配、验证、排除、失访与最终分析人数不能通过稿件说明互相换算，或同一终点在正文和表图使用无法解释的分母。

- major：影响主要终点、频率、安全性或主要分析人群；
- minor：次要表格的一处编辑性分母差异；
- critical：无法确定任何核心结果来自哪一分析集。

分析集定义清楚但采用何种统计策略是否正确，转 M4。

### 5.6 终点、时间点与分析人群发生未解释变化

Primary categories 按根因三选一：

- endpoint_switching：主要/次要终点或时间点发生未解释变化；
- analysis_population_mismatch：ITT、PP、安全性集或其他分析人群前后不一致；
- selective_reporting：预设的一组分析只报告有利部分，且有正向证据表明其余分析存在。

注册或方案可得时与稿件对账；不可访问时登记 system_limitation。不能仅因某常见结局未出现而推断选择性报告。

核心终点被替换、隐匿或选择性报告可为 critical；次要终点或分析集说明不足通常为 major。

### 5.7 内部数值、单位、方向和时间线冲突

Primary category：internal_inconsistency

同一 grouping key 下的观测在 Abstract、正文、表格、图注或 supplement 中无法同时成立。grouping key 至少包含研究组件、分析人群/材料、组别、时间点、终点和单位。

以下更具体 category 只在其能准确表达根因时替代 internal_inconsistency：

- abstract_main_text_inconsistency；
- timeline_inconsistency；
- statistical_method_mismatch，仅限 Methods 声称的检验与 Results 实际报告的统计量形式矛盾。

同一根因造成的多处冲突聚成一条 finding，列出全部证据，不按每个表格单元重复计数。数值是否统计合理交 M4；正文与表格说法不一致归 M2。

### 5.8 窄义循环论证

Category：circular_reasoning

仅在待证明结论直接决定关键样本选择、标签、分组或评价规则，随后同一规则又被用来证明该结论时成立。例如先按“对药物敏感”选择对象，再用这些对象证明药物有效。

以下不自动成立：

- 常规疾病模型选择；
- Discussion 对结果作机制解释；
- 事后亚组已明确标为 exploratory。

### 5.9 形式层面的结论跳跃与 M7 转交

Category：conclusion_overreach 仅用于研究中根本没有对应对象或层级的形式跳跃，例如：

- 只有体外数据，却直接声称已改善患者临床结局；
- 只有动物数据，却声称已在人群中证实疗效；
- 只测一个指标，却声称完整验证了多个未测通路；
- 没有任何安全性测量，却宣称安全。

只要存在相关实验或分析，但因设计、样本量、混杂、替代终点或证据层级而可能不足，M2 不立此 finding，而是生成 possible_unsupported_claim 或 possible_causal_overreach 候选给 M7，附 claim 原文、locator、设计和实际结果。

### 5.10 ML/预测模型接口

仅当 design_components 含 ML、预测、分类、风险评分或 benchmark 时运行。检查六个接口：

1. 样本/患者/切片/站点/时间等独立切分单元；
2. 同一实体或衍生样本是否跨训练、验证和测试集合；
3. 归一化、插补、特征选择和降维是否只在训练数据/训练折拟合；
4. 调参与模型选择是否与最终测试集隔离；
5. 特征是否包含预测时点之后的信息或标签派生信息；
6. 外部验证是否真正独立于开发数据和开发决策。

判定层级：

- 有明确重叠、全数据拟合、测试集调参或未来/标签信息证据：按具体 data_leakage_* category 立 finding，major 或 critical 取决于是否污染主要性能；
- 只是不报告切分单元、预处理顺序或独立性：data_split_not_reported，通常 major，不能写成“已发生泄漏”；
- 代码、supplement 或数据不可访问：system_limitation；
- 无 ML 组件：coverage 中一行 not_applicable。

---

## 6. 结构与编辑完整性

主链检查完成后再运行本节。章节以信息功能而非标题字面判断；合并的 Results and Discussion 或 Discussion 中的 Conclusion 视为存在。

### 6.1 核心结构

| 稿件组件 | 通常需要的信息 | 判定护栏 |
| --- | --- | --- |
| Abstract | 目标、设计/材料、主要结果、结论 | 非结构化摘要不因缺小标题报警 |
| Introduction | 问题、缺口、目标 | 背景长短不等于完整性 |
| Methods | 设计、对象、流程、测量、分析 | 具体领域参数转 M3/M4 |
| Results | 对应主要目标的结果 | 综述类按其文章类型解释 |
| Discussion/Conclusion | 解释、局限、对目标的回答 | 可合并，不强制独立 Conclusion |
| Funding/COI | 声明或明确无 | 依期刊和稿件类型判断 |
| Data availability | 声明或访问路径 | 未给期刊/资助政策时只记待确认，不自动 finding |
| References | 正文引用与条目可对应 | 引用真实性依赖 X1 |

missing_section 只在该组件确实适用、全文 absence 检索完成且信息功能也不存在时使用。Methods 或 Results 的实质性缺失可为 critical；影响解释的 Introduction/Discussion 缺失通常 major；期刊依赖或编辑性声明通常 minor 或待确认。

人体/动物伦理、同意和注册的适用性由 M6 最终判定。公共去标识数据库、公开组学数据、纯 in-silico、综述和 meta-analysis 不得套用原始人体研究的同意要求。

### 6.2 摘要

incomplete_abstract 用于摘要缺少目标、基本设计/材料、主要结果或结论信息。缺少结构化小标题本身不是 finding。摘要遗漏主要数值可按影响取 minor/major；摘要与正文冲突使用 abstract_main_text_inconsistency。

### 6.3 图表、术语和引用

- missing_figure_reference：正文引用的图表不存在；主要结果依赖该图表时 major，否则 minor；
- orphan_figure：图表未被正文或集体补充材料引用，通常 minor；
- terminology_inconsistency：组别、终点、材料或实体名称变化造成实际映射歧义；纯风格差异不报警；
- abbreviation_undefined：首次出现的非通行缩写未定义，minor；
- reference_numbering_error：仅对已确认的数字顺序制运行；作者-年份制不检查连续编号。

上述编辑项合并输出，不得挤占 critical/major 逻辑问题。

### 6.4 报告规范

CONSORT、STROBE、STARD、PRISMA、PRISMA-IPD、PRISMA-ScR、ARRIVE、TRIPOD 等只用于识别“当前组件可能缺少哪个接口”，不是统一严重度表。

missing_reporting_guideline_element 必须同时满足：

1. 已确认规范和版本适用于该具体研究组件；
2. 缺失条目是必需而非建议项；
3. 已完成 absence 检索；
4. finding 说明该缺失如何影响流程、分母、主要终点解释或可复核性。

严重度按实际影响决定。不得把任何 CONSORT/PRISMA/ARRIVE 条目缺失一律标为 critical；也不得用规范清单替代 M3、M4 或 M6 的专业判断。

---

## 7. 外部核验候选

M2 只消费 X1 已生成的 external_validation_candidate，不自行声称联网核验成功。

| X1 check_type | M2 primary category | 成立条件 |
| --- | --- | --- |
| `cited_work_retracted` | cites_retracted_work | 被撤稿文献被当作有效依据，稿件未说明撤稿状态 |
| `reference_doi_resolves` | reference_not_resolvable | 权威源明确无法解析，且已排除排版错误 |
| `gene_symbol_excel_corruption` | gene_symbol_data_corruption | 日期化符号出现在实际数据或结果中 |
| `gene_symbol_outdated` | gene_symbol_outdated | 旧符号造成实体映射风险；通常 minor |
| `gene_symbol_unrecognized` | gene_symbol_unrecognized | 权威源无法识别且人工语境复核仍存疑 |
| `variant_position_range` | variant_inconsistent_with_reference | 稿件物种、转录本/蛋白版本一致后，位置仍超出范围 |
| `variant_reference_residue` | variant_inconsistent_with_reference | 稿件物种、转录本/蛋白版本一致后，参考残基仍冲突 |

引用撤稿论文讨论撤稿事件本身不是错误。外部服务超时或无权限只登记 system_limitation。

确定性工具的 count_percentage_mismatch 和 table_total_mismatch 可作为候选；M2 回查稿件后，以 internal_inconsistency 或 participant_flow_inconsistency 定性。

---

## 8. Severity 与去重

Severity 由对论文主链的实际影响决定，不由规则名称或报告指南名称决定：

- critical：唯一核心目标/主要结果不可解释，核心分析集无法识别，或有明确的数据完整性污染使主要性能无效；
- major：主要目标、分母、流程、关键承诺、主要数值或分析→主张接口明显断裂，需要实质性补充或重分析；
- minor：编辑性、局部说明或次要结果缺口，不改变当前核心推断。

去噪规则：

1. 同一根因只立一条 finding；
2. 每条 finding 只用一个 primary category；
3. “未发现”和 not_applicable 放入紧凑 coverage 表，不写成长段；
4. absence、inaccessible 和 confirmed leakage 必须明确区分；
5. finding 数量不是目标，优先保留最先阻断主要结论的断点。

---

## 9. 输出要求

### 9.1 审查顺序

1. 过滤非稿件来源；
2. 识别所有 design_components；
3. 建四张 ledger；
4. 做 critical/major 主链检查；
5. 路由 M3/M4/M5/M6/M7 候选；
6. 最后做 minor 结构和编辑检查；
7. 对候选去重并绑定 evidence_refs。

### 9.2 最终回答必须直接回答

- 结构是否完整；若不完整，缺口是否真的适用；
- 核心逻辑链是否闭环；
- 最先阻断主要结论的断点是什么；
- 哪些结论仍需 M7 或其他模块复核；
- 哪些判断受不可访问来源限制。

推荐摘要句式：

“结构基本完整/存在 X 项适用缺口；核心逻辑链闭合/部分闭合/未闭合。首要断点位于 A→B：稿件声称……，但……，因此主要主张……目前无法由稿件内部自洽支持。”

### 9.3 每条 finding 最小内容

- 单一 primary category 和 severity；
- 具体问题，不写泛化清单；
- 至少一个 present 证据；缺失问题另有 absence 证据；
- 受影响的目标、结果或结论；
- 可执行修订建议；
- review_confidence；
- finding origin；
- 若跨模块，写 suggested_modules，不重复立项。

---

## 10. Category 速查

### 主链

| category slug | 默认 severity | 用途 |
| --- | --- | --- |
| `objective_drift` | major；唯一目标未回答可 critical | 明确目标无对应结果 |
| `methods_results_gap` | major；按承诺重要性可 critical/minor | Methods 的关键完成式承诺无下游交代 |
| `orphan_results` | major/minor | 重要结果无上游动机/方法来源 |
| `design_analysis_disconnect` | major | 设计、抽样、验证、分析和主张无法衔接 |
| `analysis_reporting_gap` | major/minor | 核心模型/分析缺少使其不可解释的接口说明 |
| `participant_flow_inconsistency` | major；核心分析集不可识别可 critical | 人群、样本、队列或分析分母不闭合 |
| `endpoint_switching` | major/critical | 终点或时间点未解释变化 |
| `analysis_population_mismatch` | major | 分析人群定义或使用前后不一致 |
| `selective_reporting` | major/critical | 有证据表明只报告预设分析中的有利部分 |
| `internal_inconsistency` | major/minor | 同一观测跨来源冲突 |
| `circular_reasoning` | major | 待证结论参与样本/标签/评价定义 |
| `conclusion_overreach` | major | 结论对象或层级在研究中根本未测 |

### 结构与编辑

| category slug | 默认 severity | 用途 |
| --- | --- | --- |
| `missing_section` | major；按实际影响可 critical/minor | 适用且必需的信息功能不存在 |
| `incomplete_abstract` | minor；主要结果缺失可 major | 摘要缺核心信息要素 |
| `missing_reporting_guideline_element` | major/minor；仅阻断核心解释时 critical | 适用规范的必需接口缺失 |
| `abstract_main_text_inconsistency` | major/minor | 摘要与正文同一事实冲突 |
| `timeline_inconsistency` | major/minor | 时间点或流程时间线冲突 |
| `statistical_method_mismatch` | major | Methods 声称与 Results 统计量形式矛盾 |
| `missing_figure_reference` | major/minor | 被引用图表不存在 |
| `orphan_figure` | minor | 图表未被正文引用 |
| `terminology_inconsistency` | minor | 命名差异造成实体/组别歧义 |
| `abbreviation_undefined` | minor | 非通行缩写首次出现未定义 |
| `reference_numbering_error` | minor | 数字顺序制引用编号错误 |

### ML 与外部核验

| category slug | 默认 severity | 用途 |
| --- | --- | --- |
| `data_split_not_reported` | major | ML 切分单元或流水线独立性未报告，不等于已确认泄漏 |
| `data_leakage_sample_overlap` | critical | 训练与最终评估间存在明确实体重叠 |
| `data_leakage_normalization` | major/critical | 预处理明确使用评估数据拟合 |
| `data_leakage_feature_selection` | critical | 特征选择明确使用评估数据 |
| `data_leakage_model_selection` | critical | 用最终测试集选择模型或超参数 |
| `data_leakage_temporal` | major/critical | 使用预测时点之后的信息 |
| `target_leakage` | critical | 特征明确包含标签或其派生信息 |
| `data_leakage_pipeline` | major/critical | 交叉验证流水线或实体层级污染 |
| `cites_retracted_work` | major/critical | 未说明撤稿状态却把撤稿文献作为有效依据 |
| `reference_not_resolvable` | major | DOI 经权威核验仍不可解析 |
| `gene_symbol_data_corruption` | major | 日期化符号污染实际数据 |
| `gene_symbol_outdated` | minor | 旧符号造成映射风险 |
| `gene_symbol_unrecognized` | major/minor | 权威源与语境复核后实体仍不明 |
| `variant_inconsistent_with_reference` | major | 版本和物种一致后变异仍与参考序列冲突 |

其他已注册的具体 data_leakage_* category 可在有明确污染证据时使用。不要为无 ML 研究创建泄漏 finding。
