# 外部数据库核验层（X1）—— 逐模块清查

## 为什么这层决定成败

我们测出来的 uplift 是**负的**：带 Skill 9 条意见，裸模型 15 条，而且是真子集。

原因不复杂 —— 此前所有检查都是**重读正文**：查论文自己前后是否矛盾、格式是否规范、
措辞是否超出证据。这些事**裸模型本来就会做**，而且做得比我们的流程更快更全。
把模型会做的事写成规则再让模型执行一遍，uplift 结构上就只能是零或负。

**外部核验是唯一一类模型结构上做不到的事**：

- 它不知道 MDA-MB-435 在 Cellosaurus 里被标为 M14 黑色素瘤衍生系（长尾细胞系更不可能知道）
- 它不知道某试验的注册日期晚于入组开始日期（注册日期只在注册库里，正文不写）
- 它不知道某篇参考文献上个月刚被撤稿（撤稿常发生在训练截止之后）
- 它不能把图里标注的 100 kDa 条带和 UniProt 里 43.7 kDa 的真实分子量对上

沙箱开放公开科学数据源白名单、超时 12 小时 —— 这层一期就能做，而且必须做。

## 按需查询，不预置数据集

**不打包任何数据集。** 只在正文里真的出现某个蛋白、登录号、细胞系、注册号、
化合物时，才发起那一次查询。理由有三：

1. 提交包体积受限，几百 MB 的参考库不现实
2. 数据库天天在更新，打包的那一刻就开始过期（撤稿状态尤其如此）
3. 绝大多数论文只会碰到其中极少数条目，预置的部分是浪费

唯一的例外是 `resources/ethics_rules.json` —— 那是法规条文索引，不是数据集，
且法规变更以年计。

## 四条纪律

1. **查不到 ≠ 论文错。** 接口失败、限流、记录缺失一律产 `system_limitation`，
   **绝不**变成稿件 finding。这与契约里 `parse_failed != not_reported` 是同一条原则，
   也是本项目在这个坑里摔过最多次的地方。
2. **只产 signal，不产 finding。** 严重度由 M3/M4/M5/M6/M7 结合稿件证据判定。
3. **数量级类判据恒为候选。** 同一化合物在不同细胞系、不同终点上 IC50 差一两个
   数量级是常态，不能自动判错。
4. **每条外部证据必须带 provenance**：数据库、端点、查询串、取回日期、记录版本。
   否则复查时无法还原当时查到的是什么。

---

## 逐模块清查

图例：**已实现** = 已写进 `scripts/external_figure_validation.py` 且自检通过（对着线上接口）；
**待建** = 已确认可行但尚未实现。

### M1 结构化提取

M1 不产 finding，它的职责是**把可核验的标识符抽出来，登记成下游的查询入口**。
没有这一步，后面所有外部查询都无从触发。

| 抽取项 | 供哪个模块查 | 状态 |
| --- | --- | --- |
| 试验注册号 NCT / ChiCTR / ISRCTN | M6 注册日期、M4 结局切换 | **已实现**（NCT） |
| 数据可得性登录号 GSE / SRR / PXD | M7 | **已实现** |
| 细胞系名称 | M3 | **已实现** |
| UniProt accession | M5 | **已实现** |
| 人类基因符号 | M2 / M3（HGNC） | **已实现** |
| 物种学名、试剂 RRID、化合物名、PDB 编号 | M3 | **已实现** |
| 参考文献 DOI 列表 | M2 | **已实现** |
| 化合物名 / ChEMBL ID | M5 | **已实现** |
| 抗体 catalog number / RRID | M3 | **已实现** |

ChiCTR 与 ISRCTN 尚未接：ChiCTR 无稳定公开 REST 接口，ISRCTN 有但格式不同。

### M2 宏观逻辑（卓妍）

| 能查什么 | 拿什么核 | 模型能否自己做 | 状态 |
| --- | --- | --- | --- |
| 引用了**已撤稿**的文献 | Europe PMC `pubType` | **不能** —— 撤稿常在训练截止后 | **已实现** |
| 参考文献是否真实存在 | Crossref DOI 解析 | 不能（幻觉引文、纸厂引文） | **已实现** |
| 「首次报道」类主张 | PubMed 检索既往文献 | 部分能，长尾不能 | 待建 |

注：Crossref 的 `update-by` 字段对已撤稿论文**常常是空的** —— 实测 Surgisphere 那篇
Lancet（10.1016/S0140-6736(20)31180-6）在 Crossref 查不到撤稿关系，
Europe PMC 的 `pubType` 则正确标注为 `Retracted Publication`。所以撤稿状态走 Europe PMC。

### M3 实验方法

