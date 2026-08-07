# Round 23 · 评分与覆盖率的统计合理性 提案

## 摘要

现有三项评分虽可确定性复算，但 `25/10/3/0`、category 上限 30、`20/50` 分段、`0.60/0.25/0.15` 与 confidence 折扣均无经验标定，不能称为已验证量表。
category 硬上限会掩盖跨多个独立实验反复出现的系统性 major，空维度按 1.0 赠分会让唯一图完全不可读的任务仍得 0.75，乘性 confidence 又会对同一低质量资产重复折扣。
本轮先修正 partial 的跨报告不可比表述与非法示例；生产公式暂不改，参数重标定、新评分门禁与置信度去重均须经十篇语料压力测试和有效 Qwen 基线探针后拍板。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §1.3、§5.1 | 明确 partial 风险分不得与任何其他报告比较或排序，包括 partial↔partial 与 partial↔full | 旧文只禁止与完整审核比较，仍允许把 M4-only 的 25 与 M6-only 的 0 错排成稿件风险高低 |
| `skills/biomed-paper-review/references/00-contracts.md` | §8.1、§11 | 同步跨报告不可比规则与 lint；把 partial 示例补齐 `band`、`priority_manual_review`、`threshold_caveat` | 示例原先缺少 schema 必填字段；不可比规则必须覆盖运行输出与人工使用口径 |
| `skills/biomed-paper-review/templates/review_report.md` | 第一节 partial 警示 | 固定显示“不得与任何其他报告横向比较或排序” | 只写 `comparable_to_full_review=false` 不能阻止下游比较两份不同 scope 的 partial 分数 |
| `skills/biomed-paper-review/schemas/review_report.schema.json` | `manuscript_risk_score.band` | 在字段说明中写明 partial 不得进入任何跨报告比较 | 不改 schema 形状，先消除字段语义歧义 |
| `tools/validate_schemas.py` | 模板静态门禁 | 要求 partial 跨报告禁比文案存在 | 防止模板后续回退为只禁止 partial↔full |
| `tools/probe_cases/round23_*.md` | 四个新案例 | 增加 category cap、空维度覆盖率、共同根因连乘、不同 partial scope 排序案例 | 为本轮所有新评分组件建立强制基线探针输入 |

## 基线探针结果

| 候选 | 案例 | `qwen3.8-max × 3` | 结论 | 本轮行动 |
| --- | --- | --- | --- | --- |
| category cap 单调性审计 | `round23_category_cap_systemic_major.md` | 有效样本 0；3 次均为 `[Errno 1] Operation not permitted` | `INCONCLUSIVE` | 不实现、不声称 baseline miss；恢复出站访问后重跑 |
| active-dimension 覆盖率 | `round23_coverage_empty_dimension.md` | 有效样本 0；3 次同上 | `INCONCLUSIVE` | 同上 |
| 共同根因置信度去重 | `round23_confidence_shared_root.md` | 有效样本 0；3 次同上 | `INCONCLUSIVE` | 同上 |
| partial scope 防排序 | `round23_partial_scope_ranking.md` | 有效样本 0；3 次同上 | `INCONCLUSIVE` | 同上 |

失败发生在 DashScope 出站连接阶段，不是模型返回 `NO`。因此四项均不得记作
`BASELINE_MISSES_IT`，也不得据此承诺 uplift。恢复网络后按案例文件逐项运行：

```bash
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round23_category_cap_systemic_major.md \
  --error "同一 category 的 30 分硬上限使新增相互独立且已确认的系统性 major 不再提高风险分" \
  --repeats 3
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round23_coverage_empty_dimension.md \
  --error "空字段与空补充材料维度各记 1.0，使唯一图不可读的任务仍得 0.75 覆盖率" \
  --repeats 3
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round23_confidence_shared_root.md \
  --error "同一低质量图在 coverage、Q 与 C 中被重复折扣，乘性结果不能解释为独立可靠性" \
  --repeats 3
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round23_partial_scope_ranking.md \
  --error "不同审核模块与 scope 的 partial 风险分不可排序" \
  --repeats 3
```

只有 `BASELINE_UNRELIABLE` / `BASELINE_MISSES_IT` 才允许把对应生产组件转入实现；
`BASELINE_FINDS_IT` 必须移入“已探针，放弃”。评测门禁本身仍应保留，因为它用于测量
参数与 uplift，不是让模型重复指出同一个稿件问题。

## B 类提案

以下生产变更均被基线门禁阻断；技术设计用于有效重跑后直接执行，不构成本轮实现授权。

### P1 · 十篇语料的预注册评分标定与压力测试包

