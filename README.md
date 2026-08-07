# 生物医药论文 AI 审稿 Skill

黑客松交付物：**一个自包含的 Agent Skill 包** → [`skills/biomed-paper-review/`](skills/biomed-paper-review/)

输入一篇生物医药论文（JATS XML / PDF / 纯文本），输出结构化证据表、图表解读与定位、
多维审核发现、抽取覆盖率与复核置信度，以及分优先级的人工复核建议。

> **本分支（`main`）只放交付物本体。**
> 开发工作区 —— 测试语料、评测工具、实验记录、设计文档 —— 全部在
> [`dev`](../../tree/dev) 分支。

---

## 核心设计：分层隔离的是「审阅目标」，不是「论文正文」

这是本项目最重要的一条经验，也是它与「把规则塞进一个大提示词」的根本区别。

裸模型本身就是很强的审稿人。把五千行规则压进一次上下文会挤占注意力
（实测出现过八本规则库只读了一本），所以**审阅目标必须拆开**：
一个子会话一个角色、一本规则、一个干净的推理上下文。

但**正文不能跟着一起切**。实测代价（同一篇真实论文、同一模型、同一份全文）：

| | 裸模型（全文 + 开放提问） | 曾用架构（发现层压成候选 → 专家只拿证据包） |
| --- | --- | --- |
| 发现数 | **63**（critical 2） | 43（critical 0） |

失败机理是**两次压缩、且第二次由第一次决定**：发现层先把论文压成候选清单，
证据包再按该清单去正文取片段 —— 没人标注过的段落（构件示意图、克隆描述、品系来源）
就没有任何一层读得到，漏了即结构性不可恢复。

现在的流水线：

```
L0   全局审阅    全文 + 极简提问，无规则库 / 无 schema / 无清单
                 └ 这就是裸模型条件本身 → Skill 的下限被钉死在裸模型上
L0b  测绘与路由  全文，只产地图与标识符，不找问题
L1   M2–M7      **各拿全文** + 自己那一本规则；对 L0 的每一条必须表态
L2   确定性工具 + X1 外部核验
L3   同 task_id 续接，让专家看到确定性证据后复议
L4   校正子会话  **也拿全文**；审计有没有 L0 条目不明不白消失
L5   契约归一与报告渲染
```

**加法保证**：最终结果 ⊇ L0 的结论，减去且仅减去被显式驳回并给出理由的条目。
Skill 相对裸模型只能做加法，或带论证地做减法，不得凭空缩水；
违反则拒绝渲染报告，把缺口写进 `system_limitations`。

---

## 增益从哪来

纯文本的内部一致性检查，裸模型本来就会做 —— 那部分不可能有增益。
真正的增益只能来自模型**结构上做不到**的两件事：

1. **确定性计算**：`table_total` / GRIM / p 值反算 / CI 自洽 / 计数-百分比 / 单位归一化 ——
   可复算，不靠语感。
2. **外部权威数据**：训练截止之后的撤稿、误认细胞系长尾、注册库里的结局切换 ——
   模型无从知晓。

`scripts/external_figure_validation.py`（X1）按需查询 **12 个数据库、14 项检查**：
Cellosaurus、ClinicalTrials.gov、Europe PMC、Crossref、UniProt、ChEMBL、PubChem、
RCSB PDB、HGNC、SciCrunch/RRID、NCBI E-utilities、PRIDE。
**不预置任何数据集**：稿件里真的出现某个标识符才发起那一次查询。

外部源不可达时一律产 `system_limitation`，**绝不**变成 finding ——
「查不到」不等于「论文错」。

---

## 包内结构

```
skills/biomed-paper-review/
├── SKILL.md                    唯一入口：编排流程、模块路由、共享契约（482 行）
├── references/                 11 份规则库
│   ├── 00-contracts.md         ★ 共享契约（证据登记表 / 三类记录 / 三项评分）
│   ├── 00-routing.md           问题类型 → 专家 → 索引 → 规则库 → 工具
│   ├── 00-runtime-contract.md  子会话用的最小契约集合
│   ├── 01-structured-extraction.md   前置抽取（不产 finding）
│   ├── 02-macro-logic.md             M2 宏观逻辑与报告完整性
│   ├── 03-experimental-methods.md    M3 方法重构与逻辑审计（7 阶段）
│   ├── 04-statistics.md              M4 统计学方法
│   ├── 05-figures-and-charts.md      M5 图谱解析与图表规范
│   ├── 06-ethics-compliance.md       M6 伦理合规（三法域规范库）
│   ├── 06b-animal-model-ethics-enhancement.md  动物福利红线与 3R
│   └── 07-conclusions-discussion.md  M7 结论与证据层级
├── scripts/                    7 个确定性工具，全部带 --selftest
│   ├── statistical_forensics.py      5 项统计取证
│   ├── external_figure_validation.py X1 外部核验：12 库 / 14 检查
│   ├── ethics_compliance_check.py    伦理规范库筛查
│   ├── animal_model_compliance.py    动物模型福利与 3R 审计
│   ├── sequence_identifier_audit.py  序列 / HGVS / 登录号 / 引物
│   ├── figure_integrity_audit.py     图像重复 / 拼接 / 异常均匀区块
│   └── normalize_biomed_units.py     单位归一化，fail-closed
├── schemas/                    12 份 JSON Schema（模块间集成契约）
├── resources/                  伦理规范库 + X1 离线回放 fixture
└── templates/review_report.md  报告渲染模板
```

**自包含**：包内不引用任何包外路径，全部内部引用可解析。

**依赖：不需要 `requirements.txt`，也刻意不提供。**

| 脚本 | 依赖 |
| --- | --- |
| 其余 6 个 | **纯标准库** |
| `figure_integrity_audit.py` | 可选 `numpy` + `Pillow`（仅像素级审计需要） |

`numpy` / `Pillow` 缺失时**不报错**：登记
`system_limitation(figure_unreadable)` 后正常退出（exit 0），其余审核不受影响。
该降级路径带专门自检（`依赖缺失 -> system_limitation 而非崩溃`），
可用 `PYTHONPATH` 屏蔽依赖复现。

**为什么不给 `requirements.txt`**：给了就等于请求评测环境执行一次 pip 安装 ——
在白名单网络下安装失败会把「一个可选检查降级」升级成「整次运行失败」。
现在的形态是：装了更好，没装也照跑。

## 自检

```bash
cd skills/biomed-paper-review
for f in scripts/*.py; do python3 "$f" --selftest; done
```

X1 支持离线回放：`--offline` 严格回放已录制响应，未命中即报错，绝不回退到网络。

## 边界（必须原样写入每份报告）

- 本工具**不替代同行评审**，不产出录用/退稿决定；
- 每条发现必须可回溯到论文原文位置，**不得**凭生成内容立论；
- 「未报告」不等于「未实施」；「我们没拿到」不等于「稿件没写」；
- 工具失败、外部源不可达、图像无法读取，一律登记 `system_limitation`，
  **不归责稿件**；
- 三项评分（稿件风险分 / 抽取覆盖率 / 复核置信度）**互不替代**，
  不得合并为单一数字；partial 分数不得与完整审核分数并列比较。
