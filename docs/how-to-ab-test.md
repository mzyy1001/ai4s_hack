# 怎么**跑** A/B（uplift）测试 —— 操作篇

> 这份讲**怎么敲命令**。想知道一个 A/B 测试该怎么**设计**、
> 标准答案怎么造、有哪些坑，先看 [`ab-test-method.md`](ab-test-method.md)。

**这是本项目最该反复做的一件事。** 官方评分里权重最高的一维（可完成性与工程质量，30%）
判的不是绝对表现，而是 **uplift** —— 同一任务、同一模型下，**挂了本 skill 比裸模型提升了多少**。

> 裸模型本来就能做好的事，做进 skill 里贡献为零，还多花 token（负分）。
> 所以每加一样东西之前，先问一句：**裸模型自己能不能做到？**

---

## 0. 一分钟结论（已实测，别重复踩）

| 实测 | 结果 |
| --- | --- |
| 完整论文，裸模型 vs 挂 skill（gpt-5.6-sol） | 裸模型 **15 条**实质发现，挂 skill 只有 **9 条**，且是**真子集** |
| 原因一 | 契约挤占注意力：模型先读三份 reference 才读论文，结构取代了发现 |
| 原因二 | 确定性脚本**从未被执行** —— 模型把 `.py` 当资料读了 |
| 修正 | `SKILL.md §2.0` 加「先通读列全问题再进契约」；`§6.5` 加「脚本要运行不要只读」 |
| 修正后 | 脚本确实被执行了，找回 1 条，**差距仍未补平** |
| 单项探针（qwen3.8-max） | `table_total_mismatch`（分类计数之和 ≠ 分母）裸模型自己就查得出来 → 零 uplift |

**结论：裸模型在这个任务上很强。** uplift 只能来自它**做不到的确定性计算**，
而且必须对准真实论文里**实际出现**的错误类型。

---

## 1. 两种测法，分别回答不同问题

| 工具 | 回答的问题 | 什么时候用 |
| --- | --- | --- |
| `tools/fault_injection_benchmark.py` | **有标准答案**：植入 N 条已知错误，两臂各查出几条？ | **首选** —— 改了任何东西之后 |
| `tools/uplift_ab.py` | 无标准答案：两份自由文本意见的粗对比 | 只作辅助，结论要人读 |
| `tools/baseline_probe.py` | **某一条具体检查**，裸模型能不能自己查出来？ | **加任何新检查之前** |
| `tools/uplift_sweep.py` | 已实现的**全部**检查里，哪些其实是零 uplift？ | 定期体检；决定哪些写详细规则 |

---

## 2. 整体 A/B：`uplift_ab.py`

```bash
# 凭据（官方统一模型是 GLM / Kimi 系列；我们手上有 Qwen）
source ~/.config/qwen/credentials.env

python3 tools/uplift_ab.py \
  --paper datasets/papers/rct_clinical__journal.pone.0339677/fulltext.xml \
  --model qwen3.8-max
```

它做的事：造两个**除 skill 外完全相同**的临时目录（一个带 `.opencode/skill/`，
一个不带），跑同一条指令，把两份输出并排存下来。

**输出怎么读**

```
指标                    裸模型      挂 skill        差值
编号条目数                 15            9         -6
出处引用数                 42           38         -4
执行过确定性脚本         False         True
```

- **条目数下降不必然是退步** —— 合并同类项也会让条数变少。
- **但如果挂 skill 的发现是裸模型的真子集，就是实打实的负 uplift。**
  必须人工 diff 两份输出确认这一点：
  ```bash
  diff -y <工作目录>/baseline.out.md <工作目录>/withskill.out.md | less
  ```
- **「执行过确定性脚本」为 False 时**，本 skill 的主要增量来源根本没生效，
  这时候比条目数没有意义，先去修 `SKILL.md §6.5`。

---

## 3. 单项探针：`baseline_probe.py`（**加检查前必跑**）

```bash
source ~/.config/qwen/credentials.env

# 先生成宿主论文（把错误藏进真实论文里，见 §5 为什么必须这样）
python3 tools/make_host_paper.py \
  datasets/papers/omics_heatmap__journal.pone.0338705/fulltext.xml \
  --max-chars 26000 > /tmp/host.txt

python3 tools/baseline_probe.py \
  --case tools/probe_cases/<你的案例>.md \
  --error "该错误的具体描述，裁判据此判定" \
  --host /tmp/host.txt \
  --repeats 3
```

**四档结论与处置**

