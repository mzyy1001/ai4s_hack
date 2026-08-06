#!/usr/bin/env python3
"""论文内图像完整性审计（一期能力，本地计算，不联网）。

检测**论文自身图像之间**的可疑重复与拼接痕迹。这是生物医学论文最高发的
学术不端形态，也是通用大模型**完全做不到**的一类检查 —— 它需要像素级计算。

三类检查
--------
1. `duplicated_region_candidate` —— 跨图或同图远距离的重复区域
2. `splice_discontinuity_candidate` —— 印迹图背景的垂直不连续（拼接痕迹）
3. `uniform_patch_candidate` —— 异常均匀区块（涂抹/克隆的痕迹）

**最重要的设计约束：绝不自动下「造假」结论。**
本模块的全部输出都是 `candidate`，`severity_hint` 恒为 `null`，
路由到 M5 并**强制**人工复核。图像重复有大量正当解释：
同一对照组图片在多图复用、模板化示意图、放大插图、拼接展示。
把这类判断自动化为指控是本项目风险最高的动作，因此契约层面禁止。

防误报设计
----------
- **方差门控**：空白/背景区块（局部方差过低）一律跳过 ——
  否则每张图的白底都会互相匹配，产出海量垃圾。
- **两阶段判定**：先用完全相同的 dHash 分桶，再用实际像素的 Pearson 相关精确验证，
  只有 r ≥ 0.98 才算候选。
- **同图近邻排除**：同一张图内距离过近的区块不算重复（那是纹理连续性）。
- **依赖缺失不崩**：numpy/PIL 不可用时产出 `system_limitation`，不是报错。

已知局限（必须如实告知，不得让读者以为这是完备的取证）
--------------------------------------------------------
- **只检出相对位移为 `STRIDE` 整数倍的重复。** 本方法按固定网格切块并用
  精确 dHash 分桶，因此任意偏移的复制粘贴可能漏检。要做到偏移无关，
  需要 ORB/SIFT 之类的关键点匹配，属后续工作。
- **不检出经旋转、缩放、镜像后的重复**，同样需要关键点匹配。
- **漏检不等于清白**：本模块沉默只说明这三类模式没命中，
  不构成「图像无问题」的结论。报告中必须这样表述。

命令行：
    python3 figure_integrity_audit.py --selftest
    python3 figure_integrity_audit.py <图像目录>       # 对真实语料跑一遍
"""

import os
import sys

RULE_VERSION = "2026-08-07"

try:
    import numpy as np
    from PIL import Image
    DEPS_OK = True
    DEPS_ERR = None
except Exception as exc:                                    # pragma: no cover
    DEPS_OK = False
    DEPS_ERR = str(exc)

# ---------------------------------------------------------------- 参数
BLOCK = 64          # 区块边长（像素）
STRIDE = 16         # 滑窗步长。见文首「已知局限」：只能检出相对位移为步长整数倍的重复
MIN_STD = 12.0      # 区块灰度标准差下限：低于此视为空白/背景，跳过
MIN_ENTROPY = 4.0   # 区块灰度熵下限（bit）。线条图/坐标轴/网格熵极低（~1-2），
                    # 显微图/印迹/散点等真实影像熵高（~6-7）。
                    # 没有这道门控时，图表的重复线条元素会产生大量 r=1.0 的假重复。
CORR_MIN = 0.98     # 精确验证的 Pearson 相关下限
MIN_SELF_DIST = 96  # 同图内两区块中心的最小距离，低于此不算重复
MAX_SIDE = 1200     # 超大图先缩放，控制计算量


def _system_limitation(detail, sid="SYS-001"):
    return {
        "id": sid,
        "category": "figure_unreadable",
        "impact": detail,
        "affected_modules": ["M5"],
        "affected_targets": [],
        "affected_fields": [],
        "evidence_refs": [],
        "recommended_action": "在具备 numpy 与 Pillow 的环境重跑图像完整性审计",
        "produced_by": "stage_3",
    }


def _sig(sid, target, detail, extra):
    """图像审计信号。severity_hint 恒为 null —— 契约层面禁止自动定性。"""
    return {
        "id": sid,
        "type": "figure_integrity_candidate",
        "target": target,
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": [],
        "routed_to": ["M5"],
        "produced_by": "stage_3",
        "image_audit": dict(
            extra,
            rule_version=RULE_VERSION,
            candidate=True,
            severity_hint=None,
            manual_review_required=True,
        ),
    }


