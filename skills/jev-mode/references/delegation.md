# 서브에이전트에 Jev를 쓰게 만드는 법

**Claude 전용 확장** — Codex 원본(`~/.codex/skills/jev-mode/`)에는 없다. 재이식할 때 이 파일과 SKILL.md의 링크 한 줄을 보존한다.

## 측정된 사실

iPad 앱 저장소를 다루던 다른 세션(2026-09-21)이 같은 결함 수정 워크플로를 세 번 돌렸다.

| 회차 | 지시 방식 | 실제 Jev 호출 |
|---|---|---|
| 1·2차 | 프롬프트 산문: "Jev 먼저 규칙을 따르라" | 0~1회 — 사실상 무시됨 |
| 3차 | 출력 스키마에 **required 필드** 추가: 실제 명령 출력을 그대로 붙여넣을 것 | **36/36** 항목에서 채워짐. 빈 값·ERROR 없음 |

한 세션의 세 번 실행이다. 일반 법칙이 아니라 재현된 관찰로 취급한다.

## 규칙

**"Jev를 써라"는 산문 지시는 믿지 않는다.** 서브에이전트가 Jev를 불렀는지는 **그 호출의 산출물이 아니면 채울 수 없는 required 필드**로 강제한다.

- 필드는 Jev 명령의 **원문 출력**을 요구한다. "Jev로 확인했음" 같은 자기 보고 불리언은 쓰지 않는다 — 부르지 않고도 true를 쓸 수 있다.
- 원문 형식이 정해져 있어야 부모가 코드로 검증할 수 있다. `jevq.py`는 `판정 confidence` 한 줄을 낸다.
- 부모는 받은 필드를 **코드로** 검사한다: 형식 불일치, 빈 값, `ERROR`는 그 항목을 미검증으로 표시한다. 조용히 통과시키지 않는다.

## 예시 — Workflow 스키마

```js
const FINDING = {
  type: 'object',
  required: ['file', 'line', 'claim', 'jev_claim_output'],
  properties: {
    file:  { type: 'string' },
    line:  { type: 'integer' },
    claim: { type: 'string', description: '이 줄이 무엇을 잘못하는지 한 문장' },
    jev_claim_output: {
      type: 'string',
      description: 'echo "<claim>" | python3 ~/.claude/jev/jevq.py claim <file> <line> 의 출력을 한 글자도 바꾸지 말고 붙여넣는다. 예: "supported 0.91"',
    },
  },
}
```

부모 쪽 검사:

```js
const ok = /^(supported|contradicted|cannot_tell|UNSURE) \d(\.\d+)?$/.test(f.jev_claim_output)
if (!ok) f.status = 'unverified'   // 형식이 안 맞으면 Jev를 실제로 안 부른 것으로 본다
```

## 판정 결합은 코드가

Jev 판정과 검증자 반박을 함께 받으면 결합 규칙을 코드에 둔다. 예:

- Jev `supported` ≥0.8 **그리고** 검증자가 반박 못 함 → 확정
- Jev `contradicted` ≥0.8 → 기각
- Jev가 강하게 지지하는데 검증자가 기각, 또는 그 반대 → **사람이 본다.** 둘 중 하나를 골라 덮지 않는다
- `UNSURE`·`cannot_tell`·`ERROR` → 더 날카로운 질문으로 2차, 그래도 안 되면 미검증으로 남긴다

## 관련

- 워크플로 에이전트는 출력 스키마로 강제한다. `Agent` 도구 에이전트는 스키마가 없으니 커스텀 에이전트의 frontmatter 훅으로 강제한다 — 아래 "Agent 도구로 띄운 에이전트" 참조.
- 서브에이전트 모델 티어는 `~/.claude/jev/agent-tier.json` — 부모 모델을 그대로 상속하지 않게 한다.

## Agent 도구로 띄운 에이전트 — 스키마가 없다 (2026-09-22)

Workflow 밖에서 `Agent` 도구로 띄운 에이전트에는 required 출력 필드를 걸 수단이 없다(공식 문서 확인). 그래서 산문으로 시키게 되고, 산문은 무시된다.

| 실측 (iPad 앱 저장소 세션, 같은 원인 위치 찾기) | Jev 호출 | 시간 | 토큰 |
|---|---:|---:|---:|
| Explore(sonnet) + 산문 "Read 전에 jevq로 먼저 물어라" | **0** | 6분 21초 | 11.3만 |
| 부모가 직접 chunk → 키워드 거름 → jev-mode batch | — | **7.3초** | — |

같은 세션의 앞선 기록: 산문 지시만 준 워크플로 에이전트 36개 합쳐 jevq 5회, required 필드를 건 단계는 102/102.

**규칙:**

1. **위치 찾기는 위임하지 않는다.** 부모가 `python3 ~/.claude/jev/locate.py "<찾을 것>" --root <저장소> --keywords 'a|b'`를 직접 부르고, 출력된 범위만 읽는다.
2. 위치 찾기를 꼭 위임해야 하면 **내장 Explore가 아니라 `jev-scout`** 을 쓴다. Explore·Plan은 CLAUDE.md를 건너뛰어 Jev 정책 자체를 모른다. 커스텀 에이전트는 CLAUDE.md를 받는다.
3. `jev-scout`은 frontmatter의 PreToolUse 훅(`~/.claude/jev/scout-gate.py`)으로 **Jev를 한 번 부르기 전에는 Read와 `cat`·`head`·`sed`류 읽기를 차단**한다. 산문이 아니라 기계적 강제다.

**검증 (2026-09-22, 실제 서브에이전트):** frontmatter 훅은 서브에이전트 안에서 **그 서브에이전트 자신의 agent_id로** 실행됐다. Jev 지시가 전혀 없는 프로브 에이전트는 첫 Read가 차단됐고, 차단 메시지대로 locate.py를 부른 뒤에야 읽을 수 있었다. `jev-scout` 자체는 두 번 다 차단 없이 스스로 Jev를 먼저 불렀다.

**안 되는 것:** `SubagentStop`은 exit 2를 무시한다 — 서브에이전트가 이미 끝난 뒤라 정보용이다. "Jev를 안 불렀으면 종료를 막고 되돌려 보내기"는 불가능하다. 강제는 시작 전·도중(PreToolUse)에만 걸린다.

"서브에이전트는 pre-action 훅을 받지 않는다"는 jev-mode 저자의 **Codex** 관측이다. Claude Code의 커스텀 에이전트 frontmatter 훅에는 해당하지 않는다(위 검증). 설정 파일(settings.json)의 전역 훅이 내장 에이전트에 걸리는지는 확인하지 않았다.
