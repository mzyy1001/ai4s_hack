# Round 4 · 外部数据源与新功能组件 提案

## 摘要

现有文档把公开数据库统一推到二期，但真实阻塞已不是网络或时限，而是 `evidence.schema.json` 只有 `present/absence`、产出者没有外部验证阶段、外部失败还会错误污染抽取覆盖率；必须先补一条 fail-closed 的外部证据流水线。
Round 1–3 已提出登录号存在性、实体身份、撤稿、图像、化合物、抗体、蛋白坐标与 SRA 元数据，本轮不重复这些清单，改为三个更窄而可验收的垂直组件：临床注册安全性/分母对账、临床变异主张核验、蛋白质组肽段唯一性核验。
其中联网部分均应纳入黑客松一期的**可选增强层**；离线核心继续完整运行，外部源不可用只记录 `system_limitation`，绝不生成稿件 finding。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `README.md` | 使用、提交合规自查、分期范围、当前状态 | 把 900 秒改为 12 小时；把 444 行/4 份 schema 改为实测正文 496 行（含 frontmatter 共 501 行）/10 份；删除“仅拷贝 skill 目录即可获得工具能力”和“external 字段已预留”的错误声称；把一期改为离线保底 + 可选联网增强；区分约 396 KiB 的 skill 本体与约 200 MiB 的完整工作区 | 四个工具仍在根 `tools/`，`evidence.schema.json` 也没有 `external` 分支；旧文本会在 L0/L1 静态检查和实际运行时被直接证伪，且误将整仓打包会纳入一份 18,677,256-byte PDF |

## B 类提案

### P1 · 外部证据解析层 X1 与 Skill 内脚本封装

- **问题**：Round 1 P4–P6 已分别提出连接器，但没有统一的可执行入口。当前 `evidence.schema.json` 只接受 `present/absence`，`created_by`、`extraction_signal.produced_by` 与 `system_limitation.produced_by` 都不允许外部阶段；`all_system_limitations` 只聚合四个 stage-local 数组。更直接的交付硬伤是已实现的四个确定性工具仍在仓库根 `tools/`，仅拷贝 `skills/biomed-paper-review/` 后运行时不可见。
- **影响**：各连接器若自行写 finding，会破坏“M1 不产 finding”和三类记录边界；若把 429、超时或数据库维护解释成 `not_found`，会直接冤枉稿件。脚本不在 skill 本体则自动评审只能看到文档，看不到 uplift 最大的确定性能力，主要损失 30% 工程质量与 14% Skill 复用分。
- **方案**：**一期基础设施，P0 前置**。新增 `skills/biomed-paper-review/scripts/external_evidence_resolver.py` 与 `resources/external_sources.json`，所有连接器实现同一接口：
  1. 输入 `lookup_request:{request_id,connector,query_kind,normalized_input,manuscript_evidence_refs[],requested_assertions[]}`；输出只允许 `external_evidence[]`、`external_validation_signals[]`、`external_system_limitations[]`，禁止输出 finding。
  2. 新增 `stage_3c_external_validation`，位置固定在 Stage 3b 后、Stage 4 前。X1 只解析标识符与外部事实；M2–M7 结合稿件内证据判定。
  3. `evidence_registry` 增加第三型 `external`，最小字段为 `{id,type,database,endpoint,query,record_id,retrieved_at,database_version,http_status,retrieval_status,response_sha256,parser_version,assertions[],created_by}`；`record_id` 在 `not_found/not_addressed` 时为 `null`。`assertions[]` 保存 `{predicate,subject,external_value,unit,relation_to_manuscript,comparability}`；不把整份响应塞进报告。`query` 只保存规范化参数，禁止保存 API key、cookie 或 Authorization header。
  4. `retrieval_status` 固定为 `resolved/not_found/not_addressed`。格式合法的精确 accession 在权威库得到明确 404 或成功响应中的零记录，才可记 `not_found`；语义检索零命中只能是 `not_addressed`。429、5xx、DNS、超时、白名单拦截、响应结构漂移分别产 `external_rate_limited`、`external_source_unavailable` 或 `external_response_unparseable` 类 `system_limitation`，不得产 mismatch signal。
  5. 新增单一 signal type `external_validation_candidate`，其条件必填 `external_check:{check_type,manuscript_value,external_value,comparison_result,comparability,rule_version}`；`comparison_result` 为 `match/mismatch/not_comparable/needs_manual_review`。只有 `mismatch` 才路由审核模块，后三类之外不得自造结论枚举。
  6. 顶层新增非记录对象 `external_validation_coverage:{requested,completed,failed,not_applicable,by_connector[]}`。外部失败不计入 `extraction_coverage` 分母，也不改变 manuscript risk；只降低依赖该 connector 的 finding confidence，并在报告“系统限制”节展示。
  7. 将 `normalize_biomed_units.py`、`statistical_forensics.py`、`ethics_compliance_check.py` 与 `validate_schemas.py` 的运行时代码迁入 `skills/biomed-paper-review/scripts/`；根 `tools/` 保留薄包装以维持四条既有自检命令。所有路径以脚本位置或 CLI 参数解析，不写仓库绝对路径。外部响应缓存由 `--cache-dir` 指定，默认使用运行时临时目录；缓存不进入提交包。
  8. 修改 `SKILL.md §0.2/§2`、`00-contracts.md §1/§6/§7/§9`、`01-structured-extraction.md §14`、`evidence.schema.json`、`extraction_signal.schema.json`、`system_limitation.schema.json`、`execution_scope.schema.json`、`review_report.schema.json`、模板、fixtures 与 validator。删除 `07 §11.4` 中非法的 `created_by:"M7"` 示例，外部证据只能由 `stage_3c_external_validation` 创建。
