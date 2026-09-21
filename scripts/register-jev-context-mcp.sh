#!/bin/bash
# jev-context MCP 서버를 Claude Code 유저 스코프에 등록한다.
# Codex의 jev-context@personal 플러그인과 같은 서버 코드를 쓰되, 메트릭 디렉터리는 분리한다.
set -uo pipefail

NAME=jev_context
SERVER="$HOME/.local/share/codex-token-tools/jev-context/src/server.mjs"
DATA="$HOME/.local/share/codex-token-tools/context-data-claude"
RG=/Applications/ChatGPT.app/Contents/Resources/rg

[ -f "$SERVER" ] || { echo "서버 없음: $SERVER"; exit 1; }
[ -x "$RG" ]     || { echo "ripgrep 없음: $RG"; exit 1; }
mkdir -p "$DATA"

if claude mcp get "$NAME" >/dev/null 2>&1; then
  echo "이미 등록돼 있음 — 변경 없음"
  claude mcp get "$NAME" 2>&1 | head -8
  exit 0
fi

claude mcp add "$NAME" --scope user \
  -e JEV_CONTEXT_ROOT= \
  -e JEV_CONTEXT_RG="$RG" \
  -e JEV_CONTEXT_DATA_DIR="$DATA" \
  -- /usr/local/bin/node --env-file="$HOME/.jev-router.env" "$SERVER"

echo
echo "=== 확인 ==="
claude mcp get "$NAME" 2>&1 | head -10
echo
echo "완료. Claude Code를 재시작하면 mcp__jev_context__search_code 도구가 생깁니다."
echo "메트릭: $DATA  (Codex는 context-data, 분리됨)"
