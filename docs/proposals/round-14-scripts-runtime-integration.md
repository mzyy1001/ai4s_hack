# Round 14 · 脚本运行时集成与跨模型健壮性 提案

## 摘要

五个确定性工具已全部位于 Skill 的 `scripts/` 内，Round 6 的迁移项已实现；本轮补齐可从任意工作目录调用的 JSON CLI、具体示例和受控错误出口。
统计脚本已产出的 `table_total_mismatch` 此前会被 `forensics.check` schema 拒收，而现有校验器仍误报通过；本轮已同步 schema 并新增深一层门禁。
文档未发现依赖 GPT、Claude 或厂商专属 tool-call 语义的运行指令；下一步不应再扩平行 runner，而应做包级运行时合约测试，并新增 qPCR / dPCR 两个确定性分子定量取证器。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §6.5 | 以运行时解析的 `BIOMED_REVIEW_SKILL_DIR` 调用五个脚本，不再要求切换工作目录；补单位、统计、伦理、序列、图像五组具体 CLI 示例、退出码规则与伦理必跑触发条件 | 原 `python -c + sys.path.insert` 不是稳定文件接口，且遗漏了伦理工具的运行触发；切换 cwd 会改变稿件相对路径含义 |
| `scripts/normalize_biomed_units.py` | CLI、`compare_units()`、自检 | 增加 `--normalize` / `--compare` JSON CLI；0、负数、非数值与无穷分子量 fail closed，不再除零或产生无穷换算 | 分子量是跨质量/摩尔浓度换算的必要前提，非法值不得导致 traceback 或伪换算 |
| `scripts/statistical_forensics.py` | CLI、`check_all()`、自检 | 增加 `--input FILE|-`；拒绝非数组、非对象、未知 check 与非法参数，stderr 返回结构化 `invalid_input`、退出码 2 | 旧脚本除 `--selftest` 外没有机器 CLI，字符串 n / 非对象元素会直接抛 traceback，模型无法区分“无 signal”与“工具失败” |
| `scripts/ethics_compliance_check.py` | CLI、`derive_facts()`、`screen()`、自检 | 增加 `--input` / `--rulebase`；默认规范库继续按 `__file__` 自定位；校验 structured result、设计对象与 rule 数组 | 旧脚本只能 import 调用，顶层或嵌套输入形状错误会崩溃；同时必须证明复制 Skill 目录后仍能定位 `resources/` |
| `scripts/sequence_identifier_audit.py` | CLI、文本输入、`audit()`、自检 | 增加 `--input FILE|-`；拒绝非对象项和未知 check；标量安全转文本；`_sig()` 不再修改调用方传入 dict | 旧脚本对数值/容器字段调用 `.strip()`，且批次中的坏项会产生未解释 traceback |
| `scripts/figure_integrity_audit.py` | CLI、目录扫描、图像载入 | 增加 `--input DIR` 与完整 JSON 输出；不存在目录返回结构化错误；同 basename 不再静默覆盖，改为 `parse_failed` limitation；保留旧位置参数兼容 | 旧 CLI 只打印计数摘要，无法把 signal 合并进报告；同名图静默覆盖会造成错误配对与证据丢失 |
| `references/00-contracts.md`、`04-statistics.md`、`06-ethics-compliance.md`、`resources/ethics_rules.json`、`schemas/extraction_signal.schema.json` | 运行时路径说明 | 把仓库相对 `skills/biomed-paper-review/scripts/...` 收敛为 Skill 根目录相对 `scripts/...` | Skill 安装位置可变，运行时文档不得假设仓库布局 |
| `schemas/extraction_signal.schema.json` | `forensics.check` | 增加已实现的 `table_total_mismatch` | 脚本产物此前满足顶层 type，却会被类型专属枚举拒收 |
| `tools/validate_schemas.py` | schema 层、工具 signal 层 | 强制 `forensics.check` 恰好覆盖五种已实现统计取证，并检查真实工具产物的内层 check | 原 151 项检查只验证存在 `forensics` 块，没有验证块内枚举，形成假绿灯；本轮是收紧而非放宽校验 |