- **问题**：Round 6 P1 已提出双人 gold、论文级 bootstrap 与反事实 overlay，但尚未落地，也没有把“如何用十篇论文决定参数”封闭成候选集、主要指标与接受阈值。当前 `datasets/` 只有 `manifest.json`；论文内容须由 `tools/fetch_papers.py` 重建。十篇均为已发表 PLOS 论文，发表状态不是质量标签；同一论文内的 finding、panel 与扰动也不是独立样本。
- **影响**：直接观察十篇结果后反复调 `30/20/50/0.60/0.5` 会产生严重过拟合；把数百个 finding 当独立样本会给出虚窄区间。评委追问参数来源时，团队目前只能回答“专家初始值”，科学可信性与工程可复现性都会扣分。
- **方案**：**一期离线评测基础设施，不新增 M1–M7 模块。** 落实 Round 6 指定的唯一 `tools/evaluate_scoring.py`，不得另建平行 evaluator；新增 `tools/fixtures/scoring-calibration/` 测试 schema 与运行 artifact。
  1. 先执行 `tools/fetch_papers.py` 到临时评测目录，生成 `corpus_lock.json`，逐篇记录 DOI、真实研究设计、JATS/PDF/图件 SHA-256、获取时间与解析器版本。不得按 manifest 的营销式 `slot` 当真实设计；`dose_response` 槽实际是回顾性队列，不能进入 IC50 分层。
  2. 两名生物医学审稿者独立标注，第三人裁决。原子标签固定为：字段是否可解析、资产是否足以回答 scope、finding 是否成立、证据是否充分、severity、`issue_family`、是否为独立实验/终点、人工 triage `P0/P1/P2/none`。不标“应接收/应拒稿”。报告字段状态逐类一致率，severity 报加权 Cohen κ；保留分歧，禁止把模型输出当 gold。
  3. 每篇预注册七个不写回 `datasets/**` 的 overlay：唯一必需资产不可读、被引用 supplement 不可达、20% 条件必填字段 `parse_failed`、只增加网络 `system_limitation`、同一 finding 拆成两条、增加同一 family 的独立 major、只改变 category slug。每个 overlay 保留 `base_report_hash`、操作、受影响 refs 与期望不变量。
  4. 候选参数在看结果前冻结。风险只比较 R0=当前 cap、R1=无 cap、R2=Round 6 的 family 递减 `lambda=0.5`；coverage 只比较 C0=当前、C1=active dimensions 内按 `0.60/0.25/0.15` 重归一、C2=active dimensions 等权；confidence 只比较 Q0=当前连乘、Q1=Round 6 的 process coverage 与 finding reliability 分列。十篇不足以搜索连续参数或重新估计 `20/50` 阈值，禁止扩大网格。
  5. 同一官方模型、同一论文、同一模式下裸模型与 Skill 各跑 3 次，取论文级中位数。主要 uplift 指标为经裁决 finding precision/recall、major/critical recall、evidence ref 可解析率、正确定位率、结构化字段准确率；风险排序用人工 triage 的 Kendall τ-b 与 pairwise concordance；coverage 用 scope 任务完成比例的 MAE；confidence 只有在明确定义为“本次 findings 中证据充分且成立的比例”时才报 Brier/ECE，否则只报 rank correlation 并继续标 `uncalibrated`。
  6. 所有区间以论文为一级重采样单位；overlay 与三次运行留在论文簇内。报告 2,000 次 cluster bootstrap 95% 区间，并以 10 个论文级差值做精确符号检验；不得按 finding 随机切分。参数选择用 leave-one-paper-out，但只作粗筛，不宣称外部验证。
  7. 上线门槛预注册为：全部硬不变量零违反；候选在至少 8/10 篇不劣于现式；major/critical precision 不下降；人工 triage τ-b 与 coverage MAE 的论文级中位数均改善；任何指标区间跨越实质无差异界时保留现式。十篇只能把状态升级为 `stress_tested_small_corpus`，不能写 `calibrated`。
- **代价**：4–6 人日；双人标注与裁决 3–4 人日，下载锁定、evaluator、overlay 与统计报告 1–2 人日。依赖官方统一模型可运行、十篇资产可重建及 Qwen 探针恢复。
- **建议优先级**：P0 交付前至少完成 corpus lock、双人标注、三次运行与四个硬不变量；参数替换须等有效探针与盲态结果。
- **阶段 / 归属**：一期（不调用外部数据库；PLOS 资产重建是评测准备，不是审稿时外部核验）；开发期评测层，不属于 M1–M7，不进入生产报告。
- **契约字段**：生产契约暂不改；测试 artifact 新增 `corpus_hash`、`paper_id`、`run_id`、`parameter_profile_id`、`gold_findings[]`、`gold_scope_tasks[]`、`adjudication`、`counterfactual_operations[]`、`metric_results[]`。只有候选过门后才在生产对象增加 `parameter_version` 与 `calibration_status`。
- **假阳性**：评测不立 finding。最大风险是把已发表状态、单一审稿者意见或合成扰动当真值；用双人盲标、第三人裁决、论文级区间和真实/反事实结果分层展示控制。

