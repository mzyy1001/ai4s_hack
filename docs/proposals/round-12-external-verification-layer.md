# Round 12 · 外部验证层 X1 提案

## 摘要

Round 4 P1 提出的统一 X1 前置本轮已部分采纳：`stage_3c_external_validation`、第三种
`external` evidence、无 severity 的 `external_validation_candidate`、失败降级与缓存/重试契约
已落地，不再允许 connector 自行写 finding。
当前仍没有运行时 connector，因而不能声称已完成任何外部数据库核验；最小一期联网切片应先交
ClinicalTrials.gov、Europe PMC、GEO/SRA/PRIDE 与 HGNC/Ensembl/UniProt/InterPro，而不是继续扩文档。
外部零命中、白名单拦截与接口故障必须与稿件风险隔离；X1 的主要价值是可追溯的第二来源对账，
不是用“数据库没写”反驳新发现。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/00-contracts.md` | §1.2–§1.7、§6、§7.1、§9.2、§11 | 证据由两型扩为 `present/absence/external`；固定 X1 输入输出、external 元数据、finding 的稿件 `present` 首锚点、失败分类、缓存/重试、阶段本地数组与 lint | 不落这些规则，connector 会把 404/429 当反证，或让外部事实脱离稿件锚点直接变 finding |
| `skills/biomed-paper-review/SKILL.md` | §0.1–§0.2、§1、§2.1–§2.9、§3 | 把可选 X1 放在 Stage 3b 后、Stage 4 前；声明只路由 M2/M4/M6/M7、禁止 X1 产 finding，并如实注明 connector 尚未交付 | 旧文仍称 external schema 未落地，且流水线没有外部产物的合法消费位置 |
| `skills/biomed-paper-review/schemas/evidence.schema.json` | `evidence_entry`、`external_evidence`、`external_assertion`、`created_by` | 新增可审计 `external` 分支；成功记录强制 record/assertions，零命中强制空 assertions，接口失败不能伪装成 evidence | 保证端点、查询、版本、时间、HTTP 状态、响应 hash 与解析器版本可复核 |
| `skills/biomed-paper-review/schemas/extraction_signal.schema.json` | `type`、`external_check`、条件约束 | 新增单一 `external_validation_candidate`；强制 X1 产出、双证据引用与 M2/M4/M6/M7 路由 | signal 只保存可复算比较，不带 severity，也不让每个 connector 发明自己的顶层记录 |
| `skills/biomed-paper-review/schemas/common.schema.json`、`execution_scope.schema.json` | `stage_id`、阶段依赖 | 新增 `stage_3c_external_validation`，强制依赖 Stage 3b，同时不要求离线运行必须执行 X1 | 只改 evidence/signal 会让 execution scope 拒绝实际 X1 运行 |
| `skills/biomed-paper-review/schemas/system_limitation.schema.json` | category、producer 条件 | 新增 `external_source_unavailable/external_access_denied/external_rate_limited/external_response_unparseable`，且只能由 X1 产出 | 白名单、权限、429、5xx 与响应漂移需要机器可区分的安全降级路径 |
| `skills/biomed-paper-review/references/01-structured-extraction.md`、`06-ethics-compliance.md`、`07-conclusions-discussion.md` | 外部核验边界与消费规则 | 同步为“X1 核心契约已落地、connector 尚未交付”；统一使用 `external_validation_candidate`，并固定 M2/M6/M7 的稿件首锚点与完整可比 mismatch 门槛 | 消费模块若仍按旧的“两型证据/外部核验未定”口径执行，会拒绝合法 X1 产物或绕开现有契约 |
| `skills/biomed-paper-review/schemas/review_report.schema.json` | `all_extraction_signals`、`all_system_limitations` 描述 | 将可选 X1 纳入 signal 与 limitation 汇总来源 | 报告 schema 不应把合法 X1 产物描述成越权记录 |
| `skills/biomed-paper-review/templates/review_report.md` | `render_evidence_refs` | 规定 external evidence 展开 database、record/version/time、状态、hash 前缀与 assertion 路径，不倾倒响应 | 只打印 `EV-*` 或整份 API JSON 都不可审计、不可用 |
| `tools/validate_schemas.py`、`tools/fixtures/sim1_rct_full_review.json` | 枚举、阶段依赖、三型证据与 external fixture | 校验 external 产出者、hash、双证据、finding 首锚点、signal 路由、X1 limitation；增加 Europe PMC match signal 正例 | 防止“schema 写了但实例路径从未跑过” |
| `README.md`、`docs/schema-migration.md` | 当前状态与 evidence 迁移 | 改为“X1 核心契约已落地、connector 尚未落地”，并修正 SKILL 正文少于 500 行的失实自查 | 提交说明不能把未实现 connector 写成已完成，也不能保留已被本轮推翻的两型口径 |

## B 类提案

### P1 · 唯一运行入口 `external_evidence_resolver.py` 与 connector manifest

- **问题**：Round 4 P1 已定义统一入口，但仓库仍没有脚本。若四组 connector 分别处理请求、缓存、错误和 evidence id，将再次出现不同的 404 语义、重试策略和产出者血缘；本轮 A 类 schema 只能证明“允许输出”，不能产生 uplift。
- **影响**：自动评审无法执行任何联网核验，X1 仍是文档功能；更危险的是实现者可能让 M6/M7 直接访问 API 并创建 external evidence，破坏唯一产出者和失败降级。
- **方案**：**一期联网增强，X1 基础设施，P0。** 新增 `skills/biomed-paper-review/scripts/external_evidence_resolver.py`、`references/08-external-verification.md` 与 `resources/external_sources.json`。主入口接收：
  ```json
  {
    "request_id": "XREQ-001",
    "connector": "clinicaltrials_gov",
    "query_kind": "trial_registration",
    "normalized_input": "NCT01234567",
    "manuscript_evidence_refs": ["EV-031"],
    "requested_assertions": ["study_first_submit_date", "primary_outcome_definition"]
  }
  ```
  返回只允许 `{external_evidence[], external_validation_signals[], external_system_limitations[]}`。
  connector manifest 固定 `{connector,base_urls[],allowed_methods[],query_kinds[],parser_version,rate_limit,
  timeout_seconds,success_ttl_seconds,negative_ttl_seconds,consumer_modules[],response_fixture_version}`；
  启动时拒绝 manifest 外主机、HTTP、重定向到未登记主机、私网地址和含凭证的 query。
  缓存与重试直接实现 `00-contracts.md §1.6`，`--offline` 只读缓存，cache miss 产
  `external_source_unavailable` 而非 `not_found`。API key 只从 connector 专属环境变量读取，
  永不进入 query、日志、evidence 或 cache key 的可展示部分。
- **代价**：1.5–2 人日；0.5 人日 resolver/manifest，0.5 人日缓存与错误分类，0.5–1 人日录制响应和恶意重定向/凭证泄漏负例。无 GPU；标准库 `urllib` 足够，Biopython仅用于后续序列处理。
- **建议优先级**：P0 交付前必须做；P2–P4 的共同前置。
- **阶段 / 归属**：一期联网增强；新增共享层 X1，不新增审核模块，离线 Stage 1–5 不依赖它。
- **契约字段**：复用本轮已落地的 `external`、`external_check` 与 X1 limitations；manifest 是运行资源，不是第四类记录。
- **假阳性**：低。resolver 不判断稿件；精确 404 与语义零命中分开，失败只产 limitation。风险主要是重定向或陈旧缓存，故 host allowlist、响应 hash、TTL 与条件请求必须同时启用。

### P2 · 临床注册与注册结果 connector：ClinicalTrials.gov

- **问题**：Round 4 P2 与 Round 9 P6 已分别提出注册时序、主要终点、安全性分母、受试者流和结果统计对账，但未收敛成一个字段映射。临床论文最实质的不是“有无 NCT”，而是 arm、time frame、analysis population、units analyzed 与 endpoint role 是否同义。
- **影响**：只比标题会把措辞差异误报为终点漂移；只比数字会把 ITT/PP、participants/events、当前注册更新与论文发表时版本混为一谈。反之，严格语义键上的计数、估计量、CI 与 p 不一致是裸模型难稳定完成的高价值 uplift。
- **方案**：**一期联网增强，X1 → M2/M4/M6/M7，P0。** connector=`clinicaltrials_gov`：

  | query_kind | 数据源与端点 | 请求 | external assertions | signal / 路由 |
  | --- | --- | --- | --- | --- |
  | `trial_registration` | ClinicalTrials.gov API v2：`GET https://clinicaltrials.gov/api/v2/studies/{nctId}`；版本元数据 `GET /api/v2/version` | 只接受 `^NCT[0-9]{8}$` | `nct_id`、`study_type`、`study_first_submit_date`、`study_first_post_date`、`start_date`+date type、`enrollment`、arm ids、primary outcome `measure/description/timeFrame` | `registration_timing_candidate`→M6；`registered_outcome_mismatch_candidate`→M2/M7 |
  | `participant_flow_safety` | 同一 study 记录 | 由 v2 的 NCT + arm/time/population/unit 键查询 | `participant_flow_count`、`serious_adverse_event_count`、`adverse_event_denominator`，每条保存 group id、period、milestone/category、participants/events | 完全同键数值不等才 `mismatch`→M2/M4；缺任一键为 `not_comparable` |
  | `result_statistics` | 同一记录的 `resultsSection.outcomeMeasuresModule` | outcome title + type + time frame + group set + population + units + param type 全匹配 | estimate、CI sides/level/limits、p、dispersion、statistical method、non-inferiority fields | `registered_result_statistic_mismatch_candidate`→M4；结论依赖时同时路由 M7 |

  官方字段以 [Study Data Structure](https://clinicaltrials.gov/data-api/about-api/study-data-structure)
  与 [API v2 OpenAPI](https://clinicaltrials.gov/api/oas/v2/ctg-oas-v2.yaml) 为唯一来源。
  当前公开记录不等于论文投稿时历史版本；本期不抓 Record History UI 私有接口，不输出
  “注册后修改终点”。`studyFirstSubmitDate > startDate` 只表示晚注册候选，不自动等于伦理违规。
- **代价**：3–4 人日；1 人日 parser，1 人日语义键对齐，1 人日 10 个 NCT 录制响应，0.5–1 人日 M2/M4/M6/M7 消费规则与 current-record 反例。
- **建议优先级**：P0 先交 `NCT + submit/start + primary outcome + estimate/CI/p`；flow 与 adverse-event 分母为 P1。
- **阶段 / 归属**：一期联网增强；X1 取证，M6 判断注册时序，M2 判断终点/受试者流，M4 判断数值，M7 判断结论是否依赖漂移终点。
- **契约字段**：扩展 `external_check` 的 connector 专属 payload 应放 `target` 或 assertion 值中；若要机器封闭语义键，新增 `comparison_context:{arm_ids[],time_frame,analysis_population,units_analyzed,count_semantics,param_type}`，不改三类记录。
- **假阳性**：高。任一语义键不等都只能 `not_comparable`；当前记录与论文不同不能证明选择性修改。404、429、5xx、白名单阻断只走本轮 X1 limitation。

### P3 · 文献状态与数据可及性 connector：Europe PMC + NCBI + PRIDE

- **问题**：稿件引用已撤稿文献支撑核心主张、或声称 GEO/SRA/PRIDE 数据已上传但 accession 不可解析，都是编辑能快速核对的客观风险。Round 1 P4/P6 已提方向，Round 4 未给统一的零命中与字段映射。
- **影响**：裸模型依赖记忆，既会漏掉新撤稿，也会把“讨论一篇撤稿案例”误判成正向引用；数据 accession 的一位抄错会直接破坏可复现性，但 API 暂时无响应不能归责作者。
- **方案**：**一期联网增强，X1 → M2/M7，P0/P1。** 实现三个 connector：

  | connector | 端点与查询 | 返回字段 → external assertions | signal 与消费 |
  | --- | --- | --- | --- |
  | `europe_pmc` | DOI/PMID/PMCID 先 `GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&resultType=core&format=json`；批量状态用 `POST .../rest/status-update-search`，body=`{"ids":[{"src":"DOI","extId":"..."}]}` | `source/id/pmid/pmcid/doi/title/pubYear`；status relation 的 original id、updated id、update type | `publication_status_update_candidate`→M2/M7；只有稿件 `present` citation context=`supports_claim` 且状态明确为 retracted/withdrawn 才允许 M7 建 finding 候选；correction 默认人工 |
  | `ncbi_accession` | E-utilities `esearch.fcgi` + `esummary.fcgi`；GEO 用 `db=gds&term={GSE}[ACCN]`，SRA 用 `db=sra&term={SRP/SRX/SRR}[ACCN]`，`retmode=json` | canonical accession/uid、title、organism/taxid、study/bioproject、公开状态、更新时间 | `data_accession_identity_candidate`→M2/M7；格式合法精确零记录仅 `needs_manual_review`，不自动 finding |
  | `pride_archive` | `GET https://www.ebi.ac.uk/pride/ws/archive/v2/projects/{accession}`；需要文件存在性时再取 project files | accession、title、projectDescription、organisms、publication references、submission/publication date、file count/category | `data_accession_metadata_mismatch_candidate`→M2/M7；只在 accession 精确命中后比较物种/论文 DOI，文件列表为空不等于数据无效 |

  Europe PMC 使用官方 [REST/状态更新接口](https://europepmc.org/RestfulWebService)，NCBI 依
  [E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/) 在无 key 时限速 ≤3 req/s；PRIDE
  依 [Archive API Guide](https://www.ebi.ac.uk/pride/ws/archive/v2/docs/api-guide.html)。正文引用语境
  先由 M1 抽为 `supports_claim/background/discusses_retraction`；X1 不做语义定罪。
- **代价**：3–4 人日；Europe PMC 1 人日，GEO/SRA 1–1.5 人日，PRIDE 0.5–1 人日，录制响应与 citation-context 负例 1 人日。
- **建议优先级**：P0 Europe PMC + GEO/SRA 精确 accession；P1 PRIDE 文件元数据。
- **阶段 / 归属**：一期联网增强；X1 产 evidence/signal，M2 判断引用/数据声明一致性，M7 只在核心主张依赖时判断影响。
- **契约字段**：复用本轮契约；M1 后续需扩 `citation_contexts[]` 与 `data_availability.accessions[]`。这是 structured result 扩展，不新增记录。
- **假阳性**：中高。引用撤稿论文可能是批判性讨论，correction 可能不影响结论；repository embargo、private reviewer token、尚未公开或 accession 版本迁移都可造成暂时无记录。精确零命中只排人工，不自动判“数据未上传”。

### P4 · 基因—蛋白实体与坐标 connector：HGNC/Ensembl + UniProt/InterPro

- **问题**：Round 1 P5、Round 3 P5 与 Round 11 P5 已提出实体/结构核验，但尚未落地。最可靠的不是“数据库是否支持新功能”，而是批准符号、物种、稳定 accession、isoform 长度、参考残基和结构域区间这些确定性事实。
- **影响**：废弃人类基因符号、把人/鼠同名实体混用、突变位点越界、声称位点落在 kinase domain 但区间不重叠，均会使机制链失效；通用模型无法稳定处理版本、isoform 和成熟链编号。把无注释当反证又会误伤真正的新发现。
- **方案**：**一期联网增强，X1 → M2/M7，P1。** 两个组合 connector：

  | connector | 端点与查询顺序 | external assertions | 只允许的比较 |
  | --- | --- | --- | --- |
  | `gene_identity` | 人类：`GET https://rest.genenames.org/fetch/symbol/{symbol}`；无 approved 命中再 `search/prev_symbol/{symbol}`、`search/alias_symbol/{symbol}`。非人类或物种复核：`GET https://rest.ensembl.org/lookup/symbol/{species}/{symbol}`，稳定 id 再 `lookup/id/{id}` | HGNC id、approved symbol/name/status、prev/alias、Ensembl/UniProt ids；Ensembl stable id/version/species/assembly | `approved_alias/deprecated_symbol/species_match/species_mismatch_candidate`。大小写、同名 ortholog 或讨论人类 homolog 不能单独 mismatch |
  | `protein_coordinate_domain` | `GET https://rest.uniprot.org/uniprotkb/{accession}.json`；InterPro `GET https://www.ebi.ac.uk/interpro/api/entry/interpro/protein/uniprot/{accession}/` | accession、entry/sequence version、organism、canonical/isoform、length、sequence、feature type/start/end；InterPro/Pfam accession、名称、match fragments | 仅在 `numbering_basis + isoform + organism` 唯一时做 position range、reference residue 与 feature overlap；数据库无 function comment 为 `not_addressed` |

  HGNC 端点与字段以 [HGNC REST](https://hgnc.genenames.org/help/rest/) 为准；Ensembl 以
  [symbol lookup](https://rest.ensembl.org/documentation/info/symbol_lookup) 与
  [id lookup](https://rest.ensembl.org/documentation/info/lookup) 为准；UniProt 以
  [individual entry API](https://www.uniprot.org/help/api_retrieve_entries) 为准；InterPro 以
  [API 文档](https://interpro-documentation.readthedocs.io/en/latest/api.html) 为准。
  `external_check` 保存 `numbering_basis`、isoform、species、reference residue 与 feature interval；
  construct、mature chain、signal peptide 或 PDB author numbering 无 offset evidence 时停止比较。
- **代价**：3–4 人日；HGNC/Ensembl 1 人日，UniProt/InterPro 1–1.5 人日，isoform/成熟链/ortholog 困难反例 1–1.5 人日。
- **建议优先级**：P1；最小切片先交 exact accession + length/residue + InterPro overlap。AlphaFold/PDB 结构语义继续按 Round 11 留后，不在本轮重复扩张。
- **阶段 / 归属**：一期联网增强；X1 核验事实，M2 处理命名/指代一致性，M7 处理主张依赖。按本轮任务暂不路由 M3。
- **契约字段**：复用 `external`；扩展 `external_check` connector payload 为 `entity_context` 与 `coordinate_context` 即可，不重构 finding。
- **假阳性**：高。isoform、物种、前体/成熟链、构建体 offset、数据库版本任一不明确即 `not_comparable`。无注释不是反证，InterPro/Pfam 边界差异不能强并为唯一“真区间”。

### P5 · 独立 `external_validation_coverage` 与录制响应回归门禁

- **问题**：本轮 X1 limitation 已明确不改变现有三项评分，但顶层报告尚无“请求了多少、成功多少、因何失败”的机器对象。没有录制响应时，API 字段漂移、缓存命中和失败降级也无法离线回归。
- **影响**：用户看见没有 external signal，无法区分“全部匹配”“没有可核验对象”“网络全失败”；若把失败塞入 `extraction_coverage`，会把外部环境问题错误归因到论文抽取质量。
- **方案**：**一期工程迁移，Stage 5 非记录对象，P0。** 新增：
  ```json
  {
    "external_validation_coverage": {
      "requested": 8,
      "resolved": 5,
      "not_found": 1,
      "not_addressed": 0,
      "failed": 2,
      "cache_hits": 3,
      "by_connector": []
    }
  }
  ```
  要求五项状态之和等于 requested；`failed` 必须逐项指向 X1 system limitation；本对象不带
  severity，不进入 `extraction_coverage`、`review_confidence` 或 risk。修改
  `review_report.schema.json`、模板第六/七节、fixtures 与 validator。每个 connector 至少保存
  `resolved/not_found/not_addressed/429/403/503/schema_drift/cache_304` 八类脱敏响应 fixture；CI 默认
  只跑录制响应，在线 smoke test 单独执行且失败不阻断离线核心。对外部支持的 finding 做负例门禁：
  移除 present 首锚点、把 response 改 503、把 comparability 改 partial 后都必须拒绝 finding。
- **代价**：1–1.5 人日 schema/模板/聚合器；每个 connector 另需 0.5 人日录制响应。不得提交大规模数据库快照。
- **建议优先级**：P0；至少与首个 connector 同批落地，否则“零结果”不可解释。
- **阶段 / 归属**：一期；Stage 5 聚合视图，不属于 M1–M7，不新增记录。
- **契约字段**：新增非记录 `external_validation_coverage`；三类记录和现有三项评分不变。
- **假阳性**：不判断稿件。风险是把 404 计作成功或把 cache stale 当 resolved；状态必须从每个 request 的终态机械聚合，不允许模型自由填写。

## 未解决 / 需要人来定的问题

1. 是否批准首批白名单主机：`clinicaltrials.gov`、`www.ebi.ac.uk`、`europepmc.org`、
   `eutils.ncbi.nlm.nih.gov`、`rest.genenames.org`、`rest.ensembl.org`、`rest.uniprot.org`。
   未批准的主机必须走 `external_access_denied`，不得在运行时换代理或镜像绕过。
2. 是否接受 ClinicalTrials.gov 本期只比较**当前公开记录**。建议接受；没有稳定、公开、文档化的
   历史版本 API 时，禁止声称自动识别“注册后改终点”。
3. 是否采纳 P5 的独立 `external_validation_coverage`。建议接受；否则报告必须逐条列 X1 limitation，
   但仍不得把失败写入现有 extraction coverage。
4. 本轮按任务要求把 external signal 路由限定为 M2/M4/M6/M7。Cellosaurus、抗体/RRID、试剂目录
   和蛋白构建体身份最自然的消费者是 M3；若要实施 Round 10 P4 或 Round 11 的材料身份能力，需由
   团队明确批准把 X1 路由扩到 M3，不得让 connector 越过当前 schema。
5. `not_found` 是否进入人工队列。建议仅格式合法、精确 identifier 的权威 404 进入 P2 人工核对；
   名称/语义零命中 `not_addressed` 不进队列。两者都不得自动生成 finding。
6. SKILL.md 正文已超过 500 行。本轮只放 X1 核心操作规则；若 P1 被采纳，connector 端点与映射必须
   放 `references/08-external-verification.md`，不得继续堆回主文档。
7. Round 4 P1 的核心 schema 本轮已部分采纳；Round 4 P2、Round 9 P6、Round 10 P2/P4、Round 11
   P4–P6 仍只有提案。本轮 P2–P4 是对这些既有方向的统一实施顺序与端点映射，不应再建平行 X1。
8. 当前工作区排除 `.git` 后约 124 MB，且
   `datasets/papers/toxicology__journal.pone.0339571/paper.pdf` 约 18.7 MB，超过 50 MB/单文件
   10 MB 的严格提交口径；`datasets/**` 属本轮禁改路径，未擅自删除。打包负责人必须确认评测提交是否
   排除 `datasets/`；若不排除，应在提交清单层移除语料而不是修改论文文件，并重新生成包体积报告。