## B 类提案

### P1 · 包级 runtime conformance harness：验证“换目录、坏输入、缺依赖”仍守契约

- **问题**：本轮给五个脚本补了逐工具 CLI，但仓库还没有黑盒测试证明压缩包解开到任意路径后仍可执行。Round 7 P1 已提出统一 `run_deterministic_checks.py`，Round 13 P2 已提出适用项账本；本项不重复 runner 或 coverage，而是验证所有现有/未来入口的安装位置独立性与失败语义。
- **影响**：GLM / Kimi 是否愿意构造 `python -c`、是否保留当前 cwd、是否把 stderr 当结果，各模型行为不同；若 CLI 合约不由黑盒测试固定，换模型后最常见的退化是脚本根本没跑、错误被当空结果，直接损失工程质量与 uplift。
- **方案**：新增开发期 `tools/test_skill_runtime.py` 和包内 `resources/runtime_interfaces.json`。manifest 每项固定 `{tool_id,script,operations[],input_media_type,stdout_schema,exit_codes,optional_dependencies[]}`；测试器只消费解包后的 Skill 目录，逐项从临时 cwd、含空格/中文的安装路径、只读 cwd、`LANG=C` 运行。每个入口至少覆盖：合法 stdin、合法文件、空文件、坏 JSON、顶层类型错误、未知操作、缺文件、同名图、可选依赖缺失。门禁要求 stdout/stderr 可解析、退出码属于 manifest、无 traceback、无 Skill 目录写入、伦理规则库仍从 `__file__` 解析。它只测试现有脚本，不再新建第二套执行器；Round 7 runner 落地后同样注册到 manifest。
- **代价**：1–1.5 人日；标准库 `subprocess/tempfile/json` 足够。依赖缺失路径可用隔离解释器或 import hook 测试，不修改官方镜像。
- **建议优先级**：P0 交付前必须做；至少覆盖五个现有 CLI 的 25 个黑盒 case。
- **阶段 / 归属**：**一期离线**；工程门禁，不属于 M1–M7，不进入审稿报告。
- **契约字段**：不改生产三类记录；新增运行资源 manifest 与测试 artifact `{tool_id,case_id,cwd_mode,exit_code,stdout_valid,stderr_valid,writes_detected}`。若 Round 7 `tool_runs[]` 后续落地，复用其 tool id，不另造报告字段。
- **假阳性**：不判断稿件。最大风险是测试器把平台缺失可选依赖当失败；manifest 必须区分 `required` 与 `optional`，后者只有未产合法 `system_limitation` 才失败。

### P2 · RT-qPCR 量化算术取证器：从 Cq 链重算 ΔCq、ΔΔCq 与 fold change

