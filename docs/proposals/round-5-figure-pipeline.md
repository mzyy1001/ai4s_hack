# Round 5 · 图表管线与 Stage 3/3b 衔接 提案

## 摘要

`figure_record.observations[]` 原先通过不可满足的 schema 组合追加路由字段，且 Stage 3b 没写清“并入既有组 / 新建组 / 移除临时字段”的确定算法；本轮已直接修复并把 panel 粒度、定量结果唯一回流入口和重复 observation 处理写进契约。
现有像素估读约束能阻止伪造点值，却不能阻止任意窄区间；必须增加坐标标定、像素误差传播和裁剪依据，才能把“区间”变成可审计测量而非换一种写法的猜数。
`references/05-figures-and-charts.md` 仍把 Figure Parser 与 M5 Reviewer 混为同一产出者，多曲线图的系列、逐时点样本量和误差棒语义也会在回流中丢失；应先修职责与上下文契约，再上图内算术审计和既有图像取证提案。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §2.7 | 固定“每个可独立解读 panel 一条记录”；Figure Parser 只记录科学问题与可见事实，图型适配和呈现规范只由 M5 判断；`curve_fit` / `significance_markers` 的定量值必须进入 `observations[]` 才能被审核消费 | 原文要求 Parser“判断图型是否匹配”，与“不评判”冲突；辅助对象里的 IC50、AUC、p 值原本会绕过 provenance 与 Stage 3b |
| `skills/biomed-paper-review/SKILL.md`、`references/00-contracts.md` | §2.8；§5.4 | 写明图观测按指标身份 + 五键完全匹配既有组，否则新建组；入组时只移除三项临时路由字段，保持 observation id/value/provenance；重复 id 内容不一致时 fail closed | 原契约只说“归组”，没有定义无匹配组、字段迁移和重复副本冲突，两个实现会产生不同 v2 |
| `references/00-contracts.md` | §2.4 | 将单侧 `lower_bound` / `upper_bound` 限定为图像可见范围确实截断真实值的情形 | 原规则允许任何像素估读使用单侧边界，可能把普通模糊读数伪装成有方向的约束 |
| `schemas/key_data.schema.json` | `$defs.observation*` | 拆出可组合的 `observation_core`；key_data 落盘形状继续以 `unevaluatedProperties: false` 封闭 | 原 `observation` 自带 `additionalProperties: false`，figure schema 用 `allOf` 添加 `target_grouping_key` / 指标字段后，标准 Draft 2020-12 验证器会同时要求并禁止这些字段 |
| `schemas/figure_record.schema.json` | 文件说明、`observations`、`curve_fit`、`significance_markers`、顶层 `allOf` | 改引用 `observation_core` 并封闭最终形状；五键禁止额外属性，指标名非空；辅助对象明确不是回流接口；任一 pixel observation 强制 panel 记录整体 `low + manual_review_needed=true` | 修复 schema 不可满足和定量值旁路；原来只约束 observation，自身记录仍可声称 high / 无需复核 |
| `tools/validate_schemas.py` | schema 层、figure 实例 lint | 增加组合形状、五键路由、panel 级像素降级、curve-fit 来源声明与 significance-marker 完整性检查 | 旧校验器只检查单个 pixel observation，无法发现 figure schema 的组合矛盾或整条记录未降级 |

## B 类提案

### P1 · 把 `references/05` 拆成 Parser 事实层与 M5 判断层

