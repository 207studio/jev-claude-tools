#!/bin/bash
# 주간 토큰 최적화 스윕의 기계적 부분. 태스크가 이것 하나만 호출하도록 해서
# 권한 프롬프트를 1회로 줄인다 (무인 실행 시 멈추지 않게).
# 판단·보고서 작성은 에이전트가 한다. 이 스크립트는 설치·수정을 하지 않는다.
set -uo pipefail
S=/private/tmp/weekly-sweep-$$
mkdir -p "$S"

echo "===== 1. 측정 ====="
jevprune gain 2>&1 | head -1

echo
echo "===== 2. 건강 ====="
jev-mode check 2>&1 | head -c 400
echo
for b in jev-claude jev-explain jev-mode jev-judge jevprune jev-codex; do
  printf '%-12s %s\n' "$b" "$(command -v "$b" 2>&1 || echo MISSING)"
done
printf 'fast-jev-compaction: %s (0이면 사라짐)\n' "$(grep -c 'fast-jev-compaction' "$HOME/.claude/settings.json" 2>/dev/null || echo 0)"
printf "jev_context MCP: %s\n" "$(claude mcp get jev_context 2>/dev/null | grep -m1 Status || echo MISSING)"
printf 'user skills: %s (기준 19)\n' "$(ls "$HOME/.claude/skills/" 2>/dev/null | wc -l | tr -d ' ')"
printf 'agent model tiers:\n'
for f in "$HOME"/.claude/agents/*.md; do
  printf '  %-20s %s\n' "$(basename "$f" .md)" "$(grep -m1 '^model:' "$f" 2>/dev/null || echo '(없음)')"
done

echo
echo "===== 3. GitHub 스윕 (신규 후보 판별은 에이전트가 state 파일과 대조) ====="
for q in 'jev claude code' 'jev tokens' 'jev compaction' 'jev hook' 'jev context'; do
  echo "--- $q ---"
  gh api -X GET search/repositories -f q="$q" -f sort=stars -f order=desc -f per_page=12 \
    --jq '.items[] | [.stargazers_count, .full_name, .pushed_at[:10], (.description // "")] | @tsv' 2>/dev/null | head -12
done

echo
echo "===== 4. 설치물 업데이트 확인 (pull 하지 않음) ====="
git -C "$HOME/.local/share/jev-mode" fetch -q 2>/dev/null
n=$(git -C "$HOME/.local/share/jev-mode" log --oneline HEAD..origin/HEAD 2>/dev/null | wc -l | tr -d ' ')
echo "jev-mode 새 커밋: ${n:-0}"
printf 'jev-router  로컬=%s 최신=%s\n' \
  "$(grep -m1 '"version"' "$HOME/.local/share/jev-router-prefix/lib/node_modules/jev-router/package.json" 2>/dev/null | sed 's/[^0-9.]//g')" \
  "$(npm view jev-router version 2>/dev/null)"
printf 'jevprune    로컬=%s 최신=%s\n' \
  "$(jevprune --version 2>/dev/null)" "$(npm view jevprune version 2>/dev/null)"

rm -rf "$S"
echo
echo "===== 끝 ====="
