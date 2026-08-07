# 审阅过程记录 · PMC13254492

> **论文**：Effects of Celecoxib and Etoricoxib on the Pharmacokinetics and Pharmacological Effects of Orally Administered Tramadol: A Randomised Controlled Trial.  
> **期刊 / 年份**：None · 2026  
> **错误类型**：`retrospective_registration`  
> **标准答案出题人**：ClinicalTrials.gov

## 标准答案

本文声称的注册号 NCT01304069 的注册日期为 2011-02-24，晚于研究开始日期 2011-01 —— 属回顾性注册，不符合 ICMJE 的前瞻性注册要求。注册日期只存在于注册库，正文通常不写。

判定只问一件事：审稿意见有没有**实质性**指出这个问题。只提到名词、或给「建议核对一下」这类通用建议，都不算命中 —— 那种话几乎每份意见都会写，算进去 uplift 就被稀释没了。

---

## 裸模型（baseline）

**工具调用 2 次**

| # | 工具 | 参数（截断） | 状态 |
| --- | --- | --- | --- |
| 1 | `bash` | {"command": "ls -la"} | completed |
| 2 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/baseline/fulltext.txt"} | completed |

### 最终审稿意见

```markdown
作为资深同行评审,我对这篇 COX‑2 抑制剂(塞来昔布/依托考昔)对曲马多及其活性代谢物药代动力学影响的随机交叉研究进行了审阅。问题按严重程度排列如下。

## 一、严重问题(影响结果可信度,须逐条澄清或修正)

**1. 表 1 中多个 p 值与所报告的 GMR 90% CI 系统性矛盾,疑似存在系统性小数点错位**

- 位置:第 3.2 节表 1(第 71 行)。
- 依据:曲马多 AUC₀₋∞ GMR 1.13(1.06–1.21)却报 p=0.765;Cmax GMR 1.08(0.99–1.18)报 p=0.862;t₁/₂ GMR 1.06(1.01–1.12)报 p=0.804;依托考昔 t₁/₂ GMR 1.06(1.02–1.10)报 p=0.836;代谢物 t₁/₂ 塞来昔布 GMR 1.08(1.03–1.14)报 p=0.69、依托考昔 GMR 1.06(0.99–1.14)报 p=0.809。90% CI 已完全落在 1 的一侧时,p 值不可能高达 0.69–0.86。这些数值若把小数点左移一位(0.0765、0.0862、0.0804、0.069、0.0809、0.0836)则与 CI 完全吻合,提示系统性录入错误。
- 为什么重要:p 值与效应估计来自同一数据,二者不可能如此背离。要么 p 值列整体有误,要么 p 值与 GMR 来自不同尺度/不同模型却未说明,直接动摇整个结果表的可信度,必须用原始数据核验。

**2. 表 1 中依托考昔组 O‑desmethyltramadol t₁/₂ "2.6 (0.7) h" 自相矛盾,几乎可肯定是数据错误**

- 位置:表 1,代谢物 t₁/₂ 行。
- 依据:安慰剂组 5.6 (1.1) h、塞来昔布组 6.1 (1.3) h,而依托考昔组报 2.6 (0.7) h,但同行 p=0.809、GMR 1.06(0.99–1.14)。若均值真从 5.6 降到 2.6,p 应远小于 0.001,GMR 也应约 0.46 而非 1.06。
- 为什么重要:这是结果表中一眼可见的内部矛盾,属于数据完整性问题;审稿人和读者会据此怀疑数据核对质量。

**3. 表 2 列标题错误:"几何均数比(90% CI)"列中出现不可能为负数的"比值"**

- 位置:表 2,Drug effect (VAS) 行;方法与表不一致也涉及 2.7 节。
- 依据:该行报告 3.29(−87.89, 94.47)和 22.13(−69.06, 113.31)——几何均数比不可能为负值,这显然是均数差。尽管 2.7 节写明"非严格阳性终点报告均数差",表头却统一标注为"GMR",且按方法 VAS AUEC 本应属阳性终点。
- 为什么重要:效应尺度与方向被错误标注,可能误导读者对该终点结果的解读;也说明统计报告流程缺乏一致性核查。

**4. 交叉设计的统计分析不完整、不透明**

- 位置:2.7 节;结果表 1/表 2。
- 依据:仅写"repeated-measures ANOVA",未说明模型是否包含序列(sequence)与周期(period)效应,未做残留效应(carry-over)检验;未说明 PK 变量的 ANOVA 是否在对数尺度上进行;表 1 同时给出(疑似原始尺度的)p 值和(对数尺度的)GMR,两套推断框架混用且互不吻合;多个 PK/PD 终点未做任何多重性校正;tmax 采用成对 Wilcoxon 也未校正。
- 为什么重要:三阶段交叉试验如不控制周期/序列效应、不检验残留效应,处理效应估计可能有偏;多重比较不校正会放大 I 类错误。这是本研究发现"统计学显著"结论的方法学基础。

**5. 主要终点与实际结论错位**

- 位置:2.7 节声明主要终点为曲马多 AUC₀₋∞;但 3.2 节、讨论与结论的核心发现是代谢物 AUC(下降 14%)与 AUCm/AUCp(下降 24%)。
- 为什么重要:样本量计算依据"曲马多 AUC 30% 差异"设定,而对代谢物和比值的推断属于未做样本量论证、未校正多重性的次要分析,却承担了论文的主要结论,存在选择性突出阳性结果的嫌疑。

**6. 讨论中将"胃肠道出血"归为"血清素能不良反应",概念性错误**

- 位置:讨论第 5 段("In chronic administration of tramadol, there is an increased risk of serotonergic adverse effects, such as gastrointestinal bleeding [30, 31]")。
- 依据:文献 30、31 是出血风险研究,消化道出血不属于血清素综合征类反应;且"母体曲马多暴露升高→出血风险"的因果链并未被所引文献证实。
- 为什么重要:该句是讨论中论证临床意义的关键环节,机制归类错误会误导读者对风险性质的理解。

## 二、重要方法学与解释问题(中等严重)

**7. 塞来昔布血药浓度 SD(693)>均值(548) ng/mL,极端变异未被讨论**

- 位置:第 3 节首段(第 54 行)。
- 依据:SD 大于均值提示存在极端个体(如 CYP2C9 慢代谢者),但未报告范围或个体数据,也未做抑制效应与塞来昔布暴露的暴露‑反应分析;"所有受试者 compliance 良好"的推断正建立在如此离散的数据上。
- 为什么重要:DDI 强度取决于抑制剂暴露水平;个别高暴露个体可能驱动了全部"显著"抑制效应,不做敏感性分析就无法排除。

**8. 依托考昔/塞来昔布采样时点与给药关系交代不清**

- 位置:2.2 节("Samples for celecoxib and etoricoxib … were taken before administration of tramadol")。
- 依据:预处理写"8 天",但曲马多在 Day 7 给予;Day 7 早晨 7:00 的 coxib 剂量是否在采血/曲马多给药前服用未说明。若已服用,所测为给药后约 1 小时的近峰值浓度(与测得浓度量级相符),而非谷浓度,直接影响对抑制发生时机和强度的解读。
- 为什么重要:这是解释 DDI 的核心暴露信息,必须明确。

**9. 无 COX‑2 抑制剂单独用药组,药效学"无差异"结论被过度解读**

- 位置:讨论第 1 段(作者已承认该局限);2.7 节样本量论证。
- 依据:研究按 30% 的 PK 差异设定样本量,PD 终点自称探索性且 CI 很宽(作者也承认),但结论部分(第 98 行)却表述为"PK 改变未转化为有临床意义的药效学差异"。
- 为什么重要:在小样本、宽 CI、缺乏单独用药对照的情况下,这是"未发现证据"而非"无差异的证据";结论措辞超出了数据支持范围。

**10. CYP2D6 表型构成与分析策略不匹配**

- 位置:3.1 节(9 正常、1 中等、2 超快代谢者);讨论第 7 段。
- 依据:合并分析纳入了 IM 与 2 名 UM(Finnish 人群中 2/12 为 UM 偏高),但未做剔除非正常代谢者的敏感性分析;结论限定于"正常 CYP2D6 活性个体",分析却基于混合人群。
- 为什么重要:UM 会明显改变代谢物暴露及比值,可能放大或掩盖塞来昔布的抑制效应;至少应提供敏感性分析支持稳健性。

**11. 引文错误/不当**

- 位置:讨论第 2 段及引文列表。
- 依据:① "符合 CYP2D6 的弱抑制 [27]"——文献 27 是依托考昔的 PK 综述(Takemoto 2008),与塞来昔布抑制 CYP2D6 无关;② 2.6 节将 TaqMan OpenArray 基因分型方法引为文献 21(Dicko 等的疟疾/伯氨喹临床试验),作为方法学引文不当;③ 引言称塞来昔布升高"右美沙芬和美托洛尔"暴露仅引文献 13,而该文只有美托洛尔数据。
- 为什么重要:关键机制论断依赖错误引文,属于实质性学术准确性问题。

## 三、次要问题

**12. 图序混乱**:图 2 在 3.1 节(第 60 行)先于图 1(3.2 节)被引用和出现。

**13. "大部分落在生物等效界值内"表述不精确**(3.2 节):恰恰是两个最关键的指标——AUCm/AUCp 0.76(0.69–0.84)与代谢物 Cmax 0.75(0.71–0.78)——完全落在 0.80–1.25 之外,应逐变量说明而非笼统概括。

**14. 结果与讨论措辞不一致**:3.2 节称塞来昔布"未显著改变曲马多暴露",讨论却称"modestly increased tramadol exposure"(GMR 1.13,90% CI 上限 1.21),两处需统一并与第 1 条的 p 值问题一并澄清。

**15. 注册时点需核实**:EudraCT 号含"2010",ClinicalTrials.gov 注册日期为 2011‑07‑11,需确认是否前瞻性注册,否则应如实说明。

**16. 单盲范围不清**:2.2 节仅说明单盲,未说明结局评估者(尤其 VAS、DSST 等主观/操作者依赖的 PD 终点)是否设盲。

**17. 图 3 图注自相矛盾**:"Higher values indicate … greater cold pain tolerance, whereas lower values indicate reduced pain intensity"——对 CPI 指标方向描述混乱。

**18. 讨论冗余**:第 2、3、4 段反复陈述"弱抑制、幅度小、无临床意义",AUCm/AUCp 段与第 2 段内容高度重复,可合并压缩。

**19. 报告细节缺失**:AUEC 与 AUC 单位不完整(如 DSST AUEC 应为效应×时间单位);未报告 AUC₀₋∞ 的外推比例;WinNonlin 4.1 过于陈旧;Shapiro–Wilk 检验后未说明非正态时的处理方案。

## 总体评价

研究设计(随机、交叉、安慰剂对照、依从性监测)总体合理,临床问题有实际意义。但表 1 存在疑似系统性 p 值错误和一处明显的数据矛盾(第 1、2 条),表 2 存在列标题错误(第 3 条),统计分析对交叉设计的处理不完整(第 4 条)。建议 **大修(major revision)**:退回原始统计输出核验全部表格数值,补全交叉设计统计模型说明,修正引文与概念错误,并按数据实际支持力度收敛结论。若作者不能用原始数据排除第 1、2 条的误差,则应考虑拒稿。
```

