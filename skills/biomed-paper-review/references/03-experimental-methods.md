# M3 · 实验方法合规性

**原负责人：Peter** · 状态：**一期规则库已填充（框架层代填，待 Peter 复核）**

对应会议纪要「第二层：实验方法合规性校验」。对照**领域通用实验惯例库**，
排查异常实验对象、非通用流程等需要作者额外解释的场景。

**本模块的定位边界（最容易做错的地方）**：
**不判断方法在科学上是否最优，只判断是否偏离通用惯例而未加说明。**
「这个实验设计不够好」不是 M3 的结论；「这个设计偏离常规且作者没解释为什么」才是。

**本文件依赖 `00-contracts.md`。**

---

## 1. 输入与路由

| 来源 | 用途 |
| --- | --- |
| `structured_result_v2.design` | `arms[]`（剂量/途径/周期/重复类型）、`controls`、`randomization`、`blinding` |
| `structured_result_v2.measurement.assays[]` | 每项 `{name, purpose, reference_citation}` |
| `structured_result_v2.population.subjects` | 物种/品系/细胞系/原代来源 |
| `structured_result_v2.article_design` | 路由：仅 `family ∈ {experimental, human_interventional}` 启动完整检查 |
| `sequence_identifier_inconsistent` signals | 引物、登录号、基因符号的确定性问题（`scripts/sequence_identifier_audit.py`） |
| `evaluation_matrix` | **仅**用于路由与定位证据，立 finding 前必须回查 `evidence_refs` |

`evidence_synthesis` 与 `computational` 族：只跑 §5 的试剂溯源部分（通常不适用），
其余判 `not_applicable`。

---

## 2. Assay 最低报告要素清单（本模块核心交付物）

**判据**：缺少「必报」要素 → `method_reporting_incomplete`（major）；
缺少「建议报」要素 → 同 slug 但 minor。
**每种 assay 只查它自己那一行，不要跨 assay 套用。**

| assay | 必报要素 | 建议报 | 常见缺失 |
| --- | --- | --- | --- |
| **Western blot** | 抗体来源+货号、稀释比、上样量、内参蛋白 | 转膜条件、封闭液、曝光时间 | 只写「anti-XXX antibody」无货号；无内参 |
| **qPCR** | 引物序列或货号、内参基因、定量方法（2^-ΔΔCt 等） | 扩增效率、熔解曲线、RNA 质量（RIN） | 无引物序列；内参未验证稳定性（MIQE 要求） |
| **ELISA** | 试剂盒厂商+货号、检测范围、标准曲线 | 批内/批间 CV、稀释倍数 | 无货号；未说明样本稀释 |
| **IHC / IF** | 抗体货号+稀释、抗原修复方法、阳性/阴性对照 | 定量方法（阳性细胞比例 vs 光密度）、判读是否盲法 | 无抗原修复条件；无阴性对照 |
| **流式细胞术** | 抗体 panel（荧光素+克隆号）、门控策略、同型/FMO 对照 | 补偿方案、活死细胞染色、采集细胞数 | **无门控策略图**；无 FMO 对照 |
| **MTT / CCK-8 / 细胞活力** | 接种密度、处理时长、读数波长、溶剂对照 | 复孔数、是否扣除背景 | 未说明溶剂（DMSO）终浓度 |
| **组织学（HE/特殊染色）** | 固定方式、切片厚度、染色方案、评分标准 | 判读者数量与是否盲法、每样本视野数 | 无评分标准；视野选择方式不明 |
| **测序（RNA-seq 等）** | 平台、建库试剂盒、测序深度/读长、比对软件+版本、参考基因组版本 | 质控指标、批次信息 | 无软件版本；无参考基因组版本 |
| **动物行为学** | 装置规格、测试时长、环境条件（光照/噪声）、判读是否盲法 | 适应期、测试顺序随机化 | 未说明盲法；未说明测试时间段 |
| **免疫共沉淀 / pulldown** | 抗体货号、裂解缓冲液配方、对照 IgG | 洗涤次数与强度、input 比例 | **无 IgG 对照** |

