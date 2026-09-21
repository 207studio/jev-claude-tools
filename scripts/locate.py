#!/usr/bin/env python3
"""locate — find where something happens in a repository without reading it: chunk -> keyword filter ->
jev-mode batch -> top file:line ranges. Prints ranges and scores only, never code.

  locate.py "what to find" [--root PATH] [--keywords 'a|b|c'] [--top 10] [--questions q.json]

Call this from the parent session instead of delegating "find the code that…" to a subagent. Measured in an
iPad app repository session (2026-09-22): an Explore agent told in prose to use Jev made 0 Jev calls and took
6 min 21 s and 113k tokens; the same search done this way took 7.3 s.

Default question: one choice — here / related / no. score = P(here) + 0.4 * P(related).
--questions replaces it; the first question's "here"-like first criterion is scored.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("chunk", os.path.join(HERE, "chunk.py"))
chunk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chunk)


def default_question(query):
    return {"loc": {
        "type": "choice",
        "instructions": f"A developer is looking for the code that causes or implements this: {query}. "
                        "Is it in this numbered code slice? Judge only from the code shown.",
        "criteria": {
            "here": "this slice contains the code that directly does it: the call, condition or state change a fix would touch",
            "related": "this slice is on the path (a caller, callee, or data it uses) but the deciding code is elsewhere",
            "no": "unrelated to it",
        }}}


def main():
    ap = argparse.ArgumentParser(description="Locate code by meaning with Jev; prints file:line ranges only.")
    ap.add_argument("query", help="what to find, in plain language")
    ap.add_argument("--root", default=".", help="any path inside the repository")
    ap.add_argument("--keywords", help="case-insensitive regex; only matching chunks go to Jev (recommended)")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--questions", help="custom jev-mode questions JSON (replaces the default)")
    ap.add_argument("--exclude", action="append", default=[], metavar="PREFIX")
    ap.add_argument("--ext")
    ap.add_argument("--max-chunks", type=int, default=600, help="refuse above this many chunks after filtering")
    ap.add_argument("--pool", type=int, default=12)
    a = ap.parse_args()

    top = chunk.git_top(a.root)
    if not top:
        sys.exit("locate.py: not inside a git repository (use --root)")
    exts = tuple(e if e.startswith(".") else "." + e for e in a.ext.split(",")) if a.ext else chunk.DEFAULT_EXT
    kw = re.compile(a.keywords, re.I) if a.keywords else None

    recs, total = [], 0
    for r in chunk.chunks(top, exts, list(chunk.ALWAYS_EXCLUDE) + a.exclude):
        total += 1
        if kw is None or kw.search(r["text"]):
            recs.append(r)
    if not recs:
        sys.exit(f"locate.py: 0 of {total} chunks matched --keywords")
    if len(recs) > a.max_chunks:
        sys.exit(f"locate.py: {len(recs)} chunks after filtering (limit {a.max_chunks}). Narrow --keywords or raise --max-chunks.")

    q = json.load(open(a.questions)) if a.questions else default_question(a.query)
    qkey = next(iter(q))
    crit = list(q[qkey]["criteria"])
    with tempfile.TemporaryDirectory() as d:
        items, qf, out = (os.path.join(d, n) for n in ("items.jsonl", "q.json", "out.jsonl"))
        with open(items, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        json.dump(q, open(qf, "w"), ensure_ascii=False)
        res = subprocess.run(["jev-mode", "batch", "--items", items, "--questions", qf, "--out", out,
                              "--pool", str(a.pool)], capture_output=True, text=True)
        rows = []
        if os.path.exists(out):
            for line in open(out, encoding="utf-8"):
                try:
                    o = json.loads(line)
                    ans = o["answers"][qkey]
                    p = ans.get("probabilities", {})
                    s = p.get(crit[0], 0) + (0.4 * p.get(crit[1], 0) if len(crit) > 2 else 0)
                    rows.append((s, o["id"], ans.get("choice", "?"), ans.get("confidence", 0)))
                except Exception:
                    pass
    failed = len(recs) - len(rows)
    rows.sort(reverse=True)
    print(f"# {total} chunks, {len(recs)} after keywords, {len(rows)} judged" + (f", {failed} failed" if failed else ""))
    for s, cid, choice, conf in rows[:a.top]:
        print(f"{s:.2f}  {choice:8} {cid}")
    if not rows:
        sys.exit("locate.py: no judgments returned — run `jev-mode check`. stderr: " + res.stderr.strip()[:300])


if __name__ == "__main__":
    main()
