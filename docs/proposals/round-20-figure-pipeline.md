# Round 20 · 图表管线与 Stage 3/3b 衔接 提案

## 摘要

Figure Parser 与 M5 的主契约已经分成“Stage 3 事实抽取 / Stage 4 稿件判断”，但禁改的 `references/05` 仍保留旧的混合产出者叙述，交付前必须由 M5 负责人收敛。
本轮直接封住了三类确定性丢失：图观测回流时非数值字段漂移、图观测无轨迹消失、含视觉来源的图文冲突未路由 M5；同时强制 `axis_readable` 记录坐标轴及其 scale。
新增能力不重复 Round 5/11/16：建议优先做同稿高质量资产获取与矢量抽取，再做流式 gating 图谱和 Kaplan–Meier 风险表/曲线联合取证，三者都只产可审计事实或候选，不自动指控稿件。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §2.8 步骤 2、5 | Stage 3b 只移除三个临时路由字段，其余 `observation_core` 必须原样保留；每条图观测必须落入一个组或被 Stage 3b limitation 以 `affected_targets[]` 明确拒收；含视觉来源的冲突必须再路由 M5 | 旧摘要只点名保留 id/value/provenance，允许单位、uncertainty、n、重复类型和置信度在回流中漂移；M5 也可能收不到已经计算出的图文冲突 |
| `skills/biomed-paper-review/references/00-contracts.md` | §5.4 第一步、第四步；§6.2 | 固定跨副本逐字段一致性、路由身份与目标组一致性、拒收轨迹；把视觉来源的 `source_value_conflict` 消费者扩为 M2/M4/M5 | 同一 observation id 只比较 value/provenance 不足以证明数据无损；Stage 3b 仍只产 signal，M5 才能判断 `figure_text_contradiction` |
| `skills/biomed-paper-review/schemas/figure_record.schema.json` | `axes`、`$defs.axis`、顶层 `allOf` | 禁止空 `axes`；轴对象必填 `scale`；出现 `axis_readable` observation 时必填至少一个轴 | 文档声称线性/对数必须显式记录，旧 schema 却接受 `axes: {}` 或完全缺轴，数值可在尺度未知时进入 v2 |
| `skills/biomed-paper-review/schemas/key_data.schema.json` | `observations` 说明 | 明确落盘副本必须保留全部 `observation_core` 字段，跨对象一致性由校验器执行 | 防止实现者把 schema 的“核心对象复用”误解成只复制三项字段 |
| `tools/validate_schemas.py` | schema 层、Figure 路由、key_data、signal lint | 检查 axis scale；检查 Stage 3 重复 id 全字段一致；在 v2 中核对图观测 core、指标身份、五键、唯一落组或明确拒收；含视觉来源的冲突强制路由 M5 | 原 153 项检查只验证单个 figure observation 形状，没有证明 Figure → v2 的跨对象传递，也没有检查 M5 消费闭环 |

## B 类提案

### P1 · 同稿资产解析器：优先作者源数据 / 矢量图，再退化到像素估读