- **问题**：`references/05-figures-and-charts.md` 开头把同一“模块”定义为 Stage 3 解析和 Stage 4 审核；§A.1 步骤 2–5 要 Parser 判断图型适配、位置和规范并输出 `figure_record + finding[]`，§A.5 又写“M5 产出 `figure_record[]` 与 `finding[]`”。§D 让命中解析条件时同时写 `figure_record.manual_review_needed` 和 `finding.manual_review.action`；§F.1 说取证只产 `suspected`，§F.5 却把候选直接映射为 `critical` category。这与 `SKILL.md §2.2`、`figure_record.schema.json` 的唯一产出者模型正面冲突。
- **影响**：实现者可能让 Stage 3 直接产 critical finding，违反三类记录边界和唯一产出者；另一实现若严格禁止，则 §A.2/B/C 大量规则没有执行角色。自动评审会把同一输入跑出不同数组，直接扣工程质量、复用性和科学可信性。
- **方案**：**一期离线，P0**。由 M5 文件负责人修改 `references/05-figures-and-charts.md`：① §A 只保留定位、panel 切分、图型分类、条件/坐标/可见结果抽取与 provenance，产物固定为 `figure_records[]`、`stage3_system_limitations[]`；② §B–D 明确为 M5 规则，只读已封闭的 `figure_records[]` 与稿件证据，产 `m5_findings[]`；③ §A.1 步骤 2 改为“记录图型”，适配性判断移到 §B；④ §A.5 删除 M5 产 figure record 的表述；⑤ §D 把 Parser 触发条件与 M5 finding 动作分列，Parser 不创建 `manual_review.action`；⑥ §F.1/F.5 的图像取证结果先进入无 severity 候选，只有 M5 人工核对原图与合法复用说明后才可决定 finding，category 文案必须含“疑似/需核对”，禁止自动写“造假”。同步 `SKILL.md §2.2/§2.7/§2.9`、`tools/validate_schemas.py` 增加产出者静态检查。
- **代价**：0.5–1 人日；不改算法和 schema，需 M5 文件负责人拍板并修改禁改文件。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期；Stage 3 Figure Parser + Stage 4 M5，不新增模块。
- **契约字段**：不新增字段；收敛现有产出者语义。若后续落地图像取证，复用 Round 1 P7 的候选字段，不在本项另造一套。
- **假阳性**：本项不产生稿件判断；它阻止 Parser 把启发式观察直接升级为 finding。

### P2 · 多系列图的条件、编码与样本量无损回流

- **问题**：`figure_record.experimental_conditions` 只有全图级 `groups[] / dose_levels[] / timepoints[] / n_per_group`，`axes` 只有 `x/y`。真实生物医学图常见多条 treatment curve、sex/亚组 facet、左右双轴、每个时间点不同的 at-risk n、技术/生物重复混用、SD/SEM/CI 不同误差带。当前 schema 无法把“哪条线、哪个时点、哪个分析集、哪个误差定义”绑定到 observation；单个 `n_per_group` 会把 KM 风险表、纵向失访和不同实验批次压扁。Round 3 P3 已提出扩展 key_data 上下文，但 figure 侧没有对应载体。
- **影响**：Stage 3b 可能把女性亚组与总体、PP 与 ITT、72 h n=3 与 24 h n=6 合并为冲突；M4 也可能把 technical replicate 当样本量，或把 SEM 带当 SD。其结果不是少抽字段，而是制造错误 finding。
- **方案**：**一期离线，P0/P1**。在 `figure_record.schema.json` 新增 `series[]`，元素固定为 `{series_id,legend_label,group,comparison,dose,timepoint,endpoint,analysis_population,strata[],n,replicate_type,error_bar_type,axis_ref,facet_ref,aesthetic_encoding,evidence_refs[]}`；`error_bar_type` 为 `SD/SEM/95CI/IQR/range/unknown/none`。`axes` 改为带稳定 `axis_id` 的数组，支持 `x/y/y2/color/facet`，每轴保存 scale、unit、range 与 tick evidence。每条 observation 新增必填 `series_ref` 与 `axis_ref`；Stage 3b 把这些字段投影到 Round 3 P3 已提的扩展 grouping context，投影规则写入 `00-contracts.md §5.4`。无法把图例颜色/线型唯一解析到系列时，不合组，产 `partial_extraction` signal；不得选“最像”的系列。增加多曲线剂量反应、KM 风险表、分面 forest plot、双轴图四个 fixture。
- **代价**：2–3 人日；依赖团队接受 Round 3 P3 的上下文扩展。若暂不迁移 key_data，可先保留 series fields，但必须禁止自动合组并在报告披露回流不完整。
- **建议优先级**：P0 交付前至少完成 `series_ref + timepoint-specific n + error_bar_type`；完整 axis/facet 模型为 P1
- **阶段 / 归属**：一期；Stage 3 产上下文，Stage 3b 投影，M4/M5/M7 消费，不新增审核模块。
- **契约字段**：扩展 `figure_record.series[]`、`axes[]`、figure observation；与 Round 3 P3 扩展现有 `grouping_key`，不重构三类记录。
- **假阳性**：高；默认动作必须是“不合组 + 人工映射”。颜色相近、图例顺序不清、同一组多分析集或风险表 OCR 不稳时不得生成 conflict。

### P3 · 可审计的像素坐标标定与误差传播器

