# Round 7 · 对抗性审查：评委会怎么挑刺 提案

## 摘要

最伤的点不是规则不够多，而是当前没有统一执行入口与可复跑的 uplift artifact；评委无法证明四个确定性脚本真的进入了论文审核任务。
第二个硬伤是 `full_review` 默认可选，但 M2/M3 仍是骨架，M5 角色冲突与 M7 调度竞态也尚未按既有提案收敛；“六模块完整审核”目前属于超额承诺。
第三个硬伤是共享契约与评分已超过三千行，而最接近真实生物医学审稿的报告规范与实验方法规则仍未机器化；应停止继续扩 schema，先交付可执行的指南规则编译器。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `README.md` | 定位、仓库结构、语料、使用、合规自查、当前状态 | 将“替代人工”改为“自动化并辅助”；补列第 4 个运行时脚本；把校验数改为 140；明确 10 份 PDF 实际存在且不得入提交包；删除平台专属加载表述与无 artifact 的端到端成功声称；M5 改为已填充 v1、M2/M3 仍为骨架 | 原文可被仓库事实逐项反证，十分钟评审会直接判为工程可信度不足 |
| `skills/biomed-paper-review/SKILL.md` | §0.2、§2.9 | 把“已实现离线流程”收敛为“已定义流程 + 四项独立脚本”；删除 Skill 外部的 proposal / architecture 运行时引用 | 当前没有统一执行器，且自包含 Skill 不应依赖包外文档才能解释运行边界 |
| `scripts/sequence_identifier_audit.py`、`schemas/extraction_signal.schema.json`、`references/00-contracts.md` | signal id、HGVS 分支、signal 契约 | 将非法 `SIG-S01` 改为 `SIG-001`；新增 `hgvs_syntax_unresolved`，复杂但可能合法的 HGVS 表达式只作人工候选；补 schema 与自检 | 旧脚本产物不能通过自己的 id schema，还会把“解析器未覆盖”冒充确定性语法错误 |
| `references/01-structured-extraction.md` | §14 | 区分已实现的本地格式/序列检查与未实现的外部真实性核验；删除当前 enum 不接受的 `identifier_verification` JSON 示例；改为一期可选联网增强 | 旧示例无法通过声明的 schema，且“只抽取、不核验”与已交付序列脚本矛盾 |
| `references/04-statistics.md` | §3、§4、§9、§10、§12 | 禁止用 `p>0.05` 宣称“确认正态”；未报告正式正态性检验不再自动 major；`wrong_test` 默认 major、只有改变主要推断才升 critical；补 Mann-Whitney 的解释边界；后续能力不再按网络/时限推到二期 | 旧规则会系统性误报，并把配对数据按独立分析这种常见但未必改变结论的问题机械标成 critical |
| `references/06-ethics-compliance.md`、`resources/ethics_rules.json` | §2、§4、§6、§8；四条核心规则 | `not_reported` 只证明报告缺口，伦理批准/知情同意/动物批准/人源材料授权默认 major；只有明确未获授权且规则适用时才升 critical；外部核验改为一期联网增强 | “稿件没写”不等于“研究未获批准”；旧 severity 有名誉与合规误伤风险 |
| `references/07-conclusions-discussion.md` | 开头、§5.7、§6、§8、§11 | 把旧二期表述改为当前未实现的一期增强；删除 `created_by: M7` 的非法 external evidence 示例，并明确 M7 不得创建外部证据 | 外部证据尚无 schema 与唯一产出者，旧例违反证据血缘并夸大已交付能力 |

## B 类提案

### P1 · 攻击面 #1：确定性后端统一入口与可复跑任务轨迹

