# Round 24 · 对抗性审查：评委会怎么挑刺 提案

## 摘要

最伤的点是仓库仍没有论文输入到最终报告的统一执行轨迹，也没有官方模型三次中位数的正 uplift artifact；五个脚本目前只能证明“分别能跑”，不能证明“挂 Skill 后更好”。
第二个硬伤是 `full_review` 仍是默认模式，而 M2 明写为骨架；手工 fixture 列满 `M2–M7` 不能证明六个审核模块真实完成。
第三个硬伤是 624 行 `SKILL.md` 与 5,039 行运行时 Markdown 形成高认知负担；README 的十分钟速览已补，但默认热路径仍需用组件消融裁掉没有增量的说明。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `README.md` | 开头“十分钟速览”、目标输入/输出、使用、合规自查、当前状态 | 把“全部能力”“端到端模拟”收敛为五个独立 CLI + 契约模拟；明确无统一执行器、无 X1 connector、无 GLM/Kimi 正 uplift artifact；修正包体积和 M3 状态 | 旧文案可被仓库文件直接反证，评委会把成熟度描述视为不可信 |
| `skills/biomed-paper-review/SKILL.md` | §6.5 | 删除“五个脚本都是裸模型做不到、构成 uplift”的绝对承诺；改为逐检查基线与真实 artifact 门禁，并明确 `table_total_mismatch` 不得作为 uplift 证据 | “确定性可复算”不等于“裸模型发现不了”；旧表述与已知 Qwen 探针结论矛盾 |
| `references/03-experimental-methods.md` | §3、§6 | 修复失效的 §8.1/§8.2 引用；把“二期才可查”改成“当前离线不查、一期可选 X1 增强”，并保留外部失败不得产 mismatch 的门控 | 旧分期仍建立在过期的无网络假设上，也指向不存在的小节 |
| `references/05-figures-and-charts.md` | 开头、§A.1、§A.5、§B、§D、§F | 明确 Stage 3 Parser 只产 record/signal/limitation，Stage 4 M5 Reviewer 只产 finding；更新已实现图像候选与未实现稳健变换边界；修复 §E.5 悬空引用与旧二期表述 | 旧文件要求 Parser 输出 `finding[]`，正面违反三类记录与唯一产出者架构；又把已经存在的图像脚本写成未实现 |
| `tools/probe_cases/round24_flow_laser_fluorochrome_mismatch.md` | 新文件 | 增加流式荧光团—激光配置错配的埋入式最小案例 | 候选新组件先过基线探针；本次 3 次调用均被沙箱网络拒绝，结论为 `INCONCLUSIVE`，不据此立项 |

### 既有提案采纳状态

- **已采纳实现**：Round 1 的单位归一化与基础统计取证、Round 4 的脚本入 Skill 本体、Round 11 的图像候选最小版、Round 12 的 X1 核心契约；Round 5 P1 的 M5 角色拆分在本轮完成文档收口。
- **部分采纳**：Round 12 外部验证层只有 schema/失败契约，resolver、connector、录制响应和独立覆盖率未实现。
- **仍未采纳且已成阻断项**：Round 7 P1/P2、Round 13 P1/P2、Round 15 P1。下列 P1/P2 是采纳裁决与验收顺序，不重复设计第二套 runner、manifest 或评测口径。

## B 类提案

### P1 · 攻击面 #1：把既有执行与 uplift 提案升为唯一交付阻断门

