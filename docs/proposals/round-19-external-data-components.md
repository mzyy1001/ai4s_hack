# Round 19 · 外部数据源与新功能组件 提案

## 摘要

现有 X1 的三型证据、失败降级与 `external_validation_candidate` 契约已经落地，但运行时 connector 仍为零；在此状态下继续增加数据库名称不会产生 uplift，所有新组件都必须复用 Round 12 的唯一 resolver。
已有提案已经覆盖临床注册、撤稿、数据 accession、基因/蛋白/细胞系/抗体身份、变异、肽段唯一性与化合物活性，本轮不重复这些方向，集中提出 CRISPR 靶向取证、Reactome 富集复算、跨物种直系同源关系核验三个垂直切片。
三项都把数据库事实与稿件判断分开：外部失败只产 `system_limitation`，数据库未收录不构成反证，高假阳性比较只能进入人工复核。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/01-structured-extraction.md` | §14 标识符真实性核验表，抗体 / 试剂行 | 把“Antibody Registry 可证明抗体无特异性”改为核对 RRID、厂商、货号、靶标、宿主、反应物种与登记警示，并明确“未列某应用”只表示未知 | 登记记录不是独立特异性实验；旧表述会把缺少用途注释错误升级为方法学问题，与 Round 2 P5 已定义的安全边界冲突 |

## B 类提案

### P1 · CRISPR guide—参考组装—PAM—靶位点闭合审计器

- **问题**：当前 `sequence_identifier_audit.py` 只检查序列字母表、引物粗略 QC、HGVS 子集与给定完整参考序列上的位置；Round 11 P4 提过 primer pair 和参考版本，但把全基因组 off-target 留到二期，也没有覆盖 CRISPR。论文中的 sgRNA 可能根本不落在声称的基因、使用了与 nuclease 不相容的 PAM、在完整参考组装上多位点精确匹配，或声称 base edit 却没有可编辑碱基落入编辑窗口。这些是序列层面的可复算事实，不应交给模型凭记忆判断。
- **影响**：错误 guide 会使 knockout / CRISPRi / CRISPRa / base-edit 证据链失效；只检查 20 nt 字母表会错过最实质的构建设计错误。裸模型无法遍历完整参考组装、正反链和注释坐标，现有工具在此类稿件上的 uplift 仍接近零。
- **方案**：**一期离线保底 + 一期联网增强，M1 / X1 / M3 / M7。** 不新建平行外部层，在 `skills/biomed-paper-review/scripts/sequence_identifier_audit.py` 增 `crispr_target` operation；若复杂度影响现有自检，再拆为同目录 `crispr_target_audit.py`，仍由统一 deterministic runner 调用。
  1. M1 新增 `genome_editing_reagents[]`：`{reagent_id,experiment_id,guide_sequence,declared_5prime_extension,nuclease,pam_rule,edit_mode,species_taxid,assembly_accession,claimed_gene_id,claimed_transcript_id,claimed_target_interval,claimed_strand,editor_window,claimed_edit,evidence_refs[]}`。`nuclease`、`pam_rule`、assembly、物种任一缺失时不得默认成 SpCas9 / NGG / GRCh38，只产 `partial_extraction`。
  2. 离线路径接受用户提供的版本化 FASTA + GFF3，保存 assembly accession、文件 SHA-256 与注释版本。联网路径优先使用 NCBI Datasets 官方命令 `datasets download genome accession {GCF_or_GCA} --include genome,gff3` 下载指定组装；数据包自带 `assembly_data_report.jsonl`、`dataset_catalog.json` 与 `md5sum.txt`，不得按物种名静默选择“最新参考组装”。官方接口与包内容见 [NCBI genome data package](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-packages/genome/) 和 [download genome](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/how-tos/genomes/download-genome/)。只需局部坐标时可调用 `GET https://rest.ensembl.org/sequence/region/{species}/{region}`，但必须同时冻结 assembly / coordinate-system version；端点参数见 [Ensembl sequence region](https://rest.ensembl.org/documentation/info/sequence_region)。
  3. 全组装本地枚举 guide 与反向互补序列，PAM 规则由稿件声明的 nuclease 配置驱动。`guide_target_absent_candidate` 仅在完整 primary assembly、序列无未声明 adapter、PAM 已知且两条链均无合法命中时产生；`pam_context_mismatch_candidate` 仅在 protospacer 命中但相邻 PAM 明确不符合时产生；`claimed_locus_mismatch_candidate` 要求唯一合法命中与 GFF3 中声称 gene / transcript 不相交。
  4. 精确多位点命中产 `exact_multimapping_candidate`，保存每个 locus、链、PAM、gene overlap；它只表示 guide 不具“组装级唯一性”，不等于实验必然 off-target。1–3 mismatch、DNA/RNA bulge 和变异单倍型搜索只生成 `off_target_review_candidate`，不得按候选数量自动立 finding。NCBI BLAST 仅作跨库候选补充：`POST https://blast.ncbi.nlm.nih.gov/Blast.cgi` 以 `CMD=Put&PROGRAM=blastn&DATABASE=core_nt&SHORT_QUERY_ADJUST=true` 提交，随后以 RID + `CMD=Get&FORMAT_TYPE=JSON2` 获取结果；官方 [Common URL API](https://blast.ncbi.nlm.nih.gov/doc/blast-help/urlapi.html) 明确了 Put/Get、RID 和 JSON2。BLAST 的截断 hit list 不得替代完整组装的穷尽枚举。
  5. base editor 只在稿件给出 editor、strand 与 editing window 时检查目标碱基是否落窗、参考碱基是否相容，产 `edit_window_mismatch_candidate`。prime editing、大片段重排、染色体结构变异和个体单倍型 off-target 留二期，因为它们需要 pegRNA / nicking guide / donor 与更复杂的等位基因模型。
  6. X1 将组装元数据登记为 `external` evidence：assertion 至少含 `assembly_accession`、`assembly_name`、`taxid`、`annotation_release`、`sequence_file_sha256`、`annotation_file_sha256` 与响应字段路径；比较写入 `external_check`，同时引用 guide 的稿件 `present` evidence。要路由 M3，必须把 `extraction_signal.schema.json` 和 `00-contracts.md §6.2` 当前的 X1 消费者集合从 `M2/M4/M6/M7` 扩为 `M2/M3/M4/M6/M7`；这只是扩展合法消费者，不改变三类记录。
- **代价**：3–4 人日；参考下载/缓存 0.5 人日，双链/PAM/注释闭合 1–1.5 人日，base-edit 窗口 0.5 人日，15–20 个困难 fixture 与 X1/M3 接线 1–1.5 人日。人类完整组装可在 2 核 / 4 GB / 12 小时内用 seed index 分块扫描；缓存不得进入提交包。
- **建议优先级**：P1 应该做；先交“唯一 on-target + PAM + gene overlap”，模糊 off-target 只在 precision 门禁通过后启用。
- **阶段 / 归属**：一期离线核心可用用户 FASTA/GFF3；一期联网增强由 X1 取得版本化参考。M1 只抽取，X1 / 工具只产 signal，M3 判构建设计，M7 只判断核心 claim 是否依赖该构建。prime editing 深度审计为二期。
- **契约字段**：扩展 `structured_result.genome_editing_reagents[]`；`external_check.manuscript_value/external_value` 已能保存比较值，建议再增可选 `comparison_context:{assembly_accession,species_taxid,nuclease,pam_rule,reference_hash}` 以机械校验可比性。扩 X1 的 `routed_to` 白名单以允许 M3；不新增记录类型，不让 M1 产 finding。
- **假阳性**：中高。Cas 变体、非标准 PAM、5' G、载体 adapter、样本变异、替代组装、杂合位点和 CRISPRi/a 的有效窗口都会改变解释；任一上下文不全即 `not_comparable` 或 `partial_extraction`。多位点与近似 off-target 固定交人工；只有完整版本化组装上的 target/PAM/locus 硬冲突才允许 M3 考虑 finding。

### P2 · Reactome 过度富集分析的版本化复算与“背景集”门禁

- **问题**：组学论文常把一张 DEG / protein list 送入 pathway enrichment 后直接把富集条目写成机制结论。当前 M4 能复算局部 p / CI，却不能核对输入标识符、物种投影、背景 universe、数据库 release、命中数、原始 p 与 FDR 是否闭合。仅凭 pathway 名称做语义评价会漏掉“把全部检测到的基因误换成全基因组背景”“小鼠列表默认投影到人”“上调/下调列表混用”等高发错误。
- **影响**：富集结果对 universe、ID mapping、数据库版本和多重校正极敏感；相同 gene list 在不同设置下可以得到完全不同的显著通路。裸模型既无法重跑完整列表，也无法追踪 `identifiersNotFound` 与 release，容易把不可复现的 pathway narrative 当作独立生物学证据。
- **方案**：**一期联网增强 + 可录制离线回归，M1 / X1 / M4 / M7。** 新增 `scripts/pathway_enrichment_audit.py`，首版只支持 over-representation analysis（ORA），不把 ranked GSEA、ssGSEA 或拓扑分析压成同一算法。
  1. M1 新增 `enrichment_analyses[]`：`{analysis_id,experiment_id,method,input_identifier_namespace,input_entity_refs[],input_selection_rule,direction_policy,species_taxid,background_mode,background_entity_refs[],pathway_database,pathway_database_version,multiple_testing_method,reported_pathways[],evidence_refs[]}`；每个 `reported_pathway` 保存 stable ID（若报告）、名称、hits、set size、p、adjusted p 与 evidence。正文只给“top genes”而非完整输入列表时标 `partial_extraction`，禁止复算。
  2. connector=`reactome_analysis`。稿件明确使用 Reactome 默认 ORA 且为人类标识符时，`POST https://reactome.org/AnalysisService/identifiers?pageSize={n}&page=1`，body 为一列带 `#Genes` header 的标识符；只有稿件明确做跨物种 human projection 时才调用 `/identifiers/projection`。Reactome 官方说明 `/projection` 会把非人标识符映射到人，且结果提供 `pathwaysFound`、`identifiersNotFound`、`summary.type`、pathway stable ID、species、entities coverage、`pValue` 与 `fdr`，见 [Analysis Service](https://reactome.org/dev/analysis)。数据库 release 另取 `GET https://reactome.org/ContentService/data/database/version`，见 [Content Service](https://reactome.org/dev/content-service)。
  3. external assertions 固定为 `analysis_type`、`database_release`、`identifiers_not_found`、`pathway_stable_id`、`pathway_species`、`entities_found`、`entities_total`、`p_value`、`fdr`，每项保留响应字段路径。`summary.token` 可作 `record_id`，但 Reactome 只保证 token 七天可取；可审计事实必须保存在 assertions + response hash 中，报告不得依赖 token 长期存活。
  4. 只有以下键全部相同才允许 `enrichment_result_mismatch_candidate`：输入列表 hash、identifier namespace、物种、是否 projection、ORA、background mode、Reactome release、方向拆分策略、multiple-testing family 与 pathway stable ID。Reactome公开 service 的默认 universe 与稿件自定义 universe 不同，不能强行比较；稿件使用自定义 background 时，工具仅在背景列表与同 release pathway membership 均可得时用 `scipy.stats.hypergeom` 本地复算，否则 `not_comparable`。
  5. 单独产三类高确定性候选：`identifier_loss_candidate`（未映射比例及具体 ids 与稿件声称不符）、`species_projection_mismatch_candidate`（稿件称物种内分析但实际只能通过 projection 重现）、`enrichment_arithmetic_mismatch_candidate`（同 universe / hit / set-size 下超几何 p 或声明的校正值不闭合）。当前 release 找不到旧论文通路、pathway 名称相似或 FDR 阈值附近变化只进人工。
  6. M4 只对统计闭合立 finding；M7 仅在稿件把该通路作为核心机制证据、且不是由独立实验支撑时评估 `unsupported_claim` / scope overreach。数据库给出显著通路不等于因果机制成立，外部重现成功也不能作为“证明 pathway 被激活”的 finding 反向证据。
- **代价**：2.5–3.5 人日；M1 完整列表抽取 0.5–1 人日，Reactome connector 0.5 人日，本地 hypergeometric 与舍入/校正 0.5–1 人日，版本/背景/物种困难反例 1 人日。至少需要 8 个 fixture：custom universe、mouse projection、ID 丢失、上下调混合、旧 release、同名不同 stId、FDR 边界、API 失败。
- **建议优先级**：P1 应该做；在 Round 12 resolver 与一个实际 connector 跑通后，这是比“查询 pathway 是否存在”更有 uplift 的第二个垂直切片。
- **阶段 / 归属**：一期联网增强；X1 取 Reactome 当前事实，M4 复算统计，M7 审核机制结论。离线只在用户提供带版本的 gene-set membership / 录制响应时复算；GSEA permutation、single-cell pseudobulk 与多组学联合通路模型为二期。
- **契约字段**：扩展 `structured_result.enrichment_analyses[]`；复用 `external` evidence 与 `external_validation_candidate`。`comparison_context` 增 `input_sha256/background_sha256/database_release/species_taxid/projection/method/correction_family` 即可，无需重构 finding。
- **假阳性**：高。universe、ID 映射、物种、release、方向、ORA/GSEA 与校正 family 任一不同都停止比较。数据库当前零命中为 `not_addressed`；旧版本不可得或 API 失败只产 X1 `system_limitation`。任何“富集支持机制”的表述必须降级为关联性证据并由人工复核。

### P3 · Ensembl Compara 一对一 / 一对多同源关系与跨物种外推审计

- **问题**：M7 已有 species scope overreach，Round 12 P4 也提了基因符号与物种身份，但二者都没有回答“论文在鼠 / 斑马鱼 / 果蝇中操作的基因，是否真是其声称的人类基因一对一直系同源物”。基因家族复制后常出现 one-to-many / many-to-many；把最相似 paralog、同名基因或一个鱼类 duplicate 直接写成“the human ortholog”会使跨物种机制链过度收窄。
- **影响**：符号拼写正确不等于正交关系正确；一对多关系中只操作一个 paralog，也不能无条件外推整个哺乳动物基因功能。裸模型通常只记住常见同源基因，无法稳定处理 Ensembl stable ID、物种 division、gene-tree duplication 与 release。
- **方案**：**一期联网增强，M1 / X1 / M2 / M7。** 新增 `orthology_claim` query，不另建基因身份 connector。
  1. M1 新增 `cross_species_gene_claims[]`：`{claim_id,source_species_taxid,source_gene_symbol,source_gene_id,target_species_taxid,target_gene_symbol,target_gene_id,claimed_relation,claimed_functional_equivalence,experimental_scope,evidence_refs[]}`；`claimed_relation` 仅 `ortholog_one2one/ortholog_one2many/ortholog_many2many/paralog/unspecified`。稳定 ID 缺失时先复用 Round 12 的 gene identity lookup；候选不唯一则停止。
  2. 精确 stable ID 优先调用 `GET https://rest.ensembl.org/homology/id/{species}/{id}?type=orthologues;target_species={target};format=condensed;sequence=none`；仅有批准 symbol 时调用 `GET /homology/symbol/{species}/{symbol}`，参数同上。官方端点允许 `target_species` / `target_taxon`、`type=orthologues|paralogues|projections|all` 与 `format=full|condensed`，见 [Ensembl homology by symbol](https://rest.ensembl.org/documentation/info/homology_symbol)。release 取 `GET https://rest.ensembl.org/info/data`，该端点可能返回多个可用 release，必须原样保存而非猜单值，见 [Ensembl info/data](https://rest.ensembl.org/documentation/info/data)。
  3. external assertions 保存 source/target stable ID、species、homology type、taxonomy level，以及响应实际提供的 identity / positivity / dN / dS 字段；缺失字段保持 null。Ensembl gene tree 能表达 one-to-many 和 many-to-many，并用 gene tree 与 species tree reconciliation 区分 orthologue / paralogue，方法边界见 [Ensembl protein trees](https://www.ensembl.org/info/docs/compara/homology_method.html)。
  4. `orthology_identity_mismatch_candidate` 只用于稿件明确给出 source + target stable ID 和一对一关系，而同一 Ensembl release 的完整响应把两者分类为 paralogue，或返回一对多 / 多对多且稿件明确声称唯一一对一。数据库只返回其他 ortholog、无结果、symbol 候选不唯一、跨 Ensembl division 或 stable ID 已归档时统一 `needs_manual_review` / `not_addressed`，不得 mismatch。
  5. `orthology_scope_review_candidate` 保存未被实验覆盖的同源分支与 sequence identity，但固定 `comparison_result=needs_manual_review`。M7 只有在稿件把一个物种、一个 paralog 的结果扩成跨物种功能等价，且内部证据链没有人类或第二物种验证时，才能结合稿件证据立 scope finding。M2 只处理命名 / 指代矛盾，不评价功能保守性。
- **代价**：2–3 人日；复用 gene identity connector 后，API/parser 0.5 人日，claim 对齐 0.5 人日，gene family / teleost duplication / archived ID / cross-division fixtures 1–2 人日。
- **建议优先级**：P2 二期做，或在 preclinical / model-organism 语料占官方任务较高时提前为 P1；优先级低于可直接打断实验构建的 P1 和可复算统计的 P2。
- **阶段 / 归属**：一期联网增强能力可以完成，但建议排在首批 connector 之后；X1 取同源事实，M2 判实体指代，M7 判跨物种 scope。自动“功能等价评分”、祖先序列重建与系统发育树重算为二期。
- **契约字段**：扩展 `structured_result.cross_species_gene_claims[]`；复用 external assertions 与 signal。`comparison_context` 增 `source_taxid/target_taxid/source_gene_id/target_gene_id/ensembl_release/compara_division`，不新增第四类记录。
- **假阳性**：高。orthology 是进化关系，不等于功能等价；one-to-one 也不能证明表型保守。不同 orthology 算法 / release 可能给出不同关系，因此身份 mismatch 的 `review_confidence` 最高为 `medium`，所有功能性判断必须交人工；无数据库记录绝不作为反证。

## 未解决 / 需要人来定的问题

1. Round 12 P1 的 `external_evidence_resolver.py` 与 connector manifest 仍未实现。建议先完成唯一 resolver 和既定首个 connector，再实现本轮组件；否则三项只能继续停留在文档层，无法贡献 uplift。
2. 是否批准 X1 signal 路由 M3。当前 schema 与 `00-contracts.md` 明确排除 M3，但 CRISPR、Cellosaurus、RRID 与试剂身份的自然消费者都是 M3；建议扩为 `M2/M3/M4/M6/M7`，仍禁止 X1 产 finding。此项需 M3 负责人确认，本轮未修改其文件。
3. 分期口径存在文本冲突：本轮任务末尾写“一期 = 不调用外部数据库”，但评测环境章节明确推翻旧边界并要求“离线保底 + 一期可选外部增强”。本提案按后者使用“一期离线核心 / 一期联网增强”；若团队仍把联网统一称二期，需一次性改名，不能改变已落地的失败降级契约。
4. Reactome 当前 service 不等于论文所用历史 release，也不支持把任意自定义 background 偷换成默认 universe。若不能冻结同 release gene-set membership，报告只能显示“当前版本复跑差异”，不得写“原分析错误”。
5. `rest.ensembl.org` 与 `reactome.org` 需要加入白名单；NCBI Datasets 与 BLAST 需要 `api.ncbi.nlm.nih.gov`、`blast.ncbi.nlm.nih.gov`。拒绝访问、429、5xx 与响应漂移必须沿用现有 X1 `system_limitation`，不得自动切换未登记镜像。
6. 已有提案状态：Round 4 P1 / Round 12 A 类的 X1 evidence、signal、stage 与降级契约已采纳；Round 11 P4 的 primer/参考序列方向和 Round 12 P4 的 gene identity connector 尚未实现。本轮 P1 是在同一序列工具上新增 CRISPR 垂直切片，P3 复用 gene identity 结果，不建立平行 resolver。
