# 提案：分层架构下 M2 / M4 / M5 的运行时接口调整

> **本提案不直接改这三个文件** —— 它们分属卓妍（M2）、蒋蕴（M4）、敏怡（M5）。
> 下面写清楚新架构对各模块提出的接口要求，请各自评估后自行修改。
> 框架侧（`SKILL.md`、`00-contracts.md`、`00-runtime-contract.md`、
> `00-routing.md`、schemas）已按新架构改好，M3/M6/M7 由我同步。

## 背景：为什么要改

实测三个数字：

- 一次全流程追踪里，**八个规则库只有一个被真正读过**
- 更早一次 A/B：挂 Skill 9 条意见，裸模型 15 条，**且是真子集**
- 单体架构两次因调用错误整轮作废

诊断（详见 `docs/architecture-diagnosis.md`）：模型被要求在**发现问题之前**
先装下约五千行形式规范，注意力被结构化占满。缺的不是规则，是**路由**——
没有人告诉它「这篇论文的这个疑点该查哪一本」。

新架构把执行分成五层：全局发现 → 路由专家 → 确定性核验 → 全局校正 → 契约归一。
**规则库的内容不需要重写，改的是它被调用的方式。**

## 各模块需要做的三件事

### 1. 在文件开头声明「本模块处理哪些候选类型」

Layer 1 产出的候选带 `type`（形如 `possible_xxx`）。路由表
（`references/00-routing.md` §1）已给出初版映射，**请各模块确认或修正**：

| 模块 | 当前路由给它的候选类型 |
| --- | --- |
| M2 | `possible_internal_inconsistency`、`possible_reporting_omission`、`possible_data_leakage`、`possible_reference_problem` |
| M4 | `possible_statistical_test_mismatch`、`possible_sample_size_issue`、`possible_numeric_inconsistency`、`possible_multiplicity_issue`、`possible_outcome_switching` |
| M5 | `possible_figure_presentation_issue`、`possible_figure_duplication`、`possible_figure_text_contradiction`、`possible_blot_annotation_issue` |

若某类候选应当归你、或不该归你，请直接改 `00-routing.md` 的表并说明理由。
**漏掉一类的代价是那类问题永远进不了你的模块。**

### 2. 声明「本模块需要哪一包证据」

新架构**不再把全文塞给每个专家**。每个模块只拿一包证据 + 轻量全局上下文。
包的定义在 `00-routing.md` §3。请确认你那一包够不够：

- M2 → 跨节包、参考文献包、声明包
- M4 → 统计包（统计方法段落、相关 Results、表格、图注统计量、样本量、检验、p 值、CI）
- M5 → 图包（图像、图注、正文首次引用、相关 Results、相关方法）

**如果你的规则需要包里没有的东西，请写出来** —— 否则运行时会因为拿不到材料
而把问题记成 `unresolved`，看起来像「没查出来」。

每包都会附带全局上下文（研究设计、`experiment_id`、支撑哪条主张、
关联图表、总样本量、随访时长），确保不会做出局部正确、整体荒谬的判断。

### 3. 产 `provisional_finding` 而非最终 finding

专家层的产物**不做去重、不做聚簇、不定最终 severity**，
那些留给 Layer 4 与 Layer 5。你只需要：候选展开 → 规则判定 → 证据绑定 →
必要时请求工具 → 产出临时结论。

**不要在模块里渲染报告。**

## 对各模块的具体请求

### M2（卓妍）

1. **跨节问题不再全归 M2。** Layer 1 会把明显的跨节矛盾标
   `suggested_modules: ["RECONCILE"]` 直接送 Layer 4，因为单个专家只拿一包证据、
   看不见另一节。请确认 `02-macro-logic.md` 里哪些规则属于「模块内可判」、
   哪些必须靠全局校正 —— 后者建议在文件里标出来。
2. **`statistical_forensics` 现在会把 `count_percentage_mismatch` 与
   `table_total_mismatch` 同时路由给 M4 和 M2**（数值本身归 M4，
   「表格与正文数据不一致」归 M2 的完整性范畴）。已在 §3.1 加了接收表，
   请复核 severity。
3. X1 的接收表（§3.1）里 `cited_work_retracted` 的判据要特别注意：
   **引用已撤稿文献本身不一定是错误** —— 论文在讨论撤稿事件本身、
   或已写明该文献已撤稿，都是做对了，不得立 finding。
   这条是建 A/B 语料时踩出来的：差点把一篇《Misconduct in science and medicine》
   当成错误案例。

### M4（蒋蕴）

1. **`possible_numeric_inconsistency` 路由规定 `statistical_forensics` 必跑。**
   同时表格解析出互斥穷尽计数列会**主动扫描**触发同一检查 —— 两条路径都指向它，
   是有意为之：不依赖模型是否想到去算。请确认还有哪些检查值得加入主动扫描清单
   （`00-routing.md` §5）。
2. **signal 无 severity，severity 由你定。** 工具只给「算出来对不上」这个事实，
   是否构成稿件问题、多严重，由 M4 结合影响判定 —— 这正是你在
   §3.5 写的「severity 由影响决定，不是按 slug 固定」，架构已按此设计。
3. §10.1 已加 `outcome_switching` 的接收表，severity 标了待你确认。

### M5（敏怡）

1. **图包只含相关图与其上下文，不含全文。** 请确认判断图表类型是否匹配
   研究目的时，包里的「研究设计 + 支撑哪条主张」是否够用；
   不够的话需要在包里补什么。
2. **`possible_figure_duplication` 规定 `figure_integrity_audit` 必跑**，
   且所有图像候选恒为 `suspected` 强制人工复核 —— 这条现有约束不变。
3. §C.1 已加 X1 五类外部 signal 的接收表，severity 标了待你确认。
   其中四类恒为 `needs_manual_review`（修饰、二聚体、盐型、内部代号都是合法解释），
   只有 `pdb_entry_exists` 的 mismatch 可直接立 finding。

## 不需要改的部分

以下已验证的语义**保持不变**，请勿削弱：

```
证据登记表          finding / extraction_signal / system_limitation 三分
not_reported vs parse_failed        execution-scope 感知的评分
研究设计路由        观测组        确定性工具校验        schema 校验
```

改的是**执行方式**，不是这些语义。

## 怎么验证改对了

```bash
python3 tools/validate_schemas.py      # 契约与实例
python3 tools/consistency_audit.py     # 跨文件闭环（含逐 check_type 核对）
```

以及看遥测：新架构每次运行输出 `runtime_utilization`，
其中 `reference_routing_recall` 应为 1.0 ——
**「本次路由要求读的规则库一个不漏」，而不是「读满八本」。**

## 最关键的一次实验

`tools/ablation_harness.py` 提供五个条件。最重要的一行比较是：

```
D discovery_plus_tools   （全局发现 + 工具 + 校正，不读规则库）
E hierarchical_skill     （完整分层，含规则库）
```

- **D ≈ E** → 五千行规则库贡献有限，应当**裁剪**而不是继续加规则
- **E > D** → 规则库有真实增量价值

这个结果直接决定三位的规则库该扩还是该收。建议改完接口后一起跑一轮。
