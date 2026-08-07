# Round 22 · 图表管线与 Stage 3/3b 衔接 提案

## 摘要

Stage 3 → Stage 3b 的观测核心字段已能无损回流，但系列、轴、分析集与逐时点样本量仍没有观测级绑定；这是 Round 5 P2 尚未采纳的结构缺口，不应另建平行字段。
像素估读此前允许 `low == high` 的零宽区间，等价于把点值换壳写入，本轮已封禁；任意窄区间仍需 Round 5 P3 的像素标定与误差传播器才能从根本约束。
本轮新增组学坐标图与 Bland–Altman 两个专业候选，但 Qwen 探针均因沙箱出站限制得到 `INCONCLUSIVE`，有效重跑前不得实现。

## A 类已直接修改

| 文件 | 位置 | 改了什么 | 为什么 |
| --- | --- | --- | --- |
| `skills/biomed-paper-review/SKILL.md` | §2.7 | 把像素估读规则收紧为非零宽 `interval`，明确禁止零宽区间伪装点值 | 原规则只禁 `point`，`{"type":"interval","low":1.23,"high":1.23}` 仍能合法注入伪精确读数 |
| `skills/biomed-paper-review/references/00-contracts.md` | §2.4 第 1 条 | 增加 `interval.low < interval.high`，并禁止用单侧边界伪装点值 | 让主契约与执行门禁使用同一可复算条件 |
| `skills/biomed-paper-review/schemas/key_data.schema.json` | `metric_name`、pixel 条件说明 | `metric_name` 增 `minLength: 1`；记录 pixel 非零宽由跨值校验器执行 | 空规范名无法参与 Stage 3b 指标身份分组；Draft 2020-12 不能表达同对象 `low < high` |
| `skills/biomed-paper-review/schemas/figure_record.schema.json` | `experimental_conditions.n_per_group`、`$defs.axis` | `n_per_group` 下界改为 1；对数轴显式范围的每个端点强制为正值 | 旧 schema 接受负样本量和包含 0/负值的 log 轴，二者都会污染图表解读与回流 |
| `tools/validate_schemas.py` | provenance / Figure 路由检查 | 拒绝 pixel 零宽区间、非递增 axis range、含非正端点的 log axis range | 跨字段大小关系无法只靠当前 JSON Schema 表达，必须由契约校验器补门禁 |
| `tools/probe_cases/round22_volcano_coordinate_mismatch.md` | 新文件 | 增加 `log2FC / -log10(FDR)` 点位与显著性分类错配案例 | 为组学坐标图候选提供不泄露裁判结论的裸模型输入 |
| `tools/probe_cases/round22_bland_altman_loa_mismatch.md` | 新文件 | 增加 Bland–Altman limits of agreement 使用 ±1 SD 而非声明的 ±1.96 SD 案例 | 为方法比较图候选提供可复算基线输入 |

## 基线探针结果

| 候选 | 案例 | `qwen3.8-max × 3` | 结论 | 本轮行动 |
| --- | --- | --- | --- | --- |
| 组学坐标图数据—几何闭合 | `round22_volcano_coordinate_mismatch.md` | 0 个有效样本；3 次均为 `urlopen: [Errno 1] Operation not permitted` | `INCONCLUSIVE` | 不实现、不宣称 baseline miss；恢复出站访问后原命令重跑 |
| Bland–Altman 方法比较闭合 | `round22_bland_altman_loa_mismatch.md` | 0 个有效样本；3 次均为同一 socket 拒绝 | `INCONCLUSIVE` | 同上 |

凭据可读取，失败发生在 DashScope 出站连接阶段，不是模型返回错误。恢复网络后运行：

```bash
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round22_volcano_coordinate_mismatch.md \
  --error "Figure 4 的 STAT1 与 CXCL8 点位没有按声明的坐标定义映射：STAT1 的 FDR=0.002 应对应 -log10(FDR)=2.70 而不是 0.70；CXCL8 的 log2FC=+2.00 却被画在 x=-2.00 并错误标成下调。" \
  --repeats 3
python3 tools/baseline_probe.py \
  --case tools/probe_cases/round22_bland_altman_loa_mismatch.md \
  --error "Bland–Altman 95% limits of agreement 算错：bias=-0.20、差值 SD=1.50 时应为 -0.20±1.96×1.50，即约 -3.14 到 2.74 mg/dL；图和正文的 -1.70 到 1.30 实际只用了 ±1 SD。" \
  --repeats 3
```

只有 `BASELINE_UNRELIABLE` / `BASELINE_MISSES_IT` 才允许把对应候选转入实现；
`BASELINE_FINDS_IT` 必须移入“已探针，放弃”。

## B 类提案

以下两项均被基线门禁阻断。技术设计用于有效重跑后快速拍板，不构成当前实现授权。

