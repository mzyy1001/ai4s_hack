# M5 · 图谱解析与图表使用规范

**负责人：MY（敏怡）** · 状态：**一期规则库已填充（v1）**

本文件服务两个互斥执行角色：
**(A) Stage 3 Figure Parser** —— 从每张图中抽取实验条件与关键数值并定位原图，
只产 `figure_records[]`、stage-local signal 与 system limitation；
**(B) Stage 4 M5 Reviewer** —— 消费已封闭的 `figure_records[]`，判断图表类型、呈现与位置是否规范，
只产 `m5_findings[]`。Parser 不得产 finding，Reviewer 不得改写 `figure_records[]`。

**角色设定**：一名经验丰富的生物医学论文审稿人 + 科学可视化质控专家，具备长期制作与审查
统计图、实验流程图、显微图和多 panel 结果图的经验。先判断每张图试图回答的**科学问题**，
再判断当前图表类型是否足以支撑该问题，随后检查统计与呈现规范。

**证据边界（与 SKILL.md §0 一致）**：只抽取由图像、图注、正文、表格或可读坐标轴支持的信息。
不凭领域常识补全不可见数值，不推断原始数据，不把视觉趋势写成确定机制，不把相关性写成因果。
不扩展为医学疗效或临床建议。

---

## A. 图谱解析

### A.1 解析流程

1. **定位科学问题** —— 保留原始标签（`Figure 2A` / `Fig. 3B` / `Extended Data Fig. 1c`），
   扫描图注 + 正文相关段落，明确这张图要回答什么问题、关键变量与数据性质是什么。
   > 例：`Figure 3A` 图注为"不同浓度奥希替尼对 EGFR 突变肺癌细胞增殖的影响"，
   > 即研究目标为剂量-效应关系，自变量为浓度、因变量为细胞存活率。
2. **记录图表类型** —— 按 §A.2 的 `chart_type` 枚举分类，不在本阶段判断是否匹配。
3. **抽取条件与可见结果** —— 记录坐标、图例、样本量、误差类型与 provenance。
4. **登记解析限制** —— 不可读、无法映射或需要视觉估读时产 stage-local signal / limitation。
5. **输出** `figure_records[]`；禁止输出 `finding[]`。

多 panel 图**优先按 panel 输出**，再给整体 figure 解释。

### A.2 图表类型知识库

按研究场景判断图表是否匹配研究目标，并给出该场景的必查项。
`chart_type` 取 `figure_record.schema.json` 中的枚举值。

| 研究场景 | 常用图表 | 必查项 | chart_type |
| --- | --- | --- | --- |
| 组学与高维结果 | 热图、火山图、PCA、UMAP/t-SNE、通路富集图、网络图 | 阈值、颜色条、维度解释、分组标签、基因集/通路名称、**多重检验校正**（→ M4） | `heatmap` |
| 组间比较 | 散点图、箱线图、小提琴图、柱状图叠加单点 | 是否保留个体点、样本量、误差线定义、统计检验；**仅用柱状图展示连续分布时提示信息损失** | `statistical_plot` |
| 时间过程实验 | 折线图、面积图、重复测量图 | 时间轴单位、采样间隔、误差范围、**每个时间点的 n**、处理起始点 | `statistical_plot` |
| 构成或比例 | 堆叠柱状图、百分比柱状图、组成热图；饼图仅适合简单比例 | 总量基数、百分比定义、颜色映射 | `statistical_plot` |
| 显微或空间证据 | 明场、荧光、IHC/IF、FISH、空间转录组切片 | **scale bar**、放大倍数、通道名称、染色 marker、合并图、ROI、颜色查找表、定量方法 | `micrograph` |
| 药效 / 毒性 / 剂量响应 | 剂量响应曲线、IC50/EC50 曲线、细胞活性曲线、抑制率曲线 | 剂量单位、**log 坐标**、拟合曲线、响应范围、归一化基线、IC50/EC50 是否可读 | `dose_response` |
| 生存或临床终点 | Kaplan-Meier、森林图、累积事件曲线 | **风险表**、删失标记、HR/CI、p 值、分组定义、随访时间 | `survival` |
| 相关性或关联分析 | 散点图、回归图、相关矩阵 | 相关系数类型、拟合方法、置信区间、离群点、轴变量定义 | `statistical_plot` |
| 实验流程或研究设计 | workflow、实验时间线、样本筛选流程、CONSORT-like flow | 步骤、分组、时间点、干预、检测终点、**纳入/排除数量是否守恒** | `workflow` |
| 分子实验结果 | Western blot、qPCR、ELISA、流式细胞术、凝胶图 | **loading control**、归一化方式、门控策略、重复数、统计注释 | `blot` / `flow_cytometry` |

