# Round 6 · 评分与覆盖率的统计合理性 提案

## 摘要

当前三项评分已经做到确定性复算，但所有权重、category 上限、分段阈值和置信度惩罚系数都没有语料标定；“可复算”不能替代“有经验效度”。
固定 `0.60/0.25/0.15` 在单图任务上会让唯一图像完全不可读时仍得到 `0.75` 覆盖率，category 上限 30 则会把五个同类独立 major 压成 30 分，两者都会产生反直觉排序。
十篇 PLOS 语料适合做真实输入回归和反事实压力测试，但全是已发表论文、只有 10 个论文级独立单位，且 `dose_response` 槽位实际不是剂量反应研究，因此本轮建议先建双人金标准、论文级 bootstrap 与受控扰动门禁，再决定是否改公式。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §0.2 | 把“无网络所以一期不查外部库”改成“离线保底 + 一期可选联网增强”，同时明确当前 external evidence 契约尚未落地，不得声称已核验 | 旧边界与官方白名单网络和 12 小时环境冲突；又不能把尚未实现的 X1 写成已交付能力 |
| `skills/biomed-paper-review/SKILL.md`、`references/00-contracts.md` | §5；§8 | 明示权重、上限、阈值和惩罚系数均为未经语料标定的初始专家参数 | 原文只承认风险分段未经验证，会让覆盖率与 confidence 系数看起来像已有统计依据 |
| `references/00-contracts.md`、`schemas/review_report.schema.json`、`tools/fixtures/sim3_targeted_ethics_supplement_inaccessible.json`、`tools/validate_schemas.py` | §8.1；risk score 条件分支；模拟③；评分复算 | partial 风险分的 `band` 固定为 `partial_not_classified`；schema 双向强制少于六模块为 partial、恰好六模块为非 partial | 旧 JSON 虽带 `comparable_to_full_review=false`，却仍把 M6 单模块 0 分标成 `routine_review`；schema 也允许六模块报告继续写 partial |
| `docs/schema-migration.md`、`README.md` | risk score 迁移；当前状态 | 同步 partial band 迁移规则与当前 140 项校验计数 | 避免下游按旧三值 band 实现，或用过期检查数描述工程状态 |
| `references/04-statistics.md` | §9 | p 不一致、百分比不一致与 GRIM 命中改为按主终点、显著性阈值、分母影响和人工排除口径差异后升级 severity；修正 `sample_size` 可为 minor/major | 固定把任何 p 抄录错或 GRIM 命中标成 critical 会把次要表格笔误放大为稿件级最高风险 |
| `references/00-contracts.md`、`references/04-statistics.md`、`references/06-ethics-compliance.md`、相关 schema/resource/script docstring | 运行时脚本引用 | 将已实现工具路径统一为 `skills/biomed-paper-review/scripts/` | 根 `tools/` 不属于 Skill 运行时；旧引用会让执行器找不到已交付能力 |
| `scripts/statistical_forensics.py`、`scripts/ethics_compliance_check.py`、`schemas/extraction_signal.schema.json` | signal 生成与类型专属字段 | 默认 id 从非法的 `SIG-F01` / `SIG-E01` 改为数字 id；为伦理 signal 的无 severity 规则轨迹补 schema 与条件必填，并移除嵌套 `severity_hint` | 两个已实现脚本原本生成不了符合 `^SIG-[0-9]{3,}$` 和 `additionalProperties:false` 的输出；`severity_hint` 还会绕过“signal 无 severity”边界 |

## B 类提案

### P1 · 十篇语料上的评分标定与反事实压力测试门禁

