# 论文审核报告 · Effect of telemedicine-supported structured exercise program in patients with chronic low back pain: a randomized controlled trial

> DOI：10.1371/journal.pone.0326218 ｜ 期刊：PLOS ONE ｜ 输入格式：`jats_xml`

## 一、执行摘要

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。本 Skill 的任何评分均为筛查信号（screening / triage signal），不构成录用、退稿或发表决定。

### 本报告能回答什么

> 已执行 M2–M7 中路由命中的模块；『未产出 finding』只表示本流程在已取得证据中未检出，不等于论文结论已被证实。

| 执行模式 | submode | 已执行审核模块 | 未执行审核模块 |
| --- | --- | --- | --- |
| `full_review` | `—` | M2, M4, M5, M6, M7 | M3 |

- 范围依据：RCT 设计触发 M4/M6/M7；大量跨节数值矛盾与参考文献问题触发 M2；表格/图注呈现问题触发 M5（范围受限：无图像文件）。M3 未触发：本篇为人体临床 RCT，无动物实验、无体外细胞、无湿实验方法学成分（候选路由与工具信号均无 M3 触发项）。M5 的像素级审计因无图像文件挂起（SYS-001）。
- 已执行阶段：stage_1, stage_2, stage_3, stage_3c_external_validation, stage_4, stage_5

### 审稿人先看

- 范围内问题权重合计：`100/100`；本次 `partial=true`（M3 未路由命中），不作全稿分段。
> ⚠️ 这是已执行模块范围内的局部筛查分，`comparable_to_full_review=false`。未执行模块没有被判定为『无问题』；本分数不得与任何其他报告的风险分横向比较或排序。
- 评分边界：分段阈值未经实证验证，是初始经验值，不得表述为自动化的录用/退稿决定。
- findings：共 43 条（critical 1 / major 30 / minor 11 / info 1）；复核动作：P0 5 / P1 7 / P2 1。
- 抽取覆盖率计算值：`0.284`；必须结合第七节分子/分母解释，不是稿件质量概率。
- 审核置信度：`0.62`。这是未经校准的证据支撑指数，不是 finding 正确概率，也不是稿件质量概率。

### 优先处理（最多三项）

- [ ] **[P0] 裁决 EARS 表-文矛盾：调取原始数据复核 Table 5 各时点组间比较；更正摘要/结论的依从性表述**（统计审稿人）
  - 关联判断：M2-101（critical）Table 5(EARS) 表-正文-摘要矛盾：表示组间显著，正文/摘要称无差异
- [ ] **[P0] 分析集与数据完整性裁决：GRIM 不可能值、ITT/PP 标注、Cases=234 对账；澄清前相关定量结论暂缓**（统计审稿人）
  - 关联判断：M4-108（major）GRIM/算术不可能值聚簇：Table 5 'ITT' 标签被证伪；M5-101（major）ITT/PP 标注混乱：标题与脚注矛盾、'*' 锚点丢失；M2-113（major）Table 3 Cases=234 与 7 例脱落不闭合
- [ ] **[P0] PCS 基线不均衡的校正分析（ANCOVA/回归均值敏感性）与多重性校正后重报**（统计审稿人）
  - 关联判断：M4-104（major）SF-12-PCS 基线显著不均衡且主分析未校正；M4-103（major）多重性未校正：PCS P=0.006 校正后可能不显著

## 二、结构化结果表

> 结构化结果版本 v2；`stage_3b_executed=False`。下文展示条件必填、未解析/冲突及与 finding 证据相交的字段；其余字段保留在 JSON。

| 字段 | 适用性 / 必填性 | 状态 | 值 | 抽取置信度 | 原文定位 |
| --- | --- | --- | --- | --- | --- |
| `objective.research_question` | `applicable` / `required` | `reported` | 远程医疗支持的结构化运动程序 vs 常规照护对 CLBP 患者的临床效果比较 | `high` | [EV-147｜present｜introduction/sec001-objective] |
| `objective.hypothesis` | `applicable` / `required` | `reported` | 8 周时试验组在改善 disability including pain 上优于对照组（优效假设） | `high` | [EV-147｜present｜introduction/sec001-objective] |
| `objective.primary_endpoint` | `applicable` / `required` | `conflicting` | disability including pain（RMDQ 0–24）——与并列报告的 NRS 构念重叠、estimand 未分离 | `medium` | [EV-121｜present｜methods/sec018] [EV-147｜present｜introduction/sec001-objective] |
| `objective.secondary_endpoints` | `applicable` / `required` | `reported` | NRS 疼痛强度、DASS21 心理健康、SF-12 PCS/MCS、TUG 步行能力、EARS 依从性 | `high` | [EV-121｜present｜methods/sec018] |
| `population.subjects` | `applicable` / `required` | `reported` | 18–65 岁 CLBP 成人患者（NRS≥3、疼痛≥12 周），华西医院特需门诊招募，N=78（每组 39） | `high` | [EV-123｜present｜methods/sec004] [EV-117｜present｜results/sec033] |
| `population.inclusion_criteria` | `applicable` / `required` | `reported` | Table 1 纳入标准（含 'Ability to operate a smartphone'） | `high` | [EV-114｜present｜results/Table 2] |
| `population.exclusion_criteria` | `applicable` / `required` | `reported` | Table 1 排除标准（脊柱特异疾病、手术史、妊娠等） | `high` | [EV-114｜present｜results/Table 2] |
| `design.arms` | `applicable` / `required` | `reported` | EG：app 运动+app 教育+WeChat 视频健康教练；CG：纸质手册运动+相同 app 教育（无运动模块权限） | `high` | [EV-129｜present｜methods/sec011] [EV-132｜present｜methods/sec015] |
| `design.interventions` | `applicable` / `required` | `conflicting` | 干预总场次多套口径互斥（Abstract 8 weekly sessions vs Methods 24 sessions vs 组分换算 EG 40/CG 32 次）；教练时长 20 vs 40 分钟 | `high` | [EV-104｜present｜abstract/abstract-methods] [EV-128｜present｜methods/sec010] |
| `design.controls` | `applicable` / `required` | `reported` | CG 为同内容同频次纸质运动+相同 app 教育的活性对照，正文标签为 'usual care therapy' | `high` | [EV-132｜present｜methods/sec015] [EV-133｜present｜methods/sec016] |
| `design.randomization` | `applicable` / `required` | `conflicting` | Abstract 'randomized numeric table' vs Methods 计算机区组序列；固定 block=4 vs 'permuted blocks at random' | `high` | [EV-104｜present｜abstract/abstract-methods] [EV-125｜present｜methods/sec006] |
| `design.allocation_concealment` | `applicable` / `required` | `reported` | 顺序编号密封不透光信封，入组现场拆封 | `high` | [EV-126｜present｜methods/sec007] [EV-127｜present｜methods/sec008] |
| `design.blinding` | `applicable` / `required` | `reported` | 开放标签：受试者/治疗师/评估者均不盲；缓解措施为 '保密试验假设'（有效性存疑） | `high` | [EV-124｜present｜methods/sec009] |
| `measurement.assays` | `applicable` / `required` | `reported` | RMDQ/NRS/DASS21/SF-12/TUG/EARS（中文版本与信效度数值未逐一声明；SF-12 机构归属表述不准确） | `high` | [EV-140｜present｜methods/sec019-024] [EV-141｜present｜methods/sec022] |
| `measurement.statistical_methods` | `applicable` / `required` | `ambiguous` | ITT 为预设主分析集；重复测量 ANOVA/LMM 选择条件未报告、实际全用复合对称 LMM；TUG 仅 PP；模型细节（固定效应/协变量/MAR/诊断/敏感性分析）缺失；多重性未校正 | `high` | [EV-119｜present｜methods/sec030] [EV-206｜缺失检索｜结果 no_match] |
| `measurement.sample_size_justification` | `applicable` / `required` | `conflicting` | G*Power 效应量 0.3 'based on Murtezani'——X1 核实该引用为 McKenzie vs 电物理因子 RCT，与本研究语境不符 | `high` | [EV-120｜present｜methods/sec026] [EV-969｜Crossref｜resolved｜2026-08-07] |
| `design_specific.trial_registration` | `applicable` / `required` | `reported` | ChiCTR2300071560；WHO ICTRP 核实：注册 2023-05-18、首例入组 2023-05-20、前瞻、样本量 39+39；正文治疗起始 05-15 与伦理号年份与注册库存在不一致 | `high` | [EV-122｜present｜methods/sec003] [EV-300｜WHO ICTRP Trial Search Portal｜resolved｜2026-08-07] |
| `design_specific.protocol_changes` | `applicable` / `required` | `ambiguous` | sec003 自述存在 'important changes' 需报批但未披露内容；注册库零修订、招募状态 Pending | `medium` | [EV-122｜present｜methods/sec003] [EV-211｜缺失检索｜结果 no_match] |
| `conclusion.limitations` | `applicable` / `required` | `conflicting` | 局限段将智能手机要求的选择方向写反；未披露接触量不匹配、无长期随访、样本年轻高教育 | `high` | [EV-112｜present｜discussion/sec041-limitations] [EV-140｜present｜methods/sec019-024] |
| `conclusion.generalization_scope` | `applicable` / `required` | `reported` | 单中心、8 周、中位年龄 22/27 岁、本科以上 84.6%/89.7%——结论未加 scope 限定 | `high` | [EV-114｜present｜results/Table 2] |
| `declarations.ethics_statement` | `applicable` / `required` | `reported` | 华西医院生物医学伦理委员会 2022 Review (1976)；未见赫尔辛基宣言表述 | `high` | [EV-122｜present｜methods/sec003] [EV-205｜缺失检索｜结果 no_match] |
| `declarations.informed_consent` | `applicable` / `required` | `conflicting` | 书面知情同意已报告；4 例在线知情同意与纸质程序不一致、合规依据未说明；发表同意为单数模板句 | `high` | [EV-123｜present｜methods/sec004] [EV-138｜present｜methods/sec031] |
| `declarations.funding` | `applicable` / `required` | `reported` | 7 项公共基金资助；声明 funder 无角色 | `high` | [EV-146｜present｜funding/funding-statement1] |
| `declarations.conflict_of_interest` | `applicable` / `required` | `conflicting` | COI 脚注 'no competing interests'；但干预用商业 app（ShuKang 公司）供应商角色未说明；处理编辑 Özden 的研究被 Discussion 有利引用且转述有误 | `medium` | [EV-144｜present｜conflict_of_interest/coi001] [EV-143｜present｜declarations/ack1] |
| `declarations.data_availability` | `applicable` / `required` | `conflicting` | 声明数据存于 Dryad doi:10.5061/dryad.zpc866tkh；该记录处于 embargo/不可见，doi.org/DataCite/Crossref 均 404 | `high` | [EV-139｜present｜data_availability/notes1] [EV-301｜Dryad API v2｜resolved｜2026-08-07] |

## 三、图表解读与原图定位

> 本次输入未提供任何图像文件（Fig 1/Fig 2 图像缺失，见系统限制 SYS-001），视觉层图表解读不可执行。以下为基于表格/图注文本的只读核对结论，不是像素级判断。

- **Fig 1（CONSORT 流程图）**：图像未提供，框内人数无法核验；正文自报 104 筛检、78 随机、EG 37 / CG 34 完成。脱落率文字（CG 12.8% vs Discussion 18%）的裁决需此图。→ SYS-001
- **Fig 2（ITT 结局箱线图）**：图像未提供；caption 声称 ITT 分析，而 sec039 明确 TUG 仅做 PP——caption 声明与正文冲突待人工核验。→ SYS-001、M5-101
- **Table 2**：计数/百分比/列合计经确定性核验全部自洽（各行=39）；唯 Pain intensity 行缺 P 值。
- **Table 3**：Cases=234（非 TUG）与 TUG Cases=178；ITT/PP 以上标区分，锚点在 txt 中丢失。
- **Table 4/5**：EG/CG 汇总口径（均值±SD vs 中位数 IQR）跨组混用；Table 5 的『Difference』列含义未定义。→ M4-109、M5-102

