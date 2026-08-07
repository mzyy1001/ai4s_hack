# M3 · Experimental Methods Compliance (v2 — Rebuilt)

**原负责人：Peter** · 状态：**v2 完整重建（2026-08-08）**

**核心原则（与 v1 的根本区别）**：
先理解每个步骤在做什么，再评判它做得对不对。
不允许跳过 Phase 1（步骤解构）直接套清单。

**本文件依赖 `00-contracts.md`。**

---

## 0. 执行顺序（不可颠倒）

```
Phase 1:  步骤解构  → 理解每个步骤的目的、输出与实验角色（step_role）
Phase 1b: 步骤角色要求核查 → 每类角色有自己的基础要求，逐项检查
Phase 2:  流程连接验证 → 步骤间能否合理衔接
Phase 3:  生物实体核查 → 实体的已知属性与交互是否合理
Phase 4:  实验逻辑核查 → 剂量、结局、干扰因素、对照
Phase 5:  汇总 → 严重性标定与 finding 产出
```

**不允许在 Phase 1 完成前立任何 finding。**
所有 finding 只在 Phase 5 产出；Phase 1–4 只产内部候选账本条目。

**Phase 1b 与 Phase 4 的分工**：
Phase 1b 检查**单步骤本身**是否满足其角色的基础要求（可控性、可重复性）；
Phase 4 检查**整体实验设计**的逻辑合理性（假设链、干扰因素、对照完整性）。
同一缺失可能在两个 Phase 都被发现 — Phase 5 合并时只产一条 finding，取最高 severity。

---

## Phase 1 · 步骤解构

### 1.1 执行方式

按**方法节的叙述顺序**，将每一个操作单元提取为原子步骤，并填写如下记录：

```
step_id        : S01, S02, ...（全文唯一递增）
text_excerpt   : 方法节原文引用（≤150字）
skill_type     : 见 §1.2 Lab Skill 分类表
step_role      : 见 §1.3 Step Role 分类（新增）
protocol_source: 见 §1.4 协议来源层级
step_purpose   : 这一步产生了什么（输出物/状态）
step_input     : 需要什么前置产物（来自哪个前置步骤）
role_req_status: PASS / PARTIAL / FAIL / UNKNOWN（Phase 1b 填写）
notes          : 任何需要在后续 Phase 中检查的线索
```

**粒度原则**：
- 一个操作单元 = 一种方法对一种样本的一次独立处理。
- 同一试剂的平行处理可合并为一条，但条件不同时必须分条。
- 不拆到「吸管移液」级；保留到「离心 → 收集上清」级。

### 1.2 Lab Skill 分类表

| code | 类别 | 典型步骤举例 |
|------|------|------------|
| `CELL_CULTURE` | 细胞培养与维持 | 解冻、传代、冻存、培养基更换 |
| `CELL_TREAT` | 细胞给药/处理 | 药物加入、siRNA 转染、慢病毒感染、辐射 |
| `CELL_VIABILITY` | 细胞活力检测 | CCK-8、MTT、MTS、台盼蓝、LDH |
| `COLONY_FORM` | 克隆形成/增殖 | 软琼脂克隆、平板克隆、BrdU/EdU 标记 |
| `APOPTOSIS_DETECT` | 细胞死亡/凋亡检测 | Annexin V/PI、AO/EB、TUNEL、Caspase 活性 |
| `PROTEIN_EXPR` | 蛋白表达检测 | Western blot、ELISA、流式胞内染色 |
| `PROTEIN_INTERACT` | 蛋白互作 | Co-IP、pulldown、proximity ligation |
| `NUCLEIC_ACID` | 核酸分析 | PCR、qPCR、RT-PCR、RNA-seq、ChIP-seq |
| `MICROSCOPY` | 显微成像 | 共焦、荧光、明场、电镜、组织切片 |
| `HISTOPATH` | 组织病理 | HE 染色、Masson 染色、IHC、特殊染色、评分 |
| `FLOW_CYTOM` | 流式细胞术 | 表面标记、DNA 含量、多色 panel |
| `ANIMAL_MODEL` | 动物模型建立 | 手术、注射造模、药物诱导、基因工程 |
| `ANIMAL_BEHAV` | 动物行为学 | OFT、EPM、MWM、FST、NOR、旷场 |
| `BIOCHEM_ASSAY` | 生化活性检测 | SOD/CAT/POD 活性、MDA、ATP、ROS |
| `CHROMATOGRAPHY` | 色谱分析 | HPLC、LC-MS、GC-MS |
| `IN_SILICO` | 计算/生信 | 分子对接、靶点预测、通路分析、网络药理 |
| `SAMPLE_PREP` | 样品制备 | 裂解、离心、研磨、固定、包埋、切片 |
| `ADMIN_ROUTE` | 给药途径 | 灌胃、IP 注射、IV 注射、吸入、经皮 |
| `CLINICAL_PROC` | 临床操作 | 抽血、活检、影像、问卷、体格检查 |
| `OTHER` | 其他 | 无法归入上述类别；在 notes 详述 |

