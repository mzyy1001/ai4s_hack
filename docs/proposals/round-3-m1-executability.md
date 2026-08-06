# Round 3 · M1 抽取规则的可执行性 提案

## 摘要

§5.3 路由表中出现的字段都能在 §5.1/§5.2 找到名义定义，24 个 `design_type` 也都有族级或专门路由；真正的断点是 Markdown 规则未编译成可穷尽执行的决策表，`arms/claims` 被路由却没有三维字段状态，且 schema 允许多个条件必填字段整体省略。
`mixed/other` 缺端点归属与分类排除轨迹，五键 `grouping_key` 又会把性别、亚组、分析集、调整模型和批次不同的数值误并；这两项需要契约扩展，不应在本轮直改。
Round 1 的单位归一化与确定性统计取证已被采纳并实现；本轮不重复旧提案，新增路由编译器、设计分类轨迹、观测上下文、序列确定性检查、蛋白坐标核验与组学元数据对账六个组件。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §1.4、§2.8 | `targeted_check` 的 v1 在 scope 内有 `unresolved` 时强制先跑覆盖 `expected_sources[]` 的 Stage 3；观测先按 `metric_family + metric_name` 分流再比五键 | 未跑 Stage 3 时，`not_reported` 缺完整检索，`parse_failed` 缺真实解析尝试，pending 无合法收敛态；不同指标不得因五键相同而误并 |
| `skills/biomed-paper-review/references/00-contracts.md` | §4、§5.4 | 区分 v1 终态的 pending 覆盖率结算与 v2 收敛；禁止 Stage 3b 伪造视觉尝试；补全指标身份 + 五键的组身份 | 旧规则同时声称 pending “不降覆盖率”和 v1 终态“计入未解析”，且不同 metric 可落入同一组 |
| `skills/biomed-paper-review/references/01-structured-extraction.md` | §4.2、§5.3.3–§5.3.7、§6.2、§7.4、§9 | 分开“多设计事实”与“抽取不确定”；修复 case-control 错误定义、case report/series 纳排路由、一级人/动物材料伦理路由、动物剔除标准与 scoping review 偏倚评估路由；删除“跳过 Stage 3 也可收敛”的非法分支；signal 总枚举更正为十一值 | 旧表会把前瞻嵌套 case-control 说成“回顾性配对”，漏掉人源 organoid/一级细胞的伦理路由，并把 scoping review 的可选 critical appraisal 误判为概念不适用；“六种”已与现契约十一种不一致 |
| `skills/biomed-paper-review/schemas/structured_result.schema.json` | `article_design`、`$defs.design_pair_constraint` | 机器约束 7 族 × 24 型的 `family/type` 配对；禁止复合类型出现在实验组件；`preclinical_mixed` 强制展开为至少两个 experimental 组件 | 旧 schema 接受 `human_observational + randomized_controlled_trial`，也接受没有组件的 `preclinical_mixed` |
| `skills/biomed-paper-review/schemas/key_data.schema.json` | 文件与 `grouping_key` 描述 | 明确规范指标名与指标族是五键之前的分组门 | 五键相同不能说明 HR、中位生存和 p 值是同一个数值 |
| `docs/schema-migration.md`、`docs/consistency-audit.md` | `article_design` 迁移、模拟③、执行依赖图 | 记录新配对约束；把模拟③改为“本例无 pending，因此可跳过 Stage 3” | 旧审计把一个不含 pending 的 fixture 误当成“Stage 3b 可无条件收敛 pending”的证据 |

## B 类提案

### P1 · 把 §5.3 从 Markdown 编译为可穷尽的 M1 路由器

