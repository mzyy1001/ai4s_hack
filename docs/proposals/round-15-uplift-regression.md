# Round 15 · Uplift 回归 提案

## 摘要

历史实测仍是负 uplift：裸模型 15 条、挂 Skill 修正前 9 条且为真子集；修正后虽运行了脚本，差距仍未补平，而且指定的 `docs/uplift-baseline.md` 不存在，原始记录实际散落在 `docs/overnight-status.md`。
本轮把 Stage 0 提到主文首屏、阻止 rejected candidate 污染 `system_limitation`，并修复了 §6.5 复制即失败的路径初始化和名不副实的统计示例。
现有五个脚本与真实论文错误只部分对齐：已命中表格合计，尚未覆盖同一结果跨位置冲突和 claim—表格测量对象错配；下一步应补现有统计工具与回归门禁，不应再新增第六个旁置工具。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | 标题后执行入口、§2.0 | 在首屏固定“判模式 → Stage 0 → references/schema”的顺序；Stage 0 候选改为内部账本三态，只有真实能力限制才能进入 `system_limitation` | 原 Stage 0 位于第 169 行，模型可能先被模式/契约占满注意力；被证伪候选不是系统能力限制，也不应增加最终报告 token |
| `skills/biomed-paper-review/SKILL.md` | §6.5 | 增加仓库内可直接复制的 Skill 路径 preflight；把声称演示 `table_total_mismatch`、实际却调用 `count_percentage` 的示例改为真实 `12+18≠28` 输入 | 原命令在变量未赋值时立即失败，且示例没有执行历史负例对应的检查 |
| `tools/uplift_ab.py` | `metrics()` 与判读提示 | 把“执行过确定性脚本”改为“输出提及脚本（非执行证明）”，明确只有 execution trace 才能证明脚本生效 | 正则命中脚本名、`--selftest` 或一句说明都可能被旧指标误记为已执行 |

## B 类提案

### P1 · 把负 uplift 历史变成三次中位数、逐条裁决的回归门禁

- **问题**：`tools/uplift_ab.py` 每臂只运行一次，默认模型仍是 `openai/gpt-5.6-sol`，只统计条目数、locator 数、脚本名提及和字符数；这与官方“同任务同模型各 3 次取中位数”的口径不符，也不能区分真阳性、误报与重复项。`docs/uplift-baseline.md` 缺失，现有 15 vs 9 只有交接文档摘要，没有逐 finding 原始输出、裁决状态和模型/Skill hash。更关键的是，历史差异项不全是 gold：`ASA I–III` 是允许入组范围，实际样本只有 II/III 本身并不矛盾；“48 小时内未报告严重并发症”若上下文已限定为术后两天，也不能自动判成过度安全声明。
- **影响**：把裸模型的可疑意见全部当真阳性，会奖励误报并惩罚 Skill 的保守门控；把字符数和脚本名提及当 uplift，则会直接鼓励冗长输出。评委复跑三次后若结果不稳定，30% 工程质量维度仍无法举证。
- **方案**：落实 Round 6 P1 与 Round 13 P1，但只改现有入口，不再新建第二套 evaluator：
  1. 修改 `tools/uplift_ab.py`：`--model` 改为必填；新增 `--runs 3`、`--task-manifest`、`--adjudication`、`--outdir`；按 run 保存 baseline/with-skill 原文、退出码、模型完整标识、prompt hash、Skill tree hash、输入 hash、开始/结束时间。模型不支持 seed 时记录 `seed_control=unavailable`，不得伪称配对随机。
  2. 新增 `tools/fixtures/uplift-regression/adjudication.json`，每条使用 `{finding_key,error_family,gold_status,evidence_refs,scientific_rationale,detectable_inputs,expected_consumer}`；`gold_status` 只允许 `confirmed/disputed/not_an_error`。双人独立裁决后才进入 precision/recall，分歧保留，不用接收/拒稿作真值。
  3. 对历史 RCT 至少重裁七类：表格互斥分类合计错误=`confirmed`；Table 2 `P=.025` 与讨论 `P=.098`=`confirmed`；“总剂量降低”但所引 Table 2 只报患者人数=`confirmed`；随机后排除/分析集问题=`disputed`，须先恢复 CONSORT flow 和排除原因；ASA 等级缺 I=`not_an_error`；Horner 征破盲=`disputed`，须核对谁被盲、何时评估；48 小时安全性=`disputed`，须按 claim scope 裁决。
  4. 聚合只报告三次论文级中位数：confirmed finding precision/recall、正确 evidence locator 率、确定性适用项执行率、人工复核队列长度、每千输出 token 的 confirmed true positive。字符数和 finding 数只作诊断，不作质量分。
  5. 生成 `docs/uplift-baseline.md` 作为单一事实源，链接每次 artifact；`docs/overnight-status.md` 只保留历史摘要，不再手工更新数字。
  6. 采纳 Round 13 P1/P5 的信息预算门禁：以下内容若不增加 confirmed finding、证据定位或安全降级，必须退出默认热路径——Stage 0 的历史解释、未命中模块的整份 reference、schema 已表达的重复枚举、空报告节长说明、被证伪候选及其搜索过程。安全边界、三类记录定义和失败降级不参与删减。
