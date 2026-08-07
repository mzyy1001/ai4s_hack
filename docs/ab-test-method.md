# 怎么**搭**一个 A/B（uplift）测试 —— 方法篇

> 这份讲**方法**：一个可信的 A/B 测试该怎么设计、标准答案从哪来、怎么避坑。
> 只想知道命令怎么敲，看 [`how-to-ab-test.md`](how-to-ab-test.md)。
>
> **2026-08-07 大改**：放弃人工植入错误，改用**真实论文 + 权威来源给出的客观
> 标准答案**，并按错误类型铺开、每类只取一两篇。原因见 §2.3 与 §2.5。

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

这条我们是**用一次负 uplift 换来的**：挂 Skill 9 条意见，裸模型 15 条，
而且是真子集。当时全部检查都停在「重读正文查内部自洽」这一层 ——
而内部自洽裸模型本来就会做。详见 [`external-databases.md`](external-databases.md)。

---

## 2. 标准答案从哪来

### 2.1 先排除一个错误做法

最直觉的做法是：让两臂各写一份审稿意见，然后比谁写得好。
**这个做法不可用**：

- 两份自由文本没有可比的量纲，只能靠人读
- 条目数会被「合并同类项」影响 —— 少不代表差
- 不可复现，换个人读结论就变

必须有**标准答案**：一组「这篇论文确实存在的问题」，再逐条问两臂查没查出来。

### 2.2 三种来源，按优劣排序

| 来源 | 错误真不真 | 标准答案客不客观 | 推荐度 |
| --- | --- | --- | --- |
| **A. 权威来源判定的已知问题** | 真 | 客观（数据库/期刊给的） | **首选** |
| B. 撤稿论文 + 撤稿声明 | 真 | 客观（期刊给的） | 好，但稀缺 |
| C. 人工植入错误 | 假 | 客观（自己写的） | **不要用**（见 §2.3） |

### 2.3 为什么放弃人工植入（两轮实测失败记录）

植入式基准做过两轮，两轮都**饱和** —— 两臂满分，测不出任何差异。
原因不是错误写得不好，而是**植入这个动作本身留下痕迹**：

**第一轮：语言破绽。** 中文错误段落插进英文论文。裸模型在意见里自己起了个
小标题叫「三、插入的中文实验段落（逐条）」—— 它根本不用去**找**，
只要挑出那几段明显不属于本文的段落逐条读就行。它在挑外来物，不是在审稿。

**第二轮：主题破绽。** 全部改写成英文、融入既有章节、不新起标题之后仍然饱和。
往一篇纯 TCGA 生信论文里插动物实验、临床试验、毒理段落，模型第一句话是
「大量与研究主题无关、彼此孤立的实验段落被插入方法部分」。

**结论：只要错误是外来的，就总有痕迹可循，难度就不真实。**
真实论文里的错误骗过了真实的同行评审 —— 那才是我们要测的难度。

### 2.4 四类真实错误，四个不同的出题人

| kind | 错误 | 出题人 | 裸模型能不能自己查 |
| --- | --- | --- | --- |
| `cell_line` | 细胞系被错误鉴定 | Cellosaurus | 著名的几条知道，长尾不知道 |
| `cited_retracted` | 引用已撤稿文献，且发表于撤稿**之后** | Europe PMC | 不能 —— 撤稿常在训练截止之后 |
| `retrospective_registration` | 注册晚于研究开始（违反 ICMJE） | ClinicalTrials.gov | **绝无可能** —— 正文不写注册日期 |
| `retracted_statistical` | 因统计/数据错误被撤稿 | 期刊撤稿声明 | 部分能 |

举一个具体的。Cellosaurus 对 MDA-MB-435 的注释是：

> `Problematic cell line: Contaminated. Shown to be a M14 derivative.
> Originally thought to originate from the pleural effusion of a breast carcinoma.`

它是**黑色素瘤**衍生系。而 Europe PMC 里用它研究「乳腺癌」的开放获取全文有
三千三百余篇 —— 这些论文的结论都建立在「它是乳腺癌细胞」这个不成立的前提上。
这个错误**推翻的是全文**，不是某个次要瑕疵。

`retrospective_registration` 那一类尤其能说明问题：注册日期和研究开始日期
**都只存在于注册库**，论文正文几乎从不写。裸模型不是「没想到去查」，
而是**根本无从查起**。这就是「裸模型做不到」的教科书定义。

### 2.5 为什么每类只要一两篇

拿二十篇同一个细胞系错误去测，测的是**这一条检查通不通**，不是 Skill 的能力面。
每类一两篇、类型铺开，才能看出**哪几类真有 uplift、哪几类是裸模型本来就会**——
后者应该从 Skill 里删掉，因为它们只会多花 token 拉低分数。

**宽而浅优于窄而深。** 我们要的是「增益在哪里」，不是「某一处增益多大」。

要提升统计可信度时，正确做法是**加类型**（多接几个数据库、多几种错误），
而不是在同一类里堆篇数。

---