- **问题**：当前字段名义没有悬空引用，24 个 `design_type` 也都能落到某张表，但“有任何统计比较”、“使用人体数据”、“延迟型参照标准”等条件没有统一输入；同一优先级内的重叠、漏项和默认分支无法由当前 validator 穷尽。更直接的契约断裂是 `design.arms` 与 `conclusion.claims` 在 §5.3 被赋予 applicability/requiredness，schema 却把它们定义为无状态的裸数组；`follow_up`、`target_condition`、`dataset`等条件必填属性也可被整体省略，省略后既不是 `not_reported` 也不是 `parse_failed`。
- **影响**：两个实现可以对同一篇 human-organoid 稿件给出不同的 `ethics_statement.applicability`，进而改变 M6 路由与覆盖率分母。评委一旦追问“24 种设计是否全覆盖”，现有答案只是人工阅表。
- **方案**：**一期**先统一可路由形状：引入 `routed_collection` 包装 `{applicability,requiredness,status,items,evidence_refs,extraction_confidence,...}`，把 `design.arms` 与 `conclusion.claims` 迁移为该形状；其余在字段全集中的属性必须始终物化，不适用也要保留状态对象。再新增 `resources/m1_routing_rules.json` 与 `tools/route_m1_fields.py`。规则文件为每条路由保存 `{rule_id, priority, field_path, design_types[], predicate, true_result, false_result, search_scope, consumers[]}`；predicate 只读取显式三值路由上下文，如 `has_statistical_comparison: true/false/unknown`、`material_origin: established_cell_line/human_primary/animal_primary/unknown`。`unknown` 必须导向 `applicability_uncertain`，禁止当作 `false`。脚本穷尽 `24 design_type × 字段全集`，对“零条命中、同优先级多条命中、未定义 field_path、路由字段未物化、not_applicable 无 na_reason、absence 无 search_scope”任一情况 fail closed。`01 §5.3` 改为该 JSON 的人类可读投影，不再各自维护。
- **代价**：3–4 人日；需迁移 `arms/claims` 消费者与 fixtures，把现有八个小节转录一次，并为每个条件 predicate 定义上游证据字段。无外部依赖。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M1 / Stage 2 的执行基础设施，Stage 3b 只读其结果。
- **契约字段**：新增 `$defs.routed_collection`；扩展 `extracted_field` 与 `routed_collection` 为必填 `routing_rule_id` 和 `routing_context_refs[]`；在 `structured_result` 增加非记录对象 `routing_context`。三类记录不变，不需要 finding。
- **假阳性**：不直接产生稿件判断。风险是错路由导致下游规则误跑；所有不完整 predicate 都转 `applicability_uncertain` 并交人工，不自动转 `not_applicable`。

### P2 · 端点归属驱动的 `mixed` / `preclinical_mixed` / `other` 分类轨迹

- **问题**：`mixed` 的核心条件是“没有单一组件承载全部 primary endpoints”，但 `primary_endpoint` 没有 `experiment_id` 或组件归属，该条件无法复算。`other` 只要求一段自由文本，没有证明 24 个已知类型已逐一排除。`preclinical_mixed` 与文章级 `mixed_multi_family` 的分界也只在 TODO 中。
- **影响**：实验链“细胞机制 + 动物验证”可被不同实现分成 `experimental/preclinical_mixed`、`mixed` 或 `other`，随后 M3/M4/M6 的字段白名单全部改变。
- **方案**：**一期**为 `objective.primary_endpoint` 解析出 `endpoint_items[]:{endpoint_id,name,role,experiment_refs[],evidence_refs[]}`，为 `design_components[]` 增加 `component_role: primary/supporting/validation` 和 `endpoint_refs[]`。固定判据：①同一 experimental family 内，至少两个不同叶子类型共同支撑主端点 → `preclinical_mixed`；②至少两个不同 family，且无任一组件覆盖全部 primary endpoint → `mixed_multi_family`；③多个候选是读法不确定而非事实多设计 → `alternatives[] + ambiguous_study_design`；④只有 `classification_trace.candidates=[]` 且每个 family 都记录一条未满足的必要条件时才允许 `other_unclassified`。优先补边界对：`ex_vivo` vs `organoid`、`cohort` vs `case_control`、`prediction_model` vs `benchmark_study`、`systematic_review` vs `scoping_review`。
- **代价**：2 人日契约与规则，1–2 人日在 10 篇语料上双人标注。依赖 P1 的机器路由器。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M1 设计分类，M2/M3/M4/M6 只消费结果。
- **契约字段**：扩展 `primary_endpoint`、`design_components[]` 与 `article_design.classification_trace:{rule_version,candidates[],eliminated[],endpoint_coverage}`；不重构三类记录。
- **假阳性**：不立 finding。端点无法绑定实验时，`primary_design.status=ambiguous` 并路由人工；禁止为了给出唯一 type 而猜测 endpoint ownership。

