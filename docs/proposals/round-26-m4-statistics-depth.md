# Round 26 · M4 统计学规则库深度 提案

## 摘要

M4 的 `design_shape` 已声明 `crossover`，但原对照表没有交叉设计行，匹配病例对照也会被错误路由到普通 McNemar；本轮直接补齐单样本、交叉、匹配、聚合比例与合成量表边界。
§5.2 虽已删除固定 n 下限，旧措辞仍把“任一输入无法核验”近似当作样本量问题；本轮改成目标、报告缺失、可复算矛盾与精度越界四者分离，n 小本身不立 finding。
统计取证原 signal 无法按文档要求独立复算 p，且正确的 `p<上界` 会错误产生 `partial_extraction`；本轮已修复血缘与算法，新增的非劣效、组成数据和多重插补组件则因基线探针 `INCONCLUSIVE` 暂不实现。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/04-statistics.md` | §2.1 | p 反算 signal 强制保留检验族、统计量、tail 与自由度；Stage 2 应传入 observation/evidence refs | 旧文要求 M4 复算，但 signal 没有保存复算输入，也无法稳定绑定原文数字 |
| 同上 | §3.1、§4.1–§4.6、§4.9 | 增单样本、两周期交叉、匹配病例对照、交叉二分类、聚合比例；扩 RMST/灵活参数生存模型；限定 count、零膨胀、Likert 与 batch 规则 | `acceptable` 过窄会把合理稳健/阻断分析误报，过宽或缺行又会漏掉交叉内相关、匹配集与不同分母 |
| 同上 | §3.4–§3.5、§4.10、§9 | 模型诊断改为“有风险证据 + 无相容处理”才报警；删除 VIF/EPV/外部验证的机械必报；五项取证恢复按主要终点与结论影响分级 | 并行合入版本一度把“未报告某诊断名”直接升 major/critical，并漏掉第五个 `table_total_mismatch`，会破坏 Round 6/9 已完成的防误报门 |
| 同上 | §5.1–§5.3、§11 | 把“n 小”“依据未报告”“作者声称的 power 输入不可复算”“CI 跨临床界值”分开；移除 in vitro 的隐含 n<3 门 | 旧入口仍会误伤小样本 pilot，并把抽取不足误写成稿件样本量错误 |
| `skills/biomed-paper-review/scripts/statistical_forensics.py` | 文件头、p/计数/GRIM/check_all、自检 | “四项”更正为五项；p signal 保存完整输入；正确 p 上界不再产 partial；拒绝 F/χ² 的双尾声明；负计数报警；GRIM 不依赖 Python banker rounding；保留输入 refs | 修复会改变真实运行结果或证据可复算性的明确 bug，不新增检查 family |
| `skills/biomed-paper-review/schemas/extraction_signal.schema.json` | `forensics` | 显式声明 p 反算的 `test_family/statistic/df/df1/df2/tail/reported_bound` | `additionalProperties` 虽允许旧输出，却没有机器可发现的复算字段契约 |
| `skills/biomed-paper-review/SKILL.md` | §6.5 统计 CLI | 示例传入 evidence ref，并说明脚本会保留 refs、未传时由汇总器补齐 | 旧示例产空血缘，和 M4 消费门脱节 |
| `skills/biomed-paper-review/references/00-contracts.md` | §6.2 统计 signal | 同步输入 refs 与 p 复算字段要求 | 共享契约必须与脚本和 M4 同义 |
| `skills/biomed-paper-review/references/00-contracts.md`、`references/07-conclusions-discussion.md` | finding 示例；M4→M7 联动表 | 把运行规则中的旧 `sample_size_reporting/wrong_test/no_multiple_comparison_correction` 迁到 `power_and_sample_size/statistical_test_selection/multiple_testing_control` | 并行 taxonomy 更新若只改 M4 与一个 fixture，M7 不会消费新 category；旧名仅应保留在迁移表 |
| `tools/probe_cases/round26_*.md` | 三个新案例 | 增非劣效界值方向、组成闭合伪相关、多重插补错误 stacking 探针 | 新组件必须先证明裸模型不稳定或漏检 |

## 基线探针结果

| 候选 | 案例 | `qwen3.8-max × 3` | 结论 | 本轮行动 |
| --- | --- | --- | --- | --- |
| 非劣效界值—CI 闭合 | `round26_noninferiority_margin_direction.md` | 3 次均为 `[Errno 1] Operation not permitted`，有效样本 0 | `INCONCLUSIVE` | 不实现 P1，不声称 baseline miss；恢复出站访问后重跑 |
| 组成数据闭合伪相关 | `round26_compositional_correlation.md` | 同上，有效样本 0 | `INCONCLUSIVE` | 不实现 P2 |
| 多重插补错误 stacking | `round26_multiple_imputation_stacking.md` | 同上，有效样本 0 | `INCONCLUSIVE` | 不实现 P3 |

本轮按指定命令实际发起三组探针；失败发生在 DashScope 出站连接，不是模型回答 `NO`。
孤立案例本来还会高估裸模型命中率，因此恢复网络后应先按以下命令复跑，再用完整宿主论文做第二轮埋入式确认：

```bash
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round26_noninferiority_margin_direction.md \
  --error "非劣效结论错误：结局越高越差且界值为 +5%，95% CI 上限 +6.4% 越过界值，不能因优效性 p>0.05 或点估计低于界值宣称非劣效" --repeats 3
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round26_compositional_correlation.md \
  --error "直接对总和固定为 100% 的相对丰度做 Pearson 相关，负相关可能由组成闭合约束产生，不能据此推出两个菌群互相抑制" --repeats 3
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round26_multiple_imputation_stacking.md \
  --error "把 20 个多重插补数据集纵向拼成 9600 个独立样本后做一次普通回归，未按 Rubin 规则合并估计与插补内/插补间方差，导致伪精确" --repeats 3