# ---------------------------------------------------------------- 图像载入
def load_gray(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    if max(w, h) > MAX_SIDE:
        scale = MAX_SIDE / float(max(w, h))
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))))
    return np.asarray(im, dtype=np.float64)


def dhash(block):
    """差分哈希：缩到 9x8，比较水平相邻像素，得 64 位。"""
    im = Image.fromarray(block.astype(np.uint8)).resize((9, 8))
    a = np.asarray(im, dtype=np.int16)
    bits = a[:, 1:] > a[:, :-1]
    out = 0
    for b in bits.flatten():
        out = (out << 1) | int(b)
    return out


def popcount(x):
    return bin(x).count("1")


def shannon_entropy(block):
    """8 bit 灰度直方图的香农熵。线条图约 1-2 bit，真实影像约 6-7 bit。"""
    hist = np.bincount(block.astype(np.uint8).flatten(), minlength=256).astype(np.float64)
    total = hist.sum()
    if total <= 0:
        return 0.0
    p = hist / total
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def iter_blocks(arr, name):
    h, w = arr.shape
    for y in range(0, max(1, h - BLOCK + 1), STRIDE):
        for x in range(0, max(1, w - BLOCK + 1), STRIDE):
            blk = arr[y:y + BLOCK, x:x + BLOCK]
            if blk.shape != (BLOCK, BLOCK):
                continue
            sd = float(blk.std())
            if sd < MIN_STD:          # 空白/背景，跳过
                continue
            ent = shannon_entropy(blk)
            if ent < MIN_ENTROPY:     # 线条图/坐标轴/网格，跳过
                continue
            yield {"image": name, "y": y, "x": x, "std": sd, "entropy": ent,
                   "hash": dhash(blk), "pixels": blk}


def pearson(a, b):
    av, bv = a.flatten(), b.flatten()
    av = av - av.mean()
    bv = bv - bv.mean()
    denom = np.sqrt((av * av).sum() * (bv * bv).sum())
    return float((av * bv).sum() / denom) if denom > 0 else 0.0


# ---------------------------------------------------------------- 1 重复区域
def find_duplicate_regions(images, max_signals=20):
    """images: {name: gray_array}。返回候选重复区域信号列表。"""
    blocks = []
    for name, arr in images.items():
        blocks.extend(iter_blocks(arr, name))

    # 按精确 dHash 分桶：像素级复制粘贴会产生完全相同的哈希，
    # 因此分桶是 O(n) 的有效预筛，避免 O(n^2) 两两比较。
    buckets = {}
    for b in blocks:
        buckets.setdefault(b["hash"], []).append(b)

    # 先收集全部匹配，再按「图对」聚合成一条信号 ——
    # 同一处重复会命中相邻的多个网格块，逐对报告会淹没真正的信号。
    pairs = []
    for _, group in buckets.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                b1, b2 = group[i], group[j]
                if b1["image"] == b2["image"]:
                    dy = abs(b1["y"] - b2["y"])
                    dx = abs(b1["x"] - b2["x"])
                    if (dy * dy + dx * dx) ** 0.5 < MIN_SELF_DIST:
                        continue
                r = pearson(b1["pixels"], b2["pixels"])
                if r < CORR_MIN:
                    continue
                pairs.append((b1, b2, r))

    by_pair = {}
    for b1, b2, r in pairs:
        key = tuple(sorted([b1["image"], b2["image"]]))
        by_pair.setdefault(key, []).append((b1, b2, r))

    sigs = []
    for n, (key, matches) in enumerate(sorted(by_pair.items()), 1):
        if n > max_signals:
            break
        same = key[0] == key[1]
        examples = [
            {"a": [m[0]["x"], m[0]["y"]], "b": [m[1]["x"], m[1]["y"]],
             "r": round(m[2], 4)} for m in matches[:5]
        ]
        best = max(m[2] for m in matches)
        sigs.append(_sig(
            f"SIG-{n:03d}",
            f"figure_integrity.{key[0]}",
            f"检出 {len(matches)} 处候选重复区块（{BLOCK}×{BLOCK}），"
            f"{'同图内远距离重复' if same else f'跨图重复：{key[0]} ↔ {key[1]}'}，"
            f"最高像素相关 r={best:.4f}，前几处位置 {examples[:3]}。"
            f"**这只是候选**：同一对照组图片复用、模板化示意图、放大插图都会产生"
            f"合法重复，必须人工核对原图后判断。",
            {"check": "duplicated_region_candidate",
             "image_a": key[0], "image_b": key[1], "same_image": same,
             "match_count": len(matches), "max_correlation": round(best, 4),
             "examples": examples}))
    return sigs