### P3 · 上下文完整的观测组身份

- **问题**：现有五键不包含亚组、性别、ITT/PP 分析集、未调整/调整模型、标本区室、实验批次和归一化方式。例如同一 RCT 的总体 HR 与女性亚组 HR，或同一 RNA-seq 终点的未调整与多变量调整效应，当前可落入同组并被标为 `conflicting`。
- **影响**：这会制造最危险的假阳性之一：把正常的 effect modification、sensitivity analysis 或 batch-specific result 写成稿件内部矛盾，并由 M2/M7 放大成 finding。
- **方案**：**一期**扩展 `grouping_key` 而不改观测组架构：新增 `analysis_population` （`overall/ITT/mITT/PP/safety/other/null`）、排序后的 `strata[]:{axis,level}`、`specimen_context:{species,tissue,model_system}`、`assay_context:{assay,matrix,normalization}`、`analysis_variant:{adjustment_status,adjustment_set,imputation}` 和 `reported_batch`。只有论文把 batch/run/plate 作为分开结果报告时才填 `reported_batch`；纯技术来源保留在 provenance。上下文完整且全等才自动合组；两个来源的关键上下文都为 `null` 时，只有显式交叉引用同一图/表单元格才可合组，否则分立并出 `partial_extraction` signal。
- **代价**：2–3 人日；需迁移 `key_data.schema.json`、`figure_record.target_grouping_key`、fixtures 和单位/统计取证工具的输入适配。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；M1 建组，Stage 3 填目标上下文，Stage 3b 合并；M2/M4/M7 消费。
- **契约字段**：只扩展 `grouping_key` 与对应 `target_grouping_key`；可增加 `context_completeness: complete/partial` 和 `context_evidence_refs[]`。无需新顶层记录。
- **假阳性**：高，但方案的默认动作是“不合组”而非“判冲突”。上下文不全时只降覆盖率并交人工，不产生 `source_value_conflict`。

### P4 · 引物、序列与变异坐标确定性审计器