### 1.3 Step Role 分类（每个步骤必须指定一个主要角色）

每个步骤除了属于某个 `skill_type` 之外，还有一个**实验角色（step_role）**。
step_role 决定该步骤需要满足哪些基础要求（见 Phase 1b）。

| role | 含义 | 典型示例 |
|------|------|----------|
| `INTERVENTION` | 施加实验变量 —— 处理、给药、基因操作、手术、刺激。**是结果差异的直接来源** | 给药（IP/口服/雾化）、siRNA 转染、CRISPR 编辑、OVA 致敏、模型造模 |
| `DETECTION` | 测量/定量一个结局指标 —— 产生原始数值或图像数据。**是结论的直接依据** | Western blot、ELISA、qPCR、CCK-8、流式、行为学评分、病理评分 |
| `PROCESSING` | 对样品进行不产生结局数据的中间转化 —— 必须对所有组均匀执行 | 组织裂解、离心、RNA 提取、石蜡包埋、切片、蛋白定量 |
| `VALIDATION` | 确认模型/试剂/步骤的有效性 —— 是「继续推进」的前提 | 造模成功性评估（行为表现）、转染效率检测、细胞支原体检测、阳性对照组效果验证 |
| `CALIBRATION` | 为 DETECTION 步骤提供定量参照 —— 没有 CALIBRATION，DETECTION 只能给出相对值 | ELISA 标准曲线、WB 内参蛋白、流式 FMO 对照、组织学阳性对照切片 |
| `ANALYSIS` | 数据处理与统计推断 —— 将原始数值转化为结论 | ImageJ 定量、GraphPad 统计、评分系统、图像阈值分割 |

**一个步骤可以同时承担多个角色**（如 ELISA 标准曲线既是 `CALIBRATION` 也是 `DETECTION` 的一部分）；
此时取**主要角色**，在 notes 里注明附加角色。

**关键规则**：
- 每个 `DETECTION` 步骤必须能找到对应的 `CALIBRATION` 步骤（或在同一步骤内）。
- 每个 `INTERVENTION` 步骤必须能找到对应的 `INTERVENTION` 对照条件。
- 每个 `VALIDATION` 步骤必须有预先定义的成功/失败标准。
- 上述对应关系缺失 → 候选账本标记 `ROLE_REQ_MISSING`。

---

### 1.4 协议来源层级（优先级从高到低）

对每个 step，依次尝试以下层级，命中即记录并停止向下查找：

| 层级 | 来源 | 记录方式 |
|------|------|----------|
| **L1** | 方法节明确引用的方法学文献（"按文献 [X] 方法"） | 引用编号；X1 可核验该文献是否包含该方法 |
| **L2** | 商业试剂盒/仪器的标准流程（"按说明书"） | 厂商+货号；若仅写厂商无货号 → 记入候选账本 |
| **L3** | 领域公认标准协议（MIQE/ARRIVE/CONSORT 等） | 标准名称与版本 |
| **L4** | 论文自述流程（方法节内已自洽描述） | 摘录关键参数 |
| **L5** | 无来源可溯 | 标记 `PROTOCOL_MISSING`，记入候选账本 |

**L5 不自动产 finding**；是否构成问题取决于步骤的关键程度（Phase 5 判断）。

---

---

## Phase 1b · 步骤角色要求核查

完成 Phase 1 步骤表后，**对每个步骤**按其 `step_role` 核查下表中的基础要求。
每条要求的状态填入 `role_req_status`（PASS / PARTIAL / FAIL / UNKNOWN）。
**FAIL 和 PARTIAL 直接进入候选账本**，不自动产 finding（Phase 5 判 severity）。

---

### 1b.1 `INTERVENTION` 的基础要求

一个 INTERVENTION 步骤是受控实验的"变量"。受控要求是：**改变一个变量，保持其余不变。**

| 要求 | 检查方式 | 失败标记 |
|------|----------|----------|
| **并行对照存在** | 是否有一个同条件但省略/替代该变量的对照组与该步骤同时进行？（溶剂对照、空载体对照、假手术、生理盐水组） | `MISSING_PAIRED_CONTROL` |
| **变量唯一性** | 同一步骤中是否同时改变了多个变量（如同时改变剂量和给药途径，却没有拆开的单变量组）？ | `CONFOUNDED_VARIABLE` |
| **剂量/浓度/时长/途径全部记录** | 四项缺少任何一项 | `INTERVENTION_UNDERSPECIFIED` |
| **所有组操作者一致** | 不同组是否由不同人员或不同批次处理而未说明？ | `OPERATOR_BATCH_UNREPORTED`（对动物/临床研究更关键） |
| **随机分配** | 受试者/样本是否随机分配到各干预组（或说明了无法随机化的理由）？ | `RANDOM_ASSIGNMENT_MISSING` |

---