- **问题**：`25/10/3/0`、category cap 30、风险分段 `20/50`、coverage 的 `0.60/0.25/0.15`、confidence 的 `0.30/0.20/0.10`、冲突惩罚和 `<0.5` 警告均无数据来源。十篇语料又全是 2025 年已发表 PLOS 论文，不能用“是否发表”作标签；同一篇中的 panel、observation 和 finding 共享实验与写作过程，也不能当独立样本。`datasets/manifest.json` 的 `dose_response` 槽位标题为 *Early-pregnancy HDL-related inflammatory indices and risk of preeclampsia*，实际是回顾性队列，不包含预期的 IC50/剂量反应压力测试。
- **影响**：直接在 10 篇上调参会严重过拟合并产生伪精确阈值；不做任何实验则无法回答评委“为什么是 30、0.60 或 0.5”。Uplift 消融也可能只证明输出变多，而不是证据正确率、审稿召回或人工优先级排序变好。
- **方案**：**一期离线评测基础设施**，新增 `tools/evaluate_scoring.py`、`tools/fixtures/scoring-calibration/` 与独立测试 schema，不修改 `datasets/**`。
  1. 两名生物医学审稿者独立标注十篇论文：条件必填字段状态、图表可读性、补充材料依赖、issue family、finding 是否成立、severity、主/次终点、是否必须优先人工复核；分歧由第三人裁决。severity 报加权 Cohen κ，字段状态与 finding 报逐类一致率，不把模型输出当 gold。
  2. 金标准目标是“证据成立的 finding 与人工 triage 优先级”，不是录用/退稿。风险分报告与 gold 优先级的 Spearman ρ、Kendall τ-b、major/critical precision/recall；confidence 若声称可校准，则报告 Brier score、可靠性图和 expected calibration error。没有明确概率语义时只报告 rank correlation，不计算 Brier。
  3. 同一官方模型、同一论文、同一模式分别跑裸模型与 Skill 各 3 次，取论文级中位数；同时报告 evidence-ref 可解析率、正确证据定位率、finding precision/recall、结构化字段准确率和人工复核队列长度，避免用字数或 finding 数冒充 uplift。
  4. 以论文为重采样单位做 2,000 次 cluster bootstrap，给全部指标 95% 区间；调参使用 leave-one-paper-out，不得按 finding 随机切训练/验证。只有候选参数在至少 8/10 个留一折中不劣于现公式、且 major/critical precision 的区间下界达到团队预注册门槛，才允许替换生产参数。
  5. 对每篇生成不落回 `datasets/` 的反事实 overlay：遮掉一个条件必填字段、令补充材料不可达、模糊一张必需图、增加 OCR 噪声、复制/拆分同一 finding、把同一问题换一个 category slug、给次要结果注入一位数 p/CI/百分比错误。门禁不要求每个变体都像真实投稿，但要求单调性：系统限制不得升高风险、证据变差不得升高 coverage/confidence、重复或拆分同一问题不得升高风险、增加独立已确认 major 不得降低风险。
  6. 按语料能力分层报告：`rct_clinical` 检验受试者流与重复测量；`survival_km` 检验 KM/Cox；`meta_analysis` 检验异质性与森林图；`omics_heatmap` 检验多重比较；`small_sample_pilot` 检验小样本；`animal_invivo` 与 `toxicology` 检验生物学重复、性别分层和剂量；`microscopy_ihc`、`flow_cytometry` 检验视觉/OCR。现有语料不覆盖的剂量反应不得伪称已验证，另加合成 fixture 或后续补一篇真实论文。
- **代价**：3–5 人日标注，1–2 人日评测脚本；需要至少两名领域审稿者和一名裁决者。10 篇只够做回归与粗标定，不能支撑稳定的跨期刊阈值估计。
- **建议优先级**：P0 交付前必须做最小版：双人标注 10 篇、三次 uplift、五类反事实门禁、论文级 bootstrap；完整参数搜索可在初筛后继续。
- **阶段 / 归属**：一期离线；评测基础设施，不属于 M1–M7，不进入生产报告。
- **契约字段**：生产契约暂不改；测试 schema 新增 `gold_findings[]`、`gold_field_states[]`、`triage_priority`、`adjudication`、`counterfactual_operations[]` 与 `parameter_version`。只有参数被接受后才按 P2–P4 扩展生产字段。
- **假阳性**：评测本身不立稿件 finding。最大风险是把审稿者分歧或已发表状态当真值；保留逐条分歧、裁决理由与论文级区间，不用单一总分掩盖不确定性。

### P2 · 取消 category 硬截断，改做问题家族内的递减累积