# ---------------------------------------------------------------- 2 拼接痕迹
def find_splice_discontinuity(name, arr, z_threshold=6.0):
    """列向背景统计的突变 —— 印迹图拼接的典型痕迹。"""
    if arr.shape[1] < 40:
        return []
    col_med = np.median(arr, axis=0)
    d = np.abs(np.diff(col_med))
    if d.size < 8:
        return []
    mad = np.median(np.abs(d - np.median(d)))
    if mad < 1e-6:
        return []
    z = (d - np.median(d)) / (1.4826 * mad)
    peaks = np.where(z > z_threshold)[0]
    # 边缘 5% 不算（图像边框）
    margin = max(2, int(arr.shape[1] * 0.05))
    peaks = [int(p) for p in peaks if margin < p < arr.shape[1] - margin]
    if not peaks:
        return []
    return [_sig(
        "SIG-001",
        f"figure_integrity.{name}",
        f"检出 {len(peaks)} 处列向背景突变（x≈{peaks[:5]}），"
        f"稳健 z 分数超过 {z_threshold}。印迹类图像的背景在拼接处常出现此类不连续。"
        f"**这只是候选**：泳道间隔、图像本身的分区排版也会产生同样信号，"
        f"必须人工核对原图。",
        {"check": "splice_discontinuity_candidate", "image": name,
         "columns": peaks[:20], "z_threshold": z_threshold})]


# ---------------------------------------------------------------- 3 异常均匀区
def find_uniform_patches(name, arr, min_run=3):
    """连续多个区块方差近似为零 —— 可能是涂抹或克隆填充。"""
    h, w = arr.shape
    flat = []
    for y in range(0, max(1, h - BLOCK + 1), BLOCK):
        for x in range(0, max(1, w - BLOCK + 1), BLOCK):
            blk = arr[y:y + BLOCK, x:x + BLOCK]
            if blk.shape == (BLOCK, BLOCK) and blk.std() < 0.5 and 20 < blk.mean() < 235:
                flat.append([int(x), int(y)])
    if len(flat) < min_run:
        return []
    return [_sig(
        "SIG-001",
        f"figure_integrity.{name}",
        f"检出 {len(flat)} 个近似完全均匀的非极值区块（灰度标准差 <0.5 且非纯黑纯白）。"
        f"**这只是候选**：纯色填充的示意图元素、图例底色都会命中，必须人工核对。",
        {"check": "uniform_patch_candidate", "image": name,
         "patches": flat[:20], "patch_count": len(flat)})]


# ---------------------------------------------------------------- 主入口
def audit_figures(paths):
    """paths: 图像文件路径列表。返回 (signals, system_limitations)。"""
    if not DEPS_OK:
        return [], [_system_limitation(
            f"图像完整性审计需要 numpy 与 Pillow，当前环境不可用：{DEPS_ERR}")]

    images, limits = {}, []
    for p in paths:
        try:
            images[os.path.basename(p)] = load_gray(p)
        except Exception as exc:
            limits.append(_system_limitation(
                f"无法读取图像 {os.path.basename(p)}：{exc}",
                sid=f"SYS-{len(limits) + 1:03d}"))

    if not images:
        return [], limits

    sigs = find_duplicate_regions(images)
    for name, arr in images.items():
        sigs.extend(find_splice_discontinuity(name, arr))
        sigs.extend(find_uniform_patches(name, arr))
    # 各检测器可独立调用，因而各自从 SIG-001 起编号；汇总入口必须重排为
    # 报告内唯一、符合 schema 的数字 id。
    for i, sig in enumerate(sigs, 1):
        sig["id"] = f"SIG-{i:03d}"
    return sigs, limits


