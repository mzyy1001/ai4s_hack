#!/usr/bin/env bash
# 跑一轮 codex 评审。
#
#   ./loop/run_round.sh [轮次号]
#
# 一轮的完整生命周期：
#   1. 选主题（按轮次号在 themes.txt 中轮转）
#   2. 组装 prompt = _base.md + 本轮主题
#   3. codex exec（workspace-write，仅本仓库可写）
#   4. 守卫一：改动路径必须在白名单内 —— 碰了队友文件就整轮丢弃
#   5. 守卫二：tools/validate_schemas.py 必须通过 —— 不通过就整轮丢弃
#   6. 提交并推送，把摘要追加进 loop/state/history.md
#
# 任一守卫失败 → git 硬回滚到本轮开始时的状态，本轮不产生提交。

set -uo pipefail

REPO="/Users/henrychen/ai4s_hack"
STATE_DIR="$REPO/loop/state"
LOG_DIR="$REPO/loop/logs"
PROMPT_DIR="$REPO/loop/prompts"
HISTORY="$STATE_DIR/history.md"
ENV_FILE="$HOME/.config/ai4s_hack/openai.env"

mkdir -p "$STATE_DIR" "$LOG_DIR" "$REPO/docs/proposals"
cd "$REPO" || exit 1

# ---------------------------------------------------------------- 轮次与主题
if [ $# -ge 1 ]; then
  ROUND="$1"
else
  ROUND=$(( $(cat "$STATE_DIR/round" 2>/dev/null || echo 0) + 1 ))
fi
echo "$ROUND" > "$STATE_DIR/round"

THEME_COUNT=$(grep -c '|' "$PROMPT_DIR/themes.txt")
THEME_IDX=$(( (ROUND - 1) % THEME_COUNT + 1 ))
THEME_LINE=$(grep '|' "$PROMPT_DIR/themes.txt" | sed -n "${THEME_IDX}p")

THEME_SLUG="${THEME_LINE%%|*}"
REST="${THEME_LINE#*|}"
THEME_NAME="${REST%%|*}"
THEME_BODY="${REST#*|}"

STAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG="$LOG_DIR/round-$(printf '%03d' "$ROUND")-$THEME_SLUG.log"

echo "=========================================================="
echo "Round $ROUND · $THEME_NAME ($THEME_SLUG)"
echo "开始 $STAMP"
echo "日志 $LOG"
echo "=========================================================="

# ---------------------------------------------------------------- 前置检查
if [ ! -f "$ENV_FILE" ]; then
  echo "FATAL: 找不到 $ENV_FILE" | tee -a "$LOG"; exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

if [ -n "$(git status --porcelain)" ]; then
  echo "WARN: 工作区不干净，先暂存" | tee -a "$LOG"
  git stash push -u -m "pre-round-$ROUND" >> "$LOG" 2>&1
fi

BASE_SHA=$(git rev-parse HEAD)
echo "基线 $BASE_SHA" | tee -a "$LOG"

# ---------------------------------------------------------------- 组装 prompt
PROMPT_FILE=$(mktemp)
{
  cat "$PROMPT_DIR/_base.md"
  echo
  echo "---"
  echo
  echo "# 本轮任务"
  echo
  echo "**轮次 N = $ROUND** · **主题 theme = $THEME_SLUG** · **$THEME_NAME**"
  echo
  echo "$THEME_BODY"
  echo
  echo "提案文件请写到：\`docs/proposals/round-$ROUND-$THEME_SLUG.md\`"
} > "$PROMPT_FILE"

# ---------------------------------------------------------------- 跑 codex
echo "--- codex 开始 ---" | tee -a "$LOG"
set +e
codex exec \
  --sandbox workspace-write \
  -C "$REPO" \
  -c model_reasoning_effort="high" \
  "$(cat "$PROMPT_FILE")" < /dev/null >> "$LOG" 2>&1
CODEX_RC=$?
set -e
rm -f "$PROMPT_FILE"
echo "--- codex 退出码 $CODEX_RC ---" | tee -a "$LOG"

# ---------------------------------------------------------------- 守卫一：路径白名单
CHANGED=$(git status --porcelain | awk '{print $NF}')
if [ -z "$CHANGED" ]; then
  echo "本轮 codex 没有产生任何改动。" | tee -a "$LOG"
  printf -- '- **R%s** %s · `%s` · 无改动\n' "$ROUND" "$STAMP" "$THEME_SLUG" >> "$HISTORY"
  exit 0
fi

echo "改动文件：" | tee -a "$LOG"
echo "$CHANGED" | sed 's/^/  /' | tee -a "$LOG"

FORBIDDEN=$(echo "$CHANGED" | grep -E \
  '^(skills/biomed-paper-review/references/0[235]-|datasets/|loop/|\.gitignore)' || true)

if [ -n "$FORBIDDEN" ]; then
  echo "GUARD-FAIL 改动触碰禁止路径，整轮回滚：" | tee -a "$LOG"
  echo "$FORBIDDEN" | sed 's/^/  /' | tee -a "$LOG"
  git reset --hard "$BASE_SHA" >> "$LOG" 2>&1
  git clean -fd >> "$LOG" 2>&1
  printf -- '- **R%s** %s · `%s` · ❌ 回滚（触碰禁止路径：%s）\n' \
    "$ROUND" "$STAMP" "$THEME_SLUG" "$(echo "$FORBIDDEN" | tr '\n' ' ')" >> "$HISTORY"
  exit 0
fi

# ---------------------------------------------------------------- 守卫二：四项自检
# 契约校验器 + 三个一期工具的自检必须全部通过。
echo "--- 自检 ---" | tee -a "$LOG"
CHECKS=(
  "python3 tools/validate_schemas.py"
  "python3 skills/biomed-paper-review/scripts/normalize_biomed_units.py --selftest"
  "python3 skills/biomed-paper-review/scripts/statistical_forensics.py --selftest"
  "python3 skills/biomed-paper-review/scripts/ethics_compliance_check.py --selftest"
  "python3 skills/biomed-paper-review/scripts/sequence_identifier_audit.py --selftest"
)
FAILED_CHECK=""
for chk in "${CHECKS[@]}"; do
  set +e
  OUT=$($chk 2>&1)
  RC=$?
  set -e
  echo "  [$([ $RC -eq 0 ] && echo OK || echo FAIL)] $chk" | tee -a "$LOG"
  echo "$OUT" | tail -5 >> "$LOG"
  if [ $RC -ne 0 ]; then FAILED_CHECK="$chk"; break; fi
done

if [ -n "$FAILED_CHECK" ]; then
  echo "GUARD-FAIL 自检不通过（$FAILED_CHECK），整轮回滚。" | tee -a "$LOG"
  git reset --hard "$BASE_SHA" >> "$LOG" 2>&1
  git clean -fd >> "$LOG" 2>&1
  printf -- '- **R%s** %s · `%s` · ❌ 回滚（自检失败：%s）\n' \
    "$ROUND" "$STAMP" "$THEME_SLUG" "$FAILED_CHECK" >> "$HISTORY"
  exit 0
fi

# ---------------------------------------------------------------- 提交并推送
N_FILES=$(echo "$CHANGED" | wc -l | tr -d ' ')
git add -A
git -c user.name="henry chen" -c user.email="hongruichen2003@gmail.com" \
  commit -q -m "codex R$ROUND · $THEME_NAME

主题：$THEME_SLUG
改动 $N_FILES 个文件；校验器全部通过。
提案见 docs/proposals/round-$ROUND-$THEME_SLUG.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" >> "$LOG" 2>&1

NEW_SHA=$(git rev-parse --short HEAD)

set +e
git push origin main >> "$LOG" 2>&1
PUSH_RC=$?
set -e

if [ $PUSH_RC -eq 0 ]; then
  echo "已提交 $NEW_SHA 并推送。" | tee -a "$LOG"
  printf -- '- **R%s** %s · `%s` · ✅ %s · %s 文件 · 已推送\n' \
    "$ROUND" "$STAMP" "$THEME_SLUG" "$NEW_SHA" "$N_FILES" >> "$HISTORY"
else
  echo "已提交 $NEW_SHA，但推送失败（下轮会重试）。" | tee -a "$LOG"
  printf -- '- **R%s** %s · `%s` · ⚠️ %s · %s 文件 · 提交成功但推送失败\n' \
    "$ROUND" "$STAMP" "$THEME_SLUG" "$NEW_SHA" "$N_FILES" >> "$HISTORY"
fi

echo "Round $ROUND 结束。"