- **代价**：1–2 人日工程，另需两名领域审稿人各 2–3 小时重裁历史 RCT；正式 GLM/Kimi 运行依赖对应凭据。
- **建议优先级**：P0 交付前必须做；没有逐条 gold 与三次中位数，任何“uplift 已转正”声明都不成立。
- **阶段 / 归属**：一期离线评测基础设施，不属于 M1–M7，不改变生产流水线。
- **契约字段**：生产契约不改；测试 artifact 增 `run_index/model_id/model_version/prompt_sha256/skill_sha256/input_sha256/gold_status/error_family/token_usage/execution_trace_ref`。
- **假阳性**：评测本身不立 finding。主要风险是裁决者把审稿偏好当事实错误；只裁“事实是否成立、证据是否足够、是否影响人工 triage”，保留 `disputed`，不强行多数表决。

### P2 · 在现有统计脚本补“同一结果跨位置闭合”，对准本次真实漏检

- **问题**：`statistical_forensics.py` 的五项检查只验证单个局部对象。真实 RCT 中已出现两个当前工具抓不到的确定性缺口：同一“累计救援镇痛”在 Table 2 报 `P=.025`、讨论报 `P=.098`；正文声称“总 pethidine dose 降低”，所引 Table 2 的行和脚注却只给接受 pethidine 的患者人数。前者是同一统计结果跨位置冲突，后者是 claim 的 measure kind 与所引表格不一致；两者都不是再写一遍通用审稿清单能稳定发现的。
- **影响**：模型会偶尔人工看出冲突，但现有脚本无法遍历全文建立同一语义键，正是 `table_total_mismatch` 修复前的同类断点。若新增独立第六个脚本，适用项枚举、CLI、schema 和执行轨迹会再次分叉。
- **方案**：**一期离线**扩展现有 `scripts/statistical_forensics.py`，新增一个输入操作 `cross_location_consistency`，不新增脚本：
  1. M1 为每个统计断言抽取封闭 `semantic_key={outcome,measure_kind,groups,timepoint,analysis_population,estimand,contrast}`；任一键不确定即 `binding_status=ambiguous`，工具不比较。
  2. 每个 assertion 保存 `{assertion_id,semantic_key,value,qualifier,unit,evidence_refs,cited_table_ref}`。p 值按原文精度转换为点/上界/下界区间；只有同键区间不相交才产 `reported_result_conflict`。
  3. 对带显式表格引用的 claim，比较 `claim.measure_kind` 与表格 row/footnote 的 `measure_kind`。`dose` 对 `person_count`、`event_count` 对 `participant_count`、`mean` 对 `median` 等不相同只产 `claim_measure_mismatch_candidate`；M7 必须再检索全文，确认没有其他数据支撑后才可立 finding。
  4. 复用现有单位归一化器处理同量纲单位；单位不可比、ITT/PP 不同、时间点不同、调整/未调整模型不同均返回 `not_comparable`，不得产 mismatch。
  5. 修改 `references/01-structured-extraction.md` 的统计 assertion 抽取、`references/04-statistics.md` 的 M4 消费门、`references/07-conclusions-discussion.md` 的 claim 支撑消费门、`schemas/extraction_signal.schema.json` 和 validator；M1/工具仍不产 finding。