- **问题**：四个 `scripts/*.py` 只有 Python 函数与 `--selftest`，没有一个接受 Stage 2 标准 JSON、执行全部适用工具、合并合法 signal 并装配报告的统一入口。四个 `tools/fixtures/*.json` 是手工契约实例，不是从论文输入跑出的结果；仓库也没有同一官方模型下 skill / no-skill 三次运行的可核验轨迹。Round 6 P1 已定义完整评测指标，但尚未解决“工具如何真正挂入一次审核”的执行断点。
- **影响**：这是 30% 可完成性与工程质量、14% Skill 复用价值以及 uplift 消融的共同致命点。评委可以合理判断四个脚本只是旁置 demo，官方模型执行 Skill 时仍主要依赖自由文本推理，uplift 接近 0。
- **方案**：**一期离线**新增 `skills/biomed-paper-review/scripts/run_deterministic_checks.py`，输入固定为 `{run_id,evidence_registry,structured_result_v1,statistical_claims[],sequence_items[],execution_scope}`，先校验所有输入 evidence ref，再按适用性调用单位归一化、统计取证、伦理筛查与序列审计，输出只允许 `m1_extraction_signals[]` 与工具执行轨迹，禁止 finding。再新增 `scripts/assemble_review_report.py`，只负责 Stage 3b 后的数组合并、聚簇、三项分数复算和模板渲染；任何不合法中间产物 fail closed。两个入口都支持 `--input`、`--output`、`--offline`、`--selftest`，路径按 `__file__` 或 CLI 参数解析。Skill 的 Stage 2 指令必须明确调用统一入口，禁止让模型手抄脚本算法。新增三个包内 smoke case：M4 的 p/计数不一致、M6 的补充材料不可得、M3 的 HGVS 复杂表达式；每例保存输入、工具输出和预期 schema path。官方模型的 uplift 运行沿用 Round 6 P1 的指标与三次中位数，不重复造评测口径，只新增可复跑命令、stdout/stderr、模型版本、prompt hash、skill hash 和结果 hash artifact。
- **代价**：2–3 人日；1 人日统一适配四个脚本，1 人日装配器与三个 smoke case，0.5–1 人日记录官方模型三次对照。标准 Draft 2020-12 校验依赖 Round 5 P5；其落地前可先用现有 validator，但不得称为完整 JSON Schema 验证。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期离线；Stage 2 工具后端 + Stage 5 装配器，不新增审核模块。M1/工具层仍不产 finding。
- **契约字段**：扩展顶层非记录对象 `execution_trace:{run_id,skill_hash,model_id,tool_runs[]}`；`tool_runs[]` 元素固定为 `{tool,tool_version,status,input_sha256,output_sha256,started_at,ended_at}`。现有 `m1_extraction_signals[]`、`evidence_registry`、三类记录与 finding 契约不变。
- **假阳性**：低。统一入口只产 signal；脚本前提不满足时输出 `partial_extraction` 或跳过。M4/M6/M2/M3 必须回查稿件证据后才可立 finding，工具异常只产 `system_limitation`。

### P2 · 攻击面 #2：能力就绪门禁，禁止把骨架模块算作 full review

- **问题**：`SKILL.md` 默认 `full_review` 并要求 M2–M7 全部运行，但 M2/M3 明写“骨架—待填充”；M5 的 Parser/Reviewer 产出者冲突尚未按 Round 5 P1 修复；M7 又要求消费 M2–M6 findings，与“六模块并行”冲突，Round 2 P6 的两波屏障尚未实现。当前 schema 只检查 `executed_modules` 是否列满六项，不检查这些模块是否具备可执行规则，因此把模块名写进数组就能得到 `partial:false`。
- **影响**：评委只需打开三个 reference，就能证明“完整审核”并不完整；更坏的是 skeleton 模块可能返回空 finding，被误读成“未发现问题”。这会同时损伤领域理解、工程质量和科学可信性。
- **方案**：**一期离线**新增 `resources/capability_manifest.json`，为 M2–M7、Figure Parser、四个确定性工具登记 `{status,rule_version,required_inputs,produces,depends_on,tests,last_verified_at}`；`status` 仅允许 `ready/conditional/skeleton/disabled`。Stage 1 前的执行规划器冻结 `capability_snapshot_hash`：只有所有 M2–M7 为 `ready`、M5 职责冲突已按 Round 5 P1 关闭、M7 依赖已按 Round 2 P6 建立屏障时，才允许 `effective_mode=full_review`。否则保留 `requested_mode=full_review`，将可运行模块按 targeted partial 执行，未就绪模块写入 `skipped_modules[]`，产 `stage_1 system_limitation: module_not_ready`，风险分必须 `partial:true`。validator 反向检查 manifest 与 `executed_modules[]`，禁止 skeleton/disabled 模块计作已执行。
- **代价**：1–1.5 人日；manifest 与门禁 0.5 人日，schema/validator/fixtures 0.5–1 人日。M2/M3 规则填充本身另计；M5 与 M7 的具体修复分别依赖其负责人接受 Round 5 P1 与 Round 2 P6。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期离线；执行规划层，不新增 M1–M7 模块。
- **契约字段**：扩展 `execution_scope` 为 `{requested_mode,effective_mode,capability_snapshot_hash}`，保留现有 `mode` 一个迁移版本后删除；`system_limitation.category` 增 `module_not_ready`。`capability_manifest` 与 `execution_scope` 都不是第四类记录。
- **假阳性**：不产生稿件 finding。代价是暂时少报问题而非误报；所有未审核维度显式列入系统限制与 skipped modules，禁止把“没跑”展示成“没问题”。

### P3 · 攻击面 #3：设计路由驱动的生物医学报告规范编译器