### P2 · partial 模式取消标量风险分，改为范围内风险画像

- **问题**：本轮已把文档收紧为 partial 不得与任何报告比较，但 schema 仍强制 `figure_review` / `targeted_check` 输出 `manuscript_risk_score.value`。数值天然诱导排序；M6-only 的 0 与 M4-only 的 25 不共享可发现问题空间，添加 `comparable_to_full_review=false` 也无法阻止 BI、前端或用户按数值着色。
- **影响**：局部审核 0 分最容易被读成“低风险”，未执行模块被静默当作无问题；这会破坏三项分数分离，并使 partial 的安全文案在下游排序中失效。
- **方案**：**一期离线，Stage 5 输出契约迁移。** `manuscript_risk_score` 只允许 `partial=false` 的 `full_review`；审核模块未跑满时改输出非记录对象 `partial_risk_profile:{executed_modules[],skipped_modules[],scope_fingerprint,cluster_counts_by_severity,cluster_counts_by_module,cluster_counts_by_category,priority_manual_review,comparison_prohibited:true}`。`scope_fingerprint=sha256(canonical_json({mode,submode,executed_modules,fields,assets,supplements}))` 只用于证明范围，不授权同 hash 报告自动比较。报告只展示严重度/模块分布和 P0/P1 动作，不显示 `/100`、band 或红黄绿。
- **代价**：1.5–2.5 人日；review schema、四个 fixtures、validator、模板与 migration 同步。下游若已硬编码 partial `value` 需要一次破坏性迁移。
- **建议优先级**：P1 应该做；P0 先由团队拍板是否接受破坏性 schema 迁移。有效探针若为 `BASELINE_FINDS_IT`，不把它包装成 uplift 组件，但仍可作为安全/可解释性修复评估。
- **阶段 / 归属**：一期（不调用外部数据库）；Stage 5 聚合/报告层，不新增审核模块。
- **契约字段**：删除 partial 分支中的 `value/band/threshold_caveat`；新增 `partial_risk_profile` 与 `scope_fingerprint`。finding、signal、system limitation 均不变。
- **假阳性**：不判断稿件。风险是失去局部任务内部的粗排序；以严重度计数、最高优先级动作和 cluster 明细替代，禁止另造隐式总分。

### P3 · 评分公式的变形关系与 taxonomy 稳定性门禁

- **问题**：`tools/validate_schemas.py` 只能证明当前公式被正确复算，不能证明公式本身满足合理性质。category cap 使第五个与第六个独立 major 都不加分；同一科学问题换成多个 category slug 又可绕过 cap。Round 6 P2 已提出 family 递减公式，本项不重复拍公式，只补任何候选公式都必须通过的黑盒性质测试。
- **影响**：可复算但非单调、依赖 taxonomy 粒度的分数仍会给出反直觉排序；新增模块或 category 时，稿件风险会因命名而非科学事实漂移。
- **方案**：**一期离线工程门禁，探针有效前不实施。** 新增 `tools/audit_scoring_invariants.py`，读取合法 review fixture 后生成最小变体并对每个 `parameter_profile_id` 检查：①重排 finding/cluster 不变；②拆分同一 cluster 不变；③新增独立已确认 major 在未到总分 100 前不得降分或保持不变；④只改展示 category slug、保持 `issue_family + independence_key` 不变时分数不变；⑤新增 system limitation 不得升高 risk；⑥使必需资产/字段不可用不得升高 coverage/confidence；⑦ inactive 维度不得赠分；⑧同一范围内提高任一子率不得降低 coverage。失败输出反例 JSON 和最小 diff，不自动修改公式。
- **代价**：1–2 人日；属性生成器、三个参数 profile 与 20–30 个回归变体。taxonomy 稳定性依赖 Round 1/Round 6 尚未落地的 `issue_family + independence_key`。
- **建议优先级**：P0 先恢复四个基线探针；cap/coverage 候选为 `MISSES/UNRELIABLE` 后，本门禁为 P0。若 `FINDS_IT`，不把相应检查放入 Skill 默认热路径，但可保留为开发期公式单元测试。
- **阶段 / 归属**：一期（不调用外部数据库）；开发期 Stage 5 公式门禁，不属于 M1–M7。
- **契约字段**：生产契约只在采用 family 公式后扩展 `issue_family`、`independence_key`、`parameter_profile_id`；测试 artifact 为 `{invariant_id,base_hash,variant_hash,expected_relation,observed_relation,profile_id}`。不新增记录类型。
- **假阳性**：不产稿件 finding。错误的 `independence_key` 会把同一问题误当多个独立问题；只有实验/终点/人群与主证据锚点均明确不同才允许“独立 major”测试，不确定时合并计一次。

