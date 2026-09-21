# 레시피

iPad 앱 저장소를 다루던 다른 세션이 2026-09-21 하루에 세 번 재사용한 절차를 옮긴 것이다. 도구의 하드코딩 경로만 일반화했고 절차·질문·임계값은 그대로다.
임계값은 그 저장소에서 쓴 값이다. 다른 저장소에서는 출발점으로만 쓰고 결과를 보며 조정한다.

## 1. 청킹

```sh
cd <저장소>
python3 ~/.claude/jev/chunk.py /tmp/sweep/items.jsonl --exclude docs/ --exclude tests/
```

- 기본 확장자: .swift .py .mjs .js .ts .tsx .sh .c .h .go .rs .gd .cs — `--ext`로 바꾼다
- 항상 제외: vendor/ node_modules/ dist/ build/ Pods/ .build/ 와 *.min.js, 한 줄 4000자 초과 파일
- 저장소 전용 제외는 `--exclude PREFIX`를 반복해서 준다
- 출력은 `files N chunks M skipped K` 한 줄뿐이다. 레코드 본문을 컨텍스트에 들이지 않는다

## 2. 1차 판정

```sh
jev-mode batch --items /tmp/sweep/items.jsonl --questions questions.json --out /tmp/sweep/r1.jsonl --pool 6
```

`questions.json`의 세 질문(`risk`·`kind`·`pinpoint`)을 한 호출에 묻는다 — 항목 하나에 질문 여럿은 한 번에 보내는 게 jev-mode의 권장 형태다.
**`instructions` 첫 문장의 도메인 설명을 저장소에 맞게 바꾼다.** 예시는 iPad 앱(Swift)용이다.

## 3. 코드로 조합·2차

점수 조합은 코드가 한다. 아래는 원 세션이 실제로 쓴 식이다(변수명 그대로, 원 세션이 직접 알려줌).

**1차** — `risk`와 `pinpoint`만 쓴다. `kind`는 점수에 안 쓰고 4단계 배정에만 쓴다.

```python
pd = a["risk"]["probabilities"].get("defect", 0)
py = a["pinpoint"]["probabilities"].get("yes", 0)
score = 0.5 * pd + 0.5 * py
```

`fragile`에 따로 가중치를 두지 않는다. 3지선다 분포에서 `defect`만 뽑아 쓰면 `fragile`로 간 확률은 자연히 깎인다.
임계값 `score >= 0.4` → 원 세션에서 813청크 중 282개 통과.

**2차** — 통과분에만 두 질문을 더 묻고 1차 점수를 보정한다.

```python
pu    = a["guard"]["probabilities"].get("unguarded", 0)
pship = a["ships"]["probabilities"].get("user_facing", 0)
final = b["score"] * (0.4 + 0.6 * pu) * (0.5 + 0.5 * pship)
```

질문 원문: [questions-pass2.json](questions-pass2.json) (1차는 [questions.json](questions.json)).

- `guard` — 청크에서 가장 위험한 연산 하나를 찾아 가드 여부를 묻는다. 선택지 `unguarded` / `guarded` / `benign`(위험한 연산 없음). 점수엔 `unguarded` 확률만 쓴다 — `guarded`나 `benign`이어도 **0.4배까지만** 깎고 0으로 죽이지 않는다. Jev 판정 자체가 틀릴 수 있어서다
- `ships` — 사용자에게 노출되는 경로인가. 선택지 `user_facing` / `dev_only`. 개발자 전용이면 0.5배, 사용자 노출이면 그대로
- **`ships.user_facing`의 criteria는 저장소마다 바꾼다.** 예시는 "교사의 iPad에서 도는 앱 기능 코드"다. 1차 `questions.json`의 도메인 첫 문장도 마찬가지다

임계값 `final >= 0.25`~`0.3`, 검수 예산에 따라 정한다. 원 세션: 0.25 이상 117청크 → 17묶음 배정.

원 세션 흐름을 숫자로: **813 청크 → 1차 282 → 2차 117 → 17 묶음.** 에이전트가 읽은 코드는 117청크분이다.

- 임계값을 넘은 청크만 더 날카로운 질문으로 2차를 돌린다
- 1차 confidence가 낮은 청크는 버리지 않고 2차로 보낸다 — 조용히 `sound`로 수용하지 않는다
- 청크 텍스트는 이 단계에서도 읽지 않는다. id와 확률만 다룬다

## 4. 묶어서 배정

- 상위 청크를 파일·모듈 단위로 묶어(cluster) 검수 에이전트 하나당 한 묶음을 준다
- 에이전트에게는 청크 id(`path:START-END`)와 `kind` 판정만 준다. 본문은 에이전트가 직접 읽는다
- 에이전트 티어: `jev-mode ask --state-file <역할설명> --questions-file ~/.claude/jev/agent-tier.json`.
  원 세션의 2차 티어 질문은 "가드 유무를 한두 파일 안에서 판정" = sonnet, "여러 파일의 상태·타이밍을 조합해 어디에도 적혀 있지 않은 실패 순서를 구성" = opus 였다

## 5. 발견 대조

에이전트가 낸 발견마다:

```sh
echo "<주장 한 문장>" | python3 ~/.claude/jev/jevq.py claim <file> <line>
# -> supported 0.91 | contradicted 0.88 | cannot_tell 0.62 | UNSURE 0.31 | ERROR 0.0
```

- 이 출력을 에이전트 스키마의 required 필드로 받는다 — [위임 규칙](../../jev-mode/references/delegation.md)
- 별도 검증 에이전트가 반박을 시도한다
- 결합은 코드가: Jev 강한 지지 + 반박 실패 → 확정 / Jev 강한 반박 → 기각 / **둘이 갈리면 사람이 본다**

`jevq ask FILE START END "질문"`은 특정 구간에 대해 예/아니오가 필요할 때 쓴다. 220줄 이하만 받는다.

## 하지 않는 것

- 전체 파일을 먼저 읽고 나서 Jev에 묻기 — 절감이 사라진다
- `text_tokens`를 절감 증거로 보고하기 — 입력 크기 추정일 뿐이다. 절감은 같은 작업의 대조 실행과 비교해야 안다
- Jev 판정만으로 수정 착수 — 판정은 선별이고, 수정은 실제 코드를 읽은 검수 결과로 한다