### 1b.2 `DETECTION` 的基础要求

一个 DETECTION 步骤是受控实验的"读数"。可重复性要求是：**同样的样本多次检测应得到一致的数值。**

| 要求 | 检查方式 | 失败标记 |
|------|----------|----------|
| **CALIBRATION 步骤配对** | 同一检测 run 中是否有对应的 `CALIBRATION` 步骤（内参、标准曲线、阳性对照）？ | `CALIBRATION_MISSING` |
| **可重复性证据** | 是否报告了技术重复（复孔/复管）数量或批内 CV？ | `REPRODUCIBILITY_UNREPORTED` |
| **客观性或盲法** | 若检测结果依赖主观判断（病理评分、行为计时、条带判读），是否说明盲法或算法化评判？ | `SUBJECTIVITY_UNCONTROLLED` |
| **定量标准预定义** | 截断值/评分阈值/计数准则是否在执行前定义（非数据驱动地设定）？ | `QUANTIFICATION_CRITERIA_UNDEFINED` |
| **检测范围覆盖** | 被测物的预期浓度/信号范围是否在检测方法的线性范围内（标准曲线覆盖，凝胶分辨率覆盖目标分子量）？ | `DETECTION_RANGE_CONCERN` |

---

### 1b.3 `PROCESSING` 的基础要求

一个 PROCESSING 步骤本身不产数据，但其不一致会给不同组引入系统偏差。
均匀性要求是：**所有组的样品必须经过完全相同的处理历史。**

| 要求 | 检查方式 | 失败标记 |
|------|----------|----------|
| **所有组同时/同批处理** | 是否描述了各组样品同批处理？还是存在批次分离（如不同天裂解、不同人切片）？ | `BATCH_EFFECT_UNCONTROLLED` |
| **关键参数记录** | 时间（孵育时长）、温度、速度（离心）、缓冲液成分是否记录？ | `PROCESSING_UNDERSPECIFIED` |
| **样品稳定性** | 从前一步骤到本步骤的间隔时间是否在被测分析物的稳定窗口内（特别是蛋白质、RNA、细胞因子）？ | `STABILITY_WINDOW_VIOLATED` |
| **差异处理缺席** | 是否存在某些组接受了额外处理步骤而其他组没有（如溶剂组额外离心）？ | `DIFFERENTIAL_PROCESSING` |

---

### 1b.4 `VALIDATION` 的基础要求

一个 VALIDATION 步骤是"通行证"。没有它，就无法确认后续测量的前提是否成立。

| 要求 | 检查方式 | 失败标记 |
|------|----------|----------|
| **成功标准预定义** | 成功/失败的判定标准是否在方法节或已引文献中明确？（如"≥5次/3分钟咳嗽即视为造模成功"） | `VALIDATION_CRITERIA_UNDEFINED` |
| **全组均等应用** | 验证步骤是否对所有组（包括对照组）均等执行？ | `VALIDATION_SELECTIVELY_APPLIED` |
| **失败后处置说明** | 如果验证失败，该动物/样本如何处理（排除？补充？）？ | `VALIDATION_FAILURE_UNADDRESSED` |
| **验证结果被报告** | 验证步骤的结果是否在结果节或方法节中呈现（而不是只在方法里声明了验证程序）？ | `VALIDATION_RESULT_UNREPORTED` |

---

### 1b.5 `CALIBRATION` 的基础要求

一个 CALIBRATION 步骤是 DETECTION 结果的"参照系"。没有参照系，数值就没有绝对意义。

| 要求 | 检查方式 | 失败标记 |
|------|----------|----------|
| **与 DETECTION 同 run** | 校准步骤是否在与被测样品完全相同的实验 run 中执行？（跨 run 使用同一标准曲线是常见错误） | `CALIBRATION_NOT_CONCURRENT` |
| **范围覆盖** | 标准曲线/参照范围是否覆盖了被测样品的预期浓度/信号范围？ | `CALIBRATION_RANGE_INSUFFICIENT` |
| **参照物来源记录** | 标准品/参照抗体/阳性对照的来源、浓度、批号是否记录？ | `CALIBRATION_SOURCE_MISSING` |
| **线性区使用** | 仅在标准曲线线性范围内插值（不在范围外外推）？ | `EXTRAPOLATION_CONCERN` |

---

### 1b.6 `ANALYSIS` 的基础要求

一个 ANALYSIS 步骤将数字转化为结论。透明性要求是：**他人可以用相同规则复现相同结论。**

| 要求 | 检查方式 | 失败标记 |
|------|----------|----------|
| **软件+版本记录** | 分析软件名称与版本是否记录？ | `SOFTWARE_VERSION_MISSING` |
| **参数/阈值记录** | ImageJ 阈值、分割参数、截断值等是否记录？ | `ANALYSIS_PARAMETER_UNDEFINED` |
| **盲法（主观分析）** | 若分析步骤涉及主观判断（如病理切片评分），执行者是否对组别设盲？ | `SUBJECTIVITY_UNCONTROLLED` |
| **多评分者一致性** | 若多人参与评分，是否报告了评分者间一致性（Cohen's κ 或 ICC）？ | `INTER_RATER_UNREPORTED` |
| **预设而非数据驱动** | 分析参数是否在看到数据前预先定义（而非调整参数直到结果"好看"）？ | `POST_HOC_PARAMETER_TUNING` |

