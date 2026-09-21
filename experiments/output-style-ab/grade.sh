#!/bin/bash
# 정답 대조 채점 — Jev가 판정, 답 본문은 컨텍스트에 들이지 않는다.
H=$(cd "$(dirname "$0")" && pwd)
python3 - "$H" <<'PY'
import json, sys, glob, os
H = sys.argv[1]
ref = {
 "1": "text_tokens is the sum of estimate_tokens over the input items' text: an estimate of the size of the input records. It does NOT measure tokens that entered the agent's context window.",
 "2": "Before any API call, batch checks every item's estimated size plus the questions against the request ceiling (about 32k tokens). If any item is too large it raises an error for the whole batch, naming the first oversized item. Nothing is sent to Jev.",
 "3": "First the TYPESAFE_API_KEY environment variable. If that is not set, a key file whose path is given by TYPESAFE_ENV_FILE, defaulting to ~/.config/jev-mode/typesafe.env. The key is never logged.",
}
with open(f"{H}/grade-items.jsonl", "w") as f:
    for p in sorted(glob.glob(f"{H}/out/*.txt")):
        name = os.path.basename(p)[:-4]
        q = name.split("_q")[1][0]
        ans = open(p).read().strip() or "(empty answer)"
        f.write(json.dumps({"id": name, "text": f"REFERENCE ANSWER:\n{ref[q]}\n\nCANDIDATE ANSWER:\n{ans}"}, ensure_ascii=False) + "\n")
json.dump({"grade": {"type": "choice",
  "instructions": "Compare the CANDIDATE ANSWER with the REFERENCE ANSWER. Judge factual correctness only; ignore length, tone and formatting.",
  "criteria": {
    "correct": "states the reference's key facts and contradicts none of them",
    "partial": "gets the main point but misses or blurs one key fact",
    "wrong": "contradicts the reference, misses its main point, or is empty"}}},
  open(f"{H}/grade-q.json", "w"))
PY
jev-mode batch --items "$H/grade-items.jsonl" --questions "$H/grade-q.json" --out "$H/grades.jsonl" --pool 6 2>&1 | grep -E '"(ok|failed)"' | tr -d ' ,'