- **问题**：当前 `pixel_estimated` 只强制区间、low、人工复核和禁止 M4 复算，但没有保存 plot area、刻度锚点、线性/对数变换、像素坐标、线宽或分辨率。实现者仍可把肉眼猜测的 `12.37–12.39` 写成“合法区间”；对 log10 轴、粗 marker、抗锯齿边缘和截断柱尤其危险。
- **影响**：评委查看 JSON 时无法复算区间来自哪里，“防编造”只停留在枚举层。伪精确会污染 canonical、图文冲突和 claim 支撑，主要扣 25% 科学可信性与 30% 工程质量。
- **方案**：**一期离线，P0**。新增 `skills/biomed-paper-review/scripts/calibrate_figure_values.py`，输入 panel 图、plot-area bbox、至少两个同轴 tick 锚点及 marker/segment bbox；输出 `visual_measurement:{axis_ref,axis_scale,plot_bbox_px,calibration_points[],mark_bbox_px,pixel_uncertainty_px,value_interval,interval_method,source_width_px,source_height_px,algorithm_version}`。线性轴拟合 `value=a·pixel+b`；log2/log10/ln 轴在变换空间拟合后反变换。区间至少覆盖 marker/线条整个像素宽度、标定残差和 ±1 pixel 量化误差；OCR tick 只要有一个字符低置信或不足两个有效锚点，就不产数值 observation，改产 `visual_calibration_unavailable` system limitation。`lower_bound/upper_bound` 还必须保存 `clipped_at:{axis_ref,boundary,value}`。修改 `common.schema.json` 使 `pixel_estimated` 条件必填 `visual_measurement`，validator 用脚本重算 interval 并验证报告区间不窄于计算区间。无论标定多好，pixel 值仍不得进入 M4 复算，finding confidence 上限不变。
- **代价**：2–3 人日；numpy/scipy 足够，图像坐标需 PIL/OpenCV 中择一。若环境无 OpenCV，先接受人工给 bbox 与 tick anchors，仍能交付可复算核心。
- **建议优先级**：P0 交付前必须做最小垂直切片：linear/log axis + 两点标定 + 误差区间；自动 tick/marker 检测为 P1
- **阶段 / 归属**：一期；Stage 3 工具能力，只产 observation 或 system limitation，不产 finding。
- **契约字段**：扩展 observation 的 `visual_measurement` 条件分支；system limitation category 新增 `visual_calibration_unavailable`。这是现有契约扩展，不新增记录类型。
- **假阳性**：低；组件不判断稿件问题。标定不足时宁可不出读数；人工修改 bbox 后必须重新计算并保存算法版本，禁止手填 interval。

### P4 · 生物医学图内守恒与几何一致性审计器

- **问题**：现有 M5 规则主要检查“有没有标签”，没有利用图中结构化数字做确定性闭合。常见硬错包括：CONSORT 流程人数不守恒、flow cytometry 四象限百分比不合计 100%、标准化堆叠柱超过 100%、forest plot 点估计落在自身 CI 外、KM 风险表在无延迟入组时人数回升、剂量反应图标注 IC50 却不在可见 50% 响应交点附近。这些是裸模型难以稳定逐项复算的 uplift 来源。
- **影响**：复制粘贴、panel 标签错位、分母混用和绘图脚本错误会被漏掉；直接把任何“不相等”判错又会误伤四舍五入、非互斥 gate、left truncation、subgroup subtotal 和未展示分支。
- **方案**：**一期离线，P1**。新增 `skills/biomed-paper-review/scripts/figure_consistency_forensics.py`，只消费 P2 的结构化 panel/series/observation：① `flow_conservation` 仅在父节点与子分支被标为 exhaustive + mutually_exclusive 时检查人数守恒；② `composition_sum` 仅对明确标成 100% normalized 的同一分母系列检查，容差取各标签舍入区间之和；③ `quadrant_sum` 仅对同一 parent gate 的四个互斥象限；④ `estimate_ci_geometry` 检查同尺度点估计在 CI 内、marker 位于 whisker 内；⑤ `risk_table_monotonicity` 仅在普通 KM、无 delayed entry/replenishment 时运行；⑥ `forest_weight_sum` 排除 subtotal/overall 行后按显示精度检查约 100%。输出 `figure_internal_consistency_candidate` extraction signal，`target.figure_check` 保存 `{check_type,inputs,expected_interval,observed_interval,preconditions,rule_version,figure_id,series_refs[],observation_refs[]}`；Stage 3b 产 signal，M4 判断统计语义，M5 判断图形呈现，Stage 5 聚簇。任何前置条件缺失只产 `partial_extraction` 或跳过。
- **代价**：2–4 人日；先做 percentage/count closure 与 estimate-in-CI，KM/forest/dose-response 几何检查随后。每条规则至少 5 个正例、5 个困难反例，并设自动 finding precision 门槛 ≥0.95；未达门槛只进人工队列。
- **建议优先级**：P1 应该做；这是本轮最直接的确定性 uplift 组件
- **阶段 / 归属**：一期；Stage 3b 工具产 signal，M4/M5 产 finding，不新增模块。M1 仍不产 finding。
- **契约字段**：扩展 signal type 与条件必填 `target.figure_check`，复用 observation refs；不新增第四类记录。
- **假阳性**：中高；每条规则必须由机器可核对的前置条件门控。非互斥 gate、累计 incidence、延迟入组、四舍五入、隐藏分支、subgroup subtotal 一律不自动判错。

