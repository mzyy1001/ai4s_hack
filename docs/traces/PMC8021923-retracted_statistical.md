# 审阅过程记录 · PMC8021923

> **论文**：PTIP Inhibits Cell Invasion in Esophageal Squamous Cell Carcinoma &lt;i&gt;via&lt;/i&gt; Modulation of EphA2 Expression.  
> **期刊 / 年份**：None · 2021  
> **错误类型**：`retracted_statistical`  
> **标准答案出题人**：期刊撤稿声明

## 标准答案

本文后被撤稿，期刊给出的理由为：The publisher retracts the article cited above. Following the publication of the article, the authors contacted the Editorial Office to request a correction of the cited article after a comment on PubPeer reported image duplication. An investigation was conducted in accordance with Frontiers’ polici

判定只问一件事：审稿意见有没有**实质性**指出这个问题。只提到名词、或给「建议核对一下」这类通用建议，都不算命中 —— 那种话几乎每份意见都会写，算进去 uplift 就被稀释没了。

---

## 裸模型（baseline）

**工具调用 2 次**

| # | 工具 | 参数（截断） | 状态 |
| --- | --- | --- | --- |
| 1 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/baseline/fulltext.txt"} | completed |
| 2 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/baseline/fulltext.txt"} | completed |

### 最终审稿意见