### P1 · 组学坐标图的源数据—变换—几何闭合审计

- **问题**：`references/05 §A.2` 只要求火山图报告阈值和多重校正，没有核对补充表中的 `log2FC`、`p/q`、基因方向与图中点位。常见硬错包括把 `p` 画成 `-log10(q)`、折叠变化方向翻转、标签绑到另一转录本、阈值线与 Methods 不一致，以及把 capped 点当真实 y 值。Round 5 的通用守恒提案不包含实体—二维坐标—变换三元绑定。
- **影响**：火山图、MA plot 与 Manhattan plot通常承载组学候选筛选；点位或显著性分类错配会把错误基因送入后续机制验证。裸模型不会稳定遍历数千行 source data 并逐点复算变换，但本轮没有有效基线样本，尚不能据此声称 uplift。
- **方案**：**一期离线，Stage 1/3/3b + M4/M5，不新增模块。** 依赖 Round 20 P1 的同稿 source-data 资产图和 Round 5 P2 的 series/axis 绑定，不另建第二套资产或轴字段。Stage 3 新增嵌套 `omics_coordinate_map`：`{plot_kind,x_transform,y_transform,multiplicity_measure,thresholds[],entity_points[]}`；每个点固定带 `{entity_id,source_row_ref,x_reported,y_reported,x_rendered_interval,y_rendered_interval,class_label,series_ref,axis_refs[],evidence_refs[]}`。只在 source row、稳定实体 id、panel、axis 与变换全部唯一绑定时运行。确定性检查限于：`x_reported ↔ rendered x`、`-log10(p/q) ↔ rendered y`、方向颜色、阈值分类和 Methods 阈值一致性；`p=0`、轴上限裁剪、箭头点、重复 gene symbol、isoform 多映射均停止点值比较。Stage 3 产 `omics_plot_consistency_candidate` signal，M4 判断变换/多重校正，M5 判断点位、颜色与图注；Parser 不产 finding。
- **代价**：探针通过后 2–3 人日；source-data/panel 绑定 0.5–1 人日，变换和几何复算 0.5 人日，volcano/MA/Manhattan 的 capped p、重复 symbol、p/q 混用等 15 个困难 fixture 1–1.5 人日。
- **建议优先级**：P0 仅指恢复并重跑基线探针；结果为 `MISSES/UNRELIABLE` 时组件为 P1，结果为 `FINDS_IT` 时放弃默认实现。
- **阶段 / 归属**：一期（不调用外部数据库）；Stage 1 登记同稿数据资产，Stage 3 抽取二维事实，Stage 3b 回流一维 observation 与保留二维绑定，M4/M5 唯一产 finding。
- **契约字段**：扩展 `figure_record.omics_coordinate_map` 和现有 signal 条件块；一维值仍通过 `observations[]` 回流，二维点只保存 refs 与审计轨迹。可增 signal type `omics_plot_consistency_candidate`，不新增第四类记录，不重构 finding。
- **假阳性**：中高。`p` 与 `q`、gene 与 transcript、截顶与真实值、正负方向定义、全数据与展示子集任一不清都可造成表面错配。只在区间不相交且绑定完整时产候选；实体多映射或轴裁剪固定 `needs_manual_review`，不得写“组学结果错误已确认”。

### P2 · Bland–Altman 方法比较图的 limits-of-agreement 闭合审计

