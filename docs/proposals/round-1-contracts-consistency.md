# Round 1 · 契约一致性与可实现性 提案

## 摘要

旧报告模板仍使用已废弃字段，且 `execution_scope` 被错误标成 Stage 5 产物；两者已直接修复。
`§5.4` 原先没有覆盖全部数值变体，`§5.5` 的“命中即停”与兜底规则互相冲突，评分公式也从未被校验器复算；本轮已把这些规则收敛为确定算法并补齐验证。
下一阶段最值得投入的是观测级血缘、UCUM 单位归一化、确定性统计取证、注册/数据登录号核验、生物实体身份核验、撤稿状态核验与图像取证。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §0.2、§2.4、§4.2、§5.3 | 修复不存在的二期文档链接；把 `execution_scope` 的产出者改为 Stage 1 前的执行规划步骤；修正 evaluation matrix 小节号；明确 observation 评分分母 | 旧文本让 Stage 1–4 消费一个“Stage 5 才产出”的白名单，且存在悬空路径与失效小节引用 |
| `references/00-contracts.md` | §2.3、§5.3–§5.5 | 约束 `ocr_text ⇔ ocr_used=true`；补齐分类值、点值、区间、单边界的穷尽比较和组状态归档；把 canonical 改为逐层筛选 | 原算法存在未定义分支；“命中即停”会在多个候选同时命中时无法选择，字典序兜底又与“无法选择时置 null”矛盾 |
| `references/00-contracts.md` | §7.1、§8、§9 | 新增 `execution_scope.observations[]`；规定三位小数舍入、finding↔observation 关联、冲突计数、cluster 的单一计分类别与稳定代表选择；为 absence 证据定义锚点回退 | 原 confidence 分母、风险分类上限和聚簇代表无法唯一复算；absence 没有 locator，旧主锚点算法会中断 |
| `references/00-contracts.md`、`SKILL.md`、`references/07-conclusions-discussion.md` | 迁移表与内部引用 | `01 §8/§8.4` 改为 `§11/§11.4`，M7 的外部文献引用改为 `§11.1`，风险分聚簇引用改为 `§9.3` | 上一轮审计声称引用均可解析，但这些引用已随章节重排失效 |
| `schemas/common.schema.json` | `uncertainty`、`derivation` | 禁止负 SD/SEM、禁止 `none` 携带数值、强制区间/离散度字段形状，并机器约束 OCR 标志 | 旧 schema 接受 `{"type":"none","low":3}`、`SD=-1`、`ocr_text + ocr_used=false` |
| `schemas/key_data.schema.json` | 组状态与 observation | `reported`/多来源/冲突/pending/parse_failed 分别约束 observation 数量、canonical、关系数组与系统限制；关键 observation 字段改为显式必填 | 旧 schema 一方面要求所有组至少一个 observation，导致 `parse_failed` 无法表示；另一方面允许 `reported` 无 canonical 或含多个来源 |
| `schemas/execution_scope.schema.json` | 全文件 | 增加 observation 分母、数组去重、Stage 1→5 完整依赖和审核模块↔Stage 4/5 绑定 | 旧 schema 允许重复模块凑满 6 个，也允许执行审核模块却不声明 Stage 4/5 |
| `schemas/review_report.schema.json` | 模式条件、confidence、issue cluster | 审核模式强制输出 v2/findings/clusters/复核计划；低置信度警告机器化；cluster 强制 anchor 并支持 absence 回退 | 旧 schema 允许有风险分却没有 findings/clusters，且 `<0.5` 警告只写在 description 中 |
| `templates/review_report.md` | 全文件 | 从旧 `confidence_score`、`methods.*`、`min_group_n`、内联 evidence 迁移为固定八节与现契约字段 | 旧模板无法渲染任何符合当前 schema 的完整报告，是演示时会直接暴露的断裂 |
| `tools/validate_schemas.py` | schema lint、实例 lint、评分校验 | 新增模板迁移检查、absence 类型校验、key_data 引用校验、mode/stage 校验，并实际复算 risk/coverage/confidence 与复核计划覆盖 | 原“全部通过”只验证字段存在，没有证明公式结果正确 |
| `tools/fixtures/*.json` | 四个模拟的 `execution_scope`；sim4 证据与 finding | 补齐 observation scope；删除“15.1 超过 15.7 上界”的错误陈述；为两个 `not_reported` 字段补合法 absence 证据 | 原模拟含明显算术错误，并用 present 证据支撑缺失状态，违反证据契约 |