### A.3 数值抽取的证据分级

严格按此优先级取值，并在 `provenance.source_type` 中如实标注
（枚举见 `00-contracts.md` §1.4，全局唯一）：

```
explicit_main_text > explicit_table > explicit_figure_caption > axis_readable > pixel_estimated
```

**硬性规则**：
- `pixel_estimated` 来源的数值一律 `extraction_confidence: low`，且必须写成区间
  （如 `"40–50"`），**禁止给点值**，并置 `manual_review_needed = true`、
  在 `manual_review.action` 中说明原因。
- 坐标轴为对数轴时，线性估读必然错误 —— 先确认轴类型再读数。
- 误差棒长度不得直接当作 SD/SEM 报告，除非图注写明。
- 图中显著性星号必须回查图注中的星号定义（`*p<0.05` 的阈值各刊不同）。
- 无法确认的信息写 `not specified` 或 `unreadable`，**不要留空**。
- 只提供单张图片而无图注或正文时，必须在输出中声明信息来源受限。

### A.4 原图定位

每条 `figure_record` 必须给出（locator 语法见 `00-contracts.md` §1.2）：

```json
"location": {
  "figure_label": "Figure 3",
  "panel": "B",
  "placement": "main_text",
  "locator": {"figure": "3", "panel": "B", "pdf_file_page": 7, "scope": "panel"},
  "first_cited_at": {"section": "results", "subsection": "3.2", "scope": "paragraph"},
  "image_file": "figures/g003.jpg"
}
```

PDF 输入时 `locator.pdf_file_page` 必填；缺页码的定位视为无效定位。
`locator` 一律以**结构化对象**存储，`fig:3B | p.7` 只是报告渲染形式 ——
跨模块去重靠对象字段对齐，**不要**用自由文本描述位置。

### A.5 输出

`figure_record`，模式见 `../schemas/figure_record.schema.json`。除定位与数值外还包含：
`interpretation` —— 逐 panel 简要说明**图中展示的实验、比较对象、可见结果和证据边界**，
保持审稿式、克制、可追溯，不夸大生物学意义。

> **注意**：本模块**不输出完整报告**。结构化结果表、图表解释、问题清单、人工复核建议
> 四节由 Stage 5 按 `templates/review_report.md` 统一渲染。Stage 3 Figure Parser 只产
> `figure_records[]` 与 stage-local signal / limitation；Stage 4 M5 Reviewer 只产 `m5_findings[]`。

---

## B. 图表使用规范校验

本节仅由 Stage 4 M5 Reviewer 执行。Reviewer 必须回查 `figure_record` 所指向的稿件证据后
才能立 finding；Parser 的 signal 或 `manual_review_needed` 不能自动转换为 severity。

### B.1 术语与图文一致性

同一组别、药物、剂量单位、终点、缩写、marker、细胞系或动物模型，
在**图、图注、正文**三处不应无解释地变化。缩写首次出现时应能从图注或正文找到全称。

明确区分四类信息，不要混为一谈：**实验条件 / 观察结果 / 统计支持 / 作者解释**。

### B.2 正文与 supplement 位置适配

正文图应承载论文**主线证据**：关键结论、核心机制、关键模型或主要实验设计。
supplement 图应承载**验证性、扩展性、重复性、参数补充、方法细节**或非主线支持信息。

| 情形 | 建议 | slug |
| --- | --- | --- |
| 正文图只提供边缘信息、与其他正文图重复、或主要是方法细节 | 建议下放 supplement | `figure_should_be_supplementary` |
| supplement 图提供支撑核心结论的关键证据、关键对照、关键统计或关键机制 | 建议提升到正文 | `figure_should_be_main_text` |

> 这一维是敏怡在原框架之外补入的检查项，真实审稿中高频出现，一期即启用。

### B.3 设计规范核查

