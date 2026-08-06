# Round 16 · 契约一致性与可实现性 提案

## 摘要

§5.4 原算法会用“95% CI 重叠”掩盖点估计跨位置不一致，且未把单位换算因子应用到数值、不确定度与舍入容差；本轮已改成先比数值本体、再核对 uncertainty 端点的 fail-closed 顺序。
`stage3_extraction_signals[]` 在共享契约中有产出者，但在 `SKILL.md` 的 Stage 3 本地产物表中消失；聚簇步骤又与 `all_findings[]` 的无损拼接相冲突，两处已直接收敛。
Round 1 的单位/统计取证、Round 11 的序列/图像候选器、Round 12 的 X1 基础契约和 Round 14 的 Skill 内运行路径已被采纳；本轮不重复提数据库清单，只处理仍阻断实现的契约缺口。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §2.2–§2.4 | 把 `stage3_extraction_signals[]` 补入 Figure Parser 产物、Stage 3 本地产物和唯一产出者表 | 图像完整性脚本明确在 Stage 3 产 signal，旧主文却没有该本地数组，Stage 5 无法按文档聚合 |
| `skills/biomed-paper-review/SKILL.md` | §2.8 步骤 3 | 兼容性摘要改为“单位换算工作副本 → 数值本体 → uncertainty 端点”，明禁用 CI 重叠代替重复报告一致性 | 旧摘要与修正后的 §5.4 会给实现者两套顺序 |
| `skills/biomed-paper-review/references/00-contracts.md` | §2.2、§5.2、§5.4 | `unit_normalized` 对齐脚本实际 `ucum_code`；规定 `factor_a_to_b` 的固定调用方向，并同比例换算 value、uncertainty 和精度单位 | 旧文只比 `unit_normalized` 字符串；`1 mM` 与 `1000 µM` 虽然脚本可换算，工程实现仍会判 `ambiguous` 或直接比错数值 |
| 同上 | §5.4 步骤 3–5 | 先比点估计/数值约束，中心值兼容后才比同型 uncertainty 的对应端点；不同 uncertainty type 不互相否定 | 两个宽 CI 可能重叠，但稿件两处的点估计仍可明显不同；旧顺序会把真实内部矛盾洗掉 |
| 同上 | §5.5 | 规定任一候选缺本层信息时对全体跳过该判据；补齐 `source_class` 与 criterion 6 的 `canonical_rationale` 固定写法 | 旧文没规定“一个候选已知、另一个未知”时是跳过还是惩罚未知，绝对来源规则也没有合法的 rationale 编码 |
| 同上 | §6.3 规则 2 | 明确 system limitation 不直接扣分，只能通过已声明的 scope 字段/资产/补充材料/pixel/OCR 变量影响 coverage/confidence | 旧文“限制降低分数”允许实现者另加一个公式中不存在的惩罚项 |
| 同上 | §9.3 | “同模块合并”改为非破坏性建子簇；`issue_cluster.evidence_refs[]` 取成员并集，不改写 finding | §9.2 要求 `all_findings[]` 是六个本地数组的拼接，旧 §9.3 又要删并其元素，两者不可同时实现 |
| 同上 | §11 lint | pixel 强制约束数量从错写的四项改为五项 | §2.4 实际列出 5 项 |
| `skills/biomed-paper-review/schemas/key_data.schema.json` | `$defs.observation_core` | `unit_normalized` 说明对齐“只作审计轨迹，比较前应用 factor”；pixel 说明改为五项 | schema 说明原允许实现者直接比较原数值，且与共享契约计数不一致 |
| `skills/biomed-paper-review/scripts/normalize_biomed_units.py` | 模块用法、`_selftest()` | 示例改为实际 `μM → uM`，新增 `μM` 与 `μmol·L−1` 的精确 `ucum_code` 回归断言 | 旧自检只证明两种写法可比，无法阻止单单位输出再次与契约漂移 |
| `tools/fixtures/sim4_ic50_source_conflict.json` | `OBS-014`–`OBS-016`、`SIG-002` | `unit_normalized` 与 signal 说明从 `umol/L` 改为归一化脚本对 `μM` 实际返回的 `uM` | 模拟实例原与确定性脚本自相矛盾 |
| `docs/consistency-audit.md` | 模拟④、核对表 #14、已知遗留项 #3 | 同步 `uM`、pixel 五项约束，并把“单位表未实现”改为“归一化器已实现但 Stage 3b 未接线” | 审计结论仍描述旧实现，会误导后续工程师重复造单位表 |

