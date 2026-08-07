#!/usr/bin/env python3
"""跨文件一致性审计：确保整套 Skill **闭环**。

与 `validate_schemas.py` 的分工
------------------------------
- `validate_schemas.py` 查的是**契约与实例**：schema 是否自洽、样例是否合法、
  工具产出是否合契约。它看的是 JSON。
- 本脚本查的是**文档之间是否对得上**：SKILL.md 说的模块、阶段、脚本、
  category slug、signal 类型，在各模块 reference 与 schema 里是不是都存在，
  反过来各模块声明的东西是不是都被主框架承认。它看的是 Markdown 与代码的交叉引用。

一个东西「只在一处出现」就是没闭环 —— 要么是主框架承诺了但没人实现，
要么是模块实现了但主框架不知道。两种都会让运行时找不到东西。

用法
----
    python3 tools/consistency_audit.py
    python3 tools/consistency_audit.py --verbose
"""

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "biomed-paper-review")
REFS = os.path.join(SKILL, "references")
SCHEMAS = os.path.join(SKILL, "schemas")
SCRIPTS = os.path.join(SKILL, "scripts")

MODULES = ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]
REF_OF = {
    "M1": "01-structured-extraction.md", "M2": "02-macro-logic.md",
    "M3": "03-experimental-methods.md", "M4": "04-statistics.md",
    "M5": "05-figures-and-charts.md", "M6": "06-ethics-compliance.md",
    "M7": "07-conclusions-discussion.md",
}


class Report:
    def __init__(self, verbose=False):
        self.fail = 0
        self.total = 0
        self.verbose = verbose

    def section(self, t):
        print(f"\n=== {t} ===")

    def check(self, ok, label, detail=""):
        self.total += 1
        if ok:
            print(f"  \033[32mPASS\033[0m {label}")
        else:
            self.fail += 1
            print(f"  \033[31mFAIL\033[0m {label}")
            if detail:
                for line in str(detail).split("\n")[:6]:
                    print(f"       {line}")

    def note(self, label, detail=""):
        """不算失败，但需要人看一眼的观察。"""
        print(f"  \033[33mNOTE\033[0m {label}")
        if detail and self.verbose:
            for line in str(detail).split("\n")[:8]:
                print(f"       {line}")