- **问题**：Round 7 P1 已提出 `run_deterministic_checks.py` 与报告装配器，Round 13 P2 已提出逐适用项 `check_inventory[]`，Round 15 P1 已提出三次中位数与逐 finding 裁决；三项均未落地。当前 `skills/biomed-paper-review/scripts/` 只有五个独立入口，`tools/uplift_ab.py` 仍每臂只跑一次、默认 `openai/gpt-5.6-sol`，粗指标仍是条目数、locator 数、脚本名提及和字符数。四个 report fixture 是手工契约实例，不是运行产物。
- **影响**：这是 30% 可完成性、25% 证据链和 uplift 机制的共同阻断项。评委无需质疑任何生物医学规则，只要问“给我一条命令和三次对照 artifact”，项目就无法回答；新增第六个算法也不会改变这一结论。
- **方案**：不另建入口或评测口径，直接按 Round 7 P1 → Round 13 P2 → Round 15 P1 的依赖顺序实施。涉及文件固定为 `skills/biomed-paper-review/scripts/run_deterministic_checks.py`、同目录 `assemble_review_report.py`、包内 smoke cases 与现有 `tools/uplift_ab.py`；接口和字段以三份既有提案为准。本轮只新增交付验收条件：一次命令可从封闭中间 JSON 得到 schema 合法 JSON + Markdown，所有适用工具有 trace，至少一个经双人确认的真实阳性仅 Skill 臂稳定命中，且 major/critical precision 不低于裸模型。任一条件未满足时，README 必须保持“未打通 / 未证明”，不得用新算法数量替代。
- **代价**：2–4 人日；runner/assembler 约 2 人日，三次官方模型运行与双人裁决约 1–2 人日。依赖可用的官方模型凭据；无凭据时只能完成工程门禁，不能宣称 uplift。
- **建议优先级**：P0 交付前必须做；在它完成前暂停新增生产组件。
- **阶段 / 归属**：一期离线工程基础设施 + 官方模型评测；Stage 2/3 工具编排与 Stage 5 装配，不新增 M1–M7 模块。
- **契约字段**：复用 Round 7 的非记录 `execution_trace` 和 Round 13 的非记录 `check_inventory[]` / `deterministic_check_coverage`；不增加第四类记录，不改变 finding/signal/limitation 边界。
- **假阳性**：runner 不产 finding，风险低；真实风险是用“多报”冒充“更准”。逐 finding 双人裁决、证据定位正确率和人工复核队列长度必须与召回同时报告。

### P2 · 攻击面 #2：`full_review` 必须通过能力门禁，不能靠数组列满六项

- **问题**：`references/02-macro-logic.md` 仍标为“骨架—待负责人填充规则库”，但 `SKILL.md §1.1` 默认 `full_review`，schema 只检查 `executed_modules[]` 是否列满 `M2–M7`。`sim1` / `sim4` 因手工写入六个模块即可得到 `partial:false`。本轮已直接修复 M5 Parser/Reviewer 角色冲突并纠正 README 的 M3 状态，但 M2 未就绪这一事实受禁改路径限制仍存在。
- **影响**：评委打开 M2 的前 10 行即可证明“完整审核”承诺超过实际能力。更严重的是骨架模块返回空 finding 会被解释成“已审且无问题”，形成未执行维度的假阴性，而 `review_confidence` 与风险分仍显示完整。
- **方案**：团队在提交前二选一，不再发明第三套状态模型。推荐直接采纳 Round 7 P2 的 `capability_manifest + requested/effective mode` 门禁，修改 `SKILL.md §1/§2.9`、`execution_scope.schema.json`、`review_report.schema.json`、fixtures、validator 与 README；M2 文件仍只由负责人修改。若团队拒绝该 schema 迁移，唯一替代是由 M2 负责人补齐规则、正反例和至少一个真实回归，再保留默认 `full_review`。不能继续维持“骨架 + 完整分数”。
- **代价**：能力门禁 1–1.5 人日；补齐 M2 规则和回归至少 1–2 人日并需要卓妍拍板。两条路径都不依赖外部数据库。
- **建议优先级**：P0 交付前必须做。
- **阶段 / 归属**：一期离线执行规划层；不新增审核模块。
- **契约字段**：若采能力门禁，扩展 `execution_scope` 的 `requested_mode`、`effective_mode`、`capability_snapshot_hash`，增加 `system_limitation.category = module_not_ready`；均为现有对象扩展。
- **假阳性**：不新增稿件 finding。降级会减少表面上的“完整度”，但会把未审范围显式暴露，避免把没跑误写成没问题。

### P3 · 攻击面 #3：把默认热路径压到 430 行以内，再用组件消融决定保留项