- **问题**：方法学论文常同时在正文、表格与 Bland–Altman 图报告 bias、差值 SD、95% limits of agreement（LoA）及其置信区间。当前 `statistical_plot` 只能回流孤立数值，不能表达差值方向、x 轴定义、配对结构和 LoA 公式；把 ±1 SD 误标成 95% LoA、上下界未以 bias 对称、mg/dL 与百分差混用都不会被现有统计脚本发现。
- **影响**：临床检验、影像测量和设备一致性研究会据 LoA 判断两方法能否互换。相关系数高不能替代 agreement；若图中 LoA 算错或定义漂移，稿件核心可替代性结论失去量化依据。
- **方案**：**一期离线，Stage 3/3b + M4/M5，不新增模块。** 在 `figure_record` 增嵌套 `method_comparison_plot:{difference_definition,x_definition,unit,pair_count,repeated_measure_structure,bias,difference_sd,loa_lower,loa_upper,loa_multiplier,loa_ci,transform,evidence_refs[]}`。M1/Parser 只抽论文明确声明的公式与数值；工具仅在同一配对集合、同一单位/变换、独立 pair 或作者声明的重复测量模型可识别时运行。首版确定性检查：按稿件声明的 multiplier 复算 `bias ± multiplier × SD`、检查上下界围绕 bias 的对称性、差值符号与图注一致、正文 LoA 与图上线位置区间相交。重复测量、非参数 quantile LoA、log-ratio/percentage difference 与 heteroscedastic regression 走独立 `not_comparable` 分支，禁止套 1.96 常数。输出 `method_comparison_consistency_candidate` signal；M4 判断统计公式和依赖结构，M5 判断线位/标签，M3 只在另有 assay 设计问题时独立审核。
- **代价**：探针通过后 1.5–2.5 人日；简单 LoA 算术/单位 0.5 人日，schema 与 Stage 3b 绑定 0.5 人日，重复测量、log transform、非参数 LoA、LoA CI 等 12 个困难反例 0.5–1.5 人日。
- **建议优先级**：P0 先恢复探针；`MISSES/UNRELIABLE` 后建议 P1，且只交简单 paired-difference 垂直切片。`FINDS_IT` 则不实现该算术检查。
- **阶段 / 归属**：一期（不调用外部数据库）；Stage 3/3b 产事实与 signal，M4/M5 产 finding。
- **契约字段**：增量扩展 `figure_record.method_comparison_plot` 与 signal 判据块，可增 `method_comparison_consistency_candidate`；所有 bias/SD/LoA 数值仍各自进入 `observations[]`，finding 契约不变。
- **假阳性**：高。重复测量、多中心分层、比例偏倚、非正态差值、ratio scale、robust/quantile LoA、小样本 t multiplier 和 LoA 的 CI 都会改变公式。只有方法声明与数据结构完全可比时产 mismatch candidate；模型结构不清只产 `partial_extraction`，不得自动判方法错误。

## 未解决 / 需要人来定的问题

1. **Figure Parser / M5 的主契约已干净，M5 reference 仍未收敛。** `SKILL.md §2.2/§2.7` 与 `figure_record.schema.json` 明确 Stage 3 不产 finding；但禁改的 `references/05` §A.1 步骤 2–5、§A.5、§D、§F.5 仍要求 Parser 评判并产 `finding[]`、让 M5 产 `figure_record[]`，还把图像候选预设为 `critical`。这是 Round 5 P1 未采纳项，必须由敏怡在交付前修改；本轮未触碰该文件。
2. **`references/05` 还有两个新增的可执行冲突。** §A.3 仍给出已废弃的绝对 canonical 顺序，违反 `00 §5.5` 的“两级来源 + 有序判据”；像素示例仍用 schema 禁止的字符串 `"40–50"`，并要求 Parser 写 `finding.manual_review.action`。负责人应改成 numeric variant 示例并把人工复核动作留给 M5。
3. **回流接口只对 `observation_core` 无损，不对生物学上下文无损。** `figure_record.observations[]` 没有 `series_ref` / `axis_ref` / `analysis_population` / `strata` / 逐时点 n / `error_bar_type`；当前全图级 `experimental_conditions.n_per_group` 与 x/y 轴对象无法证明某个值属于哪条线、哪个 y 轴或哪个分析集。Round 5 P2 已给出统一 migration，未采纳前多系列/双轴/亚组图必须“不合组 + `partial_extraction`”，不能声称完整回流。
4. **像素防编造只补了最低门。** 本轮能拒绝点值和零宽区间，但 `sim2_figure_interpretation_only.json` 的 `0.38–0.46` 仍没有 plot bbox、tick anchors、mark bbox、像素误差或标定残差，任意窄的非零区间依然合法。Round 5 P3 是 P0 前置；未落地前不得把 pixel interval 用于图文冲突 finding，更不得送入 M4 复算。
5. **Stage 3b 仍只有文档与终态 lint，没有执行器。** Round 16 P1 的 `merge_observations.py + comparison_trace[]` 尚未实现；当前 validator 只能发现最终副本丢字段，不能从 v1 + figure records 重算分组、单位工作副本、pair verdict、status 与 canonical。应先实现既有 P0，再新增图型组件。
6. **缺端到端正例。** 四个 fixture 中唯一非空 `figure_records[]` 是 `interpretation_only`，它明确不跑 Stage 3b；因此本轮“无损回流”仍没有一个 `figure_review/full_review` fixture 从 Figure observation 合并到 v2。该项已在 Round 5 P5 / Round 20 #4 提出，不再另建重复提案。
7. **已采纳能力不要重复建设。** Round 1/11 的论文内图像候选器已实现为 `scripts/figure_integrity_audit.py`，Round 20 已补全跨副本字段与拒收轨迹 lint；尚未采纳的是旋转/镜像/缩放稳健匹配、像素坐标血缘和 M5 安全消费门，不能把当前网格 dHash 自检宣传成完整 image forensics。
8. **新组件当前无实现授权。** 两个 Round 22 探针有效样本均为 0；恢复 DashScope 出站访问前，不得把 P1/P2 写进默认热路径、schema 枚举或 README 能力清单。
