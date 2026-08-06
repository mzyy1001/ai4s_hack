# M2 · 宏观逻辑与格式完整性

**负责人：ZY（卓妍）** · 状态：**骨架 — 待负责人填充规则库**

对应会议纪要"第一层：无依赖内部逻辑校验"。**不调用任何外部数据**，仅凭论文自身内容判断。
核心问题：抛开生物学专业性，这篇论文作为一篇论文，逻辑链是否闭环、各部分是否完整？

---

## 1. 输入

- `structured_result`（M1 产出），重点看 `objective` / `conclusion.claims[]` / `evaluation_matrix` / `gaps[]`
- 全文分节结果与图表清单（阶段 ①）

## 2. 校验清单

### 2.1 章节完整性

逐项核对是否存在且非空：Abstract / Introduction / Methods / Results / Discussion / Conclusion /
Ethics statement / Funding / Conflict of interest / Data availability / References。

> 缺失哪一节触发哪种 severity，按期刊类型有别 —— **待填充**：不同刊型（研究论文 / 短报告 / 病例报告）的必备章节表。

### 2.2 逻辑链闭环

沿 `研究问题 → 假设 → 实验设计 → 结果 → 结论` 逐段追踪，检查四类断裂：

| 断裂类型 | 表现 |
| --- | --- |
| 目标漂移 | Introduction 提出的问题在 Results 中没有对应实验 |
| 结果孤儿 | Results 中的实验在 Introduction 中无动机、在 Discussion 中无解读 |
| 结论跃迁 | Conclusion 的主张范围超出实验设计能支持的范围（与 M7 联动） |
| 循环论证 | 用待证结论作为方法设计的前提 |

### 2.3 数据泄露场景库

会议纪要中卓妍原方案的核心资产，迁移到本模块作为规则库：

- [ ] 重复样本跨训练/测试集
- [ ] 数据拆分**前**做归一化 / 标准化 / 特征选择
- [ ] 用测试集调超参或选模型
- [ ] 时间序列数据随机切分（未来信息泄露）
- [ ] 同一受试者的多个样本被拆到不同集合
- [ ] 待补充……

> 本节仅适用于含机器学习 / 预测模型的论文（`evaluation_matrix.has_ml_model`）。**待填充**：需要 M1 补一个 `has_ml_model` 键。

### 2.4 前后一致性

- 摘要数值 vs 正文数值（M1 已给出 `abstract_text_mismatch` 线索，此处判定 severity）
- 正文引用的图表是否都存在，图表是否都被正文引用
- 术语与缩写前后是否统一、首次出现是否定义
- 组名/剂量/时间点在不同章节的写法是否一致

## 3. category slug（待补全）

| slug | 说明 | severity |
| --- | --- | --- |
| `missing_section` | 必备章节缺失 | major |
| `logic_gap` | 逻辑链断裂 | major |
| `data_leakage` | 疑似数据泄露 | critical |
| `internal_inconsistency` | 前后表述/数值矛盾 | major |
| `orphan_figure` | 图表未被正文引用，或引用了不存在的图表 | minor |
| `terminology_inconsistency` | 术语不统一 | minor |

## 4. TODO

- [ ] 填充 §2.1 刊型-必备章节对照表
- [ ] 填充 §2.3 数据泄露场景库（这是本模块相对通用大模型的**主要差异化价值**）
- [ ] 为每条规则写 1 个正例 + 1 个反例，便于回归测试
- [ ] 与 M7 划清边界：结论跃迁归 M7，逻辑链断裂归 M2
