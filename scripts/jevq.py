#!/usr/bin/env python3
"""jevq — 코드를 컨텍스트에 들이기 전에 Jev에 묻는다. 출력은 한 줄(판정 + confidence). 코드는 출력하지 않는다.

  jevq.py ask   FILE START END "예/아니오 질문"   -> YES | NO | UNSURE | ERROR  conf
  jevq.py claim FILE LINE        (주장 본문은 stdin) -> supported | contradicted | cannot_tell | UNSURE | ERROR  conf

FILE은 저장소 루트 기준 상대경로. 루트는 JEVQ_ROOT 환경변수, 없으면 현재 디렉터리의 git 최상위, 그것도 없으면 현재 디렉터리.
ask는 220줄 이하만 받는다(jev-mode 요청 상한 보호). claim은 LINE 앞뒤 45줄을 본다.

원작: iPad 앱 저장소를 다루던 다른 세션(2026-09-21)이 서브에이전트용으로 세 번 다시 쓴 도구. 특정 워크트리에 경로가
하드코딩돼 있어 매번 재작성됐던 것을 루트 자동 탐지로 일반화했다. 판정 기준·임계값은 원작 그대로다.
"""
import json
import os
import subprocess
import sys
import tempfile

ASK_MAX_LINES = 220
CLAIM_WINDOW = 45
ASK_UNSURE_BELOW = 0.55
CLAIM_UNSURE_BELOW = 0.4


def repo_root():
    root = os.environ.get("JEVQ_ROOT")
    if root:
        return root
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else os.getcwd()


def slice_lines(path, a, b):
    lines = open(os.path.join(repo_root(), path), encoding="utf-8").read().split("\n")
    a, b = max(1, a), min(len(lines), b)
    return "\n".join(f"{i}: {lines[i - 1]}" for i in range(a, b + 1)), a, b


def ask_jev(state, question):
    with tempfile.TemporaryDirectory() as d:
        sp, qp = os.path.join(d, "s.txt"), os.path.join(d, "q.json")
        with open(sp, "w", encoding="utf-8") as f:
            f.write(state)
        with open(qp, "w", encoding="utf-8") as f:
            json.dump({"v": question}, f, ensure_ascii=False)
        r = subprocess.run(["jev-mode", "ask", "--state-file", sp, "--questions-file", qp],
                           capture_output=True, text=True, timeout=120)
    try:
        out = json.loads(r.stdout)
        ans = (out.get("answers") or out)["v"]
        return ans["choice"], float(ans.get("confidence", 0))
    except Exception:
        return "ERROR", 0.0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("ask", "claim"):
        print(__doc__.strip().split("\n\n")[1])
        return 2

    if argv[1] == "ask":
        if len(argv) != 6:
            print('usage: jevq.py ask FILE START END "question"')
            return 2
        path, a, b, question = argv[2], int(argv[3]), int(argv[4]), argv[5]
        if b - a > ASK_MAX_LINES:
            print(f"REJECTED: {ASK_MAX_LINES}줄 이하로 나눠 물을 것")
            return 2
        code, a, b = slice_lines(path, a, b)
        choice, conf = ask_jev(f"File: {path} (lines {a}-{b})\n{code}", {
            "type": "choice",
            "instructions": question + " Judge only from the numbered code shown.",
            "criteria": {
                "yes": "the code shown clearly makes this true",
                "no": "the code shown clearly makes this false, or the thing asked about is absent",
            },
        })
        verdict = "UNSURE" if conf < ASK_UNSURE_BELOW and choice != "ERROR" else choice.upper()
        print(verdict, round(conf, 2))
        return 0

    if len(argv) != 4:
        print("usage: jevq.py claim FILE LINE   (claim text on stdin)")
        return 2
    path, line = argv[2], int(argv[3])
    claim = sys.stdin.read().strip()[:3000]
    code, a, b = slice_lines(path, line - CLAIM_WINDOW, line + CLAIM_WINDOW)
    choice, conf = ask_jev(f"CLAIM about {path} line {line}:\n{claim}\n\nCODE ({path} lines {a}-{b}):\n{code}", {
        "type": "choice",
        "instructions": "A reviewer made the CLAIM about the numbered CODE. Judging only from the code shown, "
                        "does the code behave the way the claim says at the named line?",
        "criteria": {
            "supported": "the named line and surrounding code match the claim; the described operation is there "
                         "and the described check is absent",
            "contradicted": "the code shown has a check, guard or different behaviour that makes the claim wrong",
            "cannot_tell": "the claim depends on code that is not shown",
        },
    })
    verdict = "UNSURE" if conf < CLAIM_UNSURE_BELOW and choice != "ERROR" else choice
    print(verdict, round(conf, 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
