# Spec과 선택적 실행

현재 task, goal, cwd, files, argv, timeout_ms를 작은 spec에 적는다. scope_complete는 호출자의 범위 주장이다. mandatory를 거짓으로 바꿔 SKIP을 유도하지 않는다.

판단 기능이 활성화되어 있고 선택적 재검증이 필요할 때 `jev-verify plan --spec FILE` 후 `jev-verify run --spec FILE --execute`를 사용한다. 동일 fingerprint의 유효한 캐시를 재사용한다. NARROW는 미리 제공한 narrow_argv만 선택할 수 있다.

verification_gate가 꺼져 있으면 wrapper는 필요성 판단 API를 호출하지 않고 기존 코드 정책으로 실행 여부를 정한다. verification_assessment가 꺼져 있으면 결과 평가도 호출하지 않는다. SKIP·UNKNOWN·비활성 평가를 테스트 통과로 표시하지 않는다.

선택적 재검증에 Jev 판단이 실제로 필요하면 해당 plan/run 프로세스에만 `JEV_VERIFICATION_GATE_ENABLED=1`을 지정한다. 결과 의미가 불명확할 때만 `JEV_VERIFICATION_ASSESSMENT_ENABLED=1 jev-verify assess --spec FILE --log LOG --exit-code N`을 사용한다. 전역 설정을 켜 두거나 같은 종료코드를 다시 판정하지 않는다.

원본 로그와 실제 종료코드는 디스크에 보존하며 stdout은 4000바이트 이내로 제한한다. 실패 시 마지막 오류와 관련 범위만 읽는다. 결과의 의미가 불명확할 때만 bounded 근거를 Jev에 보내며 로그 전체를 보내지 않는다.

verification_enforcement가 켜진 호스트는 등록된 절대경로 wrapper를 요구한다. 다른 인터프리터·셸·도구로 차단을 우회하지 않는다. 이 절차는 호스트 권한·사용자의 중지·필수 테스트를 대체하지 않는다.
