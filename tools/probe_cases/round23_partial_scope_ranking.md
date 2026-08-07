# 两份定向核查报告

同一篇稿件分别运行两个 `targeted_check`：

| 报告 | 已执行模块 | 未执行模块 | partial 风险分 |
| --- | --- | --- | ---: |
| A | M6 伦理合规 | M2、M3、M4、M5、M7 | 0 |
| B | M4 统计学 | M2、M3、M5、M6、M7 | 25 |

两份报告均写 `partial=true`、`comparable_to_full_review=false` 和 `band=partial_not_classified`。汇总页面仍按数值从低到高排列，显示“报告 A 风险低于报告 B”，并把 A 的 0 分渲染为绿色。
