# Round 8 · 输出报告与实际可用性 提案

## 摘要

旧模板虽然名义上有八节，却重复表头、倾倒原始对象、重复展示 finding，并且只打印 `EV-*`，审稿人无法据此快速回到原文；本轮已直接重写为按范围、判断、证据、动作组织的审稿人视图。
非 `full_review` 与零 finding 的边界原先容易被读成“没有问题”，P0/P1/P2 也缺统一口径；本轮已补固定警示、优先级语义、schema 约束与 fixture 门禁。
下一步不应继续增加报告篇幅，而应交付真实渲染器验收、claim 级审阅矩阵、页内证据图谱和人工裁决导出，使报告从静态 Markdown 变成可复核的审稿工作单。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/templates/review_report.md` | 全文件 | 重写八节模板；首屏增加范围警示、finding 计数与前三条 P0/P1；结构化字段只保留一个表头并格式化数值对象；观测组改为可读表格；finding 按 cluster 只展示一次；规定证据按 compact/expanded 真正展开；signals/limitations 明示非稿件问题；复核动作直接附核对证据 | 旧模板把 schema 对象原样倾倒、finding 展示两遍、证据只列 id，真实审稿人无法快速定位或直接使用 |
| `skills/biomed-paper-review/SKILL.md` | §2.10、§6 | 固定 cluster、复核计划排序；定义 present/absence 证据渲染失败规则；定义 P0/P1/P2 唯一语义；为四种非 full 模式和“已执行但零 finding”规定不可误读文案 | 原规范只说“展开证据”“按 P0/P1/P2”，没有规定展开格式、排序依据或 partial 警示 |
| `skills/biomed-paper-review/references/00-contracts.md` | §6.1 | 增加人工复核优先级的操作定义；critical 固定 P0、major 仅 P0/P1、minor/info 若进入计划仅 P2；带 P2 的 minor/info 也必须进入报告计划 | 旧契约允许同一严重度随意赋 P0/P1/P2，优先级不可解释；minor 的已写动作还可能从第八节消失 |
| `skills/biomed-paper-review/schemas/finding.schema.json` | `allOf` | 机器约束 critical→P0，minor/info 若有 priority→P2；保留 major 的 P0/P1 区分 | 不改变 finding 架构，只封闭明确非法组合 |
| `skills/biomed-paper-review/schemas/review_report.schema.json` | `manual_review_plan` | `finding_ids[]` 增 pattern 与 `uniqueItems`；说明 P2 minor/info 的纳入规则 | 旧 schema 接受重复或非 finding id，且文档与报告计划覆盖范围不一致 |
| `tools/validate_schemas.py` | 模板检查、复核计划检查 | 增加证据展开/partial 警示/P0-P2 语义静态门禁；检查复核计划引用、重复、覆盖和 item priority 与 finding priority 一致 | 防止模板后续退化回“只有八个标题”，也防止计划漏掉已有 P2 动作 |
| `tools/fixtures/sim1_rct_full_review.json` | `manual_review_plan` | 把 `M2-001` 的 P2 澄清动作加入报告级计划 | finding 已声明 P2，但旧计划静默丢弃它，模板第八节无法给审稿人完整待办 |

## B 类提案

### P1 · 把 Round 7 装配器提案收敛为可验收的报告渲染门禁

- **问题**：Round 7 P1 已提出 `assemble_review_report.py`，但当前仓库仍没有渲染器；本轮模板新增的 evidence lookup、cluster lookup、排序和人类可读格式化若只停留在注释中，评委仍无法运行一次命令得到报告。本项不另建第二个装配入口，只补 Round 7 P1 尚未定义的报告验收面。
- **影响**：模板再专业，不能从四个合法 fixture 确定生成 Markdown 就仍是“文档设计”；这会直接损失 30% 工程质量、14% Skill 复用，并使证据展开无法进入 uplift 消融。
- **方案**：**一期离线**在 Round 7 的 `skills/biomed-paper-review/scripts/assemble_review_report.py` 中实现本轮模板 helper，并增加 `scripts/render_report_snapshots.py` 与四份 golden Markdown。门禁固定检查：①输出无 `{{...}}` 残留；②八节各一次；③不得出现 Python/JSON 对象倾倒；④每个 finding 的全部 evidence ref 均展开且 locator 次序固定；⑤缺 ref 立即非零退出；⑥四种模式的范围警示逐字命中；⑦cluster 和复核计划排序稳定；⑧同一 finding 不在第四节重复；⑨absence 无 quote/页码；⑩Markdown 表格通过 CommonMark 快照。命令接收 `--input/--output/--template`，相对路径以脚本位置解析。
- **代价**：1–1.5 人日；依赖 Round 7 P1 的装配器决策，不依赖网络或第三方数据库。golden fixture 可直接复用现有四例。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期离线；Stage 5 输出装配，不属于 M1–M7，不新增模块。
- **契约字段**：不新增生产字段；helper 只读现有 report JSON。可在测试 artifact 保存 `template_sha256` 与 `rendered_sha256`，不写回三类记录。
- **假阳性**：不产生科学判断。最大风险是模板查找失败导致静默缺段；任何不存在/重复 ref、finding 或 limitation id 都 fail closed，禁止降级成空文本。

### P2 · 以核心 claim 为轴的“结论—数据—问题—动作”审阅矩阵

- **问题**：当前八节按数据类型分区，适合审计契约，却不符合领域审稿人的第一条阅读路径：逐条判断论文的核心 claim 由哪些实验支撑、哪些 finding 会削弱它、哪些输入缺口使它暂不可判。审稿人现在必须在 `conclusion.claims[]`、key data、M4/M7 finding、系统限制和复核计划间人工跳转。
- **影响**：报告可能准确列出十个问题，却没有回答“哪个主结论受影响”；评委会认为它更像质量检查日志，而不是能帮助形成审稿意见的生物医学报告。
- **方案**：**一期离线**在 Stage 5 生成非记录投影 `claim_review_matrix[]`，每项为 `{claim_id,statement,scope,supporting_key_data_refs[],supporting_evidence_refs[],finding_refs[],system_limitation_refs[],review_status,manual_review_action_refs[]}`。`review_status` 只允许 `finding_present/no_finding_in_executed_scope/blocked_by_system_limitation/not_reviewed`，禁止使用模糊的 `supported` 或 `true`。为 finding 增可选 `claim_refs[]`；只有显式 claim id 才连边，M7 未执行则全部 `not_reviewed`，系统限制只产生 `blocked_by_system_limitation`，不得转 finding。报告首屏显示受 P0/P1 影响的 claim，第四节按 claim 折叠 cluster；没有 claim_ref 的 finding 保留在“跨 claim 问题”。Round 2 P1/P2 若后续加入 centrality/support_edges，本矩阵消费其字段，不另建第二套 claim 模型。
- **代价**：2–3 人日；1 人日 schema/聚合器，1 人日模板与 fixture，0.5–1 人日人工核对 10 篇语料的 claim 链。无外部依赖。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：一期离线；M1 继续只抽取 claims，M2–M7 只产 finding，Stage 5 生成视图；不新增审核模块。
- **契约字段**：扩展 finding 的可选 `claim_refs[]`；顶层增加非记录对象 `claim_review_matrix[]`。不改变 severity、证据登记表或三类记录。
- **假阳性**：中。语义相似不等于同一 claim，自动模糊匹配会错误放大影响；只接受审核模块显式写入的 `claim_refs[]`，无法绑定的 finding 不强配。`no_finding_in_executed_scope` 绝不能渲染成“claim 已被证实”。

### P3 · PDF/JATS 页内证据图谱与候选区域裁片

- **问题**：现有 locator 能落到页、段、图和 panel，但 PDF 一页可能有双栏正文、多幅 panel 和长表；只给“PDF p.8, Fig 3B”仍需审稿人二次搜索。OCR 输入还可能出现 quote 正确但页内位置错位，当前报告没有可视校验面。
- **影响**：证据链机器上可解析、人工上仍慢；在 20–40 条 finding 的报告里，定位成本会抵消 Skill 节省的审稿时间。图像或表格争议若没有候选区域裁片，也难以核对系统究竟看到了什么。
- **方案**：**一期离线**新增 `scripts/build_evidence_atlas.py`。在 locator 增可选 `page_region:{x0,y0,x1,y1,coordinate_space,page_width,page_height,derivation}` 与 `text_span:{normalized_document_id,start,end,quote_sha256}`；`derivation` 为 `native_pdf_text/native_xml/ocr/manual_anchor`。脚本验证坐标边界和 quote hash，为每条 present evidence 生成 `evidence/EV-xxx.png` 候选裁片及 Markdown 相对锚点；图/表证据裁片保留 label、坐标轴或表头上下文，不得只裁一个数值。absence 不生成裁片。报告中的 EV id 链接到证据图谱，JSON 仍保留规范 locator。OCR region 必须显示 `OCR` 徽标与置信度，不能伪装成原生文本定位。
- **代价**：2–3 人日；PDF 坐标抽取需选一个已验证的 CPU 库或复用 Stage 1 现有解析产物，JATS span 可用标准库完成。提交包不保存论文裁片，运行产物置用户指定输出目录。
- **建议优先级**：P1 应该做；先交付 native PDF/JATS，OCR region 为 P2
- **阶段 / 归属**：一期离线；Stage 1 记录坐标，Stage 5 生成 evidence atlas；不属于 M1–M7。
- **契约字段**：只扩展 `locator` 的可选 `page_region/text_span`；不新增 evidence 类型。生成文件路径属于渲染 artifact，不写入 finding。
- **假阳性**：中。PDF 字序、旋转页、双栏与 OCR 会造成 bbox 偏移；Stage 1 坐标/hash 校验失败时只保留页级 locator，并产 `system_limitation: parse_failed`，不得把错误 region 交给 Stage 5 生成裁片。图谱只辅助定位，不改变 finding。

### P4 · 人工裁决状态与作者问询安全导出

- **问题**：当前报告到 `manual_review_plan` 即结束，审稿人核对后无法结构化记录“确认、驳回、需作者回答”，也无法从已确认 finding 生成不带机器内部术语的作者问询。重新编辑 Markdown 会切断原 finding、证据和规则的血缘。
- **影响**：Skill 只能产一次性报告，不能进入真实审稿闭环；被人工排除的图像/统计候选仍可能被复制给作者，尤其学术不端相关措辞存在名誉风险。
- **方案**：**一期离线**增加非记录工作状态 `reviewer_adjudications[]:{finding_id,status,reviewer_role,note,evidence_refs_added[],adjudicated_at}`，`status` 固定为 `unreviewed/confirmed/dismissed/needs_author_response`。新增 `scripts/export_review_queries.py`，输出两份文档：①给编辑的内部审阅表，保留 signals、limitations 与裁决轨迹；②给作者的问询清单，只纳入 `confirmed` 或 `needs_author_response` finding，按 P0/P1/P2 分组，使用“请核对/请说明/请补充”句式，绝不输出“造假”“违规”自动定性。自动 finding 原对象保持不可变，人工裁决不反写 severity/risk；若需要最终人工严重度，另存 `reviewer_assessed_severity` 并明确不是模型值。
- **代价**：1.5–2 人日；脚本、schema、两个 fixture 和审稿人角色映射。无网络依赖。
- **建议优先级**：P1 应该做；作者问询导出在图像取证上线前必须完成安全词门禁
- **阶段 / 归属**：一期离线；Stage 5 后的人机协作层，不新增审核模块。
- **契约字段**：新增非记录 `reviewer_adjudications[]` 与可选 `reviewer_assessed_severity`；finding、signal、system_limitation 保持只读。导出文档是 artifact，不是第四类记录。
- **假阳性**：高，主要风险是把未复核候选直接发给作者。默认全部 `unreviewed` 且不可导出；只有人工显式改为 `confirmed/needs_author_response` 才进入作者清单。dismissed 条目只保留在内部轨迹，不影响原始自动化结果的可审计性。

## 未解决 / 需要人来定的问题

1. Round 7 P1 的 `assemble_review_report.py` 是否在交付前落地。建议接受，并把本轮 P1 作为其唯一 Markdown 验收门禁；不要另建第二个 renderer。
2. P2 的 `claim_refs[]` 是否先以可选字段落地。建议先可选；M7 不明确绑定时保留“跨 claim 问题”，禁止模型按语义相似度强配。
3. P3 选择哪一个 PDF 坐标解析依赖。必须先用四个 fixture 对旋转页、双栏、图注与表格做回归，再锁版本；无稳定坐标时只交 JATS text span。
4. P4 的裁决数据是否属于提交报告还是本地工作状态。建议默认单独 sidecar 保存，只有用户明确要求时才附在最终 JSON，避免把审稿人身份与时间戳泄露给作者。
5. Round 1 的旧模板迁移、Round 6 的 `partial_not_classified` 与本轮模式警示已采纳实现；Round 4 X1、Round 5 图像取证、Round 7 统一装配器仍未落地。本轮未重复提出外部数据库连接器或图像异常算法。
