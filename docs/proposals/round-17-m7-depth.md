# Round 17 · M7 结论与讨论规则库深度 提案

## 摘要

M7 的线性层级表此前把病例系列与队列、meta-analysis 与其底层证据能力混为一谈，还会把普通纵向回归的三项清单当作因果免责，本轮已直接修正。
`not superior` 被误判为等效声明、`claim_magnitude_mismatch` 只有 slug 没有规则、Limitations 依赖关键词和 §6 全局联动门互相冲突，本轮已补成可执行且保守的判据。
当前最大剩余缺口不是再加措辞词表，而是安全性精度、专门因果设计识别假设、证据合成能力继承，以及 surrogate/诊断性能到患者获益之间的桥接审计。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/07-conclusions-discussion.md` | 开头 | 增加一层目录 | 长 reference 需要让运行时按主题定位，避免深层引用 |
| `skills/biomed-paper-review/references/07-conclusions-discussion.md` | §3.1–§3.4 | 明确 evidence tier 是能力上限而非质量分；拆开纯模拟与经验数据生信、病例系列与分析性观察；E8 改为继承纳入证据能力；补诊断与安全性专门边界 | 旧表会让观察研究的 meta-analysis 自动获得 C5、让病例系列直陈关联，并把外部诊断验证误写成普适临床效用 |
| 同上 | §4.3 | 区分认识性 modal 与规范性 modal；区分未观察到事件、总体安全、零关联和“不能排除” | `may be recommended` 仍是推荐，`cannot exclude benefit` 也不是正向疗效；只看 modal 会同时漏报和误报 |
| 同上 | §5.1、§5.2.1 | 范围轴改为八轴 strict-superset 比较；为既有 `claim_magnitude_mismatch` 补完整触发、排除、severity 和证据要求 | 原范围判断没有 null/同义歧义出口，量级 slug 则无法从文档实现 |
| 同上 | §5.3 | 普通纵向观察路径不再自动获得因果能力；专门设计必须有 estimand、识别假设、诊断和敏感性分析；病例对照不再机械 critical | “时序 + 已测混杂 + 一项敏感性分析”不是充分因果识别条件，病例对照也不必然缺时间顺序 |
| 同上 | §5.4、§9.3 | 把等效/非劣效/效果为零与“未证明优效”分开；增加正常 `not found to be superior` 反例 | 优效性检验失败的限定陈述可以完全正确，旧规则会误伤常见 RCT 摘要 |
| 同上 | §5.6–§5.8 | Limitations 改为“问题域命题 + 推断影响命题”，词表只召回；异质性要求可比 estimand 与区间/检验；`discussion_hollow` 限定 full-length original research 和全文句级证据 | 固定关键词、点估计方向相反和短 Discussion 都会制造大量低价值假阳性 |
| 同上 | §6 | claim 级四门与研究级 `limitations_evasive` 分开；固定不可变上游快照、单遍执行和同根因聚簇 | 旧全局第②/④门会错误压制研究级局限核对，新建 M7 finding 若递归消费还会级联抬分 |

## B 类提案

### 真实文献压力测试（不作为对论文整体有效性的定性）

以下均来自仓库 10 篇 PLOS 开放语料，只检查所列 claim 与论文内直接证据的对齐：

| 文献与短句 | 越界模式 | 本轮规则能否抓到 |
| --- | --- | --- |
| [Nano-curcumin 与 tamoxifen-resistant breast cancer cells](https://doi.org/10.1371/journal.pone.0335165)：体外 MCF7-TR 结果后写“potential adjuvant for ER+ breast cancer patients” | 单一细胞模型 → 患者辅助治疗；E2 的 hedged C4 本身会放行，但 patient scope 扩张 | **条件可抓**：§5.1 在模型与患者范围均解析后报 `claim_beyond_evidence`；当前 `scope` 仍是自由字符串，Round 2 P1 未落地前稳定性不足 |
| [Insulin–aromatase 与生长板](https://doi.org/10.1371/journal.pone.0337215)：HFD 大鼠结果后称“novel therapeutic targets for obesity-related growth disorders” | 动物机制 → 人体疾病治疗靶点；另把 rat 范围从结论中删除 | **能抓**：E4 assertive C4 的 Δ=1；物种范围扩张再加一次修正，但 severity 仍按 §3.4 上限，不重复造 finding |
| [Exercise、肥胖与女性不孕的 rapid review + pilot](https://doi.org/10.1371/journal.pmen.0000202)：单组 pilot 仅 11 人入组、7 人完成，却写“clinicians should incorporate additional support mechanisms” | 单组可行性结果/rapid scoping review → 临床实践推荐 | **能抓**：规范性 `should` 为 C6 assertive；E6 单臂和未做 EtD 的 E8 均不能支持自动推荐 |
| [Thai polyherbal functional beverage](https://doi.org/10.1371/journal.pone.0339571)：大鼠 90 天 NOAEL 与体外抗氧化后称产品是“safe, antioxidant-rich functional beverage”并支持商业化 | 动物毒理 + 体外活性 → 人体长期安全/健康用途/商业可用 | **部分可抓**：本轮 safety 脚注阻止 animal NOAEL → human safety；但当前没有零事件风险上界、暴露时长和主动监测的确定性组件，需 P1 |
| [MAGEA3/6 胃癌多组学](https://doi.org/10.1371/journal.pone.0338705)：相关性分析后提出 potential biomarkers / therapeutic targets | 计算相关 → 生物标志物或治疗靶点 | **能抓**：E0 empirical association 的 hedged 上限为 C2，C4 进入 `claim_beyond_evidence`；数据库未注释不得作为反证 |

### P1 · 安全性主张精度与零事件上界审计器

- **问题**：当前 C0–C6 没有独立 safety 轴；本轮只能把“观察期内未见事件”映射为 C0、把“对目标人群安全”暂映射为 C5。`0/20` 与 `0/20,000` 都可能被语言模型写成“未见安全问题”，动物 NOAEL/HED 还常被错误升级为人体安全剂量。
- **影响**：药物、器械、食品和动物毒理稿件中，“没有观察到”被改写成“没有风险”是高发越界。没有可复算的事件率上界，M7 仍主要靠措辞，无法形成对裸模型稳定的 uplift。
- **方案**：**一期离线**扩展现有 `scripts/statistical_forensics.py`，增加 `safety_precision` 操作，不新建第六个旁置脚本。M1 抽取 `safety_claim_context:{population_or_species,dose,route,exposure_duration,independent_exposed_n,event_count,person_time,ascertainment_mode,adverse_event_scope,claim_ref,evidence_refs[]}`。工具对独立受试者的二项事件率用 `scipy.stats.beta` 给精确 Clopper–Pearson 区间；零事件时保存精确上界 `1-alpha^(1/n)`，只把 `3/n` 作为显示近似；person-time 用精确 Poisson 上界。重复测量不得膨胀 n。M7 新增 `safety_overreach`：仅当 claim 把范围扩成“安全/无风险”，而区间仍允许临床不可忽略风险，或把 animal NOAEL/HED 当成人体安全结论时立 finding。HED 只表示剂量缩放，不表示人体安全证据。
- **代价**：2–3 人日；0.5 人日契约，1 人日计算与 CLI，0.5–1.5 人日药物、器械、食品、动物到人体的 20 个困难正反例。
- **建议优先级**：P0 交付前先做 `0 events + n + exposure window`；person-time、分层安全性和 competing risk 为 P1。
- **分期 / 归属**：一期（不调用外部数据库）；M1 抽取，Stage 2 工具产 signal，M4 复核分母/区间，M7 判断安全 claim。M1 不产 finding。
- **契约字段**：`structured_result` 增 `safety_claim_contexts[]`；`extraction_signal.type` 增 `safety_precision_candidate`，条件块为 `{event_model,independent_n,event_count,person_time,confidence_level,upper_bound,claim_scope,rule_version}`；finding 增 slug 但基础形状不变。
- **假阳性**：中高。主动与被动监测、停药后随访、重复暴露、聚类和事件定义都会改变分母；任一项不明只产 `partial_extraction`。区间宽不等于稿件证明有害，只说明总体安全主张证据不足，默认 `major`，不得自动 `critical`。

### P2 · 专门因果设计的识别假设规则卡

- **问题**：§5.3 目前要求“逐项报告该设计的识别假设”，但没有逐设计字段；实现者无法知道 MR、DiD、RD、IV 与目标试验模拟各自要检查什么。只识别设计名称会让 `B` 路径成为新的免责关键词。
- **影响**：排除限制、水平多效性、平行趋势、阈值操纵、immortal-time bias 任一失效都可能翻转因果解释。缺少结构化 assumption card，会同时漏过伪因果和误伤合理的准实验研究。
- **方案**：**一期离线**新增 `resources/causal_identification_rules.json` 与 `scripts/causal_identification_audit.py`。首批规则卡固定：① MR：instrument relevance、population/ancestry、independence、exclusion restriction、directionality、horizontal pleiotropy 诊断及至少一种稳健估计；② IV：relevance、independence、exclusion、monotonicity 与 weak-instrument 诊断；③ DiD：平行趋势/事件研究、no anticipation、稳定样本构成、同时冲击、staggered adoption 处理；④ RD：running variable、cutoff 预设、密度/操纵、协变量连续性、带宽与函数形式敏感性；⑤ target trial emulation：eligibility、treatment strategies、time zero、follow-up、outcome、causal contrast、analysis plan 和 immortal-time 处理。规则只判断稿件是否报告并检验必要假设，不替作者证明不可检验假设为真。
- **代价**：3–4 人日；规则 JSON 1 人日，抽取/脚本 1–1.5 人日，至少 25 个真实方法段落与困难反例 1–1.5 人日。
- **建议优先级**：P1 应该做；先交 MR + DiD + target trial 三个语料常见切片。
- **分期 / 归属**：一期（不调用外部数据库）；M1/Stage 2 产无 severity signal，M4 检查分析实现，M7 判断 causal claim，不新增模块。
- **契约字段**：新增 `causal_design_specs[]:{design_family,estimand,assumptions[],diagnostics[],sensitivity_analyses[],evidence_refs[],extraction_status}`；signal 新增 `causal_identification_candidate` 与 `{rule_id,missing_assumptions[],failed_diagnostics[],claim_refs[],rule_version}`。
- **假阳性**：高。很多识别假设不可由单篇论文验证；“未报告”不等于“假设不成立”。缺报告只允许 `major` 候选并要求 absence 证据，只有稿件自己的诊断明确失败却仍直陈因果时才允许更高优先级；网络或外部复现不属于本组件。

### P3 · 证据合成能力继承与 Evidence-to-Decision 编译器

- **问题**：本轮把 E8 改为继承底层证据，但当前 `systematic_review/meta_analysis` 字段只保存检索、RoB 和 synthesis method，无法把每个 claim 绑定到 RCT/观察/动物设计分层、certainty、绝对获益/伤害与 EtD。Round 2 P1 解决 claim 多维化，本项解决 E8 特有的“合成不升级能力”。
- **影响**：观察研究 meta-analysis 会被误当临床疗效最高证据；scoping review 也可能凭 `should` 直接输出实践建议。Cochrane 的 certainty 需要按 outcome 评估 risk of bias、inconsistency、indirectness、imprecision 和 publication bias；推荐还需要获益-伤害、价值偏好、资源、可接受性、可行性与公平性，而不是多一层文献汇总。[Cochrane Handbook Chapter 14](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14)、[GRADE EtD](https://book.gradepro.org/guideline/introduction-to-the-evidence-to-decision-frameworks)
- **方案**：**一期离线**新增 `scripts/evidence_synthesis_claim_audit.py`。M1 为每个 synthesized outcome 抽取 `{included_design_strata,pooled_estimate,absolute_effects,certainty,risk_of_bias,inconsistency,indirectness,imprecision,publication_bias,benefits,harms,etd_dimensions,claim_refs}`。工具机械执行：① claim 只能继承实际 synthesis stratum 的 capability；②混合设计未分层为 `not_comparable`；③低/极低 certainty 不自动否定效应，但禁止确定性/普适性措辞；④ C6 只有 EtD 所需维度齐全时交人工，不自动通过；⑤ scoping/narrative review 不因检索广而获得 efficacy/recommendation capability。
- **代价**：2.5–3.5 人日；schema 与抽取 1 人日，继承/EtD 规则 1 人日，10–15 篇不同综述类型回归 0.5–1.5 人日。
- **建议优先级**：P0；当前 E8 是 §3.3 最容易被一篇观察 meta-analysis 击穿的行。
- **分期 / 归属**：一期（不调用外部数据库）；M1 抽取，Stage 2 工具产 signal，M4 复核 synthesis 数值，M7 判 finding。
- **契约字段**：扩展 `structured_result.design_specific` 为 `synthesis_claim_contexts[]`；新增 `evidence_synthesis_claim_candidate`，保存 `{claim_ref,synthesis_result_ref,inherited_capability,certainty_status,etd_completeness,rule_version}`。不新增记录类型。
- **假阳性**：中。作者可以合理总结低 certainty 证据，只要措辞反映不确定性；缺 GRADE 不等于结论错误。certainty 未报告时先人工，只有 claim 明确使用高确定性/推荐措辞且必要桥接缺失时才立 finding。

### P4 · Surrogate / 诊断性能 / 预后模型到临床效用的桥接审计

- **问题**：现 §3.3 脚注已承认 AUC、敏感度/特异度和校准不等于 clinical utility，但没有结构化 bridge。常见越界还包括 biomarker association → 可筛查、surrogate 改善 → 患者获益、预测模型 discrimination → 改善临床决策、target association → 可成药。
- **影响**：这些句子常使用 `potential` 而词面很谨慎，单轴 Δ 容易放行；真正缺失的是 analytical validity → clinical validity → clinical utility，或 surrogate → patient-important outcome 的证据边。
- **方案**：分两层。**一期离线**新增 `scripts/clinical_bridge_audit.py`，消费 Round 2 P2 尚未落地的 `support_edges[]`，将 bridge 固定为 `surrogate_to_patient_outcome`、`diagnostic_performance_to_utility`、`prognostic_association_to_actionability`、`target_association_to_druggability`；只有稿件实际给出直接管理/患者结局证据时才能跨到 C5/C6。**一期联网增强**在唯一 X1 下增加 `fda_surrogate_endpoint` query kind，对官方页面 `GET https://www.fda.gov/drugs/development-resources/table-surrogate-endpoints-were-basis-drug-approval-or-licensure` 做版本化表格快照，返回 disease/use、patient population、surrogate endpoint、approval type、mechanism 与 age range。该表命中只表示特定 regulatory context 有先例，不证明当前干预的临床获益；FDA 也明确逐项目决定适用性。[FDA Surrogate Endpoint Table](https://www.fda.gov/drugs/development-resources/table-surrogate-endpoints-were-basis-drug-approval-or-licensure)
- **代价**：离线 2–3 人日；FDA connector、HTML schema-drift fixture 与缓存另 1–1.5 人日。依赖 Round 2 P2 support edges 与 Round 12 X1 resolver，不得自行建立第二套 external evidence。
- **建议优先级**：P1；先交 surrogate/diagnostic 两类离线 bridge，FDA 正向先例查询随后。
- **分期 / 归属**：一期离线 + 一期可选联网增强；M1 抽取，X1 只产 external evidence/signal，M7 判 claim，不新增模块。
- **契约字段**：`claims[]` 增 `bridge_requirements[]` 或复用 `support_edges[].directness`；新增 `clinical_bridge_candidate:{bridge_type,source_endpoint,target_claim,bridge_evidence_refs[],missing_bridge,rule_version}`。external assertion 增 `{disease_use,population,surrogate_endpoint,approval_type,mechanism,age_range,table_version}`；`not_found/not_addressed` 不得成为 finding。
- **假阳性**：很高。一个 surrogate 在疾病、药物机制、阶段或人群改变后可能不再有效；FDA 表有命中也不等于当前 claim 成立，无命中更不是反证。所有外部对照先交人工；离线只有“稿件明确把 surrogate 当患者获益且没有任何 bridge”时才允许 `clinical_bridge_overreach`，默认 `major`。

