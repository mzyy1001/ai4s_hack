# 架构诊断与分层重构

## A. 诊断：单体架构把注意力花在了错误的地方

### A.1 症状

| 观测 | 数值 | 来源 |
| --- | --- | --- |
| 一次全流程追踪里读了几个规则库 | **1 / 8**（只读了 `00-contracts`） | `docs/traces/PMC8021923-*.md` |
| 同一次执行了几个脚本 | 5 / 6 | 同上 |
| 挂 Skill 意见长度 vs 裸模型 | 7,350 vs 3,477 字符 | 同上 |
| 更早一次的 uplift | **负**：挂 Skill 9 条，裸模型 15 条，且是真子集 | 早期自由文本 A/B |
| 单体架构的调用稳定性 | 两次因 `Error:` 整轮作废 | `docs/results/monolithic-baseline-run.log` |

### A.2 注意力浪费在哪

单体架构要求模型在**发现问题之前**先装下：

```
SKILL.md 665 行 + 00-contracts.md 1209 行 + 七本规则库约 3000 行 ≈ 5000 行
```

这些内容绝大部分是**形式规范**：证据登记表怎么写、三类记录如何区分、
severity 枚举、覆盖率公式、阶段依赖图。它们对「这篇论文哪里有问题」
没有任何直接贡献 —— 它们的作用是**事后组织与校验**。

后果是模型进入一种「先满足格式」的模式：追踪里它一上来就读契约、
反复 grep 脚本源码确认输入格式，真正用于阅读论文的注意力被挤走。
**结构化取代了发现。**

这解释了为什么会出现负 uplift：裸模型把全部注意力用于读论文，
挂 Skill 的那一臂把相当一部分用于满足契约，而契约本身不发现任何问题。

### A.3 为什么规则库没被用起来

不是模型偷懒，是**没有人告诉它该读哪一本**。

八本规则库平铺在那里，没有「这篇论文的这个疑点应当查哪本」的映射。
在没有路由的情况下，理性的做法恰恰是先读那本看起来最像总纲的
（`00-contracts`），然后就没有余力了。

**缺的不是规则，是路由。**

### A.4 为什么「1/8」本身不算错

一篇纯生物信息学论文不涉及动物、不涉及知情同意，
**读伦理规则库对它毫无用处**。强行要求读满八本只会重演同一个错误：
把注意力花在与本篇无关的形式上。

所以 `references_read = 8/8` 是个**错误的优化目标**。

正确的目标是**路由召回率**：

```
reference_routing_recall = |实际读了 ∩ 本次路由要求读的| / |本次路由要求读的|
```

目标 1.0。要求之外的不读不是缺陷，是设计。
而 1/8 之所以是问题，是因为那一次**统计与图表规则库本该被读却没读**——
问题在分母，不在分子。

### A.5 为什么只做分块切分不够

把论文按 token 窗口切开分别审，会**系统性丢掉最有价值的一类问题**：跨节矛盾。

实测中裸模型发现的高价值问题恰恰是这一类：

- Methods 写纳入 ASA I–III，基线表里只有 II/III
- 表里报一个 p 值，Discussion 里报另一个
- 随访只有 48 小时，结论却称「未见严重并发症」

这些问题**任何单块里都不存在**，只存在于块与块的关系里。
所以架构必须同时保留两个视角：**全局表示** + **局部专家深度**，
并在最后做一次显式的全局校正。

---

## B. 重构后的执行图