- **问题**：当前 `SKILL.md` 624 行，`00-contracts.md` 1,205 行，`01-structured-extraction.md` 1,013 行，全部运行时 Markdown 合计 5,039 行。README 现已能在十分钟内说明项目，但真正执行 Skill 的模型仍先加载超出建议上限的主文档，再按任务读取长 reference。主文档重复保存评分公式、CLI 示例和契约摘要；这些内容增加注意力竞争，却没有 artifact 证明对 GLM/Kimi 的正确 finding 或证据定位有增益。
- **影响**：评委会把这视为“契约复杂到没人实现”的直接证据；官方模型可能因规则占满上下文而漏掉 Stage 0 自由发现，重演历史上的负 uplift。14% Skill 复用价值也会因入口难读、运行时操作散落而下降。
- **方案**：一期做文档剖面迁移，不改科学架构：①把 `SKILL.md` 控制在 430 行内，只保留触发、四模式路由、阶段依赖、三类记录边界、必须运行的适用性表和一层 reference 索引；②评分公式只保留在 `00-contracts.md §8`，主文档只写三项含义与禁止混用；③把五个 CLI 的完整命令与错误码迁入新的单层 `references/08-runtime-tools.md`，主文档保留一条统一入口命令；④为 `00`、`01`、`04`、`05` 增短目录和 `rg` 检索词提示；⑤按 Round 13 P1 运行 `bare / deterministic_only / full_skill` 三臂最小消融，某段不增加正确 finding、正确 locator 或安全降级且增加 token，就移出默认热路径。安全声明、三类记录边界和失败降级不参与删除。
- **代价**：0.5–1 人日迁移与引用 lint，另需官方模型三臂各 3 次；不涉及 schema migration。
- **建议优先级**：P0 在 P1 runner 可复跑后立即做；没有消融结果前先完成机械去重，不凭主观删除领域规则。
- **阶段 / 归属**：一期平台 Skill 热路径；不属于 M1–M7，不调用外部数据库。
- **契约字段**：无。只迁移说明位置并保持所有枚举、schema 与脚本接口不变。
- **假阳性**：不产生稿件判断。主要风险是压缩时删掉安全门控；以关键短语 lint、全部 fixtures 和六项自检作为迁移门禁。

## 基线探针结果

| 候选 / 已实现检查 | 模式 | 结果 | 本轮决定 |
| --- | --- | --- | --- |
| `table_total_mismatch` | 既有 Qwen 3 次探针（题目已给定实测结论） | `BASELINE_FINDS_IT` | **已探针，放弃作为 uplift 卖点**；脚本中仅保留为低成本、可复算回归门禁，不再为它扩规则文字 |
| 流式 `fluorochrome_laser_mismatch` | 将错误埋入 `flow_cytometry` 完整 JATS；`qwen3.8-max × 3` | `INCONCLUSIVE`：3/3 API 调用被当前沙箱以 `Errno 1 Operation not permitted` 拒绝，有效样本 0 | **不得实施、不得提为新组件**；网络恢复后重跑。若 `BASELINE_FINDS_IT` 则放弃，若 `UNRELIABLE/MISSES` 才另轮提出 M1→signal→M3/M5 的契约扩展 |

本轮没有提出新的生产检查组件。原因不是该方向价值低，而是强制基线探针没有有效样本；在 `INCONCLUSIVE` 上立项会违反本项目与稿件缺失判断相同的 fail-closed 原则。P1–P3 都是既有交付断点的收敛、能力门禁或文档剖面，不是新的稿件检查算法。

## 未解决 / 需要人来定的问题

1. **是否接受暂时降级默认 `full_review`。** 推荐接受能力门禁；若拒绝，必须由卓妍在提交前把 M2 从 skeleton 提升为有规则、有正反例、有真实回归的 ready 状态。
2. **谁负责 P1 的唯一 runner 与 assembler。** 不能再把它们拆给不同模块各写一套；建议指定一名集成人对 Stage 2/3 输入适配、Stage 5 输出和 artifact hash 负责到底。
3. **官方 GLM/Kimi 的具体型号与凭据。** 未冻结型号、prompt、temperature 和三次运行参数前，不得发布任何 uplift 数字；当前 `tools/uplift_ab.py` 的 GPT 默认值只能作为历史开发配置。
4. **是否暂停 X1 多 connector 扩张。** 建议先完成一个真实阳性垂直切片及其失败降级，再启第二个数据库；当前“契约已落地、connector 为零”比少列一个候选数据源更伤。
5. **流式硬件闭合候选是否重跑。** 当前有效样本 0；只有网络恢复并得到有效三次结果后才能决定放弃或进入下一轮提案。