## 未解决 / 需要人来定的问题

1. Round 2 P1 的 `claim_type/epistemic_strength/centrality/scope` 结构化迁移仍未实现；当前 schema 的 `scope` 还是自由字符串。若不采纳，§5.1 的八轴范围比较只能 fail closed，不能稳定自动执行。
2. Round 2 P2 的 `support_edges[]` 仍未实现；P4 不应另造第二套 claim 图。建议先落 `target_ref/directness/endpoint_role/analysis_role/evidence_refs` 最小字段。
3. `SKILL.md §2.9` 仍要求 M2–M7 并行，而 M7 §1/§6 必须消费封闭的 M2–M6 finding snapshot。Round 2 P6 的 Stage 4a/4b 屏障尚未采纳；在屏障落地前，`limitations_evasive` 与 §6 联动不能宣称可确定执行。
4. 当前 validator 会拒绝 finding 消费并行模块创建的 evidence；M7 应重新引用 Stage 1–3b 的稿件证据，而不是引用上游模块新建 evidence。若上游 finding 只有模块本地 evidence，需由 Round 16 P3 的中央 registry assembler 重映射后再运行 M7。
5. 本轮真实语料显示 safety、recommendation、biomarker/target claim 已经出现；Round 2 P3 的 40 条 M7 双人回归集仍未落地。建议先把上表五例作为 seed，但不得把“已发表”或本轮判断本身当 gold，仍需双人独立裁决。