| 结论 | 含义 | 该怎么做 |
| --- | --- | --- |
| `BASELINE_FINDS_IT` | 裸模型多数能查出 | **① 只列清单** —— SKILL.md 里留一行引导注意力即可，**别写判定细则** |
| `BASELINE_UNRELIABLE` | 时对时错 | **② 清单 + 确定性工具** —— 用工具变成稳定命中，规则文字仍精简 |
| `BASELINE_MISSES_IT` | 完全查不出 | **③ 完整规则 + 工具** —— uplift 主来源，值得写清楚 |
| `INCONCLUSIVE` | 调用失败、有效样本 0 | **不得据此下任何结论**，修好再跑 |

> **「不写详细规则」不等于「删掉这个检查」。** 一行清单条目几乎不花 token
> 还能把注意力引过去；四百行判定表很贵，而且按实测会挤占发现的注意力。

### 怎么写一个案例

案例是一段**含该错误的最小论文片段**，放 `tools/probe_cases/<name>.md`。
写完在 `manifest.json` 里登记一条，`uplift_sweep.py` 就会自动带上它。

```json
{
  "id": "stat.my_new_check",
  "implemented_by": "scripts/statistical_forensics.py",
  "error": "裁判用来判定的错误描述，要具体到能一眼确认",
  "case": "## Methods\n……含该错误的片段……"
}
```

---

## 4. 全量体检：`uplift_sweep.py`

```bash
source ~/.config/qwen/credentials.env
python3 tools/make_host_paper.py datasets/papers/omics_heatmap__journal.pone.0338705/fulltext.xml > /tmp/host.txt

python3 tools/uplift_sweep.py --host /tmp/host.txt --repeats 3 --gap 15
```

- 断点续跑：缓存在 `~/.config/ai4s_hack/sweep_cache.json`（**仓库外** ——
  放仓库里会被轮次守卫的 `git clean -fd` 删掉，白白浪费配额）
- 产出 `docs/uplift-sweep.md`，逐条给「① 只列清单 / ② 清单+工具 / ③ 完整规则」
- 只想重跑某几类：`--only stat. seq.`
- 只出报告不跑探针：`--report`

---

## 5. 方法学：为什么**必须**把错误藏进真实论文

**这是最容易做错、也最容易得出反向结论的一步。**

用孤立的最小片段做探针会**系统性高估裸模型**：

- 片段里几乎只有那一个错误，注意力不被稀释
- 错误因为「是唯一内容」而显眼
- 没有其他发现与它竞争篇幅

真实审稿是在一整篇论文里找问题，几十个观察互相竞争，**难度完全不同**。
据孤立片段的结论去删检查，会**误删真正有价值的能力**。

所以 `baseline_probe.py` 与 `uplift_sweep.py` 都应当带 `--host`。
不带时脚本会显式警告。报告里标 `isolated` 的行，结论要打折看。

---

## 6. 几条纪律

1. **调用失败 ≠ 模型查不出来。** 这与契约里 `parse_failed != not_reported` 是同一条原则。
   探针初版曾把超时计为「漏掉」，从而得出「值得实现」的反向结论 —— 已修。
   有效样本为 0 时一律 `INCONCLUSIVE`，拒绝下结论。
2. **一个宿主、一个模型、三次重复只是方向性证据**，不是精确命中率。
   `① 只列清单` 的结论比 `③ 完整规则` 更可信 ——
   「裸模型在干扰下还是找到了」比「这次没找到」是更强的证据。
3. **本方法只测「能不能发现」**，没测「发现后的表述质量与证据可审计性」。
   后者是 skill 的另一类价值（证据链维度 25%），
   **不因某条检查被判零 uplift 而否定**。
4. **官方统一模型是 GLM / Kimi 系列。** 我们手上是 Qwen，同为国产同族，
   但**不是**评测用的那一个。跨模型结论要保守。
5. 改 SKILL.md 主流程后**一定要重跑整体 A/B** —— 我们已经踩过一次
   「加了很多东西反而变差」。

---

## 7. 凭据与成本

| 项 | 位置 |
| --- | --- |
| Qwen / DashScope | `~/.config/qwen/credentials.env` 的 `DASHSCOPE_API_KEY`（600 权限，仓库外） |
| 端点 | `https://dashscope.aliyuncs.com/compatible-mode/v1`（OpenAI 兼容） |
| 可用模型 | `qwen3.8-max` / `qwen3.7-max` / `qwen3-max` / `qwen3-max-preview` |
| OpenAI（备用） | `~/.config/ai4s_hack/openai.env` |

一次整体 A/B ≈ 2 次完整论文审阅；一条探针 ≈ `repeats × 2` 次调用（审阅 + 裁判）。
全量扫描 20 条 × 3 次 ≈ 120 次调用，**注意配额**。
遇到 HTTP 403 / 连接重置多半是限流，加大 `--gap` 或改用 token-plan 端点
（`~/.config/qwen/credentials.env` 里的 `QWEN_PLAN_BASE_URL`）。
