# Round 11 · 图像与结构层面的硬核取证 提案

## 摘要

Round 1 P7 的最小图像候选器与 Round 3 P4 的部分序列审计已经实现，但当前图像算法只覆盖网格对齐原样复制，序列算法此前还会把未版本化片段误当完整参考；本轮先修复后者及 signal id 契约断裂。
图像取证下一步不应只“加一个相似度”，而应交付可回映原图的几何证据包、旋转/镜像/缩放验证与 blot 专属前置条件；所有结果仍是候选，绝不能自动写成“造假”或“学术不端”。
按新评测环境，UniProt/InterPro/AlphaFold DB、HGNC/Ensembl、PubChem/ChEMBL 可进入一期可选联网增强，但必须依赖 Round 4 P1 的统一 X1 契约，网络失败只产 `system_limitation`，数据库未注释也不是稿件反证。

本文把“一期”拆成 **一期离线**（不调用外部数据库，必须完整可跑）与 **一期联网增强**（白名单可用时执行）；二期只保留原始大数据重算、复杂结构模拟等超出初筛交付面的能力。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/scripts/figure_integrity_audit.py` | signal / limitation 构造、自检、目录扫描 | 将非法 `SIG-IMG*` / `SYS-IMG` 改为契约接受的数字 id；汇总入口统一重编号；自检增加 id pattern；扫描补 TIFF；文档改为真实的“精确 dHash 分桶” | 原脚本自检通过但产物无法通过 `^SIG-[0-9]{3,}$` / `^SYS-[0-9]{3,}$`；`HAMMING_MAX` 从未被执行，文档却声称近邻哈希粗筛 |
| `tools/validate_schemas.py` | 工具产物契约检查 | 增加实际工具 signal id pattern 门禁 | 旧门禁只查必填字段、type、producer 与 severity，漏掉了会让正式 schema 拒收的 id |
| `skills/biomed-paper-review/scripts/sequence_identifier_audit.py` | `check_hgvs()`、自检 | 位点越界/参考残基核对强制要求 `reference_id + reference_version + sequence_complete=true`；缺上下文改产 `partial_extraction`；`n./m./r./o.` 未覆盖表达式改为 `hgvs_syntax_unresolved` 候选；蛋白位置 0 改判语法违规 | 任意蛋白片段都能被旧代码当完整序列，造成确定性假阳性；合法但未支持的 HGVS 前缀也被错误描述成“缺前缀”；旧代码会把第 0 位索引到 Python 序列末位 |
| `skills/biomed-paper-review/schemas/extraction_signal.schema.json` | `sequence_audit.check` | 增加 `reference_context_incomplete` | 让上述 fail-closed 路径可机器校验，不把输入不足伪装成序列不一致 |
| `skills/biomed-paper-review/references/00-contracts.md` | §6.2 | 补上十三值表中遗漏的 `figure_integrity_candidate` 行；写明蛋白坐标检查的完整序列/accession/版本前提 | 标题声称十三值但表中只有十二行；旧文字没有封住片段误判路径 |
| `skills/biomed-paper-review/references/01-structured-extraction.md` | §14 | 收敛为“版本化完整参考序列上的范围/残基检查”，缺上下文只产 `partial_extraction` | M1 文档必须与脚本真实适用前提一致 |
| `skills/biomed-paper-review/SKILL.md` | §0.2、资源索引 | 独立确定性脚本数由四项改为五项；序列脚本说明补充参考上下文降级规则 | 图像脚本已加入 Skill，本体仍使用旧计数和过宽能力声明 |
| `README.md` | 仓库结构、分期范围、当前状态 | 补图像脚本、28 部伦理规范、科学栈依赖和已实现图像边界；删除“四脚本/图像未实现”等过期陈述 | 静态评审可直接用仓库事实证伪旧 README |

## B 类提案

### P1 · 图像取证的坐标血缘与不可定性契约

- **问题**：现有 `image_audit` 保存文件名、块坐标和相关系数，但没有原始资产 hash、解码尺寸、缩放矩阵、候选 polygon 或算法参数快照；`evidence_registry.present` 也只能定位到 figure/panel。若输入在 `MAX_SIDE` 被缩放，当前 bbox 无法可靠回映 PDF 原图。相同 basename 还会在 `audit_figures()` 的字典中静默覆盖。Round 1 P7 提过 bbox，Round 5 P3 提过图值坐标标定，但没有定义图像取证的 chain of custody。
- **影响**：评委无法从 signal 回到被比较的两个像素区域，也无法判断候选来自压缩后的论文图、补充原图还是重复文件；算法升级后结果不可复算。没有可复核候选区域的“相似度 0.98”不是证据链，只是一个数。
- **方案**：**一期离线，P0；Stage 3 产 signal，M5 消费。** 扩展现有 `image_audit`，不新增记录类型：
  1. 每个输入资产保存 `asset_id/source_evidence_ref/sha256/media_type/original_width/original_height/decoded_width/decoded_height/color_mode/decoder_version`；文件身份使用相对路径 + hash，不用 basename。
  2. 每个候选保存 `regions[]:{asset_id,panel_ref,polygon_source_px,polygon_decoded_px}`、`source_to_decoded_transform`、`comparison_transform`、`score_components`、`algorithm_version`、`parameter_profile`、`artifact_preview_ref`。preview 只用于展示，判断始终回到原始像素。
  3. `evidence_refs[]` 必须引用两个来源 panel 的 `present` evidence；同图候选也至少引用该 panel。Stage 3 不创建 finding。M5 人工复核后若立 finding，必须重新引用这些稿件证据，不能只引用 signal id。
  4. schema 把 `image_audit.additionalProperties` 从开放对象迁为按 `check` 条件封闭的 `$defs`；候选恒有 `candidate=true`、`severity_hint=null`、`manual_review_required=true`。任何字段不得命名为 `fraud_probability` 或 `misconduct_score`。
- **代价**：1.5–2 人日；修改 `extraction_signal.schema.json`、`00-contracts.md §6.2`、图像脚本、validator 和 6 个资产身份 fixture。若未来采用 Round 1 P1 的 `observation_registry`，这里只迁移 refs，不重构候选对象。
- **建议优先级**：P0 交付前必须做；它是 P2/P3 的契约前置。
- **输入 / 输出映射**：输入为 Stage 1/3 已定位的原始图、panel bbox 与 `present` evidence ref；输出仍为 `figure_integrity_candidate` signal，细节进入 `image_audit`。不增加 `figure_record` 的第二份候选副本，避免与 signal 漂移。
- **契约字段**：扩展 `image_audit` 与 `present` 图像证据的可选资产元数据；不改 finding 基础形状，不引入第四类记录。
- **假阳性**：本项不判断稿件。**绝不能自动下造假结论**：算法候选无法区分合法对照复用、放大 inset、示意图模板、排版软件重采样与不当复制；“行为意图”更不可能由像素相似度推出。

### P2 · 旋转、镜像、缩放稳健的论文内重复区域检测

- **问题**：已实现脚本是 Round 1 P7 的最小落地，但只对 64×64 网格块做完全相同 dHash 分桶，再以像素相关验证；任意偏移、裁剪、旋转、镜像、缩放或轻微对比度变化都会漏检。相邻滑窗命中又被计为多“处”，没有合并为一个几何区域。
- **影响**：显微视野、IHC、菌落、Western blot 条带等最常见的变换后复用无法检出；同时，把多个重叠 tile 当多处异常会夸大候选数量。裸模型无法做全稿跨图的局部几何对齐，这正是高 uplift 面。
- **方案**：**一期离线，P0/P1；Stage 3 + M5。** 在 `figure_integrity_audit.py` 增加 `geometric_duplicate` backend：
  1. panel 级 pHash 与多尺度重叠 tile 只作召回；使用评测环境已有 `numpy/scipy` 实现 DoG keypoint、旋转 BRIEF 描述子与 RANSAC affine/homography，若 `cv2` 可用则允许 ORB backend，但输出算法名与版本，不能把可选依赖当唯一实现。
  2. 对 normal / horizontal mirror / vertical mirror 三种方向分别估计变换；候选必须同时满足局部特征内点数、内点率、空间覆盖、重投影误差和 warp 后 NCC/SSIM 门。阈值由 P7 回归集冻结，不能把 `r≥0.98` 直接沿用到变换场景。
  3. 用变换一致的 tile 连通分量合并成 region pair；报告“1 对区域 + N 个支持匹配”，不把 N 个重叠 tile 冒充 N 处异常。
  4. 排除同一 panel 的近邻纹理、坐标轴/文字/比例尺 mask、整幅 inset 与其母图的明确放大关系；图注出现 `representative image reused`、`same control` 等文字只作为合法解释候选，不能自动压制。
  5. 输出 `check=geometric_duplicate_candidate`、两侧 polygon、变换矩阵、mirror flag、scale、rotation、inlier count/ratio、reprojection error、warped similarity、召回与确认阈值、人工复核清单。
- **代价**：4–6 人日；2–3 人日算法，1 人日区域合并/排版 mask，1–2 人日变换合成集与真实负例。2 核/4 GB 可按 figure pair 分批运行，12 小时足够。
- **建议优先级**：P0 先交跨图平移/90°旋转/镜像/0.5–2×缩放；任意角度与严重非刚性形变为 P1。跨论文图像搜索涉及大库与版权，留二期。
- **输入 / 输出映射**：输入为 P1 资产对象与 panel mask；输出复用 `figure_integrity_candidate`，`evidence_refs[]` 指向两张稿件内图，`image_audit` 保存几何取证包；M5 人工检查原图与图注后才决定是否立 finding。
- **契约字段**：扩展 `image_audit.check` 与其条件字段即可；不需要重构 `evidence_registry` 或增加 severity。
- **假阳性**：高。规则图案、同一视野的合法多通道成像、时间序列、对照复用、inset、重复曝光都可产生真实几何匹配。所有候选强制人工；**不得输出“duplicate fabrication”“manipulation confirmed”或任何造假概率**。沉默同样不得写“图像清白”。

### P3 · Western blot / gel 专属拼接与条带候选器

- **问题**：当前 `find_splice_discontinuity()` 对每张图整幅计算列中位数突变；它既没有确认 `chart_type=blot`，也没有排除条带、lane 间隔、标签和多 panel 排版。一条垂直亮度边界可由合法泳道间隔、曝光梯度、扫描阴影或版面拼接产生。单一 z 阈值不足以支撑“拼接痕迹”。
- **影响**：对普通统计图和组合图运行会产生无意义候选；对真实 blot 又会漏掉背景均值连续但噪声纹理、压缩残差或 band edge 不连续的拼接。图像完整性假阳性具有最高名誉风险。
- **方案**：**一期离线，P1；Stage 3 + M5。** 新增 `blot_forensics` 垂直切片：
  1. 只在 `figure_record.chart_type=blot` 且置信度至少 `medium` 时运行；输入必须是原始 panel bbox，分辨率过低、JPEG 严重块化、饱和像素比例过高时产 `system_limitation(figure_unreadable)`，不产拼接候选。
  2. 先做 lane/band/文字 mask。拼接边界至少由两个独立特征家族支持：背景中位数/方差 change point、左右噪声功率谱或自相关差异、跨边界梯度连续性、JPEG block phase 不一致。单一笔直边缘不得命中。
  3. 候选边界需跨越足够背景高度且不能只存在于 band 内；同时记录是否与 lane 间隙、panel 边界或图注标示的非相邻 lanes 对齐。合法删除泳道若有分隔线/说明，仍交人工判断呈现是否充分。
  4. 条带复制另走局部候选：背景扣除后比较 band contour 与局部噪声纹理，要求 band 与周围背景共同匹配；只比较条带强度轮廓会把常见饱和矩形 band 误报。
  5. 输出 `splice_boundary_candidate` / `band_region_duplicate_candidate`，保存边界线段、两侧背景 ROI、各分量分数、适用性前提和失败门控。
- **代价**：3–5 人日；需 20–30 张有原始分辨率的 blot/gel 正负例和合成 seam。当前 10 篇语料不足以单独校准，不能用纯噪声自检声称真实 precision。
- **建议优先级**：P1 应该做；在 P2 稳定后交付。原始未裁剪 blot 与曝光序列核验为二期，因为通常不随论文输入提供。
- **输入 / 输出映射**：输入为 blot panel、chart type、panel/lane mask、图注 evidence；输出仍为无 severity signal，并路由 M5。M5 若未能读取原图，只能保留候选或写系统限制，不能立“拼接已确认”。
- **契约字段**：P1 的区域/资产字段 + `applicability_gates[]`、`component_scores`、`boundary_geometry`；扩展现有 signal，不增加 finding 类别由本轮直接决定。
- **假阳性**：很高。裁剪、非相邻泳道并排、膜条切割、曝光校正、扫描器阴影和压缩都会产生边界。**绝不能从候选推断作者意图或直接下造假结论**；人工必须同时核对未裁剪原图、图注说明和实验设计。

### P4 · 版本化序列、引物靶向与基因—物种身份对账器

- **问题**：Round 3 P4 已部分实现为 HGVS/格式/引物 QC，但尚未验证 primer pair 是否在声称 transcript 上形成同向 amplicon；基因—物种检查目前只看大小写惯例，不能证明符号是否获该物种命名机构批准。不同 transcript、assembly、5' adapter、突变特异引物和成熟蛋白编号会让“看似不匹配”完全合法。
- **影响**：引物打不到靶标、reverse primer 方向错误、同一对在全基因组多位点扩增、密码子与氨基酸不对应，均会直接破坏机制实验；把小鼠同源基因写成人类符号也可能只是讨论人类 ortholog，自动判错同样危险。
- **方案**：分两条一期路径，共用同一审计器与 reference hash：
  1. **一期离线，P0**：M1 抽取 `sequence_entities[]` 与用户/补充材料提供的版本化 FASTA。primer pair 输入固定为 `{forward,reverse,target_transcript,organism_taxid,assembly,expected_amplicon_length,reported_tm,tail_5prime_length,evidence_refs[]}`。先剥离有明确标注的 5' tail，再用 IUPAC-aware exact scan 搜 forward 与 reverse-complement；只有方向相向、落在同一 reference、amplicon 长度落入报告舍入/范围才记 match。多匹配、只单侧匹配、reference 多 isoform 时输出候选或 `partial_extraction`，不选“最像”者。
  2. **一期联网增强，P1**：严格复用 Round 4 P1 的 X1。Ensembl 用 `GET /sequence/id/{stable_id}?type=cdna|cds|genomic` 获取明确版本序列，并用 `GET /lookup/id/{id}` 核对 species/version；官方端点见 [Ensembl sequence API](https://rest.ensembl.org/documentation/info/sequence_id) 与 [lookup API](https://rest.ensembl.org/documentation/info/lookup)。RefSeq 可沿 Round 3 P4 的 NCBI EFetch 路径。
  3. 人类符号先 `GET https://rest.genenames.org/fetch/symbol/{symbol}`，无 approved 命中再查 `search/prev_symbol` 与 `search/alias_symbol`；HGNC 官方说明 fetch/search 字段及 10 req/s 限速，见 [HGNC REST](https://www.genenames.org/help/rest/)。非人类用带 species 的 Ensembl symbol lookup 或对应命名库；大小写只保留 `candidate=true`，只有 taxon + 稳定 ID + 权威记录直接矛盾才形成身份 mismatch 候选。
  4. codon 检查必须绑定 CDS transcript、reading frame 与 genetic code；线粒体、硒代半胱氨酸、RNA editing 或成熟蛋白编号不明确时跳过。蛋白位点沿用本轮 A 类门控：完整序列、accession 与版本缺一不可。
