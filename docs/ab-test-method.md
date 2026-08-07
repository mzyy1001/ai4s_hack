# 怎么**搭**一个 A/B（uplift）测试 —— 方法篇

> 这份讲**方法**：一个可信的 A/B 测试该怎么设计、怎么造标准答案、怎么避坑。
> 只想知道命令怎么敲，看 [`how-to-ab-test.md`](how-to-ab-test.md)。

---

## 1. 先明确要回答的问题

官方评分里权重最高的一维（可完成性与工程质量，30%）判的是 **uplift**：

```
uplift = 挂 skill 的表现 − 同任务同模型下裸模型的表现
```

**不是绝对表现。** 所以：

- 裸模型本来就能做好的事 → 做进 skill 贡献为零，还多花 token（负分）
- 只有裸模型**做不到**的事，才可能产生 uplift

一切设计都要围绕「测出这个差值」，而不是「证明我们的 skill 很好」。

---

## 2. 方法：造标准答案，别比自由文本

### 2.1 错误做法（我们先走过一遍）

最直觉的做法是：让两臂各写一份审稿意见，然后比谁写得好。
**这个做法不可用**，因为：

- 两份自由文本没有可比的量纲，只能靠人读
- 条目数会被「合并同类项」影响 —— 少不代表差
- 不可复现，换个人读结论就变

### 2.2 正确做法：植入已知错误

```
干净的真实论文
      │
      ├─ 植入 N 条**已知**错误（每条带标准答案描述）
      │
      ├──────────────┬──────────────┐
      │              │              │
   A 臂：裸模型    B 臂：挂 skill   （两臂除 skill 外完全相同）
      │              │
      └──── 逐条判定「这条被发现了吗」────┘
                     │
      uplift = B 命中数 − A 命中数
```

这样才有 **ground truth**：每条错误是我们自己埋的，
「发现了没有」是客观事实，不靠人读。

实现：`tools/fault_injection_benchmark.py` + `tools/probe_cases/fault_library.json`

---

## 3. 怎么造这个测试

### 3.1 选宿主论文

用 `datasets/` 里的**真实论文**，不要用自己编的短片段。

```bash
python3 tools/make_host_paper.py \
  datasets/papers/<slot>/fulltext.xml --max-chars 26000 > host.txt
```

**为什么必须用完整论文** —— 这是最容易做错的一步：

| | 孤立片段 | 埋进真实论文 |
| --- | --- | --- |
| 错误周围有什么 | 几乎只有那一个错误 | 几十段正常内容 |
| 注意力 | 不被稀释 | 与其他发现竞争 |
| 结果 | **系统性高估裸模型** | 接近真实审稿难度 |

用孤立片段测，会得出「裸模型什么都能查出来」的结论，
据此去删检查，**会误删真正有价值的能力**。

建议选一篇**与错误类型领域不同**的宿主（比如用组学论文当宿主，
埋临床统计类错误），避免错误与上下文过于贴合而变得显眼。

### 3.2 写一条错误

在 `tools/probe_cases/fault_library.json` 里加一条：

```json
{
  "id": "stat.p_value_inconsistent",
  "description": "论文报告 t(10)=2.228 对应 P=0.001，但该统计量对应的双尾 P 约为 0.05，统计量与 P 值对不上",
  "inject": {
    "mode": "append",
    "position": 0.55,
    "faulty": "## Additional statistical comparison\n\n……含该错误的一段……"
  }
}
```

三个字段的要求：

- **`description` 是标准答案**，裁判拿它去判「这条被指出了吗」。
  要具体到能一眼确认，不要写「统计有问题」这种。
- **`inject.mode`**
  - `replace`：把宿主里已有的 `find` 串换成 `faulty`。**最自然**，
    因为错误长在论文原有内容里。缺点是依赖宿主含有该串。
  - `append`：在正文约 `position`（0–1）处插入一段。**最可靠**，
    但插入的段落会比原生内容略显突兀。
