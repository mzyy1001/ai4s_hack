# Round 21 · 外部数据源与新功能组件 提案

## 摘要

M3 仍把 Cellosaurus / ICLAC / RRID 写成“二期”，与现行“离线保底 + 一期可选 X1”口径冲突；本轮已修成 connector 就绪度边界。
Round 4 / 12 的 X1 三型证据、失败降级和双证据规则已经采纳，但唯一 resolver 与任一真实 connector 仍未实现；继续罗列 ClinicalTrials.gov、UniProt、Cellosaurus、ChEMBL 等既有方向不会增加 uplift。
本轮筛出 PDB 实验结构质量、ncRNA/miRNA 试剂身份、MGI 小鼠 allele/Cre driver 三个未被既有提案覆盖的窄切片，但 Qwen 探针因沙箱禁止网络而全部 `INCONCLUSIVE`，因此三项仅保留为候选设计，**探针有效重跑前不得实现或进入默认流程**。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/references/03-experimental-methods.md` | §9.5、§11 | 把“细胞系外部核验属二期”改为“X1 connector 未实现/未运行时降级”；把“二期扩展”改为“一期联网增强候选”；同步 RRID “未列应用≠无特异性”，并删除“参数偏离即 minor finding”的自相矛盾分支 | 旧分期来自无网络假设；Antibody Registry 沉默不是有效性反证，常规分布 outlier 也不是稿件错误。修改不批准 X1→M3 路由或新增 connector |
| `tools/probe_cases/round21_pdb_record_mismatch.md` | 新文件 | 增加 PDB method / resolution 错配最小案例 | 为 P1 提供不泄露数据库真值的裸模型探针 |
| `tools/probe_cases/round21_mirna_sequence_mismatch.md` | 新文件 | 增加 miRNA 名称—成熟链序列错配最小案例 | 为 P2 提供裸模型探针 |
| `tools/probe_cases/round21_mouse_allele_mismatch.md` | 新文件 | 增加 MGI allele ID—Cre driver 错配最小案例 | 为 P3 提供裸模型探针 |

## 基线探针结果

| 候选 | 案例 | `qwen3.8-max × 3` | 结论 | 本轮行动 |
| --- | --- | --- | --- | --- |
| PDB 条目与实验质量对账 | `round21_pdb_record_mismatch.md` | 0 个有效样本；3 次均为 `urlopen: [Errno 1] Operation not permitted` | `INCONCLUSIVE` | 不实现、不宣称 baseline miss；保留候选设计，修复网络后原命令重跑 |
| ncRNA / miRNA 试剂身份 | `round21_mirna_sequence_mismatch.md` | 0 个有效样本；3 次均为同一 socket 拒绝 | `INCONCLUSIVE` | 同上 |
| MGI allele / Cre driver 身份 | `round21_mouse_allele_mismatch.md` | 0 个有效样本；3 次均为同一 socket 拒绝 | `INCONCLUSIVE` | 同上 |

调用已进入 `baseline_probe.py`，凭据可读取；失败发生在沙箱网络层，不是 Qwen 返回错误。
不得把 `0/0` 写成“裸模型完全查不出”。恢复 DashScope 出站访问后，必须原样重跑：

```bash
python3 tools/baseline_probe.py --case tools/probe_cases/round21_pdb_record_mismatch.md \
  --error "PDB 9BEI 的权威记录是 4.16 Å electron microscopy 结构，不是稿件声称的 2.10 Å X-ray crystallography；该分辨率也不足以据此直接指认侧链氢键。" --repeats 3
python3 tools/baseline_probe.py --case tools/probe_cases/round21_mirna_sequence_mismatch.md \
  --error "稿件标为 hsa-miR-21-5p 的 22 nt mimic 序列 CAAGCUCGUGUCUGUGGGUCCG 实际对应 hsa-miR-99b-3p；hsa-miR-21-5p 的成熟序列不是该序列。" --repeats 3
python3 tools/baseline_probe.py --case tools/probe_cases/round21_mouse_allele_mismatch.md \
  --error "MGI:7520935 对应 1600020E01Rik 的 gene-trap Cre/ERT2 allele，不是 Alb-CreERT2；稿件的 allele ID 与所称 driver 身份不一致。" --repeats 3