---

### 1b.7 Phase 1b 汇总原则

- 对每个步骤，将所有相关要求过一遍，在 `role_req_status` 中填写：
  - `PASS`：所有适用要求均满足
  - `PARTIAL`：部分满足，部分未报告（非致命）
  - `FAIL`：至少一条关键要求明显违反
  - `UNKNOWN`：信息不足以判断（方法节表述模糊）
- FAIL / PARTIAL 的具体要求条目 → 进入候选账本，带标记代码（`CALIBRATION_MISSING` 等）
- 在 Phase 5 汇总时，这些候选与 Phase 2–4 的候选一起接受 severity 标定
- **防误报原则**：要求未报告 ≠ 要求未满足。只有「确认缺失」才进候选；「描述不清」先入 UNKNOWN，不立 finding

---

## Phase 2 · 流程连接验证

完成 Phase 1 步骤表后，**按 step_id 顺序**检查每对相邻步骤（Sn → Sn+1）：

### 2.1 连接合理性检查

| 检查项 | 判据 | 候选账本标记 |
|--------|------|------------|
| **输出-输入匹配** | Sn 的 `step_purpose`（输出）是否是 Sn+1 的 `step_input`（所需输入） | `FLOW_BREAK` |
| **样本完整性** | 样品在 Sn 和 Sn+1 之间是否经历了未描述的处理步骤（如洗涤、离心、转移） | `MISSING_INTERMEDIATE` |
| **时序合理性** | 时间节点（培养时间、冷冻时间、处理间隔）是否符合生物学上的合理范围 | `TIMELINE_ANOMALY` |
| **试剂兼容性** | Sn 中引入的试剂是否与 Sn+1 的反应条件兼容（如 DMSO 溶剂与后续水相反应） | `REAGENT_CARRY_OVER` |
| **平行性** | 当多组样品同时处理时，操作是否能真正并行（单人操作的时间窗口是否现实） | `PARALLELISM_CONCERN` |

**重要：FLOW_BREAK 是最高优先级候选。** 一个步骤如果其输出无法成为下一步的有效输入，整个实验链就断裂了。

### 2.2 整体流程完整性

- 实验是否有明确起点（动物/细胞/样本来源）？
- 实验是否有明确终点（检测方法与被测物）？
- 主要结局指标（primary endpoint）是否在流程中有对应的检测步骤？
- 副结局指标的检测步骤是否也在流程中？

---

## Phase 3 · 生物实体核查

对方法节中出现的所有生物/化学实体，进行基础知识层面的核查。
**这一层检查的是「专家的常识」，不需要数据库查询即可识别大多数问题；
X1 层提供数据库确认。**

### 3.1 动物/生物物种核查

| 检查项 | 关注点 | 典型错误 |
|--------|--------|----------|
| **物种-模型匹配** | 该物种/品系是否适合该疾病模型？ | 用 BALB/c（Th2 倾向）做需要 Th1 反应的模型；C. elegans 用于哺乳动物专用疾病 |
| **年龄/性别-研究类型匹配** | 幼年/老年/雌雄是否符合研究目的？ | 激素相关研究未区分性别 |
| **物种-药物反应** | 该物种对所用药物/化学品是否有已知的特殊反应或代谢差异？ | 猫对乙酰氨基酚极度敏感；豚鼠对组胺高度反应 |
| **物种-行为特性** | 物种的正常行为特征（运动模式、社会性等）是否被正确理解？ | C. elegans 游泳（液体中）vs 爬行（琼脂上）混用参数（见已知问题）|
| **数量与预期死亡率** | 每组 n 是否在实验设计期间考虑了预期失落率？ | n=5 无缓冲的行为学实验 |

### 3.2 细胞系核查

| 检查项 | 关注点 | 候选账本标记 |
|--------|--------|------------|
| **细胞系来源** | 有无供应商+货号/ATCC/RRID？ | `CELL_LINE_SOURCE_MISSING` |
| **支原体检测** | 是否声明 mycoplasma-free？ | `MYCOPLASMA_UNREPORTED` |
| **STR 鉴定** | 是否提及 STR 验证？ | `STR_UNREPORTED` |
| **培养条件匹配** | 培养基成分、血清浓度、CO₂ 浓度是否与该细胞系已知需求一致？ | `CULTURE_CONDITION_MISMATCH` |
| **已知争议系** | 是否涉及已知误认/污染细胞系（HeLa 污染系、MDA-MB-435 等）？ | X1 via Cellosaurus；离线层记 `CELL_LINE_IDENTITY_UNVERIFIED` |
| **传代数** | 原代细胞是否说明传代数？高传代是否可能影响结果？ | `PASSAGE_UNREPORTED` |