- **`position`**：错误藏在什么位置也影响难度。别全塞在结尾。

### 3.3 保证两臂只差一个变量

```
baseline/                withskill/
├── paper.md   ←同一份→   ├── paper.md
                          └── .opencode/skill/biomed-paper-review/
```

同一条指令、同一个模型、同一份论文，**只差挂不挂 skill**。
脚本自动造这两个目录，不要手工改其中一边。

### 3.4 判定

对每条错误，把审稿意见和标准答案一起交给裁判模型：

> 这份意见**是否明确指出了**该问题？实质说到即算 YES，措辞不必相同；
> 只泛泛提到相关章节、或只说「建议核对」而没点出具体问题，算 NO。

裁判用 `temperature=0`。判定失败记 `None` 并**排除出统计**。

### 3.5 读结果

报表里最该看的不是总分，是**两个差集**：

| 清单 | 含义 | 该怎么办 |
| --- | --- | --- |
| **只有挂 skill 查出来的** | skill 的真实价值所在 | 这些检查值得写完整规则 + 上工具 |
| **只有裸模型查出来的** | **skill 反而挡住了发现** | 必须修 —— 说明契约挤占了注意力 |

第二个清单非空是**红灯**。我们实测出现过：完整论文自由 A/B 里，
裸模型 15 条、挂 skill 9 条且是**真子集**。

---

## 4. 五个坑（每个都真实踩过）

### 4.1 调用失败 ≠ 没查出来

**今晚栽了四次，这是最危险的一个。**

API 超时、限流、服务端错误 → 拿到的是错误串，不是「什么都没发现的意见」。
把它当成「漏掉」，会得出**完全相反**的结论。

这与本项目契约里 `parse_failed != not_reported` 是同一条原则：
**我们没问到 ≠ 对方没有。**

做法：

- 审阅结果先做**有效性检查**（长度下限 + 错误标记），无效就**中止整次基准**，
  不产出任何数字
- 裁判失败记 `None` 并排除，不记 0
- 有效样本为 0 时输出 `INCONCLUSIVE`，明确拒绝下结论

### 4.2 两臂同时 0 命中 = 先怀疑工具

植入的错误比天然错误显眼，裸模型在真实论文上都能报十几条。
**两臂同时 0 命中，几乎一定是审阅或裁判没跑起来**，不是「都没查出来」。
先打开两份 `.out.md` 人工确认里面确实是审稿意见。

### 4.3 模型与凭据要真的通

两个独立的坑，都会让 opencode 静默失败：

1. **provider 没配**。opencode 需要 `provider/model` 形式。
   Qwen 要先在 `~/.config/opencode/opencode.jsonc` 里加 DashScope 兼容 provider，
   之后才能 `--model dashscope/qwen3.8-max`。
2. **变量没导出**。`~/.config/qwen/credentials.env` 里的行**没有 `export`**，
   直接 `source` 只设了 shell 变量，**不会传给子进程**。
   必须 `set -a; source ...; set +a`。
   （Python 工具直接读文件所以不受影响，opencode 读 `os.environ` 就挂了 ——
   这种「一半能用」最难查。）

跑基准前先冒烟测一次：

```bash
set -a && source ~/.config/qwen/credentials.env && set +a
opencode run --model dashscope/qwen3.8-max "只回复两个字：可用"
```

### 4.4 植入的错误偏显眼 —— 但不影响结论

刻意加进去的段落，比论文里天然长出来的错误好找，
所以**绝对命中率会偏高**。

但 uplift 是**差值**，这个偏差对两臂**同等作用**，会被差掉。
所以：**可以信差值，不要信绝对命中率**。

### 4.5 别用同一个模型既审稿又当裁判就下强结论

裁判和被裁判同源会有偏差。条件允许时换一个模型当裁判，
或至少对关键结论人工复核那两份 `.out.md`。

---

## 5. 拿到结果之后怎么用

