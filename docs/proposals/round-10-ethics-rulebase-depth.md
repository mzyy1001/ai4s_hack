# Round 10 · 伦理规范库深度与准确性 提案

## 摘要

规范库存在两处可证伪的法源错误：把中国 2023 年《伦理审查办法》第32条写成知情同意豁免，并把实验动物许可证归到并不直接规定该制度的法规；本轮已纠正并更新 2024/2025 修订状态。
更危险的不是少几条法规，而是执行语义过浅：多数规则声明必须报告两个以上要素，筛查器却把任意非空 `reported` 字段当作全部满足，`ETH-HUM-006` 等规则因此几乎不可执行。
下一步应优先交付要素级伦理授权对象、法域/时间路由与材料来源闭环；外部查询只增强证据，查询失败必须降级为 `system_limitation`。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/resources/ethics_rules.json` | `instruments` | 新增《科技伦理审查办法（试行）》《实验动物许可证管理办法（试行）》和《人类遗传资源管理条例实施细则》；把中国人遗条例更新为 2024 修订及国家卫健委主管，把病原微生物条例更新为 2024 修订，把 ISSCR 标为 2025 定向更新 | 原库漏掉直接法源，并把旧版本/旧主管部门当成当前状态 |
| 同上 | `ETH-HUM-001`–`ETH-HUM-008` | 用 2024 版赫尔辛基宣言第23、25–32、35段替换旧版模糊定位；把 CIOMS Guideline 9/10/15/17/24 提升为精确定位；删除 `ETH-HUM-003` 对中国第32条的错误引用；把中国弱势群体、未成年人和知情同意定位到第17、33–38条 | 第32条是“免除伦理审查”，不是“免除知情同意”；两者混用会给出错误法律结论 |
| 同上 | `ETH-HUM-004`、`ETH-ANI-002` | 单缺赫尔辛基宣言名称从 `minor` 降为 `info`；单缺 3R 表述从 `major` 降为 `minor`，并禁止用零散福利措施推定“全部 3R 已满足” | 名称缺失不等于未获审查；replacement 属立项判断，不能从论文没写“3R”反推未实施 |
| 同上 | `ETH-ANI-001`–`ETH-ANI-006` | ARRIVE 改为真实 item：伦理声明是 Recommended Set 14，动物信息是 Essential 10 Item 8，实验程序是 Item 9；中国动物伦理改引科技伦理办法，许可证改引 2001 年许可证办法 | 原 `Essential 10 — Ethical statement` 不存在，且许可证法源错位 |
| 同上 | `ETH-CELL-001`–`ETH-CELL-004` | 人源材料定位到赫尔辛基 2024 第1/32段和中国办法第3/32/51条；`ETH-CELL-003` 改为 `manual_only`，区分 ISSCR Category 1A 常规培养与 Category 2；14天规则定位到 ISSCR Recommendation 2.2.2.1 与中国第6条第1项 | 仅出现 hESC 名称不能推出必须专门持续审查，更不能自动定 `critical` |
| 同上 | `ETH-HGR-001`、`ETH-HGR-002` | 人遗要求拆成采集/保藏、国际合作、材料出境、信息对外提供，明确普通境内利用不当然需要行政许可；名古屋规则明确不自动套用于人类遗传资源 | 旧文本把“使用中国样本”与“须行政许可”混为一谈，会误报大量普通境内研究 |
| 同上 | `ETH-BIO-001` | 精确到病原微生物条例第4–5、18–29条，并明确灭活样本、非复制型载体、质粒和无感染性假病毒不按活病原体触发 | 原关键词 `virus/infect` 会把常规载体和假病毒论文推入 BSL 缺失路径 |
| 同上 | `exempt_cell_lines` | 移除通常属于原代材料的 HUVEC；把名单定位为“名称召回”而非合规白名单，禁止命中一个名称后压制同文原代材料；名称数由30改为29 | HUVEC 无条件豁免是实质错误；盲目扩到 100+ 会放大同名、衍生株和来源不明风险 |
| `skills/biomed-paper-review/scripts/ethics_compliance_check.py` | `derive_facts()`、`manual_only`、自检 | 细胞系改为实体边界匹配，避免 `CHO` 命中 `chondrocyte`；补 HUVEC、混合患者材料和假病毒负例；病原体泛称改为不确定；人工规则改产 `partial_extraction`，不再冒充 `ethics_requirement_unmet` | 修掉三类真实论文中高频的假阳性路径，并维持“未判定不等于未满足” |
| `skills/biomed-paper-review/references/06-ethics-compliance.md` | §2–§4、§6–§7 | 同步 28 部规范、4 条 `manual_only`、severity、细胞系边界与已核实/待核实引用；停止“名单扩到100+”路线 | 主文档必须与规则库和当前法源一致，且不能把人工候选写成自动定性 |
| `skills/biomed-paper-review/SKILL.md` | 资源索引 | 规范数 25 改为 28 | 修复静态计数漂移 |

## B 类提案

### P1 · 要素级 `ethics_authorization_record` 与可执行规则编译器

- **问题**：当前 `field_present` 只检查字段 `status == reported`。因此 `declarations.ethics_statement = "approved"` 即使没有委员会名称、批件号、适用实验和日期，也会让 `ETH-HUM-001` 静默通过；`ETH-HUM-006` 虽要求 `vulnerable_group_safeguards + proxy_consent_arrangement`，实际检查的却是必然已有的人群描述。`manuscript_must_report[]` 目前只是展示文本，不参与计算。
- **影响**：评委给一个“写了伦理二字但没有任何可核验授权信息”的稿件即可击穿规则库。22 条规则看似专业，真实 uplift 接近零，直接损失工程质量、证据链与 Skill 复用分。
- **方案**：**一期离线，M1 抽取 + M6 消费，P0**。在 `structured_result` 新增 `ethics_authorization_records[]`，每条固定为 `{record_id,authorization_kind,subject_scope,experiment_refs[],jurisdiction,authority_name,identifier,decision,decision_date,validity_interval,consent_mode,waiver_basis,source_or_use_scope,evidence_refs[],extraction_status}`。`authorization_kind` 至少区分 `human_ethics_approval/animal_protocol/informed_consent/waiver_of_consent/waiver_of_documentation/exemption_from_ethics_review/hgr_approval/hgr_filing/biosafety_authorization/stem_cell_oversight`；禁止再把三种 waiver 合并成一个布尔值。新增 `resources/ethics_rule_checks.json`，规则使用封闭算子 `all_present/any_present/value_in/date_before/scope_covers`，把 `manuscript_must_report` 编译成真实要素断言。新增 `scripts/compile_ethics_rules.py` 检查未定义字段、永真规则、不可达规则、`manual_only` 无触发事实、法域规则无 jurisdiction gate；新增 `scripts/ethics_authorization_audit.py` 只产 signal。修改 `01-structured-extraction.md`、`06-ethics-compliance.md §1–§3`、`structured_result.schema.json`、`extraction_signal.schema.json`、fixtures 与 validator。
- **代价**：3–4 人日；1.5 人日 schema/M1 迁移，1 人日规则编译器，1–1.5 人日 30 个要素级正反例。现有 `declarations.*` 保留一个迁移版本，只作为原文摘要，不再作为要素完整性的唯一依据。
- **建议优先级**：P0 交付前必须做；最小版先覆盖 `ETH-HUM-001/002/003/005`、`ETH-ANI-001`、`ETH-CELL-001`。
- **阶段 / 归属**：一期；M1/Stage 2 抽取与产 signal，M6 唯一产 finding。M1 仍不产 finding。
- **契约字段**：扩展 `structured_result` 和现有 `ethics_requirement_unmet` 的 `ethics` 块，增加 `{requirement_results[],missing_elements[],applicability_facts[],rule_version}`；不新增顶层记录类型。
- **假阳性**：中高。一个委员会可能批准多实验，多中心可有主审/确认审查，批件号格式也无法跨机构统一。只有 `scope_covers` 有明确文本证据时才判满足或矛盾；范围/日期缺失为 `partial_extraction`，不得自动判“未获批准”。

### P2 · 中国法规的法域、日期与技术路径路由包

- **问题**：中国规则现在只有一个粗粒度 `jurisdiction_hint`，无法区分研究实施地、样本来源地、机构所在地、境外合作和论文发表时间。更关键的是，2026年5月1日已施行《生物医学新技术临床研究和临床转化应用管理条例》，对作用于人体细胞/分子层面的新技术建立了伦理审查、学术审查、备案、书面同意和方案变更再审路径；当前规则库完全未覆盖。2026年5月发布的人遗实施细则仍是征求意见稿，若直接覆盖现行 2023 版同样会出错。
- **影响**：干细胞、体细胞、基因编辑、组织工程和其他新技术临床研究是中国生物医学伦理的高风险核心场景。漏掉已生效行政法规会被领域评委立即发现；把征求意见稿当现行法或把药械试验误路由到新技术路径则会给出错误合规结论。
- **方案**：**一期离线规则路由 + 一期联网增强，M1/M6，P0/P1**。新增 `regulatory_context:{study_sites[],sample_origin_countries[],sponsor_control_countries[],first_activity_date,manuscript_date,technology_path,technology_path_basis,evidence_refs[]}`；`technology_path` 固定为 `drug/device/biomedical_new_technology/ordinary_research/ambiguous`。离线规则包新增《生物医学新技术临床研究和临床转化应用管理条例》及 2026 年第4号实施公告，重点编码第8、14–19、25–27条；药品/器械路径命中第55条排除，不得双重处罚。纳入《科技伦理审查办法（试行）》附件七类高风险活动，先输出 `expert_review_required` 候选。日期路由按 `effective_from/effective_to` 选择规则版本，征求意见稿只能存 `draft_monitoring`，不得进入 finding。联网增强复用 Round 4 P1 的 X1，不新建证据架构；对官方国家医学研究登记备案信息系统 `https://www.medicalresearch.org.cn` 只查询公开记录，若没有稳定公开 API 或查询被拦截则产 `system_limitation`，禁止抓私有接口或把无结果记为未备案。法源依据：[国务院令第818号](https://xzfg.moj.gov.cn/front/law/detail?LawID=1781)、[国家卫健委2026年第4号公告](https://www.nhc.gov.cn/qjjys/c100016/202604/4238842553fd41a9a80c289c5132fc78.shtml)、[科技伦理审查办法](https://www.most.gov.cn/xxgk/xinxifenlei/fdzdgknr/fgzc/gfxwj/gfxwj2023/202310/t20231008_188309.html)。
- **代价**：2–3 人日完成离线路由和 12 个技术路径 fixture；公开登记查询另需 1–2 人日，依赖 Round 4 X1 schema 落地与官方公开查询稳定性。
- **建议优先级**：P0 先交离线法域/日期/技术路径；备案查询为 P1 一期联网增强。
- **阶段 / 归属**：M1 抽 `regulatory_context`，X1 可选取公开记录，M6 结合稿件内证据判定。
- **契约字段**：扩展 `structured_result`；外部部分严格复用 Round 4 的 `external` evidence、`external_validation_candidate` 和 `external_validation_coverage`，不另造 connector 契约。
- **假阳性**：高。细胞治疗可能走药品路径，器械组合产品也可能走器械路径；论文发表晚于法规生效不代表实验实施时已适用。`technology_path` 或 `first_activity_date` 不明确时只交人工；外部系统零结果不能证明未备案。

