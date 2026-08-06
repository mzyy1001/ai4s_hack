# Round 13 · Uplift 差异化审查 提案

## 摘要

当前默认流程仍包含一遍接近裸模型基线的 Stage 0 自由审稿，以及 M2/M3 骨架、M5/M7 常识性清单；这些内容会增加上下文、候选问题和报告篇幅，却没有证据证明带来增量真阳性。
本轮直接接通了第 5 项统计取证 `table_total_mismatch`：修复非法 signal id，补齐 M4 消费门、severity、示例和校验器真实执行，避免已写好的确定性能力在审核链中失效。
最应强化的三件事依次是：**确定性工具的适用项执行覆盖、与原始资产绑定的证据链、X1 权威记录对账**；三者都能产生裸模型无法稳定给出的可复算 artifact。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/scripts/statistical_forensics.py` | `check_table_total()` | 默认 id 从非法的 `SIG-F05` 改为 `SIG-105` | 直接调用该函数时旧输出违反 `^SIG-[0-9]{3,}$`，第五项取证无法进入合法 signal 流 |
| `tools/validate_schemas.py` | signal 枚举与工具实跑 | 真实执行 `table_total` 阳性；要求其携带 `forensics`；十五值文案与 Skill 内路径同步 | 旧校验器虽接受该枚举，却从未调用该分支，无法发现默认 id 和产物形状断裂 |
| `skills/biomed-paper-review/references/04-statistics.md` | §2、§9、§10.7 | M4 的确定性取证由四项补为五项；增加互斥/穷尽/同分析集门控、finding slug、severity 算法与正反例 | 脚本已经检测表格合计错误，但 M4 没有消费规则，signal 会被静默搁置 |
| `skills/biomed-paper-review/SKILL.md` | §0.2、§6.5、资源索引 | 统计能力补入表格合计；增加必跑触发条件；要求从 Skill 根目录解析相对路径；把未定义的 `screen(sr)` 改为可执行示例 | 旧主文少报一项 uplift，且伦理示例直接运行会 `NameError`；工作目录不明确也会让模型只读脚本不执行 |
| `skills/biomed-paper-review/references/00-contracts.md` | §6.2、§11 | signal 数量从十四改为十五，并明确五种统计取证 signal 的产出者 | 表中实际已有十五项，“后四种”还错误指向表尾的伦理/序列/图像/X1 项 |
| `skills/biomed-paper-review/references/01-structured-extraction.md` | §9 | 全局 signal 数量从十一改为十五 | M1 文档的契约导航已落后于 schema，容易让实现者丢弃合法工具 signal |
| `skills/biomed-paper-review/schemas/extraction_signal.schema.json` | `type.description` | 枚举说明从十四值改为十五值 | schema 的实际 enum 与说明不一致 |

## B 类提案

### P1 · 逐节组件消融门禁：删除“只让模型多说一遍”的默认上下文

- **问题**：Round 6 P1 已提出整体 skill/no-skill 三次 uplift，但没有回答“Skill 内哪个组件贡献 uplift”。当前 `SKILL.md` 600 行，超过建议的 500 行；`00-contracts.md` 与 `01-structured-extraction.md` 合计 2,149 行。更关键的是 `SKILL.md §2.0` 明令先做一遍自由文本专家通读，并列出“裸模型也该看出来”的问题；M2/M3 仍是骨架，M5/M7 又包含大量通用审稿常识。若这些段落只增加 finding 数和输出字数，整体 uplift 会被稀释。
- **逐节审查结论**：

  | 文件 / 位置 | 裸模型本来会做什么 | Skill 的非基线增量 | 保留判断 |
  | --- | --- | --- | --- |
  | `SKILL.md §0.1` | 会引用原文，但经常给不精确页码或补造缺失引文 | 三型证据、首锚点、ref 可解析和失败即丢弃 | **保留核心规则**；这是差异化，不是普通提示 |
  | `SKILL.md §1、§2.1–§2.10` | 会按章节“分析一遍” | 阶段依赖、唯一产出者、v1/v2、M1 不产 finding、X1 降级 | **保留流程骨架，压缩重复解释**；细节只留在 `00/01` |
  | `SKILL.md §2.0` | 自由列问题正是裸模型基线 | 当前只多出候选清单，没有独立算法或新证据 | **必须做独立消融**；若不增加经取证真阳性，移出默认流程，改为“工具与规则完成后的漏项复核”或仅在 targeted fallback 启用 |
  | `SKILL.md §3–§5` | 能理解 evidence、字段状态和常见评分描述 | 精确枚举、状态机和公式来自契约 | **只保留不可违反的短表**；公式、示例和迁移细节只在 `00-contracts.md`，避免双份 prompt |
  | `SKILL.md §6`、`templates/review_report.md` | 会写长审稿报告 | 固定排序、partial 警示、证据展开和三类记录分栏 | **保留机器稳定性，压缩空内容**；空节只渲染一行状态，不重复 limitation/signal 解释 |
  | `SKILL.md §6.5` | 不会稳定逐项复算或做像素搜索 | 五个确定性脚本及 fail-closed 输出 | **P0 保留并强化**；默认流程必须证明实际运行 |
  | `references/00-contracts.md` | 不会自行保持全稿 id、状态机、聚簇和评分可复算 | 本项目最强的可审计基础设施 | **保留**；把“为什么”段和重复示例移出运行时热路径，schema/validator 成为规范源 |
  | `references/01-structured-extraction.md` | 会抽 population/design/outcome | 三维度字段、条件路由、pending 生命周期、观测组与 Stage 3b 合并 | **保留状态机与路由**；字段释义和已完成 TODO 不应进入每次运行上下文 |
  | `references/02-macro-logic.md §2` | 会指出章节缺失、逻辑跳跃、术语不一 | 尚无机器规则；§2.3 数据泄漏也只是待填清单 | **当前不应计作 ready 或 uplift**；禁止本轮修改，交负责人按 Round 7 P2/P3 完成规则与能力门禁 |
  | `references/03-experimental-methods.md §2` | 会建议对照、随机、盲法、剂量和重复 | 尚无 assay 最低要素库或可执行惯例分布 | **当前不应计作 ready**；尤其“动物是否必要”主观性高，未有规则前只交人工，不进入自动高 severity |
  | `references/04-statistics.md §3–§8` | 最新通用模型通常知道 t/ANOVA/χ²、多重比较和效应量常识 | §2.1 的绑定门、五项复算、伪重复层级与 severity 升级条件 | **保留取证门和困难边界**；按 outcome/design 只加载命中的表行，不能每稿注入整张统计教科书 |
  | `references/05-figures-and-charts.md A.2/B.2–B.4/C` | 会给“补坐标、误差棒、比例尺、图注”的常规意见 | 当前差异化实际来自独立图像脚本，不来自这些清单 | **通用清单降为按图型加载**；`A.1/A.5/D/F.5` 的角色冲突沿用 Round 5 P1，禁止本轮修改负责人文件 |
  | `references/06-ethics-compliance.md` + `resources/ethics_rules.json` | 会提醒伦理批准/知情同意 | 法域、版本、条款、反向豁免、`parse_failed ≠ 缺失` 和 severity ceiling | **P0 保留**；这是规范库型 uplift。Round 10 P1 要素级记录未实现前，不宣称已核对批件子要素 |
  | `references/07-conclusions-discussion.md §3–§5` | 会指出因果越界、过度外推、不显著误读和局限不足 | evidence/claim tier 矩阵与下层 finding 降级较稳定 | **保留矩阵，压缩措辞词表与重复例子**；`discussion_hollow`、`limitations_evasive` 等低确定性项只在影响核心 claim 时进主报告，否则放 P2 折叠区 |

- **影响**：不做组件消融，评委只能看到“挂 Skill 后输出更多”，无法证明多出的内容更正确；Stage 0、骨架模块和空报告节还会占用官方模型上下文与输出预算，使确定性 signal 被淹没。最坏情况下，Skill 因结构化约束漏掉自由发现，又因通用清单制造更多低价值 finding，整体 uplift 为负。
- **方案**：**一期离线评测基础设施**，扩展 Round 6 P1，不另建第二套 gold：同一论文、同一官方模型、同一输出上限、各 3 次，增加六个组件臂：`bare`、`generic_review_only`（Stage 0 + M2/M3/M5/M7 常识项）、`contract_only`、`deterministic_only`（契约 + 五脚本）、`deterministic_plus_ethics_rulebase`、`full_skill`；首个 X1 connector 落地后再加 `full_skill_plus_x1`。逐论文报告：经裁决 finding precision/recall、正确 locator 率、absence 检索可复核率、确定性适用项执行率、外部原子事实正确率、人工复核队列长度、重复 finding 数和每千输出 token 的经裁决真阳性。某节若中位数不增加任何正确 finding/证据定位/安全降级，且增加 token 或误报，只能移出默认热路径；安全声明和三类记录边界不参与删除判断。结果写 `tools/fixtures/uplift-ablation/` 与 `tools/evaluate_uplift_components.py`，不改 `datasets/**`。
- **代价**：2–3 人日工程，另需 Round 6 P1 的双人标注；先在 4 篇覆盖 RCT、动物、组学、显微/流式的语料完成最小版，再扩到 10 篇。GLM/Kimi 各自记录模型版本，不用某一家模型的工具调用习惯作结论。
- **建议优先级**：P0 交付前必须做最小版；这是决定删哪些 prompt 的唯一可靠依据。
- **阶段 / 归属**：一期离线；评测基础设施，不属于 M1–M7。生产流程暂不新增阶段。
- **契约字段**：生产契约不改；测试 artifact 新增 `component_arm`、`input_token_count`、`output_token_count`、`adjudicated_true_findings[]`、`unsupported_findings[]`、`locator_accuracy`、`deterministic_applicability_coverage`。沿用 Round 6 的论文级 bootstrap 与三次中位数。
- **假阳性**：不产生稿件判断。风险是把审稿者偏好当 gold；只标“事实是否成立、证据是否定位正确、是否改变人工 triage”，保留分歧，不用接收/拒稿作为真值。

### P2 · 确定性适用项覆盖账本：让“脚本存在”变成“每个该跑的检查都跑了”

- **问题**：本轮修复的第五项统计取证暴露了真正断点：脚本、schema、M4 三者任一未接线，确定性能力就对最终报告贡献为零。Round 7 P1 已提出统一执行入口和 `tool_runs[]`，但它只能证明某个脚本启动过，不能证明论文中每个适用的 p/df、计数-百分比、GRIM 均值、互斥分类表、单位对、序列项和可读图像都被覆盖。
- **影响**：模型选择性调用一两个 demo 就能声称“已运行工具”，漏检率无法计算；评委的真实任务若没有恰好命中示例输入，uplift 仍接近零。工具异常若静默跳过，还会把“没检查”伪装成“没问题”。
- **方案**：**一期离线**扩展 Round 7 P1 的 `run_deterministic_checks.py`，不另建平行入口。Stage 2/3b 先生成封闭 `check_inventory[]`，每项为 `{check_instance_id,check_type,target_refs[],evidence_refs[],applicability,applicability_basis,status,tool_version,signal_refs[],limitation_refs[]}`；`status` 只允许 `executed_no_signal/executed_signal/skipped_not_applicable/blocked_missing_input/tool_failed`。适用性分母按对象而非脚本计数：一篇有 30 个 `statistic+df+p` 就必须登记 30 项。`blocked_missing_input` 产 `partial_extraction`，`tool_failed` 产 `system_limitation`；两者都不得变 finding。Stage 5 新增非记录 `deterministic_check_coverage={applicable,executed,blocked,failed,by_check_type[]}`，并列出所有未执行 id；报告首屏只在 `blocked+failed>0` 时给一行限制，不倾倒全账本。
- **代价**：1.5–2 人日；依赖 Round 7 P1 统一入口。先覆盖五项统计、单位、序列和图像四组适用性枚举；伦理筛查以命中的 rule id 为实例。每类至少一个“应跑未跑”负例。
- **建议优先级**：P0 交付前必须做；它是最能拉开差距的第 1 项强化。
- **阶段 / 归属**：一期离线；Stage 2/3/3b 工具层 + Stage 5 聚合，不新增审核模块。M1 与工具仍不产 finding。
- **契约字段**：扩展 `execution_trace`（Round 7 P1）并新增非记录 `deterministic_check_coverage`；三类记录不变。若暂不采纳 `execution_trace`，账本可先作为运行 artifact，正式报告不得伪填。
- **假阳性**：低；账本不判断稿件。主要风险是适用性误判导致无意义运行；前提不全统一记 `blocked_missing_input`，不允许工具猜默认分母、尾数、量表或图像语义。

### P3 · 原始资产绑定的证据验证器：证明 quote 与 locator 真的来自该稿件

- **问题**：现有 `evidence_registry` 能检查 ref 唯一、字段齐全和 absence 形状，却不能证明 `present.quote` 确实出现在 locator 指向的 PDF/JATS，也不能证明 `searched_locations[]` 真被检索。一个模型完全可以生成格式合法但页码错误的 quote；这会让最有差异化价值的“可审计证据链”退化为漂亮 JSON。Round 8 P3 提出页内证据图谱，本项只补其前置的确定性真实性门，不重复 UI/裁片方案。
- **影响**：评委抽查两条 finding 即可击穿证据可信性；错误页码和模型改写的“近义 quote”会同时损失 25% 科学可信性与 30% 工程质量。absence 尤其危险：只写检索词而没有执行轨迹，仍可能把解析失败归责作者。
- **方案**：**一期离线**新增 `scripts/verify_evidence_registry.py`。Stage 1 为每个输入资产登记 `{artifact_id,media_type,sha256,page_count_or_xml_root,normalizer_version}`；present evidence 增 `{artifact_ref,content_sha256,match_mode}`，`match_mode` 只允许 `exact_text/normalized_text/ocr_region/visual_region`。验证器按 locator 回到 paragraph/XML node/page bbox，核对 quote；允许 Unicode/空白规范化，但禁止语义改写。OCR/visual 证据必须保存 bbox、裁片 hash 与 OCR 置信度，仍按现有 confidence 上限处理。absence evidence 增 `search_run_ref`，指向 `{artifact_refs[],locations[],terms[],normalization,match_count,ambiguous_match_refs[],engine_version}`；`no_match` 只有全部声明范围成功读取且 `match_count=0` 才合法。定位失败、资产 hash 不符或范围未读全产 `system_limitation`，对应 finding 丢弃，不增加 manuscript risk。Stage 5 在渲染前强制运行；非零退出禁止输出“审核完成”。
- **代价**：2–3 人日；文本/JATS exact/normalized 先做 1–1.5 人日，PDF OCR region 与图像裁片 hash 再做 1–1.5 人日。与 Round 8 P3 共用 artifact/坐标，不另建第二套定位对象。
- **建议优先级**：P0 先交文本/JATS/PDF 文本层；OCR/visual 为 P1 一期离线。它是最能拉开差距的第 2 项强化。
- **阶段 / 归属**：一期离线；Stage 1 资产登记 + Stage 5 输出门禁，不属于 M1–M7。
- **契约字段**：扩展 `normalized_document.asset_registry`、present evidence 的 `artifact_ref/content_sha256/match_mode`、absence evidence 的 `search_run_ref`；这是现有 evidence 与非记录运行轨迹扩展，不新增第四类记录。
- **假阳性**：不立稿件 finding。双栏 PDF、连字、公式和 OCR 会造成定位假失败；先尝试 exact，再尝试仅空白/Unicode 规范化，仍失败就降级为 `system_limitation` 并交人工，绝不把近义文本当 exact quote。

### P4 · 只交付一个 X1 垂直切片：ClinicalTrials.gov 当前记录三向对账

- **问题**：Round 12 已完整提出 X1 resolver 与四组 connector，本轮不再重复数据库清单。当前硬伤是契约已经落地、connector 仍为零；若周日前继续扩文档，外部核验在 uplift 评测里仍是 0。首批同时做多个浅 connector 会消耗时间，却没有一个能从稿件事实走到 external evidence、signal、M2/M4/M6/M7 finding 和失败降级。
- **影响**：外部权威记录是最能拉开差距的第 3 项，但“API 能返回 JSON”不等于生物医学审稿能力。临床试验中 endpoint role、time frame、arm、analysis population、participants/events 任一错配都会制造严重假阳性；只验 NCT 格式又没有足够 uplift。
- **方案**：**一期联网增强**，直接采纳 Round 12 P1 + P2 + P5 的最小垂直切片，不另造字段或入口：① `external_evidence_resolver.py` 只先启用 `clinicaltrials_gov`；②精确 NCT 取当前 API v2 记录与 `/api/v2/version`；③对账 `studyFirstSubmitDate vs startDate`、主要终点 `role+measure+timeFrame`、同 `arm+population+units` 的主要结果 `estimate+CI+p`；④所有语义键完全相等才允许 `mismatch`，否则 `not_comparable`；⑤ 403/429/5xx/白名单/结构漂移只产 X1 limitation；⑥同时落地独立 `external_validation_coverage` 和录制响应回归。验收用 6 个有 posted results 的 NCT：至少覆盖 ITT/PP 不同、participants/events 不同、当前记录晚更新、晚注册候选、精确数值一致和 API 失败。只有贯通此切片后再做 Round 12 P3/P4 的 Europe PMC、GEO/SRA/PRIDE 与蛋白坐标。
- **代价**：3–4 人日，沿用 Round 12 估算；不需要 GPU。若白名单尚未批准，先用录制响应完成全链回归，在线失败仍不得阻断离线流程。
- **建议优先级**：P0 交付前完成 NCT + 注册时序 + 主要终点；estimate/CI/p 三元组为 P1 一期联网增强。不要在此切片完成前新开第五种 connector。
- **阶段 / 归属**：一期联网增强；X1 取证，M6 判断注册时序，M2 判断终点/受试者流，M4 判断统计数值，M7 判断核心 claim 是否依赖差异。X1 不产 finding。
- **契约字段**：复用已落地 `external` evidence、`external_validation_candidate` 与 X1 limitation；采纳 Round 12 P5 的非记录 `external_validation_coverage`。若需要封闭语义键，只扩展 `external_check.comparison_context`，不重构三类记录。
- **假阳性**：高。当前注册记录不是投稿时历史版本；晚提交只是候选，不能自动写伦理违规。arm、time frame、analysis population、units、endpoint role 任一不等即交人工；网络失败和零命中不影响三项现有评分，也不成为稿件问题。

### P5 · 通用审稿项的“信息预算”与主报告降噪

- **问题**：`discussion_hollow`、`limitations_evasive`、`redundant_presentation`、术语/图注类 finding 很容易被裸模型生成，且 `info` 不进风险分，却仍占据第四、第五、第八节和审稿人注意力。`SKILL.md §2.0` 还要求“全部列出”候选并解释丢弃原因，可能把未证实的自由联想转成 system limitation 或人工复核项；system limitation 本应只描述系统能力，不应承载“候选没有证据”的理由。
- **影响**：输出更长但核心风险更难找，正是 uplift 规则明确惩罚的行为；把被证伪候选写入 system limitation 还会污染三类记录边界。评委可能看到几十条 P2/info，却找不到 p 值硬错、批件缺项或注册终点差异。
- **方案**：**一期离线输出策略**，以 P1 消融结果拍板：① `candidate_rejected` 只进内部 execution trace，保存 `{candidate_id,reason,evidence_search_refs[]}`，不进三类记录和用户报告；②主报告默认只展开 P0/P1、影响核心 claim 的 P2、全部 system limitation；其余已成立 minor/info 按 category 给计数并可展开，不能删除 JSON canonical 记录；③每个 cluster 只给一次 detail、一次证据并集和一次动作，禁止在摘要/发现/计划三处重复长段；④空节保留标题以兼容模板，但固定一行状态；⑤以“经裁决真阳性/千输出 token”和人工找到最高优先级问题的时间作为降噪验收，不设任意 finding 数上限。
- **代价**：1–1.5 人日；修改 `SKILL.md §2.0/§6`、模板与渲染器。依赖 Round 8 P1 的真实渲染器；在其未实现前只能定义快照，不能声称已降噪。
- **建议优先级**：P1 应该做；先完成 P1 最小消融，避免凭主观删除有用内容。
- **阶段 / 归属**：一期离线；Stage 0 内部轨迹 + Stage 5 渲染，不属于新的审核模块。
- **契约字段**：JSON canonical 的 finding 不删；`execution_trace` 可扩 `rejected_candidates[]`，模板增加折叠投影规则。`system_limitation` 不新增“无法取证候选”类别。
- **假阳性**：不新增判断。风险是折叠真正重要的 minor；凡影响主要终点、伦理授权、数据完整性或被人工标 P0/P1 的项强制展开，机器可读 JSON 始终保留全量。

## 未解决 / 需要人来定的问题

1. 是否接受用 P1 的组件级消融决定 Stage 0 去留。建议接受；在没有数据前不直接删，但不得继续把“裸模型再读一遍”宣称为 uplift。
2. 是否批准 Round 7 P1 的统一执行入口与本轮 P2 的适用项账本一起落地。建议合并实现；只做 `tool_runs[]` 仍无法证明每个适用对象被检查。
3. 是否接受 present evidence 绑定输入资产 hash、absence 绑定实际 search run。建议接受；否则“可审计”只能证明 JSON 自洽，不能证明证据真实来自稿件。
4. X1 首个切片选 ClinicalTrials.gov 还是 Europe PMC。建议 ClinicalTrials.gov：字段更能体现生物医学专业度；若只剩不足 2 人日，则改做 Europe PMC 撤稿状态 + GEO/SRA 精确 accession，但不得两个都做成浅 demo。
5. M2/M3 是否在 capability manifest 落地前继续计入 `full_review`。建议不计；两文件明确标为骨架。受禁改约束，本轮只记录，未修改负责人文件。
6. M5 负责人需处理 Round 5 P1 的 Parser/Reviewer 冲突，并把已实现的 `figure_integrity_audit.py` 从旧“二期”叙述接回 Stage 3 signal；本轮未修改禁改文件。
7. `SKILL.md` 是否以 500 行为硬门禁。建议不机械按行数删规则，而以 P1 消融决定热路径；但默认正文应低于 500 行，详细公式、示例、TODO 和模块表只按需加载。
8. Round 6 P1、Round 7 P1/P2、Round 8 P1/P3、Round 10 P1、Round 11 P1/P2/P7、Round 12 P1/P2/P5 均已有直接依赖，本轮没有重复提出第二套 runner、图像算法或 external schema；应冻结新提案数量，转入实现。
