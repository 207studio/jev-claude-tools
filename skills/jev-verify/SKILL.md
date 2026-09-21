---
name: jev-verify
description: Decide whether an optional repeated verification is worth running.
---

# 선택적 재검증 판단

변경 없는 재검증을 추가로 할지 애매할 때만 쓴다. 필수 검증·첫 관련 테스트·종료코드 확인을 위해 별도 Jev 판단을 만들지 않는다.
코드·입력 변경, 새 실패, 명시된 요구가 없으면 이미 충분한 검증을 반복하지 않는다.
선택적 판단이 필요하면 [spec과 실행 흐름](references/verification.md)을 읽는다. 원본 로그·종료코드와 Jev 평가는 구분한다.
호스트가 강제 경유를 켠 경우에는 등록 wrapper를 사용한다; 차단·승인·필수 검증을 우회하지 않는다.