# ---------------------------------------------------------------- 自检
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    if not DEPS_OK:
        print(f"  SKIP  numpy/PIL 不可用：{DEPS_ERR}")
        sigs, lims = audit_figures(["nonexistent.png"])
        expect("依赖缺失 -> system_limitation 而非崩溃", len(lims) >= 1, True)
        print("\n全部通过（降级路径）")
        return 0

    rng = np.random.default_rng(42)

    # --- 造一张含真实重复区块的图 ---
    # 植入位置必须落在步长网格上：本方法按网格切块，只能检出
    # 相对位移为 STRIDE 整数倍的重复（见文首「已知局限」）。
    base = rng.integers(0, 255, size=(256, 256)).astype(np.float64)
    patch = base[0:64, 0:64].copy()
    base[128:192, 128:192] = patch          # 位移 (128,128) = STRIDE 的整数倍
    imgs = {"dup.png": base}
    sigs = find_duplicate_regions(imgs)
    dup = [s for s in sigs if s["image_audit"]["check"] == "duplicated_region_candidate"]
    expect("植入的重复区块被检出", len(dup) >= 1, True)
    if dup:
        expect("重复候选标 candidate=True", dup[0]["image_audit"]["candidate"], True)
        expect("重复候选不给 severity", dup[0]["image_audit"]["severity_hint"], None)
        expect("强制人工复核", dup[0]["image_audit"]["manual_review_required"], True)
        expect("路由到 M5", dup[0]["routed_to"], ["M5"])

    # --- 纯噪声图不应互相误报 ---
    noise = {"a.png": rng.integers(0, 255, size=(256, 256)).astype(np.float64),
             "b.png": rng.integers(0, 255, size=(256, 256)).astype(np.float64)}
    s2 = find_duplicate_regions(noise)
    expect("两张独立噪声图无重复误报",
           len([x for x in s2 if x["image_audit"]["check"] == "duplicated_region_candidate"]), 0)

    # --- 全白背景绝不能互相匹配（方差门控）---
    blank = {"w1.png": np.full((256, 256), 255.0), "w2.png": np.full((256, 256), 255.0)}
    s3 = find_duplicate_regions(blank)
    expect("纯白背景被方差门控挡住", len(s3), 0)

    # --- 拼接痕迹 ---
    spliced = rng.normal(120, 6, size=(128, 256))
    spliced[:, 128:] += 60                  # 右半边整体变亮 = 拼接
    s4 = find_splice_discontinuity("blot.png", spliced)
    expect("植入的拼接不连续被检出", len(s4) >= 1, True)
    smooth = rng.normal(120, 6, size=(128, 256))
    s5 = find_splice_discontinuity("smooth.png", smooth)
    expect("平滑背景无拼接误报", len(s5), 0)

    # --- 契约 ---
    allsig = dup + s4
    expect("全部信号 type 一致",
           {x["type"] for x in allsig}, {"figure_integrity_candidate"})
    expect("无信号携带 severity", all("severity" not in x for x in allsig), True)
    expect("图像信号 id 符合 schema",
           all(__import__("re").match(r"^SIG-[0-9]{3,}$", x["id"]) for x in allsig), True)
    lim = _system_limitation("测试")
    expect("图像 system_limitation id 符合 schema",
           bool(__import__("re").match(r"^SYS-[0-9]{3,}$", lim["id"])), True)

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


def _scan(root):
    """对真实语料跑一遍，用于经验校准误报率。"""
    paths = []
    for dirpath, _, files in os.walk(root):
        for f in sorted(files):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")):
                paths.append(os.path.join(dirpath, f))
    print(f"扫描 {len(paths)} 张图像 …")
    sigs, lims = audit_figures(paths)
    from collections import Counter
    c = Counter(s["image_audit"]["check"] for s in sigs)
    print(f"信号 {len(sigs)} 条：{dict(c)}；system_limitation {len(lims)} 条")
    for s in sigs[:8]:
        print("  -", s["detail"][:150].replace("\n", " "))
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    if "--selftest" in args:
        sys.exit(_selftest())
    if args and os.path.isdir(args[0]):
        sys.exit(_scan(args[0]))
    print(__doc__)