- **问题**：当前同一 category 五个独立 major 的原始权重为 50，却被 cap 到 30，仍停在 `clarification_needed`；一个跨多个动物实验反复出现的伪重复问题因此可能比三个不同 slug 的普通 major 得分更低。反过来，category 拆得细的模块更容易绕开 cap，同样科学风险会因 taxonomy 粒度而改变。单个 critical 已由 `priority_manual_review=true` 兜底，但“无 critical、同类系统性 major”仍会被掩盖。
- **影响**：风险分不是问题严重性的函数，而是 category 命名粒度的函数；评委用“5 个同类 major vs 3 个异类 major”即可构造反直觉排序。cap 还会让新增独立已确认 major 后总分完全不变，违反基本单调性。
- **方案**：**一期离线**在 P1 回归框架中并行比较现公式与问题家族递减公式，不先拍脑袋替换：
  ```text
  family_score = max(w_i) + lambda × Σ其余独立 cluster 的 w_i
  manuscript_risk_score = min(100, Σ_family family_score)
  ```
  `lambda` 只在 `{0.25, 0.50, 0.75}` 中用 leave-one-paper-out 选择；独立性键为不同实验/终点/受试者群 + 不同主证据锚点，不能靠拆 finding 获得。severity 权重只在保持 `critical > major > minor > info=0` 的小网格中比较，不以已发表/未发表拟合。若 10 篇无法区分候选，保留现权重并继续标 `uncalibrated`，但先删除 cap 的“统计依据”暗示。完整审核 band 仅按双人 gold 的人工 triage 优先级定阈值；区间重叠时不改 `20/50`，继续显示未经验证。
- **代价**：1–2 人日；依赖 P1 gold。还依赖 Round 1 P1 已提出但未实现的稳定 `scoring_category/issue_key`，本轮不另造第二套聚簇架构。
- **建议优先级**：P0 交付前至少完成现公式与 `lambda=0.5` 的盲测对照；是否切换生产公式由结果拍板。
- **阶段 / 归属**：一期离线；Stage 5 聚合器，不新增审核模块。
- **契约字段**：扩展 `issue_cluster` 的 `issue_family`、`independence_key`；risk score 增加 `scoring_rule_version`、`parameter_version` 与逐 family `score_breakdown[]`。这是现有对象扩展，不新增记录类型。
- **假阳性**：不新增 finding，但错误拆分“独立 cluster”会抬高风险。只有 issue family、实验/终点键和主锚点都可解析时才递减累积；不确定时合并计一次并交人工，不允许模型自行宣称独立。

### P3 · 按模式激活覆盖率维度，禁止空维度赠送分数

- **问题**：三个子率分母为 0 时都记 1，再以固定权重相加。`interpretation_only` 若只请求一张图且该图不可读，字段与补充材料两个空维度各得满分，最终 `extraction_coverage = 0.60 + 0 + 0.15 = 0.75`；这不是细微权重争议，而是任务完全失败仍显示高覆盖。full review 中没有补充材料的论文也固定获得 0.15，和“补充材料存在且全部可得”不可区分。
- **影响**：单图/纯文本/无补充材料等模式间的 coverage 数值不可解释；随后 confidence 再乘 coverage，会把错误基线继续传播。评委最容易用一张不可读图构造这一失败案例。
- **方案**：**一期离线**保留三维向量，但标量只在预先声明的 active dimensions 上归一化：
  ```text
  active_d = 该模式与 scope 需要此维度
  extraction_coverage = Σ(active_d × base_weight_d × rate_d)
                        / Σ(active_d × base_weight_d)
  ```
  `interpretation_only` 固定只激活 `asset_readability`，唯一图不可读即 coverage 0；纯文本结构化抽取只激活 field；full review 按 Stage 1 冻结的 evidence dependency 激活 field/asset/supplement。`denominator=0` 只有在维度明确 `not_applicable` 时才排除；若本应盘点但 Stage 1 失败，维度状态为 `inventory_failed` 并降低 coverage，禁止伪装成 `not_applicable`。基础权重先沿用 0.60/0.25/0.15，最终值由 P1 比较“固定权重”“等权”和小网格候选；报告永远展示向量，不允许只报标量。
- **代价**：1–2 人日；需新增四模式各一个正例和“唯一图不可读 / inventory 失败 / 无补充材料”负例。
- **建议优先级**：P0 交付前必须修复空维度赠分；权重重标定为 P1 的后续。
- **阶段 / 归属**：一期离线；执行规划 + Stage 5 装配，不属于记录或审核模块。
- **契约字段**：扩展 `execution_scope.coverage_dimensions[]:{dimension,status,reason}`；`extraction_coverage` 新增 `active_dimensions[]`、`weight_profile`、`parameter_version`。复用现有三个 rate，不重构三类记录。Round 4 已提出的 `external_validation_coverage` 必须继续独立，网络失败不得塞进本分数。
- **假阳性**：不产生稿件判断。主要风险是执行器通过错误声明 `not_applicable` 抬分；active dimensions 必须在抽取前冻结，并由模式与 Stage 1 inventory 规则推导，不能由最终结果反推。