- **问题**：方法中的 primer 序列、反向互补关系、预期 amplicon、密码子和氨基酸位点可以确定性核对，当前 M1 却只能把它们当自由文本。错一个碱基、把 reverse primer 当正向序列、或使用不同 transcript isoform，都可以让整个 qPCR 机制链失效。
- **影响**：这是一期最能体现“不是套壳大模型”的本地能力；不做会漏掉可客观复现的方法错误，直接用简化 Tm 公式下结论又会在 Mg²⁺/盐浓度不明时制造假阳性。
- **方案**：分两步。**一期**新增 `tools/sequence_forensics.py`，只读论文/补充材料或用户提供的 FASTA：① IUPAC 字母、长度、GC%、反向互补与重复序列；②将 forward 与 reverse-complement primer 在明确 transcript/genome 版本上做退化碱基精确匹配，输出方向与 amplicon 长度；③核对 HGVS/codon 的 reference base/amino acid 与位点是否越界。Tm 只在盐、Mg²⁺、dNTP 和 primer 浓度齐全时用 nearest-neighbor 复算；否则仅输出 `tm_inputs_incomplete`，禁止判错。**二期**经外部证据层调用 Ensembl `GET /sequence/id/{stable_id}?type=cds|cdna|genomic` 或 NCBI EFetch `efetch.fcgi?db=nuccore&id={accession.version}&rettype=fasta&retmode=text`；必须固定物种、assembly、transcript 与版本。官方端点见 [Ensembl sequence API](https://rest.ensembl.org/documentation/info/sequence_id) 与 [NCBI EFetch](https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.EFetch)。
- **代价**：一期 3–4 人日，二期 connector 1–2 人日；需正反例 FASTA、退化引物和多 isoform fixture。
- **建议优先级**：P1 应该做（一期本地部分）；外部序列获取二期做
- **阶段 / 归属**：一期 M1/Stage 2 工具层产 signal，M3 判方法学 finding；涉及 claim 的变异功能由 M7 复核。M1 不产 finding。
- **契约字段**：在 `structured_result` 增 `sequence_entities[]:{id,kind,sequence,orientation,target_id,organism,reference_version,evidence_refs}`；扩展 signal type 为 `sequence_mismatch_candidate` / `coordinate_out_of_range` / `tm_inputs_incomplete`，并增加条件必填 `sequence_check:{algorithm,rule_version,reference_hash,inputs,result}`。
- **假阳性**：中到高。多 isoform、信号肽/成熟蛋白编号、引物 5' adapter/tail、允许 mismatch 的突变特异引物都会误报。只有参考序列版本与编号基准明确时才生成确定性 candidate；否则 `partial_extraction` 并交人工。

### P5 · 蛋白变体–结构域–结构坐标对账器

- **问题**：Round 1 P5 已提出 UniProt 身份核验，但尚未覆盖“R175H 的参考氨基酸是否真为 R”、“位点是否在该 isoform 长度内”、“声称位于 kinase domain 是否与 InterPro/Pfam 坐标重叠”和“已解析 PDB 是否实际覆盖该残基”。这些是坐标问题，不是泛化的“功能相似度”。
- **影响**：编号越界或 reference residue 错误是可确定检出的硬错；而“未见数据库注释”并不反证新功能。两者不分开会要么漏报，要么冤枉真正的新发现。
- **方案**：**二期**作为 Round 1 X1 的增量 connector，不新建并行架构。① UniProt `GET https://rest.uniprot.org/uniprotkb/{accession}.json` 取 canonical/isoform 长度、sequence 与 feature 坐标；② InterPro `GET https://www.ebi.ac.uk/interpro/api/entry/interpro/protein/uniprot/{accession}/` 取结构域匹配区间，接口组合语义见 [InterPro API](https://www.ebi.ac.uk/interpro/api/static_files/swagger/)；③ PDBe v2/SIFTS 做 UniProt↔PDB 残基映射，调用 `/pdbe/api/v2/mappings/uniprot/{accession}` 与具体 PDB 的 secondary-structure/domain 端点，官方 v2 入口见 [PDBe API](https://www.ebi.ac.uk/pdbe/api/)。AlphaFold DB 只用于结构候选复核：下载 mmCIF 后从 residue-level pLDDT 判断该区段是否足以评估二级结构；低 pLDDT 表示“无法核对”，不表示论文错误。AlphaFold 官方下载说明见 [AlphaFold DB downloads](https://alphafold.ebi.ac.uk/download)。
- **代价**：4–5 人日；依赖 Round 1 外部 evidence 产出者/stage 决策，需 isoform、signal peptide、propeptide 和 PDB 缺失残基 fixture。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；X1 产 external evidence/signal，M3 核对材料与构建，M7 核对结构/功能 claim。
- **契约字段**：复用 Round 1 P4 的 external evidence，增加 `protein_coordinate:{accession,isoform,numbering_basis,claimed_position,claimed_residue,sequence_length,resolved_residue}`、`feature_overlap[]:{source,feature_id,start,end,overlap}` 与 signal type `protein_coordinate_mismatch_candidate` / `domain_location_mismatch_candidate`。finding 仍必须同时引用稿件内 claim 证据。
- **假阳性**：高。只有 exact accession + isoform + numbering basis 都明确时，越界/reference-residue mismatch 才是确定性 candidate。成熟蛋白编号、类缘蛋白编号、数据库无注释、AlphaFold 低 pLDDT 全部降级为人工复核，不得自动判“功能错误”。

### P6 · GEO/SRA/BioSample 的样本与文库元数据对账

- **问题**：Round 1 P4 的数据登录号网关主要核验“号码是否存在”。真实审稿中更关键的是对账：论文称 48 例人肿瘤 paired-end RNA-seq，存档却可能只有 36 个 unique BioSample、部分为小鼠、或 `library_strategy` 实为 WGS。用 Run 数代替样本数又会把技术重复误当生物学 n。
- **影响**：只验登录号会给“已接外部数据”留下很浅的印象；样本数、物种、组织、sex、treatment、library strategy/layout 与 platform 的矛盾才是会改变方法可复现性和 claim 范围的实质问题。
- **方案**：**二期**作为 Round 1 数据登录号 connector 的第二层。先用 NCBI E-utilities `esearch.fcgi?db=sra&term={accession}[ACCN]&retmode=json`，再用 `efetch.fcgi?db=sra&id={uid}&retmode=xml` 取 Study→Sample→Experiment→Run 图；沿 BioSample accession 调 `efetch.fcgi?db=biosample&id={uid}&retmode=xml` 取 organism/taxid、tissue、sex、disease、treatment 和自定义 attributes。NCBI 明确把 SRA metadata 组织为 Study/Sample/Experiment/Run，且 library strategy/layout/instrument 属于 Experiment，见 [SRA metadata model](https://www.ncbi.nlm.nih.gov/sra/docs/submitmeta/)；BioSample 用于描述实体生物材料，见 [BioSample documentation](https://www.ncbi.nlm.nih.gov/biosample/docs/)。对账时以 unique BioSample 计生物样本，Run 数只作技术文件数；分别输出 exact mismatch 与 `metadata_missing`。
- **代价**：3–4 人日；依赖 Round 1 X1，需缓存、限速、XML 版本 fixture 与 multi-omics/池化样本测试集。
- **建议优先级**：P1 应该做
- **阶段 / 归属**：二期；X1 产 external evidence/signal，M2 判数据可及性，M3 判样本与测序方法，M7 判结论范围。
- **契约字段**：external evidence 增加 `archive_graph:{study_accession,sample_accessions[],experiment_accessions[],run_accessions[]}`、`sample_metadata[]`、`library_metadata[]` 和 `response_hash`；signal type 增 `archive_metadata_mismatch_candidate`，target 存 `{manuscript_value,archive_value,comparison_dimension,comparability}`。
- **假阳性**：高。质控后剔除、pooled sample、multi-omics、一个 BioSample 多 library、数据库元数据未更新和 dbGaP 受控数据都可以造成表面差异。任何差异先产 signal；只有 accession 精确对应、数据公开、维度语义一致，且 M3 排除 QC/池化解释后才可立 finding。API 故障只产 `system_limitation`。

## 未解决 / 需要人来定的问题

1. P1 的路由规则 JSON 是否成为唯一规范源；若 Markdown 与 JSON 都允许手工修改，两者必然再次漂移。
2. P2 的 `endpoint_items[]` 是否在周日前进行 schema migration；不迁移则 `mixed` 的第二个合法性条件仍无法机器证明。
3. P3 是否接受“上下文不全默认不合组”的保守策略；它会增加人工合并量，但能避免把亚组/调整分析误报为冲突。
4. Round 1 外部 evidence 的产出者与 `stage_3c` 尚未拍板；P4 二期部分、P5 和 P6 在该决策前只能做 connector 原型，不得绕过 evidence registry 直接向 M3/M7 送判断。
5. `preclinical_mixed` 是否必须包含 `in_vivo_animal`。建议不以“有动物”作语义必要条件：`in_vitro + organoid + ex_vivo` 也可形成跨模型预临床证据链；应以两个不同实验叶子类型共同支撑主端点为判据。