- **代价**：3–4 人日离线 primer pair + codon；1–2 人日 Ensembl/HGNC connector 与录制响应。Biopython 已预装，但简单 IUPAC exact matching可用标准库完成，避免新依赖。
- **建议优先级**：P0 交付离线 primer pair + reference metadata；P1 加 Ensembl/HGNC 联网增强。模糊比对、全基因组 off-target 和 primer-dimer thermodynamics 为二期。
- **输入 / 输出映射**：M1 只抽实体；本地工具产 `sequence_identifier_inconsistent` 或 `partial_extraction`。联网结果进入 X1 `external` evidence，signal 同时引用稿件内 primer/symbol evidence 与外部记录；M3 判断方法学 finding，M2 只判断正文命名一致性。
- **契约字段**：扩展 `structured_result.sequence_entities[]`、`sequence_audit.check`（如 `primer_target_mismatch_candidate`、`primer_pair_nonunique_candidate`、`codon_residue_mismatch_candidate`）与条件输入块；联网字段复用 Round 4 P1，不另建 external schema。
- **假阳性**：中高。5' tail、允许 mismatch、基因组/转录本差异、剪接异构体、SNP、反义转录本和 nested PCR 都会改变匹配。只有精确 reference 与实验语义齐全时才允许确定性 mismatch；其余交人工。基因大小写永远不能单独证明物种错误。