- **问题**：当前共享契约、M1、M4、M6、M7 合计超过三千行，但 M2/M3 的核心仍是 TODO。评委会认为团队优先设计了复杂分数和 schema，而没有把 CONSORT、STROBE、PRISMA、ARRIVE、STARD、TRIPOD+AI、MIQE 等真实审稿清单编译成可执行规则；这正是“复杂到没人实现”的典型过度设计。现有 M4 §6 只有规范索引，不能对条目适用性、检索范围与缺失证据做机器判定。
- **影响**：裸模型本来就能给出“建议补充随机化、盲法和样本量”等泛化意见；没有版本化规则 id、设计适用性与 absence 证据，Skill 无法证明这些意见来自确定性规则而非模型常识。M2/M3 继续为空还会让 full review 的最大两个领域面失真。
- **方案**：**一期离线**新增 `resources/reporting_guidelines.json` 与 `scripts/reporting_guideline_check.py`。规则对象固定为 `{guideline_id,version,item_id,article_types[],design_types[],predicate,required_fields[],searched_locations[],search_terms_zh[],search_terms_en[],consumer,severity_ceiling,citation}`；首批只做七个高收益垂直切片：CONSORT 的随机序列/分配隐藏/盲法/受试者流，STROBE 的混杂与缺失数据，PRISMA 的检索日期/完整检索式/筛选流程，ARRIVE 的实验单位/随机化/盲法/排除标准，STARD 的参照标准与阈值预设，TRIPOD+AI 的数据拆分/外部验证/校准，MIQE 的引物序列/扩增效率/阴性对照。脚本只在 `article_type + design_type + predicate` 全部确定时运行；字段 `not_reported` 必须附满足规则词表的 absence evidence，随后产 `reporting_requirement_unmet` signal。M2/M3/M4/M6 根据科学影响立 finding；单纯报告遗漏不得自动写成“实验未做”。规则库只保存条目 id、必要字段的释义与来源链接，不复制受版权保护的整份清单。
- **代价**：2–4 人日；1 人日定义 25–35 条最小规则，1 人日脚本与 schema，1–2 人日由模块负责人复核正反例。先覆盖现有 10 篇语料实际出现的设计，不追求一次穷尽所有指南。
- **建议优先级**：P0 交付前至少完成 CONSORT + ARRIVE + MIQE 三个垂直切片；其余 P1
- **阶段 / 归属**：一期离线；Stage 2 工具层产 signal，主消费者为 M2/M3，M4/M6 只消费各自条目。不新增审核模块。
- **契约字段**：`extraction_signal.type` 增 `reporting_requirement_unmet`，条件必填 `reporting_rule:{guideline_id,version,item_id,predicate_result,required_field_refs[],search_scope_complete,rulebase_version}`；`structured_result.meta` 增 `article_type`，`article_design` 继续提供 design 路由。三类记录不变。
- **假阳性**：中。期刊体例、研究类型与指南版本错配会制造误报；`article_type` 或 predicate 不确定时只产 `partial_extraction`，不产 unmet signal。未报告默认 severity 上限为 `minor`，只有影响复现、偏倚判断或主要终点解释时由审核模块升 `major`；仅凭清单缺项不得 `critical`。

## 未解决 / 需要人来定的问题

1. 是否在初筛前停止宣称 `full_review` 可用，直到 M2/M3 从 `skeleton` 升为 `ready`、Round 5 P1 的 M5 职责冲突与 Round 2 P6 的 M7 屏障落地。建议接受 P2；否则 README 与 Skill 必须只展示已支持的 targeted 模式。
2. Round 6 P1 的双人金标准与三次 uplift 仍未实现。P1 只补统一执行与可复跑 artifact，不替代领域标注；没有 gold 时不得用“输出更长、finding 更多”证明 uplift。
3. Round 4 P1 的 X1 外部证据层仍未落地；四个确定性脚本迁入 Skill 的子项已采纳，`external` evidence、失败降级与 `external_validation_coverage` 尚未采纳。连接器不得各自绕过该前置。
4. Round 1 P2/P3 已采纳并实现为单位归一化和四类统计取证；Round 3 P4 已部分实现为序列/标识符离线审计。本轮修复了序列 signal id 与 HGVS 子集误报，但“引物对参考转录本比对”仍未实现。
5. Round 5 P5 的标准 Draft 2020-12 引擎尚未落地；当前 140 项标准库 lint 不能证明十份 schema 的完整标准语义。建议初筛前完成，不要把“JSON 可解析 + 定向 lint”称为完整 schema validation。
6. Skill 包内仍有 `skills/biomed-paper-review/.DS_Store`。该路径不在本轮允许修改清单内，未删除；提交打包前应移除并用显式文件清单生成压缩包。
7. 是否接受 P3 的 `article_type` 字段。若不接受，指南适用性无法与 `design_type` 分离，例如 trial protocol、brief report、secondary analysis 会被主研究报告规则误伤。