### P3 · 伦理批准—招募—采样—方案变更的时间与范围对账

- **问题**：当前只检查“有没有批件”，不检查批件是否覆盖该实验，也不检查批准日期是否早于首例入组/首份样本采集。多中心研究还常出现主中心批准、分中心确认、豁免与方案修订混在一段文字里的情况。
- **影响**：批准晚于研究启动、动物方案号覆盖错物种、旧批件被用于新增侵入性采样，都是伦理秘书会优先核对的硬问题；裸模型难以建立逐实验时间线。反过来，仅因论文没有写日期就推定追认审批，会造成严重名誉风险。
- **方案**：**一期离线，Stage 2 工具层 + M6，P1**。在 P1 记录上新增 `research_events[]:{event_id,event_type,experiment_ref,site_ref,date_or_interval,evidence_refs[]}`，事件至少覆盖 `first_recruitment/first_sample_collection/first_animal_procedure/protocol_amendment/approval/continuing_review/reconsent`。新增 `scripts/ethics_timeline_audit.py`：仅对同一 `site + experiment_ref + authorization_kind` 比较；确定 `approval_date > first_activity_date` 时产 `approval_after_activity_candidate`，方案实质变更晚于相应批准时产 `amendment_scope_candidate`，批准有效期无法覆盖活动时产 `authorization_validity_candidate`。同一批件号跨人体和动物仅作 `scope_mismatch_candidate`，不得按字符串相同直接定错。
- **代价**：2–3 人日；依赖 P1，需处理不完整日期、区间日期、多中心和续审。至少 20 个 fixture，其中一半为合理例外。
- **建议优先级**：P1 应该做；它是规则库从“关键词检查”升级为确定性证据链的高 uplift 组件。
- **阶段 / 归属**：一期，无外部数据库；工具层产 signal，M6 产 finding。
- **契约字段**：新增嵌套 `research_events[]`，signal 的 `ethics.timeline_check` 保存 `{authorization_ref,event_ref,comparison,assumptions,rule_version}`；扩展现有 signal，不新增第四类记录。
- **假阳性**：高。论文中的年份常是获批年度而非精确日期，样本可能来自已批准生物样本库，分中心可依赖主审加本地确认。只有完整日期、范围和站点全部可比时才生成 mismatch candidate；日期缺失只列人工索取项。