## B 类提案

### P1 · Stage 3b 观测合并器与成对决策轨迹

- **问题**：本轮修正了 §5.4，但仓库仍没有执行该算法的 Stage 3b 脚本；`tools/validate_schemas.py` 只核对 fixture 最终形状，不会从原观测重算单位换算、成对关系、组 status 或 canonical。Round 5 P5 是标准 JSON Schema 验证，不是合并语义实现；本项不重复它。
- **影响**：评委只要用 `1 mM` vs `1000 µM`、`12.4 (95% CI 9–16)` vs `15.1 (95% CI 14–16)` 两个案例，就能暴露“脚本存在但没有接入 Stage 3b”。这直接损失 30% 工程质量与 25% 证据链。
- **方案**：**一期离线，Stage 3b，P0**。新增 `skills/biomed-paper-review/scripts/merge_observations.py`，输入 `structured_result_v1 + figure_records[] + evidence_registry`，输出 `structured_result_v2 + merge_extraction_signals[] + stage3b_system_limitations[]`。顺序固定为：指标身份/五键分组→观测 id 副本一致性→全部无序对按 id 排序→单位工作副本→数值本体→uncertainty→组状态→canonical。每对落一条 `comparison_trace`，fixture 至少覆盖等价 SI 单位、需分子量但缺失、点值舍入、宽 CI 掩盖中心值冲突、不同 uncertainty type、单边界、categorical 和重复 id 漂移。
- **代价**：2–3 人日；1–1.5 人日合并器，1 人日困难反例与 validator 复算。无网络、无 GPU 依赖。
- **建议优先级**：P0 交付前必须做。
- **分期 / 归属**：一期（不调外部数据库）；Stage 3b 共享工具层，不新增 M 模块，M1 仍不产 finding。
- **契约字段**：扩展 `key_data` 的 `comparison_trace[]:{observation_a,observation_b,unit_verdict,factor_applied,value_result,uncertainty_result,final_result,reason_code,rule_version}`；它是组内决策轨迹，不是第四类记录，不带 severity。
- **假阳性**：低到中。最大风险是原文精度、analyte 或分子量绑错；任一必需输入不能由 evidence 恢复时固定 `ambiguous`，不产 `source_value_conflict`。

### P2 · canonical 选择特征与决策轨迹正规化

- **问题**：§5.5 的判据 1、3、4、5 依赖“主要结果”、原文有效数字、“约”等近似标记和指标族要素，但 observation schema 只有 value/unit/uncertainty/n/provenance 与可选 quote。本轮 A 类修复能保证“缺信息时不猜”，却不能让工程师稳定执行高价值判据。Round 1 P3 提过 `reported_value_text`，但未落地，且未覆盖 canonical 特征。
- **影响**：不同模型会对“主要”与“叙述性摘要”做不同自由解读；最保守的实现又会几乎总是落到 id 字典序，使领域化 canonical 规则徒具文档外观。
- **方案**：**一期离线，M1/Stage 3 抽取 + Stage 3b 消费，P1**。observation 新增 `reported_value_text`、`selection_features:{result_role,approximation_status,significant_digit_unit,reported_elements[],feature_evidence_refs[]}`；`result_role` 只取 `primary/secondary/exploratory/unspecified`，`approximation_status` 只取 `exact/approximate/unknown`。Stage 3b 新增 `canonical_decision_trace[]`，逐层保存候选集、本层是否可计算、跳过原因与剩余集。`reported_elements[]` 只允许 `01 §6.3` 已登记的要素；不从自由文本猜一个新枚举。
- **代价**：1.5–2 人日；schema/迁移 0.5 人日，抽取与 canonical 负例 1–1.5 人日。
- **建议优先级**：P1 应该做；若 P1 合并器交付，至少同步落地 `reported_value_text + significant_digit_unit`。
- **分期 / 归属**：一期（不调外部数据库）；M1/Stage 3 产抽取属性，Stage 3b 产决策轨迹。
- **契约字段**：扩展 observation 与 `key_data.canonical_decision_trace[]`；不改 finding/signal/system limitation 三类记录。
- **假阳性**：不直接产 finding。错误特征会选错 canonical 并污染下游，因此任一候选的本层特征为 `unknown/unspecified` 时对全体跳过该层，不惩罚未知。

