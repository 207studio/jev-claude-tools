#!/bin/bash
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd)
W="$H/work"; OUT="$H/out"
Q1='In src/jev_mode/batch.py, what does text_tokens measure? Does it measure the tokens that actually entered the agent context window?'
Q2='When one item in a jev-mode batch is too large to send to Jev, what does jev-mode do?'
Q3='Where does jev-mode get the TypeSafe API key from, and in what order does it look?'
run() {  # $1 설정용 스타일명  $2 파일 라벨  $3 반복번호
  for qi in 1 2 3; do
    eval q=\$Q$qi; f="$OUT/${2}_q${qi}_r${3}.json"
    ( cd "$W" && claude -p "$q" --model claude-sonnet-5 --output-format json \
        --settings "{\"outputStyle\":\"$1\"}" \
        --allowedTools "Read,Grep,Glob" --disallowedTools "Edit,Write,Bash,NotebookEdit,WebFetch,WebSearch,Agent" \
        --max-turns 12 > "$f" 2>/dev/null )
    python3 -c "
import json;d=json.load(open('$f'));u=d.get('usage',{})
open('$f'.replace('.json','.txt'),'w').write(d.get('result',''))
print(f\"{'$2':8} {$qi:3} {$3:4} {u.get('output_tokens',0):8} {d.get('num_turns',0):5} {d.get('total_cost_usd',0):9.4f}\")"
  done
}
printf '%-8s %-3s %-4s %8s %5s %9s\n' STYLE Q REP OUT_TOK TURNS COST_USD
run default default 2
run Concise Concise 2
run Jev     Jev2    1
run Jev     Jev2    2
