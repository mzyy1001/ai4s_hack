# 审核置信度评分片段

Figure 4 是主要终点的唯一来源。低分辨率图像只能 OCR 和像素估读；OCR 把一个刻度读错，导致同一主要终点的正文值与图值形成一个未消解冲突。系统产生一条依赖该图的低置信度 finding。

评分规则与本例输入：

```text
extraction_coverage = 0.50                 # Figure 4 不可可靠读取已降低覆盖率
pixel_dependency_rate = 1.0
ocr_dependency_rate = 1.0
low_conf_finding_rate = 1.0
Q = 1 - 0.30 - 0.20 - 0.10 = 0.40
unresolved_conflict_count = 1
C = 1 - 0.10 = 0.90
review_confidence = 0.50 × 0.40 × 0.90 = 0.18
```

上述四个折扣都由同一张低质量 Figure 4 触发；没有第二个独立的信息质量缺陷。