```

`BASELINE_FINDS_IT` 的候选移入“已探针，放弃”；只有
`BASELINE_UNRELIABLE` / `BASELINE_MISSES_IT` 才可进入实现。

## 真实文献压力测试

本节复用尚未落地的 Round 9 P2 `m4-literature-regression`，不另建第二套 fixture 目录。

| 真实文献样例 | 已报道的统计问题 | 本轮规则能否抓到 |
| --- | --- | --- |
| Li 等对 83 个交叉试验的审计发现，period/carryover/missing data 常被忽略，部分论文未按受试者内配对结构分析，并像平行试验一样列表。[PLOS ONE 原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4540315/) | 交叉设计按独立平行组分析，精度没有保留 within-subject correlation | **A 类修复后能抓明确子集**：设计、period、sequence 与实际模型成功绑定，且全文明确把两周期观测当独立时为 `statistical_test_selection`；仅未报告 carryover 检验不报警，因为预检后丢第二周期本身也可能有偏 |
| Rehal 等审计 168 篇非劣效试验：39% 只报告一种分析，43% 的 type-I error 与 CI 口径不清或不一致。[BMC Medicine 原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC5073571/) | 用优效性“不显著”代替非劣效，margin/CI/tail 或 ITT/PP 口径不闭合 | **当前抓不到核心错误**：§4 没有 inferential objective、margin 方向与 CI 决策规则；P1 才能确定性检查“CI 是否越过 margin” |
| Díaz-Ordaz 等审计 cluster RCT：32 篇说明处理缺失，其中 8 篇使用多重插补但未在插补中容纳聚类。[PubMed 记录](https://pubmed.ncbi.nlm.nih.gov/24902924/) | 分析模型考虑 cluster，不代表 imputation model 也保留 cluster structure | **当前多数抓不到**：§4.9 只审最终模型的独立单位；P3 需分别记录 imputation 与 analysis 的层级处理。仅全文未写插补细节时只能报报告不足，不能断言方法错误 |
| 微生物组网络方法综述指出，直接对相对丰度用 Pearson/Spearman/Kendall 不处理 compositionality，会因固定总和产生伪相关，且传统相关不能直接证明微生物互作。[原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC6857202/) | 相对丰度闭合约束被当普通欧氏数据，随后把相关升级为生态抑制机制 | **当前抓不到**：§4.8 只有 FDR、批次与特征泄漏；P2 才记录数据几何、绝对负荷与 log-ratio/组成敏感性 |

以上聚合审计不能把每篇被纳入论文自动标为有错。回归集只保存审计文章明确验证的方法事实，
并为“报告不足”“明确错误”“可接受替代方法”分别建 gold；比例只作覆盖背景。

## B 类提案

### P1 · 非劣效 / 等效界值—区间闭合审计器

- **问题**：M4 目前只按 outcome/design 选择检验，无法表达 `superiority/noninferiority/equivalence`、有利方向、绝对/相对 margin、单侧 α 与分析集。`p>0.05` 不证明非劣效；点估计位于 margin 内也不够，必须由方向正确且置信水平匹配的 CI 完整越过界值。
- **影响**：这是临床试验中会直接反转结论的硬错。没有确定性方向归一化，模型容易把“高值更好/更坏”、risk difference 的减法顺序、HR/RR 的 1 与差值的 0 混淆；错误 finding 会影响临床解释并带来高假阳性。
- **方案**：**一期离线，M1 + Stage 2 工具层 + M4/M7；有效探针前不实现。** 复用 Round 9 P1 的 `analysis_spec`，增加 `inferential_objective`、`effect_measure`、`contrast_order`、`beneficial_direction`、`null_value`、`margin_scale`、`margin_lower/margin_upper`、`alpha_sidedness`、`ci_level`、`analysis_population` 与 `claim_ref`。新增现有统计脚本的 `margin_inference` operation，不另建脚本：先把效应变换为“正值=新治疗更差”的统一尺度；非劣效要求不利侧 CI 界限严格位于 `margin_upper` 内，等效要求整个 CI 位于双侧界值内，优效仍按 null。仅保存完整原文精度区间，工具产 `margin_inference_candidate`，M4 回查 margin/CI/analysis population 后立 `noninferiority_claim_inconsistent`；M7 只判断结论依赖。注册 margin 对账是**可选联网增强**，必须复用 Round 12 X1/ClinicalTrials.gov，当前值不代替历史版本。
- **代价**：2–3 人日；字段/方向变换 1 人日，absolute RD、RR/HR、连续差值、双侧等效与 20 个方向困难反例 1–2 人日。依赖 Round 9 P1 最小 `analysis_spec`。
- **建议优先级**：有效探针为 `MISSES/UNRELIABLE` 后 P0；当前为 `INCONCLUSIVE`，实现门禁未通过。
- **契约字段**：扩展 `analysis_spec` 与现有 `extraction_signal`；不增加记录类型，M1/工具不产 finding。
- **假阳性**：高。margin 方向、contrast 次序、绝对/相对尺度、CI level、ITT/PP、协变量调整或 estimand 任一不明即 `partial_extraction`。仅缺 ITT/PP 双分析不得自动判错；先按方案、缺失机制与一致性人工判断。网络失败只产 `system_limitation`。

### P2 · 微生物组 / 组成型组学的数据几何审计器

- **问题**：M4 把组学统一成“领域工具 + FDR”，没有区分绝对丰度、测序计数、总和缩放后的组成、log-ratio 坐标与零值处理。相对丰度总和固定会诱导相关；从相对变化不能识别绝对微生物负荷，更不能仅凭 pairwise correlation 宣称生态抑制。
- **影响**：16S、宏基因组、脂质组、代谢组和细胞组成数据会稳定漏检。只检查 BH 校正会给组成伪相关披上“adjusted p 合格”的外观，损害 25% 科学可信性；反过来把所有非 CLR 方法判错也会误伤 ANCOM-BC、ALDEx2、基于采样模型的 count 方法及有 spike-in/qPCR 的绝对定量。
- **方案**：**一期离线，M1 + Stage 2 工具层 + M4/M7；有效探针前不实现。** M1 增 `data_geometry:{geometry,measurement_scale,total_constraint,absolute_load_measurement,normalization,zero_handling,analysis_target,evidence_refs[]}`，`geometry` 仅 `euclidean/compositional/count_with_sampling_depth/unknown`。若补充矩阵可取，新增 `compositional_audit` operation：验证每样本闭合和零比例；对原文声称的 taxon pair 运行 subcomposition/reference sensitivity，不把结果相同当验证，只把符号/排序对 reference 或 pseudocount 极不稳定记录为候选。固定总和 + 原始 Pearson/Spearman + 无组成/绝对负荷敏感性只产 `compositional_method_candidate`；M4 立 `compositional_structure_ignored` 前必须确认作者作绝对或互作推断，M7 再审核因果越界。若数据只在 GEO/SRA，下载属于可选联网增强并复用唯一 X1；取不到只产 limitation，离线流程照常完成。
- **代价**：3–4 人日；schema/抽取 1 人日，闭合与敏感性算法 1–2 人日，绝对负荷、SparCC/CLR、ANCOM-BC、零替换与高多样性困难反例 1 人日。
- **建议优先级**：有效探针后 P1；先做 correlation/interaction claim 垂直切片，不做“所有 DA 方法排行榜”。当前不得实施。
- **契约字段**：扩展 structured result 的非记录数据几何对象与 signal 条件块 `composition_audit`；finding 基础形状不变。
- **假阳性**：高。组成感知方法并不限于 log-ratio，测序 count 也不能仅因未转百分比就当绝对量。没有原始矩阵、绝对负荷、reference/pseudocount 或明确 claim 时只交人工；候选不得写“互作不存在”或“数据造假”。

### P3 · 多重插补合并与层级相容性审计器

- **问题**：M4 只检查“是否说明缺失处理”，无法区分 Rubin pooling、合法加权 stacking 与把 `m` 份插补简单拼成 `m×n` 个独立对象。它也不检查 cluster/longitudinal 层级是否同时进入 imputation model 和 analysis model。
- **影响**：错误 stacking 会把同一受试者复制 m 次并严重低估 SE；cluster RCT 即使最终模型用了随机效应，插补阶段忽略 cluster 仍可能扭曲不确定性。裸模型可能提醒“说明插补方法”，却未必复算 within/between-imputation variance。
- **方案**：**一期离线，M1 + Stage 2 工具层 + M4；有效探针前不实现。** 在 Round 9 `analysis_spec` 下增 `missing_data_analysis:{m,original_n,completed_n_each,combination_method,parameter_scale,per_imputation_estimates[],per_imputation_variances[],stack_weights,stack_variance_method,imputation_cluster_terms[],analysis_cluster_terms[],evidence_refs[]}`。扩展现有统计脚本 `multiple_imputation_pooling`：标准 MI 在参数正确尺度上复算 `q_bar`、within variance、between variance 与 total variance；只有原文明示将 `m×n` 行按独立样本普通回归且没有权重/专用方差，才产确定性候选。合法 weighted stacking、D1/D2/D3 检验或无法从论文重建的模型只记录 `not_comparable/partial_extraction`。M4 finding slug 为 `multiple_imputation_pooling_error`，默认 major，主要终点且显著性分类改变才可 critical。
- **代价**：2–3 人日；Rubin 标量合并与 stacking 门 1 人日，log OR/HR、变换参数、有限 m 自由度、cluster MI 与合法 StackImpute 反例 1–2 人日。
- **建议优先级**：有效探针后 P1；当前 `INCONCLUSIVE`，不实现。
- **契约字段**：扩展 `analysis_spec` 与 extraction signal 的 `mi_audit` 条件块，不新增记录类型。
- **假阳性**：中高。现代加权 stacking 可合法使用，但必须有专用权重与方差估计；不能看到“stacked”一词就报警。插补模型未报告只构成可复现性缺口，不能推定没有纳入 outcome、cluster 或辅助变量。

## 已探针，放弃

本轮没有候选得到 `BASELINE_FINDS_IT`；三项均为 `INCONCLUSIVE`，所以没有组件可列为“已证明应放弃”或“已证明有 uplift”。

## 未解决 / 需要人来定的问题

1. Round 9 P1 `analysis_specs[]` 仍未落地；没有最小 analysis binding，P1/P3 都只能生成高风险文本候选。建议先实现其最小字段集，不另建平行对象。
2. Round 9 P2 真实文献回归集仍未落地。本轮四个样例应追加到同一目录，且必须有明确阴性；不能再只靠合成 selftest 宣称真实 uplift。
3. Round 18 已提出 `design_modifiers` 解决 crossover/matched/cluster 路由。本轮只修 M4 表行，没有重复改 schema；若 Round 18 不采纳，复杂交叉和匹配研究仍会大量 `undetermined`。
4. Round 6 P5 的统计关系图、Round 9 P3/P4/P5/P6、Round 15 P2 均未实现；本轮不重复提出 SD/SEM、interaction、实验单位、precision、ClinicalTrials.gov 或跨位置闭合。
5. 是否把 `censoring_ignored` 固定 critical 改为与 §9 的主终点/结论影响门一致，需要 M4 与总评分负责人拍板；本轮不直接改变 severity taxonomy。
6. 三个 Round 26 探针须在可出站环境重跑。有效结果出来前不得合并 P1–P3 的 schema 或脚本变更。