```

只有 `BASELINE_UNRELIABLE` / `BASELINE_MISSES_IT` 才允许把对应组件转入实现；
`BASELINE_FINDS_IT` 必须移入“已探针，放弃”，不得用更长 prompt 包装成新能力。

## B 类提案

以下三项是**被基线门禁阻断的候选设计**，不是已批准 backlog。技术细化只用于探针转为有效结果后快速拍板，不构成实现授权。

### P1 · PDB 条目—实验方法—验证报告闭合审计

- **问题**：Round 11 P5 只提过 UniProt 位点、InterPro 区间和 PDB 是否覆盖残基，没有核对稿件对其自有 PDB 条目的 method、resolution、entry revision、实体组成、配体和 wwPDB validation 指标。结构论文中把 cryo-EM 写成 X-ray、把 4.16 Å 写成 2.10 Å、把不同 revision 的模型混用，属于可确定性元数据错误；“该分辨率能否支持某条侧链氢键”则不能由单一 Å 阈值自动裁决。
- **影响**：method / resolution / entry 身份硬错会破坏结构证据链，局部几何主张若未回到 map / density 与 validation outlier 又会产生虚假精确性。裸模型无法可靠记住新近 PDB 条目及 revision；但本轮探针无有效样本，尚不能证明 uplift。
- **方案**：**一期联网增强可做；离线接受用户提供的 mmCIF + validation XML，二期才做 map-level 局部重拟合。归属 X1 + M3/M7，不新增审核模块。** 复用 Round 12 的唯一 resolver，connector=`pdb_deposition_validation`：
  1. M1 抽取 `structure_claims[]:{claim_id,pdb_id,claimed_method,claimed_resolution,claimed_entities[],claimed_ligands[],claimed_revision_or_date,claimed_local_feature,chain_or_residue_refs[],evidence_refs[]}`。未给 PDB ID 时不做名称搜索，不从图片猜 accession。
  2. 精确条目先调 RCSB Data API `GET https://data.rcsb.org/rest/v1/core/entry/{pdb_id}`；按 `rcsb_entry_container_identifiers` 再取 `/polymer_entity/{pdb_id}/{entity_id}`、`/nonpolymer_entity/{pdb_id}/{entity_id}`。登记 `struct.title`、`exptl[].method`、`rcsb_entry_info.resolution_combined`、初次发布日期、revision 日期、实体/链/来源物种、配体 CCD ID 与主引文。RCSB REST 层对未知条目返回 404，接口层级与错误语义见 [RCSB Data API](https://data.rcsb.org/index.html)。
  3. validation 数据只用官方 wwPDB/PDBe 产物：经 [PDBe Download API](https://www.ebi.ac.uk/pdbe/download/api/docs) 取得 `validation-data` XML/mmCIF 和 validation report，保存文件 SHA-256、PDB revision 与 parser version。首版只抽全局/链级事实，如 clashscore、Ramachandran/side-chain outlier、reported resolution、EM map-model fit 摘要；不得用“percentile 低”自动判结构错误。
  4. `external` evidence 每个 assertion 保存一个原子事实与 `source_path`，例如 `experimental_method`、`reported_resolution`、`initial_release_date`、`revision_date`、`polymer_entity_identity`、`ligand_ccd_id`、`validation_metric`。`external_check` 同时引用稿件 `present` 与 X1 `external`；只有 method、同 revision resolution、PDB ID/实体/配体的精确冲突可设 `comparison_result=mismatch`。
  5. M3 只判断构建体/配体/实验方法身份；M7 只在核心结构 claim 依赖该错误时立 finding。局部氢键、侧链 rotamer、配体 pose 或界面机制一律 `needs_manual_review`，必须查看对应 map/density、occupancy、B factor、局部分辨率与 validation outlier；不得设统一 resolution cutoff。
- **代价**：探针转有效且通过后 2–3 人日完成 entry/entity/validation 垂直切片，另需 1–2 人日做 X-ray/cryo-EM/NMR、entry revision、无公开条目、低分辨率但合理主张等 15 个困难 fixture。map coefficients / EM half maps 下载与局部复核再需 3–5 人日，列为二期。
- **建议优先级**：**未定；P0 仅指先恢复基线探针并重跑。** 若结果为 `MISSES/UNRELIABLE`，建议组件 P1；若 `FINDS_IT`，放弃默认组件，只保留人工查询说明。
- **契约字段**：可扩展 `structured_result.structure_claims[]` 与 `external_check.comparison_context:{pdb_id,entry_revision,method,entity_id,chain_id,residue_numbering_basis}`；复用既有 `external_validation_candidate`，不新增 signal 顶层类型、不改 finding 基础形状。X1 若需路由 M3，必须先解决当前 schema 只允许 M2/M4/M6/M7 的待拍板项。
- **证据映射**：稿件声明由 M1 建 `present` evidence；RCSB/PDBe 响应由 X1 建 `external` evidence；signal 的 refs 恰好覆盖两组证据。任何 M3/M7 finding 仍以稿件 `present` 为首锚点，并同时引用 `retrieval_status=resolved` 的 external 条目。
- **假阳性**：method / 同 revision resolution 精确不等风险低；结构解释风险很高。PDB 当前 revision 可能晚于论文，author numbering、label numbering、biological assembly、asymmetric unit、局部分辨率和 remediated coordinates 不可混比。无公开记录可能是 embargo，只能 `not_found` + 人工；API/下载失败只产 X1 `system_limitation`。

### P2 · miRBase / RNAcentral 驱动的 ncRNA 试剂身份与成熟链审计

- **问题**：现有 `sequence_identifier_audit.py` 能查字母表、HGVS 子集与给定完整参考上的位点，却不理解 `MI` precursor accession、`MIMAT` mature accession、`5p/3p` arm、物种前缀和数据库 release。论文把 hsa-miR-21-5p 名称配上 hsa-miR-99b-3p 序列、用 precursor 序列冒充 mature mimic、或把同一保守序列仅凭序列断言成人源，都会使 knockdown/rescue 的分子身份不成立。
- **影响**：miRNA mimic / inhibitor 身份错会使整条靶基因机制链失效；通用模型可能记住少数热门 miRNA，但无法穷尽 mature.fa、dead entries、release diff 与跨物种同序列。当前探针仍为 `INCONCLUSIVE`，不能声称已经证明基线漏检。
- **方案**：**一期离线核心可消费冻结的 miRBase 包，一期联网增强负责获取与更新；归属 M1 / X1 / M3 / M7。** connector=`ncrna_identity`：
  1. M1 新增 `ncrna_reagents[]:{reagent_id,ncrna_class,reported_name,external_accession,species_taxid,sequence,sequence_role,arm,declared_overhang_or_tail,evidence_refs[]}`；`sequence_role` 固定 `mature/precursor/guide/passenger/unknown`。不从长度猜 mature，也不把 `miR-21` 自动补成 `5p`。
  2. 有 miRBase accession 时调 RNAcentral `GET https://rnacentral.org/api/v1/rna/?external_id={accession}&flat=true`；API 可按 expert-database external ID 过滤，并返回 URS、sequence、length 与 xrefs，见 [RNAcentral API v1](https://rnacentral.org/api)。物种比较必须使用 `URS.../{taxid}` 语义；同一 URS 可存在多个物种，序列相同不能证明来源物种。
  3. 版本化事实以 miRBase `CURRENT/mature.fa`、`hairpin.fa`、`miRNA.dat`、`miRNA.dead`、`miRNA.diff` 为准；当前下载页同时保留 previous releases，见 [miRBase downloads](https://www.mirbase.org/download/)。下载后记录 release、文件 SHA-256 和获取时间，在本地建立 `MIMAT/MI/name/species/arm/sequence/status` 索引；runtime cache 不进入提交包。
  4. 只对论文明确给出的三元组做确定性检查：`accession↔name`、`accession↔mature/precursor role`、`accession/name↔sequence`。先把 DNA `T` 规范化为 RNA `U`；仅移除稿件明确标注的 overhang、adapter 或化学修饰。序列恰好映射到另一个 accession 时输出该候选集，多个 taxon/多个名字命中不得自动选一个。
  5. assertions 保存 `rnacentral_id`、miRBase accession/name、taxid、arm、sequence、length、entry status、release 与 xref source path。X1 仍只产 `external_validation_candidate`；M3 判断试剂身份，M7 仅在核心 rescue/target claim 依赖错误 reagent 时评估影响。
- **代价**：探针通过后 2–3 人日；索引/缓存 0.5 人日，M1 对象与精确比对 0.5–1 人日，precursor/mature、5p/3p、U/T、同序列跨物种、dead entry、带 overhang 的 20 个 fixture 1 人日。靶基因预测与 seed-site 功能判断不纳入首版。
- **建议优先级**：**未定；P0 先重跑探针。** 通过 uplift 门禁后建议 P1，因为本地 exact lookup 成本低；若裸模型 2/3 以上稳定命中，则放弃默认 connector。
- **契约字段**：扩展 `structured_result.ncrna_reagents[]` 和 `external_check.comparison_context:{database_release,species_taxid,sequence_role,arm,normalization_steps[]}`；复用 generic external assertions / signal。finding 可在 M3 增 slug `ncrna_reagent_identity_mismatch`，但不需要新记录类型。X1→M3 路由仍需人批准。
- **证据映射**：M1 的名称、accession、序列分别定位到稿件 `present` evidence；X1 每个数据库原子事实写 external assertion。没有稿件序列时不得仅因数据库给出序列立 finding；数据库沉默不构成反证。
- **假阳性**：中。pre-miRNA/mature miRNA、5p/3p、isomiR、非模板尾、mimic passenger strand、同序列跨物种与旧 release 都可造成表面冲突。只有 release、accession、role 和声明修饰完整时才允许 mismatch；isomiR 或多命中固定 `needs_manual_review`。不得用数据库身份匹配反向证明该 mimic 在细胞内特异或确实命中靶基因。

### P3 · MGI allele—基因—遗传背景—Cre driver 身份审计

- **问题**：M3 目前只检查“是否报告品系/来源/随机化”等文字要素。小鼠论文常把 stock、strain、allele、genotype 四层混写：MGI allele ID 可能对应另一个基因，`flox` 与 null allele 可能混用，Cre driver 的正式 allele 与俗名不一致，C57BL/6J、C57BL/6N 和混合背景又不能互换。Round 19 的 gene identity / orthology 不覆盖 allele 与遗传背景。
- **影响**：错误 allele 或 driver 会让组织特异 knockout 的实验单位从根上失效；背景亚系错写会影响代谢、免疫和神经表型解释。裸模型能提醒“应验证 Cre specificity”，但未必能把一个新 MGI ID 解析到正式 allele；本轮 0 个有效探针样本，尚不能据此主张 uplift。
- **方案**：**一期联网增强下载权威 MGI 报表并本地精确索引；离线可读用户提供的同版快照。首版归属 M1 / X1 / M3 / M7，复杂组织重组效率与表型因果留二期。** connector=`mgi_mouse_model_identity`：
  1. M1 新增 `model_organism_reagents[]:{model_id,species_taxid,reported_strain,stock_id,allele_ids[],allele_symbols[],target_genes[],zygosity,cre_driver,claimed_target_tissues[],induction_regimen,reported_background,evidence_refs[]}`。stock ID、MGI allele ID 与 genotype ID 分字段保存，禁止塞进一个自由文本 accession。
  2. 从 MGI [Data and Statistical Reports](https://www.informatics.jax.org/downloads/reports/index.html) 获取并 hash：`MGI_PhenotypicAllele.rpt`（allele ID、symbol、name、type、gene/marker）、`MGI_Strain.rpt` 与 `MGI_Nonstandard_Strain.rpt`（正式/非标准 strain nomenclature）、`MGI_Recombinase_Full.rpt`（driver、allele、detected/absent tissue、IMSR strain）。只有论文给 genotype ID 且需要背景闭合时才加载 `MGI_PhenoGenoMP.rpt`；大报表保存在 runtime cache，不进入 50 MB 提交包。
  3. 确定性比较限于：精确 `MGI:<digits>` 是否映射到稿件所称 allele symbol / target gene / allele type；正式 strain 字符串是否与所引 MGI strain ID 一致；论文给出的 Cre allele ID 是否对应所称 driver。俗名搜索、多候选 stock、只有 gene 名无 allele ID 时不得自动绑定。
  4. `detected in/absent in` 只生成 `cre_tissue_scope_review_candidate`：MGI 的组织注释不是本实验的重组效率测量，也不是穷尽阴性。只有 allele 身份硬冲突可设 `mismatch`；组织特异性、leakiness、induction efficiency 和 developmental timing 固定交人工，并要求稿件内 reporter / recombination evidence。
  5. assertions 保存 MGI release/update date、file hash、row key、allele ID/symbol/type、marker ID/symbol、strain ID/name、Cre tissue annotation 与来源列。M3 回查模型构建，M7 只判断核心组织特异 claim 是否完全依赖错配模型。
- **代价**：探针通过后 2.5–3.5 人日；下载/增量 hash 和索引 0.5–1 人日，M1 对象与 exact-ID 对账 1 人日，allele/stock/genotype 混淆、B6J/B6N、CreERT2、混合背景、非标准 strain、无 ID 多候选等 20 个 fixture 1–1.5 人日。
- **建议优先级**：**未定；P0 先恢复探针。** 若基线漏检/不稳定，建议 P1，优先 exact allele→gene/type/driver 三元组；背景和组织表达为后续人工候选。若基线稳定指出 exact ID 错配，则不实现默认组件。
- **契约字段**：扩展 `structured_result.model_organism_reagents[]`；`external_check.comparison_context` 增 `species_taxid,mgi_release,identifier_kind,allele_id,strain_id,genotype_id`。复用 `external_validation_candidate`；M3 可增 slug `animal_model_identity_mismatch`，不改变 finding schema。该组件同样依赖批准 X1 signal 路由 M3。
- **证据映射**：稿件中 allele/strain/driver 声明必须各有 `present` evidence；X1 assertion 指向具体报表行与 file hash。finding 以稿件证据为首锚点，同时引用 external evidence；只给俗名、无精确 ID 或外部报表无记录时不得立 finding。
- **假阳性**：allele ID 精确指向另一基因的风险低；背景/Cre scope 风险高。回交代数、亚系、母系效应、嵌合 founder、诱导时点、reporter 灵敏度和本实验重组验证都可能改变解释。MGI “absent in” 不能替代本实验阴性，`not_found` 不能证明模型不存在，网络/报表漂移只产 X1 limitation。

## 已探针，放弃

本轮没有候选得到 `BASELINE_FINDS_IT`，因此没有可据实放弃的组件。三项均为
`INCONCLUSIVE`，不得把它们列为“已证明有 uplift”，也不得把连接失败当作模型漏检。

## 未解决 / 需要人来定的问题

1. **先恢复 Qwen 探针出站访问。** 这是三项候选进入实现队列的硬门；当前环境对 DashScope socket 返回 `Operation not permitted`。有效样本仍为 0 时不得拍组件优先级。
2. **先实现 Round 12 P1 的唯一 `external_evidence_resolver.py`。** 当前只有 X1 schema，没有 resolver / manifest / connector。即使探针通过，P1–P3 也不得各自实现网络、缓存、错误分类和 evidence id。
3. **是否批准 X1 signal 路由 M3。** 当前 `00-contracts.md §6.2` 与 schema 明确只允许 M2/M4/M6/M7，但 PDB 构建体、miRNA reagent、小鼠 allele 的自然消费者都是 M3。本轮未修改契约；建议一次性扩为 `M2/M3/M4/M6/M7`，仍禁止 X1 产 finding。
4. **分期术语统一。** 本轮按最新环境口径使用“一期离线保底 / 一期联网增强”；若团队仍坚持“一期 = 绝不访问数据库”，则 P1–P3 的在线获取统一改名二期，但不应改变它们在 12 小时沙箱中的技术可行性或失败降级规则。
5. **PDB 提案与 Round 11 P5 的边界。** Round 11 P5 负责 protein residue / domain / structure coverage；P1 只扩同一 connector 的 deposition method、revision、entity/ligand 与 validation facts，不建立平行 PDB resolver。
6. **提交包大小。** miRBase / MGI 快照、wwPDB validation 文件和原始响应只能进 runtime cache；仓内只放 manifest、parser 与小型脱敏 fixtures，任何单文件仍按 10 MB 门禁。
7. **既有提案状态。** Round 4 P1 / Round 12 A 类的 `external` evidence、X1 stage、双证据与失败降级已采纳；Round 12 P1 resolver、ClinicalTrials.gov / Europe PMC / NCBI / UniProt 等 connector 仍未实现。Round 19 已覆盖 CRISPR、Reactome 与 orthology，本轮没有重复提出。