### P4 · 基于 accession 与来源授权的细胞材料豁免器（扩展 Round 1 P5）

- **问题**：29 个字符串只能避免少数明显误报，不能证明细胞身份、来源、供者可识别性或允许用途；继续扩到 100+ 会把名称歧义、误认细胞系和原代衍生株一并放进豁免。Round 1 P5 已提出 Cellosaurus 身份核验，但没有定义 M6 如何消费其结果来决定伦理豁免。
- **影响**：ATCC/DSMZ/JCRB 购得的既有细胞系、人源生物样本库细胞株、患者来源 organoid 和新鲜 HUVEC 的伦理义务完全不同。只看名称会同时误伤合规细胞系论文并放过新增供者材料。
- **方案**：**一期离线保底 + 一期联网增强，M1/X1/M6，P1**。不重复建设 Round 1 的 Cellosaurus connector；在其上补 `biomaterial_sources[]:{material_id,reported_name,material_class,provider,catalog_number,rrid,cvcl,donor_linkage,identifiability,acquisition_type,consent_or_authorization_scope,mta_restrictions,evidence_refs[]}`。`material_class` 区分 `established_cell_line/primary_cells/tissue/organoid/biobank_line/engineered_derivative/unknown`。有 `CVCL` 时调用既有端点 `GET https://api.cellosaurus.org/cell-line/{accession}?format=json`，只取推荐名、同义名、物种、来源类别和 problematic/misidentified 标记形成 external evidence；数据库记录不证明伦理授权。豁免仅在论文内 provider/catalog 或 repository provenance 明确、`donor_linkage != identifiable`、用途在授权范围、且研究材料集合中每一项均满足时成立。任一 `unknown` 即不压制规则，并输出 `partial_extraction`，而不是立 finding。
- **代价**：2–3 人日；依赖 Round 4 X1 与 Round 1 P5 connector，新增 M1 材料集合抽取和 15 个混合材料 fixture。
- **建议优先级**：P1 应该做；交付前不应扩充字符串名单。
- **阶段 / 归属**：M1 抽材料来源，X1 解析身份，M3 消费误认/污染状态，M6 只消费 donor linkage、来源和授权范围。
- **契约字段**：扩展 `structured_result.biomaterial_sources[]`；复用 external evidence。M6 signal 增 `ethics.exemption_basis_refs[]`，finding 仍须引用稿件内 evidence。
- **假阳性**：高。Cellosaurus 的 `problematic` 不等于伦理不合规，catalog 存在也不证明本实验实际购自该供应商；作者自建衍生株可能仍合法。外部命中只解决身份候选，不自动授予豁免；来源或用途无稿件内证据时交人工。