> **溯源要求**：关键试剂（抗体、化合物、细胞系）应给出**来源 + 货号/批号**。
> 只写厂商不写货号 → `reagent_traceability_incomplete`（minor）。
> RRID 格式的正确性由 `scripts/sequence_identifier_audit.py` 确定性检查。

---

## 3. 方法学引用（§2.1）

| 检查 | 判据 | slug |
| --- | --- | --- |
| 非商品化方法是否引用了方法学文献？ | `assays[].reference_citation` 为空且该方法非试剂盒标准流程 | `method_no_reference`（major） |
| 引用是否指向原始方法学文献而非综述？ | 一期只能看引文题名线索，判不准就不判 | 同上（minor） |
| 对已发表方法的改动是否说明？ | 出现 "modified from" / "adapted from" 但无改动细节 | `protocol_deviation_unexplained`（major） |

**一期做不到的**：被引文献里是否**真的**包含该方法。这需要取回原文，属二期（§8.1）。
**不得**因为「看起来像是套用了别人的方法」就判引用不当。

---

## 4. 动物实验必要性（§2.2）

`evaluation_matrix.has_animal_experiment = true` 时启动。
**这是 M3 与 M6 的分界线：是否**必要**归 M3，是否**合规/有批件**归 M6。**

### 4.1 判据表

| 判据 | 支持「必要」的线索 | 支持「必要性存疑」的线索 |
| --- | --- | --- |
| 科学问题是否需要完整生理系统？ | 涉及药代动力学、整体免疫应答、行为、器官互作、长期毒性 | 结论只涉及单一通路的分子机制，且已有细胞学证据 |
| 是否已有体外/类器官证据支撑？ | 动物实验是对体外结论的**在体验证** | 动物实验只是重复体外已证明的结论 |
| 物种/品系选择是否有依据？ | 说明了该物种在该疾病模型上的适用性 | 未说明为何选该物种；换成常规品系亦可 |
| 样本量是否为达成效能的最小量？ | 有效能分析（与 M4 联动） | 无效能分析；或组数远超必要 |
| 是否体现 3R？ | 说明了替代/减少/优化措施（与 M6 联动） | 完全未提 |

### 4.2 输出口径（**克制**）

本模块对必要性的输出一律为
**`animal_use_justification_unclear`（major）—— 「未见动物实验必要性的说明，建议作者补充」**，
**不得**输出「本研究不需要动物实验」。

理由：必要性判断高度依赖领域语境与研究目标，自动判定误报代价极高
（等于指控研究者不当使用动物）。我们能确定性判断的只有
「作者有没有说明」，不是「说明得对不对」。

**不触发的情形**：论文明确写了物种选择理由与 3R 考量 → 不报。

---

## 5. 实验设计惯例（§2.3）

### 5.1 对照设置

| 情形 | 应有的对照 | 缺失时 |
| --- | --- | --- |
| 药物/化合物处理 | 溶剂对照（vehicle，同浓度 DMSO/生理盐水） | `missing_control`（critical） |
| 基因敲低（siRNA/shRNA） | 非靶向对照（scrambled/NC） | `missing_control`（critical） |
| 过表达 | 空载体对照 | `missing_control`（critical） |
| 抗体类实验（IP/IHC） | 同型对照 IgG / 一抗省略 | `missing_control`（major） |
| 手术模型 | 假手术（sham） | `missing_control`（critical） |
| 临床干预 | 安慰剂或标准治疗 | 与 M4 联动 |

**防误报**：`controls` 字段为 `parse_failed` 或 `ambiguous` 时**不报** ——
我们没读到不等于没有（`00-contracts.md §6.4`）。

### 5.2 剂量与时间点

| 检查 | 判据 | slug |
| --- | --- | --- |
| 剂量梯度组数 | 剂量-反应研究少于 4 个非零剂量点，难以拟合曲线 | `dose_design_questionable`（major） |
| 剂量跨度 | 全部剂量集中在一个数量级内，无法覆盖 EC50 | 同上 |
| 剂量依据 | 未说明剂量选择依据（预实验/文献/MTD） | 同上（minor） |
| 时间点 | 只测单一时间点却下动力学结论 | 与 M7 联动 |
| 溶剂浓度 | 细胞实验 DMSO 终浓度 >0.5% 而未说明 | `protocol_deviation_unexplained`（minor） |