- **代价**：2–3 人日；1 人日做 schema migration 与 fixtures，1 人日做连接器基类、缓存/重试和根工具包装，0.5–1 人日做离线录制响应回归。P2–P4 均依赖本项。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；新增共享阶段 X1，不新增审核模块。离线模式跳过 X1 仍能完成现有 Stage 1–5。
- **契约字段**：扩展 `evidence`、`extraction_signal`、`system_limitation`、`execution_scope` 与顶层 report；不新增第四类记录，不改变 finding severity 机制。
- **假阳性**：低。X1 永不直接立 finding；成功查询但数据库未覆盖该主张时记 `not_addressed`，失败记 `system_limitation`。finding 必须同时引用至少一条稿件内 `present` 与一条 `external` evidence。

### P2 · ClinicalTrials.gov 安全性、受试者流与终点三向对账

- **问题**：Round 1 P4 只提出“注册号是否存在、终点与注册是否一致、是否晚注册”。真实临床审稿还常见三类可量化偏差：论文安全性分母使用 `treated`，注册结果却按 `atRisk`；严重不良事件人数/事件数混用；CONSORT 流程图的随机、接受干预、完成随访、进入分析人数与注册结果不一致。单查注册号不会发现这些问题。
- **影响**：安全性分母偏小会系统性低估 adverse-event rate，受试者流不一致会影响 attrition bias，主要终点的 measure/time frame/type 不一致会影响选择性报告判断。这些字段是注册 JSON 中的结构化事实，裸模型既难稳定取全，也无法保存可复算的逐臂对账链。
- **方案**：**一期联网增强**新增 `clinicaltrials_gov` connector：
  1. 用 `GET https://clinicaltrials.gov/api/v2/studies/{nctId}` 精确取记录，用 `GET https://clinicaltrials.gov/api/v2/version` 保存 `dataTimestamp`。API v2 单研究端点与版本字段见 [ClinicalTrials.gov API migration guide](https://clinicaltrials.gov/data-api/about-api/api-migration)。
  2. 固定读取 `protocolSection.identificationModule.nctId`、`statusModule.studyFirstSubmitDate/firstPostDateStruct/startDateStruct/primaryCompletionDateStruct`、`designModule.enrollmentInfo`、`armsInterventionsModule.armGroups`、`outcomesModule.primaryOutcomes`，以及 `resultsSection.participantFlowModule`、`outcomeMeasuresModule`、`adverseEventsModule`。字段路径与枚举以官方 [Study Data Structure](https://clinicaltrials.gov/data-api/about-api/study-data-structure) 为唯一规范源。
  3. M1 需先从稿件表格/CONSORT 图抽取 `trial_report:{nct_id,arms[],flow_counts[],primary_outcomes[],adverse_events[]}`；每个数保留 arm、时间窗、分析集、单位（participants/events）与稿件内 evidence ref。X1 只对完全相同 arm + time frame + population + unit 的值做确定性比较。
  4. 外部 evidence 的 `assertions[].predicate` 限定为 `registration_timing`、`primary_outcome_definition`、`participant_flow_count`、`serious_adverse_event_count`、`adverse_event_denominator`。signal 的 `check_type` 对应 `late_registration_candidate`、`registered_outcome_mismatch_candidate`、`participant_flow_mismatch_candidate`、`safety_denominator_mismatch_candidate`。
  5. `studyFirstSubmitDate > startDate` 只路由 M6 人工核对，不自动称为违规；outcome 的标题相似但 time frame、计量方式或 role 不同，路由 M2/M4/M7；人数与分母在同一语义键上精确不等，路由 M2/M4。M6 在 `06-ethics-compliance.md §8` 登记注册时序 category；M4 登记计数/分母 category；M2 文件由负责人登记受试者流与预设终点 category。
  6. 官方 v2 API目前没有已文档化的历史版本 API。不得抓 UI 的 `?tab=history&a=` 页面冒充稳定接口，也不得声称自动识别“注册后改终点”。历史版本差分留到二期，除非团队获得稳定端点或固定月度快照；本期报告明确写“只比较当前公开记录”。ClinicalTrials.gov 的 Record History 可供人工查看，但不等于程序化历史契约，见 [Record History 说明](https://clinicaltrials.gov/study-basics/how-to-read-study-record)。
- **代价**：3–4 人日；1 人日 connector 与录制响应，1–1.5 人日稿件表/流程图结构化，1 人日 arm/time-frame 对齐与正反例，0.5 人日模块规则接线。需要 6–10 篇有 posted results 的 RCT 做回归。
- **建议优先级**：P0 交付前必须做一个最小垂直切片：NCT 精确解析 + 注册时序 + 主终点 + 严重不良事件分母；完整 participant-flow 对账为 P1。
- **阶段 / 归属**：一期联网增强；X1 产 evidence/signal，M6 判注册时序，M2/M4 判受试者流与数字，M7 判论文结论是否越过预设终点。历史版本差分为二期。
- **契约字段**：复用 P1；M1 新增 `trial_report` 非记录对象，`external_check` 增 `arm_id/time_frame/analysis_population/count_semantics`。无需改变 finding 基础形状。
- **假阳性**：中高。安全集、ITT、PP、随机人数、治疗人数、participants affected 与 event count 不可互比；arm 合并、交叉设计、多周期试验也不得自动对齐。任一语义键缺失即 `not_comparable`，只交人工。注册当前值与论文不一致不能证明选择性修改。

### P3 · ClinVar + Ensembl VEP 的变异身份、频率与临床主张核验

- **问题**：稿件常把不同 transcript 的同名变异混在一起，或声称“罕见致病变异”却未给 assembly/transcript/condition。Round 3 P4/P5 只覆盖序列与蛋白坐标，没有处理 ClinVar 的 variant-condition 语义、review status、相互冲突提交和人群等位基因频率。
- **影响**：reference allele 错、HGVS 对不上指定 transcript、蛋白后果不一致属于可确定性错误；而把 VUS 写成“已知致病”、忽略 ClinVar 冲突或把常见多态称为“极罕见”会直接改变临床解释。裸模型容易只记住一个过期标签，无法区分 VCV（variant）与 RCV（variant-condition）层级。
- **方案**：**一期联网增强**新增 `clinical_variant` connector：
  1. M1 抽取 `variant_claims[]:{claim_id,input_notation,rsid,assembly,transcript,ref,alt,gene,condition,inheritance,claimed_consequence,claimed_significance,claimed_frequency,frequency_population,evidence_refs[]}`。assembly、transcript 或 condition 未给时必须显式为 `null`，不得猜默认版本。
  2. 对 HGVS 调 `GET https://rest.ensembl.org/vep/human/hgvs/{hgvs_notation}?hgvs=1&mane=1`；对 rsID 调 `/vep/human/id/{id}?hgvs=1&mane=1`。保存 `assembly_name`、normalized HGVS、`most_severe_consequence`、逐 transcript consequence、MANE 标记、allele string、rsID 与 `colocated_variants.frequencies`。VEP 的 HGVS 输入、MANE 与频率输出见 [Ensembl VEP HGVS API](https://rest.ensembl.org/documentation/info/vep_hgvs_get)。
  3. 只有 VEP 解析到完全相同 assembly/ref/alt 后才查 ClinVar。用 `esearch.fcgi?db=clinvar&term={rsid}` 找候选，再用 `efetch.fcgi?db=clinvar&rettype=vcv&is_variationid&id={variation_id}` 取 VCV；若稿件主张特定疾病，再解析相应 RCV/SCV。保存 VCV/RCV accession + version、clinical significance、review status、condition、last evaluated、submitter count 与 conflicting classifications。官方说明支持 `esearch/esummary/elink/efetch` 及 versioned VCV/RCV，见 [ClinVar programmatic access](https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/)。
  4. 确定性 signal 仅三类：`variant_reference_mismatch_candidate`（明确 transcript/assembly 下 ref 或 alt 不符）、`variant_consequence_mismatch_candidate`（明确 transcript 下稿件蛋白后果与 VEP 不同）、`claimed_frequency_mismatch_candidate`（稿件给出可数值化阈值，且同 allele、同 assembly、匹配总体/人群频率明确超过阈值与舍入容差）。
  5. 临床意义只产 `clinical_significance_review_candidate`：外部 assertion 同时保存 `review_status` 与 condition match。ClinVar 无记录、单提交者、VUS、conflicting、condition 不同、过期评价均不能自动判稿件错误；M7 只可在稿件把数据库状态表述成既成事实且外部记录明确相反时立 finding。ClinVar 本身明确说明 NIH 不独立核实提交信息，也不用于未经专业复核的医疗决策，见同一官方说明。
  6. 在 `07-conclusions-discussion.md` 登记 `variant_claim_external_mismatch`，并规定 severity：坐标/参考等位基因硬错且支撑主结论时最高 major；ClinVar 标签差异最高 info/人工复核，不得自动 critical。M3 负责人另行登记样本/构建中的变异身份错误。
- **代价**：3–5 人日；需要 HGVS URL 编码、XML 解析、VCV↔RCV 映射和 20 个 fixture（多 transcript、左右归一化 indel、相反链、冲突分类、不同 condition）。不接入商业 OncoKB/HGMD，避免许可与覆盖问题。
- **建议优先级**：P1 应该做；先交付 rsID/HGVS 身份 + reference/consequence，临床意义聚合随后。
- **阶段 / 归属**：一期联网增强；X1 + M7，变异材料身份部分路由 M3。肿瘤用药可操作性与 ACMG 自动重分类属于二期，且本项目不应自动做患者级诊断。
- **契约字段**：复用 P1；扩展 `structured_result` 的 `variant_claims[]` 与 `external_check.variant_context`，不重构三类记录。
- **假阳性**：高。transcript、assembly、基因组正负链、HGVS 左右归一化、体细胞/胚系、condition 和 ancestry 任一不匹配都停止自动比较。数据库没有收录表示 `not_addressed`，不是反证。

### P4 · UniProt 参考蛋白组上的肽段唯一性与 PTM 位点核验

- **问题**：蛋白质组论文常用共享肽段支撑某个 paralog/isoform 的特异表达，或把 PTM 位点编号映射到错误 isoform。Round 3 P5 核对的是稿件声称的蛋白变体与结构域坐标，没有回答“补充表里的鉴定肽段是否真的唯一支持该蛋白”。这是质谱审稿中非常实质、又适合确定性计算的问题。
- **影响**：如果所有 supporting peptides 都同时匹配多个同源蛋白，protein-level claim 不具特异性；若 phosphosite 对应位置不是 S/T/Y 或 peptide 根本不覆盖该残基，位点机制链可能失效。通用模型无法在完整物种蛋白组上做穷尽映射，也无法稳定处理 I/L 等质量等价残基。
- **方案**：**一期同时提供离线与联网路径**，新增 `proteomic_peptide_forensics.py`：
  1. M1 从补充表抽取 `peptide_evidence[]:{peptide_id,sequence,modified_sequence,charge,protein_accessions[],organism_taxid,claimed_isoform,ptm_sites[],search_engine,protein_fdr,peptide_fdr,evidence_refs[]}`。没有肽段序列时不运行，不从图中猜序列。
  2. 联网时按精确 `organism_id`/reference proteome 从 `https://rest.uniprot.org/uniprotkb/stream` 下载 gzip FASTA，查询形如 `(proteome:UP000005640)`，`format=fasta&compressed=true&includeIsoform=true`；单 accession 用 `GET /uniprotkb/{accession}.fasta`。UniProt 官方 REST 支持 `search/stream`、FASTA、压缩与 `includeIsoform`，见 [query API](https://www.uniprot.org/help/api_queries) 与 [individual entry API](https://www.uniprot.org/help/api_retrieve_entries)。离线时接受用户提供的带版本 FASTA；两条路径共用同一映射器。
  3. 保存 UniProt release/下载时间、query、response hash、FASTA header 中 accession/isoform/organism/sequence version。不得把下载的整套 proteome 放入提交包；缓存由 P1 管理。
  4. 用 Biopython/本地索引做穷尽 exact mapping，同时跑一条 I↔L 等价映射。输出 `{exact_accessions[],mass_equivalent_accessions[],unique_at_gene_level,unique_at_protein_level,unique_at_isoform_level,matched_positions[],reference_hash}`。只有 exact + I/L 等价结果都唯一时才允许称 protein-unique；isoform-specific 必须匹配该 isoform 独有区段。
  5. PTM 核验只做坐标事实：peptide 覆盖目标位点、参考残基相同、修饰类型允许该残基。phosphorylation 只接受 S/T/Y；N 端乙酰化、蛋白切割后编号与可变修饰必须走各自规则。localization probability 缺失或低于稿件预设阈值时只产 `ptm_localization_unresolved`，不判位点错误。
  6. signal type 仍用 P1 的 `external_validation_candidate`，`check_type` 为 `peptide_not_mapped_candidate`、`protein_assignment_nonunique_candidate`、`isoform_assignment_nonunique_candidate`、`ptm_coordinate_mismatch_candidate`。M3 只有在稿件明确作 protein/isoform-specific claim 且其全部直接支持肽段均不唯一时才可立 `protein_identification_not_unique`；M7 只有在该鉴定是结论唯一支撑时升级 claim 风险。
- **代价**：3–4 人日；1 人日 FASTA 下载/缓存与索引，1 人日肽段/PTM 解析，1–2 人日用人类 paralog、剪接异构体、I/L 等价、tryptic missed-cleavage 与 decoy 表做 fixtures。人类 reference proteome 可在 4 GB CPU 沙箱内处理。
- **建议优先级**：P1 应该做；这是最可能产生明显 uplift 的新组件之一。先交付 peptide→protein uniqueness，PTM 规则为第二批。
- **阶段 / 归属**：一期；M1 只抽取肽段，X1/本地工具产 signal，M3 判鉴定方法 finding，M7 评估主张依赖。蛋白推断的 razor peptide、谱图重打分和原始 mzML 复算为二期。
- **契约字段**：复用 P1；`structured_result` 增 `peptide_evidence[]`，signal 的 `external_check` 增 `reference_set/mapping_mode/matched_accessions[]/matched_positions[]`。不新增记录类型。
- **假阳性**：中。I/L 不可区分、等位变体、未收录 isoform、信号肽/起始 Met 切除、污染物库与搜索数据库版本差异都会制造表面不匹配；reference hash 或稿件搜索数据库不明时，只报 `needs_manual_review`。共享肽段不等于蛋白不存在，只说明不能支撑特异归属。

## 未解决 / 需要人来定的问题

1. 是否接受 `stage_3c_external_validation` 作为唯一外部产出者。若让 M6/M7 直接创建 external evidence，会再次破坏阶段血缘；建议不接受。
2. `external_validation_coverage` 是否独立于 `extraction_coverage`。建议独立，否则网络失败会错误降低论文内容抽取分，三项分数分离失真。
3. P1 schema migration 是否在周日前完成。没有 `external` 分支时可以做 connector 原型，但演示报告不得声称外部核验已经进入可审计证据链。
4. ClinicalTrials.gov 历史版本没有已文档化的 API；是否接受本期只比较当前公开记录。建议接受，并把“无法判断何时改终点”明确列为限制，禁止抓 UI 私有接口。
5. Round 1 P2/P3 已被采纳并实现为根 `tools/` 脚本，但尚未迁入 skill；Round 1 P4–P7、Round 2 P4/P5、Round 3 P4–P6 均未见 schema/脚本落地。本轮 P2 是对 Round 1 P4 未覆盖的 safety/flow 垂直切片，P3/P4 是新增能力，不应再并行新建第二套外部网关。
6. 提交打包范围必须锁定为 `skills/biomed-paper-review/` 及官方要求的必要顶层文件，禁止整仓打包。`datasets/papers/toxicology__journal.pone.0339571/paper.pdf` 单文件为 18,677,256 bytes；本轮受 `datasets/**` 禁改约束未处理，若官方要求连 datasets 提交，必须由数据集负责人压缩或从提交清单排除。