| 能查什么 | 拿什么核 | 模型能否自己做 | 状态 |
| --- | --- | --- | --- |
| **细胞系被认定污染 / 错误鉴定** | Cellosaurus | **不能** —— 约六百条，著名的几条知道，长尾不知道 | **已实现** |
| 抗体 RRID 是否有效 | SciCrunch | 不能 | **已实现** |
| 物种 / 品系名是否有效 | NCBI Taxonomy | 部分能 | **已实现** |

**这是全套价值最高的一条。** MDA-MB-435 被大量论文当作乳腺癌细胞系，
Cellosaurus 明确标注：`Problematic cell line: Contaminated. Shown to be a M14 derivative`
—— 它是黑色素瘤衍生系。用它做出的「乳腺癌」结论，研究对象本身就不是乳腺癌，
这直接推翻全文，而不只是某个次要瑕疵。

### M4 统计

| 能查什么 | 拿什么核 | 模型能否自己做 | 状态 |
| --- | --- | --- | --- |
| **结局切换**（报告的主要结局 ≠ 注册的） | ClinicalTrials.gov v2 | **不能** —— 必须比对注册记录 | **已实现** |
| 注册样本量 vs 报告样本量 | ClinicalTrials.gov v2 | 不能 | 待建 |

M4 其余部分（p 值重算、GRIM、CI 自洽）是纯计算，本来就该由
`statistical_forensics.py` 确定性地算，不需要外部数据 —— 那部分的 uplift 来自
**算得准**，不来自查得到。

### M5 图表

| 能查什么 | 拿什么核 | 模型能否自己做 | 状态 |
| --- | --- | --- | --- |
| WB 条带标注分子量 vs 真实分子量 | UniProt | 不能（需精确 kDa） | **已实现** |
| 突变位点越界 / 参考残基不符 | UniProt 序列 | 不能 | **已实现** |
| 报告 IC50 vs 已知活性数量级 | ChEMBL | 不能 | **已实现** |
| 基因表达方向 vs 参考队列 | GEO / TCGA | 不能 | 待建 |
| 引用的 PDB 条目是否存在 | RCSB PDB | 不能 | **已实现** |
| 化合物名与分子量 | PubChem | 不能（精确分子量） | **已实现** |
| 结构图所述结构域 | InterPro / AlphaFold | 部分能 | 待建 |

突变核验这条同时**升级了本地工具**：`sequence_identifier_audit.py` 原先只能
拿论文自己给的序列做比对，论文不给序列就查不了；接上 UniProt 后，
只要论文提到蛋白和位点就能查。

### M6 伦理合规

| 能查什么 | 拿什么核 | 模型能否自己做 | 状态 |
| --- | --- | --- | --- |
| **回顾性注册**（注册日期晚于研究开始） | ClinicalTrials.gov v2 | **不能** —— 正文不写注册日期 | **已实现** |
| 注册号是否真实存在 | ClinicalTrials.gov v2 | 不能 | **已实现** |

ICMJE 要求前瞻性注册（首例入组前完成注册）。注册日期与开始日期都在注册库里，
论文正文几乎从不写，因此**纯读正文绝无可能发现**回顾性注册。

### M7 结论与讨论

| 能查什么 | 拿什么核 | 模型能否自己做 | 状态 |
| --- | --- | --- | --- |
| 声称「数据已上传」的登录号不存在 | GEO / SRA / PRIDE | 不能 | **已实现** |
| 结论所据文献已撤稿 | Europe PMC | 不能 | **已实现**（与 M2 共用） |

登录号那条恒为候选：可能处于 embargo 或刚提交未索引，不能直接判为造假。

---

## 已实现的十四条

`skills/biomed-paper-review/scripts/external_figure_validation.py`，
45 项自检全部对着**线上接口**通过（非 mock），覆盖十个数据库：

| check | 数据库 | `comparison_result` |
| --- | --- | --- |
| `cell_line` | Cellosaurus | `mismatch`（污染 / 错误鉴定是确定事实） |
| `variant` | UniProt | `mismatch`（位点越界、残基不符） |
| `trial_registration` | ClinicalTrials.gov | `mismatch`（回顾性注册）/ `needs_manual_review`（查无记录） |
| `cited_retracted` | Europe PMC | `mismatch` |
| `gene_symbol` | HGNC | `mismatch`（Excel 日期化、已改名）/ `needs_manual_review`（无法识别） |
| `reference_exists` | Crossref | `mismatch`（DOI 无法解析） |
| `rrid` | SciCrunch | `mismatch`（RRID 无法解析） |
| `pdb` | RCSB PDB | `mismatch`（条目不存在） |
| `species` | NCBI Taxonomy | `needs_manual_review`（可能是俗名或旧分类名） |
| `compound` | PubChem | `needs_manual_review`（盐型、水合物可解释分子量差异） |
| `outcome_switching` | ClinicalTrials.gov | `needs_manual_review`（措辞差异可致误判） |
| `blot_band` | UniProt | `needs_manual_review`（修饰、二聚体改变迁移） |
| `accession` | GEO / SRA / PRIDE | `needs_manual_review`（可能 embargo） |
| `ic50` | ChEMBL | `needs_manual_review`（体系不同活性差异是常态） |