## 四、审核发现

### [CRITICAL] CL-001 · Table 5(EARS) 表-正文-摘要矛盾：表示组间显著，正文/摘要称无差异

- 类别：internal_inconsistency；锚点：{"figure": null, "panel": null, "table": "Table 5", "paragraph_id": "sec040", "evidence_ref": "EV-100"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M2-101**（严重(critical)，module=M2，category=`internal_inconsistency`，置信度 high）
    - Table 5 显示 EARS 在 T1（Z=−5.5，P<0.001）与 T2（Z=−3.19，P=0.001）均为 EG 更优的显著组间差异；Z=1.91（P=0.06）是组内变化量（Difference）的组间比较。sec040、Discussion、Abstract 却称 4/8 周组间『无显著差异(P>0.05)』，Abstract 并把 Z=1.91 误归为组内时间效应。确定性 Z→P 核验（SIG 无信号=表内自洽）证明错误在正文；Abstract/Conclusion『依从性等效』结论链建立于被证伪叙述上。
    - 复核：[P0] 裁决表与正文孰是孰非（Z→P 核验已证表内自洽）：调取原始数据/CRF 复核 EARS 各时点组间比较；在更正前，摘要与结论中依从性『等效/无差异』表述不得采信。（统计审稿人）

- 证据包：

- `EV-100`（present）section=results，table=Table 5，xml_id=sec040
  - 摘录：EG 49(46~51) / CG 43.68±3.5; Z −5.5 / −3.19 / 1.91; P <0.001 / 0.001 / 0.06
- `EV-101`（present）section=results，para=sec040，xml_id=sec040
  - 摘录：no statistically significant differences between the two groups' EARS scores at 4 and 8 weeks of intervention (P > 0.05)
- `EV-102`（present）section=abstract，para=abstract-results，xml_id=abstract
  - 摘录：only within-group differences ... exercise adherence (Z: 1.91, P = 0.06) over time
- `EV-103`（present）section=abstract，para=abstract-conclusion，xml_id=abstract
  - 摘录：the telemedicine program is equally effective as usual care therapy in enhancing mental health status, ... and exercise adherence

### [MAJOR] CL-002 · 不良事件零报告且有无据安全性主张

- 类别：harms_not_reported；锚点：{"figure": null, "panel": null, "table": null, "paragraph_id": "sec010", "evidence_ref": "EV-128"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M6-101**（重要(major)，module=M6，category=`harms_not_reported`，置信度 high）
    - Methods sec010/sec025 预设 AE 记录于 CRF 并描述两组伤害风险缓解措施，但 Results/Discussion 对 AE 零报告（absence 检索覆盖 Results 全文与 Table 3-5）；Discussion 反称视频监督 'decreased risk of sports injuries'。违反 CONSORT 2010 harms 扩展；8 周运动干预无 harms 数据时任何安全性方向主张均无据。
    - 复核：[P0] 要求作者补充 AE 汇总表（发生数/类型/严重度/组间分布/与运动因果关系）；若 Dryad 数据含 AE 变量一并核对。（作者）
  - **M2-105**（重要(major)，module=M2，category=`methods_results_gap`，置信度 medium）
    - sec017 允许病情恶化时使用药物/物理治疗并承诺记录于 CRF，但 Results 对随机化后合并治疗零报告（absence 检索确认）；Table 2 基线止痛药 EG 35.9% vs CG 28.2%，试验期用药变化未报告，可能混杂 NRS/主结局的组间比较。
    - 复核：[P1] 要求报告两组随机化后合并治疗（药物/物理治疗）发生率与类型。（作者）
  - **M6-111**（次要(minor)，module=M6，category=`monitoring_gap`，置信度 medium）
    - 全文与注册记录均未提及数据监查委员会、中期监查或停止规则；低风险行为干预下非强制，但叠加 AE 承诺记录却零报告（M6-101），安全监测可信度进一步降低。
    - 复核：[P2] 说明试验的安全监查安排（或声明低风险豁免理由）。（作者）

- 证据包：

- `EV-128`（present）section=methods，para=sec010，xml_id=sec010
  - 摘录：The two groups conducted an 8-week intervention, for a total of 24 sessions ... Frequency of attendance, medication changes, adverse events, etc. were ... duly recorded in the case report form
- `EV-135`（present）section=methods，para=sec025，xml_id=sec025
  - 摘录：Subjects in the EG group were supervised by weekly videoconferences to reduce the risk of injury during exercise
- `EV-200`（absence）范围 section，检索词 adverse event、harms、injury、complication…，结果 no_match
- `EV-134`（present）section=methods，para=sec017，xml_id=sec017
  - 摘录：permitted to utilize any relevant treatment ... such as drug therapy or physical therapy ... documented them in the case report forms

### [MAJOR] CL-003 · GRIM/算术不可能值聚簇：Table 5 'ITT' 标签被证伪

- 类别：grim_violation；锚点：{"figure": null, "panel": null, "table": "Table 5", "paragraph_id": null, "evidence_ref": "EV-100"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M4-108**（重要(major)，module=M4，category=`grim_violation`，置信度 high）
    - 确定性核验：①Table 5 标 '*ITT'，但 CG T1 均值 43.68±3.5 与 n=39 数学不相容（整数条目量表），仅与 n=34/37/38 相容——n=34 恰为 CG 完成者数，强烈提示该表实为完全病例分析误标 ITT；②NRS CG 基线 3.47 在 n=39 不可能（n=34/36/38 可行）；③NRS CG 8 周 1.96 在 n=34–39 全部不可能（最强违规）；④奇数 n=39 整数量表报告中位数 0.5/3.5 不可能。转录误差（3.46/3.49/1.95/1.97 均可行）仍为候选解释，原始数据（Dryad embargo）不可裁决，故不升 critical。
    - 复核：[P0] 调取原始数据复核 CG NRS/EARS 各时点 n 与均值；在澄清前 Table 4/5 的 CG 均值与 ITT 标签不得用于定量结论。（统计审稿人）
    - 溯源信号：SIG-177, SIG-178, SIG-179
  - **M5-101**（重要(major)，module=M5，category=`figure_text_contradiction`，置信度 high）
    - Table 3 标题 (N=78) 与 TUG Cases=178（PP，仅上标区分）混排；Table 4 标题 '*ITT analysis' 与脚注 'Linear mixed-effects model based on PP analysis' 并存且 '*' 在表内无可见锚点；Table 5 caption '*ITT analysis' 无对应脚注；Fig 2 caption 声称 ITT 而 sec039 明确 TUG 仅 PP（图像未提供，caption 冲突待人工核验）。结合 M4-108（Table 5 的 ITT 标签被 GRIM 证伪），分析集标签不可信是系统性问题。
    - 复核：[P0] 对照原始 PDF 还原 '*' 上标锚定；每个表格/图明确标注其实际分析集（ITT/PP/完全病例）。（统计审稿人）
  - **M4-109**（重要(major)，module=M4，category=`statistical_assumption`，置信度 high）
    - 同一指标跨组混用汇总统计量：NRS 基线 EG 3.5(3-5)（中位数）vs CG 3.47±1.28（均值），8 周 EG 0.5(0.25-1) vs CG 1.96±1.03；MCS 8 周与基线口径互异；TUG 8 周 EG 中位数 vs CG 均值；Table 5 CG T1 均值±SD vs T2 中位数。NRS 为 0–10 整数（入组≥3，地板效应），EG 按偏态报中位数、CG 按正态报均值，同一变量两组分布判断不一致，参数检验/LMM 前提对哪组成立无法判断，效应量不可复算；与 GRIM 违规、ITT/PP 标注问题交互。
    - 复核：[P1] 要求统一各指标的汇总口径并说明正态性判断依据；对偏态有界数据考虑稳健/非参数方法。（统计审稿人）
  - **M5-102**（次要(minor)，module=M5，category=`caption_not_self_contained`，置信度 high）
    - Table 5 脚注 'Mann-Whiteney U test' 拼写错误；'Difference' 列含义（组内变化 T2−T1 的组间比较）未在表内定义，而该列携带 Abstract 唯一引用的 EARS 统计量（Z=1.91/P=0.06）；Table 3/4/5 均未报告逐组逐时点 n，与分析集判定困难（M4-108/M5-101）交互；'~' 与 '-' IQR 记法跨表不统一。
    - 复核：[P2] 更正拼写、定义 Difference 列、补充逐时点 n、统一记法。（作者）

- 证据包：

- `EV-100`（present）section=results，table=Table 5，xml_id=sec040
  - 摘录：EG 49(46~51) / CG 43.68±3.5; Z −5.5 / −3.19 / 1.91; P <0.001 / 0.001 / 0.06
- `EV-116`（present）section=results，table=Table 4，xml_id=sec034
  - 摘录：NRS 基线 EG 3.5(3-5) vs CG 3.47±1.28，8w EG 0.5(0.25-1) vs CG 1.96±1.03；SF-12-PCS 基线 EG 37.1±7.18 vs CG 41.51±7.41；TUG 8w N=10/12；脚注 '*ITT analysis' 与 'based on PP analysis' 并存
- `EV-115`（present）section=results，table=Table 3，xml_id=sec034
  - 摘录：Cases 234（RMDQ/NRS/DASS21/SF-12）; TUG 行 Cases=178，0.97*（PP 脚注）

### [MAJOR] CL-004 · Table 3 Cases=234 与 7 例脱落不闭合

- 类别：participant_flow_inconsistency；锚点：{"figure": null, "panel": null, "table": "Table 3", "paragraph_id": "sec033", "evidence_ref": "EV-115"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M2-113**（重要(major)，module=M2，category=`participant_flow_inconsistency`，置信度 high）
    - Table 3 各指标 Cases=234=78×3，暗示全部随机者贡献全部三时点观测；但 sec033 报告脱落 EG 2、CG 5。确定性核算（SIG-255）：若脱落者无随访数据，观测上限 (37+34)×3=213<234；若 'Cases' 指模型纳入记录数，则其定义与缺失模式未披露。结合 NRS CG 基线 GRIM 仅容 n=34/36/38（SIG-177），分析集构成不可识别，直接影响主要终点 RMDQ 的 ITT 解释。
    - 复核：[P0] 要求披露各结局各时点实际进入分析的 n 与脱落者数据贡献方式（ITT 定义下的处理）。（统计审稿人）
    - 溯源信号：SIG-255
  - **M2-102**（重要(major)，module=M2，category=`participant_flow_inconsistency`，置信度 high）
    - TUG 出现四套口径：Table 3 Cases=178；Table 4 8 周 n=10/12（合计 22）；sec039『4 周失访 16、8 周失访 28』；Discussion『基线 74、再失访 28』。确定性核算（SIG-257）：仅『累计 28』口径 74+58+46=178 闭合，『additional 28』口径=162 不符；Table 4 的 n=10/12 与任一口径均不相容。TUG 实际分析人数不可确定。
    - 复核：[P1] 请作者给出 TUG 各时间点各组实际分析 n 及缺失原因交叉表，澄清 178 与 n=10/12 的关系。（统计审稿人）
    - 溯源信号：SIG-257
  - **M4-102**（重要(major)，module=M4，category=`percentage_mismatch`，置信度 high）
    - sec033 完成率 EG 94.9%(37/39)、CG 87.2%(34/39)，即脱落 5.1% 与 12.8%；Discussion 称 CG 脱落 18%。确定性核验（SIG-182）：18% 仅当分子取两组总脱落 7（7/39=17.9%）时成立——总脱落数被错配到 CG 分母，用于放大『EG 脱落更低』的对比。
    - 复核：[P1] 请作者更正 Discussion 脱落率数字（CG 应为 12.8%）或与 Fig 1 原始口径对账。（统计审稿人）
    - 溯源信号：SIG-182

- 证据包：

- `EV-115`（present）section=results，table=Table 3，xml_id=sec034
  - 摘录：Cases 234（RMDQ/NRS/DASS21/SF-12）; TUG 行 Cases=178，0.97*（PP 脚注）
- `EV-117`（present）section=results，para=sec033，xml_id=sec033
  - 摘录：The completion rate was 94.9% (37/39) in the EG and 87.2% (34/39) in the CG
- `EV-137`（present）section=results，para=sec039，xml_id=sec039
  - 摘录：16 cases were lost after 4 weeks of intervention, and 28 cases were lost after 8 weeks ... missing values for the TUG indicator were not interpolated, and only PP analyses using actual data were conducted
- `EV-108`（present）section=discussion，para=sec041-p4，xml_id=sec041
  - 摘录：baseline TUG data for only 74 patients. By week 4, 16 patients were lost ... By week 8, an additional 28 patients were lost

### [MAJOR] CL-005 · SF-12-PCS 基线显著不均衡且主分析未校正

- 类别：model_specification；锚点：{"figure": null, "panel": null, "table": "Table 4", "paragraph_id": "sec034", "evidence_ref": "EV-116"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M4-104**（重要(major)，module=M4，category=`model_specification`，置信度 high）
    - 基线 PCS EG 37.1±7.18 vs CG 41.51±7.41（差 4.41），确定性重算 t=−2.669、df=76、p=0.0093（SIG-219）：sec034『基线各指标无显著差异、可比』对该指标为假。8 周两组原始均值几乎相同（46.85 vs 46.80），未调整 LMM 的 +4.5 变化差全部利于基线较低组，回归均值未排除；模型未纳入基线值/预后因素。
    - 复核：[P0] 要求对 PCS（及其余结局）补做基线调整/ANCOVA 与回归均值敏感性分析后重报组间估计。（统计审稿人）
    - 溯源信号：SIG-219
  - **M4-103**（重要(major)，module=M4，category=`multiple_testing_control`，置信度 medium）
    - 6 结局×3 时间点×组/时间/交互多重检验均按双侧 α=0.05 无校正，统计分析节亦无预定义主对比层级（absence 检索确认）。SF-12-PCS 组间 P=0.006 为三项优效结论中边际最小者，经 Bonferroni/Holm 类校正后可能不再显著。
    - 复核：[P0] 要求说明预设主对比与多重性控制策略；对 6 结局组间对比给出校正后 P 或层级检验。（统计审稿人）
  - **M4-105**（重要(major)，module=M4，category=`model_specification`，置信度 medium）
    - sec030 声称满足假设用重复测量 ANOVA、否则混合模型，但结果（Table 3/4 脚注）一律为复合对称 LMM：前提检验、固定效应结构、时间编码、协变量、缺失机制（MAR）假设、模型诊断、任何敏感性分析均未报告（absence 检索确认）。
    - 复核：[P1] 要求公开模型设定（固定/随机效应、协方差结构、协变量、缺失假设）或提供分析代码。（统计审稿人）
  - **M4-106**（重要(major)，module=M4，category=`model_specification`，置信度 medium）
    - 'estimated value' 未说明是组间变化差、校正端点差还是边际均值差；Table 3 的组主效应 P（RMDQ 0.04）与正文组间对比 P（<0.001）共用 'between-group' 之名而行不同 estimand；主要终点 RMDQ 模型估计 −3.96 与中位数口径变化差（约 −2）差距大，且表内只报中位数/IQR。CI 自洽性核验通过，排除区间抄写错误，不可复核性源于模型/分析集未披露。
    - 复核：[P1] 要求明确主对比 estimand 定义并给出可复核的描述统计（均值±SD 或个体变化）。（统计审稿人）
  - **M4-110**（重要(major)，module=M4，category=`statistical_assumption`，置信度 high）
    - sec034 以 P>0.05 'confirming their comparability'（不显著≠可比；且 PCS 基线实算 p=0.0093，见 M4-104）；Table 2 'Pain intensity' 行缺 P 值且等级界值未定义（纳入已要求 NRS≥3，'mild' 对应区间不明）；Education 2×6 表 8/12 格期望频数<5、Smoking 期望格 4.5<5，渐近卡方适用性存疑；Exercise regime 48.7% vs 66.7%（P=0.11）未在任何分析中校正。
    - 复核：[P1] 撤回 'confirming comparability' 表述改为逐变量陈述；补 Pain intensity 行检验与界值；分类变量改用精确法。（统计审稿人）
  - **M2-109**（次要(minor)，module=M2，category=`analysis_reporting_gap`，置信度 high）
    - 数据采集于 baseline/4w/8w 三时点（Table 3 Cases=234 表明 4 周数据进入模型），但除 EARS T1 外所有结局均未报告 4 周组间/组内估计。sec018 已预设基线-8 周为主要对比，故降为 minor；报告不对称仍限制疗效时间轨迹的解读与选择性呈现的排除。
    - 复核：[P2] 建议补充 4 周时点估计或在补充材料说明未呈现原因。（作者）

- 证据包：

- `EV-116`（present）section=results，table=Table 4，xml_id=sec034
  - 摘录：NRS 基线 EG 3.5(3-5) vs CG 3.47±1.28，8w EG 0.5(0.25-1) vs CG 1.96±1.03；SF-12-PCS 基线 EG 37.1±7.18 vs CG 41.51±7.41；TUG 8w N=10/12；脚注 '*ITT analysis' 与 'based on PP analysis' 并存
- `EV-118`（present）section=results，para=sec034，xml_id=sec034
  - 摘录：there were no statistically significant differences between the two groups in all clinical outcome index scores before treatment (P > 0.05), confirming their comparability
- `EV-119`（present）section=methods，para=sec030，xml_id=sec030
  - 摘录：two-factor, three-level repeated measures analysis of variance (group*time) was applied; otherwise, a mixed-effects model was utilized ... intention-to-treat (ITT) analysis was chosen as the primary analysis set
- `EV-206`（absence）范围 section，检索词 fixed effects、covariate、missing at random、MAR…，结果 no_match
- `EV-207`（absence）范围 section，检索词 Bonferroni、Holm、FDR、multiplicity…，结果 no_match

### [MAJOR] CL-006 · 'equally effective/等效' 结论无等效或非劣检验支撑

- 类别：negative_result_misread；锚点：{"figure": null, "panel": null, "table": null, "paragraph_id": "sec042", "evidence_ref": "EV-105"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M7-104**（重要(major)，module=M7，category=`negative_result_misread`，置信度 medium）
    - Abstract/Conclusion 对 DASS21、MCS、TUG、EARS 以 'equally effective/equivalent' 表述组间无差异；试验按优效设计估算样本量，全文无预设等效/非劣界值、无相应检验（absence 检索确认）；TUG PP n=10/12、EARS 样本小效力不足。不显著≠等效；Discussion 'viable alternative' 推断链同样不闭合（无未治疗对照，组内改善不能归因于干预）。
    - 复核：[P1] 要求将 'equally effective' 改为 '未检出组间差异（效力有限）'，或补做非劣/等效分析。（统计审稿人）
  - **M7-105**（重要(major)，module=M7，category=`selective_result_interpretation`，置信度 high）
    - sec041 首段称结果 'confirmed the additional contribution of telemedicine ... in disability, pain, mental health status, quality of life and walking ability'；但 Table 3 组间效应 DASS21 P=0.63、MCS P=0.83、TUG P=0.84 均不显著——对心理健康/心理 QoL/步行的 '额外贡献' 主张与论文自身结果直接抵触；且该句与正式结论 'equivalent' 表述互相矛盾。
    - 复核：[P1] 请作者将 Discussion 首段改为与组间检验结果一致的表述（三项域无组间差异）。（领域审稿人）
  - **M7-106**（重要(major)，module=M7，category=`claim_beyond_evidence`，置信度 medium）
    - 单中心特需门诊、开放标签、仅 8 周随访、中位年龄 EG 27/CG 22 岁、本科以上 84.6%/89.7%、61.5–74.4% 经未定义 'Other' 渠道招募；Conclusion/Abstract 却称方案 'could reduce the burden'、'could be considered to be promoted in clinical applications'——推荐所依赖的恰是研究缺失的证据（无 >8 周随访、无成本效果，Discussion 自认）。Dryad 数据 embargo 进一步使推广主张不可复核。
    - 复核：[P1] 结论增加 scope 限定（人群/时程/中心）；将推广建议降为需要长期随访与成本效果证据的假设。（领域审稿人）
  - **M7-102**（重要(major)，module=M7，category=`claim_beyond_evidence`，置信度 medium）
    - CG 实际接受与 EG 相同的 app 教育 + 同动作同频次纸质运动处方（sec015/sec016），属结构性活性对照；标题/摘要/结论通篇称 'usual care therapy'，使 'more effective than usual care' 被读作优于常规临床诊疗的证据。Discussion 对 Fanuscu/Shi 的对照强度解释恰好反证优效结论由对照强度决定。
    - 复核：[P1] 请作者在结论中将对照界定为活性对照（纸质运动+教育），并限定优效表述的比较范围。（领域审稿人）
  - **M7-103**（重要(major)，module=M7，category=`causal_overreach`，置信度 medium）
    - EG 每周团体视频教练+app 目标提醒 vs CG 初诊后 'no further teaching unless requested'；接触量/注意力系统性不匹配，显著组间差异可能部分来自接触量与期望效应；Discussion 未将其列为局限，反称两组 'similar treatment doses administered'（该句本身与干预描述不符）；客观依从数据（app 日志/出勤）可得未报告。
    - 复核：[P1] 请作者报告两臂接触时长与客观依从数据，并在局限中讨论注意力/期望效应混杂。（领域审稿人）
  - **M7-107**（重要(major)，module=M7，category=`unsupported_claim`，置信度 high）
    - Discussion 称智能手机使用要求 'may have limited participation to individuals with lower socioeconomic status and education levels'——方向相反：'能操作智能手机' 是纳入标准，排斥的是数字弱势群体；Table 2 本科以上占 84.6%/89.7% 印证样本系统性偏高教育，该选择偏倚未被正确表述，影响外推判断。
    - 复核：[P1] 更正局限表述方向；将样本高教育构成作为外推限制讨论。（领域审稿人）
  - **M7-101**（重要(major)，module=M7，category=`claim_magnitude_mismatch`，置信度 high）
    - Discussion 称『两组 NRS 均改善超过 2 分达到 MCID』；X1 核实 ref37(Ostelo) 确为 MIC 共识（引用类型恰当），但 Table 4 CG 均值 3.47→1.96，实测改善 1.51 分 <2（GRIM 候选修正值下为 1.49–1.54，仍 <2，对转录误差稳健）；EG 仅报中位数口径。临床意义声称对 CG 不成立。
    - 复核：[P1] 请作者按个体水平数据计算达到 MCID（≥2 分）的受试者比例，或撤回『两组均达 MCID』表述。（统计审稿人）
  - **M2-106**（次要(minor)，module=M2，category=`design_analysis_disconnect`，置信度 medium）
    - 主要终点 RMDQ 的 24 项全部以 'because of my back pain' 限定，与并列报告的 NRS 疼痛构念重叠；优效假设写为 'disability including pain'，结论却分别以 disability 与 pain 两个名义各报告一次优效，存在重复计数风险。可复核性核心问题由 M4-106 承载。
    - 复核：[P2] 请作者明确 RMDQ 与 NRS 的层级（主/次）与 estimand 分离。（领域审稿人）

- 证据包：

- `EV-103`（present）section=abstract，para=abstract-conclusion，xml_id=abstract
  - 摘录：the telemedicine program is equally effective as usual care therapy in enhancing mental health status, ... and exercise adherence
- `EV-105`（present）section=conclusion，para=sec042，xml_id=sec042
  - 摘录：promotes recovery equivalent to usual care therapy concerning mental health status ... walking ability, and exercise adherence
- `EV-106`（present）section=discussion，para=sec041-p1，xml_id=sec041
  - 摘录：both groups showed an improvement of more than 2 points in the NRS to reach the minimal clinically significant difference (MCID); The results confirmed the additional contribution ... in disability, pain, mental health status, quality of life and walking ability
- `EV-112`（present）section=discussion，para=sec041-limitations，xml_id=sec041
  - 摘录：the requirement for smartphone use may have limited participation to individuals with lower socioeconomic status and education levels
- `EV-116`（present）section=results，table=Table 4，xml_id=sec034
  - 摘录：NRS 基线 EG 3.5(3-5) vs CG 3.47±1.28，8w EG 0.5(0.25-1) vs CG 1.96±1.03；SF-12-PCS 基线 EG 37.1±7.18 vs CG 41.51±7.41；TUG 8w N=10/12；脚注 '*ITT analysis' 与 'based on PP analysis' 并存

### [MAJOR] CL-007 · TUG 背离预设 ITT 主分析集：仅 PP、信息性缺失、无敏感性分析

- 类别：missing_data_handling；锚点：{"figure": null, "panel": null, "table": "Table 4", "paragraph_id": "sec039", "evidence_ref": "EV-137"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M4-101**（重要(major)，module=M4，category=`missing_data_handling`，置信度 high）
    - sec030 预设 ITT 为主分析集，但 TUG 以缺失多为由仅报 PP（8 周 n=10/12），未做插补或敏感性分析；失访理由含『症状显著改善』（SIG-257 相关叙述），属结局相关的信息性缺失（MNAR 方向偏向高估改善）；该 PP 结果仍被 Abstract/Conclusion 作为『步行能力等效』的正式结论。
    - 复核：[P1] 要求补齐 TUG 的 ITT 分析（多重插补或混合模型）与敏感性分析；在此之前结论中 TUG 表述限于 PP 范围并声明偏倚方向。（统计审稿人）
  - **M2-110**（重要(major)，module=M2，category=`methods_results_gap`，置信度 medium）
    - sec028 允许在线受试者经视频会议完成 TUG，但远程计时的标准化方案（指令、摄像头距离、计时方式、质量控制、信效度）均未报告；现场/远程混合的模式效应未讨论；Discussion 自述 4 例因场地限制未测。该终点（并见 M2-102/M4-101）的数据质量基础不成立。
    - 复核：[P1] 要求补充远程 TUG 测量方案与模式效应分析，或将其降级为探索性指标。（领域审稿人）

- 证据包：

- `EV-119`（present）section=methods，para=sec030，xml_id=sec030
  - 摘录：two-factor, three-level repeated measures analysis of variance (group*time) was applied; otherwise, a mixed-effects model was utilized ... intention-to-treat (ITT) analysis was chosen as the primary analysis set
- `EV-137`（present）section=results，para=sec039，xml_id=sec039
  - 摘录：16 cases were lost after 4 weeks of intervention, and 28 cases were lost after 8 weeks ... missing values for the TUG indicator were not interpolated, and only PP analyses using actual data were conducted
- `EV-136`（present）section=methods，para=sec028，xml_id=sec028
  - 摘录：the TUG test was done through video conferencing
- `EV-108`（present）section=discussion，para=sec041-p4，xml_id=sec041
  - 摘录：baseline TUG data for only 74 patients. By week 4, 16 patients were lost ... By week 8, an additional 28 patients were lost

### [MAJOR] CL-008 · 干预总场次跨节矛盾（8 周会话 vs 24 sessions vs 40/32 口径）

- 类别：internal_inconsistency；锚点：{"figure": null, "panel": null, "table": null, "paragraph_id": "sec010", "evidence_ref": "EV-128"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M2-103**（重要(major)，module=M2，category=`internal_inconsistency`，置信度 medium）
    - Abstract 称 'eight weekly sessions'；sec010 称 8 周共 24 sessions；sec014 称 24 次中 8 次受监督；按 sec011/sec015 组分换算 EG=运动 24+教育 8+教练 8=40 次接触、CG=24+8=32 次。多套口径互斥，实际递送剂量不可重建，直接影响两臂可比性与 Discussion 'similar treatment doses' 主张。
    - 复核：[P1] 请作者给出两臂逐成分会话频次与总接触时长对账表，并更正摘要表述。（领域审稿人）
  - **M2-104**（次要(minor)，module=M2，category=`internal_inconsistency`，置信度 medium）
    - sec011 教练 20 分钟/次 vs sec014 每次视频 40 分钟；sec011 运动 40 分钟/次 vs sec012 40–60 分钟；sec012 称初诊指导 'in three parts' 实列四项。
    - 复核：[P2] 统一剂量表述（教练与运动单次时长、初诊指导项数）。（作者）
  - **M2-108**（重要(major)，module=M2，category=`missing_reporting_guideline_element`，置信度 medium）
    - 干预描述缺少 TIDieR 关键要素：治疗师人数/资质、团体视频参与人数、运动处方进阶规则、健康教练内容标准化、执行保真度核查（absence 检索确认）；Introduction 宣称的 'dynamic videoconferencing monitoring' 在 Methods 无操作对应。CONSORT 清单虽列为补充材料（未提供），正文逐项落实存在缺口（见 M6-106 等）。
    - 复核：[P1] 要求按 TIDieR 补充干预递送细节（人员、进阶、保真度）。（领域审稿人）

- 证据包：

- `EV-104`（present）section=abstract，para=abstract-methods，xml_id=abstract
  - 摘录：conducted over eight weekly sessions ... using a randomized numeric table
- `EV-128`（present）section=methods，para=sec010，xml_id=sec010
  - 摘录：The two groups conducted an 8-week intervention, for a total of 24 sessions ... Frequency of attendance, medication changes, adverse events, etc. were ... duly recorded in the case report form
- `EV-129`（present）section=methods，para=sec011，xml_id=sec011
  - 摘录：app-based exercise therapy (40 minutes per session, 3 times per week), patient education (10 minutes, 1/week), WeChat video-based health coaching (20 minutes per session, 1/week)
- `EV-131`（present）section=methods，para=sec014，xml_id=sec014
  - 摘录：A group WeChat video was held once a week (each video lasts 40 minutes), which means 8 out of 24 sessions are supervised by therapists
- `EV-212`（absence）范围 section，检索词 number of therapists、therapist qualification、group size、progression rule…，结果 no_match

### [MAJOR] CL-009 · 开放标签+自报主要结局下 '保密假说' 偏倚控制无效

- 类别：blinding_bias；锚点：{"figure": null, "panel": null, "table": null, "paragraph_id": "sec009", "evidence_ref": "EV-124"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M6-102**（重要(major)，module=M6，category=`blinding_bias`，置信度 medium）
    - 主要结局（RMDQ/NRS/DASS21/SF-12/EARS）全部为患者自报且受试者明确知晓分组；sec009 以 '向评估者与受试者保密试验假设' 作为替代控制，对已知分组的自报结局无法防御期望/报告偏倚（RoB 2 下该类设计偏倚风险高）。
    - 复核：[P1] 在局限与偏倚讨论中明确自报结局+不盲受试者的偏倚方向；后续试验考虑中心化盲法评估或客观终点。（领域审稿人）
  - **M6-104**（重要(major)，module=M6，category=`randomization_concern`，置信度 medium）
    - ①Abstract 'randomized numeric table' vs sec006 计算机生成区组序列（SPSS）；②sec006 固定 block=4 vs sec008 'Permuted blocks of size 4 was used at random'；③sec007 信封隐藏 vs 现场拆封。固定区组 4 + 现场依次拆封 + 开放标签：入组医生在知晓既往分配后可推断区组内后续分配，构成可预测的选择偏倚通道；序列生成/封装由独立人员完成仅为部分缓解。
    - 复核：[P1] 请作者澄清随机化实际执行方式；评估入组顺序与区组末端分配的关系（敏感性分析）。（领域审稿人）
  - **M6-103**（重要(major)，module=M6，category=`protocol_change_undisclosed`，置信度 medium）
    - sec003 承认研究存在 'important changes' 并以将来时称将报批伦理——与已完成试验（2024-05-10 结束）矛盾；变更内容/时间/批件均未披露。注册库（WHO ICTRP）无任何修订记录、招募状态仍 Pending；注册库伦理批准日 2023-03-15 与正文伦理号 '2022 Review (1976)' 的口径不一致（或为修订批件，需澄清）。
    - 复核：[P0] 向作者/华西伦理委员会索取 '2022 Review (1976)' 批件与 2023-03-15 批准文件的对应关系（初批 vs 修订）及变更内容；核对注册记录是否应更新。（伦理委员会）
  - **M6-106**（重要(major)，module=M6，category=`consent_irregularity`，置信度 medium）
    - Discussion 披露 4 名受试者的知情同意与基线数据在线收集，与 sec004 的 'signing an informed consent form' 纸质程序不一致；未说明该方式是否获伦理批准（或即 'important changes' 之一，见 M6-103）、电子签署的身份核验与存档；发表同意为单数模板句（'the patient' vs N=78）；数据共享同意范围未说明（与 Dryad 公开数据相关）。
    - 复核：[P1] 请作者说明在线知情同意的伦理依据与记录方式；核对同意书是否涵盖数据公开共享。（伦理委员会）
  - **M6-107**（次要(minor)，module=M6，category=`registration_discrepancy`，置信度 high）
    - WHO ICTRP 证实 ChiCTR2300071560 存在且前瞻（注册 2023-05-18 < 首例入组 2023-05-20，标记 Prospective；样本量 39+39 一致；格式经 sequence_identifier_audit 合规）。残留：①正文治疗起始 2023-05-15 早于注册日且与注册库首例入组矛盾；②正文伦理号 '2022 Review (1976)' vs 注册库伦理批准日 2023-03-15；③招募状态仍 Pending、结果未发布；④注册机构名称两处表述不一。若作者确认治疗确于注册前开始，性质应升级。
    - 复核：[P2] 请作者澄清治疗实际起始日期与伦理批件对应关系；提醒注册库记录更新义务。（编辑）
  - **M6-105**（次要(minor)，module=M6，category=`consort_flow_gap`，置信度 medium）
    - 筛查 104 例中 22 不合格、2 拒绝均有类别，'2 exclusions' 未说明原因；7 名脱落者与 TUG 失访者的基线特征未报告，无法评估脱落偏倚。Fig 1（CONSORT 流程图）图像未提供，框内细节无法裁决（SYS-001）。
    - 复核：[P2] 补充筛查排除原因与脱落者基线特征表；图像补齐后与 Fig 1 对账。（作者）
  - **M6-110**（提示(info)，module=M6，category=`helsinki_statement_missing`，置信度 high）
    - 全文（declarations/methods）未见 Helsinki/赫尔辛基字样（ethics_rules#ETH-HUM-004）；伦理批准与知情同意实质要素均已报告，属声明完备性信息项，建议补充。
    - 复核：[P2] 在伦理声明中补充遵循《赫尔辛基宣言》的表述。（作者）

- 证据包：

- `EV-124`（present）section=methods，para=sec009，xml_id=sec009
  - 摘录：It is not possible for blind doctors and volunteers to do group assignments ... the trial hypothesis is specifically kept secret from both assessors and participants
- `EV-125`（present）section=methods，para=sec006，xml_id=sec006
  - 摘录：block randomization with a computer-generated random sequence. We chose 4 as the block
- `EV-127`（present）section=methods，para=sec008，xml_id=sec008
  - 摘录：Permuted blocks of size 4 was used at random ... assignment group was determined on-site by opening sealed and opaque envelopes
- `EV-122`（present）section=methods，para=sec003，xml_id=sec003
  - 摘录：prospectively approved by the Biomedical Ethics Committee of West China Hospital (number 2022 Review (1976)) and registered on the Chinese Clinical Trial Registry (ChiCTR2300071560). Treatment occurred from May 15th, 2023, through May 10th, 2024. There are important changes to the study that will be reported ... for approval
- `EV-300`（external）WHO ICTRP Trial Search Portal｜record=ChiCTR2300071560｜resolved｜sha256 `2153360a2b36…`｜2026-08-07T20:48:03Z
- `EV-123`（present）section=methods，para=sec004，xml_id=sec004
  - 摘录：Participants were considered dropouts if they: (1) abandoned the study; or (2) did not engage in any exercise session for 12 consecutive days in the EG or missed 4 consecutive scheduled sessions in the CG

### [MAJOR] CL-010 · COI/供应商角色不透明与编辑-引文关系

- 类别：coi_transparency；锚点：{"figure": null, "panel": null, "table": null, "paragraph_id": "ack1", "evidence_ref": "EV-143"}
- 关联判断（每条 finding 仅在此展开一次）：

  - **M6-108**（重要(major)，module=M6，category=`coi_transparency`，置信度 medium）
    - ①'Shu Kang PRO' 为 ShuKang 公司商业产品，致谢提及 'technical support'，但 COI 声明（'no competing interests'）与资助声明均未说明供应商角色（免费提供/商业合作/数据流经）；②fulltext.xml 显示 Özden Fatih 为本文 Editor（非作者，txt 作者列表为转换误并），其同类 RCT(ref45) 在 Discussion 被有利引用且未披露关系；③X1 核实 ref45 实为 single-blind、n=44，Discussion 却称 'double-blind...on 50 patients'——盲法与样本量均被夸大（方向均为增强引文证据强度）；④ref21(Nicholl) 实为系统综述，Introduction 描述为开发 app 的原始研究。建议编辑部核查编辑回避与引文更正。
    - 复核：[P1] 编辑部核查处理编辑是否应回避；请作者更正 ref45 转述并要求披露供应商角色。（编辑）
  - **M6-109**（次要(minor)，module=M6，category=`data_availability_issue`，置信度 high）
    - Data Availability 声称数据存于 https://doi.org/10.5061/dryad.zpc866tkh；X1 核验：Dryad 系统内记录存在（id 152010）但 'Identifier cannot be viewed'（embargo/权限），doi.org/DataCite/Crossref 解析均 404。论文 2025-06 发表，核验时（2026-08）仍不可公开访问——声明与事实不符（或长期未解除 embargo），并阻断对 AE 数据存在性、共享同意覆盖范围及全部数值疑点的外部复核。
    - 复核：[P2] 请编辑/作者确认 embargo 原因与解除时间，或更正数据可用性声明。（编辑）
  - **M4-107**（重要(major)，module=M4，category=`power_and_sample_size`，置信度 high）
    - sec026 以 'Murtezani's test results' 的效应量 0.3 计算样本量；X1 核实 ref35 为 McKenzie 疗法 vs 电物理因子治疗工作相关性腰痛的面对面 RCT（n=271），与本研究（远程结构化运动 vs 活性对照、CLBP）在设计/干预/对照/结局语境均不匹配，且未指明效应量对应哪个终点与何种统计量；多个结局与交互检验无效力说明。
    - 复核：[P1] 请作者说明效应量 0.3 的确切出处（终点、统计量）或重新论证；对次要结局与交互检验补充效力说明。（统计审稿人）
  - **M2-111**（次要(minor)，module=M2，category=`terminology_inconsistency`，置信度 high）
    - 各量表信效度引用经 X1 核验全部可解析（RMDQ 中文版研究、Ware SF-12 等）；残留问题：sec022 将 SF-12 归于 'Boston Institute of Health Education'（应通常归于 The Health Institute/New England Medical Center）；DASS-21/SF-12/EARS/NRS 是否使用经验证中文版本未逐一声明；无任何信效度数值。
    - 复核：[P2] 更正 SF-12 归属表述；逐量表注明中文版本与信效度来源。（作者）
  - **M2-112**（次要(minor)，module=M2，category=`terminology_inconsistency`，置信度 medium）
    - 多处表述实质影响理解：sec009 'It is not possible for blind doctors and volunteers...'（应为无法设盲）、sec028 'logical glitches such as required fields...'（按字面为故意设置逻辑缺陷，应为 logic checks）、sec014 'adhesion'（应为 adherence）、sec039 'blind interpolation'、sec002 'difference-test manner'；另 Abstract 与 Methods 注册机构名称不一致。
    - 复核：[P2] 系统语言修订并核对关键方法学术语。（作者）

- 证据包：

- `EV-143`（present）section=declarations，para=ack1，xml_id=ack1
  - 摘录：the technical support of the ShuKang company and Chong-Yang Wang team of Tsinghua University
- `EV-144`（present）section=conflict_of_interest，para=coi001，xml_id=coi001
  - 摘录：Competing Interests: The authors have declared that no competing interests exist（fulltext.xml fn coi001；fulltext.txt 转换丢失）
- `EV-145`（present）xml_id=contrib-group-editor
  - 摘录：fulltext.xml contrib-group content-type='editor': Özden Fatih, Editor, Mugla Sitki Kocman Universitesi（非本文作者；txt 头部误并入作者列表）
- `EV-110`（present）section=discussion，para=sec041-p6，xml_id=sec041
  - 摘录：a double-blind, two-armed randomized controlled trial by Fatih Özden on 50 patients with CLBP
- `EV-139`（present）section=data_availability，para=notes1，xml_id=notes1
  - 摘录：All dataset files are available from the Dryad repository at https://doi.org/10.5061/dryad.zpc866tkh
- `EV-120`（present）section=methods，para=sec026，xml_id=sec026
  - 摘录：Select 0.3 to verify the small to medium effect size, based on Murtezani's test results ... final calculated sample size was 58 ... 25% dropout rate ... 78

## 五、抽取信号

> 本节是机器观察与下游路由轨迹，不是稿件问题，不是 finding，没有 severity。共 20 条。

- `SIG-177` · `grim_incompatible_mean`：报告均值 3.47（n=39）在整数量表下不可能：不存在整数总和使其四舍五入到 2 位小数等于该值（n=34/36/38 可行）。
  - 目标：Table4 NRS CG baseline mean；路由：M4, M2；产出阶段：`stage_2`
- `SIG-178` · `grim_incompatible_mean`：报告均值 1.96（n=39）在整数量表下不可能；n=34–38 亦全部不可行——与任何合理分析集均不相容。
  - 目标：Table4 NRS CG 8wk mean；路由：M4, M2；产出阶段：`stage_2`
- `SIG-179` · `grim_incompatible_mean`：报告均值 43.68（n=39）在整数量表下不可能；仅与 n=34/37/38 相容——与 Table 5 标称 '*ITT analysis (N=78)' 矛盾。
  - 目标：Table5 EARS CG T1 mean；路由：M4, M2；产出阶段：`stage_2`
- `SIG-182` · `count_percentage_mismatch`：Discussion 报告 CG 脱落 18%，但 5/39=12.82% 落在舍入区间之外；18% 仅当分子取总脱落 7（7/39=17.9%）时成立。
  - 目标：Discussion CG dropout claim；路由：M4, M2；产出阶段：`stage_2`
- `SIG-202` · `grim_incompatible_mean`：1.96 在 n=34 下亦不可能。
  - 目标：NRS CG 8wk alt n=34；路由：M4；产出阶段：`stage_2`
- `SIG-204` · `grim_incompatible_mean`：3.47 在 n=35 下不可能。
  - 目标：NRS CG baseline alt n=35；路由：M4；产出阶段：`stage_2`
- `SIG-205` · `grim_incompatible_mean`：1.96 在 n=35 下不可能。
  - 目标：NRS CG 8wk alt n=35；路由：M4；产出阶段：`stage_2`
- `SIG-206` · `grim_incompatible_mean`：43.68 在 n=35 下不可能。
  - 目标：EARS CG T1 alt n=35；路由：M4；产出阶段：`stage_2`
- `SIG-208` · `grim_incompatible_mean`：1.96 在 n=36 下不可能。
  - 目标：NRS CG 8wk alt n=36；路由：M4；产出阶段：`stage_2`
- `SIG-209` · `grim_incompatible_mean`：43.68 在 n=36 下不可能。
  - 目标：EARS CG T1 alt n=36；路由：M4；产出阶段：`stage_2`
- `SIG-210` · `grim_incompatible_mean`：3.47 在 n=37 下不可能。
  - 目标：NRS CG baseline alt n=37；路由：M4；产出阶段：`stage_2`
- `SIG-211` · `grim_incompatible_mean`：1.96 在 n=37 下不可能。
  - 目标：NRS CG 8wk alt n=37；路由：M4；产出阶段：`stage_2`
- `SIG-214` · `grim_incompatible_mean`：1.96 在 n=38 下不可能。
  - 目标：NRS CG 8wk alt n=38；路由：M4；产出阶段：`stage_2`
- `SIG-219` · `test_statistic_p_mismatch`：由 EG 37.1±7.18 vs CG 41.51±7.41（各 n=39）反算 t=−2.669（df=76）得 p=0.0093，与正文 'P>0.05 基线可比' 声明不符——基线差异本身显著。
  - 目标：Baseline SF12-PCS between-group；路由：M4, M2；产出阶段：`stage_2`
- `SIG-255` · `table_total_mismatch`：若 7 名脱落者不提供任何随访数据，观测上限 (37+34)×3=213 < 声明 234；Cases 定义与缺失模式未披露，流程对账不闭合。
  - 目标：Table3 Cases=234 vs completers；路由：M4, M2；产出阶段：`stage_2`
- `SIG-257` · `table_total_mismatch`：按 Discussion '再失访 28' 口径 74+58+30=162 ≠ Table 3 TUG Cases=178；仅 '累计失访 28' 口径（74+58+46=178）闭合——两处失访叙述互斥。
  - 目标：TUG 'additional-28' reading；路由：M4, M2；产出阶段：`stage_2`
- `SIG-604` · `ethics_requirement_unmet`：伦理声明未见《赫尔辛基宣言》遵循表述（ethics_rules#ETH-HUM-004，severity_hint info）。
  - 目标：ethics.ETH-HUM-004；路由：M6；产出阶段：`stage_2`
- `SIG-603` · `partial_extraction`：知情同意豁免条款适用性事实（consent_waived）无法从结构化结果推出，未评估。
  - 目标：ethics.ETH-HUM-003；路由：M6；产出阶段：`stage_2`
- `SIG-606` · `partial_extraction`：个人健康数据去标识化条款适用性事实（uses_identifiable_data）无法可靠推出，未评估。
  - 目标：ethics.ETH-HUM-008；路由：M6；产出阶段：`stage_2`
- `SIG-608` · `partial_extraction`：中国人类遗传资源条款适用性事实无法可靠推出，未评估（本研究不涉及）。
  - 目标：ethics.ETH-HGR-001；路由：M6；产出阶段：`stage_2`

## 六、系统限制

> 本节说明系统或输入『哪些地方没看清』。这些条目不是稿件问题，不得据此推断作者遗漏或违规。共 7 条。

- `SYS-001` · `figure_unreadable`：Fig 1（CONSORT 流程图）与 Fig 2（ITT 结局箱线图）图像文件未提供：图内人数/数值与正文一致性、流程守恒、figure_integrity_audit 像素级审计均不可执行。相关裁决（CG 脱落 5 vs 7、失访时点分布）挂起。
  - 受影响模块：M2, M4, M5, M6, M7；目标：fig:Fig1, fig:Fig2；恢复动作：向作者/期刊调取 pone.0326218.g001.jpg 与 g002.jpg 原图后复核；在此之前不得据『未核验』推断图无误或图有误。
- `SYS-002` · `supplement_inaccessible`：Supporting information 9 项（S1 研究方案、S2 知情同意书、CONSORT 清单、PP 分析附表等）未提供：方案变更内容、电子知情同意覆盖范围、预设统计分析计划、EARS/TUG 的 PP 附表均无法核验。相关字段按 unresolved 处理，不判 not_reported。
  - 受影响模块：M2, M4, M6, M7；目标：supplement:S1-S9；恢复动作：索取 Supporting information 全部文件后复核；PLOS ONE 补充材料应随文可下载，当前仅有占位条目。
- `SYS-003` · `section_missing_from_input`：fulltext.txt 的 References 节为空、引用标记为 []、表格上标与 COI 脚注丢失（JATS 转换损失）；已通过解析 fulltext.xml 重建（48 条文献全部恢复、COI 脚注与编辑角色恢复），残留影响为表格 '*' 脚注锚定无法还原。
  - 受影响模块：M2, M5；目标：table:Table 3, table:Table 4, table:Table 5；恢复动作：对照原始 PDF/在线版核对 Table 3/4/5 上标锚定与 Table 2 Pain intensity 行 P 值原貌。
- `SYS-004` · `external_access_denied`：Dryad 数据集 doi:10.5061/dryad.zpc866tkh 处于 embargo/不可见（Dryad id 152010；doi.org/DataCite/Crossref 均 404）：个体水平数据不可复核，GRIM 不可能值的最终归因（转录错误 vs 数据/分析集错误）、个体 MCID 达到比例、分析集分母闭合均无法用原始数据裁决。
  - 受影响模块：M2, M4, M6；目标：dataset:10.5061/dryad.zpc866tkh；恢复动作：请编辑/作者确认 embargo 原因与解除时间；解除后复算 CG NRS 均值、EARS 分析集 n 与 AE/合并治疗字段。
- `SYS-005` · `external_source_unavailable`：ChiCTR 源注册库（chictr.org.cn）无可用 API/服务端渲染，仅能经 WHO ICTRP 快照核验（仅 22 个 WHO 元素，2023-06-12 刷新）：注册记录中的主要结局/次要结局/SAP 不可见，outcome_switching（结局切换）核验无法执行；招募状态 Pending 之后的更新不可见。
  - 受影响模块：M4, M6, M7；目标：registry:ChiCTR2300071560；恢复动作：人工登录 chictr.org.cn（proj=196969）比对注册主要结局与正文报告结局；核实注册记录是否应更新为完成状态。
- `SYS-006` · `external_source_unavailable`：external_figure_validation.py 的 trial_registration/outcome_switching 连接器仅覆盖 ClinicalTrials.gov（NCT），对 ChiCTR 注册号静默不处理；注册号核验改以 WHO ICTRP 人工查询完成，脚本化复算链不完整。
  - 受影响模块：M6；目标：tool:external_figure_validation；恢复动作：为 X1 增加 ChiCTR/ICTRP 连接器后重跑；当前以 EV-300 外部证据为准。
- `SYS-007` · `table_unparseable`：txt 转写存在系统性伪影（空引用标记、上标丢失、Table 1 内容重复块、Table 2/4 空单元格）：Table 4 各行 EG 侧部分单元格空缺、Table 5 Difference 列语义、Table 2 Pain intensity 行 P 列是否为真缺失，均需原始文档裁决。
  - 受影响模块：M4, M5；目标：table:Table 2, table:Table 4, table:Table 5；恢复动作：调取原始 PDF/JATS（DOI 10.1371/journal.pone.0326218）复核上述单元格原貌。

## 七、覆盖率明细

| 子率 | 分子 / 分母（rate） |
| --- | ---: |
| 条件必填字段解析率 | 23/27（0.852） |
| 图表可读率 | 0/2（0.0） |
| 补充材料可得率 | 0/9（0.0） |

- 已解析的条件必填字段：23 项
- 未解析的条件必填字段：objective.primary_endpoint(conflicting), measurement.statistical_methods(ambiguous), design_specific.protocol_changes(ambiguous), declarations.conflict_of_interest(conflicting)
- 不可读图表：fig:Fig1, fig:Fig2
- 不可得补充材料：9 项（S1–S9）

> `not_reported` 表示已完成规定范围检索并确认稿件未报告；`parse_failed` 表示系统没读出来。两者不得互换。

## 八、人工复核建议

| 优先级 | 排序依据 | 完成时点 |
| --- | --- | --- |
| P0 | 全部 critical；以及不先核对就无法可靠解释核心结论、伦理授权或数据完整性的 major | 形成审稿结论前 |
| P1 | 其他 major：会改变 finding 成立、严重度或需作者补分析/材料 | 给出修改要求前 |
| P2 | minor/info 的报告澄清、定位核对或编辑性修正 | 常规修订清单中 |

### [ ] [P0] 裁决 EARS 表-文矛盾：调取原始数据复核 Table 5 各时点组间比较；更正摘要/结论的依从性表述

- 执行者：统计审稿人
- 逐 finding 核对包：

  - **M2-101**（严重(critical)）Table 5(EARS) 表-正文-摘要矛盾：表示组间显著，正文/摘要称无差异
    - Table 5 显示 EARS 在 T1（Z=−5.5，P<0.001）与 T2（Z=−3.19，P=0.001）均为 EG 更优的显著组间差异；Z=1.91（P=0.06）是组内变化量（Difference）的组间比较。sec040、Discussion、Abstract 却称 4/8 周组间『无显著差异(P>0.05)』，Abstract 并把 Z=1.91 误归为组内时间效应。确定性 Z→P…
    - 证据：[EV-100｜present｜results/Table 5] [EV-101｜present｜results/sec040] [EV-102｜present｜abstract/abstract-results] [EV-103｜present｜abstract/abstract-conclusion]

### [ ] [P0] 分析集与数据完整性裁决：GRIM 不可能值、ITT/PP 标注、Cases=234 对账；澄清前相关定量结论暂缓

- 执行者：统计审稿人
- 逐 finding 核对包：

  - **M4-108**（重要(major)）GRIM/算术不可能值聚簇：Table 5 'ITT' 标签被证伪
    - 确定性核验：①Table 5 标 '*ITT'，但 CG T1 均值 43.68±3.5 与 n=39 数学不相容（整数条目量表），仅与 n=34/37/38 相容——n=34 恰为 CG 完成者数，强烈提示该表实为完全病例分析误标 ITT；②NRS CG 基线 3.47 在 n=39 不可能（n=34/36/38 可行）；③NRS CG 8 周 1.96 在 n=34–39 全部不可能（最强违规…
    - 证据：[EV-100｜present｜results/Table 5] [EV-116｜present｜results/Table 4]
  - **M5-101**（重要(major)）ITT/PP 标注混乱：标题与脚注矛盾、'*' 锚点丢失
    - Table 3 标题 (N=78) 与 TUG Cases=178（PP，仅上标区分）混排；Table 4 标题 '*ITT analysis' 与脚注 'Linear mixed-effects model based on PP analysis' 并存且 '*' 在表内无可见锚点；Table 5 caption '*ITT analysis' 无对应脚注；Fig 2 caption 声称 I…
    - 证据：[EV-115｜present｜results/Table 3] [EV-116｜present｜results/Table 4] [EV-100｜present｜results/Table 5] [EV-137｜present｜results/sec039]
  - **M2-113**（重要(major)）Table 3 Cases=234 与 7 例脱落不闭合
    - Table 3 各指标 Cases=234=78×3，暗示全部随机者贡献全部三时点观测；但 sec033 报告脱落 EG 2、CG 5。确定性核算（SIG-255）：若脱落者无随访数据，观测上限 (37+34)×3=213<234；若 'Cases' 指模型纳入记录数，则其定义与缺失模式未披露。结合 NRS CG 基线 GRIM 仅容 n=34/36/38（SIG-177），分析集构成不可识别，直…
    - 证据：[EV-115｜present｜results/Table 3] [EV-117｜present｜results/sec033] [EV-119｜present｜methods/sec030]

### [ ] [P0] PCS 基线不均衡的校正分析（ANCOVA/回归均值敏感性）与多重性校正后重报

- 执行者：统计审稿人
- 逐 finding 核对包：

  - **M4-104**（重要(major)）SF-12-PCS 基线显著不均衡且主分析未校正
    - 基线 PCS EG 37.1±7.18 vs CG 41.51±7.41（差 4.41），确定性重算 t=−2.669、df=76、p=0.0093（SIG-219）：sec034『基线各指标无显著差异、可比』对该指标为假。8 周两组原始均值几乎相同（46.85 vs 46.80），未调整 LMM 的 +4.5 变化差全部利于基线较低组，回归均值未排除；模型未纳入基线值/预后因素。
    - 证据：[EV-116｜present｜results/Table 4] [EV-118｜present｜results/sec034] [EV-114｜present｜results/Table 2]
  - **M4-103**（重要(major)）多重性未校正：PCS P=0.006 校正后可能不显著
    - 6 结局×3 时间点×组/时间/交互多重检验均按双侧 α=0.05 无校正，统计分析节亦无预定义主对比层级（absence 检索确认）。SF-12-PCS 组间 P=0.006 为三项优效结论中边际最小者，经 Bonferroni/Holm 类校正后可能不再显著。
    - 证据：[EV-119｜present｜methods/sec030] [EV-207｜缺失检索｜结果 no_match] [EV-115｜present｜results/Table 3] [EV-148｜present｜results/sec035-038]

### [ ] [P0] 补充 CONSORT harms 要求的不良事件汇总报告

- 执行者：作者
- 逐 finding 核对包：

  - **M6-101**（重要(major)）不良事件零报告且有无据安全性主张
    - Methods sec010/sec025 预设 AE 记录于 CRF 并描述两组伤害风险缓解措施，但 Results/Discussion 对 AE 零报告（absence 检索覆盖 Results 全文与 Table 3-5）；Discussion 反称视频监督 'decreased risk of sports injuries'。违反 CONSORT 2010 harms 扩展；8 周运动…
    - 证据：[EV-128｜present｜methods/sec010] [EV-135｜present｜methods/sec025] [EV-200｜缺失检索｜结果 no_match] [EV-107｜present｜discussion/sec041-p2]

### [ ] [P0] 索取伦理批件（2022 vs 2023-03-15）与方案变更内容；核实在线知情同意合规性

- 执行者：伦理委员会
- 逐 finding 核对包：

  - **M6-103**（重要(major)）方案 'important changes' 未披露，与注册库记录及已完成试验状态矛盾
    - sec003 承认研究存在 'important changes' 并以将来时称将报批伦理——与已完成试验（2024-05-10 结束）矛盾；变更内容/时间/批件均未披露。注册库（WHO ICTRP）无任何修订记录、招募状态仍 Pending；注册库伦理批准日 2023-03-15 与正文伦理号 '2022 Review (1976)' 的口径不一致（或为修订批件，需澄清）。
    - 证据：[EV-122｜present｜methods/sec003] [EV-300｜WHO ICTRP Trial Search Portal｜resolved｜2026-08-07] [EV-149｜present｜supporting-info-list]
  - **M6-106**（重要(major)）4 例在线知情同意与预设纸质程序不一致
    - Discussion 披露 4 名受试者的知情同意与基线数据在线收集，与 sec004 的 'signing an informed consent form' 纸质程序不一致；未说明该方式是否获伦理批准（或即 'important changes' 之一，见 M6-103）、电子签署的身份核验与存档；发表同意为单数模板句（'the patient' vs N=78）；数据共享同意范围未说明（与 …
    - 证据：[EV-108｜present｜discussion/sec041-p4] [EV-123｜present｜methods/sec004] [EV-138｜present｜methods/sec031]

### [ ] [P1] TUG 终点：分母对账、远程测量方案、ITT 补充分析后再评价 '步行能力等效' 结论

- 执行者：统计审稿人
- 逐 finding 核对包：

  - **M2-102**（重要(major)）TUG 分母四套口径互斥、表文对账不可闭合
    - TUG 出现四套口径：Table 3 Cases=178；Table 4 8 周 n=10/12（合计 22）；sec039『4 周失访 16、8 周失访 28』；Discussion『基线 74、再失访 28』。确定性核算（SIG-257）：仅『累计 28』口径 74+58+46=178 闭合，『additional 28』口径=162 不符；Table 4 的 n=10/12 与任一口径均不相…
    - 证据：[EV-115｜present｜results/Table 3] [EV-116｜present｜results/Table 4] [EV-137｜present｜results/sec039] [EV-108｜present｜discussion/sec041-p4]
  - **M2-110**（重要(major)）TUG 远程视频测评方法学缺失
    - sec028 允许在线受试者经视频会议完成 TUG，但远程计时的标准化方案（指令、摄像头距离、计时方式、质量控制、信效度）均未报告；现场/远程混合的模式效应未讨论；Discussion 自述 4 例因场地限制未测。该终点（并见 M2-102/M4-101）的数据质量基础不成立。
    - 证据：[EV-136｜present｜methods/sec028] [EV-137｜present｜results/sec039] [EV-108｜present｜discussion/sec041-p4]
  - **M4-101**（重要(major)）TUG 背离预设 ITT 主分析集：仅 PP、信息性缺失、无敏感性分析
    - sec030 预设 ITT 为主分析集，但 TUG 以缺失多为由仅报 PP（8 周 n=10/12），未做插补或敏感性分析；失访理由含『症状显著改善』（SIG-257 相关叙述），属结局相关的信息性缺失（MNAR 方向偏向高估改善）；该 PP 结果仍被 Abstract/Conclusion 作为『步行能力等效』的正式结论。
    - 证据：[EV-119｜present｜methods/sec030] [EV-137｜present｜results/sec039] [EV-108｜present｜discussion/sec041-p4] [EV-103｜present｜abstract/abstract-conclusion]

### [ ] [P1] 干预剂量对账（场次/时长）与 TIDieR 要素补充

- 执行者：领域审稿人
- 逐 finding 核对包：

  - **M2-103**（重要(major)）干预总场次跨节矛盾（8 周会话 vs 24 sessions vs 40/32 口径）
    - Abstract 称 'eight weekly sessions'；sec010 称 8 周共 24 sessions；sec014 称 24 次中 8 次受监督；按 sec011/sec015 组分换算 EG=运动 24+教育 8+教练 8=40 次接触、CG=24+8=32 次。多套口径互斥，实际递送剂量不可重建，直接影响两臂可比性与 Discussion 'similar treatmen…
    - 证据：[EV-104｜present｜abstract/abstract-methods] [EV-128｜present｜methods/sec010] [EV-129｜present｜methods/sec011] [EV-131｜present｜methods/sec014]
  - **M2-104**（次要(minor)）干预剂量细节不一致（教练 20 vs 40 分钟、单次 40 vs 40–60、three parts 实列四项）
    - sec011 教练 20 分钟/次 vs sec014 每次视频 40 分钟；sec011 运动 40 分钟/次 vs sec012 40–60 分钟；sec012 称初诊指导 'in three parts' 实列四项。
    - 证据：[EV-129｜present｜methods/sec011] [EV-130｜present｜methods/sec012] [EV-131｜present｜methods/sec014]
  - **M2-108**（重要(major)）TIDieR/CONSORT 干预报告要素缺失
    - 干预描述缺少 TIDieR 关键要素：治疗师人数/资质、团体视频参与人数、运动处方进阶规则、健康教练内容标准化、执行保真度核查（absence 检索确认）；Introduction 宣称的 'dynamic videoconferencing monitoring' 在 Methods 无操作对应。CONSORT 清单虽列为补充材料（未提供），正文逐项落实存在缺口（见 M6-106 等）。
    - 证据：[EV-128｜present｜methods/sec010] [EV-129｜present｜methods/sec011] [EV-131｜present｜methods/sec014] [EV-212｜缺失检索｜结果 no_match]

### [ ] [P1] 评估开放标签+自报结局+随机化可预测性对主要结论的偏倚影响

- 执行者：领域审稿人
- 逐 finding 核对包：

  - **M6-102**（重要(major)）开放标签+自报主要结局下 '保密假说' 偏倚控制无效
    - 主要结局（RMDQ/NRS/DASS21/SF-12/EARS）全部为患者自报且受试者明确知晓分组；sec009 以 '向评估者与受试者保密试验假设' 作为替代控制，对已知分组的自报结局无法防御期望/报告偏倚（RoB 2 下该类设计偏倚风险高）。
    - 证据：[EV-124｜present｜methods/sec009] [EV-140｜present｜methods/sec019-024] [EV-112｜present｜discussion/sec041-limitations]
  - **M6-104**（重要(major)）随机化描述三重矛盾与分配可预测性
    - ①Abstract 'randomized numeric table' vs sec006 计算机生成区组序列（SPSS）；②sec006 固定 block=4 vs sec008 'Permuted blocks of size 4 was used at random'；③sec007 信封隐藏 vs 现场拆封。固定区组 4 + 现场依次拆封 + 开放标签：入组医生在知晓既往分配后可推断区组…
    - 证据：[EV-104｜present｜abstract/abstract-methods] [EV-125｜present｜methods/sec006] [EV-126｜present｜methods/sec007] [EV-127｜present｜methods/sec008]

### [ ] [P1] 结论措辞整改：等效/额外贡献/推广/对照界定/局限方向/MCID 表述

- 执行者：领域审稿人
- 逐 finding 核对包：

  - **M7-104**（重要(major)）'equally effective/等效' 结论无等效或非劣检验支撑
    - Abstract/Conclusion 对 DASS21、MCS、TUG、EARS 以 'equally effective/equivalent' 表述组间无差异；试验按优效设计估算样本量，全文无预设等效/非劣界值、无相应检验（absence 检索确认）；TUG PP n=10/12、EARS 样本小效力不足。不显著≠等效；Discussion 'viable alternative' 推断链同…
    - 证据：[EV-103｜present｜abstract/abstract-conclusion] [EV-105｜present｜conclusion/sec042] [EV-208｜缺失检索｜结果 no_match] [EV-120｜present｜methods/sec026]
  - **M7-105**（重要(major)）Discussion 'additional contribution' 与自身阴性结果直接矛盾
    - sec041 首段称结果 'confirmed the additional contribution of telemedicine ... in disability, pain, mental health status, quality of life and walking ability'；但 Table 3 组间效应 DASS21 P=0.63、MCS P=0.83、TUG P=0.…
    - 证据：[EV-106｜present｜discussion/sec041-p1] [EV-115｜present｜results/Table 3]
  - **M7-106**（重要(major)）结论外推过度（单中心/开放标签/8 周/年轻高教育样本）
    - 单中心特需门诊、开放标签、仅 8 周随访、中位年龄 EG 27/CG 22 岁、本科以上 84.6%/89.7%、61.5–74.4% 经未定义 'Other' 渠道招募；Conclusion/Abstract 却称方案 'could reduce the burden'、'could be considered to be promoted in clinical applications'——…
    - 证据：[EV-103｜present｜abstract/abstract-conclusion] [EV-105｜present｜conclusion/sec042] [EV-113｜present｜discussion/sec041-p9] [EV-114｜present｜results/Table 2]
  - **M7-102**（重要(major)）'usual care' 标签不准确：对照实为活性对照，优效结论外推含义被夸大
    - CG 实际接受与 EG 相同的 app 教育 + 同动作同频次纸质运动处方（sec015/sec016），属结构性活性对照；标题/摘要/结论通篇称 'usual care therapy'，使 'more effective than usual care' 被读作优于常规临床诊疗的证据。Discussion 对 Fanuscu/Shi 的对照强度解释恰好反证优效结论由对照强度决定。
    - 证据：[EV-132｜present｜methods/sec015] [EV-133｜present｜methods/sec016] [EV-103｜present｜abstract/abstract-conclusion] [EV-105｜present｜conclusion/sec042]
  - **M7-103**（重要(major)）接触时间/注意力不匹配且 'similar treatment doses' 无据，归因主张与设计不对齐
    - EG 每周团体视频教练+app 目标提醒 vs CG 初诊后 'no further teaching unless requested'；接触量/注意力系统性不匹配，显著组间差异可能部分来自接触量与期望效应；Discussion 未将其列为局限，反称两组 'similar treatment doses administered'（该句本身与干预描述不符）；客观依从数据（app 日志/出勤）可得…
    - 证据：[EV-131｜present｜methods/sec014] [EV-133｜present｜methods/sec016] [EV-106｜present｜discussion/sec041-p1] [EV-134｜present｜methods/sec017]
  - **M7-107**（重要(major)）局限方向写反：智能手机要求实际排斥弱势群体
    - Discussion 称智能手机使用要求 'may have limited participation to individuals with lower socioeconomic status and education levels'——方向相反：'能操作智能手机' 是纳入标准，排斥的是数字弱势群体；Table 2 本科以上占 84.6%/89.7% 印证样本系统性偏高教育，该选择偏倚未被…
    - 证据：[EV-112｜present｜discussion/sec041-limitations] [EV-114｜present｜results/Table 2] [EV-123｜present｜methods/sec004]
  - **M7-101**（重要(major)）NRS MCID 声称与自家数据确定性不符
    - Discussion 称『两组 NRS 均改善超过 2 分达到 MCID』；X1 核实 ref37(Ostelo) 确为 MIC 共识（引用类型恰当），但 Table 4 CG 均值 3.47→1.96，实测改善 1.51 分 <2（GRIM 候选修正值下为 1.49–1.54，仍 <2，对转录误差稳健）；EG 仅报中位数口径。临床意义声称对 CG 不成立。
    - 证据：[EV-106｜present｜discussion/sec041-p1] [EV-116｜present｜results/Table 4] [EV-973｜Crossref｜resolved｜2026-08-07] [EV-974｜Europe PMC｜resolved｜2026-08-07]

### [ ] [P1] 统计方法透明化：模型设定、estimand、汇总口径、基线推断

- 执行者：统计审稿人
- 逐 finding 核对包：

  - **M4-105**（重要(major)）统计模型细节完全缺失，效应估计不可复核
    - sec030 声称满足假设用重复测量 ANOVA、否则混合模型，但结果（Table 3/4 脚注）一律为复合对称 LMM：前提检验、固定效应结构、时间编码、协变量、缺失机制（MAR）假设、模型诊断、任何敏感性分析均未报告（absence 检索确认）。
    - 证据：[EV-119｜present｜methods/sec030] [EV-206｜缺失检索｜结果 no_match] [EV-115｜present｜results/Table 3] [EV-116｜present｜results/Table 4]
  - **M4-106**（重要(major)）Estimand 未定义：RMDQ −3.96 无法由表内数据复核
    - 'estimated value' 未说明是组间变化差、校正端点差还是边际均值差；Table 3 的组主效应 P（RMDQ 0.04）与正文组间对比 P（<0.001）共用 'between-group' 之名而行不同 estimand；主要终点 RMDQ 模型估计 −3.96 与中位数口径变化差（约 −2）差距大，且表内只报中位数/IQR。CI 自洽性核验通过，排除区间抄写错误，不可复核性源于模…
    - 证据：[EV-116｜present｜results/Table 4] [EV-115｜present｜results/Table 3] [EV-148｜present｜results/sec035-038] [EV-121｜present｜methods/sec018]
  - **M4-109**（重要(major)）Table 4/5 均值/中位数混用且分布判断口径矛盾
    - 同一指标跨组混用汇总统计量：NRS 基线 EG 3.5(3-5)（中位数）vs CG 3.47±1.28（均值），8 周 EG 0.5(0.25-1) vs CG 1.96±1.03；MCS 8 周与基线口径互异；TUG 8 周 EG 中位数 vs CG 均值；Table 5 CG T1 均值±SD vs T2 中位数。NRS 为 0–10 整数（入组≥3，地板效应），EG 按偏态报中位数、CG …
    - 证据：[EV-116｜present｜results/Table 4] [EV-100｜present｜results/Table 5] [EV-119｜present｜methods/sec030]
  - **M4-110**（重要(major)）基线可比性推断不当与 Table 2 缺陷
    - sec034 以 P>0.05 'confirming their comparability'（不显著≠可比；且 PCS 基线实算 p=0.0093，见 M4-104）；Table 2 'Pain intensity' 行缺 P 值且等级界值未定义（纳入已要求 NRS≥3，'mild' 对应区间不明）；Education 2×6 表 8/12 格期望频数<5、Smoking 期望格 4.5<5，…
    - 证据：[EV-118｜present｜results/sec034] [EV-114｜present｜results/Table 2]

### [ ] [P1] 样本量依据出处说明；供应商角色披露与编辑-引文关系核查（含 ref45 转述更正）

- 执行者：编辑
- 逐 finding 核对包：

  - **M4-107**（重要(major)）样本量依据引用与研究语境不符
    - sec026 以 'Murtezani's test results' 的效应量 0.3 计算样本量；X1 核实 ref35 为 McKenzie 疗法 vs 电物理因子治疗工作相关性腰痛的面对面 RCT（n=271），与本研究（远程结构化运动 vs 活性对照、CLBP）在设计/干预/对照/结局语境均不匹配，且未指明效应量对应哪个终点与何种统计量；多个结局与交互检验无效力说明。
    - 证据：[EV-120｜present｜methods/sec026] [EV-969｜Crossref｜resolved｜2026-08-07] [EV-970｜Europe PMC｜resolved｜2026-08-07]
  - **M6-108**（重要(major)）COI/供应商角色不透明与编辑-引文关系
    - ①'Shu Kang PRO' 为 ShuKang 公司商业产品，致谢提及 'technical support'，但 COI 声明（'no competing interests'）与资助声明均未说明供应商角色（免费提供/商业合作/数据流经）；②fulltext.xml 显示 Özden Fatih 为本文 Editor（非作者，txt 作者列表为转换误并），其同类 RCT(ref45) 在 D…
    - 证据：[EV-144｜present｜conflict_of_interest/coi001] [EV-143｜present｜declarations/ack1] [EV-145｜present｜contrib-group-editor] [EV-110｜present｜discussion/sec041-p6]

### [ ] [P1] 报告随机化后合并治疗发生率与类型

- 执行者：作者
- 逐 finding 核对包：

  - **M2-105**（重要(major)）合并治疗承诺记录但零报告；基线止痛药使用不均
    - sec017 允许病情恶化时使用药物/物理治疗并承诺记录于 CRF，但 Results 对随机化后合并治疗零报告（absence 检索确认）；Table 2 基线止痛药 EG 35.9% vs CG 28.2%，试验期用药变化未报告，可能混杂 NRS/主结局的组间比较。
    - 证据：[EV-134｜present｜methods/sec017] [EV-201｜缺失检索｜结果 no_match] [EV-114｜present｜results/Table 2]

### [ ] [P2] P2 澄清与编辑性修订清单（终点层级/脱落标准/4 周结果/流程细节/数据声明/拼写）

- 执行者：作者
- 逐 finding 核对包：

  - **M2-106**（次要(minor)）主要终点 'disability including pain' 与 NRS 构念重叠、estimand 未分离
    - 主要终点 RMDQ 的 24 项全部以 'because of my back pain' 限定，与并列报告的 NRS 疼痛构念重叠；优效假设写为 'disability including pain'，结论却分别以 disability 与 pain 两个名义各报告一次优效，存在重复计数风险。可复核性核心问题由 M4-106 承载。
    - 证据：[EV-121｜present｜methods/sec018] [EV-147｜present｜introduction/sec001-objective] [EV-140｜present｜methods/sec019-024]
  - **M2-107**（次要(minor)）脱落判定标准两组不对称
    - EG 脱落标准为 '连续 12 天未进行任何运动'（行为导向），CG 为 '连续缺席 4 次 scheduled sessions'（出勤导向）；CG 为无监督自定节奏居家训练，'scheduled sessions' 无操作定义。两臂阈值不对称，污染脱落率（5.1% vs 12.8%）与依从性比较的可比性。
    - 证据：[EV-123｜present｜methods/sec004] [EV-133｜present｜methods/sec016]
  - **M2-109**（次要(minor)）4 周（治疗中期）组间结果未报告
    - 数据采集于 baseline/4w/8w 三时点（Table 3 Cases=234 表明 4 周数据进入模型），但除 EARS T1 外所有结局均未报告 4 周组间/组内估计。sec018 已预设基线-8 周为主要对比，故降为 minor；报告不对称仍限制疗效时间轨迹的解读与选择性呈现的排除。
    - 证据：[EV-121｜present｜methods/sec018] [EV-115｜present｜results/Table 3] [EV-204｜缺失检索｜结果 no_match]
  - **M6-105**（次要(minor)）流程报告缺陷：2 exclusions 无原因、脱落者基线未报
    - 筛查 104 例中 22 不合格、2 拒绝均有类别，'2 exclusions' 未说明原因；7 名脱落者与 TUG 失访者的基线特征未报告，无法评估脱落偏倚。Fig 1（CONSORT 流程图）图像未提供，框内细节无法裁决（SYS-001）。
    - 证据：[EV-117｜present｜results/sec033] [EV-209｜缺失检索｜结果 no_match] [EV-210｜缺失检索｜结果 no_match]
  - **M6-109**（次要(minor)）数据可用性声明不可核验（Dryad embargo/404）
    - Data Availability 声称数据存于 https://doi.org/10.5061/dryad.zpc866tkh；X1 核验：Dryad 系统内记录存在（id 152010）但 'Identifier cannot be viewed'（embargo/权限），doi.org/DataCite/Crossref 解析均 404。论文 2025-06 发表，核验时（2026-08）仍…
    - 证据：[EV-139｜present｜data_availability/notes1] [EV-301｜Dryad API v2｜resolved｜2026-08-07] [EV-302｜DataCite｜not_found｜2026-08-07] [EV-303｜Crossref｜not_found｜2026-08-07]
  - **M6-110**（提示(info)）赫尔辛基宣言声明缺失
    - 全文（declarations/methods）未见 Helsinki/赫尔辛基字样（ethics_rules#ETH-HUM-004）；伦理批准与知情同意实质要素均已报告，属声明完备性信息项，建议补充。
    - 证据：[EV-122｜present｜methods/sec003] [EV-205｜缺失检索｜结果 no_match]
  - **M6-111**（次要(minor)）无 DSMB/独立安全监测披露
    - 全文与注册记录均未提及数据监查委员会、中期监查或停止规则；低风险行为干预下非强制，但叠加 AE 承诺记录却零报告（M6-101），安全监测可信度进一步降低。
    - 证据：[EV-203｜缺失检索｜结果 no_match] [EV-135｜present｜methods/sec025]
  - **M5-102**（次要(minor)）细节错误：'Mann-Whiteney' 拼写、Table 5 Difference 列含义未定义、缺逐时点 n
    - Table 5 脚注 'Mann-Whiteney U test' 拼写错误；'Difference' 列含义（组内变化 T2−T1 的组间比较）未在表内定义，而该列携带 Abstract 唯一引用的 EARS 统计量（Z=1.91/P=0.06）；Table 3/4/5 均未报告逐组逐时点 n，与分析集判定困难（M4-108/M5-101）交互；'~' 与 '-' IQR 记法跨表不统一。
    - 证据：[EV-100｜present｜results/Table 5] [EV-115｜present｜results/Table 3] [EV-116｜present｜results/Table 4]

## 附录 A · 运行时遥测与加法保证自检

- 子会话：L0、L0b、M2、M4、M5、M6、M7、L4 校正，共 child_sessions=8；task_calls=13（首次 8 + 续接 5：M2/M4/M5/M6/M7 各经同一 task_id 带确定性证据复议 1 次）；continuations=5。modules_run=[M2,M4,M5,M6,M7]；modules_skipped={M3: 无动物/细胞/湿实验成分}。
- 路由要求读的规则库：02-macro-logic, 04-statistics, 05-figures-and-charts, 06-ethics-compliance, 07-conclusions-discussion；实际读取：02-macro-logic, 04-statistics, 05-figures-and-charts, 06-ethics-compliance, 07-conclusions-discussion（路由召回率 1.0）。
- 要求执行的确定性脚本：7 个；实际执行：7 个（figure_integrity_audit 因无图像空扫、animal_model_compliance 人体研究无信号、normalize_biomed_units 无药理剂量单位对——均以终态登记，无静默缺失）。
- L0 全局审阅条目：46 条；其中 confirm/promote 40、merge 5、blocked_by_system_limitation 1、rejected 0。
- 加法保证（§6.2）：L0 的 46 条 G 条目全部在 candidate_resolution_log 中有明确终态——promoted_to_finding 40、merged 5（G-16→M7-103、G-30→M2-101、G-37→M2-104、G-43→M7-106、G-45→M6-108）、blocked_by_system_limitation 1（G-42 无图像）、rejected 0。无任何 G 条目不明不白消失；severity 被调整处（G-21/G-26/G-31/G-34/G-39/G-40/G-41/G-46）均在台账记录理由。最终 43 条 finding = G 条目晋升/合并 + 专家与确定性工具新增，故最终结果 ⊇ L0 结论（0 条被驳回）。`additive_guarantee_held = true`。
- finding 来源分布：{"multiple_sources": 25, "deterministic_tool": 4, "cross_section_reconciliation": 1, "global_review": 8, "external_validation": 5}。其中仅 global_review 独有 = 裸模型本来就有的下限；deterministic_tool / external_validation / specialist_rule / cross_section_reconciliation 独有部分为本架构增益。
- 工具信号：20 条（GRIM×9、test_statistic_p×1、count_percentage×1、table_total×2、ethics×4、其余为部分抽取/通过项）。