- **问题**：当前 Stage 1 只接受已给输入，Stage 3 的数值来源只有 `axis_readable` 与 `pixel_estimated`。同一篇开放获取论文常同时存在 JATS、矢量 PDF、独立高分辨率图、补充 XLSX/CSV 和网页渲染 JPEG；若系统只处理最后一种，主动丢掉最可审计的数据层，再用低置信像素区间补救。该能力不是 X1：这些文件是**同一稿件的其他表示**，不是独立外部事实。
- **影响**：像素估读比例会无谓升高，曲线、误差棒和细小标记难以复算，M5 只能看到压缩图。裸模型无法自动枚举 OA 包、核对文章版本与文件 hash、选择最优资产并保持 provenance；这是直接的 uplift 面。
- **方案**：**一期离线保底 + 一期联网输入增强，Stage 1 / Stage 3。** 在 `skills/biomed-paper-review/scripts/` 新增 `resolve_article_assets.py`，作为 Stage 1 的可选输入增强，不并入 X1 resolver。
  1. 本地先枚举用户提供的 JATS/XML、PDF、SVG/EPS、TIFF/PNG、XLSX/CSV 与 supplement；按 `author_source_data > embedded_vector > high_resolution_raster > rendered_raster` 固定优先级建立同稿资产图。只有图注、panel 标签、文件清单三者能闭合时才自动关联；否则保留多个候选并产 `partial_extraction`，不得按文件名相似度硬配。
  2. 有 PMCID 且允许联网时，首选 Europe PMC `GET https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/supplementaryFiles?includeInlineImage=true` 获取可用 supplement 与 inline image ZIP；官方接口明确该端点及 OA 图像限制，见 [Europe PMC REST](https://dev.europepmc.org/RestfulWebService)。NCBI 路径使用新的 PMC OA S3 数据集：先对 `pmc-oa-opendata` 以 `PMCID.` 前缀列出文章版本，再只下载该版本的 XML、图像和数据文件；官方说明了逐 PMCID 版本前缀、匿名访问和 2026 年目录迁移，见 [PMC Article Datasets on AWS](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)。不得抓取 PMC 网页正文；批量网页下载受官方版权规则限制。
  3. 所有资产先校验文章 id、版本、license、media type、byte size 与 SHA-256；压缩包做路径穿越、压缩炸弹和单文件 10 MB 门控，缓存不进入提交包。license 不允许处理、版本不匹配或 hash 变化时停止自动关联。
  4. 对 PDF/SVG 的简单 bar/scatter/step/line 图，解析文本 tick 与 vector path，在轴变换空间恢复坐标；输出必须保存 tick anchors、path id、坐标变换、拟合残差与文件 hash。复杂 clip path、broken font、rasterized layer、双轴绑定不唯一时退化到 Round 5 P3 的像素标定提案，不输出点值。
  5. 作者 XLSX/CSV 中能以 sheet/row/column 与 panel/series 唯一绑定的值，按 `explicit_table` observation 进入 Stage 3b；矢量坐标恢复值沿用 `axis_readable`，但 `derivation.extraction_method` 扩 `vector_path_read` 并必填 `measurement_trace`。同稿源数据与正文不一致仍只产 `source_value_conflict` signal，由 M2/M4/M5 回查后判断。
  6. 联网失败只新增 `asset_retrieval_unavailable` system limitation，`produced_by=stage_1`；不得复用 X1 的 `external_source_unavailable`，也不得把“无 OA 包”写成稿件数据不可得。离线输入仍跑完整流程。
- **代价**：3–5 人日；本地资产图与安全解包 1 人日，Europe PMC/PMC connector 与录制响应 1 人日，SVG/PDF 简单图型垂直切片 1–3 人日。需申请 `www.ebi.ac.uk` 与 `pmc-oa-opendata.s3.amazonaws.com` 白名单；PDF vector parser 依赖需先在官方镜像确认。
- **建议优先级**：P0 交付前先做“本地 supplement/source-data 优先 + Europe PMC 单篇 ZIP + hash”；矢量 bar/scatter 为 P1。不要先扩更多数据库。
- **阶段 / 归属**：一期离线核心 + 一期联网输入增强；Stage 1 获取与登记，Stage 3 解析，Stage 3b 合并，M2/M4/M5 判 finding。不新增审核模块，不让 M1 或 Parser 产 finding。
- **契约字段**：扩展 `asset_inventory.items[]` 为 `{asset_id,origin,parent_asset_id,article_id,article_version,license,media_type,byte_size,sha256,retrieved_at,source_manifest_ref}`；`evidence.locator` 增 `asset_id`；`provenance.derivation` 增 `vector_path_read` 与 `measurement_trace:{asset_id,axis_anchors[],path_refs[],transform,residual,algorithm_version}`。这是现有非记录对象、present evidence 与 observation 的扩展，不新增第四类记录。
- **假阳性**：低到中。最大风险是把 supplement 的汇总数据绑到错误 panel/analysis population，或把装饰性 vector path 当数据。panel/series/endpoint/单位任一不能唯一闭合就不自动关联；同稿资产缺失或 API 失败永远不是 finding。

### P2 · 流式细胞术 gate graph：把“百分比”绑定到父群、变换与补偿上下文

- **问题**：当前 `flow_cytometry` 只有通用 figure observation；五键没有 parent gate、分母基准、marker channel、坐标变换、补偿矩阵或 gating chain。`37% CD8+` 可能是占 live singlets、CD3+、lymphocytes 或 all events，四个数不能混为同一 endpoint。Round 5 P4 只提出“四象限在确认互斥穷尽时求和”，没有建立完整 gate 图，也无法复查 gate 在不同样本间是否对应同一父群。
- **影响**：Stage 3b 会把不同分母的频率误合并成冲突，或把 parent-gate 丢失后交给 M4 做错误百分比复算。流式图是免疫学、血液学与细胞治疗论文的核心证据，裸模型通常只会泛泛要求 FMO/补偿，无法构建可复算 gating 血缘。
- **方案**：**一期离线，Stage 3 / Stage 3b / M3 / M4 / M5。** 新增 `scripts/flow_gate_audit.py`，首版只审稿件已展示的 gating 事实；若 P1 取得 FCS + Gating-ML，再启用原始事件复算。
  1. `figure_record` 对流式 panel 增 `flow_gate_graph`：`{sample_or_group_ref,gates[]}`；每个 gate 固定为 `{gate_id,parent_gate_id,population_label,marker_channels[],transform_by_axis,gate_type,denominator_basis,event_count,reported_fraction,geometry_ref,evidence_refs[]}`。`denominator_basis` 只取 `parent_gate/all_acquired/live_singlets/other_explicit/unknown`，不得从常见实验流程猜默认父群。
  2. gate chain 必须显式表示 debris exclusion、singlet、viability、lineage 与终末群之间实际展示的边；未展示某一步是“未知”，不是自动的 `missing_gate` finding。不同 panel 的同名群只有 marker set、父群和分母完全一致才可共享 metric identity。
  3. 确定性检查只含：`child_count <= parent_count`；同 gate 的 count/fraction/denominator 舍入区间闭合；明确互斥穷尽 sibling 的和；正文/柱图频率与原始 gate 标签的同分母对账。未确认同一 sample、parent 或 denominator 时固定 `not_comparable`。
  4. 可获得 FCS 与 Gating-ML 2.0 时，保存 FCS hash、parameter/channel mapping、spillover matrix、transformation 与 gate geometry 后本地复算 event count；Gating-ML 2.0 可表达 gate 并应用到 FCS，标准边界见 [ISAC Gating-ML 2.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC4874733/)。只有原始文件与稿件样本 id 唯一绑定才运行；没有 Gating-ML/workspace 时禁止模型从截图重建多边形后宣称复算原始事件。
  5. 输出 `flow_gating_consistency_candidate` extraction signal，`flow_audit` 保存 gate ids、分母、舍入区间、前置条件和 rule version。M4 只判算术闭合，M3 判实验设计/控制与补偿报告，M5 判图注、轴、gate 标签和图文一致性。
- **代价**：2–3 人日完成截图 gate graph + count/fraction 闭合；FCS/Gating-ML parser 再需 2–4 人日及可再分发的困难样例。2 核/4 GB 足以按 sample 流式读取 FCS，不应把整批事件常驻内存。
- **建议优先级**：P1；优先于自动 gate 质量评分。首版只需 parent-denominator 闭合和图文频率对账。
- **阶段 / 归属**：一期离线；Stage 3 产 gate graph 与 signal，Stage 3b 只在完整上下文下合并，M3/M4/M5 产 finding。不新增模块。
- **契约字段**：扩展 `figure_record.flow_gate_graph`；`target_grouping_key` 后续与 Round 5 P2 的 context migration 合并增加 `analysis_population_ref/denominator_ref`，不得另造第二套自由字符串；扩 signal type 与 `flow_audit` 条件块。三类记录不变。
- **假阳性**：高。百分比可相对 parent 或 total、补偿/变换会改变 gate geometry、FMO 并非每个 marker 都强制、不同样本也可能合法使用自适应 gate。任何上下文缺失只产 `partial_extraction` 或人工候选；禁止自动写“gating 不当”或“数据操纵”。

### P3 · Kaplan–Meier 曲线—风险表—报告统计联合取证

- **问题**：现契约只能把 KM 图当普通 `survival` figure，无法绑定每条曲线的 `n_at_risk`、censor tick、事件数、time origin、estimand、置信带和分析集。Round 5 P4 只提出“无延迟入组时风险人数不得回升”，没有检查风险表与曲线步进、报告中位生存期、固定时点生存率和总事件数是否在同一分析集下闭合。
- **影响**：常见硬错包括风险表错行、月/周时间单位错位、ITT/PP 曲线与正文 HR 混用、median survival 与 S(t)=0.5 交点明显不相容、竞争风险曲线被当普通 KM。裸模型难以逐 tick/逐时间窗恢复曲线并管理删失假设，确定性工具能形成明显 uplift。
- **方案**：**一期离线，Stage 3 / Stage 3b / M4 / M5。** 新增 `scripts/survival_curve_audit.py`，依赖 P1 的矢量坐标或 Round 5 P3 的可审计像素标定；无可靠标定时不运行数值复算。
  1. 每个 series 建 `survival_curve_data:{series_id,analysis_population,estimand,time_origin,time_unit,probability_scale,start_n,step_points[],censor_marks[],numbers_at_risk[],reported_events,ci_band_ref,extraction_method,evidence_refs[]}`。`estimand` 至少区分 `kaplan_meier_survival/cumulative_incidence/one_minus_km/unknown`，防止把竞争风险累计发生曲线强制成单调下降。
  2. 直接几何检查：KM survival 必须在显示精度内非增；cumulative incidence 必须非减；概率需在 `[0,1]`；同 series 的时间坐标与风险表 tick 必须一致。合法绘图平滑、抗锯齿和线宽用标定区间吸收，单个像素回升不报警。
  3. 直接报告对账：只有 analysis population、time origin、time unit 与 series 唯一绑定时，核对正文/表格的固定时点生存率是否落在曲线标定区间，报告 median 是否落在首次跨过 0.5 的时间区间。曲线从未降至 0.5 时只能支持“median not reached”或下界，禁止外推点值。
  4. 有 `numbers_at_risk + total events` 时，可按 Guyot 等人的迭代方法重建**近似**个体时序，方法原文见 [BMC Medical Research Methodology](https://link.springer.com/article/10.1186/1471-2288-12-9)。重建只用于检查风险表/曲线/事件数能否同时近似满足，并保存每区间误差与多解状态；不得用近似 IPD 自动否定稿件 HR、重做亚组显著性或声称原始数据错误。
  5. 输出 `survival_curve_consistency_candidate` signal，按 `direct_geometry_mismatch/direct_report_mismatch/reconstruction_residual_high` 分层。前两类在完整绑定且区间不相交时交 M4/M5；重建残差永远 `manual_review_required=true`，review confidence 上限 `medium`。
- **代价**：3–4 人日；数据结构与直接对账 1–1.5 人日，Guyot 近似重建 1–1.5 人日，延迟入组、竞争风险、median 未达到、双轴、风险表 OCR 等 15 个困难 fixture 1 人日。numpy/scipy 已预装。
- **建议优先级**：P1；先交“固定时点/median/时间单位对账”，近似 IPD 重建为 P2 二期能力，除非官方任务生存图占比高。
- **阶段 / 归属**：一期离线直接对账；近似 IPD 深度复算建议二期。Stage 3 产事实与 signal，Stage 3b 合并，M4 判统计一致性，M5 判图形/图文一致性。
- **契约字段**：扩展 `figure_record.survival_curve_data` 与 series/axis refs；新增 signal type 及 `survival_audit:{check,series_ref,inputs,expected_interval,observed_interval,reconstruction_residuals,preconditions,rule_version}`。不新增记录类型；任何 finding 仍须引用稿件内 present evidence。
- **假阳性**：中高。延迟入组、区间删失、竞争风险、landmark 分析、加权 KM、截断 y 轴、风险表取整和不同分析集均可造成表面不闭合。上下文任一不完整时停止直接比较；近似重建只能排人工复核，不能自动给 severity。

## 未解决 / 需要人来定的问题

1. Round 5 P1 仍未采纳：`references/05-figures-and-charts.md` §A.1/A.5/D/F.5 仍让 Parser 产 finding 或让 M5 产 figure record，并把图像候选预设为 critical。该文件受禁改约束，本轮未修改；M5 负责人必须在交付前收敛到主契约。
2. Round 5 P2/P3/P5 仍未落地：多系列/逐时点 n/error-bar context、像素坐标标定、标准 Draft 2020-12 验证与正反 figure merge fixture 都是本轮 P2/P3 的前置，不应另建平行字段。
3. Round 16 P1 的 `scripts/merge_observations.py + comparison_trace[]` 仍未实现。本轮校验器能拒绝跨副本丢失，但不会替模型执行单位换算、配对比较、组状态和 canonical；这是比继续新增图型规则更高的 P0。
4. 当前四个 fixture 中，唯一非空 `figure_records[]` 属 `interpretation_only`，没有任何 `figure_review/full_review` fixture 真正执行 Stage 3b 回流。建议采纳 Round 5 P5 的 `figure_route_merge` 正反例，而不是把本轮新增 lint 的“当前全绿”误称为端到端已验证。
5. `curve_fit` 与 `significance_markers` 仍保存辅助数值副本，校验器只检查字段完整，没有证明它们与 `observations[]` 同值。Round 5 已要求 observation registry/refs 后消除双写；未迁移前 M2–M7 只能消费 observations，禁止从辅助对象取数。
6. P1 的同稿资产获取应放在 Stage 1，而不是 X1。若团队把它塞进 X1，Stage 3b 已结束后才拿到高分辨率图会形成回流环；需要拍板 `asset_retrieval_unavailable` category 与 `asset_inventory` 扩展。
7. PMC OA 数据分发在 2026 年正迁移到按文章版本组织的 S3 结构；实现必须锁定实际文章版本和 license，不能把旧 FTP 路径写死，也不能把缓存打进 50 MB 提交包。
8. 本轮按最新评测前提使用“离线保底 + 一期可选联网增强”。P1 的联网取同稿资产不改变审稿判断来源；无网络或无 OA 授权只降级能力，不构成稿件问题。