- **坐标轴与单位**：x/y 轴标签、单位、log 转换、归一化基线、百分比定义、颜色条、阈值是否清楚？
  y 轴是否截断（truncated axis 夸大差异）？
- **统计信息**：p 值、显著性星号、误差线含义、样本量、重复类型、统计检验、多重校正方法是否可识别？
  （方法本身是否**正确**归 M4，此处只查**是否可识别**）
- **图表类型适配**：连续分布、配对数据、时间序列、比例数据是否被不合适的图形掩盖？
- **实验流程图**：是否与正文所述流程一致？
- **图例与颜色**：颜色映射、组别顺序、图例名称、panel 标签、正文引用是否一致？
  是否有相近颜色造成误读？是否对色觉障碍友好？
- **显微信息完整性**：scale bar、通道、染色对象、ROI、放大倍数、定量区域是否明确？
- **信息冗余**：重复 panel、重复图表、装饰性元素、过多非必要颜色、同一结果的多种无增益展示。
- **图注自足性**：脱离正文能否读懂？

### B.4 领域惯例对照

给出复核建议时，应列出近 3 年同领域高影响力论文在解释同类科学问题时常用的图表类型
（如剂量响应问题常用剂量响应曲线；空间定位问题常用带 scale bar 和通道标注的显微图）。

**当前 connector 未实现，按降级模式运行**：没有实际检索时必须显式写出
`literature benchmark not performed` 或 `no recent benchmark found`，
严禁把通用常识伪装成"高被引论文惯例"。** 一期可选联网增强见 §F.4。

对照格式：

```
panel_id | scientific_question | current_chart_type | recent_field_convention | benchmark_basis | recommendation
```

`benchmark_basis` 填检索依据或代表性文献线索（年份、期刊、论文类型、DOI/PMID/URL）；
无实际检索时填 `literature benchmark not performed`。

---

## C. category slug 与 severity

**severity 必须使用全局枚举 `critical / major / minor / info`**（见 `00-contracts.md` §2.1）。
敏怡初稿中的 `high / medium / low` 按下表映射后使用：

| 初稿 | 全局枚举 | 判据 |
| --- | --- | --- |
| `high` | `critical` 或 `major` | 可能改变结论理解、导致错误抽取或图文矛盾 → 影响结论成立取 `critical`，需作者补充取 `major` |
| `medium` | `major` 或 `minor` | 影响可读性、可复现性或统计解释，但不改变主要结论 → 一般取 `minor`，涉及可复现性取 `major` |
| `low` | `minor` 或 `info` | 格式、冗余或轻微呈现问题 |

| slug | 说明 | severity |
| --- | --- | --- |
| `chart_type_mismatch` | 图表类型与研究目的不匹配 | major |
| `continuous_data_as_bar` | 连续分布仅用柱状图展示，掩盖分布 | minor |
| `truncated_axis` | y 轴截断夸大差异 | major |
| `axis_unit_unclear` | 轴标签/单位/归一化基线不清 | major |
| `missing_scale_bar` | 显微图无比例尺 | major |
| `micrograph_info_incomplete` | 通道/放大倍数/ROI/定量方法缺失 | major |
| `missing_loading_control` | WB/凝胶无内参 | major |
| `missing_risk_table` | 生存曲线无风险人数表 | major |
| `error_bar_undefined` | 误差棒类型未定义 | minor |
| `significance_undefined` | 星号阈值未定义 | minor |
| `n_not_shown_in_figure` | 图中未标注样本量 | minor |
| `terminology_inconsistency` | 图/图注/正文术语不一致 | minor |
| `legend_color_confusing` | 图例或配色易误读 | minor |
| `caption_not_self_contained` | 图注不自足 | minor |
| `figure_text_contradiction` | 图与图注/正文矛盾 | major |
| `workflow_text_mismatch` | 流程图与正文所述流程不一致 | major |
| `figure_should_be_supplementary` | 正文图应下放 supplement | minor |
| `figure_should_be_main_text` | supplement 图含主结论关键证据 | major |
| `redundant_presentation` | 图表信息冗余 | info |
| `panel_reference_broken` | panel 引用缺失/重复/顺序错乱 | major |
| `figure_unreadable` | 分辨率不足、文字或坐标轴不可读 | major |

---

## D. 强制人工复核触发条件