### P4 · 把“流程覆盖”与“finding 可靠性”拆开，停止相关惩罚连乘

- **问题**：当前 `review_confidence = extraction_coverage × Q × C` 把三类并不独立的缺口相乘。同一张低质量图可能同时降低 asset readability、让 finding 依赖 OCR/pixel、并造成 key_data conflict；例如三因子均为 0.5 时结果为 0.125，等于对同一根因连续惩罚。一个同时依赖 pixel 与 OCR 的 finding 还会同时进入两个 rate；`C` 则惩罚 scope 内所有冲突，而不要求最终 finding 依赖该冲突。没有 finding 时分母用 1，系统仍可给出很高的“审核置信度”，但此时没有 finding 正确率可校准。
- **影响**：confidence 更像任意的质量折扣乘积，不是可解释的结论可靠性；低分可能只表示输入差，也可能表示现有 finding 不可信。用户无法据此决定“重传 PDF”还是“让统计专家复核”。
- **方案**：**一期离线**先并列输出两个正交量，再用 P1 决定是否保留 composite：
  1. `review_process_coverage` 直接复用 P3 的覆盖向量，回答“范围内检查完成了多少”；
  2. `finding_evidence_reliability` 只在有 finding 时计算，按 finding 对 gold 的正确率标定。依赖率按 finding 求 union：同一 finding 同时依赖 pixel+OCR 只记一个复合 provenance 状态；冲突只有在该 finding 的 observation refs 指向该组时才影响它；severity 只用于分层展示，不用高 severity 自动抬高可靠性。
  3. `all_findings=[]` 时 reliability 为 `not_applicable`，不得写 1.0；报告改写为“本次未检出 finding，流程覆盖率为 X”，不能说“审核结论置信度 100%”。
  4. 若平台必须保留一个 `review_confidence.value`，候选只比较加权算术均值、调和均值和现乘法，目标为论文级 finding precision/人工证据充分性；未达到预注册校准门槛时保留数值但改名 `evidence_support_index` 并标 `uncalibrated`，不得称概率。
- **代价**：2–3 人日；可靠性血缘依赖 Round 1 P1 的 `observation_registry/observation_refs[]`。未落地前只能按共享 evidence ref 保守反推，并必须披露该限制。
- **建议优先级**：P1 应该做；交付前至少修正 pixel/OCR union、conflict 依赖门控和“零 finding ≠ 置信度 1”。
- **阶段 / 归属**：一期离线；Stage 5 评分装配，不新增审核模块。
- **契约字段**：扩展 `review_confidence` 为 `{review_process_coverage,finding_evidence_reliability,dependency_union_rate,dependent_conflict_rate,calibration_status,parameter_version}`；`finding_evidence_reliability` 允许 number 或 `not_applicable`。不改变 finding/system limitation/signal 边界。
- **假阳性**：不立 finding。若 evidence-ref 粗粒度使多个 observation 共用一条证据，依赖率会被高估；在 observation registry 未实现前按较低可靠性展示并标 `lineage_incomplete`，不得偷偷选择更乐观的匹配。

### P5 · 舍入区间驱动的统计关系图，扩展四项现有取证