三档处置，**「不写详细规则」不等于「删掉这个检查」**：

| 情形 | 处置 | 在 SKILL.md 里 |
| --- | --- | --- |
| 两臂都查得出 | **① 只列清单** | 留**一行**引导注意力，不写判定细则、阈值、正反例 |
| 裸模型时对时错 | **② 清单 + 确定性工具** | 一行清单 + 工具跑一遍，规则文字精简 |
| 只有挂 skill 查得出 | **③ 完整规则 + 工具** | uplift 来源，写进 §6.5「什么时候必须运行」最前面 |

一行清单条目几乎不花 token 还能把注意力引过去；
四百行判定表很贵，而且实测会**挤占发现的注意力**。

---

## 6. 最小复现流程

```bash
# 0. 确认模型通
set -a && source ~/.config/qwen/credentials.env && set +a
opencode run --model dashscope/qwen3.8-max "只回复两个字：可用"

# 1. 跑植入式基准（有标准答案）
python3 tools/fault_injection_benchmark.py \
  --paper datasets/papers/omics_heatmap__journal.pone.0338705/fulltext.xml \
  --model dashscope/qwen3.8-max --judge-model qwen3.8-max \
  --keep-paper --outdir /tmp/faultbench

# 2. 人工核对两份意见确实是意见，不是错误串
head -40 /tmp/faultbench/baseline.out.md
head -40 /tmp/faultbench/withskill.out.md

# 3. 加新检查前，先单项探针问一句「裸模型自己能不能查」
python3 tools/make_host_paper.py datasets/papers/<slot>/fulltext.xml > /tmp/host.txt
python3 tools/baseline_probe.py --case tools/probe_cases/<x>.md \
  --error "..." --host /tmp/host.txt --repeats 3
```

---

## 7. 一句话总结

**造标准答案，控制单一变量，把失败和「没发现」严格分开，只信差值不信绝对值。**

---

## 8. 自己动手：不依赖我们的脚本，从零做一次

如果你想自己造一篇含错误的论文、自己把流程跑通（或者想验证我们的脚本没骗你），
照下面六步走。全程只需要 opencode 和一个文本编辑器。

### 第 1 步：准备一篇干净的论文

从语料里挑一篇，转成纯文本：

```bash
python3 tools/make_host_paper.py \
  datasets/papers/omics_heatmap__journal.pone.0338705/fulltext.xml \
  --max-chars 26000 > /tmp/clean.md
```

没有这个脚本也行 —— 任何一篇真实论文的正文纯文本都可以，
**但必须是完整论文，不能是几行片段**（理由见 §3.1）。

### 第 2 步：手工植入错误，并记下标准答案

打开 `/tmp/clean.md`，在正文中间插入几段含错误的内容。
**每插一条，就在一张表里记下「这条错误是什么」** —— 这就是你的标准答案。

例如插入这一段：

```markdown
## Dose-response characterisation

化合物的半数抑制浓度经四参数 logistic 拟合为
IC50 = 20.0 μM（95% CI 9.8–15.7 μM），拟合优度 R² = 0.98。
```

对应的标准答案记为：

> 报告的点估计 20.0 μM 落在其自身报告的 95% CI [9.8, 15.7] 之外，点估计与区间不自洽

**造错误的几条建议**

- 一次埋 10–15 条，太少统计噪声大，太多单次审阅顾不过来
- 分散在论文不同位置，别全塞结尾
- 覆盖不同类型：算术自洽、统计方法、单位量纲、命名规范、伦理缺失、结论越界
- 每条都要能**一眼确认对错**，别埋「这个设计不够好」这种主观的
- 存一份 `faults.md` 记录：编号 + 标准答案描述 + 埋在哪一节

存成 `/tmp/paper_with_faults.md`。

### 第 3 步：搭两个只差一个变量的目录

