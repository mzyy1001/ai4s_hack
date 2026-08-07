# Round 25 · 输出报告与实际可用性 提案

## 摘要

报告最伤可用性的不是缺第九节，而是第二节倾倒全部字段/观测、第四节可能隐藏簇内 finding、第八节把多条 finding 的证据并成无归属集合；本轮已在现有八节内直接修复。
非 `full_review` 现在先显示逐模式固定边界，partial 数值改称“范围内问题权重合计”，零分母覆盖率显示“不适用”，不再用 `1.0` 制造 100% 完成的视觉误导。
真正仍阻断交付的是既有 Round 7/8 报告装配器尚未实现；两个新增候选（修订稿 finding 延续审计、证据定位可达性审计）已完成探针但均为 `INCONCLUSIVE`，恢复 Qwen 出站访问前不得实现。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/templates/review_report.md` | 渲染 helper 1–10 | 固定审稿人字段筛选、三型证据 compact/expanded 版式、簇内 finding 全量展开、逐 finding 复核证据包与五种模式警示原文 | 旧 helper 只说“展开/格式化”，不同实现可继续只给页码、隐藏簇成员或把多条 finding 的证据混在一起 |
| 同上 | 第一节“本报告能回答什么 / 审稿人先看” | 把模式边界置于分数之前；partial 改称“范围内问题权重合计”且不显示全稿分段；首屏显示 finding/复核动作计数与带起始定位的前三项 P0/P1 | 非完整模式最危险的误读是把局部 0 分当全稿低风险；原前三项只有动作文本，不能立即回到判断与原文 |
| 同上 | 第二节 | Markdown 只展示 required、未报告/未解析及 finding 相关字段；核心数据先给一行摘要，只对冲突、歧义、待视觉解析、解析失败或标记人工核对的组展开来源观测 | 全字段 × 全来源的表格会淹没真正需要审稿人判断的内容；完整结构化结果仍无损保留在 JSON |
| 同上 | 第三至第六节 | 明示 Stage 3 只读解读不是 M5 判断；第四节按 cluster 展开每条 finding 一次；signals/limitations 增总数与能力边界 | 原第四节只完整显示 representative finding，补充 finding 的内容取决于未定义 helper；signals 也容易被读成稿件问题 |
| 同上 | 第七节 | `total=0` 时用 `format_rate` 显示“不适用（0/0；契约哨兵 rate=1.0）”，并补充明确解释 | schema 的零分母哨兵值是 1.0，直接显示会让“本模式未检查任何图”看起来像图表 100% 可读 |
| 同上 | 第八节 | 复核动作改为可勾选工作单；逐 finding 显示 priority 依据、detail 与各自展开证据，不再显示无归属证据并集 | 审稿人需要知道每条证据在核哪一个判断；P0 major 与 P1 major 的逐项排序原因也必须可见 |
| `skills/biomed-paper-review/SKILL.md` | §6 | 同步“审稿人选择性 Markdown + 完整 JSON”、簇内逐条 finding、external 证据版式和逐 finding 复核证据要求 | 主执行规范不能继续允许旧模板式全量倾倒或无归属证据并集 |
| `tools/validate_schemas.py` | 报告模板静态门禁 | 新增 `collect_review_fields`、`format_rate`、`render_cluster_findings`、`render_plan_finding_packages`、逐 finding 核对包与零分母哨兵检查 | 防止后续只保留八个标题却把本轮可用性修复回退；本次只收紧校验，没有放宽任何契约 |
| `tools/probe_cases/round25_*.md` | 两个新探针案例 | 增加修订稿伪重复持续存在、证据 quote/locator 不可唯一定位案例 | 所有新组件先测 Qwen 裸模型，不用工程直觉冒充 uplift |

### 既有提案采纳状态

- **已采纳并由本轮继续收紧**：Round 8 A 类的八节模板、partial 警示、P0/P1/P2 口径；Round 12 的 external evidence 展开规则；Round 24 对 Stage 3 Parser / M5 Reviewer 的职责拆分。
- **仍未采纳且直接阻断真实报告生成**：Round 7 P1 与 Round 8 P1 的唯一装配器、helper 实现、golden Markdown 与无模板残留门禁。
- **本轮未重复**：Round 8 的 claim review matrix、evidence atlas、reviewer adjudication/作者问询导出；P2/P3 分别解决跨修订规则重跑与图谱生成前的 locator 可达性，不另建平行 claim/裁决/图谱对象。

## 基线探针结果

| 候选 | 案例 | `qwen3.8-max × 3` | 结论 | 本轮行动 |
| --- | --- | --- | --- | --- |
| 修订稿 finding 延续/解决状态审计 | `tools/probe_cases/round25_revision_finding_persistence.md` | 0 个有效样本；3 次均为 `urlopen: [Errno 1] Operation not permitted` | `INCONCLUSIVE` | 不实现、不宣称 baseline miss；保留条件设计，恢复出站后原命令重跑 |
| evidence locator 可达性审计 | `tools/probe_cases/round25_evidence_locator_ambiguity.md` | 0 个有效样本；3 次均为同一 socket 拒绝 | `INCONCLUSIVE` | 同上 |

调用已读取到凭据，失败发生在当前沙箱到 DashScope 的网络层，不是模型返回错误。两个案例均为孤立探针，会高估裸模型；网络恢复后除原命令外，还应把案例埋入一篇完整报告/论文再跑一次。没有 `BASELINE_FINDS_IT` 候选，因此本轮“已探针，放弃”为空；也不得把 `0/0` 写成“裸模型完全查不出”。

## B 类提案

### P1 · 把人工复核动作从自由文本升级为可验证工作单

- **问题**：`finding.manual_review.action` 和报告级 `manual_review_plan.action` 目前只要求非空字符串。文档声称动作必须包含“看哪里、核什么、若属实补什么”，schema 与 validator 却接受“核对统计”“请作者说明”这类不可执行文本；major 的 P0/P1 区分也没有逐条 `priority_rationale`，模板只能从 severity 与 priority 反向生成通用解释。
- **影响**：同一模型三次运行可给出完全不同粒度的动作，审稿人无法判断何时算核对完成，P0 major 也无法证明为何“直接阻断核心解释”。这会扣工程质量、结构化复用与实际可用性；动作变多却不可完成还会增加负 token uplift。
- **方案**：**一期离线，Stage 4 生成、Stage 5 装配，不新增模块。** 扩展现有 `manual_review`，保留 `action` 一个兼容版本，并新增：
  - `decision_impact`: `blocks_core_interpretation` / `changes_major_finding` / `clarification_only`；
  - `priority_rationale`: 非空短句，必须指出受影响的核心 claim、伦理授权、数据完整性或实质修改决定；
  - `verification`: `{question, completion_criterion, if_confirmed_request}`，三项均非空；“去哪里看”继续由 finding 自己的 `evidence_refs[]` 唯一提供，不复制自由文本位置；
  - priority 派生门禁：critical 固定 P0；major+P0 必须 `blocks_core_interpretation`；major+P1 必须 `changes_major_finding`；minor/info+P2 必须 `clarification_only`。
  报告级计划只做相同 verification 的去重分组，并保留成员 finding 各自的 rationale/evidence。修改 `finding.schema.json`、`review_report.schema.json`、`00-contracts.md §6.1`、模板第八节、四个 fixtures 与 validator；迁移期由旧 `action` 拆字段失败时拒绝自动升级，交人工补齐，不让模型猜写。
- **代价**：1–1.5 人日；schema/fixture/validator 约 0.5–1 日，M2–M7 示例与动作迁移约 0.5 日。无外部数据库依赖。
- **建议优先级**：P1 应该做；先在四个 fixtures 与 10 篇语料上要求“审稿人仅看工作单即可完成核对”的双人可执行性验收，再强制所有生产 finding。
- **契约字段**：只扩展既有 `finding.manual_review` 与 `manual_review_plan` 投影，不新增记录类型，不改变 severity、三类记录或证据登记表。
- **假阳性**：不新增稿件判断。主要风险是把普通 major 错排 P0；用 `decision_impact` 条件约束并要求具体 rationale，无法说明阻断关系时固定降为 P1，不允许模型用“可能影响结论”占位。

### P2 · 修订稿 finding 延续与回应闭合审计（探针未决）

- **问题**：真实审稿常比较初稿、作者回复与修订稿。图号、页码、finding id 和措辞会变化；按 id/locator 比较会把持续存在的伪重复误标为“已解决”，仅因新版没有再次生成 finding 也不能证明问题已消失。Round 8 P4 解决人工裁决与作者问询，不覆盖跨修订版本的规则重跑和问题延续。
- **影响**：错误的“已解决”比漏报更危险，会让编辑跳过仍影响核心结论的统计/伦理问题；纯文本 diff 又会把重排版、同义改写和正常新增分析制造成大量假变化。
- **方案**：**仅在探针得到 `BASELINE_UNRELIABLE/MISSES_IT` 后进入一期离线；Stage 5 后的人机协作层。** 新增 `scripts/compare_review_revisions.py`，输入两版规范化稿件、两份合法 report JSON、作者逐条回复和既有 Round 7 `execution_trace`。先按稳定 `issue_key`（Round 1 P1 尚未实现）或 `{module, category, affected target, evidence quote hash}` 生成候选映射；随后只对旧 finding 对应的确定性规则重跑。输出 sidecar `revision_comparison[]:{prior_finding_id,current_finding_ids[],match_basis,rule_rerun_ref,status,detail,manual_review_needed}`，status 仅 `persistent_candidate/addressed_candidate/new_candidate/unmatched`。`addressed_candidate` 必须有同一规则 `applicable + executed + no_mismatch` 的执行轨迹；即使满足也强制人工确认，报告不得自动写“问题已解决”。
- **代价**：2–3 人日；依赖尚未落地的 Round 7 runner/execution trace、Round 13 `check_inventory[]` 和稳定 `issue_key`。在这些前置项完成前不应单独实现文本 diff。
- **建议优先级**：P2 暂缓；当前探针为 `INCONCLUSIVE`，有效重跑前不得进入默认流程。
- **契约字段**：新增报告外 sidecar `revision_comparison[]`，不反写旧 finding/severity/risk；若后续并入 JSON，再作为非记录工作状态扩展，不新增第四类记录。
- **假阳性**：高。版面重排、同义改写、分析对象变化和规则未适用都会造成错误匹配；所有状态均为 candidate，低置信匹配固定 `unmatched`，没有规则重跑轨迹绝不产生 `addressed_candidate`。

### P3 · evidence locator 可达性审计（探针未决）

- **问题**：当前渲染器只要求 ref 存在并展开 locator；它不能证明页码正确、JATS `xml_id` 存在、quote 确实位于该节点，也不能发现同页两处完全相同 quote 在只有 page locator 时仍无法唯一定位。Round 8 P3 的证据图谱负责裁片与页内区域，本项只做生成图谱之前的可达性门禁，不重复坐标资产。
- **影响**：`EV-*` 在 schema 中可解析不等于审稿人能回到原文。页码错一页或重复 quote 会让证据链在机器层“全绿”、人工层不可用，直接损害 25% 科学可信性和 30% 工程质量。
- **方案**：**仅在探针得到 `BASELINE_UNRELIABLE/MISSES_IT` 后进入一期离线；Stage 1/报告装配门禁。** 新增 `scripts/audit_evidence_locators.py`：PDF 检查物理页范围、规范化 quote 在声明页的 match count、paragraph/figure/table 锚点是否把重复命中收敛到 1；JATS 检查 `xml_id` 存在且 quote 落在节点内；纯文本检查 paragraph id。精确 locator 与 quote 矛盾直接非零退出，拒绝渲染；输入本身无法提供更细锚点时由 Stage 1 产 `parse_failed` system limitation，不能降级成 finding。可选审计轨迹 `{evidence_ref,document_sha256,method,match_count,status}` 进入 Round 7 `execution_trace`，不写入 evidence 条目。无 quote 的 present evidence 仅在 figure/panel/table、xml_id/paragraph_id 或 supplement 页级锚点足够具体时通过。
- **代价**：1.5–2 人日；PDF 文本层/JATS/纯文本各一组 fixture，OCR 断词、连字符、双栏和重复标准句作为困难反例。依赖 Stage 1 暴露规范化文档及输入 hash，不依赖外部数据库。
- **建议优先级**：P2 暂缓；探针 `INCONCLUSIVE`，先恢复 Qwen 调用并跑埋入式案例。若裸模型稳定命中则放弃组件，只保留本轮明确的展开格式。
- **契约字段**：优先复用既有 `execution_trace.tool_runs[]` 保存审计 artifact；只有输入定位能力不足时产既有 `system_limitation(parse_failed)`，不新增 signal/finding，也不改变风险分。
- **假阳性**：中。OCR 标点、Unicode、断词和 PDF 阅读顺序会造成字符串不匹配；只允许可审计的轻量规范化，模糊匹配不能 hard fail，只标 `manual_review_needed`。重复 quote 若已有唯一 paragraph/xml/figure 锚点则合法。

## 未解决 / 需要人来定的问题

1. **现模板仍没有运行时渲染器。** Round 7 P1 与 Round 8 P1 已提出唯一 `assemble_review_report.py`、四 fixture golden Markdown、缺 ref fail-closed 和无 `{{...}}` 残留门禁，Round 24 确认仍未实现。本轮不重复造第二个 renderer；交付前应直接采纳既有 P0，否则模板 helper 仍只是规范文字，无法证明真实报告可生成。
2. P1 的结构化工作单是否在周日前做 schema migration。若不做，至少让双人审稿者检查所有 critical/major 的 action 是否同时回答 question、completion criterion 与 contingent request；“核对统计”不得进入演示报告。
3. `full_review` 是否允许在 M2 骨架与统一 runner 未落地时出现。Round 24 P2 已把能力就绪门禁列为阻断项；模板能正确警示 partial，但不能替编排器证明六个模块真实运行。
4. 第二节的 Markdown 筛选只影响人类视图，不得删除 JSON 中 recommended/optional reported 字段。未来 renderer 的快照必须同时检查显示行数与 JSON 字段总数，防止“减负”变成数据丢失。
5. P2/P3 的 Qwen 探针必须有效重跑；当前 `INCONCLUSIVE` 不授权实现。若恢复网络后为 `BASELINE_FINDS_IT`，在本文件追加“已探针，放弃”，不要因方案已经写得详细而继续投入。
6. Round 8 P2 claim review matrix、P3 evidence atlas、P4 reviewer adjudication/export 仍未落地；本轮没有重复提案。若团队只能选一个报告工程项，先完成既有 renderer/golden tests，再做 P1，最后才评估 P2/P3。