## B 类提案

### P1 · 观测登记表与评分血缘正规化

- **问题**：本轮用 `execution_scope.observations[]` 修复了分母，但同一 observation 仍可能同时内联在 `figure_records` 与 `structured_result.key_data`；finding 依赖 observation 只能通过共享 `evidence_ref` 保守反推。一个证据条目承载多个读数时，pixel/OCR 依赖率会过度惩罚；跨模块“语义重合”也没有机器键。
- **影响**：同一报告在不同实现中可能得到不同 confidence 和 category cap；重复 observation 副本漂移时，评分无可信血缘。评委会把“公式写得漂亮但无法稳定复算”视为工程硬伤。
- **方案**：二期前先做契约重构：在 `review_report` 顶层新增 `observation_registry`，`key_data.observations[]` 与 `figure_records.observations[]` 改存 `observation_refs[]`；finding 新增必填但可为空的 `observation_refs[]`；cluster 新增 `issue_key` 与单值 `scoring_category`。修改 `00-contracts.md §5/§6/§8/§9`、`key_data.schema.json`、`figure_record.schema.json`、`finding.schema.json`、`review_report.schema.json` 与 fixtures，并迁移旧内联 observation。`issue_key` 由 `{anchor, normalized_problem_family, affected_target}` 生成，无法归一时禁止跨模块自动合簇。
- **代价**：2–3 人日；需要一次 schema migration，所有 M2–M7 finding 示例要同步。无外部依赖。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：一期契约加固；Stage 3、3b、4、5 共用，不新增审核模块。
- **契约字段**：新增 `observation_registry`、`observation_refs[]`、`issue_key`、`scoring_category`；保留三类顶层记录，不新增第四类记录。
- **假阳性**：不产生稿件判断；风险是错误合簇导致漏计。只有 `issue_key` 完全相同才自动合簇，其余并列展示交人工。

### P2 · UCUM 驱动的生物医学单位归一化器

- **问题**：上一轮审计已承认 `§5.4` 所需单位表不存在。当前 fail-closed 规则能避免冤枉稿件，但会把 `µM`/`μmol·L−1`、`mg/mL`/`g/L` 等本可确定换算的观测降为 `ambiguous`；质量浓度↔摩尔浓度还依赖化合物分子量，不能混在普通换算里。
- **影响**：药理、蛋白定量与临床检验论文会产生大量人工复核；若工程师自行写替换表，最危险的是把 `mg/kg`、`mg/kg/day`、`mg/m²` 或总蛋白归一化单位错误合并。
- **方案**：一期新增 `tools/normalize_biomed_units.py`：解析 Unicode 微符号、乘方、斜杠与 `per`，输出 UCUM code、量纲、倍率和规则版本；只做同量纲确定性换算。质量↔摩尔转换必须同时提供 analyte 与明确 molecular weight，缺任一项返回 `conversion_requires_molecular_weight`，不得换算。为 observation 扩展 `unit_normalization:{status,ucum_code,dimension,conversion_factor,rule_id,analyte_ref}`；`unit_normalized` 保留作索引。为常见浓度、时间、长度、质量、细胞数、活性单位写表驱动测试；把区间端点与 uncertainty 同步换算。
- **代价**：1.5–2 人日；若直接采用成熟 UCUM 库需新增依赖，否则维护最小白名单。化合物分子量查询属于二期外部连接器。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；Stage 2/3b 的 M1 工具能力，不产 finding。
- **契约字段**：扩展 observation，不重构三类记录；失败只造成组 `ambiguous` 或 `partial_extraction` signal。
- **假阳性**：低。未知别名、复合单位、按体表面积归一与 analyte 不明一律 fail closed；禁止近似分子量自动转换。

### P3 · 无外部数据的统计取证组件