- **问题**：当前序列工具能检查引物字母表与粗略 QC，统计工具能核对 p / CI，却无法发现 qPCR 表中常见的内部算术断裂：目标与参考基因 Cq 对不上 ΔCq、calibrator 对不上 ΔΔCq、图中 fold change 不等于稿件声明的量化公式。`2^-ΔΔCq` 还隐含目标与参考扩增效率处理方式；效率不明时不能把公式差异写成确定性错误。MIQE 2.0 要求报告所用定量方法、效率校正、检测限与动态范围；效率与目标量换算的边界见 [MIQE 2.0](https://academic.oup.com/clinchem/article/71/6/634/8119148) 和 [Cq 使用与误用方法论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC8229287/)。
- **影响**：qPCR 是生物医学机制论文的高频证据链；小数点、符号方向、calibrator 或 reference gene 抄错可使表达倍数完全翻转。裸模型通常只会提示“报告引物和内参”，不会逐样本重算，这是一项直接 uplift。
- **方案**：新增 `scripts/qpcr_quantification_audit.py`。M1 抽取 `qpcr_quantifications[]`，每项固定 `{assay_id,experiment_id,target_gene,reference_genes[],quantification_method,calibrator_ref,efficiency_basis,observations[],evidence_refs[]}`；observation 保存 `{sample_ref,target_cq[],reference_cq_by_gene,reported_delta_cq,reported_delta_delta_cq,reported_relative_quantity,technical_replicate_policy,evidence_refs[]}`。工具按稿件明确声明的方法执行：
  1. `delta_delta_cq`：按稿件给出的 replicate 汇总和 reference 聚合规则重算 `ΔCq=Cq_target−Cq_reference`、`ΔΔCq=ΔCq_sample−ΔCq_calibrator`；只有稿件明确采用 100%/等效率模型时才核对 `2^-ΔΔCq`。
  2. `efficiency_corrected`：只在 target/reference 的效率定义与数值均报告时按稿件公式重算；不替作者选择 Pfaffl、单点校准或其他方法。
  3. `standard_curve`：只核对稿件已给 slope、intercept、稀释倍数与 reported quantity 的代数；是否达到可接受效率、R²、LOD/LOQ 由 M3 结合 MIQE 判断，不由算术器定罪。
  4. undetermined Cq、超出动态范围、技术重复被排除但理由不明、多个 reference gene 聚合规则缺失时输出 `partial_extraction`；不得把 undetermined 当 40，也不得先在线性 fold-change 上做 t 检验建议。
  工具只产 `qpcr_quantification_candidate` signal；M3 核对 assay/效率/参考基因方法，M4 核对汇总与推断，M7 仅消费已确认且影响核心 claim 的 finding。
- **代价**：2–3 人日；1 人日 schema/脚本，1 人日 20 个正反例（符号反转、多内参、效率不等、undetermined、calibrator 错位），0.5–1 人日 M3/M4 消费规则。无需网络、GPU 或原始荧光曲线。
- **建议优先级**：P1 应该做；先交 `ΔCq/ΔΔCq/2^-ΔΔCq` 纯算术，效率校正与 standard curve 为第二批。
- **阶段 / 归属**：**一期离线**；M1 抽取，Stage 2 工具产 signal，M3/M4 判 finding，M7 只评估结论依赖。不新增审核模块。
- **契约字段**：扩展 `structured_result` 的 `qpcr_quantifications[]`；`extraction_signal.type` 增 `qpcr_quantification_candidate`，条件必填 `qpcr_audit:{check,method,inputs,recomputed_value,reported_interval,formula_version,assumptions[]}`。这是现有 signal 扩展，不重构 finding 或 evidence。
- **假阳性**：中高。Cq/Ct/Cp 命名、baseline/threshold、技术重复汇总、多个 reference gene 的几何聚合、效率表示为 0.95 或 1.95、calibrator 定义均可能不同。公式或任一绑定不明确时只给 `partial_extraction`；只有同 assay、同 sample、同 calibrator、同方法下的代数矛盾才生成候选，仍不自动给 severity。

### P3 · dPCR/ddPCR 分区—Poisson—浓度闭合审计器

- **问题**：数字 PCR 报告常同时给正/负/总分区数、阳性比例、`λ`、copies/partition、copies/µL 与稀释倍数；这些量可在严格前提下确定性闭合。阳性分区不能直接当分子数，因为一个阳性分区可含多个模板；标准估计依赖空分区概率和 Poisson 模型。dMIQE 2020 明确要求分区数、分区体积和 `λ` 等信息；方法依据见 [dMIQE 2020](https://academic.oup.com/clinchem/article/66/8/1012/5880117) 与 [digital PCR Poisson 建模论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4373789/)。
- **影响**：把 positive droplets 直接除体积、混用 generated/accepted partitions、漏乘稀释倍数或把 copies/reaction 写成 copies/µL，会造成可达数量级的错误；通用模型不会稳定逐孔重算，也难识别饱和孔无上界信息。
- **方案**：新增 `scripts/dpcr_partition_audit.py`。M1 抽取 `dpcr_quantifications[]:{assay_id,platform,partition_type,partition_volume,generated_partitions,accepted_partitions,positive_partitions,negative_partitions,rain_policy,dilution_factor,reported_lambda,reported_concentration,concentration_unit,well_or_replicate_id,evidence_refs[]}`。工具执行：
  1. 先核对 `positive + negative = accepted`；generated 只作质控分母，不得混入浓度公式。
  2. 仅在分区独立、等体积模型与阈值分类已由稿件声明时重算 `λ=-ln(negative/accepted)`；`negative=0` 为饱和，只给下界/不可有限估计，不输出点值。
  3. 只有 partition volume、有效反应体积、稀释/预扩增因子和单位全部明确时才换算 copies/µL；油滴体积、dead volume 或平台软件校正不明时停在 copies/partition。
  4. 区间以正分区二项不确定性变换到 `λ`，不得只用 `sqrt(count)`；多孔合并必须区分“先合并分区再估计”与“孔级估计后汇总”。
  输出 `dpcr_quantification_candidate` signal；分区合计/单位硬错交 M4，rain、阈值、LOD、抑制与分子完整性问题交 M3。工具沉默不能证明 assay 有效。
- **代价**：2.5–3.5 人日；1 人日 Poisson/区间与单位，1 人日 schema/CLI，0.5–1.5 人日用未饱和、全阴性、全阳性、rain、不同 droplet volume、多孔合并与预扩增构造 20–25 个 fixture。
- **建议优先级**：P1 应该做；先交分区闭合 + `λ` + 饱和门控，浓度与多孔区间为第二批。
- **阶段 / 归属**：**一期离线**；M1 抽取，Stage 2 工具产 signal，M3/M4 消费。不新增模块；若原始 droplet amplitude 文件可得，阈值重判与 cluster 分类留二期。
- **契约字段**：扩展 `structured_result.dpcr_quantifications[]`；新增 signal type 与 `dpcr_audit:{check,partition_counts,occupancy_model,recomputed_lambda,recomputed_interval,volume_context,unit_conversion,formula_version}`。三类记录不变。
- **假阳性**：高。非均一分区体积、linked targets、molecular dropout、restriction digest、pre-amplification、rain 分类与平台私有体积校正都会改变结果。只有论文自报字段在同一 well/replicate 内的计数闭合或按其声明模型复算不相容时产候选；其余降级为 `partial_extraction` 或人工，不得写“定量错误已确认”。

## 未解决 / 需要人来定的问题

1. Round 7 P1 的统一 `run_deterministic_checks.py` 仍未落地；本轮只让五个工具各自可可靠调用，没有重复实现第二套 runner。交付前若不采纳该项，模型仍需逐工具枚举适用输入，可能漏跑，但不得声称已有统一编排。
2. Round 12 已采纳 X1 核心契约，connector 仍为零；Round 13 P4 已要求先做 ClinicalTrials.gov 单一垂直切片，本轮不重复数据库清单。
3. `SKILL.md` 当前 606 行，仍高于“建议 <500 行”；Round 13 P1 已提出用组件消融决定热路径，本轮没有为过静态行数机械删除安全边界。交付前至少应把公式和重复释义下沉到现有一层 reference，且用消融证明不降低执行正确率。
4. M2/M3 的 ready 状态、M5 Parser/Reviewer 冲突与 M7 两波屏障分别已有 Round 7、Round 5、Round 2 提案，且涉及禁改文件；本轮未触碰，也不应把它们计入“脚本运行时已闭合”。
5. Skill 包内仍有 `.DS_Store`，Round 7 已登记；当前允许修改清单未包含该文件。本轮未删除，提交打包必须使用显式白名单排除。
6. 是否接受 P2/P3 共用一个 `molecular_quantification` 子对象而不是各自顶层数组需要 M1/M3/M4 拍板。建议共享 `{assay_id,experiment_id,evidence_refs[]}` 基类，但 qPCR 的 Cq 链与 dPCR 的分区模型保持两个条件分支，禁止压成一个自由对象。