### 3.3 试剂/药物核查

| 检查项 | 关注点 | 候选账本标记 |
|--------|--------|------------|
| **作用机制-模型匹配** | 该试剂的已知作用机制是否与实验的预期效应方向一致？ | `AGENT_MECHANISM_MISMATCH` |
| **溶剂相容性** | 溶剂选择（DMSO、乙醇、PBS）是否适合该化合物；最终溶剂浓度是否在安全范围内？ | `SOLVENT_ISSUE` |
| **试剂来源** | 厂商+货号是否给出？ | `REAGENT_NO_CATALOG` |
| **稳定性** | 是否涉及不稳定成分（细胞因子、RNA、放射性物质）且未说明储存条件？ | `STABILITY_UNREPORTED` |

### 3.4 交互合理性（Interaction Plausibility）

对方法中涉及的**关键实体-实体交互**（药物-靶点、刺激-细胞、处理-模型），检查：

1. **方向性**：处理的预期效果方向是否与生物学常识一致？
   - 例：METH 40 mg/kg IP 对小鼠 → 接近 LD₅₀，不可能产生慢性行为模型
   - 例：抑制 PI3K/AKT → 减少 Bcl-2 依赖的生存信号 → 促凋亡（合理）

2. **量级**：剂量/浓度是否在已知活性范围内？
   - 例：IC₅₀ 10 µM 的化合物，在 0.1 µM 下做 Western blot 测通路 → 可能低于有效范围

3. **底物-环境匹配**：
   - 动物行为测试的底物（液体 vs 琼脂）是否与所引用方法的底物一致？
   - 温度、pH、离子强度是否在已知功能范围内？

**交互合理性候选** → 标记 `INTERACTION_IMPLAUSIBLE` 或 `INTERACTION_CONTEXT_MISMATCH`；
在 Phase 5 按证据质量和影响程度决定 severity。

---

## Phase 4 · 实验逻辑核查

### 4.1 剂量/处理合理性

| 检查项 | 判据 | 候选账本标记 |
|--------|------|------------|
| **剂量梯度** | 剂量-反应研究 < 4 个非零剂量点 | `DOSE_GRADIENT_INSUFFICIENT` |
| **剂量依据** | 未说明剂量选择依据（预实验/文献/MTD/IC₅₀） | `DOSE_RATIONALE_MISSING` |
| **剂量-物种适宜性** | 剂量在该物种该给药途径下是否合理（不超过 MTD/LD₁₀；DMSO <0.5%） | `DOSE_OUT_OF_RANGE` |
| **时间点** | 只测单一时间点却下动力学结论 | 与 M7 联动 |

### 4.2 结局-假设连接

核心问题：**论文的主假设（main hypothesis）能被方法节中的检测步骤所验证吗？**

- 列出主假设中的因果链：A → B → C
- 对链中每个节点检查：方法节是否有对应的测量步骤？
- 若某节点无对应测量步骤 → `ENDPOINT_MISSING`（major）
- 若测量步骤测量的指标与假设节点不匹配 → `ENDPOINT_PROXY_QUESTIONABLE`（minor/major）

**例**：假设「药物 X 通过抑制 PI3K 诱导凋亡」
- PI3K 活性（p-PI3K）→ 需 Western blot ✓
- 下游 AKT 磷酸化 → 需 Western blot ✓
- 凋亡结局 → 需 Annexin V、TUNEL 或 Caspase 活性 ✓
- 若只测 p-PI3K 而不测凋亡指标 → `ENDPOINT_MISSING`

### 4.3 干扰因素检查

询问：**方法设计中是否存在会产生意外影响的因素，且论文未对此给出控制或说明？**

常见干扰源（不限于此）：
- 溶剂毒性（DMSO、乙醇、甲醇）未设溶剂对照
- 同一批动物执行多个行为测试（顺序效应、疲劳、习惯化）
- 造模操作本身的毒性（免疫抑制剂、化学品）影响所测生理指标
- 灌胃应激对行为学结果的影响
- 同一样本用于多个分析（多次冻融）
- 检测操作的时间窗口（如免疫细胞功能的昼夜差异）

候选标记：`CONFOUND_UNREPORTED`（无控制也无说明）、`CONFOUND_CONTROLLED`（有说明，不产 finding）

### 4.4 对照设置核查

| 情形 | 应有对照 | 缺失时 |
|------|----------|--------|
| 药物/化合物处理 | 溶剂对照（相同体积/浓度溶剂） | `MISSING_CONTROL`（critical） |
| 基因敲低（siRNA/shRNA） | 非靶向对照（scrambled/NC） | `MISSING_CONTROL`（critical） |
| 过表达 | 空载体对照 | `MISSING_CONTROL`（critical） |
| 抗体类实验（IP/IHC/IF） | 同型 IgG / 一抗省略 | `MISSING_CONTROL`（major） |
| 手术模型 | 假手术（sham） | `MISSING_CONTROL`（critical） |
| 荧光染色 | 阴性对照（未染色 / 二抗单独） | `MISSING_CONTROL`（major） |
| 行为学 | 未处理/空白对照 + 阳性药物对照（若评估治疗效果） | `MISSING_CONTROL`（major） |

