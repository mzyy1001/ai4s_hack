# 运行时最小契约

> **本文件不是新的事实来源。** `schemas/*.json` 与 `00-contracts.md` 始终是权威。
> 本文件只是从中摘出**专家通道在产出记录时必须知道的最小集合**，
> 目的是让专家不必为了写出一条可互操作的记录而先读一千两百行完整契约。
>
> 冲突时一律以 `00-contracts.md` 与 schema 为准。本文件若与它们不一致，是本文件的错。

## 为什么要有这一层

实测：完整契约 1209 行，八个 reference 合计约五千行。一次全流程追踪里
模型只读了 `00-contracts` 一个文件，其余七个一个没读 —— 不是它偷懒，
而是**在发现问题之前就被要求先装下全部规范**，注意力已经耗掉了。

契约的作用是**组织和校验已发现的问题**，不是在发现之前占满上下文。
所以：发现阶段用轻量结构，最终记录才套完整契约。

## 1. 三类记录，互不混淆

| 记录 | 谁产 | 有 severity | 含义 |
| --- | --- | --- | --- |
| `finding` | M2–M7 | **有** | 稿件级问题，必须有可审计证据 |
| `extraction_signal` | Stage 2/3/3b/3c 与确定性工具 | **无** | 可复算的观察，交模块判定 |
| `system_limitation` | 任意阶段 | **无** | **我们**的能力限制，不归责稿件 |

**最容易错的一条**：外部源不可达、脚本失败、解析不了 —— 全部是
`system_limitation`，**绝不是** finding。
`parse_failed ≠ not_reported`：「我们没读到」不等于「稿件没写」。

## 2. finding 的最小形状

```json
{
  "id": "M4-003",
  "module": "M4",
  "category": "sample_size_unjustified",
  "severity": "major",
  "description": "……",
  "evidence_refs": ["EV-012"],
  "manual_review": {"action": "……", "who": "statistician"}
}
```

- `severity` 枚举：`critical` / `major` / `minor` / `info`
- `evidence_refs[]` **不得为空**；`major` 及以上必须给 `manual_review.action`
- 证据的规范存储只有一处：`evidence_registry`。其他位置只写 `evidence_refs[]`

## 3. evidence 的最小形状

三型，按「这条证据在说什么」选：

| type | 用于 | 关键约束 |
| --- | --- | --- |
| `present` | 稿件里**有**这段内容 | 必须给 `locator`；`quote` 可选 |
| `absence` | 稿件里**没有**这段内容 | 必须给检索范围与检索词；**禁止 quote 与 locator** |
| `external` | 公开数据源的事实 | 必须给端点、查询、取回时刻、响应 hash |

> **绝不为不存在的内容编造引文。** absence 型证据禁止 `quote` 就是为了防这个。

## 4. extraction_signal 的最小形状

```json
{
  "id": "SIG-042",
  "type": "table_total_mismatch",
  "target": "Table 1",
  "detail": "……",
  "evidence_refs": ["EV-007"],
  "routed_to": ["M4", "M2"],
  "produced_by": "stage_2"
}
```

**无 severity。** signal 只陈述「算出来对不上」，是否构成稿件问题由模块判定。

## 5. system_limitation 的最小形状

```json
{
  "id": "SYS-003",
  "category": "external_source_unavailable",
  "impact": "……未完成核验",
  "affected_modules": ["M3"],
  "recommended_action": "恢复后重跑；在此之前不得就该主张下结论",
  "produced_by": "stage_3c_external_validation"
}
```

**无 severity。**

## 6. confidence 枚举

`high` / `medium` / `low`。

- 视觉估读（`pixel_estimated`）一律 `low`，且必须写成区间
- 跑过审核模块用 `review_confidence`，没跑过用 `output_confidence`，**二者互斥**

## 7. 发现阶段**不受**本契约约束

Layer 1 发现与 Layer 2 专家的中间产物用轻量结构
（`candidate_issue` / `provisional_finding`），**不需要**满足上面的证据要求。
只有进入 Layer 4 之后的最终记录才必须完整合规。

这是本次架构调整的核心：**先高召回地发现，再形式化**。
不得因为「一时给不出 evidence_refs」就在发现阶段把问题丢掉。

---

完整定义见 `00-contracts.md`；机器校验以 `schemas/*.json` 为准。