### P5 · UniProt—InterPro—PDB/AlphaFold 的蛋白坐标、结构域与功能主张佐证

- **问题**：Round 1 P5 已提蛋白身份，Round 3 P5 已提坐标/结构域，但均未落地。真正可确定的是“指定 isoform 第 N 位是否存在、参考残基是什么、是否与某个 feature 区间重叠、PDB 是否覆盖该位点”；“数据库没写这个功能”并不能反驳论文的新功能发现。AlphaFold 的高 pLDDT 也不等于功能或相互作用得到验证。
- **影响**：错 isoform、成熟链/前体编号混用、位点越界、声称位于 kinase domain 但坐标不重叠，都会使突变机制链失效；反过来，把低 pLDDT 当“结构错误”或把缺注释当反证会产生专业性很差的假阳性。
- **方案**：**一期联网增强，P1；依赖 X1，M3/M7 消费。** 不新建第二个外部层：
  1. UniProt 精确 accession 调 `GET https://rest.uniprot.org/uniprotkb/{accession}.json`，保存 entry version、sequence version、canonical/isoform、长度、sequence、feature 类型与坐标；单条记录和 404/410 语义见 [UniProt individual entry API](https://www.uniprot.org/help/api_retrieve_entries)。只有 gene+species 时用 `/uniprotkb/search`，但多命中不得自动选 canonical。
  2. InterPro 调 `GET https://www.ebi.ac.uk/interpro/api/entry/interpro/protein/uniprot/{accession}/` 取 entry 与蛋白匹配区间；该组合端点由 [InterPro API](https://www.ebi.ac.uk/interpro/api/static_files/swagger/) 明确定义。Pfam member signature 作为 feature 来源之一，不把不同数据库边界差异强行合并成单一区间。
  3. 坐标比较先解析 `numbering_basis=canonical_isoform/specified_isoform/precursor/mature_chain/construct/PDB_author_numbering`。只有 basis 可唯一映射时运行 `position_in_range`、`reference_residue_match`、`feature_overlap`；构建体标签、信号肽切除和 initiator Met 移除都要显式 offset 证据。
  4. 结构证据优先已解析 PDB + SIFTS 残基映射。AlphaFold DB 用 `GET https://alphafold.ebi.ac.uk/api/prediction/{accession}` 获取模型元数据与下载链接；低 pLDDT/PAE 高只表示该区段不适合自动核对，产 `not_addressed` 或 system limitation，不表示稿件错误。高 pLDDT 只允许“模型在该局部有较高置信”，不能验证蛋白功能、配体结合或复合物界面。
  5. 功能主张输出四态 `supports/contradicts/not_addressed/not_comparable`。只有权威记录对同一实体、同一物种、同一 isoform 给出直接相反事实才允许 `contradicts` 候选；无 annotation、computational annotation 或不同 paralog 一律 `not_addressed/not_comparable`。
- **代价**：4–6 人日；X1/schema 前置 2–3 人日另计。需 TP53 isoform、受体前体/成熟链、激酶域边界、多结构覆盖缺口、低 pLDDT 无序区等 20 个 fixture。
- **建议优先级**：P1 应该做；最小垂直切片先交“exact accession + isoform 长度/残基 + InterPro 区间”。AlphaFold/PDB 结构语义随后；分子动力学、docking、ΔΔG 和复合物预测为二期。
- **输入 / 输出映射**：M1 抽取 `{claim_ref,accession,isoform,organism,claimed_position,claimed_residue,numbering_basis,claimed_feature,evidence_refs[]}`；X1 创建带 response hash/version 的 external evidence 与无 severity signal；M3 核对构建/材料，M7 核对功能或结构 claim。finding 必须同时引用稿件 claim 与外部 evidence。
- **契约字段**：复用 Round 4 P1 external evidence；`external_check` 增 `protein_coordinate`、`feature_overlaps[]`、`structure_coverage[]`、`confidence_assessment`。不改变三类记录。
- **假阳性**：高。isoform、物种、成熟蛋白、构建体、PDB author numbering、结构缺失区和数据库版本任一不明确即停止确定性比较。数据库沉默不是反证，AlphaFold 不是实验验证；所有功能/结构语义冲突交领域专家。

### P6 · 剂量—暴露—活性可比性网关，禁止把 LD50 当治疗窗

- **问题**：Round 2 P4 已提 ChEMBL/PubChem 活性数量级，但未覆盖安全窗。论文中的 `mg/kg`、血浆 `Cmax`、游离浓度、细胞培养 nominal concentration、`IC50/Ki/Kd/EC50` 与急性 `LD50` 属于不同量；盐型、立体化学、物种、route、duration、matrix、蛋白结合和 assay format 不一致时不能比较。简单规则“剂量高于 LD50”看似硬核，实际最容易误伤。
- **影响**：单位错位与 10³–10⁶ 倍数量级错误是确定性 uplift；但把小鼠腹腔单次 LD50 与大鼠口服 28 天剂量、或把 biochemical Ki 与细胞 IC50 直接对比，会给出科学上错误的安全性结论。
- **方案**：**一期离线保底 + 一期联网增强，P1；M1/X1/M3/M7。** 分三层执行：
  1. 离线 identity/context 层先抽 `{compound_name,catalog_or_cid,structure_id,salt_form,stereochemistry,organism,route,regimen,duration,dose,exposure_metric,total_or_unbound,matrix,target,assay_type,activity_type,evidence_refs[]}`；复用单位归一化器。缺 molecular weight、盐型或给药上下文只产 `partial_extraction`。
  2. PubChem PUG REST 只用于 CID/结构/分子量/同义词与 deposited assay 身份，通用格式为 `https://pubchem.ncbi.nlm.nih.gov/rest/pug/<input>/<operation>/<output>`，服务限制与状态码见 [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)。ChEMBL 用 `/chembl/api/data/molecule/{chembl_id}.json` 与 `/activity.json?...`，保存 molecule/target/assay IDs、`standard_type/value/units/relation`、organism、assay type、confidence score 与文献来源；接口见 [ChEMBL API](https://www.ebi.ac.uk/chembl/api/data/docs)。
  3. 可比性键必须完全覆盖 `chemical_identity + endpoint_family + target + target_organism + assay_format + biological_system + exposure_metric + route + duration`。`IC50/Ki/Kd/EC50` 不互换；biochemical/cell-based/in vivo 不互换；总浓度与游离浓度不互换。只有同键记录的舍入区间相差达到预注册数量级门槛才产 `bioactivity_outlier_candidate`，它仍不是矛盾。
  4. LD50 仅作同 species/strain/sex/route/acute duration/formulation 的毒理参照候选；不得把 LD50 称为治疗窗或 NOAEL。重复给药安全性优先同方案 NOAEL/LOAEL 与暴露 AUC/Cmax；无结构化权威记录时明确 `not_addressed`。人用治疗窗还需标签剂量、PK 和适应症，不从动物 LD50 外推。
  5. 网络 404 只有精确 CID/ChEMBL ID 才能记 `not_found`；名称语义搜索零命中为 `not_addressed`。429/5xx/超时/白名单拦截一律 X1 `system_limitation`，不生成稿件 signal。
- **代价**：4–6 人日；compound identity 1–2 人日，可比性路由 2 人日，录制响应与 25 个困难反例 1–2 人日。结构化 NOAEL/LOAEL 数据源需另行筛选许可与 API 稳定性，未解决前不得宣称安全窗已核验。
- **建议优先级**：P1 先交 compound identity + 同 endpoint 活性数量级；安全窗只做严格可比的垂直切片。跨物种毒代动力学、PBPK 和治疗指数建模为二期。
- **输入 / 输出映射**：M1 只抽 dose/activity/exposure 对象；X1 产 external evidence 和 `external_validation_candidate`；M3 评估实验剂量/材料身份，M7 只在论文作“clinically relevant/safe/selective”主张时消费。任何 finding 同时引用稿件剂量、claim 与外部比较记录。
- **契约字段**：复用 Round 4 P1；`external_check` 增 `chemical_identity`、`assay_context`、`exposure_context`、`comparability_dimensions[]`、`noncomparability_reasons[]`。不新增记录类型。
- **假阳性**：很高。盐型、route、species、duration、free fraction 和 assay 系统均会产生数量级差异。外部 outlier 只能排入药理专家人工复核，不能自动写“剂量不安全”“结果伪造”或提升到 critical。

### P7 · 图像与结构取证的困难反例门禁和 uplift 验收

- **问题**：当前图像自检只含植入块、纯噪声、白底和全幅亮度跳变；它能证明代码运行，不能证明对真实显微图/blot 的 precision。序列测试也缺 isoform、成熟链、5' primer tail 和多转录本反例。没有规则级 gold，新增取证器可能只增加候选数量而非 uplift。
- **影响**：六维 Rubric 明确奖励不确定性与失败案例；若只展示合成阳性，评委会认为团队回避最关键的误报问题。图像候选过多还会增加人工队列，实际 uplift 可能为负。
- **方案**：**一期离线评测基础设施，P0。** 新增包内小型 fixture 与 `tools/evaluate_forensics.py`：
  1. 图像集合包含平移/任意偏移/90°与小角度旋转/镜像/缩放/JPEG 重压缩阳性；合法多通道同视野、inset、同一 loading control 明示复用、重复纹理、相邻序列切片、坐标轴与排版模板阴性。
  2. blot 集包含真实 lane gap、非相邻泳道明确分隔、合法裁剪、曝光梯度、JPEG block、合成背景 seam、band+background 共同复制；至少两名图像完整性复核者盲标，保留分歧。
  3. 序列/结构集覆盖 canonical vs isoform、signal peptide/mature chain、initiator Met、PDB author numbering、低 pLDDT 无序区、primer 5' tail、degenerate base、intron-spanning、多个 transcript、线粒体 genetic code。
  4. 剂量集必须把不可比对作为主负例：mouse IV vs oral、acute LD50 vs repeated NOAEL、Ki vs IC50、biochemical vs cell、total vs unbound、base vs salt。门禁报告 candidate precision/recall、每篇候选数、人工复核分钟数、证据回映成功率和 system limitation 正确降级率。
  5. 同一官方模型跑 skill/no-skill 各 3 次，取任务中位数；成功标准不是文字更长，而是新增确定性错误召回、证据定位与错误降级改善，同时 major/critical 假阳性不增加。未达到预注册 candidate precision 门槛的规则只能保留在人工实验队列，不能进入默认运行。
- **代价**：3–5 人日标注与 fixture，1–2 人日评测脚本；可复用 Round 6 P1 的论文级 uplift 口径，不另造总分。
- **建议优先级**：P0；P2–P6 任一组件进入默认流程前必须过对应困难反例门禁。
- **阶段 / 归属**：评测基础设施，不属于 M1–M7，不进入审稿报告。
- **契约字段**：不改生产契约；测试 schema 保存 `gold_candidate_regions[]`、`legitimate_reuse_reason`、`reference_context`、`comparability_gold`、`reviewer_adjudication` 与算法版本。
- **假阳性**：评测不立稿件 finding。公开论文中的“可疑图像”不能自动当 gold；阳性需合成 ground truth、作者/期刊已确认材料或双人可复核的几何事实，意图和不端定性不进入标签。

## 未解决 / 需要人来定的问题

1. 是否在交付前接受 Round 4 P1 的 `stage_3c_external_validation + external evidence + external_validation_coverage`。P5/P6 与 P4 联网部分都依赖它；未采纳时只能做录制响应原型，不能把外部结果写进正式报告。
2. M5 负责人是否接受 Round 5 P1 的 Parser/Reviewer 边界修复。图像工具只能产 signal；当前 M5 文档若仍允许 Parser 直接产 critical finding，会抵消本轮全部名誉风险控制。
3. P1 的图像资产 hash 放入 `present evidence` 还是仅放 `image_audit.asset`。建议 evidence 保存最小 `asset_sha256 + dimensions`，详细解码/变换信息留在 signal，既能证明来源又不膨胀每条证据。
4. 是否把 OpenCV 作为可选优化依赖。建议默认实现只依赖预装 `numpy/scipy/Pillow`，`cv2` 仅作同输出契约的加速 backend；否则官方镜像未预装时最重要的图像能力会整体降级。
5. 图像候选是否允许自动生成任何 M5 finding。建议不允许：默认只进入编辑人工复核队列；人工确认合法解释已排除后才由 M5 建立最多 `review_confidence=medium` 的疑似完整性 finding，措辞仍不得断言造假。
6. Round 1 P7 已被部分采纳为 `figure_integrity_audit.py`，Round 3 P4 已被部分采纳为 `sequence_identifier_audit.py`；Round 3 P5、Round 4 P1、Round 5 P1 尚未见落地。本轮 P2/P4 是已实现脚本的增量，不应再创建平行工具；P5/P6 必须复用唯一 X1。
7. 当前论文语料多为 1400px JPEG，不能代表编辑部收到的原始 TIFF/blot。是否另建可再分发的真实负例集需要许可拍板；未解决前必须把真实图像 precision 标为未验证。