### 5.3 重复类型（高频问题）

- `arms[].replicate_type` 为 `unspecified` → `replicate_type_unclear`（major）
- 明确为 `technical` 却被当作统计学 n 使用 → **归 M4 的 `pseudoreplication`**，
  M3 只报「未区分」，不重复报统计问题

### 5.4 随机化与盲法（实验室研究）

动物实验未做随机化/盲法**本身不是缺陷**（ARRIVE 要求的是**报告**），
判据是：**做了没说，还是根本没做，还是说了没做也没给理由**。

| 状态 | 处理 |
| --- | --- |
| `reported` 且描述了方法 | 不报 |
| `not_reported` | `randomization_blinding_unreported`（minor，与 M6 的 ARRIVE 条目联动，Stage 5 会聚簇） |
| 明确写「未做」且给了理由 | 不报 |
| 明确写「未做」无理由 | 同上（major） |

---

## 6. 细胞系与试剂溯源（§2.4）

| 检查 | 判据 | slug |
| --- | --- | --- |
| 细胞系来源 | 未说明购自何处或由谁惠赠 | `cell_line_unauthenticated`（minor） |
| STR 鉴定 | 未提及 STR/短串联重复鉴定 | 同上（minor） |
| 支原体检测 | 未提及 | 同上（minor） |
| 传代次数 | 原代细胞未说明传代数 | `reagent_traceability_incomplete`（minor） |
| 已知误认细胞系 | **一期不查**（需 Cellosaurus/ICLAC），见 §8.2 | —— |

**重要边界**：一期只能查「有没有写」，查不了「写的对不对」。
不得因为某细胞系在你的记忆里可能有问题就报 —— 那需要权威库比对，属二期。

---

## 7. 与其他模块的边界

| 情形 | 归属 | 理由 |
| --- | --- | --- |
| 动物实验**是否必要** | **M3** | 方法学判断 |
| 动物实验**有无伦理批件** | **M6** | 合规判断 |
| 3R 是否体现 | **M6**（M3 在必要性判据中引用） | 伦理规范明确要求 |
| 技术重复当作 n | **M4**（`pseudoreplication`） | 统计推断问题 |
| 样本量是否足够 | **M4** | 统计效能问题 |
| 样本量是否**过大**（不必要地多用动物） | **M3** + M6 | 3R 的 Reduction |
| 方法描述前后矛盾 | **M2** | 内部一致性 |
| 方法节缺失整节 | **M2** | 章节完整性 |
| 引物序列/登录号格式错误 | 工具产 signal → **M3** 判定 | `scripts/sequence_identifier_audit.py` |

---

## 8. category slug

| slug | 说明 | severity |
| --- | --- | --- |
| `missing_control` | 关键对照缺失 | critical |
| `method_no_reference` | 非商品化方法无文献依据 | major |
| `method_reporting_incomplete` | assay 缺少必报要素（§2） | major / minor |
| `animal_use_justification_unclear` | 未见动物实验必要性说明 | major |
| `dose_design_questionable` | 剂量梯度或依据不足 | major / minor |
| `replicate_type_unclear` | 未区分生物学/技术重复 | major |
| `protocol_deviation_unexplained` | 偏离通用流程未说明 | major |
| `randomization_blinding_unreported` | 实验室研究未报告随机化/盲法 | minor / major |
| `cell_line_unauthenticated` | 细胞系来源/鉴定未报告 | minor |
| `reagent_traceability_incomplete` | 关键试剂缺来源或货号 | minor |

---

## 9. 正例 / 反例

### 9.1 `method_reporting_incomplete`（Western blot）

**该报警**：方法节写「Proteins were detected using anti-p53 antibody and
anti-GAPDH antibody」，无货号、无稀释比、无上样量 → **major**，
detail 列出缺的三项要素。

