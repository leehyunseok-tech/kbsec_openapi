"""
KB증권 API 웹 클라이언트 실행 진입점 (트리플 클라이언트 아키텍처).

main.py(텔레그램)/terminal.py(터미널)와 동일한 src/commands/*.py 핸들러를 공유하는
웹 인터페이스를 uvicorn으로 띄운다. 웹 관련 실제 구현(FastAPI 앱/세션/프론트엔드)은
전부 src/web/ 아래에 있고, 이 파일은 실행만 담당한다.

사용법:
  uv run python -m src.run.web        (또는 run-web.bat / run-web.sh)
  → 브라우저에서 http://localhost:8000 접속

  uv run python -m src.run.web token   (또는 run-web.bat token / run-web.sh token)
  → config/config.py의 앱키(client_key/client_secret) 및 선택 항목(Claude API 키,
    텔레그램 토큰)으로 새 브라우저 세션을 자동 설정/로그인하고, 브라우저를
    http://localhost:8000/ 로 자동으로 연다 — 로컬에서 혼자 쓸 때 설정 화면에
    매번 값을 다시 입력하지 않아도 되는 편의 기능이다.

옵션 (환경변수):
  KBSEC_WEB_HOST  바인딩 주소 (기본 127.0.0.1 — 로컬 전용.
                  같은 네트워크의 다른 기기/배포 환경에서 접속하려면 0.0.0.0)
  KBSEC_WEB_PORT  포트 (기본 8000)

터미널/텔레그램과 달리 기본적으로는 config.py의 앱키로 자동 로그인하지 않는다 —
다중 사용자 전제이므로 각 사용자가 브라우저 설정 화면에서 자기 앱키/시크릿을
입력한다. `token` 옵션은 이 기본 동작을 로컬 단일 운영자 편의를 위해 예외적으로
바꾸는 것이므로, 아래 경고와 같이 외부 노출 환경(KBSEC_WEB_HOST=0.0.0.0 등)에서는
절대 쓰면 안 된다 — 켜져 있는 동안 접속하는 모든 브라우저가 운영자의 실제 KB
계정으로 자동 로그인된다.
"""

import os
import sys
import threading
import time
import webbrowser

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import uvicorn


def _open_browser_later(url, delay=1.2):
    """서버가 리슨을 시작할 시간을 준 뒤 기본 브라우저로 url을 연다(백그라운드 스레드)."""

    def _run():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def main():
    host = os.environ.get("KBSEC_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("KBSEC_WEB_PORT", "8000"))
    autoload = any(arg.strip().lower() == "token" for arg in sys.argv[1:])

    display_host = "localhost" if host == "127.0.0.1" else host
    # token 모드도 첫 화면은 실행 화면("/") — 자동 로그인되므로 설정 화면을 거칠 필요가 없다.
    url = f"http://{display_host}:{port}/"

    print("=" * 60)
    print("🌐 KB증권 Open API 봇 - 웹 클라이언트")
    print("=" * 60)
    print(f"브라우저에서 접속: {url}")

    if autoload:
        # 이 프로세스에서 src.web.app을 import하기 전에 심어둬야 app.py가 읽을 수 있다.
        # uvicorn.run(...)이 문자열 앱 경로를 이 프로세스 안에서 import하므로 타이밍은 안전하다.
        os.environ["KBSEC_WEB_AUTOLOAD"] = "1"
        print()
        print("⚠️  token 모드: 새로 접속하는 모든 브라우저 세션이 config/config.py의")
        print("    앱키로 자동 로그인됩니다. 로컬에서 혼자 쓸 때만 사용하세요 —")
        print("    KBSEC_WEB_HOST=0.0.0.0 등으로 외부에 노출하지 마세요.")
        _open_browser_later(url)

    print("종료: Ctrl+C")
    print("=" * 60)

    # warning — /api/notifications(5초)·/api/apilog(2.5초) 폴링 access log가 계속
    # 찍히는 게 시끄러워서 info보다 낮춤. 시작/종료 등 uvicorn 자체 안내 메시지는
    # 그대로 나오고, 요청 단위 access log(각 GET/POST 라인)만 조용해진다.
    uvicorn.run("src.web.app:app", host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
