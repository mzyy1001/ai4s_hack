# M7 · 结论与讨论合理性

**负责人：MY（敏仪）** · 状态：**骨架 — 待负责人填充判据**

全流程的**收口模块**。核心问题：论文的每一条主张，是否被它自己的数据支持？

**一期边界**：只判断 **claim ↔ evidence 的对齐关系** —— 论文的主张是否被它自己的数据支持。
不查外部证据、不判断创新性、不做常识校验。违背基础常识的结论（如"面粉可治疗癌症"）
标记为 `claim_beyond_evidence` 交人工复核即可。

**这三件事二期都要做**，本模块是它们的归属方，规则见 §5。一期先把 claim 抽取和对齐做扎实 ——
二期的三项能力全都建立在"已经准确抽出每一条 claim 及其支撑证据"之上，这一步做不好，
接外部数据库也只是把错误的 claim 拿去比对。

---

## 1. 输入

`structured_result.conclusion.claims[]`（每条含 `statement` / `scope` / `supported_by[]`）、
`key_data[]`、以及 M2–M6 已产出的 findings（结论的可信度取决于底下几层有没有塌）。

## 2. 校验清单

### 2.1 claim-evidence 对齐

逐条主张检查：

| 检查 | 不通过的表现 |
| --- | --- |
| 有无支撑数据 | `supported_by[]` 为空 |
| 支撑强度是否匹配措辞 | 数据仅显示相关，结论用"导致 / 引起 / 证明" |
| 统计显著性是否被夸大 | p=0.049 被描述为"显著改善"，未提效应量 |
| 阴性结果是否被误读 | 未达显著 = 无差异（缺乏效能时不成立） |

### 2.2 外推范围

结论的适用范围是否超出实验条件？典型越界：

- 细胞实验 → 直接主张临床疗效
- 单一物种/品系 → 主张普适生物学机制
- 单中心小样本 → 主张人群层面推荐
- 特定剂量/时间窗 → 主张任意条件下有效
- 相关性研究 → 主张因果

**待填充**：敏仪梳理"实验层级 → 允许的主张层级"对照表。

### 2.3 讨论质量

- 是否讨论了与既往文献不一致的结果，还是只选择性引用支持性文献？
- 是否讨论了替代解释 / 混杂因素？
- 局限性（limitations）是否存在？是否只写无关痛痒的局限而回避核心缺陷？
  —— 若 M2–M6 报出了 major 问题而 limitations 完全未提及，触发 `limitations_evasive`。
- 结论是否重复结果而无解读（讨论空转）？

### 2.4 与下层模块联动

本模块必须消费 M2–M6 的 findings：

```
若 M4 报出 wrong_test / sample_size(critical)  → 依赖该分析的 claim 自动降级为 unsupported
若 M3 报出 missing_control                     → 相关因果主张自动降级
若 M5 报出 image_manipulation_suspected        → 相关 claim 标记 critical，直送人工
```

## 3. category slug（待补全）

| slug | 说明 | severity |
| --- | --- | --- |
| `unsupported_claim` | 主张无数据支撑 | critical |
| `claim_beyond_evidence` | 外推超出实验条件 | major |
| `causal_overreach` | 相关性表述为因果 | major |
| `negative_result_misread` | 不显著误读为无差异 | major |
| `significance_overstated` | 夸大统计显著性 | major |
| `limitations_evasive` | 回避核心局限 | major |
| `selective_citation` | 选择性引用文献 | major |
| `discussion_hollow` | 讨论仅复述结果 | minor |

## 4. TODO（一期）

- [ ] 填充 §2.2 实验层级-主张层级对照表（本模块最高优先级）
- [ ] 定义 §2.4 联动降级的具体触发规则表
- [ ] 与 M2 划清边界：逻辑链断裂归 M2，结论跃迁归 M7
- [ ] 明确"温和措辞"白名单（may / suggest / is associated with 等降级动词）

---

## 5. 二期扩展（本期不实现，规则先写下）

三项能力都归本模块。**现在只写判据，不写实现**；数据源统一走 MCP 接口，
本节只声明"需要什么数据"，不要自行实现调用方式。

### 5.1 结论科学真伪核验

- 数据源：PubMed / Europe PMC 文献库 MCP
- 判据草案：抽出每条 claim 的核心断言 → 检索同主题既往研究 → 分类为
  `consistent`（与主流一致）/ `contradicted`（有反证）/ `novel_unreplicated`（无同类报道）/ `insufficient_evidence`
- 输出 category：`claim_contradicted_by_literature`(critical) / `claim_unreplicated`(info)
- **风险**：检索召回不全会造成"查无反证 = 结论正确"的假阴性。二期必须要求
  `confidence: low` 起步，且此类 finding 一律强制人工复核，不得直接下判断。

### 5.2 领域创新性 / 重要性

- 数据源：文献库 + 引用网络
- 前置：**先定义可量化的新颖度判据**，否则会退化成主观打分。候选方向：
  claim 与既有文献的语义距离、方法组合是否首次出现、研究对象是否为空白领域
- 输出定位：不给"创新性高/低"的结论，只给"该主张在检索范围内未见同类报道"这类**事实性描述**，
  由人工判断价值 —— 这条边界二期也不要越。

### 5.3 基础常识校验

- 数据源：领域常识规则库（需自建）
- 建库方式：**先积累一期人工复核环节的误判样本**，把真实出现过的常识性错误沉淀成规则，
  而不是先验地枚举常识。这也是一期把此类问题交人工的原因 —— 一期的人工复核记录就是二期的训练材料。
- 输出 category：`violates_domain_common_sense`(critical)

### 5.4 evidence 格式变更

二期引入外部证据后，`finding.evidence` 需同时给出论文内定位与外部来源：

```json
"evidence": {
  "locator": "sec:discussion§4.1",
  "quote": "...",
  "external_source": {"type": "pubmed", "id": "PMID:12345678", "relation": "contradicts"}
}
```

`external_source` 字段已在 `schemas/finding.schema.json` 中预留，一期不填。