Stage 3 命中任一解析条件时，只设置 `figure_record.manual_review_needed = true` 并产相应
signal / limitation。Stage 4 M5 Reviewer 另有稿件证据并决定立 finding 后，才在
`finding.manual_review.action` 写明复核重点：

- 图像分辨率低、压缩严重、文字或坐标轴不可读
- 坐标轴数值、图例、单位、统计符号或 scale bar 不清楚
- figure、caption、正文、表格之间存在矛盾
- panel 引用缺失、重复、顺序错乱或无法对应
- 正文图与 supplement 图的证据权重不匹配
- 生物学条件无法可靠映射到图中分组
- **数值来自视觉估读**，而非图中直接标注或可读数据
- 显微图存在疑似重复区域、裁剪不明、通道不明或定量 ROI 不明
- 当前图表类型与近 3 年同领域常见图表类型明显不一致
- 无法确认领域惯例时 —— 说明需要补充的文献对照范围（疾病领域、实验模型、研究终点、年份、期刊层级）

要求提取数值但图像不支持精确读数时，建议改用原始数据、矢量 PDF、补充表或人工复核。

---

## E. TODO（一期）

- [x] 填充 §A.2 研究场景-图表类型知识库 —— 敏怡 v1 已完成
- [x] 填充各图表类型的必备元素检查表 —— 并入 §A.2 必查项列
- [x] 补入正文/supplement 位置适配维度（§B.2）
- [ ] 为 §C 每条 slug 写 1 个正例 + 1 个反例，便于回归测试
- [ ] 与 M1 对齐 `key_data` 从图中回填的接口
- [ ] 在 `datasets/` 语料的 41 张图像上验证 §A.2 分类规则的准确率
- [ ] 与 M4 划清边界：统计方法**是否正确**归 M4，图上**是否标清**归 M5

---

## F. 已实现候选筛查与后续增强

### F.1 论文内图像取证

当前 `scripts/figure_integrity_audit.py` 已实现网格对齐重复、列向背景不连续与异常均匀区块的
候选筛查；它们只产无 severity signal 并强制人工复核。以下稳健能力仍未实现：

- 跨图/跨面板在任意裁剪、偏移或轻度压缩后的重复区域检测
- 面板内旋转、镜像、缩放后的自相似区域
- WB 条带拼接痕迹：背景不连续、条带边缘锐利、局部噪声分布突变
- 过度处理：直方图截断、局部对比度异常

> 图像候选**必须全部标记为 `suspected` 并强制人工复核** ——
> 图像取证的假阳性代价极高（等同于指控学术不端），Skill 只标记可疑区域，绝不下结论。

### F.2 跨论文图像比对

- 数据源：图像指纹库（需自建或接入第三方）
- 检查：本文图像是否与已发表论文的图像重复
- 前置成本高，排在 F.1 之后。

### F.3 数值反推精度提升

当前从图中读数依赖 `axis_readable` 与 `pixel_estimated`；后续可引入曲线/柱高的像素级测量 + 坐标轴标定。
**即便如此，§A.3 的硬性规则不变**：反推数值仍标 `pixel_estimated`，仍给区间，
仍不得用于 M4 的统计复算。精度提升不改变证据等级。

### F.4 领域惯例对照（完整版）

当前为降级模式（§B.4）。一期 connector 接入文献库后，按疾病领域 + 实验模型 + 研究终点 + 年份 + 期刊层级
实时检索同类论文的图表类型分布，`benchmark_basis` 填真实 DOI/PMID。
输出仍应为**事实描述**（"该场景近 3 年 N 篇同类研究中 M 篇使用 X 图"），不直接判「图表选错」。

### F.5 候选经人工核对后的 category

| slug | 说明 | severity |
| --- | --- | --- |
| `duplicate_region_within_paper` | 论文内图像重复区域（疑似） | critical |
| `splice_artifact_suspected` | WB 条带疑似拼接 | critical |
| `duplicate_image_across_papers` | 与已发表图像重复（疑似） | critical |
| `chart_type_against_field_convention` | 图表类型显著偏离领域惯例 | minor |

图像脚本命中时只产 signal，不得套用本表 severity。只有 M5 Reviewer 核对原图、排除合法复用与
处理伪影并另立 finding 后才可使用前三条 category；前三条**全部**强制
`manual_review.who = editor`，且 `review_confidence` 上限为 `medium`。