**防误报规则**：`controls` 字段为 `parse_failed` 或 `ambiguous` 时不报（未读到 ≠ 不存在）。

### 4.5 Assay 最低报告要素（v1 保留，补充完善）

每种 assay 仅对其所列要素检查，**不跨 assay 套用**。

| assay | 必报要素（缺失 → major） | 建议报（缺失 → minor） |
|-------|------------------------|----------------------|
| **Western blot** | 抗体来源+货号、稀释比、上样量、内参蛋白 | 转膜条件、封闭液、凝胶浓度（跨宽分子量范围时必填）、曝光时间 |
| **qPCR** | 引物序列或货号、内参基因、定量方法（2^-ΔΔCt 等） | 扩增效率、熔解曲线、RNA 质量（RIN） |
| **ELISA** | 试剂盒厂商+货号、检测范围（线性范围）、标准曲线 | 批内/批间 CV、稀释倍数、保存条件 |
| **IHC / IF** | 抗体货号+稀释、抗原修复方法、阳性/阴性对照 | 定量方法、是否盲法判读 |
| **流式细胞术** | 抗体 panel（荧光素+克隆号）、门控策略、同型/FMO 对照 | 补偿方案、活死细胞染色、采集细胞数 |
| **CCK-8 / MTT / MTS** | 接种密度、处理时长、读数波长、溶剂对照说明 | 复孔数、是否扣除背景 |
| **组织学（HE/Masson/特殊染色）** | 固定方式、切片厚度、染色方案、评分标准 | 判读者数量、是否盲法、每样本视野数 |
| **RNA-seq / ChIP-seq** | 平台、建库试剂盒、测序深度/读长、比对软件+版本、参考基因组版本 | 质控指标（Q20/Q30）、批次信息 |
| **动物行为学** | 装置规格（尺寸/材质）、测试时长、环境条件（光照/噪声/温度）、判读是否盲法 | 适应期、测试顺序随机化、测试时间段（昼夜） |
| **Co-IP / pulldown** | 抗体货号、裂解缓冲液配方、对照 IgG | 洗涤次数与强度、input 比例 |
| **HPLC / LC-MS** | 色谱柱型号、流动相组成、流速、检测波长/质量范围、标准品来源 | 保留时间、响应因子、回收率 |
| **分子对接（in silico）** | 靶蛋白 PDB ID 和分辨率、对接软件+版本、格点/搜索空间定义、评分函数 | 与已知配体的对比验证、结合口袋选取依据 |
| **克隆形成** | 接种细胞数、培养时长、固定/染色方案、计数阈值（≥X 个细胞） | 每组孔数（生物重复 vs 技术重复的区分） |
| **AO/EB 染色** | AO/EB 浓度或比例、染色时长、每组计数细胞数、分类标准（活/早凋/晚凋/坏死） | 是否盲法、采集视野数 |

> **溯源要求（跨所有 assay）**：关键试剂（抗体、化合物、细胞系）应给出来源+货号/批号。
> 只写厂商不写货号 → `reagent_traceability_incomplete`（minor）。

### 4.6 随机化与盲法

| 状态 | 处理 |
|------|------|
| 报告了方法 | 不报 |
| 未报告（`not_reported`） | `randomization_blinding_unreported`（minor；与 M6 ARRIVE 联动） |
| 明确未做且给了理由 | 不报 |
| 明确未做且无理由 | 同上（major） |

---

## Phase 5 · Severity 标定与 Finding 产出

### 5.1 标定规则（两步法）

**Step A：判断是否伤害实验基本逻辑**

| 类型 | 判断 |
|------|------|
| 缺失信息使实验**不可复现** | 可能是 major（依据 Step B 最终定） |
| 缺失信息使**结果解释发生根本改变** | major 或 critical |
| 存在/错误信息使实验**逻辑断裂**（FLOW_BREAK / INTERACTION_IMPLAUSIBLE） | major 或 critical |
| 关键对照缺失（`MISSING_CONTROL`） | critical |
| 缺失信息**不影响核心结论，只影响可重复性** | minor 或 informational |
| 报告遗漏但**不影响解读或复现** | informational |

**Step B：检查自消解条件（任一满足即降级）**

以下任何一条成立时，候选的 severity **下调一级**（critical→major / major→minor / minor→informational）：

1. **Paper 已给出合理解释**：作者在方法节或讨论节对该偏差提供了说明，且说明在专业上合理
2. **图表数据自支持**：该信息虽未文字说明，但图表中的数据（如含有内参的 WB 图、含标准曲线的 ELISA 图）已隐含该信息
3. **领域通行惯例已覆盖**：该步骤遵循已被广泛知晓的行业标准，如商业试剂盒说明书
4. **不影响组间可比性**：缺失信息对所有组的影响完全一致，不产生差异性偏差