- **问题**：一期把“统计复现”整体推迟，但实际上多类确定性检查不需要原始数据：检验统计量/自由度/p 值自洽、效应量/SE/95% CI 自洽、百分比与计数自洽，以及满足严格前提时的 GRIM/GRIMMER。
- **影响**：这是最能证明团队懂真实审稿而非套壳 LLM 的一期能力；当前 M4 只能检查报告完整性，会漏掉复制错误、p 值错位和不可能的汇总统计。
- **方案**：一期新增 `tools/statistical_forensics.py`，输入 M1 observation 与正文统计表达式，输出扩展后的 `extraction_signal`，再由 M4 决定 finding：
  1. `test_statistic_p_mismatch`：仅对明确给出 test family、statistic、df、tail 的 t/F/χ²/z 检验反算 p；比较使用论文报告精度对应的舍入区间；
  2. `ci_estimate_mismatch`：仅对明确双侧 95% CI 与可识别尺度的差值、log(OR/RR/HR) 检查点估计是否位于 CI 内，并在对称/Wald 前提明确时反推 SE；
  3. `count_percentage_mismatch`：`count/n` 与百分比的舍入区间不相交才报警；
  4. `grim_incompatible_mean`：只用于等权、整数取值、明确 n 的原始算术均值；调整均值、LS mean、加权/缺失后 n、连续量表一律不跑；
  5. GRIMMER/SPRITE 先只输出候选并强制人工，因为可行解与舍入假设更多。
  修改 `04-statistics.md` 的消费规则需要模块负责人执行；本轮只在提案登记，禁止直接改该文件。
- **代价**：2–4 人日；需要分布函数实现或锁定一个数值库，并为每个检验写边界/舍入测试。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M1/工具层产 signal，M4 产 finding。M1 仍不产 finding。
- **契约字段**：扩展 signal type 枚举；observation 增加 `reported_value_text`、`rounding_interval`；signal target 记录 `calculation_inputs`、`expected_interval`、`observed_interval`、`rule_version`。不新增记录类型。
- **假阳性**：中。所有前提必须由明确文本证据满足；前提不全输出 `partial_extraction` 或不运行。SPRITE 多解、调整估计和单尾检验不得直接下稿件判断。

### P4 · 注册与数据登录号核验网关