## 3. 怎么跑

### 3.1 建语料

```bash
# 每类取两篇，四类共八篇
python3 tools/fetch_ground_truth_papers.py --per-kind 2

# 只跑某几类
python3 tools/fetch_ground_truth_papers.py --kinds cell_line retrospective_registration

# 先看看有哪些已知问题细胞系
python3 tools/fetch_ground_truth_papers.py --list-lines 20
```

每篇论文得到一个目录，含 `fulltext.xml` 与 `meta.json`；
`meta.json` 的 `ground_truth.expected_finding` 就是标准答案。

脚本做了几层必要的筛选，都不能省：

- **细胞系**：只保留正文里**确实把它当作那个来源的模型在用**的论文。
  只在参考文献里提到名字不算 —— 那不构成错误。
- **引用撤稿**：只保留发表于**撤稿之后**的。撤稿前引用情有可原。
- **回顾性注册**：注册库的 `startDate` 常常只有 YYYY-MM 精度，
  而注册日期是 YYYY-MM-DD。**必须取较粗的精度比较**，否则
  start=2011-02、reg=2011-02-24 会被误判 —— 研究完全可能是 24 号之后才开始的。
  宁可漏报也不能凭猜测给稿件扣帽子。

### 3.2 跑两臂

```bash
caffeinate -i python3 tools/real_paper_benchmark.py --corpus datasets/ground_truth
```

两臂只差一个变量：`withskill/` 下有 `.claude/skills/biomed-paper-review`，
`baseline/` 没有。论文文件、提示词、模型、参数全部相同。

### 3.3 判定

对每篇论文、每一臂各问裁判一次：

> 这份审稿意见有没有指出标准答案里说的那个问题？只回答 HIT 或 MISS。

判定**从严**：

- 只是提到细胞系名字 / 注册号 → MISS
- 说「建议补充细胞系 STR 鉴定」「建议核对注册信息」这类通用建议 → MISS
- 必须触及**具体这一个**对象的身份或事实本身有问题 → HIT

从严的理由：通用建议是裸模型的口水话，几乎每份意见都会写。
放宽就会把它算成命中，uplift 直接被稀释掉。

### 3.4 读结果

```
                              baseline  withskill
cell_line                        MISS      HIT
cited_retracted                  MISS      HIT
retrospective_registration       MISS      HIT
retracted_statistical            HIT       HIT
```

**按类型看，不要只看总分。** 上面这张表说明三件事：前三类有真实 uplift，
第四类裸模型本来就会 —— 那一类的规则应该考虑从 Skill 里删掉。

总分只告诉你「有没有用」，分类型才告诉你「**哪里**有用」。

---

## 4. 六个坑（每个都真实踩过）

### 4.1 调用失败 ≠ 没查出来

**这是最重要的一条。** 审阅调用超时、配额用尽、服务端报错时，输出可能是
一串错误信息或空字符串。若直接拿去判定，裁判会判 MISS ——
于是「我们没问到」被记成了「模型没查出来」。

这与契约里 `parse_failed != not_reported` 是同一条原则，而我们在这个坑里
摔过至少四次：探针把三次超时判成「裸模型查不出来，值得实现」，方向完全反了。

`real_paper_benchmark.py` 的 `review_is_valid()` 检查输出长度与错误标记，
**任何一臂无效就整轮作废退出**，绝不产出数字。

### 4.2 两臂同时 0 命中 = 先怀疑工具

如果两臂都一条没中，几乎肯定是流程有问题（skill 没加载、提示词没送到、
论文没读进去），而不是「这题太难」。先去 `withskill/review.md` 看意见本身。

### 4.3 opencode 忽略 subprocess 的 cwd

必须显式传 `--dir`。否则两臂都在仓库根目录跑，**裸模型那臂也会加载到仓库里的
skill** —— 那就不是基线了。这个 bug 让一整轮结果作废。

### 4.4 超时只杀直接子进程

`subprocess.run(timeout=)` 杀不掉 opencode 派生的孙进程，孙进程继续持有管道，
父进程在 `communicate()` 上永远阻塞。实测设了 40 分钟超时、跑了 77 分钟没被杀。
必须 `Popen(start_new_session=True)` + `killpg`。

### 4.5 超时是死锁上限，不是工作预算

一度把超时收到 900 秒，这是错的：挂 Skill 那臂要跑脚本、查数据库，
正常就是比裸模型慢。用 900 秒会杀掉合法的慢速审阅，**制造出假的负 uplift**。
默认 5400 秒，它只用来兜死锁。

另外：**笔记本合盖睡眠会让经本地代理的连接静默失效** —— socket 仍显示
ESTABLISHED，对端早断了，进程永远等下去。跑长任务加 `caffeinate`。

### 4.6 别用同一个模型既审稿又当裁判就下强结论

裁判和被审是同一个模型时，判定会偏向自己的表述习惯。
差值明显时不影响方向性结论；差一两条时不要当真。
条件允许就换一个模型做裁判。

---

## 5. 拿到结果之后怎么用