**Step C：最终 severity 边界**

| 最终 severity | 含义 |
|--------------|------|
| `critical` | 实验设计根本性缺陷，不修正无法接受；核心结论可能错误 |
| `major` | 影响结果可靠性或重要信息缺失，必须修改 |
| `minor` | 报告不完整但不影响核心结论；建议完善 |
| `informational` | 非必要信息缺失，或仅供改善透明度的建议 |

### 5.2 Finding 产出格式

每条 finding 必须包含：
- `slug`（见 §5.3）
- `severity`（经 Phase 5 Step A→B→C 标定）
- `step_refs[]`（来自 Phase 1 的 step_id，必须至少有一个）
- `evidence_refs[]`（来自 evidence_registry 的 present/absence 证据，符合 contracts §1）
- `message`：一句话陈述问题本身
- `impact`：一句话说明这如何影响实验或结论
- `recommended_action`：作者应补充/修改什么

**不允许没有 `step_refs` 的 finding。** 如果找不到对应的 step，说明 Phase 1 解构不完整，先补完 Phase 1。

### 5.3 Category Slugs

slugs 分为两组：**实验设计类**（Phase 2–4 产出）与**步骤角色要求类**（Phase 1b 产出）。

#### 实验设计类

| slug | 描述 | 默认 severity |
|------|------|--------------|
| `missing_control` | 关键对照缺失（整体设计层面） | critical |
| `flow_break` | 步骤输出-输入不匹配，流程断裂 | major |
| `interaction_implausible` | 实体-实体交互与已知生物学相悖 | major |
| `interaction_context_mismatch` | 实体交互在参数/底物上下文不匹配 | major |
| `dose_out_of_range` | 剂量超出合理范围（接近毒性剂量 / 低于有效剂量） | major |
| `endpoint_missing` | 主假设中的某节点无对应检测方法 | major |
| `confound_unreported` | 已知干扰因素存在但未控制也未说明 | major / minor |
| `method_no_reference` | 非标准流程无方法学引用且无自述 | major |
| `method_reporting_incomplete` | Assay 缺少必报要素（§4.5 清单） | major / minor |
| `protocol_deviation_unexplained` | 偏离通用流程未说明 | major |
| `animal_use_justification_unclear` | 未见动物实验必要性说明 | major |
| `dose_gradient_insufficient` | 剂量-反应点数不足 | major |
| `dose_rationale_missing` | 剂量选择依据缺失 | minor |
| `replicate_type_unclear` | 未区分生物学/技术重复 | major |
| `randomization_blinding_unreported` | 未报告随机化/盲法 | minor / major |
| `cell_line_unauthenticated` | 细胞系来源/鉴定未报告 | minor |
| `reagent_traceability_incomplete` | 关键试剂缺来源或货号 | minor |
| `endpoint_proxy_questionable` | 测量指标与假设节点的对应关系存疑 | minor |
| `timeline_anomaly` | 时间节点不符合生物学合理范围 | major / minor |
| `missing_intermediate_step` | 流程中缺少必要的中间处理步骤 | major / minor |

#### 步骤角色要求类（Phase 1b 产出）

这些 slug 源自 Phase 1b 对单个步骤的 `step_role` 要求核查；
**在 Phase 5 汇总时与实验设计类合并，避免双重计分同一问题。**

| slug | step_role | 描述 | 默认 severity |
|------|-----------|------|--------------|
| `missing_paired_control` | INTERVENTION | 干预步骤无并行对照条件 | critical |
| `confounded_variable` | INTERVENTION | 单步同时改变多变量而无拆分组 | major |
| `intervention_underspecified` | INTERVENTION | 剂量/时长/途径/条件缺失 | major / minor |
| `random_assignment_missing` | INTERVENTION | 受试者未随机分配到干预组 | major |
| `calibration_missing` | DETECTION | DETECTION 步骤无配对 CALIBRATION | major |
| `reproducibility_unreported` | DETECTION | 技术重复数或批内 CV 未报告 | minor |
| `subjectivity_uncontrolled` | DETECTION / ANALYSIS | 主观判断步骤无盲法且无算法化 | major |
| `quantification_criteria_undefined` | DETECTION | 截断值/评分阈值未预先定义 | major |
| `detection_range_concern` | DETECTION | 被测物浓度超出检测线性范围 | major |
| `batch_effect_uncontrolled` | PROCESSING | 各组样品非同批处理且未说明 | major |
| `processing_underspecified` | PROCESSING | 关键处理参数（时间/温度/速度）缺失 | minor |
| `stability_window_violated` | PROCESSING | 样品在稳定窗口外等待/处理 | major |
| `validation_criteria_undefined` | VALIDATION | 造模/试剂验证无预先定义的成功标准 | major |
| `validation_result_unreported` | VALIDATION | 验证步骤的结果未呈现 | minor |
| `calibration_not_concurrent` | CALIBRATION | 校准步骤与 DETECTION 不同 run | major |
| `calibration_range_insufficient` | CALIBRATION | 校准范围不覆盖被测样品浓度 | major |
| `calibration_source_missing` | CALIBRATION | 标准品/参照物来源未记录 | minor |
| `software_version_missing` | ANALYSIS | 分析软件版本未记录 | minor |
| `inter_rater_unreported` | ANALYSIS | 多评分者时未报告一致性 | minor |

