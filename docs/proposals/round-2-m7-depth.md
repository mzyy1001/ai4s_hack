# Round 2 · M7 结论与讨论规则库深度 提案

## 摘要

M7 现有单轴 `E0–E8 → C0–C6` 把机制、因果、转化、诊断与推荐当成同一序数轴，无法稳定表示“细胞内因果成立但不能推到患者”这类生物医学常见边界；本轮先修掉明确误判，完整多维化列为 P0。
主文档要求 M2–M7 全并行而 M7 又要求最后消费 M2–M6，现有调度无法实现；同时旧 §5/§6 会把抽取失败、上游 severity 和关键词命中级联成稿件缺陷，本轮已先阻断自动升级并提出两波 Stage 4。
Round 1 的 UCUM 最小归一化器与确定性统计取证已被采纳（`tools/normalize_biomed_units.py`、`tools/statistical_forensics.py` 及四类 signal）；本轮不重复，新增 M7 claim 图、真实文献回归集、化合物活性核验和抗体身份核验。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/07-conclusions-discussion.md` | 开头、§2.1–§2.2 | 修正 §11 引用；claim 位置不再默认取 `evidence_refs[0]`；`claims=[]` 时终止 M7 并返回编排器，不再自创“观察”或把抽取失败写成 finding | 旧流程既引用失效，又违反三类记录和 system limitation 产出者边界 |
| 同上 | §3.3 | 允许有 rescue/正交干预的细胞内因果；拆分单臂与非随机对照干预；单个 RCT 不再自动支持推荐；普通 meta-analysis 不再直陈推荐；重写诊断准确性脚注 | 旧表既误伤合格细胞机制实验，也把单臂响应、单个 RCT 和普通 meta-analysis 的证据能力抬得过高 |
| 同上 | §3.4 | 取消 scope、Abstract 位置和“未来方向”对 Δ 的重复减加；把 Abstract 改为人工复核优先级；限定 critical 的两种条件 | 同一句话不会因出现在摘要就科学上更错误；scope 限定也不能把“临床疗效”降成“机制” |
| 同上 | §4 | hedging 改按核心谓词作用域和否定解析；`is associated with` 改为 `C1 + assertive` | `demonstrate that X may...`、`did not demonstrate...` 会被旧“直陈词优先”规则误伤 |
| 同上 | §5.1–§5.3 | 增加范围轴越界；`ambiguous/parse_failed` 不再触发 unsupported；量级不符回到 `claim_magnitude_mismatch`；观察性因果改成常规纵向路径与专门因果设计路径 | 旧规则把系统能力限制升级为 critical，并用“时序+校正+剂量反应”三项清单错误裁决 MR、自然实验和目标试验模拟 |
| 同上 | §5.4–§5.5 | 补齐 `not superior/similar/comparable` 等不显著误读；明确事后效能不能证明等效；“统计学显著”不再自动等于夸大，MCID 只用于适用终点 | 旧规则漏掉真实文献常见 spin，同时会把正常的 statistical significance 表述判错 |
| 同上 | §5.6–§5.8 | `limitations_evasive` 限定为三类可披露推断边界，并要求“问题域+影响”同时成立；`selective_citation` 改为 `selective_result_interpretation` | 关键词命中会把“样本量足够”误判成已承认局限；一期没有外部检索，不能声称判了选择性引用 |
| 同上 | §6、§8–§10 | 上游联动增加四道门，不再复制 severity；M3/M4 slug 与各自 reference 对齐；补齐 8 条规则的正反例并更新 TODO | 原表引用 4 个不存在 slug，且一个上游 critical 可以把同锚点 claim 机械升级为 critical |

## B 类提案

### P1 · 把单轴层级改成多维 claim–evidence adequacy

- **问题**：`C2 机制`、`C3 因果`、`C4 转化潜力`、`C5 临床疗效`并非严格递增关系。一个带 rescue 的 CRISPR 细胞实验可支持“在该细胞中 X 导致 Y”，却不能支持患者疗效；一个大型诊断准确性研究也不能自然映射到“关联→疗效”轴。当前 `claim_tier/assertion_mode/scope_qualified/location` 还是 M7 运行时变量，schema 没有保存，复核者无法复算 Δ。
- **影响**：相同句子会因实现者对 tier 的理解不同而得到 major 或 critical；评委用一篇 preclinical paper 加一篇诊断 paper 就能暴露规则只是语言层级启发式，不是生物医学证据模型。
- **方案**：一期修改 `01-structured-extraction.md §5.1.5`、`07-conclusions-discussion.md §2–§5`、`structured_result.schema.json` 与 fixtures。为 `conclusion.claims[]` 新增：
  - `claim_type`: `descriptive` / `association` / `mechanism` / `causal_effect` / `diagnostic_performance` / `prognostic_performance` / `therapeutic_efficacy` / `safety` / `clinical_utility` / `clinical_recommendation`；
  - `epistemic_strength`: `assertive` / `hedged`；
  - `centrality`: `primary` / `secondary` / `exploratory`；
  - `location`: `abstract` / `results` / `discussion` / `conclusion`；
  - `scope`: `{species, model_system, population, intervention, comparator, endpoint, dose, time_window}`，每项允许 `null`，但对象必填；
  - `evidence_capabilities[]`: `association` / `within_model_mechanism` / `within_model_causal_effect` / `human_causal_effect` / `clinical_efficacy` / `clinical_utility` / `recommendation_support`。
  M1 只抽取这些属性，不产 finding；M7 用“claim_type 所需 capability 是否存在 + scope 是否蕴含”判定。保留 `claim_tier` 仅作迁移期展示字段，一个版本后删除，停止使用整数 Δ 评分。
- **代价**：2–3 人日；需要 schema migration、4 个 fixtures 和 M7 示例同步。M1 负责人需确认字段抽取，M7 负责人定义 capability 判据。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M1/Stage 3b 产结构化属性，M7 判稿件问题。
- **契约字段**：只扩展 `claims[]`，不新增顶层记录；finding 继续只用现有字段和 `evidence_refs[]`。
- **假阳性**：中。任何 scope 轴为 `null` 时禁止自动断言“范围扩大”；`clinical_utility` 与 `clinical_recommendation` 必须交人工复核，直到回归集达到预设精度。

### P2 · claim 支撑边与五类生物医学越界审计器

- **问题**：`supported_by[]` 只有裸 id，无法表达“直接/间接”“主要/探索”“支持/矛盾”“哪个实验组件”。M7 因而不能可靠发现 surrogate→患者获益、亚组→总体、复合终点→单一成分、单剂量→全剂量和单时间点→持久疗效这些常见越界。
- **影响**：系统可能抓得到夸张动词，却漏掉措辞温和但 estimand 已被偷换的结论；这正是专业审稿人与套壳语言模型的分界。
- **方案**：一期在 `conclusion.claims[]` 新增 `support_edges[]`，元素为 `{target_ref, experiment_id, relation, directness, endpoint_role, analysis_role, evidence_refs}`：
  - `relation`: `supports` / `contradicts` / `context_only`；
  - `directness`: `direct` / `surrogate` / `mechanistic_bridge`；
  - `endpoint_role`: `primary` / `secondary` / `exploratory` / `composite` / `component`；
  - `analysis_role`: `prespecified` / `post_hoc` / `unclear`。
  新增 `tools/audit_claim_scope.py`，只生成 M7 内部候选，由 M7 读取原文证据后决定 finding。固定检查：① preclinical→human；② surrogate→clinical outcome；③ subgroup→overall population；④ composite↔component 偷换；⑤ dose/time/species 扩张。修改 `01 §5.1.5`、`07 §5.1/§5.7`、`structured_result.schema.json`、`validate_schemas.py`，并为每类加正反例 fixture。
- **代价**：3–4 人日；依赖 P1 的 scope 字段。脚本本身标准库可实现，语义边仍需 M1 抽取。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M1 产支撑边，M7 消费。脚本不产 finding，不带 severity。
- **契约字段**：扩展 `claims[]`；可保留旧 `supported_by[]` 为 `support_edges[].target_ref` 的去重投影，兼容现有消费者。
- **假阳性**：中到高。`analysis_role=unclear`、scope 缺值或 surrogate 是否经验证不明确时，只列入 M7 人工候选，不自动立 finding。

### P3 · 真实文献回归集与 M7 判据门槛

- **问题**：§10 仍未在 10 篇语料上标注，现有正反例都是合成句，无法证明规则对真实摘要、否定作用域和跨句支撑有效。
- **影响**：没有可复跑的混淆矩阵，评委无法判断“规则多”究竟是覆盖深还是误报多；后续任何词表修改都可能悄悄破坏已修复边界。
- **方案**：一期新增 `tools/fixtures/m7_case_*.json` 与 `tools/evaluate_m7_cases.py`。每例保存论文标识符、claim 短句、设计、相关结果、人工 gold category、gold severity、是否必须人工及证据定位；脚本报告每条规则的 precision/recall 和错误清单。首批必须包含下列真实文献压力测试（这里只评价 claim↔paper data 的对齐，不据此指控论文整体无效）：

  | 文献与短句 | 越界类型 | 修补前能否抓到 | 本轮规则 | 结论 |
  | --- | --- | --- | --- | --- |
  | Almatroodi et al., *Efficacy of resveratrol against breast cancer and hepatocellular carcinoma cell lines*：结论称其为“excellent candidate agent”用于“various human cancers” [原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10043901/) | 两个细胞系→多种人类癌症治疗候选，范围轴扩张 | **不能**；E2 的 hedged 上限 C4 会放行 | §5.1 新增 model/species/disease scope 扩张 | **现在能抓**，major；P1/P2 后可稳定复算 |
  | Thomusch et al. HARMONY RCT：以 RR 1.13、95% CI 0.63–2.00 得出 incidence “not reduced” [DOI](https://doi.org/10.1016/S0140-6736(16)32187-0)；该实例由 [BMJ Open 方法学复核](https://pmc.ncbi.nlm.nih.gov/articles/PMC6738699/) 明确指出 | 不显著→无获益 | 能抓一般 `no effect`，但词形覆盖不稳定 | §5.4 覆盖 `not reduced/no benefit`，要求 CI/等效界 | **能抓**，major |
  | Johnston et al. SOCRATES RCT：HR 0.89、95% CI 0.78–1.01，却写 ticagrelor “not found to be superior” [DOI](https://doi.org/10.1056/NEJMoa1603060)；同一 [方法学复核](https://pmc.ncbi.nlm.nih.gov/articles/PMC6738699/) 认为这种结论未反映方向与不确定性 | 未跨 0.05→“不优于” | **不能稳定抓**；旧词表没有 `not superior` | §5.4 已补该谓词族 | **现在能抓**，major |
  | Kato et al., surgeon birthday observational study：结论写 performance “might be affected” [原文](https://www.bmj.com/content/371/bmj.m4381) | 负对照：谨慎的观察性解释 | **会误伤**；旧 §5.3 要求三项同时满足 | §5.3 改为设计专属识别假设，且 hedging 不自动定错 | 应交人工或不报，禁止自动 critical |

  首批至少 40 条 claim：每条自动规则 ≥5 正例、≥5 困难反例。自动生成 major/critical 的启用门槛为该规则在双人 adjudication gold 上 precision ≥0.90 且无“系统限制→稿件 finding”错误；未达标只能生成强制人工候选。
- **代价**：2 人日标注 + 1 人日脚本；需要两名生物医学审稿者盲标，分歧由第三人裁决。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M7 评测基础设施，不进入生产报告。
- **契约字段**：不改生产契约；fixture 使用独立测试 schema，validator 只新增严格检查，不放宽现有规则。
- **假阳性**：这是控制假阳性的门禁。未达 precision 门槛的规则不得自动出 finding。

### P4 · ChEMBL + PubChem 化合物活性数量级核验

- **问题**：论文常用“nanomolar inhibitor”“highly selective”“potent at clinically relevant concentration”等结论，但盐型/立体化学、靶点物种、assay 类型和 `IC50/Kd/Ki/EC50` 不可混比。Round 1 的 X1 没覆盖化合物活性。
- **影响**：数量级写错、把细胞毒性当靶点抑制、把 μM 写成 nM 会直接破坏机制或转化结论；简单按化合物名搜索又会制造严重假阳性。
- **方案**：二期在 Round 1 P4 已提的 X1 中新增 `compound_activity` connector：
  1. PubChem 用 `GET https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON` 固定结构身份；官方 PUG REST 定义 name/CID 输入、property 输出和 5 req/s 限速，见 [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)。名称返回多结构、盐型不明或手性冲突时停止自动比较。
  2. ChEMBL 用 `/chembl/api/data/molecule/search.json?q={name}`、`target/search.json?q={target}` 解析 id，再查 `/activity.json?molecule_chembl_id=...&target_chembl_id=...&standard_type=IC50`；接口实体与 activity 端点见 [ChEMBL REST API](https://www.ebi.ac.uk/chembl/api/data/docs)。保存 `standard_type/value/units/relation`、`pchembl_value`、assay type、assay/target organism、target confidence、cell line 与文献 id。
  3. 只有结构身份一致、端点类型相同、靶点/物种一致、单位可由现有归一化器确定转换时比较。按可比 assay 分层报告外部范围与稿件值，不跨 biochemical/cellular assay 合并中位数。
  4. X1 产 external evidence 与 `bioactivity_outlier_candidate` signal，路由 M3/M7；M7 只有在论文明确援引“已知活性数量级”且至少两条独立可比记录与稿件相差 ≥100 倍时，才能立最高 `major + review_confidence=medium` finding，否则仅交人工。
- **代价**：4–5 人日；依赖 Round 1 的 external evidence 决策、缓存/限速与化学结构消歧。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；X1 connector + M3 材料核验 + M7 转化/机制主张核验，不新增审核模块。
- **契约字段**：复用 Round 1 P4 的 external evidence，扩展 `entity_identity:{pubchem_cid,inchikey,stereo_status,salt_status}`、`assay_context:{standard_type,assay_type,target_id,target_organism,cell_id,comparability}`；signal enum 新增 `bioactivity_outlier_candidate`。finding 仍须同时引用稿件内 claim 与数值证据。
- **假阳性**：高。数据库无记录、单条记录、靶点复合物不同、ATP 浓度不同、细胞通透性差异、活性/结合端点不同都不得判矛盾；只形成带 comparability 原因的人工复核候选。

### P5 · RRID 抗体身份与实验适用性核验

- **问题**：Methods 中抗体货号、RRID、靶蛋白、宿主、反应物种和应用类型经常错配。抗体存在于目录不代表对 WB/IHC/IF/flow 或目标物种已经验证，单靠 LLM 记忆既不可审计也会误伤。
- **影响**：若核心 Western blot 或 IHC 用错反应物种/靶点，M7 机制链可能失去直接支撑；若系统把“无验证信息”写成“无特异性”，同样会严重冤枉稿件。
- **方案**：二期扩展 Round 1 X1：
  1. 有 RRID 时调用 `GET https://scicrunch.org/resolver/RRID:AB_{id}.json`；Antibody Registry 官方 FAQ 明确记录可通过 resolver 加 `.json`/`.xml` 无登录读取，见 [Antibody Registry FAQ](https://www.antibodyregistry.org/faq)。返回 proper citation、vendor、catalog number、target antigen、host organism、target organism、clone、applications、alerts 与更新时间。
  2. 只有 vendor+catalog 无 RRID 时用带 API key 的 SciCrunch 搜索；候选不唯一时停止，不凭名称挑第一条。home-made antibody 或停产货号不得判“不存在”。
  3. 与稿件抽取的 `{vendor,catalog,rrid,target,host,target_species,application}` 逐字段对照。RRID 指向不同 catalog/target 或明确不支持稿件目标物种时出 `reagent_identity_mismatch_candidate`；“applications 未列 WB”只能出 `application_validation_unresolved`，不能断言抗体无效。
  4. signal 路由 M3；只有 M3 以原文和外部记录确认身份错配，且该抗体结果是 claim 的全部直接支撑时，M7 才按 §6 判断 `unsupported_claim`，不得从 X1 signal 直接立 finding。
