#!/usr/bin/env bash
# KB증권 Open API - 최초 1회 설치용 진입점 (macOS/Linux).
# manage/install/install-project.sh 를 실행하고, 설치가 성공하면 이 스크립트 자신을
# 삭제해 재사용을 위해 남겨두지 않는다. 재설치가 필요하면 언제든
# manage/install/install-project.sh 를 직접 다시 실행하면 된다.
# Windows 짝은 install-kbsec-openapi.bat 이다.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if bash "$SCRIPT_DIR/manage/install/install-project.sh"; then
    echo
    echo "[OK] 설치가 완료되어 1회용 설치 스크립트를 정리합니다: $(basename "$0")"
    rm -f -- "$SCRIPT_DIR/install-kbsec-openapi.sh"
else
    status=$?
    echo
    echo "[X] 설치가 정상적으로 끝나지 않았습니다 - 재시도할 수 있도록 이 스크립트는 남겨둡니다."
    exit "$status"
fi
