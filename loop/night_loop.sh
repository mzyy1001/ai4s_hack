#!/usr/bin/env bash
# 通宵评审循环驱动器。
#
#   ./loop/night_loop.sh [轮数] [轮间隔秒]
#
# 默认跑 24 轮、轮间隔 60 秒。一轮 codex 高推理档大约 3–8 分钟，
# 24 轮约覆盖一整夜；主题在 themes.txt 的 8 个方向上轮转三遍。
#
# 每轮独立：任一轮失败（codex 报错、触碰禁止路径、校验器不过）只回滚该轮，
# 循环继续。可随时 Ctrl-C 或 kill 停止，已推送的轮次不受影响。

set -uo pipefail

REPO="/Users/henrychen/ai4s_hack"
ROUNDS="${1:-24}"
GAP="${2:-60}"

STATE_DIR="$REPO/loop/state"
mkdir -p "$STATE_DIR"
echo $$ > "$STATE_DIR/loop.pid"

cd "$REPO" || exit 1

START=$(date '+%Y-%m-%d %H:%M:%S')
{
  echo
  echo "## 通宵循环 · 启动 $START · 计划 $ROUNDS 轮 · 间隔 ${GAP}s"
  echo
} >> "$STATE_DIR/history.md"

echo "通宵循环启动：$ROUNDS 轮，间隔 ${GAP}s。PID $$"
echo "历史：$STATE_DIR/history.md"
echo "日志：$REPO/loop/logs/"

for i in $(seq 1 "$ROUNDS"); do
  if [ -f "$STATE_DIR/STOP" ]; then
    echo "检测到 STOP 文件，提前退出。"
    echo "- 循环于第 $i 轮前被 STOP 文件中止 $(date '+%H:%M:%S')" >> "$STATE_DIR/history.md"
    break
  fi

  echo
  echo "############ 循环进度 $i / $ROUNDS ############"
  bash "$REPO/loop/run_round.sh"

  if [ "$i" -lt "$ROUNDS" ]; then
    sleep "$GAP"
  fi
done

END=$(date '+%Y-%m-%d %H:%M:%S')
echo "" >> "$STATE_DIR/history.md"
echo "## 通宵循环 · 结束 $END" >> "$STATE_DIR/history.md"
rm -f "$STATE_DIR/loop.pid"
echo "循环结束 $END"
