# tools/orchestration —— **不是提交物，评测沙箱里跑不了**

> **NON_OP。** 这个目录**不属于** `skills/biomed-paper-review/` 交付包，
> 也**不是**本 Skill 的运行方式。评测沙箱运行的是 Skill 本身（由 Agent 运行时
> 按 `SKILL.md` 编排子会话），不是这里的 Python。

## 这是什么

同一套分层审阅协议的**独立 Python 实现**：不依赖任何 Agent 运行时，
直接对模型供应商发 HTTP 请求，把每一层编译成一次**无历史的独立模型调用**。

| 文件 | 作用 |
| --- | --- |
| `orchestrator.py` | 把分层协议编译成多次独立模型调用 |
| `model_client.py` | 无状态单次调用客户端；供应商由环境变量选择 |
| `router.py` | 路由决策 |
| `packet_builder.py` | 组装每一层的输入 |
| `tool_dispatcher.py` | 调用 `skills/.../scripts/` 里的确定性工具 |
| `telemetry.py` | 逐次调用的计量 |
| `prompts/` | 各阶段提示词模板 |

## 为什么留着

1. **实验台架**：可复现的 A/B 运行、逐调用可控、带遥测，适合做 uplift 测量。
2. **历史原因**：它诞生于「还不确定 Agent 运行时能否真正创建隔离子会话」的时期。
   该能力现已实测确认（见 `docs/results/hierarchical-synthetic-run.jsonl`），
   因此它不再是主路径。

## 为什么不能当成交付物

- 需要私有 API Key（`<PROVIDER>_API_KEY`）与直连模型厂商的出网权限，沙箱不提供；
- 它跑出来的结果**不能**用来代表 Skill 在沙箱里的行为。
  做对比实验时，**绝不可**把它的产物与「Skill 原生分层」条件混为一谈。

## 运行（仅本地）

```bash
export BIOMED_REVIEW_PROVIDER=dashscope        # dashscope | openai | zhipu | moonshot
export DASHSCOPE_API_KEY=...                   # 缺 key 时明确报错，不静默降级
python3 tools/orchestration/orchestrator.py --help
```
