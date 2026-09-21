---
name: jev-action-control
description: Run explicitly authorized repeated browser, macOS or iOS actions with bounded Jev choices.
---

# 허용된 반복 UI 조작

같은 정책으로 여러 UI 단계를 반복할 때 쓴다. 단일 클릭·일회성 시각 확인에는 추가 Jev 판단을 붙이지 않는다.
대상·허용 동작·완료 조건을 정하고 필요한 플랫폼의 [연결·실행 규칙](references/actions.md)만 확인한다. 브라우저는 활성 Aside를 우선한다.
실행 직전 상태를 다시 확인하고 낮은 신뢰도·권한 거부·stale 상태에서는 멈춘다. UNKNOWN이나 미확인 픽셀을 성공으로 바꾸지 않는다.
실제 픽셀 확인과 코드 작성은 해당 지원 도구로 수행한다.
