#!/usr/bin/env bash
# 신규 클론 환경 원샷 설치 스크립트 (macOS / Linux).
# Python 확인 → uv 설치(없으면) → 의존성 전체 설치(uv sync) → config/config.py 템플릿 생성
# → run-*.sh 실행 권한 부여까지 한 번에 처리한다.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

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

# -- 5) 실행 스크립트 권한 ------------------------------------
chmod +x run-main.sh run-terminal.sh run-web.sh 2>/dev/null
echo "[OK] run-*.sh 실행 권한 부여"

echo
echo "============================================================"
echo " 설치 완료. 다음 단계:"
echo "============================================================"
echo "  1. config/config.py 를 열어 실제 키를 입력하세요"
echo "     (real_client_key / real_client_secret 은 필수)"
echo "  2. 아래 중 하나로 실행:"
echo "       ./run-terminal.sh   # 터미널 클라이언트 (가장 빠른 시작)"
echo "       ./run-main.sh       # 텔레그램 봇"
echo "       ./run-web.sh        # 웹 클라이언트 (http://localhost:8000)"
echo
