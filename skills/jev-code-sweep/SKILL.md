---
name: jev-code-sweep
description: Sweep a whole repository or large change for likely runtime defects by having Jev triage every ~100-line chunk before any agent reads code, then send only the top clusters to reviewers. Use for "review the whole codebase", pre-release defect sweeps, or when a review would otherwise load many files into context.
---

# Jev 우선 코드 검수 스윕

저장소 전체를 에이전트가 읽기 **전에** Jev가 청크마다 결함 가능성을 판정하고, 상위만 검수 에이전트에게 넘긴다.
파일 몇 개·알려진 버그 하나를 볼 때는 쓰지 않는다 — 그건 그냥 읽는다.

도구는 `~/.claude/jev/`에 있다: `chunk.py`(청킹), `jevq.py`(코드 슬라이스 판정·주장 대조). 둘 다 코드 본문을 출력하지 않는다.

1. 청킹 → 2. `jev-mode batch`로 1차 판정 → 3. 코드가 확률 조합·임계값 → 4. 상위를 묶어 검수 에이전트에 배정 → 5. 발견마다 `jevq claim` + 검증자 반박, 결합은 코드가.
명령·임계값·질문은 [레시피](references/recipe.md), 질문은 [1차](references/questions.json)·[2차](references/questions-pass2.json).

**검수 에이전트에게 Jev 사용을 산문으로 지시하지 않는다.** 출력 스키마의 required 필드로 강제한다 — [jev-mode의 위임 규칙](../jev-mode/references/delegation.md).
에이전트 모델은 `~/.claude/jev/agent-tier.json`으로 정한다. 부모가 Fable/Opus면 상속시키지 않는다.
