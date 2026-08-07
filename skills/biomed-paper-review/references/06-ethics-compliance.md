# M6 · 伦理合规

**原负责人：Peter** · 状态：**一期规则库已完成法源与防误报复核（2026-08-07）**

核心问题：这项研究**该不该做**、**做之前有没有获得授权**、**稿件有没有把授权说清楚**。

**本模块与其他审核模块的关键差异**：伦理要求是**成文的规范**，不是领域惯例。
因此本模块的判定不靠经验，而靠一份可引用的规范库
——`resources/ethics_rules.json`（28 部规范、22 条结构化要求，三法域）。
**每一条 finding 都必须引用到具体规范的具体条款。**

**本文件依赖 `00-contracts.md`。** finding 结构、`evidence_refs[]`、severity 枚举
的定义都在那里。

---

## 1. 输入

| 来源 | 用途 |
| --- | --- |
| `structured_result_v2.article_design` | 判定适用哪些规范（人体 / 动物 / 细胞 / 计算） |
| `structured_result_v2.population.subjects` | 物种、人群、细胞来源、是否弱势群体 |
| `structured_result_v2.declarations.*` | 伦理声明、知情同意、资助、利益冲突、数据可及性 |
| `structured_result_v2.design.registration` | 临床试验注册号 |
| `evaluation_matrix.{has_animal_experiment, has_human_subjects, ethics_statement, informed_consent}` | 路由 |
| **`ethics_requirement_unmet` signals** | 由 `scripts/ethics_compliance_check.py`（相对 Skill 根目录）产出，见 §2 |
| `all_system_limitations[]` | 补充材料不可得时**不得**判缺失 |

## 2. 规范库与筛查工具

```
resources/ethics_rules.json          规范库（数据）
scripts/ethics_compliance_check.py   筛查器（产 signal，不产 finding）
        ↓  ethics_requirement_unmet
M6（本模块）                          判定是否构成 finding、定 severity
```

这与 `statistical_forensics.py → M4` 是同一个模式：
**工具层给出「规范要求 X，稿件未见 X」的机器级观察；M6 决定它是否构成稿件问题。**

**为什么能离线**：规范库是**结构化要求索引**，不是外部数据库查询 ——
正好落在一期定义内（`SKILL.md §0.2`：论文自身内容 + 通用规范库）。
批件号真伪需要仍未接入的数据源；**注册号时序核验的 connector 已交付**（ClinicalTrials.gov，见 §8）。

### 2.1 规范库覆盖范围

| 法域 | 主要规范 |
| --- | --- |
| 国际 | 赫尔辛基宣言、CIOMS 2016、ICH-GCP E6、ARRIVE 2.0、ISSCR 2021（2025 SCBEM 定向更新）、名古屋议定书、ICMJE |
| 美国 | Common Rule (45 CFR 46)、FDA (21 CFR 50/56)、HIPAA、PHS-OLAW、动物福利法 (9 CFR)、NRC Guide、AVMA 安乐死指南、贝尔蒙报告 |
| 中国 | 涉及人的生命科学和医学研究伦理审查办法 (2023)、科技伦理审查办法（试行）、人类遗传资源管理条例（2024 修订）及实施细则、GCP (2020)、实验动物管理条例与实验动物许可证管理办法、GB/T 35892-2018、生物安全法、病原微生物实验室生物安全管理条例（2024 修订）、个人信息保护法、人胚胎干细胞研究伦理指导原则 |

领域：`human_clinical` / `animal` / `human_derived_cells_tissue` / `cell_line_general` /
`stem_cell_embryo` / `genetic_resources` / `biosafety` / `data_privacy` /
`clinical_trial_registration`。

### 2.2 规范库的使用纪律

1. **引用要精确到条款。** finding 的 `rule_ref` 写 `ethics_rules#<rule_id>`，
   `detail` 中列出该规则的 `citations`（规范名 + 条款）。
2. **注意 `citation_confidence`。** 规范库对每条引用标了置信度；
   `medium` 及以下的定位在写入正式审稿意见前必须人工打开原文核对。
   当前仅 GB/T 35892-2018 的细目、2003 年中国人胚胎干细胞原则的部分定位和
   `ETH-BIO-002` 的中国法依据未提升为 `high`；不得把它们渲染成已确定法律结论。