- **问题**：临床论文的注册号、预设主要终点、首次提交时间与入组时间，以及 GEO/SRA/PRIDE 登录号是否真实存在，都是高价值且可客观核验的信息。现在 `design.registration` 与 `data_availability` 只能证明“论文写了什么”，不能证明编号有效。
- **影响**：伪造/写错登录号、回顾性注册、注册终点与论文主终点漂移会直接影响伦理、选择性报告与可复现性评分；这是生物医学评委非常熟悉的硬指标。
- **方案**：二期新增独立 `external-evidence-resolver`（MCP server 或 `tools/external_registry.py`）：
  - ClinicalTrials.gov：`GET https://clinicaltrials.gov/api/v2/studies/{nctId}`，另取 `/api/v2/version` 的 `dataTimestamp`；比较 NCTId、study type、enrollment、arms、primary outcomes、start date 与 first submit date。官方 v2 单研究端点与版本端点见 [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/about-api/api-migration)。
  - GEO/SRA：用 NCBI E-utilities `esearch.fcgi` + `esummary.fcgi`，分别查询 `db=gds` 与 `db=sra`；NCBI 明确将 E-utilities 作为 Entrez 公共 API，GEO 也提供 programmatic access 指南：[NCBI APIs](https://www.ncbi.nlm.nih.gov/home/develop/api/)、[GEO programmatic access](https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html)。
  - PRIDE：`GET https://www.ebi.ac.uk/pride/ws/archive/v2/projects/{accession}`，核对项目状态、标题、物种、publication 与文件清单；接口能力见 [PRIDE Archive API Guide](https://www.ebi.ac.uk/pride/ws/archive/v2/docs/api-guide.html)。
  抽取器先给出稿件内 `present` evidence；网关返回 external evidence。`accession_not_found` 先重试、记录 HTTP 状态与查询时间，只有数据库明确 404/零结果且编号格式合法才出 signal。M2/M4/M6 分别判断可及性、终点漂移与注册时序。
- **代价**：3–5 人日；需缓存、限速、重试、API schema 版本测试。ClinicalTrials.gov 先做，GEO/SRA/PRIDE 逐个加 connector。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；新增外部证据解析层 X1，位于 Stage 3b 后、Stage 4 前；路由 M2/M4/M6。
- **契约字段**：落实 `07-conclusions-discussion.md §11.4` 已提出但未实现的 `external` evidence 分支，增加 `database`、`endpoint`、`query`、`record_id`、`retrieval_date`、`database_version`、`http_status`、`response_hash`、`relation_to_claim`；新增 signal types `registration_mismatch`、`late_registration_candidate`、`accession_unresolved`。finding 仍必须同时引用稿件内 evidence。
- **产出者变更**：若采用 `stage_3c`，同步把 `extraction_signal.produced_by` 与 `evidence.created_by` 扩为允许 `stage_3c`；X1 只产 external evidence 与无 severity signal，不产 finding。
- **假阳性**：中。注册终点允许合理措辞差异，语义不一致只交人工；“first submit 晚于 start date”标 `candidate`，不能自动推定不当；临时 API 故障只能产 system limitation，不能产 finding。

### P5 · 基因、蛋白与细胞系身份核验器

- **问题**：废弃基因符号、物种张冠李戴、蛋白 accession 对不上实验物种、以及已知误认细胞系，常使整条机制链失效。单靠语言模型记忆核验这些事实既不可审计，也容易把别名误判为错误。
- **影响**：此类问题一旦属实通常是 major/critical，但假阳性同样会严重伤害审稿可信度；必须以权威记录和精确标识符为中心。
- **方案**：二期由 X1 提供三个 connector：
  - 基因：先 `GET https://rest.genenames.org/fetch/symbol/{symbol}`，无命中再查 `search/prev_symbol/{symbol}` 与 `search/alias_symbol/{symbol}`，保存 approved symbol、HGNC ID、previous/alias、Ensembl 与 UniProt IDs；HGNC 官方接口、JSON/XML 和 10 req/s 限速见 [HGNC REST help](https://www.genenames.org/help/rest/)。非人类符号再用 `GET https://rest.ensembl.org/lookup/symbol/{species}/{symbol}` 返回物种与稳定 ID，端点见 [Ensembl REST](https://rest.ensembl.org/documentation/info/symbol_lookup)。
  - 蛋白：已有 accession 用 `GET https://rest.uniprot.org/uniprotkb/{accession}.json`；只有 gene+species 时用 UniProtKB search，返回 reviewed 状态、organism、recommended name、function comments、domains/features 与 cross-references。单条记录格式和 404/410 语义见 [UniProt programmatic access](https://www.uniprot.org/help/api_retrieve_entries)。
  - 细胞系：优先要求 RRID/CVCL accession；用 `GET https://api.cellosaurus.org/cell-line/{accession}?format=json`，无 accession 才用 `/search/cell-line?q=...`，返回推荐名、同义名、物种、疾病、STR 与 problematic/misidentified 注释。端点示例见 [Cellosaurus API](https://api.cellosaurus.org/)。
  输出只做事实对照：`approved_alias`、`deprecated_symbol`、`species_mismatch_candidate`、`accession_not_found`、`misidentified_cell_line_candidate`、`annotation_supports/does_not_address_claim`。蛋白功能“数据库未注释”绝不能等价于“论文功能错误”。
- **代价**：4–6 人日；需要实体抽取、物种上下文、缓存与同义词消歧。先做 HGNC+Ensembl+Cellosaurus，UniProt 功能对照随后。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；X1 产 external evidence/signal，M3 评估材料身份，M7 评估功能主张。
- **契约字段**：复用 P4 external evidence；signal target 增加 `entity_type`、`manuscript_name`、`manuscript_species`、`resolved_id`、`resolved_species`、`match_type`。不修改 finding 的 severity 机制。
- **假阳性**：高。别名、同名异物种、细胞系衍生株和转染株一律先交人工；只有明确 accession 与权威记录直接矛盾时才允许下游考虑 major，数据库无记录只能是 system limitation 或低置信 signal。

### P6 · 引文撤稿/更正状态核验器

- **问题**：论文可能以已撤稿或已被重大更正的研究支撑关键主张；当前一期只检查论文内部引用关系，无法识别外部文献状态。
- **影响**：核心结论依赖撤稿证据是编辑最关心的风险之一；但“引用撤稿论文”也可能是为了讨论不端案例，不能见到 retraction 就自动处罚。
- **方案**：二期解析参考文献 DOI/PMID/PMCID，经 Europe PMC
  `GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{doi}&resultType=core&format=json`
  或 `/article/{source}/{id}` 获取完整元数据，再用 status-update search 核对 retraction/correction 关联；Europe PMC 官方 REST 支持 DOI/PMID 查询、core 元数据、references/citations 与 status-update 操作，见 [Europe PMC REST API](https://europepmc.org/RestfulWebService)。先把引文在正文中的语境分成 `supports_claim` / `background` / `discusses_retraction`，只有前两类进入人工复核队列。
- **代价**：2–3 人日；需要参考文献标识符归一与 citation-context 解析。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；X1 + M2（参考文献完整性）+ M7（关键主张证据链）。
- **契约字段**：external evidence 增加 `update_type`、`update_record_id`、`citation_context`、`relation_to_claim`；新增 signal type `citation_status_update`。任何 finding 同时引用论文内 citation locator 与外部状态记录。
- **假阳性**：中。只出现撤稿记录先出 signal；若正文明确把该文献当正面证据，M7 才可立 finding。API 无命中、DOI 歧义或仅有轻微 correction 均交人工，不自动赋 critical。

### P7 · 论文内图像取证候选生成器

- **问题**：重复显微区域、重复/翻转的 Western blot 条带和拼接边界无法靠文字契约发现；同时，压缩、统一背景、重复结构与合法复用会产生大量伪阳性。
- **影响**：图像异常是评委容易感知的高价值能力，但若系统直接指控不端，单个假阳性就会摧毁可信度。
- **方案**：一期在 Stage 3 增加可选 `image_forensics`：
  1. 面板切分后对重叠 tile 做感知哈希召回，使用局部特征 + RANSAC 验证平移/旋转/镜像/缩放；
  2. 对 blot lane 做背景扣除后的纵向强度轮廓相关，并排除同一 lane 的合法重复曝光声明；
  3. 拼接只检测候选边界：局部噪声方差突变、笔直梯度断点与重复背景联合命中，不用单一边缘阈值；
  4. 候选以 bbox、变换矩阵、相似度、阈值、缩略图和原图 evidence_ref 进入 `figure_record.forensic_candidates[]`，由 M5 Reviewer 查看原图后决定是否产 finding。Stage 3 仍不产 finding。
- **代价**：4–7 人日；需要 OpenCV/图像依赖、合成阳性集与语料负例标注。先做同图/跨图重复区域，再做 blot 与拼接。
- **建议优先级**：P2 二期做
- **阶段 / 归属**：一期可做最小候选器；Stage 3 产嵌套候选，M5 消费。禁止修改 M5 文件，需模块负责人采纳后落地。
- **契约字段**：扩展 `figure_record`，新增 `forensic_candidates[]:{type,source_region,target_region,transform,similarity,threshold,algorithm_version,evidence_refs,manual_review_needed}`；它是嵌套分析对象，不是第四类顶层记录，不带 severity。
- **假阳性**：高。所有候选 `manual_review_needed=true`，不得出现“伪造”“不端”定性；只有跨面板高相似、几何验证通过且无图注明示复用时，M5 才能建立最高 `review_confidence=medium` 的疑似 finding。

## 未解决 / 需要人来定的问题

1. 是否接受 P1 的 observation 正规化迁移；若周日前不迁移，当前 `execution_scope.observations[]` + value/provenance 副本一致性校验可作为一期兼容方案。
2. P2 是引入完整 UCUM 依赖，还是维护覆盖语料的最小白名单；必须指定唯一实现，禁止两个模块各自归一化。
3. P3 需要 M4 负责人确认 signal type 与 category slug；在确认前不得改 `04-statistics.md`。
4. 外部 evidence 是按 `07 §11.4` 增加第三分支，还是另建 `external_evidence_registry`；建议前者，但需全组拍板并做 schema migration。
5. X1 放在 Stage 3b 与 Stage 4 之间是否命名为新阶段 `stage_3c`；若新增 stage id，需同步所有 mode 依赖图与 `execution_scope.schema.json`。
6. 图像候选是否进入周日初筛范围；没有至少 20 个负例面板做阈值校准前，不建议在演示报告中展示自动定性。
