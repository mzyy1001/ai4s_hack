# Round 18 · M1 抽取规则的可执行性 提案

## 摘要

§5.3 使用的字段名均能在 §5.1 / §5.2 找到定义，24 个 `design_type` 也都有默认、族级、专门或组件级落点；真正会导致多实现分叉的是条件谓词此前没有 `true / false / unknown` 出口，以及 `arms[]` / `claims[]` 仍没有字段三维度。
`mixed` 的主端点归属、`other` 的已排除分类轨迹和五键 `grouping_key` 的人群/亚组/分析模型上下文仍未落地，分别对应 Round 3 P2/P3 的未采纳项，本轮不换名字重复建设。
最紧急的新契约缺口是视觉 pending 的双重状态机：`extracted_field.unresolved` 可以收敛为 `not_reported`，空 `key_data.pending_visual_resolution` 却没有对应合法 v2 出口；建议以显式视觉解析请求账本替代空观测组占位。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/01-structured-extraction.md` | §3.2 | 把不存在的“设计判为 `applicability_uncertain`”改为对 `primary_design.status="ambiguous"` / `alternatives[]` 逐候选路由；只有候选结果不同时才把字段置为不确定 | `article_design` 没有 applicability 字段，旧指令无法执行，还会把候选间共同适用的字段一并降级 |
| 同上 | §5.3 条件执行语义 | 明确斜杠字段逐项物化、search scope 取字段定义与路由表并集、条件三值出口、未列设计回落优先级；给统计分析、缺失/失访、延迟参照标准、一级材料和病例干预五个谓词封闭判据 | 旧表只写“有……时适用”，没有规定条件为 false 或证据不足时怎么落状态；两个实现会给出不同覆盖率分母 |
| 同上 | §5.3.3、§5.3.5 | `case_control` 强制抽取对照来源/选择规则；病例报告/系列的 `primary_endpoint` 降为 recommended，`interventions` 改为按病例是否接受干预路由 | 旧规则漏掉病例对照最关键的 control selection，却要求纯自然史病例必须有干预和预设主要终点，都会制造确定性误路由 |
| 同上；`references/00-contracts.md` | §7.1；§4 示例 | 区分 `extracted_field.status="unresolved"` 与 `key_data.status="pending_visual_resolution"`；把不存在的 `key_results.ic50_compound_a` 改为合法路径 `objective.primary_endpoint` | 示例路径不属于 `structured_result`，且两个不同枚举被当作同一个状态使用 |
| `skills/biomed-paper-review/references/01-structured-extraction.md` | §13 TODO | 将单位归一化项标为已完成并指向 `scripts/normalize_biomed_units.py` | Round 1 单位归一化提案已采纳实现；旧 TODO 会诱导维护第二份单位表 |

## B 类提案

### P1 · 视觉解析请求账本：消除空 `key_data` 的 pending 死分支

- **问题**：当前有两套 pending。普通字段以 `status: "unresolved"` 等 Stage 3，图中确认没有该字段时可转 `not_reported + absence evidence`；数值观测组以 `status: "pending_visual_resolution"`、`observations: []` 占位，但 `key_data.status` 没有 `not_reported`，组级也没有 absence evidence 字段。于是 Stage 3 若确认 Fig 2C 不含预期 IC50，§7.4 要求的 `not_reported` 无法通过 `key_data.schema.json`；若删除空组又没有解析轨迹。Stage 3 未执行、输出停在 v1 时不死锁，pending 可合法留在 coverage；死锁发生在必须产 v2 且视觉来源确认无值时。
- **影响**：Stage 3b 只能违规保留 pending、伪装为 `parse_failed`、或静默删除组。三条路径分别违反 v2 lint、把稿件缺失伪装成系统失败、或破坏审计链，直接损失工程质量与证据可信性。
- **方案**：**一期离线**新增非记录 `visual_resolution_requests[]`，由 Stage 2 唯一产出、Stage 3/3b 消费。每项固定为 `{request_id,target_kind,field_path,metric_identity,target_grouping_key,requiredness,expected_sources[],cross_reference_evidence_refs[]}`；`target_kind` 只取 `extracted_field/metric_observation`。Stage 3b 必须为每项写 `visual_resolution_outcomes[]:{request_id,resolution,result_refs[],evidence_refs[],system_limitation_ref}`，`resolution` 只取 `observation_created/field_reported/confirmed_absent/ambiguous/parse_failed`。`metric_observation` 只有读到数值才创建 `key_data`；确认无值留在 outcome + absence evidence，不创建空观测组。迁移一个版本后从 `key_data.status` 删除 `pending_visual_resolution` 与空组 `parse_failed`，字段 pending 继续用现有 `unresolved`。修改 `00-contracts.md §4/§5`、`01 §6/§7`、`SKILL.md §2.6–§2.8`、`structured_result.schema.json`、`key_data.schema.json`、新增 `visual_resolution_request.schema.json`、fixtures 与 validator。
- **代价**：1.5–2.5 人日；需要 v1/v2 各两个正例及“图可读但无值 / 图不可读 / 图读出新组 / 图文冲突”四个收敛 fixture。无网络、无 GPU。
- **建议优先级**：P0 交付前必须做
- **分期 / 归属**：一期（不调用外部数据库）；Stage 2 M1 产请求，Stage 3 解析，Stage 3b 收敛；不新增审核模块，M1 仍不产 finding。
- **契约字段**：新增两个非记录数组，收缩 `key_data` 状态；扩展现有契约但不新增第四类记录。若团队拒绝迁移，次选是在 `key_data` 增 `not_reported + absence_evidence_refs[]`，但这会让“观测组”长期承载零观测，语义较差。
- **假阳性**：低。`confirmed_absent` 只有 `expected_sources[]` 全部成功解析且 absence evidence 覆盖这些来源时合法；任何面板缺失、低清或 OCR 失败只能 `parse_failed + system_limitation`，不得归责稿件。

### P2 · 正交设计修饰符：让同一叶子设计内部也能正确路由

- **问题**：24 个 `design_type` 都能落表，不代表路由足够。`randomized_controlled_trial` 同时包含个体平行、cluster、crossover、factorial、stepped-wedge 和 split-body；`case_control` 还可能是 matched 或 nested。它们对 washout、carryover、ICC、随机化单位、配对分析、交互项和对照选择的条件必填完全不同。继续扩叶子枚举会产生组合爆炸，单靠 `arms[]` 又无法区分“两个独立臂”和“同一受试者两个 period/两只眼”。
- **影响**：cluster RCT 会把 participant n 当独立样本，crossover 会漏掉 sequence/period/carryover，split-eye 设计会被按独立组审核，matched case-control 会漏掉 matching 与相应分析。此类错误会把 M1 的误路由放大到 M3/M4，并制造高风险伪重复 finding。
- **方案**：**一期离线**在 `article_design` 增 `design_modifiers`，不增加新的 primary design leaf：`allocation_structure ∈ {parallel,crossover,stepped_wedge,single_arm,not_applicable,unknown}`、`factorial_structure ∈ {present,absent,unknown}`、`allocation_unit ∈ {participant,cluster,litter,cage,animal,organ,well,field,other,unknown}`、`observation_unit` 同枚举、`repeated_measures ∈ {present,absent,unknown}`、`matching ∈ {none,individual,frequency,nested,unknown}`、`period_count`、`washout_reported`。每项带 `evidence_refs[]`。新增 `resources/design_modifier_routes.json`：crossover 触发 sequence/period/washout/carryover，cluster/stepped-wedge 触发 cluster count/ICC/cluster-adjusted analysis，factorial 触发 interaction，matched/nested case-control 触发 matching basis 与 matched analysis。修改 `01-structured-extraction.md §4/§5.3`、`structured_result.schema.json`、`04-statistics.md §3/§4`、fixtures 与 validator；M3 的消费规则只写入本提案，由其负责人修改禁改的 `03-experimental-methods.md`。若采纳 Round 9 P4 的 `sampling_hierarchies[]`，`allocation_unit/observation_unit` 改存其 ref，不建立第二棵层级树。
- **代价**：2–3 人日；先做 cluster、crossover、factorial、matched case-control 四条规则卡，各 3 个正例 + 3 个困难反例。无外部依赖。
- **建议优先级**：P1 应该做；P0 最小版先交 `allocation_structure + allocation_unit + observation_unit`
- **分期 / 归属**：一期（不调用外部数据库）；M1 抽取修饰符，M3/M4 消费，不新增模块。
- **契约字段**：只扩展 `article_design` 与 design-specific routed fields；可接入 Round 3 P1 的唯一规则源，不改变 finding / signal / system limitation 基础形状。
- **假阳性**：中高。`randomized` 不自动推出 allocation unit，多个时点也不自动推出 crossover。修饰符证据不足时必须为 `unknown` 并产 `partial_extraction`；`unknown` 只阻断专门规则，不允许推断为稿件方法错误。

## 未解决 / 需要人来定的问题

1. **Round 3 P1 尚未采纳**：`arms[]` 与 `claims[]` 仍是裸数组，无法保存 §5.3 已分配的 applicability / requiredness / status；`design_specific` 也可整体省略。建议直接采纳既有 `routed_collection + m1_routing_rules.json`，本轮新增的三值谓词作为规则输入，不再另建第二套路由器。
2. **Round 3 P2 尚未采纳**：`mixed` 的“没有单一组件承载全部 primary endpoint”仍不可复算，因为 `primary_endpoint` 没有 endpoint item 与 `experiment_refs[]`；`other` 也仍把“分类体系未覆盖”强制写成 `ambiguous_study_design`。建议采纳既有 `endpoint_items[] + classification_trace`，并把 taxonomy uncovered 与 extraction ambiguous 分开。
3. **Round 3 P3 尚未采纳**：五键 `grouping_key` 对总体/女性亚组、ITT/PP、调整/未调整模型、组织区室、归一化方式和作者分别报告的 batch 均会误合。建议直接采纳既有上下文扩展；关键上下文缺失时默认“不合组 + partial_extraction”，不得依赖当前的 `null == null` 自动合并。
4. `structured_result.schema.json` 的 v2 条件目前只机器禁止 `key_data.pending_visual_resolution`；普通 `extracted_field.status="unresolved"` 由 `tools/validate_schemas.py` 递归拦截，而不是 schema 自身拦截。是否接受 Round 3 P1 迁移时同步增加标准 Draft 2020-12 的 v2 resolved-field 约束，需要团队拍板。
5. Round 12 已采纳 X1 核心 evidence/signal/limitation 契约，connector 仍未交付；Round 12–15 已给 ClinicalTrials.gov、Europe PMC、GEO/SRA、HGNC/UniProt 等端点与映射。本轮不重复数据库清单，应先实现既有单一 resolver 垂直切片。
6. Round 1 的单位归一化、Round 11 的序列/图像候选器、Round 12 的 X1 核心契约与 Round 14 的 Skill 内 CLI 已实现；Round 3 的路由编译器、mixed 分类轨迹和扩展 grouping context 仍只有提案，不能在提交说明中写成已交付能力。