### P5 · 用标准 Draft 2020-12 引擎验证 schema 与回流 fixture

- **问题**：`tools/validate_schemas.py` 当前是标准库 lint，没有把 fixtures 交给 Draft 2020-12 JSON Schema 引擎。`figure_record` 的 `$ref observation + allOf 新字段 + additionalProperties:false` 因此长期显示“全部通过”，但标准验证语义下没有任何带路由字段的 observation 能通过。本轮加了定向静态检查，只覆盖已知形状，仍不能证明 `if/then/contains/unevaluatedProperties` 的完整行为。
- **影响**：官方或复用方一旦用真正 schema validator，就可能拒绝项目自己的示例；这会直接击穿 30% 工程质量和 14% Skill 复用价值。
- **方案**：**一期工程门禁，P0**。增加开发期命令 `python3 tools/validate_jsonschema.py`，使用 `jsonschema>=4.18,<5` 的 `Draft202012Validator` 与本地 registry 加载 10 份 schema；逐个验证四个 report fixtures，并新增 `figure_route_merge.json`：含一条文本 observation、一条同组图 observation、一条新组图 observation、pixel panel 降级、非法点值 pixel、缺路由键、重复 id 不一致七个用例。正例必须通过，负例必须命中特定 schema path。运行时 Skill 不依赖该包；CI/提交前开发环境安装锁定版本。若比赛打包禁止 dev dependency，保留录制的标准验证输出并在 CI 镜像运行，不能把自写 lint 称为完整 JSON Schema 验证。
- **代价**：0.5–1 人日；仅开发依赖，不影响 4 GB/离线运行。
- **建议优先级**：P0 交付前必须做
- **阶段 / 归属**：一期工程基础设施；不属于 M1–M7，不进入审稿流水线。
- **契约字段**：不改生产字段；验证 P2/P3/P4 的迁移和现有 schema。
- **假阳性**：不产生稿件判断；它防止契约接受/拒绝行为与文档漂移。

## 未解决 / 需要人来定的问题

1. `references/05-figures-and-charts.md` 的负责人是否接受 P1。当前 §A.1、§A.5、§D、§F.5 与主框架冲突；本轮按禁改约束只记录，未修改该文件。
2. 是否在交付前接受 P2 的最小 schema migration。若不接受，必须删除“图表结果无损回流”的声称，并在多系列、逐时点 n 或误差棒语义不明时默认不合组。
3. Round 3 P3 的扩展 grouping context 尚未实现；P2 不应另建第二套 key_data 上下文。建议由同一 migration 同步 figure 投影与 key_data 落盘字段。
4. Round 1 P1 的 `observation_registry` 尚未实现。本轮保留现有双副本模型并固定一致性检查；若采纳 registry，P2/P4 的 `observation_refs[]` 直接落到登记表，不再复制 observation。
5. Round 1 P7 已提出“感知哈希召回 + 局部特征/RANSAC + blot 候选 + 强制人工复核”，`references/05 §F.1` 也已记录，但 schema、脚本和 fixture 均未落地。本轮不重复另提图像取证算法；应先完成 P1 的无 severity 候选边界与 P5 的 schema 门禁，再实现 Round 1 P7。当前 §F.5 把 `suspected` 候选预设为 critical，建议负责人明确改成“候选不是 finding，人工核对后再定 severity”。
6. `curve_fit` 与 `significance_markers` 目前仍保存辅助数值副本。本轮已禁止它们作为唯一审核输入，但长期应在 Round 1 P1 的 observation registry 落地后改为 `observation_refs[]`，避免同一 IC50/p 值双写漂移。
7. 本轮确认 Round 1 P2/P3 已实现为单位归一化与统计取证脚本；Round 1 P7、Round 3 P3、Round 4 P1 尚未见 schema/脚本落地。图表新组件不得自行创建外部证据层或第四类记录。
