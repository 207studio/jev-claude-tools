#!/usr/bin/env python3
"""chunk — git이 추적하는 소스를 ~100줄 단위 JSONL로 자른다. jev-mode batch의 --items 입력용.

  chunk.py OUT.jsonl [--ext .swift,.py,...] [--exclude PREFIX] [--exclude PREFIX] ...

현재 디렉터리의 git 최상위에서 실행된다. 레코드: {"id": "path:START-END", "text": "File: ... \\n1: ..."}.
청크는 100줄을 목표로 하되 빈 줄 경계까지(최대 135줄) 늘리고, 25줄 미만의 꼬리는 앞 청크에 붙인다.
한 줄이 4000자를 넘는 파일은 생성물·압축본으로 보고 건너뛴다.
코드 본문은 표준출력에 내지 않는다 — 개수만 출력한다.

원작: iPad 앱 저장소를 다루던 다른 세션(2026-09-21). 그 저장소 전용 제외 경로가
하드코딩돼 있던 것을 --exclude 인자로 일반화했다. 청킹 규칙은 원작 그대로다.
"""
import json
import os
import subprocess
import sys

DEFAULT_EXT = (".swift", ".py", ".mjs", ".js", ".ts", ".tsx", ".sh", ".c", ".h", ".go", ".rs", ".gd", ".cs")
ALWAYS_EXCLUDE = ("vendor/", "node_modules/", "dist/", "build/", "Pods/", ".build/")
TARGET, MAXL, MIN_TAIL, LONG_LINE = 100, 135, 25, 4000


def parse(argv):
    if len(argv) < 2:
        print(__doc__.strip().split("\n\n")[1])
        sys.exit(2)
    out, exts, excludes, i = argv[1], DEFAULT_EXT, list(ALWAYS_EXCLUDE), 2
    while i < len(argv):
        if argv[i] == "--ext":
            exts = tuple(e if e.startswith(".") else "." + e for e in argv[i + 1].split(","))
            i += 2
        elif argv[i] == "--exclude":
            excludes.append(argv[i + 1])
            i += 2
        else:
            print(f"알 수 없는 인자: {argv[i]}")
            sys.exit(2)
    return os.path.abspath(out), exts, excludes


def main(argv):
    out, exts, excludes = parse(argv)
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    if not top:
        print("git 저장소 안에서 실행할 것")
        return 2
    os.chdir(top)
    files = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"],
                           capture_output=True, text=True).stdout.splitlines()

    def keep(p):
        return p.endswith(exts) and not p.endswith(".min.js") and not any(
            p.startswith(x) or f"/{x}" in p for x in excludes)

    src = [p for p in files if keep(p)]
    n, skipped = 0, 0
    with open(out, "w", encoding="utf-8") as f:
        for p in src:
            try:
                lines = open(p, encoding="utf-8").read().split("\n")
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
                    f.write(json.dumps({"id": f"{p}:{i + 1}-{j}",
                                        "text": f"File: {p} (lines {i + 1}-{j} of {total})\n{body}"},
                                       ensure_ascii=False) + "\n")
                    n += 1
                i = j
    print(f"files {len(src)}  chunks {n}  skipped {skipped}  -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
