# Jev 반복 조작

관찰과 실행은 코드, 관찰된 후보 중 선택은 Jev가 맡긴다. 먼저 작업 대상·허용 동작·완료 조건을 정한다. 비활성 스킬은 로드하지 않는다.

- 브라우저: 활성 `aside-browser` 지침을 적용하고 기존 지속 탭 ID를 사용한다. CLI 사용법이 불명확할 때만 `jev-aside --help`를 확인한다. 일회성 REPL에서 만든 탭은 종료되면 없어질 수 있다.
- macOS: `jev-macos --status`에서 접근성 권한을 확인한다. 허용 앱이 전면일 때만 `jev-macos`를 사용한다. 권한 거부는 사용자에게 알리고 중단한다.
- iOS: Claude Code에서는 `~/.claude/jev/serve-sim.sh`로 serve-sim을 띄운 뒤 `jev-ios`를 쓴다 — 아래 "iOS (Claude Code)" 참조. 다른 작업의 시뮬레이터·서버를 종료하거나 재사용하지 않는다.
- 먼저 선택만 반환하는 기본 모드로 후보를 확인한다. 이미 허용된 반복 조작만 `--execute`로 실행하며, 무관한 요소나 외부 부작용을 허용하지 않는다.
- 컨트롤러가 실행 직전 상태를 재검사한다. 낮은 신뢰도·stale 상태·미지원 화면·timeout은 handoff하며 임의 좌표·CSS·명령을 생성해 우회하지 않는다.
- 사용자에게 필요한 결과는 완료 상태·실제 동작 수·남은 장애만 반환한다. 전체 접근성 트리·스크린샷·로그를 모델에 매번 재입력하지 않는다.
- `jev-gateway-codex`는 Codex 전용 도구 라우팅 게이트웨이다. Claude Code 작업은 이 게이트웨이를 경유하지 않는다.
- 설정은 `~/.local/share/codex-token-tools/features.json`; `jev-features disable <기능명>`으로 끈다. 기능명은 `browser_selector`, `computer_selector`, `ios_selector`, `tool_routing_gateway`이다.

자유 문장 입력·새 코드·이미지만 있는 화면·Pencil/AirPlay 같은 실제 기기 검증이 필요하면 해당 작업을 수행할 도구와 필요한 분석으로 돌아간다. 바이트 감소를 실제 토큰·비용·속도 개선으로 단정하지 않는다.

반복적인 시각 후보 선택을 이양할 때만 `jev-visual --spec FILE`을 사용한다. 일회성 시각 확인에는 추가 판단을 붙이지 않는다. DOM·AX·좌표·색상은 실제 수집값만 사용하며 픽셀 확인은 별도 지원 도구로 유지한다. 선택 토큰 적용은 `--apply --execute`와 현재 파일 해시를 요구한다.

## iOS (Claude Code)

**Claude 전용 섹션** — Codex 원본과 다르다. 재이식할 때 보존한다.

`jev-ios`는 "실행 중이고 등록된 serve-sim 0.1.46"을 요구한다. Codex에서는 `build-ios-apps` 플러그인의 `ios-simulator-browser` 스킬이 serve-sim을 띄우는데, Claude Code에는 그 스킬이 없다. 대신 `~/.claude/jev/serve-sim.sh`가 그 일을 한다.

```sh
~/.claude/jev/serve-sim.sh start <UDID>      # helper 기동, 127.0.0.1 고정. 마지막 줄이 jev-ios --url 값
jev-ios --udid <UDID> --url <그 주소> --bundle <번들ID> --element <AX 라벨> --intent "<목표>"
~/.claude/jev/serve-sim.sh stop <UDID>       # 끝나면 반드시 이 UDID만 끈다
```

- **남의 시뮬레이터에 붙지 않는다.** `start`는 이미 serve-sim이 떠 있는 UDID를 거부한다 — 다른 작업의 것일 수 있다. 부팅된 시뮬레이터가 다른 세션의 것인지 모르면 쓰지 말고 묻는다.
- `start`는 시뮬레이터를 부팅하지 않는다. 부팅은 `xcrun simctl boot` 또는 `mcp__Claude_Code_iOS_Simulator__control`로 따로 한다.
- 바인딩은 127.0.0.1 고정이다. serve-sim의 preview 서버는 토큰 보호된 셸 실행 경로를 열기 때문에 LAN(0.0.0.0) 노출은 하지 않는다. `start`는 `--detach`로 helper만 띄운다.
- `stop`은 UDID가 있어야만 동작한다. 전체 종료(`--kill` 단독)는 다른 작업의 미러까지 끄므로 하지 않는다.
- 캐시된 0.1.46만 쓴다. `npx serve-sim@latest`로 새 코드를 받지 않는다 — jev-ios는 0.1.46이 아니면 거부한다.