```bash
mkdir -p /tmp/ab/baseline /tmp/ab/withskill
cp /tmp/paper_with_faults.md /tmp/ab/baseline/paper.md
cp /tmp/paper_with_faults.md /tmp/ab/withskill/paper.md

# 只有 withskill 挂 skill
mkdir -p /tmp/ab/withskill/.opencode/skill
cp -R skills/biomed-paper-review /tmp/ab/withskill/.opencode/skill/
```

**检查一遍**：两个目录里的 `paper.md` 必须**逐字节相同**，
`baseline/` 里**不能有** `.opencode/`：

```bash
cmp /tmp/ab/baseline/paper.md /tmp/ab/withskill/paper.md && echo "论文一致"
ls -a /tmp/ab/baseline/    # 不应出现 .opencode
```

### 第 4 步：两臂各跑一次审阅

```bash
set -a && source ~/.config/qwen/credentials.env && set +a

PROMPT="你是资深生物医药论文审稿人。请审阅 paper.md 这篇论文，指出你发现的所有问题（统计学、方法学、报告规范、伦理、图表、结论等）。逐条列出，每条给出具体依据与出处。不要客套。"

opencode run --dir /tmp/ab/baseline  --model dashscope/qwen3.8-max "$PROMPT" > /tmp/ab/baseline.out.md
opencode run --dir /tmp/ab/withskill --model dashscope/qwen3.8-max "$PROMPT" > /tmp/ab/withskill.out.md
```

**`--dir` 必须给。** opencode 会自己解析「项目目录」，
**忽略你的 shell cwd** —— 不给 `--dir` 会跑到别的目录去，
两臂都读不到 paper.md，而且 baseline 臂可能误加载仓库里的 skill，
根本不是基线。这个坑我们踩过。

### 第 5 步：先验货，再算数

**打开两份输出看一眼**，确认里面确实是审稿意见：

```bash
head -30 /tmp/ab/baseline.out.md
wc -c /tmp/ab/*.out.md        # 几百字节 = 多半是错误串，不是意见
```

看到 `Error:`、`0 matches`、几百字节的短输出 —— **本次作废，重跑**。
**不要**把它当成「什么都没查出来」。

### 第 6 步：逐条判定，算差值

对标准答案里的每一条，分别问：这份意见指出这个问题了吗？
人工读也行，交给模型判也行：

```bash
# 交给模型判（对每条错误、每份意见各问一次）
opencode run --model dashscope/qwen3.8-max "下面是一份审稿意见和一个问题描述。判断这份意见是否明确指出了该问题？实质说到即算 YES，措辞不必相同；只泛泛提到相关章节算 NO。先输出 VERDICT: YES 或 VERDICT: NO。

【问题描述】报告的点估计 20.0 μM 落在其自身报告的 95% CI [9.8, 15.7] 之外

【审稿意见】
$(cat /tmp/ab/baseline.out.md)"
```

最后填这张表：

| 错误 | 裸模型 | 挂 skill |
| --- | --- | --- |
| ci_self_inconsistent | ✗ | ✓ |
| … | | |
| **命中数** | **A** | **B** |

**uplift = B − A**

然后看两个差集：**只有挂 skill 查出来的**（skill 的价值）、
**只有裸模型查出来的**（skill 挡住了发现，红灯）。

### 想省事就用脚本

上面六步等价于：

```bash
set -a && source ~/.config/qwen/credentials.env && set +a
python3 tools/fault_injection_benchmark.py \
  --paper datasets/papers/omics_heatmap__journal.pone.0338705/fulltext.xml \
  --model dashscope/qwen3.8-max --judge-model qwen3.8-max \
  --keep-paper --outdir /tmp/faultbench
```

错误库在 `tools/probe_cases/fault_library.json`，加一条就是加一个 JSON 对象（格式见 §3.2）。
**但脚本跑完也要按第 5 步人工验一次货** —— 我们已经因为跳过这一步，
把「两臂都没跑起来」误报成过「uplift = +0，两臂完全一致」。