### P3 · 并行 Stage 4 的确定性 evidence 登记器

- **问题**：`SKILL.md §2.4` 把 `evidence_registry` 定义为“Stage 1 建立，各阶段追加，id 全局递增”，同时 Stage 4 的 M2–M7 又是并行产出者。六个写者在没有分配器或重映射阶段时无法保证不重号，也无法保证同 locator+quote 复用。
- **影响**：这是真实并行实现的竞争条件；冲突 id 会使 finding 引用到错证据，比单纯 schema 失败更严重。每次运行按时序随机分号也会使快照与消融回归不稳定。
- **方案**：**一期离线工程基础设施，Stage 4/5，P0**。各模块只产本地 `evidence_delta[]`，用临时 id 引用自己的 finding；Stage 4 barrier 后由单一 registry assembler 对 evidence canonical JSON 求 hash，先按 `(type, canonical_payload_hash, producer, local_id)` 排序，再去重 locator+quote 并分配全局 `EV-*`，最后一次性重写 finding refs。任一本地 ref 未能重写则拒绝渲染，不用空 ref 继续。若团队不接受重映射，备选是一个串行 registry writer API，但需接受 id 不能跨运行稳定。
- **代价**：1.5–2 人日；需全部 M2–M7 产物适配临时 ref，但最终 review report schema 不需改变。
- **建议优先级**：P0 交付前必须至少完成单写者与重号压力测试。
- **分期 / 归属**：一期（不调外部数据库）；Stage 4/5 编排基础设施，不属于 M1–M7。
- **契约字段**：内部运行 artifact 新增 `evidence_delta[]:{local_id,evidence_entry,producer}` 与 `evidence_id_map`；最终仍只输出现有 `evidence_registry`。不新增记录类型。
- **假阳性**：不产稿件判断。风险是过度去重把同定位不同文本合并；去重键必须包含 evidence type 与全部 canonical payload，不做语义近似去重。

### P4 · 封闭 `lookup_requests[]` 的唯一产出者与 schema

- **问题**：`00-contracts.md §1.6` 说 X1 “只接受 Stage 3b 封闭后的 `lookup_request`”，`SKILL.md §2.8.1` 却让 X1 自己“再创建 `lookup_request`”；该对象无 schema、无数组名、无唯一产出者，但 `external_target.lookup_request_id` 已要求引用它。Round 12 P1 已给出 resolver 输入形状，本项是把它收入现有产物图，不重复提 connector。
- **影响**：X1 当前消费一个从未被前置阶段产出的产物，直接违反本项目“任何阶段不得消费尚未产出的产物”。不先修这一点，首个 ClinicalTrials.gov 垂直切片会被迫私造输入契约。
- **方案**：**一期契约迁移，Stage 3b → X1，P0**。采纳 Round 12 P1 的输入形状，固定数组名 `lookup_requests[]`、唯一产出者 Stage 3b、唯一消费者 X1。Stage 3b 只能从 v2 中已解析的精确标识符/引文/注册信息与稿件 `present` evidence 生成请求；X1 不改写请求。新增 `schemas/lookup_request.schema.json`，并在 `SKILL.md §2.3/§2.4`、`00 §1.6/§9.2`、Round 12 resolver CLI 中同步。离线或无请求时数组为空，不产 limitation。
- **代价**：0.5–1 人日；schema、两个 fixture 与产物表同步。connector 实现仍按 Round 12/13 另计。
- **建议优先级**：P0，在任一 X1 connector 之前完成。
- **分期 / 归属**：契约与请求生成属一期离线可完成；实际 API 调用属一期可选联网增强 X1。不新增审核模块。
- **契约字段**：`{request_id,connector,query_kind,normalized_input,manuscript_evidence_refs[],requested_assertions[],consumer_modules[]}`；扩展现有契约，不重构三类记录。
- **假阳性**：请求本身不判断稿件。非精确名称、模型记忆补出的 id、无 present 锚点的主张一律不建请求；网络失败仍只产 X1 `system_limitation`。

