#!/usr/bin/env python3
"""scout-gate — hook for the jev-scout agent. Blocks reading file contents until the agent has called Jev.

  scout-gate.py record   (PostToolUse, Bash)       mark this agent as having called Jev
  scout-gate.py gate     (PreToolUse, Read|Bash)   deny content reads before that mark

Declared in ~/.claude/agents/jev-scout.md frontmatter, so it runs only while that agent is active.
Not a security boundary: it makes "Jev first" the default path, it doesn't stop a determined bypass.
Fails open on malformed input — a gate that breaks work is worse than none.
"""
import json
import os
import re
import sys

JEV_CALL = re.compile(r"(locate\.py|jevq\.py|jev-mode\s+(ask|batch|classify)|jev-judge)")
CONTENT_READ = re.compile(r"(^|[|;&(]\s*|\s)(cat|head|tail|sed|less|more|bat|nl|awk|view)\s")
STATE = os.path.join(os.path.expanduser("~"), ".claude", "jev", ".scout-state")


def key(ev):
    k = ev.get("agent_id") or ev.get("session_id") or "unknown"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(k))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return 0
    os.makedirs(STATE, exist_ok=True)
    marker = os.path.join(STATE, key(ev))
    tool = ev.get("tool_name", "")
    cmd = (ev.get("tool_input") or {}).get("command", "") or ""

    if mode == "record":
        if tool == "Bash" and JEV_CALL.search(cmd):
            with open(marker, "a") as f:
                f.write(cmd[:200].replace("\n", " ") + "\n")
        return 0

    if mode == "gate":
        if os.path.exists(marker):
            return 0
        if tool == "Bash" and (JEV_CALL.search(cmd) or not CONTENT_READ.search(cmd)):
            return 0
        if tool in ("Read", "Bash"):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "jev-scout: call Jev before reading code. Run "
                    "`python3 ~/.claude/jev/locate.py \"<what to find>\" --root <repo> --keywords '<a|b>'` "
                    "and read only the top ranges it prints."),
            }}))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