- **问题**：现有 `statistical_forensics.py` 已覆盖 p 反算、点估计是否落在 CI、计数/百分比与 GRIM，但大量论文内部的确定性恒等关系仍未利用：`SEM = SD/√n`、均差/SE/CI/t、OR/RR 与 2×2 计数、两组同模型下 `F=t²`、meta-analysis 的 `I²=max(0,(Q-df)/Q)`、BH adjusted p 的基本顺序约束。这些检查不需要原始数据，也不应推到二期。
- **影响**：复制粘贴错列、把 SD 写成 SEM、2×2 表与报告 OR 不一致、I²/Q/df 抄错等高价值硬错会漏掉；通用模型难以逐表建立约束并传播每个数字的舍入区间。
- **方案**：**一期离线**扩展 `skills/biomed-paper-review/scripts/statistical_forensics.py`，把同一结果的 estimate、SE、SD、SEM、CI、statistic、df、p、n、2×2 count、Q、I² 与 raw/adjusted p 建成关系图。每个节点保存原文精度对应区间，每条边只在方法语义完全确定时传播可行区间：
  1. `sd_sem_n_mismatch`：明确同一分析集、同一 n、同一指标时检查 SD/SEM；n 为技术重复或逐组不同则不运行；
  2. `effect_ci_se_mismatch`：均差在线性尺度，OR/RR/HR 在 log 尺度；只有明确 Wald CI 与置信水平时由临界值反推，profile likelihood、bootstrap CI、robust/clustered SE 一律不套 Wald；
  3. `two_by_two_effect_mismatch`：由明确四格计数复算 OR/RR/RD 点估计；有零格、连续性校正、加权/调整模型时只检查可比性，不判 mismatch；
  4. `f_t_identity_mismatch`：仅同一两组线性模型、同一误差自由度、同一双侧假设下检查 `F=t²`；
  5. `heterogeneity_identity_mismatch`：仅标准 Cochran Q 定义且 df 明确时检查 Q/I²；Hartung-Knapp、tau² 估计器不影响该恒等式，但不同亚组或舍入后的显示值不得混组；
  6. `bh_adjustment_mismatch`：仅作者明确使用 BH 且同一 family 的完整 raw/adjusted p 均可得时，检查 adjusted p 不小于 raw p 及排序后的单调性；只展示显著子集时不运行。
  工具仍只产无 severity signal；M4 按本轮已修的主/次终点与结论影响算法决定 finding。每个 mismatch 必须保存输入 observation refs、可行区间、失败的关系边、方法前提和 rule version。
- **代价**：3–4 人日；优先做 SD/SEM/n、2×2 effect 与 Q/I²，随后做 Wald 图与 BH family。每条关系至少 10 个困难反例，尤其覆盖 adjusted estimate、paired design、零格、不同 n 与非 Wald CI。
- **建议优先级**：P1 应该做；这是比继续微调风险分小数更直接的 uplift 来源。
- **阶段 / 归属**：一期离线；Stage 2 工具层产 signal，M4 产 finding。M1 仍不产 finding。
- **契约字段**：扩展 signal type 或新增单一 `statistical_relation_mismatch`；`forensics` 增 `relation_type`、`input_observation_refs[]`、`feasible_intervals[]`、`failed_edge`、`preconditions`、`rule_version`。优先用单一 signal type + relation enum，避免 slug 爆炸进一步影响 P2 的 category 计分。
- **假阳性**：中。最大风险来自把不同分析集、调整模型或 CI 构造法混为一组；任一语义键缺失时产 `partial_extraction` 或跳过，不输出 mismatch。signal 不得自动转 critical，M4 必须回查独立稿件证据。

## 未解决 / 需要人来定的问题

1. 是否接受 partial score 的 `band=partial_not_classified` schema 迁移。本轮已直接修复，因为旧 `routine_review` 标签与“禁止比较”自相矛盾；下游若硬编码三值 band，需要同步更新。
2. 是否在初筛前冻结当前参数并统一标 `uncalibrated`，还是接受 P1 最小标定后再改。建议先冻结，禁止在只有 10 篇时反复看结果调参。
3. coverage 是否还需要单一标量。建议保留向量为规范输出，标量只作排序兼容层；若 P1 证明标量没有稳定增益，可在下一 schema 版本移除。
4. review confidence 的目标到底是“审核流程完成度”还是“已产 finding 的正确概率”。建议接受 P4 的拆分；不定义目标就无法谈校准，也无法为乘法系数找依据。
5. `datasets/` 是否补一篇真正的剂量反应/IC50 论文。当前 `dose_response` 槽位与论文设计不符；受本轮 `datasets/**` 禁改约束仅记录，不修改。
6. Round 1 P1 的 observation registry、Round 4 P1 的 X1、Round 5 P5 的标准 JSON Schema 引擎仍未落地；P4 依赖前者，外部 validation coverage 依赖 X1。本轮不重复这些既有提案，也不把网络失败并入 extraction coverage。