---

## 挂 Skill（withskill）

**工具调用 38 次**

| # | 工具 | 参数（截断） | 状态 |
| --- | --- | --- | --- |
| 1 | `skill` | {"name": "biomed-paper-review"} | completed |
| 2 | `bash` | {"command": "ls -la && wc -l fulltext.txt && wc -c fulltext.txt"} | completed |
| 3 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/fulltext.txt"} | completed |
| 4 | `todowrite` | {"todos": [{"content": "Stage 0: expert read-through, candidate issue ledger", "status": "completed", "priority": "high"}, {"content": "Read 00-contracts.md + templates", | completed |
| 5 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review/references/00-contracts.md"} | completed |
| 6 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review/references/00-contracts.md"} | completed |
| 7 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 \"$BI | completed |
| 8 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 \"$BI | completed |
| 9 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && grep -n \"che | completed |
| 10 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && grep -n \"che | completed |
| 11 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && grep -n \"^CH | completed |
| 12 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '1,60p | completed |
| 13 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '503,6 | completed |
| 14 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '772,8 | completed |
| 15 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '1,120 | completed |
| 16 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && grep -n \"def | completed |
| 17 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 -c \" | completed |
| 18 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 -c \" | completed |
| 19 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '120,3 | completed |
| 20 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 -c \" | completed |
| 21 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '262,3 | completed |
| 22 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/structured_result_v2.json"} | completed |
| 23 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/_stat_input.json"} | completed |
| 24 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/_seq_input.json"} | completed |
| 25 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '632,6 | completed |
| 26 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/_ext_input.json"} | completed |
| 27 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 \"$BI | completed |
| 28 | `bash` | {"command": "python3 - <<'EOF'\nimport math\ntry:\n    from scipy.stats import t as tdist\n    HAVE_SCIPY=True\nexcept Exception:\n    HAVE_SCIPY=False\n    # fallback: u | completed |
| 29 | `bash` | {"command": "python3 -c \"\nimport json\nfor f in ['_stat_out.json','_ethics_out.json','_seq_out.json']:\n    d=json.load(open(f))\n    sigs=d.get('signals', d) if isinst | completed |
| 30 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && python3 \"$BI | completed |
| 31 | `bash` | {"command": "python3 - <<'EOF'\nimport json\nd=json.load(open('_ext_out.json'))\nreg=d.get('evidence_registry',{})\nfor k,v in reg.items():\n    db=v.get('database'); st= | completed |
| 32 | `bash` | {"command": "python3 - <<'EOF'\nimport json, urllib.request\nreq=urllib.request.Request(\"https://api.crossref.org/works/10.1016/bs.apha.2018.04.007\", headers={\"User-Ag | completed |
| 33 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && for f in 02-m | completed |
| 34 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '736,8 | completed |
| 35 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/.claude/skills/biomed-paper-review\" && sed -n '409,4 | completed |
| 36 | `bash` | {"command": "python3 - <<'EOF'\nimport json\nd=json.load(open('_ext_out.json'))\nreg=d.get('evidence_registry',{})\nfor k in (\"EV-901\",\"EV-903\"):\n    v=reg[k]\n    p | completed |
| 37 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC13254492/withskill/review_report.md"} | completed |
| 38 | `todowrite` | {"todos": [{"content": "Stage 0: expert read-through, candidate issue ledger", "status": "completed", "priority": "high"}, {"content": "Read 00-contracts.md + templates", | completed |

### Skill 覆盖面

- **读了 7/8 个 reference**：`00-contracts`, `02-macro-logic`, `03-experimental-methods`, `04-statistics`, `05-figures-and-charts`, `06-ethics-compliance`, `07-conclusions-discussion`
- **执行了 4/6 个脚本**：`statistical_forensics`, `ethics_compliance_check`, `sequence_identifier_audit`, `external_figure_validation`
- **意见中提及的阶段/模块**：M2, M4, M6, M7

**其中调用 Skill 脚本的次数**：24

### 最终审稿意见

```markdown
完整审核已完成（full_review，M2–M7 全模块 + 外部数据库核验），报告已存至 `review_report.md`。以下为按严重程度排序的全部问题。

> 声明：本流程自动化并辅助论文审核的基础环节（结构化证据抽取、图表解读、报告规范核查、复核优先级排序），**不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断**；评分均为筛查信号，不构成录用/退稿决定。
>
> 评分：风险分 **71/100**（仅筛查分段：major_revision_suggested，阈值未经实证验证）；抽取覆盖率 **0.783**（三张图无图像文件）；审核置信度 **0.783**。

## Major（5 条）

**1. 表 1 有 4 行 p 值与自身 90% CI 数学互斥，含主要终点**（M4-001，P0）
- 是什么：90% CI 完全排除 1 ⟺ p<0.10，但报告 p 均 ≥0.69。由 CI 反算（df=11）：曲马多 AUC·塞来昔布 GMR 1.13 (1.06–1.21) 反算 p≈0.007，报告 **0.765**；曲马多 t1/2 两行报告 0.804/0.836（反算 ≈0.068/0.018）；ODT t1/2·塞来昔布报告 0.69（反算 ≈0.020）。同行其余 p 与 CI 均自洽，异常集中在这 4 个。
- 位置：表 1（line 71）；方法仅描述一种 PK 分析（line 47）。
- 为什么重要：这决定主要终点「塞来昔布是否显著升高曲马多暴露 13%」，必须调原始统计输出裁定哪套数值为真。

**2. 表 1 ODT t1/2 依托考昔行不可能成立**（M2-002，P0）
- 是什么：算术均值 5.6 (1.1)→2.6 (0.7) h（比值 0.46），同行 GMR 却为 1.06 (0.99–1.14)。由「几何均值≤算术均值」可证 GMR≤2.6/5.41=0.48，与 CI 下限 0.99 矛盾——该行至少一个数值是转录错误。
- 位置：表 1 ODT t1/2 行（line 71）。
- 为什么重要：更正前该行数值不可引用；也提示表格数据录入质控有缺口。

**3. 主要终点在 Results 与 Discussion 中表述相反**（M2-001，P0）
- 是什么：Results 称塞来昔布「did not meaningfully alter tramadol exposure」（line 67），Discussion 称「modestly increased tramadol exposure」（line 92）——与问题 1 互为表里，只能有一真。
- 为什么重要：主要终点的方向性结论必须统一，且须与正确的统计结果一致。

**4. 回顾性注册；正文注册日期与注册库不符**（M6-001，X1 经 ClinicalTrials.gov 核实）
- 是什么：NCT01304069 首次提交 2011-02-24，晚于研究开始 2011-01（注册库记录，EV-901）；正文却写「date of registration: 11.7.2011」（line 16），两者也不一致。结局切换核查未见异常。
- 为什么重要：前瞻性注册是 ICMJE/赫尔辛基宣言硬要求；需编辑裁定并更正注册日期表述。

**5. 「基本落在生物等效限度内」与数据不符**（M7-001）
- 是什么：Results/Discussion 均称 GMR「remained largely within bioequivalence limits」，但 ODT Cmax 0.75 (0.71–0.78) 与 AUCm/AUCp 0.76 (0.69–0.84) 的 CI **全部**低于 0.80；同段「profiles were similar」也与 ODT Cmax 降 25% 不符。
- 位置：line 67、92、表 1。
- 为什么重要：这是「无临床相关 DDI」结论的核心支撑，系统性淡化了代谢物端越界结果，需分母药/代谢物分别陈述。

## Minor（7 条）

6. **PK 主分析模型不全**：未交代交叉设计的序列/周期项；「p<0.05 显著」与 90% CI/0.80–1.25 推断两套口径关系未说明；多终点无多重性考虑（line 47–48）。
7. **塞来昔布谷浓度 548 (693) ng/mL：SD>均值**（line 54）——提示可能含 CYP2C9 慢代谢高暴露者，却仅以聚合值声称依从性良好；应给个体值与敏感性分析。
8. **设盲对象未说明**：仅「single-blinded」（line 21），主观 VAS 终点在评估者不盲时易偏倚。
9. **表 2 列头与内容矛盾**：「Geometric mean ratio (90% CI)」列下出现均值差及负界 3.29 (−87.89, 94.47)（line 86）；AUEC 缺 ×h 单位。
10. **参考文献 9 著录错误**：DOI 10.1016/bs.apha.2018.04.007 经 Crossref 解析为 *Advances in Pharmacology* 书章节（页 3–32），却被著录为 CPT 103:210–221（line 147–149）。
11. **PD「无临床相关差异」超出功效**（line 98）：n=12、探索性、CI 很宽，宜改为「未检测到差异」。
12. **把消化道出血归为「血清素能不良反应」且引用不支撑**（line 95，引文 30/31 为出血流行病学研究，未建立血清素能机制）。

## Info（2 条）

13. AE 仅汇总报告（9 例，line 81），未按三期交叉的治疗期分列、评估仅 3 h/6 h。
14. 参考文献 25 访问日期笔误「accessed 3 January 3, 2026」（line 212）。

另：三张图无图像文件（仅图注可读）、输入缺标题/摘要，属系统限制、不计为作者问题，建议索取原图核对 Figure 2 的 CYP2D6 分层个体值。
```

---

## 待分析

1. 挂 Skill 那臂**跑脚本了吗**？没跑就说明问题在执行层，不在规则层。
2. 跑了 X1 吗？`cell_line` / `retrospective_registration` 这两类**只有查外部库才可能命中**，没跑 X1 就必然 MISS。
3. 两臂意见的**重合度**有多高？若挂 Skill 只是把裸模型的意见重新组织了一遍，uplift 结构上就只能是零或负。
4. 挂 Skill 那臂有没有**漏掉裸模型提到的问题**？此前实测出现过挂 Skill 9 条、裸模型 15 条且是真子集的情况。