uplift 为正，这条能力值得留；为零或负，说明**裸模型本来就会**，
留在 skill 里只会多花 token 拉低分数。

加新检查之前，先用单项探针问一句：

```bash
python3 tools/baseline_probe.py --case <把问题藏进整篇论文里> --error "<标准答案>"
```

四种判定：`BASELINE_FINDS_IT`（别做）/ `BASELINE_MISSES_IT`（值得做）/
`BASELINE_UNRELIABLE`（时对时错，做了能提稳定性）/ `INCONCLUSIVE`（调用失败，重跑）。

**探针必须把问题藏进整篇论文里**，不能直接给一条孤立的错误笔记问模型对不对 ——
那是两种完全不同的难度。

---

## 6. 最小复现流程

```bash
# 0. 确认模型通
set -a && source ~/.config/qwen/credentials.env && set +a
opencode run --model dashscope/qwen3.8-max "回答 ok"

# 1. 建真实语料（四类错误，每类两篇）
python3 tools/fetch_ground_truth_papers.py --per-kind 2

# 2. 跑两臂
caffeinate -i python3 tools/real_paper_benchmark.py --corpus datasets/ground_truth

# 3. 人工核对：两份意见确实是意见，不是错误串
head -40 "$CLAUDE_JOB_DIR"/tmp/rpb/PMC*/withskill/review.md
```

---

## 7. 自己动手：不用我们的脚本，从零做一次

下面用最容易上手的 `cell_line` 类举例。其余三类同理，只是出题人换成
Europe PMC（撤稿状态）、ClinicalTrials.gov（注册日期）或撤稿声明。

### 第 1 步：挑一个已知问题细胞系

去 <https://www.cellosaurus.org> 搜任意细胞系，看有没有 `Problematic cell line`
注释。带 `Contaminated` 或 `Misidentified` 的最好用。或直接查接口：

```bash
curl -s 'https://api.cellosaurus.org/cell-line/CVCL_0417?format=json' |
  python3 -c "import sys,json;
cl=json.load(sys.stdin)['Cellosaurus']['cell-line-list'][0]
print([c['value'] for c in cl['comment-list'] if 'Problematic' in c['category']])"
```

把这条注释原样记下来 —— **它就是你的标准答案**。

### 第 2 步：找用了它的真实论文

```bash
curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22MDA-MB-435%22%20AND%20%22breast%20cancer%22%20AND%20OPEN_ACCESS:y%20AND%20HAS_FT:y&format=json&pageSize=5&resultType=core' |
  python3 -c "import sys,json;
d=json.load(sys.stdin);print('总数',d['hitCount'])
[print(r['pmcid'], r['title'][:60]) for r in d['resultList']['result']]"

curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12572395/fullTextXML' > fulltext.xml
```

**验一下**：正文里确实把它当作乳腺癌模型在用，不是只在参考文献里提了一句。

### 第 3 步：搭两个只差一个变量的目录

```bash
mkdir -p ab/baseline ab/withskill/.claude/skills
cp fulltext.xml ab/baseline/
cp fulltext.xml ab/withskill/
cp -r skills/biomed-paper-review ab/withskill/.claude/skills/
```

除了 `.claude/skills`，两个目录必须**完全一样**。

### 第 4 步：两臂各跑一次

```bash
P="你是资深同行评审。请审阅当前目录下的论文（fulltext.xml），列出所有问题，按严重程度排序。对每一条说明：问题是什么、依据在哪、为什么重要。"

opencode run --dir ab/baseline  --model dashscope/qwen3.8-max "$P" > baseline.md
opencode run --dir ab/withskill --model dashscope/qwen3.8-max "$P" > withskill.md
```

`--dir` 不能省 —— 见 §4.3。

### 第 5 步：先验货，再算数

```bash
wc -c baseline.md withskill.md      # 太短就是没跑起来
grep -il "error\|usage limit\|0 matches" baseline.md withskill.md
```

**只要有一份无效，整轮作废重跑**，不要凑合着判 —— 见 §4.1。

### 第 6 步：逐条判定

对两份意见各问一次：

```
标准答案：论文使用 MDA-MB-435 作为乳腺癌模型，但 Cellosaurus（CVCL_0417）
标注该细胞系为 M14 黑色素瘤衍生系，研究对象前提不成立。

审稿意见：<粘贴>

这份意见有没有实质性指出该细胞系的身份问题？只是提到名字或泛泛建议做 STR
鉴定都不算。只回答 HIT 或 MISS。
```

### 第 7 步：换一类错误再来一遍

**这一步不能省。** 一类错误只能告诉你那一条检查通不通。
至少覆盖三四类不同的错误，才能看出增益到底在哪几处。

---

## 8. 一句话总结

**用真实论文，让权威来源当出题人，按错误类型铺开。**
错误必须长在论文自己的血肉里 —— 只要是植入的，模型挑的就是外来物而不是在审稿，
测出来的差值不作数；而只测一类错误，得到的只是一条检查的通过率，不是 uplift。
