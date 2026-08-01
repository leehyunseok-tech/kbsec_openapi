#!/usr/bin/env bash
# 신규 클론 환경 원샷 설치 스크립트 (macOS / Linux).
# Python 확인 → uv 설치(없으면) → 의존성 전체 설치(uv sync) → config/config.py 템플릿 생성
# → manage/run/run-*.sh 실행 권한 부여까지 한 번에 처리한다.
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1

echo "============================================================"
echo " KB증권 자동매매 봇 - 프로젝트 설치"
echo "============================================================"
echo

# -- 1) Python ------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
    echo "[OK] $(python3 --version) 확인"
elif command -v python >/dev/null 2>&1; then
    echo "[OK] $(python --version) 확인"
else
    echo "[ERROR] Python이 설치되어 있지 않습니다."
    echo
    echo "  먼저 Python을 설치한 뒤 이 스크립트를 다시 실행하세요:"
    echo "    https://www.python.org/downloads/"
    echo "    (macOS: brew install python / Ubuntu·Debian: sudo apt install python3)"
    echo
    exit 1
fi

# -- 2) uv (패키지 관리자) ------------------------------------
if ! command -v uv >/dev/null 2>&1; then
    echo "[..] uv 패키지 관리자 설치 중..."
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        echo "[ERROR] curl/wget이 없어 uv를 설치할 수 없습니다. curl 설치 후 다시 실행하세요."
        exit 1
    fi
    # 방금 설치된 uv를 현재 셸에서 바로 쓸 수 있도록 (새 터미널은 셸 rc의 PATH로 잡힘)
    export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v uv >/dev/null 2>&1; then
    echo "[ERROR] uv 설치는 됐지만 PATH에서 찾지 못했습니다. 새 터미널을 열고 다시 실행하세요."
    exit 1
fi
echo "[OK] $(uv --version) 확인"

# -- 3) 의존성 설치 (.venv 생성, 프로젝트 고정 Python 자동 다운로드 포함) --
echo "[..] 프로젝트 의존성 설치 중 (uv sync)..."
if ! uv sync; then
    echo "[ERROR] uv sync 실패 — 네트워크 연결을 확인하고 다시 실행하세요."
    exit 1
fi
echo "[OK] 의존성 설치 완료 (.venv)"

# -- 4) config/config.py --------------------------------------
if [ -f "config/config.py" ]; then
    echo "[OK] config/config.py 이미 존재 — 그대로 둡니다"
else
    cp "config/config.example.py" "config/config.py"
    echo "[OK] config/config.py 생성 (템플릿 복사)"
fi

# -- 5) 실행 스크립트 권한 + OS 맞춤 통합 런처 생성 -------------
chmod +x manage/run/run-telegram.sh manage/run/run-terminal.sh manage/run/run-web.sh 2>/dev/null

# OS 특성에 맞는 통합 런처(run-kbsec-openapi.sh)를 여기서 생성한다.
# (런처는 리포에 커밋하지 않고 설치 시점에 이 스크립트가 만든다 — .gitignore 처리됨)
cat > run-kbsec-openapi.sh <<'RUNSH'
#!/usr/bin/env bash
# KB증권 Open API 통합 실행 런처 (Unix: macOS / Linux).
# OS 환경에 맞춰 manage/run/run-*.sh 를 파라미터로 골라 실행한다.
# 짝이 되는 Windows 런처는 run-kbsec-openapi.bat 이다.
#
# 사용법: ./run-kbsec-openapi [telegram | terminal | web [token]]
#   telegram     텔레그램 Agent 실행       → manage/run/run-telegram.sh
#   terminal     터미널 클라이언트 실행     → manage/run/run-terminal.sh
#   web [token]  웹 클라이언트 실행         → manage/run/run-web.sh  (기본값)
#                token 을 붙이면 run-web.sh token 과 동일 (config/config.py 앱키로 자동 로그인, 로컬 전용)
#   (옵션 생략)   web 실행 (token 없음)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$SCRIPT_DIR/manage/run"

show_options() {
  echo "KB증권 Open API 실행 옵션:"
  echo "  telegram      텔레그램 Agent 실행"
  echo "  terminal      터미널 클라이언트 실행"
  echo "  web [token]   웹 클라이언트 실행 (http://localhost:8000, 기본값)"
  echo "                └ token: config/config.py 앱키로 자동 로그인 (로컬 전용)"
}

TARGET="${1:-web}"
shift 2>/dev/null || true   # 남은 인자는 하위 run-*.sh 로 그대로 전달