- **代价**：3–4 人日；需要 API key 管理、缓存与 RRID/vendor/catalog 归一。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；X1 + M3，M7 仅消费已确认的同锚点 finding。
- **契约字段**：external evidence 增加 `resource_id`、`vendor`、`catalog_number`、`target_antigen`、`host_organism`、`target_organisms[]`、`applications[]`、`alerts[]`；新增两种 signal。三类记录不变。
- **假阳性**：高。目录用途是厂商/登记信息，不是独立特异性证据；应用未列出、无 alerts、无引用都只能表示未知。只有精确 RRID 的身份字段直接冲突才允许自动候选，所有有效性判断交实验审稿人。

### P6 · Stage 4 两波执行屏障

- **问题**：`SKILL.md §2.9` 规定 M2–M7 六模块并行；`07-conclusions-discussion.md §1/§6` 又规定 M7 最后运行并消费 M2–M6 findings。两个执行模型不能同时成立。
- **影响**：严格并行时 M7 看不到上游 findings，§5.6 与 §6 实际永不触发；允许 M7 读取正在写入的数组则会出现同一论文多次运行结果不同的竞态。评委会把这是“规则写了但调度不可能实现”的架构硬伤。
- **方案**：一期把 Stage 4 拆成内部两波，不新增对外 stage enum：`stage_4a` 语义波由 M2–M6 并行，全部完成后建立不可变 `upstream_findings_snapshot`；`stage_4b` 只运行 M7，读取 v2、图表、signals 与该快照。对外 `execution_scope.executed_stages` 仍记录 `stage_4`，避免 schema migration。修改 `SKILL.md §2.3/§2.9`、`07 §1/§6` 与 `00-contracts.md §9.2`；validator 增加“执行 M7 时 M2–M6 快照已封闭”的模拟检查。targeted M7 若没有执行全部 M2–M6，必须声明 `upstream_modules_available[]`，§5.6/§6 只对可用模块运行，风险分仍按 partial 规则。
- **代价**：0.5–1 人日；需要编排器加一次 barrier 和一条 targeted 模式测试。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；Stage 4 编排，不新增审核模块。
- **契约字段**：优先只在 Stage 4 内部上下文新增 `upstream_findings_snapshot` 与 `upstream_modules_available[]`，不进入三类顶层记录；若需要报告可审计性，再扩展 `execution_scope`，不得把它们称为记录。
- **假阳性**：不直接产生稿件判断。快照屏障减少不完整输入造成的级联误判；未运行的上游模块必须 skip，不得按“无 finding”处理。

## 未解决 / 需要人来定的问题

1. 是否在初筛前接受 P1 的 `claims[]` schema migration；若不接受，本轮修订后的 Δ 只能作为临时 triage，不能宣称是稳定证据模型。
2. P2 的 `support_edges[]` 是替代 `supported_by[]`，还是先作为并行字段保留一个版本；建议并行一版并由 validator 强制投影一致。
3. `07 §11.4` 的 external evidence 示例仍写 `created_by: "M7"`，与现有 evidence 的 stage 产出者模型不一致。Round 1 已提出 `stage_3c` 但尚未拍板；在决定 producer id 前不得实现 P4/P5，也不要让 M7 连接器自行写证据。
4. M4 仍是骨架，M7 虽已对齐当前 `wrong_test/sample_size/no_multiple_comparison_correction` slug，但 M4 负责人若改名，必须同步 `07 §5.5/§5.6/§6` 和回归 fixtures；禁止兼容多个别名。
5. P3 自动 major/critical 的 precision 门槛是否接受 0.90；若评委更看重不冤枉稿件，建议 critical 单独设为 0.95。
6. 是否接受 P6 的两波 Stage 4；若坚持全并行，必须删除 M7 对上游 findings 的消费和 `limitations_evasive`，两者不能并存。