def read(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def slugs_in(text):
    """抓表格首列里的 `slug`（各模块声明 category 的固定写法）。"""
    return set(re.findall(r"^\|\s*`([a-z][a-z0-9_]+)`", text, re.M))


# ---------------------------------------------------------------- 检查项
def check_reference_links(rep):
    """SKILL.md 引用的 reference 是否都存在；存在的是否都被引用。"""
    rep.section("SKILL.md ↔ references 双向闭环")
    skill = read(os.path.join(SKILL, "SKILL.md"))
    cited = set(re.findall(r"references/([0-9]{2}-[a-z-]+\.md)", skill))
    actual = {os.path.basename(p) for p in glob.glob(os.path.join(REFS, "*.md"))}

    rep.check(not (cited - actual), "SKILL.md 引用的 reference 都存在",
              f"缺失: {sorted(cited - actual)}")
    rep.check(not (actual - cited), "存在的 reference 都被 SKILL.md 引用",
              f"无人引用（运行时不会读到）: {sorted(actual - cited)}")


def check_script_links(rep):
    """SKILL.md 列出的脚本是否都存在；存在的是否都被列出且可运行。"""
    rep.section("SKILL.md ↔ scripts 双向闭环")
    skill = read(os.path.join(SKILL, "SKILL.md"))
    cited = set(re.findall(r"scripts/([a-z_]+\.py)", skill))
    actual = {os.path.basename(p) for p in glob.glob(os.path.join(SCRIPTS, "*.py"))}

    rep.check(not (cited - actual), "SKILL.md 提到的脚本都存在",
              f"缺失: {sorted(cited - actual)}")
    rep.check(not (actual - cited), "存在的脚本都被 SKILL.md 提到",
              f"未被提及（模型不会知道要跑）: {sorted(actual - cited)}")

    # 每个脚本都该有 --selftest —— 否则改坏了没人知道
    no_selftest = [os.path.basename(p) for p in glob.glob(os.path.join(SCRIPTS, "*.py"))
                   if "--selftest" not in read(p) and "selftest" not in read(p)]
    rep.check(not no_selftest, "每个脚本都有 --selftest", f"缺: {no_selftest}")


def check_module_refs(rep):
    """七个模块是否都有对应的 reference 文件，且文件里认领了自己的编号。"""
    rep.section("模块 ↔ reference 归属闭环")
    missing, unclaimed = [], []
    for m, fn in REF_OF.items():
        p = os.path.join(REFS, fn)
        if not os.path.isfile(p):
            missing.append(f"{m} -> {fn}")
            continue
        head = read(p)[:600]
        if m not in head:
            unclaimed.append(f"{fn} 开头未声明自己是 {m}")
    rep.check(not missing, "每个模块都有 reference 文件", "; ".join(missing))
    rep.check(not unclaimed, "每个 reference 开头声明了自己的模块编号",
              "; ".join(unclaimed))


def check_signal_types(rep):
    """契约枚举里的 signal 类型，是否都有生产者（工具或某个阶段）。"""
    rep.section("signal 类型 ↔ 生产者闭环")
    sp = os.path.join(SCHEMAS, "extraction_signal.schema.json")
    try:
        enum = set(json.load(open(sp, encoding="utf-8"))
                   ["properties"]["type"]["enum"])
    except Exception as exc:                                     # noqa: BLE001
        rep.check(False, "extraction_signal.schema.json 可读", str(exc))
        return

    corpus = "\n".join(read(p) for p in
                       glob.glob(os.path.join(SCRIPTS, "*.py")) +
                       glob.glob(os.path.join(REFS, "*.md")) +
                       [os.path.join(SKILL, "SKILL.md")])
    orphan = sorted(t for t in enum if corpus.count(t) < 2)
    rep.check(not orphan, "每个 signal 类型都在脚本或文档里被实际使用",
              f"只出现一次（疑似没有生产者或没有消费者）: {orphan}")


def check_x1_routing(rep):
    """X1 把 signal 路由给某模块时，该模块的 reference 必须知道怎么处理。

    这是最容易漏的一类断链：新加了外部核验、signal 有了去处，
    但接收模块的规则库里根本没有对应条目 —— 运行时模型拿到 signal 不知道怎么办。
    """
    rep.section("X1 外部核验 ↔ 接收模块闭环")
    x1 = read(os.path.join(SCRIPTS, "external_figure_validation.py"))
    if not x1:
        rep.check(False, "external_figure_validation.py 存在")
        return

    # 从 make_signal 调用里抓 routed_to 与 check_type
    routed = {}
    for m in re.finditer(r'\[((?:"M\d",?\s*)+)\],\s*"[a-z_]+",\s*"[a-z_]+",\s*'
                         r'"([a-z0-9_]+)"', x1):
        mods = re.findall(r"M\d", m.group(1))
        for mod in mods:
            routed.setdefault(mod, set()).add(m.group(2))

    rep.check(bool(routed), "能从 X1 解析出路由目标",
              "解析不到 routed_to —— 检查 make_signal 调用格式")
    if not routed:
        return

    # **逐 check_type 核对，不能只看模块有没有提过「外部核验」。**
    # 上一版就是只查模块是否提及外部核验，结果 M2/M4/M6 明明一条 check_type
    # 都没登记却通过了 —— 运行时模型拿到 signal 依然无处安放。
    blind = []
    for mod, checks in sorted(routed.items()):
        fn = REF_OF.get(mod)
        if not fn:
            continue
        txt = read(os.path.join(REFS, fn))
        listed = {c for c in checks if f"`{c}`" in txt}
        # 允许用通配或斜杠合并的写法登记一组同族 check
        for group in ("gene_symbol_", "variant_", "compound_", "trial_"):
            if f"`{group}*`" in txt:
                listed |= {c for c in checks if c.startswith(group)}
        for c in checks:
            if c in listed:
                continue
            if re.search(rf"`{re.escape(c)}`\s*/", txt) or \
               re.search(rf"/\s*`{re.escape(c)}`", txt):
                listed.add(c)
        missing = sorted(checks - listed)
        if missing:
            blind.append(f"{mod}（{fn}）收 {len(checks)} 类外部 signal，"
                         f"其中 {len(missing)} 类未登记消费判据：{missing[:4]}")
    rep.check(not blind, "每个路由到模块的 check_type 都登记了消费判据",
              "\n".join(blind))


def check_severity_declared(rep):
    """各模块声明 category slug 时是否都给了 severity。"""
    rep.section("category slug ↔ severity 闭环")
    bad = []
    for m, fn in REF_OF.items():
        if m == "M1":
            continue                       # M1 不产 finding，本就没有 severity
        txt = read(os.path.join(REFS, fn))
        s = slugs_in(txt)
        if not s:
            bad.append(f"{fn} 未以表格形式声明任何 category slug")
            continue
        if not re.search(r"critical|major|minor", txt):
            bad.append(f"{fn} 声明了 {len(s)} 个 slug 但通篇没有 severity")
    rep.check(not bad, "每个产 finding 的模块都声明了 slug 与 severity",
              "; ".join(bad))


def check_slug_uniqueness(rep):
    """同一个 category slug 不应在两个模块里各自定义 —— 那会导致归属歧义。

    要排除两类**不是冲突**的情况，否则会把正常引用报成冲突：
    1. **signal 类型**（`partial_extraction`、`source_value_conflict` 等）——
       它们由契约定义，多个模块引用是应该的，不是各自定义。
    2. **M1 的字段名** —— M1 不产 finding，它表格里的是抽取字段，
       与下游模块的 category 同名不构成冲突。
    """
    rep.section("category slug 跨模块唯一性")
    try:
        signal_types = set(json.load(open(
            os.path.join(SCHEMAS, "extraction_signal.schema.json"),
            encoding="utf-8"))["properties"]["type"]["enum"])
    except Exception:                                            # noqa: BLE001
        signal_types = set()

    # 契约里的 status / 三维度枚举值也常被当作表格行标签使用
    # （M3 与 M6 都有「| `not_reported` | …」这样的行），那不是 category 定义。
    reserved = set(signal_types)
    for fn in ("common.schema.json", "structured_result.schema.json"):
        try:
            blob = json.load(open(os.path.join(SCHEMAS, fn), encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            continue

        def walk(o):
            if isinstance(o, dict):
                if isinstance(o.get("enum"), list):
                    reserved.update(x for x in o["enum"] if isinstance(x, str))
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(blob)

    # X1 的 check_type 是**共享词汇**：同一个检查本来就可能路由给多个模块
    # （compound_name_valid 同时给 M3 与 M5）。各模块的接收表首列写的是 check_type
    # 而非自己的 category slug，不构成定义冲突。
    x1 = read(os.path.join(SCRIPTS, "external_figure_validation.py"))
    reserved.update(re.findall(r'"[a-z_]+",\s*"[a-z_]+",\s*"([a-z0-9_]+)"', x1))

    owner, dup = {}, []
    for m, fn in REF_OF.items():
        if m == "M1":
            continue                       # M1 表格里是字段名，不是 category
        for s in slugs_in(read(os.path.join(REFS, fn))) - reserved:
            if s in owner and owner[s] != m:
                dup.append(f"{s}：{owner[s]} 与 {m} 都定义了")
            else:
                owner.setdefault(s, m)
    rep.check(not dup, "没有 category slug 被两个模块同时定义", "\n".join(dup[:8]))
    print(f"       （共 {len(owner)} 个 category slug，"
          f"分属 {len(set(owner.values()))} 个模块；"
          f"已排除 {len(reserved)} 个契约保留值与 M1 字段名）")


def check_open_todos(rep):
    """列出各模块未勾选的 TODO，并标出**互相依赖**的那些。

    互相依赖的 TODO 是最典型的没闭环：两边都在等对方。
    """
    rep.section("未完成 TODO（互相依赖的会被标出）")
    todos = {}
    for m, fn in REF_OF.items():
        items = re.findall(r"^- \[ \] (.+)$", read(os.path.join(REFS, fn)), re.M)
        if items:
            todos[m] = items
    if not todos:
        rep.check(True, "无未完成 TODO")
        return

    cross = []
    for m, items in sorted(todos.items()):
        for it in items:
            other = re.findall(r"\bM[2-7]\b", it)
            other = [o for o in other if o != m]
            if other:
                cross.append(f"{m} 等 {'/'.join(other)}：{it[:60]}")
    for m, items in sorted(todos.items()):
        print(f"  {m}（{len(items)} 条）")
        for it in items:
            print(f"       - {it[:78]}")
    if cross:
        rep.note(f"其中 {len(cross)} 条是跨模块互等，需要双方同时动", "\n".join(cross))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    rep = Report(a.verbose)
    print("跨文件一致性审计（闭环检查）")
    for fn in (check_reference_links, check_script_links, check_module_refs,
               check_signal_types, check_x1_routing, check_severity_declared,
               check_slug_uniqueness, check_open_todos):
        fn(rep)

    print("\n" + "=" * 60)
    if rep.fail:
        print(f"\033[31m{rep.fail} 项未闭环\033[0m（共 {rep.total} 项检查）")
        return 1
    print(f"\033[32m全部闭环\033[0m（共 {rep.total} 项检查）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
