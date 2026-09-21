# Jev 배치 판단

항목 원문은 코드가 읽고 요청 파일도 코드가 만든다. 에이전트 컨텍스트에는 개수·사용량·미해결 건수만 반환한다. 경계 있는 의미 판단이 5개 이상 반복되면 컨텍스트에서 직접 분류하거나 표본을 보고 전체를 추정하지 말고 `jev-mode batch`로 보낸다.

## 설치 상태와 pip 함정

공유 CLI는 이미 설치되어 있다: 체크아웃 `~/.local/share/jev-mode`, 실행기 `~/.local/bin/jev-mode`, 자격증명 경로 `~/.jev-router.env`를 사용한다. 래퍼가 `TYPESAFE_ENV_FILE`을 설정하므로 키를 읽어 출력하거나 요청 파일에 넣지 않는다. 공유 체크아웃·래퍼·키·Claude Code 설정을 수정하거나 재설치하지 않는다.

연결이 미확인되었거나 설정이 변경된 때만 `jev-mode check`로 `reachable: true`, `api_key_present: true`, 기대 모델 `jev-1.13.0`을 확인한다. 확인되지 않으면 중단하고 상태만 보고한다. 직접 명령이 기존 훅에 막히면 활성 `jev-verify`의 `plan --spec` 다음 `run --spec --execute`를 사용하며 차단을 우회하지 않는다.

이 Mac의 기본 pip 21.2.4/Python 3.9.6으로 `pip install jev-mode`, Git URL pip 설치 또는 다른 PEP 621 패키지 설치를 실행하지 않는다. 성공 문구와 함께 코드 없는 `UNKNOWN-0.0.0` 메타데이터만 생길 수 있다. `pip3 show UNKNOWN`으로 확인하고 해당 잔재가 있을 때만 `pip3 uninstall -y UNKNOWN`으로 제거한다. 다른 허용된 pip 설치도 같은 Python 환경의 `python3 -c "import <module>"`과 `which <command>`가 확인되기 전에는 성공으로 보고하지 않는다.

## 요청과 결과

- 호출당 레코드 하나를 사용한다. 여러 레코드를 배열 state 하나에 넣으면 전체에 대한 한 번의 읽기로 합쳐지므로 사용하지 않는다. 한 레코드의 독립적인 여러 질문은 한 요청에 함께 둘 수 있다.
- 분류에는 짧고 결정적인 criteria를 담은 `choice` 질문 하나를 쓴다. atomic `noul` 여러 개를 argmax로 재조합하지 않는다. 저자의 합성 실험 96.1% 대 84.5%는 질문 설계 근거이며 이 환경의 정확도 보장은 아니다.
- 가중치·임계값·답 조합은 코드로 처리한다. 산문·코드 작성·설명·산술·개수 세기·크기 비교·날짜 비교는 Jev에 맡기지 않는다.
- 낮은 confidence를 조용히 수용하지 않는다. 코드가 해당 레코드만 골라 더 선명한 criteria로 2차 패스를 최대 한 번 실행하고, 원래 결과와 재판단을 구분한다. 여전히 불확실하거나 요청이 실패하면 미해결로 남긴다. 실행 권한이나 선택지 범위를 자동으로 넓히지 않는다.
- 항목·답변 파일을 `cat`, `head`, 도구 출력 또는 서브에이전트 메시지로 컨텍스트에 넣지 않는다. 명령 출력도 4000바이트 이내로 제한하고 실패는 비밀정보를 제거한 마지막 오류부터 확인한다. 기록과 종료코드는 코드로 보존한다.

```sh
jev-mode batch --items /absolute/path/items.jsonl --questions /absolute/path/questions.json --out /absolute/path/answers.jsonl --pool 4
```

현재 호스트의 승인·검증 정책을 따른다. 강제 경유가 켜진 경우에만 등록 `jev-verify` wrapper를 사용한다. 예제 확인에는 공유 체크아웃의 `examples/items.jsonl`, `examples/questions.json`을 그대로 사용하고, 기존 결과 파일이 있으면 보존한다. 입력·출력 원문을 표시하지 말고 배치 요약만 읽는다.

## 계기판과 해석

`items`, `ok`, `failed`, `input_tokens`, `text_tokens`를 기록한다. `text_tokens`를 텍스트 규모 계기판으로 쓰되 v1.2.0 구현은 **입력 항목 텍스트의 토큰 추정 합계**를 반환한다. 에이전트 컨텍스트에 실제 유입된 토큰의 측정값이 아니며, 항목이 많아지면 원문을 전혀 출력하지 않아도 커진다. 원문 출력 0건을 별도로 유지한다. 실제 절감량은 동일 작업의 대조 실행과 비교한다.

Claude Code에서 사용자가 제공한 예제 기준은 `items=8, ok=8, failed=0, input_tokens=3703, text_tokens=83`이다. 실제 실행값을 별도로 보고하고 일치를 가정하지 않는다. 78% 절감이나 정확도 우위를 일반화하지 않는다. 저자도 합성 코퍼스에서 정확도 parity를 보고했으므로 실제 데이터로 다시 측정한다.

## 서브에이전트와 선택 훅

자식에게 좁은 범위·완료 조건·필요한 제약만 전달한다. 매 단계 Jev 호출을 강제하지 않는다. Jev를 사용했다는 주장을 확인할 때만 배치 기록이나 `jev-mode coverage --task <session-id>`를 조사하며 미계측을 성공으로 단정하지 않는다.

저자가 2026-09-18에 관측한 Codex 자식 세션은 339개/29,146 tool call에서 훅 호출 0회였다. 이를 현재 호스트의 자동 보장으로 일반화하지 않는다. v1.2.0 `coverage`는 `codex-typesafe` 호출 문자열과 별도 hook trace를 세므로 이 환경의 모든 `jev-mode`·`jev-verify` 호출을 포괄한다고 가정하지 않는다. trace가 없거나 도구명이 맞지 않으면 커버리지는 미확인으로 보고하고 실제 배치 기록과 대조한다.

SessionStart/UserPromptSubmit/SubagentStart 알림 훅은 선택 사항이다. 기존 훅과 승인 흐름을 보존하고 사용자의 명시적 확인 전에는 활성화하지 않는다. 공유 CLI·Claude 설정에 영향을 주지 않도록 호스트별로 분리된 `JEV_MODE_CONFIG` 경로를 사용한다(Codex와 공유하지 않는다). 마켓플레이스 등록이나 별도 `jev-mode gate` 설치는 하지 않는다. 비활성 스킬을 의존성으로 다시 로드하지 않는다.

원본: [ddfeyes/jev-mode](https://github.com/ddfeyes/jev-mode/tree/97615aa5cc14586488c11f6644a5b845827234c6) (MIT). 기존 `jev-verify`·`jev-action-control` 형식(Codex에서 먼저 작성, Claude로 이식)과 사용자 환경에 맞춘 지침이다.