### P4 · 共同根因质量账本：为 confidence 去重提供可审计输入

- **问题**：Round 6 P4 已提出拆开 process coverage 与 finding reliability，但现契约没有表达“这些折扣来自同一个输入缺陷”。同一 Figure 4 可同时降低 asset coverage、产生 pixel/OCR dependency、使 finding 变 low、再制造 conflicting group；当前 `coverage × Q × C` 把相关变量当独立折扣。单凭换成加法或调和均值仍无法证明没有重复计因。
- **影响**：0.18 可能只代表一张图糊，而非四个独立证据缺陷；用户无法知道应重传一张图还是全面复核，数值也无法对 finding 正确率作校准。
- **方案**：**一期离线，Stage 5 质量血缘扩展，探针有效前不实施。** 新增非记录 `quality_impairment_groups[]:{impairment_id,cause_type,cause_refs[],affected_assets[],affected_fields[],affected_observations[],affected_findings[],derived_effects[],independence_status}`。只允许两种确定绑定：共享同一 `system_limitation.id`，或共享同一原始资产 ref/hash；禁止用语义相似自动合因。P1 同时比较当前连乘、Round 6 的双指标分列、以及“同一 impairment 只取最严重一次折扣”的 grouped profile；没有 findings 时 finding reliability 固定 `not_applicable`。生产公式在十篇结果出来前不改。
- **代价**：2–3 人日；账本/schema/validator 1–1.5 人日，图像、OCR、supplement、conflict 正反例 1 人日。finding 到 observation 的精确绑定最好复用 Round 1 P1 的 `observation_refs[]`；未落地时只能按 evidence ref 保守映射并标 `lineage_incomplete`。
- **建议优先级**：P1；先恢复 shared-root 探针并完成 P1 小语料压力测试。即使候选公式胜出，也不得把 resulting value 称为概率，除非 finding-level 校准通过。
- **阶段 / 归属**：一期（不调用外部数据库）；Stage 5 评分装配与质量血缘，不新增 M1–M7 模块。
- **契约字段**：新增非记录 `quality_impairment_groups[]`；`review_confidence` 候选扩展 `calculation_profile`、`impairment_group_count`、`lineage_status`。不改变三类记录与稿件风险分。
- **假阳性**：不产稿件 finding。错误合并独立缺陷会使 confidence 过高；只按同一 limitation id 或同一资产 hash 自动合并，其余 `independence_status=unknown` 并采用更保守展示，不自动抵消折扣。

## 已探针，放弃

本轮没有候选得到 `BASELINE_FINDS_IT`；四项均为 `INCONCLUSIVE`，不得列为“已证明有 uplift”，也不得把网络失败当作模型漏检。

## 未解决 / 需要人来定的问题

1. 是否立即冻结现有生产参数并统一保持 `uncalibrated`。建议冻结；在十篇盲态评测完成前不得改 `30/20/50/0.60/0.5`。
2. 是否接受 P2 的破坏性迁移：partial 模式完全取消 0–100 标量。建议接受；本轮 A 类文案修复只是安全下限，不能约束外部 BI 排序。
3. `review_confidence` 的目标究竟是流程完成度、finding 证据充分率还是 finding 正确概率。建议采纳 Round 6 P4 的拆分；目标未定义前不存在可统计标定的单一 confidence。
4. 十篇语料当前只有 manifest，且 slot 至少一处与真实设计不符。未生成 `corpus_lock.json`、未完成双人 gold 前，不得声称这些参数已在十篇论文验证。
5. 十篇是十个论文级独立单位，最多支持压力测试、淘汰病态公式与方向性比较；不能用来稳定估计 20/50 阈值，更不能证明跨期刊、跨设计校准。初筛后至少扩到 30–50 篇、预留外部 holdout。
6. Round 6 已采纳的是 `partial_not_classified`、参数“未经标定”的披露与 M4 severity 降级；其 P1–P4 的 evaluator、family 递减、active dimensions 与 confidence 拆分均尚未实现。本轮 P1/P3/P4 是执行门禁与缺失血缘，不重复建立第二套公式。
7. `external_validation_coverage` 继续独立于 extraction coverage。X1 网络失败只产 `system_limitation` 并降低该独立覆盖率，不得进入本轮三项生产公式。