```markdown
# 同行评审意见：PTIP 通过抑制 EphA2 调控食管鳞癌侵袭（fulltext.txt）

## 一、关键问题（动摇核心结论，须补实验或重写）

**1. Fosl2 调控 EphA2 的方向在正文中自相矛盾**
- 位置：Results 第168–169行称"knockdown of Fosl2… **increased** EphA2 expression"；但 Discussion 第187行称"knockdown of Fosl2 significantly **downregulated** EphA2 expression"；且 Figure 6H–M 的挽救实验逻辑（外源 EphA2 恢复 shFosl2 导致的低侵袭表型，第174–175行）只有在 Fosl2 敲低**降低** EphA2 时才成立。
- 为何重要：这是全文机制链（PTIP⊣Fosl2→EphA2→侵袭）的中枢环节。三处陈述不能同时为真，要么是结果写错，要么数据与模型冲突，审稿人无法据此接受结论。

**2. "PTIP 与 Fosl2 竞争结合同一顺式元件"证据严重不足**
- 位置：第165–181行。ChIP-seq 用的是过表达 MYC-PTIP（第44、129行），而非内源蛋白；支持"竞争"的证据仅为互斥性 ChIP-qPCR（图6N/O）。同时，HOMER 分析发现 PTIP 峰富集 AP-1（Fosl2）motif（第166行）——这更符合 PTIP 经 Fosl2 被招募（tethering/共占位），而非竞争同一 DNA 位点，作者未讨论这一替代解释。此外 PTIP 本身无已知序列特异性 DNA 结合能力，其如何靶向 EphA2 基因内区（第159行）完全没有解释。
- 为何重要：标题级结论（"competing with Fosl2 for binding to EphA2"）仅靠间接证据支撑；缺乏 EMSA、荧光素酶报告、re-ChIP 或体外竞争实验，机制被过度表述。

**3. 功能获得实验为阴性，与临床叙事冲突**
- 位置：第104–106行及 Suppl. Figure 2：PTIP 过表达不抑制侵袭。作者解释为"内源 PTIP 基础水平已足够高"，但临床数据（图1）恰恰显示肿瘤中 PTIP 低表达。
- 为何重要：功能证据只有单向（敲低），因果推断薄弱；作者的解释与自身临床发现不自洽。若基线已饱和，临床样本不应呈现低 PTIP 驱动转移的现象。

**4. 转录抑制机制悬空**
- 位置：引言第3–4行、讨论第187行。PTIP 是 H3K4 甲基转移酶复合体核心组分，本研究首次提出它有抑制功能，但未检测 EphA2 位点 H3K4me1/3 变化，未检验 MLL3/4 依赖性。
- 为何重要：作为该文最重要的新发现（PTIP 亦为抑制因子），没有任何染色质层面的机制验证。

## 二、重要问题（设计与统计）

**5. 临床分析不严谨**
- 位置：入组 87 例（第10行）但仅分析 79 例（第83行），8 例去向未说明；低 PTIP 组仅 n=25；Q-score 截断值"11"（第82行）未说明如何确定（中位数？ROC？）；Table 4（第93行）多个变量双 p 值（如 0.5995/0.4599）未解释；多个临床变量逐一比较未做多重检验校正；无生存分析。
- 为何重要：任意选择的截断值和小样本会虚高显著性（P=0.0399 处于边缘），临床相关性这一论点基础不牢。

**6. 动物模型被误读**
- 位置：第16、109–117行。尾静脉注射是肺定植/实验性转移模型，只能反映存活—外渗—定植，文中却表述为"invasion and metastasis in vivo"（图3标题）。且仅 1 株细胞（KYSE-150）、1 条 shRNA（shPTIP#1），未描述随机化与盲法。
- 为何重要：模型不能覆盖侵袭-转移级联，结论外推过度；单细胞系单 shRNA 的体内结果稳健性存疑。

**7. RNA-seq 分析标准不一致、信息缺失**
- 位置：方法写 adjusted P<0.05（第41行），图1A 图例为 adjusted P<0.01 且 |log2FC|>0.9（第82行），图4A 图例写 "|log2Foldchange| **<** 1"（第128行，疑应为 >1）；患者转录组比较（第74行）未给出样本量，"non-invasive/invasive"活检的定义也不清楚。
- 为何重要：差异基因筛选标准直接影响下游所有 GO/交集分析的可重复性。

**8. 未排除增殖混杂**
- 位置：第100–104行。仅对照了凋亡、黏附、形态，未做增殖/活力检测（如 CCK-8、EdU）。
- 为何重要：transwell 与划痕结果可能被增殖差异混淆，功能表型归因于"侵袭/迁移"缺乏依据。

## 三、中等问题

**9. Discussion 事实性错误**：第186行"decreased EMT facilitate tumor cell invasion"——应为 EMT 增强/激活才促进侵袭，方向写反。

**10. 作者贡献复制粘贴错误**：第197行写"human **CML** samples"，本研究为 ESCC，明显模板残留。

**11. 引用不当**：第2行用文献2支持 ESCC/EAC 分类，但文献2（第242–243行）是 miR-125a-5p/顺铂研究，与所述内容无关。

**12. 磷酸化 Western 无定量**：第152–154行依据 pS897↑/pY588↓ 推断"配体非依赖方式"，但未对总 EphA2 与内参归一化定量；抗体标注分子量 125 kDa 与 EphA2 的 108 kDa 不符（第34行）亦未解释。

**13. "直接靶基因"证据链单薄**：8439 个 ChIP-seq 峰仅注释到 126 个基因，与 RNA-seq 交集仅 38 个（第131–137行）；EphA2 的直接调控仅凭一个基因内峰 + ChIP-qPCR（第159–163行），无报告基因等正交验证。

**14. 图注错误多处**：图4A "|log2Foldchange| < 1"（第128行）；图6图例"* P < 0.05; * P < 0.01"（第178行，**应为双星号）；图5图注内部交叉引用 (C)/(D) 错乱（第158行）。

**15. 其他设计问题**：仅 2 株细胞系且未报告 STR 鉴定（第13行）；TNM 用已废弃的第 5 版 UICC 分期（第10行）；3 个候选基因的选择依据未说明（第137–141行）。

## 四、次要问题

**16. 语言错误较多**："meta-analysis analysis"、"is associate with"（第4行）、"This may be duo to"（第106行）、"Gibico"应为 Gibco（第13行）、"Cell were incubated"（第66行）、"Loss of function analysis shown that"（第168行）等。

**17. 术语混用**：将 N0/N+ 患者样本称为"non-invasive/invasive"（第74、146、185行），把淋巴结转移与体外侵袭混为一谈。

**18. 动物与操作细节**：仅用雌性鼠（第16行，队列 69.6% 为男性）；感染 72 h 后直接注射，未见嘌呤霉素筛选说明（第16行）。

**19. 未支持的表述**：引言称 EphA2 是"a crucial factor involved in tumor cell adhesion"（第5行），但文中黏附实验（第62–63行）从未检测 EphA2 操作后的变化，且 PTIP 敲低本身不影响黏附（Fig S1c）。

**20. 参考文献格式**：文献 13 条目内嵌"14."（第276行）等编号错乱。

---
**总体评价**：临床相关性有意思，但（1）核心机制存在内部矛盾与证据缺口，（2）关键功能实验单向且过表达为阴性，（3）临床统计与动物模型存在可避免的缺陷。建议大修：优先解决第1、2条的矛盾与机制验证，否则不建议以当前结论形式发表。
```

