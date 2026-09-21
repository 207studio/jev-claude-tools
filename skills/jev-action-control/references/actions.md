# Jev 반복 조작

관찰과 실행은 코드, 관찰된 후보 중 선택은 Jev가 맡긴다. 먼저 작업 대상·허용 동작·완료 조건을 정한다. 비활성 스킬은 로드하지 않는다.

- 브라우저: 활성 `aside-browser` 지침을 적용하고 기존 지속 탭 ID를 사용한다. CLI 사용법이 불명확할 때만 `jev-aside --help`를 확인한다. 일회성 REPL에서 만든 탭은 종료되면 없어질 수 있다.
- macOS: `jev-macos --status`에서 접근성 권한을 확인한다. 허용 앱이 전면일 때만 `jev-macos`를 사용한다. 권한 거부는 사용자에게 알리고 중단한다.
- iOS: 활성 `ios-simulator-browser` 지침으로 지정된 UDID의 serve-sim 연결을 준비한 경우 CLI 사용법이 불명확할 때만 `jev-ios --help`를 확인한다. 다른 작업의 시뮬레이터·서버를 종료하거나 재사용하지 않는다.
- 먼저 선택만 반환하는 기본 모드로 후보를 확인한다. 이미 허용된 반복 조작만 `--execute`로 실행하며, 무관한 요소나 외부 부작용을 허용하지 않는다.
- 컨트롤러가 실행 직전 상태를 재검사한다. 낮은 신뢰도·stale 상태·미지원 화면·timeout은 handoff하며 임의 좌표·CSS·명령을 생성해 우회하지 않는다.
- 사용자에게 필요한 결과는 완료 상태·실제 동작 수·남은 장애만 반환한다. 전체 접근성 트리·스크린샷·로그를 모델에 매번 재입력하지 않는다.
- `jev-gateway-codex`는 Codex 전용 도구 라우팅 게이트웨이다. Claude Code 작업은 이 게이트웨이를 경유하지 않는다.
- 설정은 `~/.local/share/codex-token-tools/features.json`; `jev-features disable <기능명>`으로 끈다. 기능명은 `browser_selector`, `computer_selector`, `ios_selector`, `tool_routing_gateway`이다.

자유 문장 입력·새 코드·이미지만 있는 화면·Pencil/AirPlay 같은 실제 기기 검증이 필요하면 해당 작업을 수행할 도구와 필요한 분석으로 돌아간다. 바이트 감소를 실제 토큰·비용·속도 개선으로 단정하지 않는다.

반복적인 시각 후보 선택을 이양할 때만 `jev-visual --spec FILE`을 사용한다. 일회성 시각 확인에는 추가 판단을 붙이지 않는다. DOM·AX·좌표·색상은 실제 수집값만 사용하며 픽셀 확인은 별도 지원 도구로 유지한다. 선택 토큰 적용은 `--apply --execute`와 현재 파일 해시를 요구한다.
