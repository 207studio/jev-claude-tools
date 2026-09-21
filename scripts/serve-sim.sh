#!/bin/bash
# Claude Code용 serve-sim 런처 — jev-ios가 요구하는 "실행 중이고 등록된 serve-sim 0.1.46"을 띄운다.
# Codex에서는 build-ios-apps 플러그인의 ios-simulator-browser 스킬이 이 일을 한다. Claude Code에는 그 스킬이 없어 따로 둔다.
#
#   serve-sim.sh start UDID   — 이 UDID에 helper를 띄운다(127.0.0.1 고정, --detach)
#   serve-sim.sh url   UDID   — jev-ios --url 에 넣을 주소를 출력한다
#   serve-sim.sh list         — 실행 중인 serve-sim 목록
#   serve-sim.sh stop  UDID   — 이 UDID의 것만 끈다. 전체 종료는 하지 않는다
#
# 안전 규칙
# - 캐시된 0.1.46만 쓴다(jev-ios가 이 경로·버전을 검사한다). npx @latest로 새 코드를 받지 않는다.
# - 바인딩은 127.0.0.1로 고정한다. serve-sim의 preview 서버는 토큰 보호된 셸 실행 경로를 열기 때문에
#   0.0.0.0(LAN 노출)은 허용하지 않는다.
# - 이미 다른 작업이 serve-sim을 띄운 UDID에는 start하지 않는다. 남의 스트림을 가로채거나 끄지 않는다.
# - UDID 없는 stop은 거부한다(다른 작업의 시뮬레이터 미러까지 꺼진다).
set -uo pipefail

SERVE_SIM="${JEV_SERVE_SIM:-$HOME/.npm/_npx/952f9bf55a4c6785/node_modules/serve-sim/dist/serve-sim.js}"
NODE=/usr/local/bin/node
UUID_RE='^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'

die() { echo "serve-sim.sh: $*" >&2; exit 1; }

check_binary() {
  [ -f "$SERVE_SIM" ] || die "serve-sim 없음: $SERVE_SIM — 'npx --yes serve-sim@0.1.46 --version' 로 캐시를 만든 뒤 경로를 확인할 것"
  local v; v=$("$NODE" "$SERVE_SIM" --version 2>/dev/null)
  [ "$v" = "0.1.46" ] || die "serve-sim 버전이 0.1.46이 아님(현재: ${v:-알수없음}). jev-ios는 0.1.46만 받는다"
}

check_udid() {
  [ -n "${1:-}" ] || die "UDID가 필요하다"
  [[ "$1" =~ $UUID_RE ]] || die "UDID 형식이 아님: $1"
  xcrun simctl list devices booted 2>/dev/null | grep -qi "($1) (Booted)" \
    || die "부팅된 시뮬레이터가 아님: $1 — 이 스크립트는 시뮬레이터를 부팅하지 않는다"
}

running_for() {  # 해당 UDID로 등록된 스트림이 있으면 0
  "$NODE" "$SERVE_SIM" --list "$1" -q 2>/dev/null | "$NODE" -e '
    let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
      try{const j=JSON.parse(s);const a=Array.isArray(j)?j:(Array.isArray(j.streams)?j.streams:[j]);
        process.exit(a.some(x=>x&&x.running!==false&&String(x.device||"").toUpperCase()===process.argv[1].toUpperCase())?0:1);
      }catch(e){process.exit(1)}})' "$1"
}

cmd="${1:-}"; udid="${2:-}"
case "$cmd" in
  start)
    check_binary; check_udid "$udid"
    if running_for "$udid"; then
      die "이 UDID에는 이미 serve-sim이 떠 있다. 다른 작업의 것일 수 있어 건드리지 않는다. 내 것이면 'url'로 주소만 받을 것"
    fi
    "$NODE" "$SERVE_SIM" --host 127.0.0.1 --detach -q "$udid" >/dev/null 2>&1 \
      || die "serve-sim 시작 실패"
    for _ in 1 2 3 4 5 6 7 8 9 10; do running_for "$udid" && break; sleep 0.5; done
    running_for "$udid" || die "시작했지만 등록이 확인되지 않음 — 'list'로 확인할 것"
    echo "started $udid"
    "$0" url "$udid"
    ;;
  url)
    check_binary; [ -n "$udid" ] || die "UDID가 필요하다"
    "$NODE" "$SERVE_SIM" --list "$udid" -q 2>/dev/null | "$NODE" -e '
      let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
        try{const j=JSON.parse(s);const a=Array.isArray(j)?j:(Array.isArray(j.streams)?j.streams:[j]);
          const m=a.find(x=>x&&String(x.device||"").toUpperCase()===process.argv[1].toUpperCase());
          if(!m||!m.url){console.error("등록된 스트림 없음");process.exit(1)}
          const u=new URL(m.url);
          if(!["127.0.0.1","localhost","::1","[::1]"].includes(u.hostname)){console.error("로컬 주소가 아님: "+u.hostname);process.exit(1)}
          console.log(u.origin);
        }catch(e){console.error("목록 해석 실패");process.exit(1)}})' "$udid"
    ;;
  list)
    check_binary
    "$NODE" "$SERVE_SIM" --list 2>&1 | head -40
    ;;
  stop)
    check_binary
    [ -n "$udid" ] || die "UDID 없이 끄지 않는다 — 다른 작업의 시뮬레이터 미러까지 꺼진다"
    [[ "$udid" =~ $UUID_RE ]] || die "UDID 형식이 아님: $udid"
    "$NODE" "$SERVE_SIM" --kill "$udid" >/dev/null 2>&1 || true
    echo "stopped $udid"
    ;;
  *)
    sed -n '5,8p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