### P5 · 可复现的法源锁文件与规则库 lint

- **问题**：`citation_confidence` 目前靠人工记忆维护，无法证明某次审稿使用了哪一版官方文本，也无法自动发现 URL 失效、主管部门变更或规则引用不存在的 instrument。此次 2024 人遗/病原微生物修订和 2025 ISSCR 更新正说明静态 JSON 会迅速陈旧。
- **影响**：规范库是本 Skill 的核心差异化资产；若条款错一处，25% 科学可信性比多加十条规则更容易失分。运行时联网查询法源又会让同一稿件的结果随网页变化，破坏可复现。
- **方案**：**一期构建时联网、运行时离线，M6 基础设施，P1**。新增 `scripts/audit_ethics_rulebase.py` 与 `resources/ethics_sources.lock.json`。锁文件对每个 instrument 保存 `{instrument,official_url,title,issuer,effective_from,effective_to,status,retrieved_at,content_sha256,locus_ids[],verification_status}`；只锁官方发布页/PDF，不复制全文。脚本检查：所有 citation 的 instrument 存在、`locus` 非空、`medium/low` 不得被标 `auto_actionable=true`、草案不得进入现行规则、同一法域日期区间不得重叠、规则数/规范数与 SKILL/06 一致。网络失败仅使更新任务失败或产构建日志，运行时继续使用已提交锁文件；绝不生成稿件 finding。首批锁定 [WMA 2024](https://www.wma.net/hb-e-version-2024-2/)、[中国2023伦理办法](https://www.natcm.gov.cn/kejisi/zhengcewenjian/2023-02-28/29341.html)、[2024人遗条例](https://xzfg.moj.gov.cn/front/law/detail?LawID=1714)、[ARRIVE 2.0](https://arriveguidelines.org/arrive-guidelines) 与 [ISSCR 2025](https://www.isscr.org/guidelines)。
- **代价**：1.5–2 人日；HTML/PDF 取正文和稳定 hash 需按来源写适配器，CI 测试用录制响应，提交包不缓存整份 PDF。
- **建议优先级**：P1 应该做；交付前最小版先 lint 结构与计数，联网 hash 更新可在发布流程执行。
- **阶段 / 归属**：规则库构建基础设施，不属于 M1–M7 审核模块；M6 只读已锁版本。
- **契约字段**：不改报告三类记录；只扩展资源元数据。若运行时发现锁文件损坏，产 `system_limitation(rulebase_integrity_failed)` 并停止 M6，不得带病输出伦理结论。
- **假阳性**：不判断稿件。网页模板变化可能改变整页 hash；适配器应只规范化正文节点，hash 变化触发人工复核，不自动宣告规范已修订。

## 未解决 / 需要人来定的问题

1. 是否接受 `ETH-CELL-003` 成为第4条 `manual_only`。建议接受；ISSCR 明确允许常规人多能干细胞体外培养在评估后归 Category 1A，旧自动 `critical` 不可保留。
2. 是否在交付前做 P1 最小垂直切片。建议接受；否则必须在 README 明示当前筛查器只判断“字段是否出现”，不能宣称已核对委员会名、批件号等子要素。
3. 是否把 2026 年《生物医学新技术临床研究和临床转化应用管理条例》立即纳入现行规则。建议先实现离线路由与药械排除，再开放备案查询；这是截至 2026-08-07 中国法规覆盖的最大缺口。
4. 2026 年《人类遗传资源管理条例实施细则》仍是征求意见稿。现阶段必须继续锁定 2023 现行版并记录 2024 主管部门变更，不得依据草案立 finding。
5. `ETH-ANI-001` 的 GB/T 35892-2018 细目、`ETH-CELL-003` 的 2003 中国原则部分定位仍为 `medium`，`ETH-BIO-002` 的中国法依据为 `low`；三者正式输出前必须人工核原文，不能为了“全 high”虚抬置信度。
6. Round 1 P5 已提出 Cellosaurus 身份 connector，Round 4 P1 已提出统一 X1；P4 只补 M6 豁免消费语义，不应再建第二套外部层。
7. 本轮未修改 `datasets/**`，真实语料误报率测试仍未完成。交付前至少在 `animal_invivo`、`rct_clinical` 和一篇纯细胞系论文上记录规则级 TP/FP/FN，不能只展示合成自检。