### P5 · 封闭 `table_record` 与生物医学表格守恒取证

- **问题**：`review_report.schema.json` 对 `table_records[]` 的 items 只写 `{"type":"object"}`，没有表 id、定位、多层表头、合并单元格、分析集、分母、脚注或 observation 回流契约。现有 `table_total_mismatch` 脚本能做确定性计数闭合，但没有一个可复用的上游表格对象向它供数。
- **影响**：“输入/输出 schema 明确”这一 14% 维度会被一个完全开放的顶层数组直接击穿；更实质的是基线特征表、不良事件表、CONSORT 受试者流和 2×2 诊断表中的分母混用无法稳定进入统计取证。
- **方案**：**一期离线，Stage 3 Table Parser + Stage 3b + M2/M4，P1**。新增 `schemas/table_record.schema.json`，核心形状为 `{table_id,location,title,header_tree[],rows[],cells[],footnotes[],observations[],parse_status,evidence_refs[]}`。cell 固定携带 row/column semantic key、raw text、rowspan/colspan、analysis_population、timepoint、denominator_ref、footnote_refs 与 evidence ref；可数值单元格投影为复用 `observation_core` 的 `observations[]`，按现有五键回流 Stage 3b。只在 parser 显式建立 `mutually_exclusive=true + exhaustive=true + same_denominator=true` 时调 `table_total`；计数-百分比闭合复用现有 signal，不另造类型。这两类由表格图像/网格触发的 signal 进 `stage3_extraction_signals[]`，需把它们的 `produced_by` 条件从“只允许 stage_2”扩为 `stage_2 | stage_3`；Stage 3b 只合并 observation，不冒充统计脚本产出者。首批 fixture 覆盖基线多级表头、SAE participants/events 双分母、诊断 2×2 表、纵向失访后 n 变化和“分类不穷尽”负例。
- **代价**：2–4 人日；最小版只支持 HTML/JATS 表和已解析 PDF 网格，复杂无线表为后续增强。
- **建议优先级**：P1 应该做；交付前至少封闭 schema 并打通 `table_total` 一个竖切。
- **分期 / 归属**：一期（不调外部数据库）；Stage 3 Table Parser 产事实对象与无 severity signal，Stage 3b 合并 observation，M2/M4 才可产 finding。
- **契约字段**：新增封闭 `table_record` schema，复用 observation、evidence 和现有统计 signal；仅扩展两个现有 signal 的合法产出阶段，不新增第四类记录。
- **假阳性**：中。合并单元格、子组小计、多选项、participants 与 events、基线缺失值都会造成表面不守恒；三个前置布尔量不是全部有证据的 `true` 时只产 `partial_extraction` 或不运行，不产 mismatch。

## 未解决 / 需要人来定的问题

1. 是否接受 P1 的 `comparison_trace[]` 作为 Stage 3b 必填产物。建议接受；否则评委无法分辨组 status 是复算结果还是模型自由填写。
2. P2 是否与 Round 1 P3 的 `reported_value_text` 一次迁移。建议合并，不建第二个“原报告字符串”字段。
3. P3 在“阶段本地 delta + Stage 5 重映射”与“中央串行 writer”中需要拍板。建议前者；它才能保持并行且让 id 分配可复现。
4. P4 应先于 Round 12 P1 的 resolver 实现。当前 X1 核心 evidence/signal/limitation 契约已落地，但 connector 为零；本轮未重复 ClinicalTrials.gov、Europe PMC、GEO/SRA/PRIDE 和 UniProt/InterPro 提案。
5. `table_records[]` 是否在初筛前升为与 `figure_records[]` 同等的封闭契约。建议至少做 JATS/HTML 表 + `table_total` 竖切，这比再增一张通用审稿清单更有 uplift。
6. `SKILL.md` 仍为 600 行以上。Round 13 P1 已提逐节消融后精简，本轮不重复提案；在消融结果出来前不应凭主观删除安全契约。
7. Skill 目录当前含 `.DS_Store` 与 `scripts/__pycache__/*.pyc`，不属运行时必需文件；本轮允许修改清单不包含这些路径，故未删除。打包负责人应在严格 50 MB/10 MB 自查前从提交包排除，不得依赖本轮未授权修改的 `.gitignore`。