几条值得单说的：

- **`gene_symbol` 的 Excel 日期化**：Excel 会把 SEPT2、MARCH1、DEC1 这类符号
  自动转成「2-Sep」「1-Mar」，这是基因列表里最常见的静默污染 ——
  HGNC 已于 2020 年为此把整个家族改名（SEPT2→SEPTIN2、MARCH1→MARCHF1）。
  日期格式本身不查库就能判，但仍去 HGNC 取现行符号供人工回溯。
  **HGNC 只管人类命名**：给了非人类物种就不查，否则会把正常的小鼠符号误报。
- **`reference_exists`**：查的是幻觉引文与纸厂引文 —— 格式完美但 DOI 根本不存在。
  模型自己核不了，它没法解析 DOI。
- **`rrid`**：抗体是复现危机的重灾区，RRID 是目前唯一能把「具体哪一支抗体」
  唯一确定下来的标识符。

产物三部分：`signals[]`（`type=external_validation_candidate`，带 `external_check` 比较块）、
`evidence_registry`（external 型证据，带端点、查询、取回时刻、响应 sha256、数据库版本、
可复核的 `source_path`）、`system_limitations[]`。

**每条 signal 必须同时引用稿件证据与外部证据。** 输入缺 `evidence_refs` 时，
工具登记为 `system_limitation` 而**不**产出不合契约的 signal ——
孤立的外部事实无法构成可复算的比较。

`retrieval_status` 三态严格区分：`resolved` / `not_found`（格式合法的精确标识符拿到
权威 404 或明确零记录）/ `not_addressed`（语义查询零命中）。
名称检索查不到某细胞系记 `not_addressed`，**绝不**当作「该细胞系不存在」。

```bash
python3 skills/biomed-paper-review/scripts/external_figure_validation.py --selftest
python3 skills/biomed-paper-review/scripts/external_figure_validation.py --uniprot P04637

printf '%s' '[{"check":"cell_line","cell_line":"MDA-MB-435","evidence_refs":["EV-001"]}]' |
  python3 skills/biomed-paper-review/scripts/external_figure_validation.py --input -
```

契约校验：`tools/validate_schemas.py` 现有 164 项检查，其中新增 10 项专查
X1 的 external evidence（必填字段、越界字段、id pattern、sha256、
resolved/未解析的条件约束、端点无凭证、assertion 完整性、ref 可解析）。
这一层是必要的 —— signal 层查不到 evidence 的问题，而外部证据是 X1
唯一能被复查的凭据，写错就等于不可复查。

## 沙箱白名单

需要申请加入白名单的域名：

```
rest.uniprot.org            # 蛋白分子量、序列
api.cellosaurus.org         # 细胞系污染 / 错误鉴定
clinicaltrials.gov          # 注册日期、登记结局
www.ebi.ac.uk               # ChEMBL、PRIDE、Europe PMC
eutils.ncbi.nlm.nih.gov     # GEO、SRA、Taxonomy
rest.genenames.org          # HGNC 基因符号
api.crossref.org            # 参考文献 DOI 解析
scicrunch.org               # 抗体 / 试剂 RRID
pubchem.ncbi.nlm.nih.gov    # 化合物分子量与分子式
data.rcsb.org               # PDB 结构条目
```

全部是公开科学数据源，无需鉴权，符合白名单准入。任一域名不可达时，
对应检查产 `system_limitation` 而非 finding —— 离线环境下流程照常跑完，
只是少了这部分覆盖，且这一点会明确写进报告。

## 下一步

uplift 要重测，而且**必须以外部核验开着为前提**测 —— 之前那次负 uplift
测的是一个没有任何外部能力的版本，结论只对那个版本成立。

优先级最高的补齐项：注册样本量 vs 报告样本量（M4）、基因表达方向 vs GEO/TCGA（M5）、
「首次报道」类主张的既往文献检索（M2）。

一条实现教训：HGNC 与 SciCrunch 不带 `Accept: application/json` 会返回 XML/HTML，
`json.loads` 失败后静默降级成 `system_limitation` —— 看起来就像「查了，没问题」。
自检里只断言「不报警」是查不出这种失败的，**必须同时断言外部证据真的被登记了**，
否则又是一次「把我们没查到当成论文没问题」。