```
                      ┌─────────────────────────┐
   归一化稿件  ─────►  │ Layer 1  全局发现        │  只带 SKILL.md + 运行时最小契约
                      │  专家通读，高召回        │  禁读 M2–M7 规则库与完整契约
                      └───────────┬─────────────┘
                                  │
              paper_map / experiment_map / claim_map
              candidate_issues[] / review_routing_plan
                                  │
                    ┌─────────────┴──────────────┐
                    │      语义证据包构建         │  构建一次，全程复用
                    │  方法/统计/图/伦理/主张/引用 │  不重复读全文
                    └─────────────┬──────────────┘
                                  │
        ┌────────┬────────┬───────┼───────┬────────┐
        ▼        ▼        ▼       ▼       ▼        ▼
    ┌───────┐┌───────┐┌───────┐┌──────┐┌──────┐         每个专家独立执行
    │  M2   ││  M3   ││  M4   ││  M5  ││  M6  │         只拿自己那包证据
    │跨节包 ││方法包 ││统计包 ││图包  ││伦理包│         只读自己那本规则
    └───┬───┘└───┬───┘└───┬───┘└──┬───┘└──┬───┘
        └────────┴────────┴───────┴───────┘
                          │  M2–M6 并行完成后
                          ▼
                      ┌───────┐
                      │  M7   │  消费 M2–M6 findings 判断结论可信度
                      │主张包 │
                      └───┬───┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │ Layer 3  确定性核验            │  候选验证 + **主动扫描**
          │ tool_task 显式登记，不得静默消失│  executed/not_applicable/failed/skipped
          └───────────────┬───────────────┘
                          ▼
          ┌───────────────────────────────┐
          │ Layer 4  全局校正              │  Abstract↔Results、Methods↔基线表
          │ 跨节矛盾在这里才可能被发现      │  随访↔安全性主张、注册↔稿件
          └───────────────┬───────────────┘
                          ▼
          ┌───────────────────────────────┐
          │ Layer 5  契约归一与渲染        │  **到这里才套完整 schema**
          │ 去重/聚簇/severity/覆盖率/报告  │
          └───────────────────────────────┘

  贯穿全程：candidate_resolution_log[]  每个候选必须结清
            runtime_utilization         哪些部分真的被用上了
```

对象随层级收敛，**四类不得混为一谈**：

```
discovery 对象      provisional 对象     已核验记录        最终契约记录
（轻量、高召回、     （已绑证据、          （工具确认）      （完整 schema、
  无需 evidence）     未去重定级）                           可追溯）
```

---

## H. 四个端到端模拟

### 案例 1 · 跨节矛盾：Methods 写 ASA I–III，基线表只有 II/III

```
Layer 1  通读时同时看到 Methods 的纳入标准与 Table 1 的构成，产出：
         CAND-003 {type: possible_internal_inconsistency,
                   description: "Methods 纳入 ASA I–III，Table 1 只列 ASA II/III",
                   locations: ["Methods §2.1", "Table 1"],
                   suggested_modules: ["RECONCILE"]}
         ← 标 RECONCILE 而非 M2：单个专家只拿自己那一包，看不见另一节

Layer 2  跳过（跨节候选不进专家通道）

Layer 3  statistical_forensics 主动扫描 Table 1 的构成计数 →
         若合计等于 n，则数值本身无误 → 说明矛盾在**纳入标准与实际人群**之间，
         不是算错。这一步把问题定性收窄了。

Layer 4  全局校正取 paper_map + Table 1 + Methods §2.1 比对：
         纳入标准声明的范围 ⊅ 实际入组人群
         → cross_section_findings[]：
           {category: eligibility_baseline_mismatch, severity: major,
            evidence_refs: [EV-011 (Methods present), EV-012 (Table 1 present)]}

Layer 5  归一为 M2-004，origin = "discovery"
         candidate_resolution_log: CAND-003 → promoted_to_finding, final M2-004
```

**关键点**：这条问题在任何单块内都不存在。若只做分块专家审阅必然漏掉。

### 案例 2 · 表格算术：12 + 18 = 30，声明 n = 28

```
Layer 1  CAND-014 {type: possible_numeric_inconsistency,
                   description: "Table 1 各类计数之和似与声明分母不符",
                   confidence: "medium", suggested_modules: ["M2","M4"]}
         ← 发现阶段**不要求**它先算准，只要求它注意到

Layer 3  路由表规定 possible_numeric_inconsistency → statistical_forensics **必跑**；
         同时表格解析出互斥穷尽计数列 → **主动扫描**也会触发同一检查
         （两条路径都指向它，正是设计意图：不依赖 LLM 是否想到）

         tool_task: {TOOL-07, statistical_forensics, "Table 1",
                     requested_checks: ["table_total_mismatch"],
                     triggered_by: ["CAND-014"], proactive: false,
                     status: "executed"}

         产出 signal（**无 severity**）：
           {SIG-042, type: table_total_mismatch,
            detail: "12+18=30，声明分母 28", routed_to: ["M4","M2"]}

Layer 2  M4 拿统计包 + SIG-042 + 04-statistics.md（**只读这一本**）
         判定：构成数据报告错误 → provisional_finding，severity 由影响决定
         （主要终点分母出错 → critical；仅基线表 → major）

Layer 5  M4-002，origin = "deterministic_tool"
         CAND-014 → promoted_to_finding
```

**关键点**：severity 由 M4 定，工具只给「算出来对不上」这个事实。
这正是 signal 无 severity 的原因。

### 案例 3 · 引用了已撤稿文献