3. **规范库不是法律意见。** 输出是筛查信号，不构成合规裁定。

---

## 3. 判定流程

```
1. 适用性路由    ← article_design + population.subjects 决定哪些规则适用
2. 状态门控      ← 字段 parse_failed / unresolved → 不判缺失，出人工复核项
3. 反向豁免      ← 商业化细胞系等情形主动压制误报
4. 立 finding    ← 独立给出稿件证据，引用规范条款
```

### 3.1 适用性路由

| 触发条件 | 适用规则域 |
| --- | --- |
| `family ∈ {human_interventional, human_observational}` | `human_clinical` + `data_privacy` |
| `type = randomized_controlled_trial` 等干预性 | 追加 `clinical_trial_registration` |
| `design_components[] 含 in_vivo_animal` | `animal`（**按实验级判定**，不是全文级） |
| `population.subjects` 含原代人源材料 | `human_derived_cells_tissue` |
| `population.subjects` 只含来源与允许用途明确的已建立细胞系 | **反向豁免候选**，见 §3.3 |
| 含 hESC / 人胚胎 | `stem_cell_embryo` |
| 中国人群样本 + 境外合作/样本出境 | `genetic_resources` |
| 活体病原微生物 | `biosafety` |

**实验级判定**：一篇论文含 `in_vitro`(EXP-01) + `in_vivo_animal`(EXP-02) 时，
动物伦理只对 EXP-02 适用；EXP-01 的 `ethics_statement` 应为 `not_applicable`
（`01-structured-extraction.md §5.3.6`）。`evaluation_matrix.ethics_statement`
会拆成两个条目，**不取「或」**。

### 3.2 状态门控（最重要的防误报）

| 字段 status | M6 的动作 |
| --- | --- |
| `reported` | 检查内容是否满足规则要求 |
| `not_reported`（已完整检索） | **可以**立 finding |
| `not_applicable` | 合规，不立 finding |
| `parse_failed` / `unresolved` / `ambiguous` | **绝不立 finding** —— 出人工复核项，说明「我们没看清」 |

**补充材料不可得时的铁律**：许多论文把伦理批件号写在 Supplementary Methods。
`system_limitation: supplement_inaccessible` 时，依赖它的伦理字段一律 `parse_failed`，
**不得**判 `not_reported` —— 我们没看过，就不能说稿件没写
（`00-contracts.md §6.4`）。这是本模块最容易冤枉作者的地方。

### 3.3 反向豁免规则

| 情形 | 被压制的规则 | 理由 |
| --- | --- | --- |
| 只用来源/允许用途明确的既有不可识别细胞系（HeLa/HEK293/HepG2/Huh7 等，规范库列 29 个名称） | `ETH-CELL-001`、`ETH-HUM-001`、`ETH-HUM-002` | 既有不可识别标本通常不构成 Common Rule 下的 human subject；中国研究还须满足 2023 办法第32条的来源、授权范围与排除条件 |
| 纯计算 / 二次文献研究 | 全部 `human_clinical` 与 `animal` 规则 | 无受试者 |
| 病例报告 | 注册、样本量类要求 | 见 `01-…md §5.3.5` |
| 公开去标识数据集二次分析 | `ETH-HUM-002`（知情同意） | 应改查是否说明数据来源与使用许可 |

细胞系名称只用于离线召回，不是合规白名单。命中任一名称时仍须扫描同一研究是否还含
原代组织、HUVEC、患者来源类器官、血液或新增供者样本；出现任一项即禁止整篇豁免。
`CHO` 等短名称按独立实体匹配，不得命中 `chondrocyte` 等普通词。未知细胞系不自动加入名单，
也不因“常见”二字推定来源合法；先核对 catalog/RRID/CVCL 与材料转移限制。

---

## 4. 规则清单（摘自规范库，完整定义见 `resources/ethics_rules.json`）

### 4.1 人体研究