---

## 挂 Skill（withskill）

**工具调用 33 次**

| # | 工具 | 参数（截断） | 状态 |
| --- | --- | --- | --- |
| 1 | `skill` | {"name": "biomed-paper-review"} | completed |
| 2 | `bash` | {"command": "ls -la"} | completed |
| 3 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/fulltext.txt"} | completed |
| 4 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/fulltext.txt"} | completed |
| 5 | `todowrite` | {"todos": [{"content": "Stage 0: 通读全文，建立候选问题台账", "status": "completed", "priority": "high"}, {"content": "Stage 1: 文档切分与证据登记（无图，仅文本+图注）", "status": "in_progress", "priori | completed |
| 6 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; for s in statist | completed |
| 7 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 \"$BIOME | completed |
| 8 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 \"$BIOME | completed |
| 9 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; grep -n 'check = | completed |
| 10 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; grep -n 'def \\\ | completed |
| 11 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; grep -n '\"check | completed |
| 12 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 -c \"\ni | completed |
| 13 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; sed -n '95,200p' | completed |
| 14 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/_stats_input.json"} | completed |
| 15 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 -c \"\ni | completed |
| 16 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 -c \"\ni | completed |
| 17 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; grep -n 'item.ge | completed |
| 18 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; grep -n 'CHECKS  | completed |
| 19 | `read` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review/references/00-contracts.md"} | completed |
| 20 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 \"$BIOME | completed |
| 21 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/_ethics_input.json"} | completed |
| 22 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 - <<'EOF | completed |
| 23 | `write` | {"filePath": "/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/_seq_input.json"} | completed |
| 24 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 \"$BIOME | completed |
| 25 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 - <<'EOF | completed |
| 26 | `bash` | {"command": "python3 - <<'EOF'\nimport json\nitems = json.load(open('_x1_input.json'))\nitems = [i for i in items if not (i.get('doi','').startswith('10.3389/fonc.2021.62 | completed |
| 27 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 - <<'EOF | completed |
| 28 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 \"$BIOME | completed |
| 29 | `bash` | {"command": "curl -s \"https://rest.uniprot.org/uniprotkb/search?query=gene_exact:PAXIP1%20AND%20organism_id:9606&fields=accession,protein_name,length,sequence&format=jso | completed |
| 30 | `bash` | {"command": "curl -s \"https://rest.uniprot.org/uniprotkb/search?query=gene_exact:PAXIP1%20AND%20organism_id:9606%20AND%20reviewed:true&fields=accession,protein_name,leng | completed |
| 31 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; printf '%s' '[{\ | completed |
| 32 | `bash` | {"command": "export BIOMED_REVIEW_SKILL_DIR=\"/Users/henrychen/.claude/jobs/6412e762/tmp/trace/PMC8021923/withskill/.claude/skills/biomed-paper-review\"; python3 \"$BIOME | completed |
| 33 | `todowrite` | {"todos": [{"content": "Stage 0: 通读全文，建立候选问题台账", "priority": "high", "status": "completed"}, {"content": "Stage 1: 文档切分与证据登记（无图，仅文本+图注）", "priority": "high", "status": "c | completed |

### Skill 覆盖面

- **读了 1/8 个 reference**：`00-contracts`
- **执行了 5/6 个脚本**：`normalize_biomed_units`, `statistical_forensics`, `ethics_compliance_check`, `sequence_identifier_audit`, `external_figure_validation`
- **意见中提及的阶段/模块**：Stage 1, Stage 4, Stage 5, M2, M3, M4, M5, M6, M7

**其中调用 Skill 脚本的次数**：22

### 最终审稿意见

```markdown
# 审稿报告 · `fulltext.txt`（PTIP–Fosl2–EphA2 与 ESCC 侵袭转移，Frontiers in Oncology 2021, DOI 10.3389/fonc.2021.629916）

> 本 Skill 自动化并辅助论文审核的基础环节，包括结构化证据抽取、图表解读、报告规范核查与人工复核优先级排序。**它不替代具备资质的审稿人在科学、统计、临床与伦理方面的判断。** 本 Skill 的任何评分均为筛查信号（screening / triage signal），不构成录用、退稿或发表决定。

**执行范围**：`full_review`（Stage 1→2→3b→X1→Stage 4 M2–M7→Stage 5）。输入仅有纯文本 `fulltext.txt`：无标题/摘要/作者列表、无图像、补充材料不可得（见文末"系统限制"）。未发现 critical 级问题。

**三项评分**（分母见末段）：
- `manuscript_risk_score` = **85/100**（`partial:false`，分段 `major_revision_suggested` —— 仅为未经实证验证的筛查信号，非录用/退稿依据；无 critical 簇，`priority_manual_review=false`）
- `extraction_coverage` = **0.70**（字段 20/20=1.0；图表可读 4/10=0.4——6 幅图无图像；补充材料 0/6=0）
- `review_confidence` = **0.69**（medium；无像素估读/OCR，全部证据来自正文与图注文本）

---

## 一、Major 问题（按对结论的影响排序）

**M-1｜临床队列人数前后矛盾：87 例 vs 79 例，无排除流程**（M2，P1）
- 问题：Methods 声明"Eighty-seven patients with ESCC underwent surgery"，但 Results 与 Table 4 只分析 79 例；8 例（约 9%）去向未交代，也无入组时间段、连续入组说明或排除标准。
- 位置：Methods "Patient Information and Tissue Samples"（第10行）vs Results "PTIP Expression Negatively Correlates…"（第83行）及 Table 4（第93行，N=79）。
- 为什么重要：这是全文临床相关性结论（低 PTIP ↔ 淋巴结转移）的根基。若被排除的 8 例与结局相关（如 IHC 失败往往与肿瘤分化/坏死相关），选择偏倚可直接改变 P=0.0399 这一边缘显著的结果。

**M-2｜核心机制链条的可重复性信息缺失：RNA-seq/ChIP-seq 均无样本量与生物学重复描述，DEG 判定标准三处不一致**（M4，P1）
- 问题：(a) 组织 RNA-seq 比较"non-invasive vs invasive tumor biopsies"，但**患者样本量 n 从未报告**；(b) TE1 细胞 RNA-seq（shCtrl vs shPTIP）未说明生物学重复数；(c) ChIP-seq 未报告重复、未说明 IgG/input 对照与质控，仅在过表达 MYC-PTIP 体系用 MYC 抗体做；(d) DEG 标准三处打架：Methods"adjusted P<0.05"，Figure 1A 图注"adjust P<0.01 and |log2FC|>0.9"，Figure 4A 图注"adjust P<0.01 and |log2Foldchange|<1"（"<1"方向明显写反，应为">1"）；(e) 分析流程只写 ballgown，未报告比对/定量工具与归一化。
- 位置：Methods "RNA-Seq Analysis"（第41行）、"ChIP-Seq Analysis"（第44行）、Results 两处 RNA-seq 段（第74、120行）、Fig 1A 图注（第82行）、Fig 4A 图注（第128行）。
- 为什么重要：776 与 6005 个 DEG、8439 个结合位点等全部下游论证（GO 富集、38 基因交集、EphA2 筛选）都建立在这些未描述清楚的数据上；n 与重复不明，差异表达与富集结果无法评估功效，也无法复现。另注：ChIP 靶基因 126 个对应 8439 个峰（平均约 67 峰/基因）比例异常，与"57% 位于启动子/TSS"的叙述不自洽，需作者澄清（同一簇）。

**M-3｜IHC 二分类截断值"Q-score 11"无任何推导依据，Q-score 判读流程不完整**（M4，P1）
- 问题：Figure 1F/5C 图注称"Cut off for high and low PTIP/EphA2 expression was defined < or > 11"，但 Methods 只描述 Q-score 计算公式（百分比×强度），未说明 11 如何选定（中位数？ROC？预设还是事后？），也未给出评分范围；"两位病理学家独立评分"却未报告一致性统计或分歧裁决规则；"Ten sections were collected randomly"的归属（每例？）表述不清。
- 位置：Methods "Immunohistochemistry"（第38行）；Fig 1 图注（第82行）；Fig 5 图注（第158行）。
- 为什么重要：全文唯一显著的临床相关性（淋巴结转移 P=0.0399）就建立在这个二分类上。截断值若为事后挑选，可在边缘 P 值场景下人为制造显著性；这是肿瘤生物标志物研究最典型的偏倚来源之一。

**M-4｜体内实验是尾静脉肺定植模型，却被结论表述为"抑制淋巴结转移"，且队列全部为 M0**（M7，P1）
- 问题：动物实验为 KYSE-150 尾静脉注射→肺部荧光/HE 检测（即实验性血行肺转移/定植模型），但 Discussion 写"these results indicate that PTIP inhibits lymph node metastasis in ESCC in vivo"；临床队列 79 例全部 M0，也没有任何淋巴结转移的体内验证（如原位/足垫模型）。
- 位置：Methods "Mouse Experiments"（第16行）、Results Fig 3（第109–117行）、Discussion（第185行）、Table 4 "Distant metastasis M0 79(100)"（第93行）。
- 为什么重要：肺定植 ≠ 淋巴结转移（涉及外渗、免疫逃逸、淋巴归巢等完全不同的步骤）。这是全文摘要级结论之一，结论的解剖学定位被数据不支持地扩展，属于典型的过度外推。

**M-5｜功能获得性实验为阴性结果，却未作为局限性讨论，且以事后解释带过**（M7，P1）
- 问题：PTIP 过表达在 TE1 与 KYSE-150 均"did not significantly inhibit cell invasion"（Fig S2a–f），正文用"This may be duo to endogenously-expressed basal level of PTIP is high enough"（"duo"亦为错字）一笔带过。全文"PTIP 抑制侵袭"的因果主张因此只有 loss-of-function 单侧证据。
- 位置：Results（第104–106行）、Supplementary Figure 2 题注（第216行）。
- 为什么重要：敲低表型可由脱靶效应解释；过表达阴性意味着剂量-效应关系未被证实。作者有义务在 Discussion 中把这一矛盾作为局限性正面讨论，而不是用无验证的事后假说化解。

**M-6｜"细胞黏附"机制框架与自身数据矛盾**（M7，P1）
- 问题：引言将 EphA2 定位为"a crucial factor involved in tumor cell adhesion"（第5行），Discussion 开篇以黏附机制立论（第185行）；但作者自己的黏附实验显示 PTIP 敲低后黏附"no significant differences"（Fig S1c），且 EphA2 敲低挽救侵袭时并未回测黏附。机制叙事的关键一环被作者自己的阴性数据否定。
- 位置：Introduction（第5行）、Results（第102–103行）、Discussion（第185行）、Supp Fig 1 题注（第211行）。
- 为什么重要：若侵袭表型并非经由黏附改变介导，则 PTIP→EphA2 的机制解释需要其他通路证据；目前数据只支持"侵袭/迁移"而不支持"黏附"机制。

**M-7｜TNM 分期采用 1997 年 UICC 第 5 版**（M3，P1）
- 问题：2021 年发表的研究按"the 5th edition of the TNM classification of the UICC"分期；食管癌 TNM 第 7 版（2009）/第 8 版（2017）对 T/N/M 定义与分期分组均已大幅修订（第 8 版对 ESCC 与 EAC 分开分组）。Table 4 的"I–II vs III–IV"分组因此基于过时标准。
- 位置：Methods "Patient Information and Tissue Samples"（第10行）、Table 4 TNM Stage 行（第93行）。
- 为什么重要：分期是临床试验最重要的预后协变量之一；用错版分期会系统性误分患者（尤其 N 分期定义变化），使"PTIP 与 TNM 无关联（P=0.43）"这类阴性结论及队列描述均不可靠。

**M-8｜动物实验合规与福利报告成组缺失**（M6，P1）
- 问题：动物伦理声明**无批准编号**（人体部分有 YX-2020-162-01，动物部分没有）；未报告 3R 考量、安乐死方法（仅"mice were euthanized"）、麻醉/镇痛方案、人道终点、随机分组与观察盲法、每鼠注射细胞数（方法只说感染 1×10⁶ 细胞）、中国实验动物许可证号（SYXK）。伦理规则库筛查命中 ETH-ANI-002（3R 缺失）。
- 位置：Methods "Mouse Experiments"（第16行）、Ethics Statement（第194行）。
- 为什么重要：ARRIVE 规范与多数期刊（含 Frontiers 动物福利政策）要求这些要素；n=8/组的小样本实验若无随机化与盲法，荧光信号定量（主观设阈值）易引入观察者偏倚。

---

## 二、Minor 问题

**m-1｜编辑完整性红旗：作者贡献残留他稿痕迹 + Discussion 自相矛盾**（M2）
- "LP, KH, YY, CJ, and JX … performed experiments using human **CML** samples"（第197行）——本文研究对象是 ESCC，CML（慢性髓系白血病）显系从他稿整段粘贴，要求作者逐句核对全文是否还有其他移植内容；Discussion 结尾"how PTIP is **upregulated** in ESCC cells need to be determined"（第188行）与全文"PTIP 在转移灶中下调"的前提直接矛盾；Discussion"decreased EMT facilitate tumor cell invasion"（第186行）应为 increased EMT。均须修正并说明成因。

**m-2｜Table 4 统计报告含糊**（M4）：每个变量给出两个未加说明的 P 值（如"0.5995/0.4599"），未声明哪个对应 χ²、哪个对应 Fisher；6 个变量平行检验未做多重比较校正，唯一显著项 P=0.0399 为名义显著。（第93行）

**m-3｜误差条与图注成组瑕疵**（M5）：Methods 声明"mean ± SEM"（第69行），所有图注却写"Mean ± s.d."（第108、128、178行等），两处必有一错；Fig 5J/K 图注内部交叉引用错乱（"within (EphA2) or outside (EphA2-NC) of the EphA2 gene **(C)** … analyses of EphA2 binding **(D)**"，而 (C)(D) 是 IHC 面板，第158行）；Fig 6 图注"*P<0.01"应为"**"（第178行）；Supp Fig 1(c) 题注一边写"did not significantly alter"一边挂"*P<0.05"（第211行），与正文"no significant differences"（第102行）冲突，需澄清是否真无差异。

**m-4｜试剂与材料报告细节**（M3）：细胞系只报告"mycoplasma tested negative"，未报告 STR 鉴定与传代数（Cellosaurus 检索 TE1/KYSE-150/HEK293T 均无 problematic 标记，但稿件仍应自证）；HEK293T 列于 Cell Culture 却未见任何实验使用（第13行）；FLAG 抗体以"1µg/µL"浓度而非稀释度报告（第34行）；"Chinese Type Culture Collection (Shanghai)"名称含糊，建议给出保藏编号。

**m-5｜命名与表述**（M2）：Table 2 的"BML"应为 BLM（Bloom 综合征基因，正文写作 BLM/TP53，第30行 vs 第78行）；人类细胞实验中基因符号一律用小鼠式小写"Fosl2"、引物表标"P53"（人类规范为 FOSL2/TP53）；"EC-matrix adhesion"应为 cell-matrix（第102行）；全文用"non-invasive/invasive tumor biopsies"指代"无/有淋巴结转移"，癌组织称"non-invasive"极易误读（第74、185行）；Table 2 中 TACSTD2、GPRC5A 引物未见于任何所述实验。

**m-6｜人体研究伦理声明未提及《赫尔辛基宣言》**（M6）：伦理规则库筛查命中 ETH-HUM-004；建议补充。（第194行）

**m-7｜统计学细节**（M4）：动物实验每周成像却只对第 4 周做 t 检验，时间点选择未说明（第111–112行）；ChIP 靶基因(126)与 DEG(6005)交集 38 个恰等于随机期望（126×6005/≈20000≈38），未见交集富集的统计检验即用于挑选直接靶基因（第137行）。

---

## 三、Info / 已核验为"无问题"的项

- **Table 4 算术自洽**：统计取证脚本核验全部行列计数（25+54=79、各列和、11 组计数-百分比换算）全部一致，无表格算术错误。
- **外部核验（X1）通过**：31 个参考文献 DOI 全部可解析（Crossref）；Europe PMC 筛查**无撤稿引用**；SRA 登录号 SRR13089664–79 首尾两条均存在；Cellosaurus 对 TE1(CVCL_C6K3)、KYSE-150(CVCL_1348)、HEK293T(CVCL_0063) 均无"problematic"标记；PTIP 报告条带 130 kDa 与 UniProt Q6ZW49 理论值 121.3 kDa 在常规 SDS-PAGE 容差内。
- GLOBOCAN 2018 引数（572,000 新发 / 509,000 死亡、发病率第 7、死亡率第 6）与原文引用一致。
- 引物常规 QC 仅 3 条 GC 含量略超 40–60% 区间的候选提示（PTIP-RT-F 61.9%、BML-RT-R 39.1%、EphA2-NC-F 63.2%），属可接受范围，不构成稿件问题。

---

## 四、系统限制（非作者问题）

1. 输入无图像：6 幅主图未做视觉解析与图像完整性审计，所有图相关判断仅基于图注文本。
2. 补充材料（Table S1/S2、Fig S1–S4）不可得：Supp Fig 1c 的 P 值矛盾等无法终审。
3. 提供的文本缺标题、摘要、作者列表与页码：无法核查摘要-正文一致性；定位以行号标注。
4. Ethics 脚本对麻醉/镇痛、 euthanasia 方法、SYXK 许可证、人类遗传资源四条因事实无法自动推出而标 `partial_extraction`，上文 M-8 的判断基于对 Methods 的直接检索。

## 五、人工复核建议（P1 优先）

1. 要求作者提供 87→79 例的排除流程图与入组时间段（M-1）；
2. 要求补齐两组 RNA-seq 的样本量/重复、ChIP-seq 重复与 IgG 对照、统一 DEG 标准并修正 Fig 4A 阈值（M-2）;
3. 要求说明 Q-score=11 截断值的预设依据与病理学家一致性（M-3）；
4. 请有动物实验资质的审稿人核对尾静脉模型的随机化/盲法原始记录，并确认是否需按 ARRIVE 补报（M-8）；
5. 请领域审稿人判断肺定植模型能否支撑"淋巴结转移"结论，或要求补做正位/淋巴转移模型（M-4）。
```

---

## 待分析

1. 挂 Skill 那臂**跑脚本了吗**？没跑就说明问题在执行层，不在规则层。
2. 跑了 X1 吗？`cell_line` / `retrospective_registration` 这两类**只有查外部库才可能命中**，没跑 X1 就必然 MISS。
3. 两臂意见的**重合度**有多高？若挂 Skill 只是把裸模型的意见重新组织了一遍，uplift 结构上就只能是零或负。
4. 挂 Skill 那臂有没有**漏掉裸模型提到的问题**？此前实测出现过挂 Skill 9 条、裸模型 15 条且是真子集的情况。