**검증됨 (2026-09-21, 테스트용 iPhone 15 / iOS 27.0, 설정 앱):** `start → url → jev-ios --execute --done-label` 전 과정이 돌았다. 후보 4개 중 Jev가 `일반`을 0.96으로 골랐고, 탭 후 화면이 `설정` → `일반`으로 바뀌었으며, `{"status":"done","reason":"done_label_observed","steps":1}`로 끝났다. 서버는 127.0.0.1에만 열렸고 `stop` 후 남은 프로세스가 없었다.

정상 사용 순서:

```sh
~/.claude/jev/serve-sim.sh start <UDID>                  # 마지막 줄 = URL
# 화면이 준비될 때까지 기다린다 — curl -s <URL>/helper/<UDID>/ax 의 Heading 라벨이 기대한 화면인지 확인
jev-ios --udid <UDID> --url <URL> --bundle <번들ID> \
  --element "<라벨1>" --element "<라벨2>" ... \
  --intent "<목표>" --execute --done-label "<도착 화면에만 있는 라벨>"
~/.claude/jev/serve-sim.sh stop <UDID>
```

**테스트에서 실제로 걸린 함정:**

1. **화면이 준비되기 전에 부르면 아무것도 안 한다.** 앱을 띄우고 3초 만에 불렀더니 AX 트리가 비어 `steps: 0`으로 멈췄다. jev-ios는 한 번 관찰하고 끝나지, 준비될 때까지 기다리지 않는다. `/helper/<UDID>/ax`의 Heading이 기대한 화면인지 먼저 확인한다.
2. **라벨은 시뮬레이터 언어 그대로, 정확히 일치해야 한다.** 한국어 맥에서 만든 시뮬레이터는 라벨이 한국어다(`General`이 아니라 `일반`). 영어 라벨을 주면 후보 0개로 멈춘다. 일부 라벨에는 일반 공백 대신 줄바꿈 없는 공백(`\xa0`)이 들어 있다(예: `Apple\xa0계정`). 라벨은 `/ax` 출력에서 복사한다.
3. **`--done-label`을 안 주면 성공해도 실패처럼 보인다.** 탭이 성공해 화면이 바뀌었는데도 `{"status":"stopped","reason":"observation_or_provider_failed","executed":true}`가 나왔다 — 새 화면에 허용 후보가 없어서다. 항상 `--done-label`을 준다. 그리고 그 라벨은 **출발 화면에는 없고 도착 화면에만 있어야** 한다. 메인 화면에도 있는 `일반`을 쓰면 탭하기 전에 끝난 것으로 판정될 수 있어서, 일반 화면에만 있는 `정보`를 썼다.
4. **출력의 `E3` 같은 번호는 내가 준 `--element` 순서가 아니다.** 후보를 요소 ID로 정렬한 순서다. 번호만 보고 어느 라벨인지 단정하지 말고, 도착 화면으로 확인한다.

jev-ios가 스스로 거부하는 경우도 있다: 허용 라벨이 화면에 두 번 이상 있으면(`ambiguous_allowed_element`), 화면 밖에 있으면 후보에서 뺀다.

### jev-ios가 안 될 때

`jev-ios`는 serve-sim 자체의 접근성 경로(`/helper/<UDID>/ax`)를 쓴다. 네이티브 `mcp__Claude_Code_iOS_Simulator__control`의 `inspect`와는 다른 경로라, 한쪽이 막혀도 다른 쪽은 될 수 있다 — 아직 확인된 사실은 아니다.

둘 다 안 되면 Jev 선택 경로를 쓸 수 없다. Jev는 텍스트 모델이라 코드가 수집한 AX 후보가 있어야 고를 수 있다. 스크린샷 판독 + 좌표 탭으로 직접 진행하고, 보고서에 "Jev 선택 아님, 직접 시각 판독"이라고 적는다. Jev가 고른 것처럼 쓰지 않는다.

관측(iPad 앱 저장소를 다루던 다른 세션, 2026-09-21): 그 앱에서 네이티브 `inspect`가 재시도·재실행·재부팅 후에도 계속 "not available right now"였다. 원인은 확인되지 않았다. 그때는 serve-sim 런처가 없어 `jev-ios`는 시도되지 않았다.
