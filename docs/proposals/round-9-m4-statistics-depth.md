# Round 9 · M4 统计学规则库深度 提案

## 摘要

M4 原三步法要求六个特征全部确定才运行，且对照表把多种合理方法排除在 `acceptable` 外；本轮已改为终点绑定后只检查当前规则所需特征，并补齐重复/聚类、竞争风险、区间删失、诊断截断值与剂量反应等边界。
§5.2 的固定 n/EPV 门槛没有跨场景依据，会误伤探索性研究又放过参数复杂的欠拟合研究；本轮已改成效能、精度、实验单位和研究目的驱动的复核入口。
Round 1 P3 的四项统计取证已采纳并迁入 Skill，本轮补上 M4 的消费门；下一步最有 uplift 的不是继续扩“检验名称词典”，而是建立终点级分析对象、实验单位层级、交互对比审计和注册结果统计对账。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/04-statistics.md` | §2.1 | 为四项统计取证 signal 增加同一终点/比较/分析集/时间点绑定、`ran=true` 复算、分母语义与 GRIM 前提门；明确工具前提不足不得自动转 finding | 原文虽列出四类 signal，却没有阻止 M4 把不同分析集的数字混算，或把 `ran=false` 当稿件缺陷 |
| 同上 | §3.1–§3.4 | “六特征任一缺失即停”改为只要求当前规则使用的特征；先按 `applied_to` 与 evidence locator 绑定终点；仅写选择理由不再自动免责 | 二分类分析不需要正态性，简单随机两组比较也不需要混杂字段；旧规则会让真实论文大量 `undetermined`，同时给错误方法留下理由文本逃生口 |
| 同上 | §4.1 | 扩充 Welch、置换、稳健模型、GEE/混合模型、析因交互、观察性调整；拆开“估计 IC50”与“只比较剂量对照”；修正基线变化值规则 | 旧 `acceptable` 过窄；把任何 dose-response ANOVA、任何变化值分析都判误用会系统性误报 |
| 同上 | §4.2–§4.7 | 补 ≥3 配对二分类、聚类二分类/计数、重复有序、竞争风险 estimand、区间删失、复发事件和重复测量相关；修正 χ² 稀疏表、logistic EPV、诊断 cutoff 与模型比较 | 这些是临床与实验论文常见设计；旧表既漏收又含“所有期望频数均≥5”“EPV≥10”“cutoff 必须独立验证”等过硬条件 |
| 同上 | §4.9、§9、§10.2 | `replicate_type=technical` 不再直接推出伪重复；要求确认干预分配层级、推断单位和实际分析 n；severity 改为默认 major、满足主结论影响门才 critical | 技术重复标签不足以证明统计单位错误，offspring/病灶等生物学亚样本又可能同样聚类；旧规则会同时误报和漏报 |
| 同上 | §5.1–§5.3、§10.6 | 删除动物 5–6、诊断 30–50、EPV 10、组学 3/5 的固定 finding 门槛；按确证/探索目标、效能或精度、事件数/参数数、分离和不确定性路由 | 固定阈值无普适依据；尤其会把小样本 pilot 判“无效”，却把达到阈值的复杂模型误当安全 |

## B 类提案

### P1 · 终点级 `analysis_spec`：让三步法有可执行输入

- **问题**：`measurement.statistical_methods` 目前只是 `{test, applied_to, software, correction}` 自由对象；M4 无法稳定知道某个 p 值对应哪个终点、estimand、时间点、分析集、协变量模型和缺失数据策略。§3 本轮新增的终点绑定仍是文本算法，不是 schema 可复算对象。Round 3 P3 扩的是观测组上下文，不能替代“一个统计分析究竟比较了什么”。
- **影响**：同一篇 RCT 的 ITT 主要分析、PP 敏感性分析和女性亚组可被混在一起；“连续变量用 t 检验”也可能错误套到配对/独立两个终点。对照表越长，错误路由越多，30% 工程质量与 25% 证据链都会扣分。
- **方案**：**一期离线，M1 抽取 + M4 消费，P0**。在 `structured_result` 新增 `analysis_specs[]`，固定为 `{analysis_id,endpoint_ref,claim_refs[],estimand,contrast,analysis_population,timepoint,units_analyzed,outcome_type,model_family,test_name,tail,alpha,covariates[],missing_data_strategy,multiplicity_family_ref,experimental_unit_ref,observation_level_ref,cluster_refs[],reported_result_refs[],evidence_refs[],binding_status}`。`binding_status` 仅 `bound/ambiguous/unbound`；后两者只能产 `ambiguous_extraction/partial_extraction`，不得进入 §4 mismatch。`statistical_methods[].applied_to` 迁移为 `analysis_refs[]`，一个分析只允许一个 endpoint/timepoint/population 键。修改 `01-structured-extraction.md §6/§11`、`04-statistics.md §1/§3`、`structured_result.schema.json`、fixtures 与 validator；与 Round 3 P3 共用 `analysis_population/strata` 枚举，不造第二套上下文。
- **代价**：2–3 人日；1 人日 schema/迁移，1 人日终点绑定器与负例，0.5–1 人日迁移四个 fixtures。依赖 M1 能稳定抽出 endpoint id。
- **建议优先级**：P0 交付前必须做最小字段集：`analysis_id + endpoint_ref + analysis_population + timepoint + model/test + experimental_unit_ref + evidence_refs`。
- **契约字段**：扩展 `structured_result` 与 `statistical_methods`；不新增记录类型。M1 仍只抽取，M4 仍是唯一统计 finding 产出者。
- **假阳性**：高；错误绑定会制造确定性外观。只接受显式 `applied_to`、同表结构或明确交叉引用；语义相似不得强配，`ambiguous/unbound` 强制交人工。

### P2 · 真实文献误用回归集：逐条验证“能抓 / 不能抓”

- **问题**：Round 6 P1 提出了十篇语料上的总体评分标定，但没有给 M4 规则级金标准。当前 §10 只有合成正反例，无法证明规则能抓住真实出版物中的错误，也无法量化 `acceptable` 扩张后是否降低误报。
- **影响**：评委会把长对照表视作统计常识整理，而不是可复用能力；没有困难反例时，规则很容易在同尾/双尾、不同分析集、复合量表和层级数据上失控。
- **方案**：**一期离线评测，M4，P0**。在 `tools/fixtures/m4-literature-regression/` 建独立评测集，不改 `datasets/**`，每例保存合法摘录、文献标识、人工特征、期望 signal/finding、预期 severity ceiling 与 `known_limitations`。它是 Round 6 P1 的 M4 子集，沿用其双人标注与论文级统计，不另建评分体系。至少纳入以下四类真实文献：

  | 真实文献样例 | 已报道的误用 | 当前规则能否抓到 | 回归期望 |
  | --- | --- | --- | --- |
  | García-Berthou & Alcaraz 复核 2001 年 *Nature* 与 *BMJ* 结果，发现 181 个 *Nature* 结果中 21 个、63 个 *BMJ* 结果中 7 个统计量/自由度与 p 不一致；部分会改变显著性数量级。[原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC443510/) | `statistic + df + p` 内部不自洽 | **能**，`test_statistic_p_mismatch → p_value_inconsistent`；前提是检验族、df、tail 与同一比较成功绑定 | 阳性；另加 p 仅因舍入差异的阴性 |
  | Brown & Heathers 对 260 篇论文应用 GRIM；71 篇可检，36 篇至少一个不可能均值，获得的 9 份数据均确认至少一个报告问题。[原文](https://research.rug.nl/en/publications/the-grim-test-a-simple-technique-detects-numerous-anomalies-in-th/) | 整数/离散量表均值与 n 不可能同时成立 | **能抓子集**，`grim_incompatible_mean → grim_violation`；复合量表、缺失后 n、调整均值必须阴性/人工 | 阳性 + 多题平均、缺失分母和 banker rounding 困难反例 |
  | Nieuwenhuis 等复核 513 篇神经科学论文：79 篇用“一组显著、另一组不显著”代替交互检验，78 篇正确检验交互。[原文](https://doi.org/10.1038/nn.2886) | 差异的显著性未被直接检验 | **不能稳定抓**；§4.1 只在方法明确写拆分分析时给提示，没有 contrast 关系审计 | 作为 P3 的必过阳性；有明确 interaction p 的阴性 |
  | Lazic 等抽查动物研究，只有 22% 可确认是真重复，46% 存在伪重复，32% 信息不足。[原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC5902037/) | 干预在 litter/animal 层，offspring/cell 被当独立 n | **多数抓不到**；`biological/technical` 不能表达分配层与测量层 | 作为 P4 的层级阳性；层级不清必须 `partial_extraction` |
  | Zaki 等系统复核 210 篇医学仪器一致性研究，27% 使用相关系数，仍见不恰当方法。[原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3360667/) | 用高相关证明两测量方法一致 | **能**，稿件明确作 agreement claim 且只用 Pearson 时为 `agreement_by_correlation` | 阳性；同时报告 Bland–Altman、r 仅作辅助时为阴性 |

- **代价**：2 人日建 20–30 个摘录级 case，1 人日双人裁决；只保存合规短摘录与结构化参数，不复制全文。
- **建议优先级**：P0 交付前至少落地上表五类、每类 2 个困难阴性；它直接验证 uplift，不等 Round 6 全量标定。
- **契约字段**：仅测试 schema 增 `literature_source`、`gold_analysis_spec`、`expected_records[]`、`known_limitations[]`；生产契约不改。
- **假阳性**：评测不产生稿件 finding。文献审计中的“疑似”不能被当成逐篇真值；只把原作者明确验证或方法学上可复算的条目作为阳性，聚合比例只作覆盖背景。

### P3 · “显著 vs 不显著”交互/对比审计器

- **问题**：真实论文常以 A 组 `p<0.05`、B 组 `p>0.05` 推出 A 与 B 的效应不同；这不等于交互或差异的差异显著。现有对照表能提醒析因模型含交互，却无法从两条结果声明确定性识别该推理结构。
- **影响**：亚组、sex-specific effect、处理×时间与基因×环境论文会漏掉最常见的推断错误之一；这是裸模型容易复述结论、却不会稳定建立 contrast 图的高价值 uplift。
- **方案**：**一期离线，Stage 2 工具层 + M4，P0/P1**。新增 `scripts/interaction_contrast_audit.py`，消费 P1 `analysis_specs[]` 与 M1 claim：构建 `{factor,levels,within_level_effects,claimed_cross_level_difference,reported_interaction}`。只有 claim 明确作“效应在水平间不同/仅某亚组有效”，却没有对应 interaction/contrast estimate、CI 或 p 时，输出 `interaction_test_missing_candidate`；若给出两个独立效应及 SE/协方差可确定，工具计算 difference-of-differences 区间并输出 `interaction_contrast_inconsistent_candidate`。协方差未知、共享对照或重复测量时不得假设独立，只产缺检验候选。M4 新增 slug `interaction_not_tested`（默认 major，主要预设亚组且改变结论才可 critical）。
- **代价**：2–3 人日；claim pattern、contrast 图和 20 个 fixture。精确复算依赖 SE/协方差，最小版先做“缺 interaction 检验”结构审计。
- **建议优先级**：P0 先落结构审计；差异的差异复算为 P1。
- **契约字段**：`analysis_spec` 增 `factor_levels[]/contrast`，signal 新增条件对象 `contrast_audit:{claim_ref,within_level_analysis_refs[],required_contrast,reported_contrast_ref,independence_status,rule_version}`。扩展现有 signal，不新增第四类记录。
- **假阳性**：中。作者可能只描述一组而未声称组间差异；只有明确跨组比较语言才触发。探索性陈述、无 cross-level claim、或已报告 interaction/contrast 时不报。共享对照相关性未知时禁止数值复算。

### P4 · 实验单位与采样层级审计器：覆盖 litter、animal、cell、field、batch

- **问题**：`replicate_type` 只有 `biological/technical/unspecified`，不能表达干预分配在 cage/litter/animal/well，测量发生在 offspring/cell/field，模型又在哪一层做推断。真实伪重复经常发生在“生物学亚样本”，并非 technical replicate。
- **影响**：M4 目前既会把 technical 标签误当定罪证据，也抓不到 litter effect、co-housing、双眼/多病灶、同一 donor 多 organoid 和同批次多孔等高发问题。`pseudoreplication` 设为 critical 时尤其有名誉和排序风险。
- **方案**：**一期离线，M1 + Stage 2 工具层 + M4，P0**。在 `structured_result.design` 增 `sampling_hierarchies[]:{hierarchy_id,experiment_id,levels[]}`，每级为 `{level_id,entity_type,parent_level_id,count,allocation_at_level,independently_sampled,random_effect_or_cluster_term,evidence_refs[]}`；P1 `analysis_spec` 引用 `experimental_unit_ref/observation_level_ref/cluster_refs[]`。新增 `scripts/experimental_unit_audit.py`：仅当分析 n 位于 observation level、但 allocation level 更高，且模型/汇总未保留 parent cluster 时产 `pseudoreplication_candidate`；层级不全产 `partial_extraction`。对 cluster RCT 同时核对 cluster 数、个体数、ICC/design effect 与自由度来源；对 cell/field 数据核对 donor/animal random effect 或先汇总策略。
- **代价**：3–4 人日；层级 schema、M1 抽取、审计器与 animal/litter/cell/eye/well 五组 fixtures。可先覆盖两层树，任意深树随后。
- **建议优先级**：P0；这是 M4 最能体现生物医学专业度的确定性组件。
- **契约字段**：扩展 `design` 与 `analysis_spec`；signal 复用或新增 `pseudoreplication_candidate`，条件必填 `unit_audit:{allocation_level,analysis_level,parent_cluster_handling,effective_independent_n,rule_version}`。finding 仍由 M4 产。
- **假阳性**：高。细胞可能是真正独立培养/随机分配单位，offspring 也可能通过设计与模型处理 litter。任一分配层证据缺失只交人工；不能因“每只动物多个细胞”单独下 finding。

### P5 · 精度与模型复杂度驱动的样本量审计器

- **问题**：删除固定 n 后，M4 仍需要比“建议人工确认”更确定的 uplift。不同设计的可核验对象不是同一个 n：诊断研究看敏感度/特异度 CI 与病例/非病例数，预测模型看总样本、事件比例、参数自由度和 shrinkage，pilot 看可行性目标的精度，动物研究看独立实验单位与预期差异/变异。
- **影响**：若只删阈值，M4 会变得保守但没有新增能力；若保留 EPV=10/每组 30，则科学可信性直接受损。评委需要看到“为什么这个 n 对这个目标不够精确”的可复算证据。
- **方案**：**一期离线，Stage 2 工具层 + M4，P1**。新增 `scripts/study_precision_audit.py`：①诊断 2×2 表用 exact/Wilson CI 重算敏感度、特异度与目标阈值下界；②单比例/事件率按预设 margin of error 反算最低 n；③预测模型记录 total n、events/non-events、candidate parameter df、optimism/shrinkage target、separation 与 validation objective，不用单一 EPV 判错；④ pilot/feasibility 只按 recruitment/adherence/variance 等预设目标的 CI 与 progression criteria 检查；⑤确证 RCT 复算样本量公式时必须有 effect、SD/event rate、alpha、power、allocation、attrition 和 test family。输出 `precision_or_power_mismatch_candidate`，只在论文给出的输入可复算且报告 n 与复算区间不相容时进入 M4；缺输入仅 `sample_size_justification_incomplete` 候选。方法依据与误伤边界可用 [EPV 10 证据薄弱的模拟研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC5122171/)、[诊断研究按目标精度规划](https://pmc.ncbi.nlm.nih.gov/articles/PMC1459608/) 和 [CONSORT pilot extension](https://pmc.ncbi.nlm.nih.gov/articles/PMC5076380/) 做回归。
- **代价**：3–4 人日；优先交付诊断 CI + 两组均值/比例 RCT + pilot feasibility，预测模型 Riley 类公式随后。
- **建议优先级**：P1 应该做；先交三类可复算垂直切片，不追求一个公式覆盖所有设计。
- **契约字段**：signal 增 `sample_size_audit:{objective,formula_family,inputs,reported_n,recomputed_n_interval,precision_result,assumptions,rule_version}`；`analysis_spec` 增 `sample_size_objective_ref`。不改 finding 基础形状。
- **假阳性**：中高。效应量、失访、聚类设计效应、有限总体修正或 one/two-sided 任一不明都停止复算。小样本但目标是可行性/参数预估时不得输出“underpowered”。

### P6 · ClinicalTrials.gov 结果统计对账：扩展 Round 4 P2

- **问题**：Round 4 P2 已提当前注册记录的终点、安全性分母与受试者流对账，但没有消费 ClinicalTrials.gov 已发布的统计分析字段。注册结果可同时给出分析组、population、units analyzed、p、估计量、CI、非劣效类型和统计方法；这正好能对稿件主要结果做第二来源核验。
- **影响**：稿件表格与注册结果中的 HR/OR/均差、CI、p 或分析组若不一致，可能是版本、分析集或抄录问题。裸模型无法稳定遍历嵌套结果 JSON 并保留逐字段证据链；直接比数字又会把当前注册更新、不同 population 和不同 time frame 误判成错误。
- **方案**：**一期联网增强，复用 Round 4 X1 + M4/M6，P1**。不新建连接器框架；在 `clinicaltrials_gov` connector 增 `result_statistics` query。用 `GET https://clinicaltrials.gov/api/v2/studies/{nctId}`，读取 `resultsSection.outcomeMeasuresModule.outcomeMeasures[]` 的 `title/type/timeFrame/populationDescription/typeUnitsAnalyzed/unitOfMeasure/groups/denoms/classes/analyses`；`analyses[]` 读取 `groupIds/statisticalMethod/pValue/paramType/paramValue/dispersionType/dispersionValue/ciNumSides/ciPctValue/ciLowerLimit/ciUpperLimit/testedNonInferiority/nonInferiorityType`。字段由官方 [Study Data Structure](https://clinicaltrials.gov/data-api/about-api/study-data-structure) 定义。仅在 NCT、outcome title+time frame、group set、population、units 与 param type 全部精确可比时做舍入区间对账；X1 产 external evidence 和 `registered_result_statistic_mismatch_candidate`，M4 回查稿件内 evidence 后决定 finding。
- **代价**：2–3 人日；依赖 Round 4 P1 external evidence schema 尚未落地。需 10 个带 results 的 NCT 录制响应和 current-record 差异反例。
- **建议优先级**：P1；先做主要终点 estimate/CI/p 三元组，非劣效与复杂表格随后。
- **契约字段**：复用 Round 4 的 `stage_3c_external_validation` 与 `external` evidence；`assertions[]` 增 `outcome_key/analysis_population/group_ids/units_analyzed/param_type/estimate/ci/p/statistical_method`，signal 的 `external_check.check_type = registered_result_statistic_mismatch_candidate`。不改变三类记录。
- **假阳性**：高。注册结果可能晚于论文、使用不同 analysis population、不同 time frame 或不同 estimand；当前值不证明历史版本。任一语义键不等即 `not_comparable/needs_manual_review`；404、429、5xx、白名单阻断只产 `system_limitation`，绝不产稿件 finding。

## 未解决 / 需要人来定的问题

1. 是否接受 P1 的最小 `analysis_spec` schema migration。若不接受，§3 只能保守返回大量 `undetermined`，不能宣称对照表已可自动执行。
2. Round 3 P3 的观测上下文与 P1 的分析上下文应共享枚举但职责不同：前者定义“这个数是什么”，后者定义“这次推断比较什么”。建议不合并对象，只用 refs 连接。
3. `pseudoreplication` 是否继续允许自动 critical。建议仅在 P4 的分配层、分析层和主结论影响全部有证据时允许；否则最高 major/人工。
4. P5 是否先做诊断 CI、pilot precision 和简单 RCT 三个垂直切片。建议接受；预测模型样本量不能再退化为 EPV 阈值。
5. Round 4 P1 的 X1 尚未落地，因此 P6 只能做 connector 原型和录制响应测试；不得让 M4 直接创建 external evidence，也不得把网络失败写成 mismatch。
6. Round 6 P5 已提出 SD/SEM/n、2×2 effect、F=t²、Q/I² 和 BH 的统计关系图，本轮不重复；它仍值得做，但应消费 P1 的 `analysis_refs[]`，避免跨分析集拼数字。
7. Round 1 P3 的四项统计取证已采纳实现，且本轮已补 M4 消费门；Round 6 的固定 severity 降级也已实现。尚未实现的是统一执行入口、关系图扩展和真实文献回归集。
