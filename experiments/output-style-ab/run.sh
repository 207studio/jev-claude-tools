#!/bin/bash
# 출력 스타일 A/B: Default / Concise(내장) / Jev(우리 것). 읽기 전용, jev-mode 복사본에서.
# 답 본문은 파일로만 남기고 표준출력엔 토큰 수만 낸다.
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd)
W="$H/work"; OUT="$H/out"; REPS="${REPS:-1}"
rm -rf "$W" "$OUT"; mkdir -p "$OUT"
cp -R "$HOME/.local/share/jev-mode" "$W"

Q1='In src/jev_mode/batch.py, what does text_tokens measure? Does it measure the tokens that actually entered the agent context window?'
Q2='When one item in a jev-mode batch is too large to send to Jev, what does jev-mode do?'
Q3='Where does jev-mode get the TypeSafe API key from, and in what order does it look?'

printf '%-8s %-3s %-4s %8s %8s %8s %8s %9s\n' STYLE Q REP OUT_TOK IN_TOK CACHE_R CACHE_W COST_USD
for rep in $(seq 1 "$REPS"); do
  for s in default Concise Jev; do
    for qi in 1 2 3; do
      eval q=\$Q$qi
      f="$OUT/${s}_q${qi}_r${rep}.json"
      ( cd "$W" && claude -p "$q" --model claude-sonnet-5 --output-format json \
          --settings "{\"outputStyle\":\"$s\"}" \
          --allowedTools "Read,Grep,Glob" --disallowedTools "Edit,Write,Bash,NotebookEdit,WebFetch,WebSearch,Agent" \
          --max-turns 12 > "$f" 2>/dev/null )
      python3 - "$f" "$s" "$qi" "$rep" <<'PY'
import json, sys
f, s, q, r = sys.argv[1:5]
try:
    d = json.load(open(f)); u = d.get("usage", {})
    open(f.replace(".json", ".txt"), "w").write(d.get("result", ""))
    print(f"{s:8} {q:3} {r:4} {u.get('output_tokens',0):8} {u.get('input_tokens',0):8} "
          f"{u.get('cache_read_input_tokens',0):8} {u.get('cache_creation_input_tokens',0):8} {d.get('total_cost_usd',0):9.4f}")
except Exception as e:
    print(f"{s:8} {q:3} {r:4} ERROR {e}")
PY
    done
  done
done