**不该报警**：写「anti-p53 (Cell Signaling, #2527, 1:1000), anti-GAPDH
(Abcam, ab8245, 1:5000); 30 μg protein per lane」→ 必报要素齐全 → **不报**。

### 9.2 `missing_control`

**该报警**：siRNA 敲低实验只有「siRNA 组 vs 未处理组」，无 scrambled 对照
→ **critical**。

**不该报警**：同实验有 NC siRNA 组 → **不报**。
`controls` 字段为 `parse_failed` 时也**不报**（我们没读到 ≠ 不存在）。

### 9.3 `animal_use_justification_unclear`（体现克制口径）

**该报警**：小鼠实验重复了论文自己体外已证明的同一分子机制，
未说明为何需要在体验证、未说明物种选择依据 → **major**，
detail 写「未见动物实验必要性的说明，**建议作者补充**」，
**不写**「本研究不需要动物实验」。

**不该报警**：论文写明「为验证该通路在完整免疫微环境下是否成立，
选用免疫健全的 C57BL/6 小鼠」→ 已说明必要性与物种依据 → **不报**。

### 9.4 `dose_design_questionable`

**该报警**：剂量-反应实验只设 1、2、4 μM 三个点（跨度不足一个数量级），
却报告 IC50 拟合结果 → **major**。

**不该报警**：设 0.1、1、10、100 μM 四个点覆盖两个数量级 → **不报**。

### 9.5 `cell_line_unauthenticated`（体现一期边界）

**该报警**：使用 HeLa 细胞，未说明来源、未提 STR 鉴定 → **minor**。

**不该报警**：写明「HeLa (ATCC CCL-2), STR-authenticated, mycoplasma-free」
→ **不报**。
另：**不得**因为某细胞系「可能是误认细胞系」就报 —— 那需要 ICLAC 比对，属二期。

---

## 10. TODO（一期）

- [x] 填充 §2 各 assay 最低报告要素清单
- [x] 填充 §4 动物实验必要性判据表与克制口径
- [x] 填充 §5 实验设计惯例（对照/剂量/重复/盲法）
- [x] 与 M6 划清边界（§7）
- [ ] **请 Peter 复核**：各 assay 必报要素是否符合他的实操经验，有无遗漏的高频 assay
- [ ] 用 `tools/baseline_probe.py` 逐条探针：本文件哪些检查是裸模型**本来就会提**的？
      那些应当简化甚至删除（贡献零 uplift 还占 token）
- [ ] 在 `datasets/` 语料上统计各 slug 的触发率与误报率
- [ ] 补充中医药、器械类研究的方法学要素（当前以生物医学基础实验为主）

---

## 11. 二期扩展（本期不实现，规则先写下）

一期只看「有没有引用方法学文献、有没有写试剂来源」，二期核验这些引用与来源**是否成立**。

### 11.1 方法学引用核验

- 数据源：Crossref / PubMed（经 X1 外部证据层）
- 检查：被引文献是否真实存在？是否已撤稿？**是否真的包含该方法**？
  论文声称「按文献 X 方法执行」但 X 用的是另一套流程 —— 一期完全查不出。
- 新增 slug：`method_citation_mismatch`（major）

### 11.2 试剂与细胞系核验

- 数据源：Cellosaurus / ICLAC / RRID Antibody Registry
- 检查：细胞系是否在 ICLAC 误认列表中？抗体 RRID 是否存在、有无已知特异性问题？
- 新增 slug：`cell_line_misidentified`（critical）、`antibody_validation_issue`（major）
- **假阳性控制**：同名细胞系可能有多个来源；只有 accession 精确匹配才判定。

### 11.3 惯例库外部化

一期惯例库靠人工梳理；二期可按研究方向实时检索同类论文的方法参数分布，
判断本文的剂量/时长/n 是否落在常规区间外。
输出应为「偏离同类研究常规区间 + 分布位置」这类**事实描述**，
**不要**直接判「方法错误」。新增 slug：`parameter_outside_norm`（minor）。