```
Layer 1  paper_map 记录 reference_count 与 registration_ids；
         通读**通常发现不了**这一条 —— 撤稿状态不在正文里，
         裸模型也不可能知道。这正是外部核验的价值所在。

Layer 3  **主动扫描**：参考文献包解析出全部 DOI →
         X1 逐条查 Europe PMC 的 pubType（不依赖任何候选）

         tool_task: {TOOL-11, external_figure_validation, "References",
                     requested_checks: ["cited_retracted"],
                     triggered_by: [], proactive: true, status: "executed"}

         产出 external evidence（端点/查询/取回时刻/响应 hash/database_version）
         + signal {type: external_validation_candidate,
                   check_type: "cited_work_retracted",
                   comparison_result: "mismatch", routed_to: ["M2","M7"]}

Layer 2  M2 拿参考文献包 + 该 signal + 02-macro-logic.md：
         **判据要点：引用已撤稿文献本身不一定是错误。**
         论文若在讨论该撤稿事件本身、或已写明该文献已撤稿 → 不立 finding。
         只有当它构成立论依据且未提及撤稿状态时才立。
         → 本例正文未提 retract → provisional_finding, severity major

         M7 另行判断：该文献是否支撑主要结论 → 若是，升 critical

Layer 5  M2-007，origin = "external_validation"
         evidence_refs 同时含稿件证据（引用位置）与 external evidence
```

**关键点**：这一类**只有查外部库才可能发现**，是相对裸模型的结构性优势。
同时它也说明为什么不能自动定罪 —— 判据必须由专家结合语境给。

### 案例 4 · 随访 48 小时却称「未见严重并发症」

```
Layer 1  claim_map 建立：
         CL-05 {statement: "本术式未见严重并发症",
                claim_scope: "安全性，全部并发症类型",
                source_location: "Conclusion",
                expected_evidence: ["足以观察到迟发并发症的随访时长"]}
         experiment_map 记录 followup_duration = "48 hours"
         CAND-021 {type: possible_followup_overreach,
                   suggested_modules: ["M7","RECONCILE"]}

Layer 2  M7 拿**主张-证据包**（主张原文 + 相关 Results + 随访时长 +
         研究人群 + 局限性段落）+ 07-conclusions-discussion.md：
         按证据层级 × 主张层级对照表判定 —— 48 小时随访支持的
         最高主张层级远低于「未见严重并发症」这种无时间限定的安全性断言
         → provisional_finding: claim_beyond_evidence

Layer 4  全局校正核对「随访时长 ↔ 安全性主张」这条关系，确认矛盾成立；
         同时检查 Abstract 是否重复了同一越界表述（常见），
         若是则合并为同一 finding 的多处 locator，而非重复立条

Layer 5  M7-003，severity major，origin = "multiple_sources"
         （discovery 提出 + specialist_rule 判定 + reconciliation 确认）
         manual_review.action: "确认随访时长是否足以覆盖该类并发症的典型发生窗口"
```

**关键点**：M7 只拿主张包，**没有读全文**，但通过包里附带的
`followup_duration` 与 `study_design` 保持了全局判断力。
这就是「局部深度 + 全局连贯」的折中。

---

## 最后一问：这到底是不是真的多趟架构？

诚实回答：**契约、路由、schema、遥测与消融条件已经就位，但「是否真的分趟执行」
取决于运行时是否按 Layer 边界分别调度。**

已经做到的：

- Layer 1 明确禁读规则库与完整契约（SKILL.md §0 表格 + §2 开头）
- 每个专家的输入被显式限定为「一包证据 + 一本规则」
- 发现对象与最终契约对象在 schema 层就是**不同的类型**，
  发现阶段不要求 `evidence_refs`
- 工具调用登记为 `tool_task`，跳过必须给理由
- `candidate_resolution_log` 强制每个候选结清
- `runtime_utilization` 让「哪一层真的被用上」可测

尚未做到的（诚实标注）：

- 目前仍是**单个 agent 按指令自我分趟**，不是由外部编排器强制分成
  多次独立调用。真正的强制分趟需要一个执行器把每层作为单独进程调起，
  这一层尚未实现 —— `tools/ablation_harness.py` 的条件 C/D/E
  是用提示词区分的，属于**近似**而非强制。
- 因此消融结果需要结合 `runtime_utilization` 一起读：
  若 E 条件下 `references_read` 仍然是 1，说明分趟没有真的发生，
  该轮结果不能用来评价规则库的价值。

**这一点必须写下来，否则下一次又会把「提示词里写了分层」误当成「架构分层了」。**
