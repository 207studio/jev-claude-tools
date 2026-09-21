---
name: jev-mode
description: Batch 5+ fixed-label judgments without loading record text into agent context.
---

# Jev 배치 판단

고정 선택지로 분류할 항목이 5건 이상일 때 쓴다. 사실 조회·산술·코드 작성·일회성 분석에는 쓰지 않는다.
코드가 원문을 읽고 요청을 만든다; 에이전트 컨텍스트에는 개수·사용량·미해결 건수만 반환한다.
호출당 레코드 하나와 명확한 choice를 사용하며 가중치·임계값은 코드가 소유한다. 낮은 confidence와 UNKNOWN을 숨기지 않는다.
배치가 필요할 때만 [요청 형식·실행·계측](references/batch.md)을 읽는다. text_tokens는 입력 추정량이며 에이전트 컨텍스트 유입 실측이 아니다.
공유 CLI는 이미 설치되어 있다. 연결 미확인·설정 변경 때만 jev-mode check를 실행하고 실패하면 멈춘다; 재설치하거나 공유 파일을 수정하지 않는다.