| rule_id | 要求 | severity |
| --- | --- | --- |
| `ETH-HUM-001` | 伦理委员会批准 + 批件号 | 未报告为 major；明确未获批准且规则适用时 critical |
| `ETH-HUM-002` | 知情同意 | 未报告为 major；明确未获同意/豁免且规则适用时 critical |
| `ETH-HUM-003` | 豁免知情同意须说明依据 | major |
| `ETH-HUM-004` | 赫尔辛基宣言遵循声明 | info；只缺宣言名称不立 finding |
| `ETH-HUM-005` | 干预性试验前瞻性注册 | major |
| `ETH-HUM-006` | 弱势群体额外保护 | major |
| `ETH-HUM-007` | 未成年人：监护人许可 + 本人赞同 | major |
| `ETH-HUM-008` | 可识别健康数据的去标识化或合法性基础 | minor |

### 4.2 动物实验

| rule_id | 要求 | severity |
| --- | --- | --- |
| `ETH-ANI-001` | IACUC / 动物伦理委员会批准 + 方案号 | 未报告为 major；明确未获批准时 critical |
| `ETH-ANI-002` | 3R 原则（替代/减少/优化） | 仅报告缺口为 minor；不得由缺少“3R”字样推定未实施 |
| `ETH-ANI-003` | 物种、品系、性别、年龄或体重、来源 | major |
| `ETH-ANI-004` | 麻醉、镇痛与人道终点 | major |
| `ETH-ANI-005` | 安乐死方法 | major |
| `ETH-ANI-006` | 中国实验动物许可证（SYXK/SCXK） | minor |

### 4.3 细胞、干细胞与胚胎

| rule_id | 要求 | severity |
| --- | --- | --- |
| `ETH-CELL-001` | 人源原代细胞/组织的供者同意 + 伦理批准 | 未报告为 major；明确未获授权时 critical |
| `ETH-CELL-002` | **反向规则**：商业化细胞系豁免 | info |
| `ETH-CELL-003` | hESC 研究类别、来源与监督路径——**一律交人工** | 默认 major；明确应审未审且影响合法性时才可 critical |
| `ETH-CELL-004` | 人胚胎体外培养期限（14 天规则）——**一律交人工** | critical |

### 4.4 遗传资源与生物安全

| rule_id | 要求 | severity |
| --- | --- | --- |
| `ETH-HGR-001` | 中国人类遗传资源审批/备案 | major |
| `ETH-HGR-002` | 名古屋议定书 PIC/MAT ——**一律交人工** | minor |
| `ETH-BIO-001` | 病原微生物实验的生物安全等级 | major |
| `ETH-BIO-002` | 两用性研究关切（DURC）——**一律交人工** | critical |

> **四条 `manual_only` 规则**（`ETH-CELL-003`、`ETH-CELL-004`、
> `ETH-HGR-002`、`ETH-BIO-002`）的共同点不是“问题严重”，而是自动化缺少决定适用性
> 所需的法域或实验类别事实。它们只产 `partial_extraction` 人工复核项，
> **不得产 `ethics_requirement_unmet`，不自动定 severity**。
> `ETH-CELL-003` 新纳入人工路径：既有 hESC 的常规体外培养可属 ISSCR Category 1A，
> 不能仅凭出现 `hESC` 就要求专门持续审查或判 critical。

---

## 5. finding 的证据要求

伦理类 finding 的证据形态与其他模块不同，须特别注意：

| 情形 | 证据要求 |
| --- | --- |
| 稿件未见伦理声明 | **必须**有 `absence` 证据，`searched_locations` 至少覆盖 `declarations` / `ethics` / `methods` 三节，`search_terms` 含中英双语（`ethics`、`IRB`、`IACUC`、`approval`、`伦理`、`批件`、`审查`） |
| 声明存在但缺批件号 | `present` 证据指向该声明原文，`detail` 说明缺的是哪个要素 |
| 声明与设计矛盾（如称无动物实验但方法节有小鼠） | 两条 `present` 证据，分别指向声明与方法节 |
| 补充材料不可得 | **不立 finding**；在人工复核建议中写明需索取哪份材料 |

**`severity >= major` 必须有可执行的 `manual_review.action`**，
写明「向作者索取什么」或「请伦理委员会核实什么」。
`manual_review.who` 对 critical 类伦理问题通常为 `ethics_committee` 或 `editor`。

---

## 6. 正例 / 反例

### 6.1 `ETH-ANI-001` 动物伦理批准

**该报警**：方法节写「C57BL/6 小鼠腹腔注射…」，全文检索 declarations / ethics /
methods 三节均未见 IACUC、伦理委员会、批件号 → **major 报告缺口**，
`action: 向作者索取动物实验伦理批件号与批准机构名称`。
只有稿件明确称未获审批，或外部核验确认无批准且该规则适用时，才升 `critical`。