- **代价**：1.5–2.5 人日；实现与 schema 1 人日，真实 RCT 两个阳性 + 不同分析集/时间点/adjusted model 等 12 个困难阴性 0.5–1.5 人日。
- **建议优先级**：P0 交付前先做 p/estimate 跨位置冲突；measure-kind 对账为 P1，但仍应优先于新增 qPCR/dPCR 工具。
- **阶段 / 归属**：一期离线；M1 抽取，Stage 2 现有统计工具产 signal，M4/M7 产 finding，不新增模块。
- **契约字段**：扩展 `structured_result` 的 `statistical_assertions[]`；signal 可新增单一 `cross_location_consistency_candidate`，条件块含 `{check,semantic_key,assertion_refs[],comparison_intervals[],comparability,rule_version}`。这是增量扩展，不重构三类记录。
- **假阳性**：中高。最大风险是把不同 endpoint、timepoint、analysis population 或模型强行合并；七维语义键必须完全一致，绑定不明确只给 `partial_extraction`。measure kind 不一致只能交人工，不能自动写成“数据造假”或 `critical`。

### P3 · 五个现有脚本按真实语料“有阳性 / 仅阴性 / 尚未对齐”挂牌

- **问题**：当前“已实现五个脚本”容易被误读为五类 uplift 已生效，但仓库证据并不支持。真实对齐情况如下：

  | 现有脚本 | 真实语料证据 | 当前判断 |
  | --- | --- | --- |
  | `statistical_forensics.py` | RCT 的 `12+18≠28` 等互斥分类合计已命中；同一 p 值跨位置冲突和 dose/person-count 错配未覆盖 | **1 类真实阳性；有明确漏检** |
  | `figure_integrity_audit.py` | 41 张真实图的网格/坐标轴误报已从 20 降到 0；阳性仍主要是植入合成块 | **真实困难阴性已验证；真实阳性 recall 未验证** |
  | `sequence_identifier_audit.py` | 语料含 primer 表、qPCR、蛋白变体与多个 accession；当前只做格式、局部 HGVS、版本化给定序列、primer QC，不做 primer→transcript 匹配 | **有真实适用对象；无经裁决阳性** |
  | `ethics_compliance_check.py` | 人体/动物论文均适用，但公开 PLOS 稿件多已报告伦理声明；历史负 uplift 未证明本工具新增了 confirmed finding | **规则型保底；真实 uplift 未量化** |
  | `normalize_biomed_units.py` | 语料有大量剂量/浓度单位，但工具只在同一指标出现不同单位时贡献冲突消解；尚无经裁决的跨单位错误 | **基础设施价值；不得按 finding uplift 宣传** |

- **影响**：把“脚本存在”当“真实错误覆盖”会在评委追问时失守；反过来，为每个脚本硬造一个阳性会过拟合合成 fixture。图像工具当前更能证明 precision 门控，不能证明真实异常 recall。
- **方案**：采纳 Round 13 P2 的 `check_inventory[]`，并为回归 artifact 增 `validation_level=synthetic_positive/real_negative/real_positive`。每个 check type 单独挂牌：至少一条双人确认的 `real_positive` 和两条困难 `real_negative` 才可写 `uplift_active`；只有阴性校准时写 `precision_calibrated_only`；只有合成阳性时写 `synthetic_only`。交付前优先让统计工具通过 P2 获得两个真实阳性；其余四个脚本保持准确披露，不为凑数新增检查。Round 9 P2、Round 11 P7 已提出真实回归集，本项只增加统一挂牌与发布门禁，不另建第三套 fixture 目录。
- **代价**：0.5–1 人日汇总既有 fixture 与标签；真实图像阳性、primer 靶向阳性若暂时没有可信 gold，保持未验证状态即可。
- **建议优先级**：P0 交付前必须完成挂牌；它直接阻止“合成自检全绿 = 对真实论文有效”的过度声明。
- **阶段 / 归属**：一期离线评测与发布门禁，不属于 M1–M7。
- **契约字段**：生产契约不改；测试记录新增 `tool_id/check_type/validation_level/gold_case_ref/hard_negative_refs/status`。
- **假阳性**：不产生稿件判断。真实出版论文中的可疑项不自动等于 gold；只有可复算错误或经领域裁决确认的事实问题才标 `real_positive`。

### P4 · 调整 X1 首个切片：先打通“正向引用已撤稿文献”的真实阳性

