# 审核证据包

## 规范化稿件片段

PDF 第 4 页 Results，第 2 段： “No serious adverse events were observed during the 48-hour follow-up.”

PDF 第 4 页 Discussion，第 3 段： “No serious adverse events were observed during the 48-hour follow-up.”

PDF 第 7 页 Methods，第 1 段： “The primary endpoint was assessed at day 28.”

## evidence_registry 摘要

- `EV-101`：type=`present`；locator 只有 `pdf_file_page=4, scope=paragraph`，没有 section、paragraph_id、figure/table；quote 为 “No serious adverse events were observed during the 48-hour follow-up.”
- `EV-102`：type=`present`；locator 为 `pdf_file_page=6, section=methods, scope=paragraph`；quote 为 “The primary endpoint was assessed at day 28.”

## 报告使用方式

finding `M7-004` 仅引用 `EV-101`；finding `M4-002` 仅引用 `EV-102`。系统确认两个 ref 均存在，因此准备把两条 finding 标为“证据可快速定位”。

请审阅这份证据包，指出会妨碍审稿人回到唯一原文位置的具体问题。