case "$TARGET" in
  telegram) DESC="텔레그램 Agent";                        SCRIPT="run-telegram.sh" ;;
  terminal) DESC="터미널 클라이언트";                     SCRIPT="run-terminal.sh" ;;
  web)      DESC="웹 클라이언트 (http://localhost:8000)"; SCRIPT="run-web.sh" ;;
  -h|--help|help)
    echo "사용법: run-kbsec-openapi [telegram|terminal|web [token]] [--help|-h|help]"
    echo
    echo "세 클라이언트는 같은 명령을 공유합니다 — 어떤 방식으로 계좌와"
    echo "상호작용하고 싶은지에 따라 골라 쓰면 됩니다."
    echo
    show_options
    echo
    echo "예시:"
    echo "  ./run-kbsec-openapi                웹 클라이언트 실행 (기본값)"
    echo "  ./run-kbsec-openapi terminal       터미널 클라이언트 실행"
    echo "  ./run-kbsec-openapi telegram       텔레그램 Agent 실행"
    echo "  ./run-kbsec-openapi web token      웹 클라이언트 실행 + 자동 로그인"
    echo "  ./run-kbsec-openapi help           이 도움말 표시"
    echo
    echo "최초 실행 전: config/config.example.py 를 config/config.py 로 복사한 뒤"
    echo "실제 KB증권 API 키를 채워 넣으세요."
    echo "개별 스크립트로도 직접 실행할 수 있습니다: ./manage/run/run-*.sh"
    exit 0
    ;;
  *)
    echo "❌ 알 수 없는 옵션: $TARGET"
    echo
    show_options
    exit 1
    ;;
esac

show_options
echo
echo "▶ 선택: $TARGET — $DESC 실행 ($SCRIPT)"
echo
exec bash "$RUN_DIR/$SCRIPT" "$@"
RUNSH
chmod +x run-kbsec-openapi.sh

# 확장자 없이 `./run-kbsec-openapi` 로도 실행되도록 링크(실패 시 복사본) 생성
if ln -sf run-kbsec-openapi.sh run-kbsec-openapi 2>/dev/null; then
    :
else
    cp -f run-kbsec-openapi.sh run-kbsec-openapi 2>/dev/null && chmod +x run-kbsec-openapi 2>/dev/null
fi
echo "[OK] 통합 런처 생성: ./run-kbsec-openapi (및 run-kbsec-openapi.sh)"

# -- 6) 클라이언트별 더블클릭 실행 숏컷 -------------------------
# 웹-실행.sh / 터미널-실행.sh / 텔레그램-실행.sh — 파라미터를 몰라도
# 파일탐색기(macOS Finder / Linux 파일관리자)에서 실행 권한만 있으면 바로
# 열 수 있도록 클라이언트별로 하나씩 만든다. (파일관리자에 따라 더블클릭 시
# "실행" 대신 편집기로 열리거나 확인창이 뜰 수 있음 — 그 경우 터미널에서
# ./웹-실행.sh 처럼 직접 실행하면 된다.)
for name_script_desc in "웹-실행:run-web.sh:웹 클라이언트" "터미널-실행:run-terminal.sh:터미널 클라이언트" "텔레그램-실행:run-telegram.sh:텔레그램 Agent"; do
  IFS=: read -r shortcut_name target_script desc <<< "$name_script_desc"
  target_arg="${target_script#run-}"
  target_arg="${target_arg%.sh}"
  cat > "${shortcut_name}.sh" <<SHORTCUT
#!/usr/bin/env bash
# KB증권 ${desc} 더블클릭 실행 숏컷 (Unix: macOS / Linux).
# 실제 구현: manage/run/${target_script} (동일 동작: ./run-kbsec-openapi ${target_arg})
# 종료: 실행된 창을 닫거나 Ctrl+C.
cd "\$(dirname "\${BASH_SOURCE[0]}")" || exit 1
exec ./manage/run/${target_script} "\$@"
SHORTCUT
  chmod +x "${shortcut_name}.sh"
done
echo "[OK] 더블클릭 실행 숏컷 생성: 웹-실행.sh / 터미널-실행.sh / 텔레그램-실행.sh"

echo
echo "============================================================"
echo " 설치 완료. 다음 단계:"
echo "============================================================"
echo "  1. config/config.py 를 열어 실제 키를 입력하세요"
echo "     (real_client_key / real_client_secret 은 필수)"
echo "  2. 통합 런처로 실행 (파라미터로 클라이언트 선택):"
echo "       ./run-kbsec-openapi            # 웹 클라이언트 (기본, http://localhost:8000)"
echo "       ./run-kbsec-openapi terminal   # 터미널 클라이언트 (가장 빠른 시작)"
echo "       ./run-kbsec-openapi telegram   # 텔레그램 Agent"
echo "     (개별 스크립트도 그대로 사용 가능: ./manage/run/run-*.sh)"
echo "  3. 또는 클릭 한 번으로: 웹-실행.sh / 터미널-실행.sh / 텔레그램-실행.sh"
echo "     (종료하려면 실행된 창을 닫거나 Ctrl+C)"
echo