**不该报警**：同样实验，Supplementary Methods S1 不可得且正文写
「All animal procedures are described in Supplementary Methods S1」
→ `ethics_statement.status = parse_failed` + `SYS-xxx (supplement_inaccessible)`
→ **不立 finding**，只在人工复核建议中写「需索取 S1 后复核」。

### 6.2 `ETH-CELL-001` 人源材料同意

**该报警**：方法节写「原代肝细胞取自接受肝切除术的患者」，
未见供者知情同意与伦理批准 → **major 报告缺口**；不得据“未报告”推断“未获得”。

**不该报警**：方法节写「HepG2 与 Huh7 细胞购自 ATCC」
→ 命中商业化细胞系反向豁免 → **不报**。
这是本模块最常见的误报来源，规范库列出 29 个常见名称作离线召回；HUVEC 因通常为
原代人脐静脉内皮细胞已从豁免列表移除。

### 6.3 `ETH-HUM-002` 知情同意

**该报警**：前瞻性临床试验，未见任何知情同意表述 → **major 报告缺口**。

**不该报警**：回顾性病历分析，作者写「本研究经伦理委员会批准免除知情同意
（回顾性去标识数据）」→ 属 `ETH-HUM-003` 的合规豁免路径 → **不报**
（但应检查豁免依据是否写明）。

### 6.4 `ETH-HUM-005` 试验注册

**该报警**：随机对照试验，全文未见任何注册号 → **major**。

**不该报警**：观察性队列研究未注册 → `ETH-HUM-005` 的
`applies_when.design_family = human_interventional` 不成立 → **不适用，不报**。

---

## 7. TODO（一期）

- [x] 建立可引用的三法域规范库（`resources/ethics_rules.json`）
- [x] 实现离线筛查器与三条防误报机制
- [x] 填充适用性路由表与状态门控规则
- [x] 每条规则配正例/反例
- [x] 复核规范库条款、severity 与中国法规：纠正 2023 办法第32条误引、动物许可证法源、ARRIVE item；更新 2024/2025 版本元数据
- [ ] 补充「伦理声明与研究设计矛盾」的检测规则（如声明无人体研究但有患者数据）
- [x] 停止把名称列表盲目扩到 100+；移除 HUVEC，并把扩展方向改为 accession + 来源/允许用途核验（见 Round 10 提案）
- [ ] 与 M3 划清边界：动物**必要性**（该不该做动物实验）归 M3，
      动物**授权**（有没有批件）归 M6
- [ ] 在 `datasets/` 的 `animal_invivo` 与 `rct_clinical` 两篇语料上实测误报率

---

## 8. 联网增强（注册号核验 connector **已交付**，批件号核验仍未接入）

当前离线层只核对「稿件有没有写」。联网增强核对「外部记录是否支持稿件表述」。

| 能力 | 数据源 | 查出什么 |
| --- | --- | --- |
| 临床试验注册号核验 | ClinicalTrials.gov API v2 / ChiCTR / WHO ICTRP | 号码不存在、终点与注册不符、**注册晚于首例入组**（回顾性注册） |
| 伦理批件号核验 | 多数机构暂无公开可查接口 | 公开记录不可得时明确告知用户，不得判真伪 |
| 机构 AAALAC 认证状态 | AAALAC 认证机构名录 | 动物设施是否具备认证 |
| 中国人类遗传资源审批 | 科技部行政许可公示 | 是否履行审批/备案 |
| 撤稿与伦理关切 | Retraction Watch / PubPeer | 该研究或其前序研究是否已被标注伦理问题 |

**联网增强的假阳性风险**：注册记录与论文的终点表述常有合理措辞差异，
语义不一致**只交人工**，不得自动判定为选择性报告。
「首次提交晚于入组开始」标为 `candidate` 而非结论 —— 注册平台的时间戳含义
在不同平台并不一致。

**契约方式**：复用 `00-contracts.md §1` 的 `external` evidence 与 §6.2 的
`external_validation_candidate`。M6 finding 的 `evidence_refs[0]` 必须是稿件内
`present`，并同时引用 external evidence；X1 failure 与零命中不得转 finding。
