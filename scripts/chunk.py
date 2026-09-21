#!/usr/bin/env python3
"""chunk — split git-tracked source into ~100-line JSONL records for `jev-mode batch --items`.

Record: {"id": "path:START-END", "text": "File: ...\\n1: ..."}. Chunks target 100 lines, extend to a blank
line (max 135), and fold a tail under 25 lines into the previous chunk. Files with a line over 4000
characters are treated as generated and skipped. Prints counts only, never code.

Origin: rewritten three times in another session working on an iPad app repository because of a hard-coded worktree path; generalized
to find the repo root from git. 2026-09-22: switched to argparse after `chunk.py --help` wrote a 6.5 MB
file named "--help" into a repository root; output inside the repository is now refused.
"""
import argparse
import json
import os
import subprocess
import sys

DEFAULT_EXT = (".swift", ".py", ".mjs", ".js", ".ts", ".tsx", ".sh", ".c", ".h", ".go", ".rs", ".gd", ".cs")
ALWAYS_EXCLUDE = ("vendor/", "node_modules/", "dist/", "build/", "Pods/", ".build/")
TARGET, MAXL, MIN_TAIL, LONG_LINE = 100, 135, 25, 4000


def git_top(path="."):
    r = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def chunks(top, exts, excludes):
    files = subprocess.run(["git", "-C", top, "-c", "core.quotepath=off", "ls-files"],
                           capture_output=True, text=True).stdout.splitlines()
    keep = [p for p in files if p.endswith(exts) and not p.endswith(".min.js")
            and not any(p.startswith(x) or f"/{x}" in p for x in excludes)]
    skipped = 0
    for p in keep:
        try:
            lines = open(os.path.join(top, p), encoding="utf-8").read().split("\n")
        except Exception:
            skipped += 1
            continue
        if max((len(l) for l in lines), default=0) > LONG_LINE:
            skipped += 1
            continue
        i, total = 0, len(lines)
        while i < total:
            j = min(i + TARGET, total)
            while j < total and j - i < MAXL and lines[j - 1].strip() != "":
                j += 1
            if total - j < MIN_TAIL:
                j = total
            body = "\n".join(f"{k + 1}: {lines[k]}" for k in range(i, j))
            if body.strip():
                yield {"id": f"{p}:{i + 1}-{j}", "text": f"File: {p} (lines {i + 1}-{j} of {total})\n{body}"}
            i = j
    chunks.files, chunks.skipped = len(keep), skipped


def main():
    ap = argparse.ArgumentParser(description="Split git-tracked source into ~100-line JSONL records for jev-mode batch.")
    ap.add_argument("out", help="output .jsonl path — must be outside the repository")
    ap.add_argument("--root", default=".", help="any path inside the repository (default: current directory)")
    ap.add_argument("--ext", help="comma-separated extensions, e.g. .swift,.py (default: common source types)")
    ap.add_argument("--exclude", action="append", default=[], metavar="PREFIX", help="path prefix to skip; repeatable")
    a = ap.parse_args()

    top = git_top(a.root)
    if not top:
        sys.exit("chunk.py: not inside a git repository (use --root)")
    out = os.path.abspath(a.out)
    if out == top or out.startswith(top + os.sep):
        sys.exit(f"chunk.py: refusing to write inside the repository ({out}). Write to a scratch directory instead.")
    exts = tuple(e if e.startswith(".") else "." + e for e in a.ext.split(",")) if a.ext else DEFAULT_EXT

    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for rec in chunks(top, exts, list(ALWAYS_EXCLUDE) + a.exclude):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"files {chunks.files}  chunks {n}  skipped {chunks.skipped}  -> {out}")


if __name__ == "__main__":
    main()