- **问题**：Round 1 P6、Round 12 P3 已提出引文状态核验，Round 13 P4 建议首个 X1 选 ClinicalTrials.gov；但当前 RCT 语料已经给出更短的真实阳性链：参考文献 10 的题名明确以 `Retracted:` 开头，正文却用 “A recent trial also demonstrated...” 把它作为正向机制证据。继续先做只有格式/注册号存在性的浅核验，会放弃一个评委可直接复查的 corpus-aligned uplift。
- **影响**：裸模型可能注意到题名中的撤稿标记，也可能漏掉；X1 可以给出当前、版本化、可追溯的状态记录，并把“引用撤稿论文”与“讨论撤稿事件”分开。这个垂直切片同时证明 external evidence、citation context、失败降级和 M7 消费链真实工作。
- **方案**：**一期联网增强**，复用 Round 12 已落地的 X1 契约，不新建 evidence 类型或并行 resolver：
  1. M1 抽取 DOI/PMID/PMCID、参考文献 locator 和正文 citation context；context 固定为 `supports_claim/background/discusses_retraction/method_source`，不明确为 `ambiguous`。
  2. connector 先用 Europe PMC `GET /search?query=DOI:{doi}&resultType=core&format=json` 解析 source/id，再调用官方 `POST /status-update-search`，JSON body 为 `{ids:[{src,extId}]}`。[Europe PMC REST API](https://europepmc.org/RestfulWebService) 明确提供 article status update 查询；保存 endpoint、请求规范化文本、响应 hash、API version、retrieved_at 与 update relation。
  3. 只有外部状态为 retracted/withdrawn，且正文 context 为 `supports_claim` 或 `method_source` 时产 `external_validation_candidate`；M7 回查稿件内 claim 与 citation locator 后才可立 finding。`discusses_retraction` 不进入人工风险队列。
  4. 题名本身含 `Retracted:` 可作为本地候选，但不得冒充外部状态已核验；网络 403/429/5xx、白名单、零匹配或 DOI 歧义只产 X1 `system_limitation`，离线审核继续。
  5. 验收至少含：本 RCT 正向引用阳性、主动讨论撤稿阴性、仅 correction 阴性、DOI/PMID 指向同一记录、标识符歧义、API 失败。完成后再按 Round 13 P4 接 ClinicalTrials.gov。
- **代价**：1.5–2.5 人日；connector/缓存 1 人日，citation context 与 6 个录制响应回归 0.5–1.5 人日。白名单未开时可先用录制响应闭合全链。
- **建议优先级**：P0 交付前优先于多数据库并行接入；它已有语料真实阳性，验收成本低于完整临床注册语义对账。
- **阶段 / 归属**：一期联网增强；X1 取证，M7 判断 claim 依赖，M2 仅处理参考文献标识与呈现。X1 不产 finding。
- **契约字段**：复用 `external` evidence 与 `external_validation_candidate`；只扩 `external_check` 的 `citation_context/update_type/update_record_id/relation_to_claim`，不重构三类记录。
- **假阳性**：中。撤稿文献可能被引用为历史背景或不端案例，轻微 correction 也不是撤稿；只有正向支撑关键 claim 才交人工。数据库未命中或网络失败绝不能变成稿件问题。

## 未解决 / 需要人来定的问题

1. 是否接受重新裁决 15 vs 9，而不是继续把裸模型全部 15 条当 gold。建议接受；ASA 等级条目不应计入 confirmed recall。
2. 是否把 P2 的跨位置闭合作为交付前唯一新增确定性 check family。建议接受；它直接来自真实漏检，并复用现有统计脚本。
3. X1 首个垂直切片是否从 ClinicalTrials.gov 改为 Europe PMC citation status。建议先做 Europe PMC 真实阳性，再做 NCT；两者均复用同一 X1 契约。
4. `docs/uplift-baseline.md` 是误删还是尚未生成。Git 历史未发现该文件；建议由 P1 evaluator 生成，避免再维护手写数字。
5. Round 7 的统一 runner、Round 13 的适用项账本与 Round 14 的 runtime conformance harness 均未落地。本轮不重复设计；P2 之前至少要实现账本，否则新增 check 仍可能只存在于源码。
6. 不应新增的 token：重复解释 rubric、把 rejected candidates 输出给用户、每稿加载未命中 reference、在摘要/发现/复核计划三处复述同一 finding、用长篇“无异常”说明填满空节。这些都增加 token 而不增加 confirmed finding、证据定位或安全降级。