---

## 6. 与其他模块的边界

| 情形 | 归属 | 理由 |
|------|------|------|
| 动物实验是否**必要** | **M3** | 方法学判断 |
| 动物实验有无**伦理批件** | **M6** | 合规判断 |
| 样本量是否**足够** | **M4** | 统计效能 |
| 技术重复当作统计 n | **M4**（`pseudoreplication`）；M3 报「未区分」 | 统计推断问题 |
| 方法描述**前后矛盾** | **M2** | 内部一致性 |
| 结论**超出数据支持范围** | **M7** | 结论-证据对齐 |
| 引物/登录号**格式错误** | 工具产 signal → **M3** 判定 | `sequence_identifier_audit.py` |
| 数值**内部不一致**（如剂量两处不同） | **M2** + **M3** 联动 | M2 查一致性，M3 查哪个值在方法上正确 |

---

## 7. 联网增强（X1 connector **已交付**，非候选）

> 本节原写作「候选／待接入」，实际 X1 外部核验层已实现并在真实论文运行中跑通
> （`scripts/external_figure_validation.py`，12 个数据库，14 项 check）。
> 下表各项**现在就该调用**，不要当作二期设想。调用方式见 SKILL.md §4。

| 功能 | 数据源 | 新增 slug |
|------|--------|----------|
| 方法学引用核验（文献是否真包含该方法） | Crossref / PubMed via X1 | `method_citation_mismatch`（major） |
| 细胞系误认/污染 | Cellosaurus / ICLAC via X1 | `cell_line_misidentified`（critical） |
| 抗体 RRID 核验 | RRID Registry / Antibody Registry via X1 | `antibody_validation_issue`（major） |
| 剂量落在同类文献分布区间外 | PubMed + ChEMBL via X1 | `dose_out_of_range`（产 external_validation_candidate，不直接立 finding） |

外部源不可达时只产 `system_limitation`，不改变稿件风险分。

---

## 8. 示例（正例/反例）

### 8.1 `flow_break`（Phase 2 → Phase 5）

**该报警**：
> S03（细胞裂解 → 收集上清蛋白质）→ S04（Western blot，样品为组织匀浆）

S03 输出是**细胞裂解液蛋白**，S04 却要求**组织蛋白**，两者来源不一致，
流程断裂。severity: major。

**不该报警**：
> S03（离心 12000g 10 min → 收集上清）→ S04（BCA 蛋白定量）

输出（蛋白上清）恰好是 S04 的输入，连接合理，不报。

### 8.2 `dose_out_of_range`（Phase 3/4 → Phase 5）

**该报警**：
> "Methamphetamine ... administered by intraperitoneal injection to mice
> in a concentration of 40 mg/kg"

小鼠 METH i.p. LD₅₀ ≈ 57 mg/kg。40 mg/kg 接近 LD₅₀，
会产生严重急性毒性，不能建立慢性行为学模型。
同文件另一处写"5 mg/kg/day"存在直接矛盾（归 M2，但 M3 同时报剂量合理性问题）。
severity: major（降级检查：无图表自支持，无作者解释 → 保持 major）。

**不该报警**：
> "Anethole 10.8 μM for CCK-8"

文中 IC₅₀ = 10.8 µM，选取该浓度有明确依据 → 不报。

### 8.3 `method_reporting_incomplete`（降级示例）

**候选**：Western blot 中未给出 SDS-PAGE 凝胶浓度。
- Step A：影响重复性，但通常不改变定性结论 → 候选 minor。
- Step B 检查：图中条带位置和分子量标记可见，读者可推断大致凝胶范围 → 图表数据自支持 → 降至 **informational**。

**候选**：ELISA 无试剂盒货号。
- Step A：无法确认检测范围和标准曲线，直接影响绝对浓度值可信度 → 候选 major。
- Step B 检查：文中无图表展示标准曲线，无其他自支持证据 → **保持 major**。

---

## 9. TODO（二期）

- [ ] 补充中医药多成分方剂的特殊处理规则
- [ ] 补充器械/影像类研究的方法学要素
- [ ] 用 `tools/baseline_probe.py` 探针各 slug 的零-uplift 率
- [ ] Peter 复核 §4.5 所有 assay 的必报要素
- [ ] 联网后对已分析的 3 篇论文重跑 X1 层，验证离线层命中率
