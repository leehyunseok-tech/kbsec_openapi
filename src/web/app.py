"""
FastAPI 웹 백엔드 — 순수 JSON API + 정적 파일 서빙.

프론트엔드(src/web/static/)는 순수 HTML+CSS+JS(fetch)로만 구성되어 있고, 서버 사이드
템플릿(Jinja2 등)은 쓰지 않는다. 모든 화면 데이터는 /api/* JSON 엔드포인트로만 오간다.

인증/세션 모델 (다중 사용자):
  - 쿠키(kbsec_web_sid) 하나 = WebClient 인스턴스 하나 (src/web/session_store.py)
  - 별도의 로그인 화면은 없다 — 설정 화면에서 KB증권 앱키(client_key)/시크릿을 입력해
    "저장" 하면 곧바로 KB 토큰 발급(로그인)까지 이뤄진다.
  - 사용자가 입력한 키는 해당 WebClient의 메모리에만 있고 디스크에 저장하지 않는다.
    응답으로도 원문을 되돌려주지 않는다(마스킹된 상태 정보만 반환).
  - 예외(로컬 편의 기능): `run-web.* token`으로 실행하면 KBSEC_WEB_AUTOLOAD=1이 설정되고,
    이때 새로 생기는 모든 세션은 config/config.py의 앱키로 자동 로그인된다
    (_autoload_from_config 참고) — 다중 사용자 원칙에서 벗어나는 예외이므로 로컬
    단일 운영자 용도로만 쓴다(src/run/web.py의 경고 참고).

실행은 src/run/web.py (또는 run-web.bat / run-web.sh) 참고.
"""

import os
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import config as app_config
from src.web.session_store import COOKIE_NAME, get_or_create
from src.web import spec_browser
from src.utils import stock_master
from src.utils.api_spec import execute_api_call, load_api_spec

STATIC_DIR = Path(__file__).resolve().parent / "static"
AUTOLOAD = os.environ.get("KBSEC_WEB_AUTOLOAD") == "1"

app = FastAPI(title="kbsec_api web", docs_url=None, redoc_url=None)

# 서버 시작(uvicorn이 이 모듈을 import하는 시점)에 종목마스터를 미리 메모리에 올린다 —
# load_all()은 lru_cache라 이후 모든 검색(/api/stock/*)이 파일을 다시 읽지 않고
# 첫 요청부터 빠르게 응답한다 (mst/api/openapi_field_*.mst 두 파일).
stock_master.load_all()


def _configured(value):
    """config.py 값이 실제로 채워졌는지 확인(placeholder "YOUR_..."/빈 값 제외)."""
    return bool(value) and not str(value).startswith("YOUR_")


def _autoload_from_config(client):
    """`run-web.* token` 전용 — 새 세션을 config.py 값으로 자동 설정/로그인한다.

    ⚠️ 로컬 단일 운영자 편의 기능. 이 함수가 호출되는 동안(AUTOLOAD=True) 서버가
    외부에 노출되면 접속하는 모든 브라우저가 운영자의 실제 KB 계정으로 자동
    로그인되므로, 반드시 로컬 전용(KBSEC_WEB_HOST=127.0.0.1)에서만 써야 한다.
    """
    client_key = getattr(app_config, "real_client_key", "")
    client_secret = getattr(app_config, "real_client_secret", "")
    if not (_configured(client_key) and _configured(client_secret)):
        return

    claude_api_key = getattr(app_config, "claude_api_key", "")
    if _configured(claude_api_key):
        client.claude_api_key = claude_api_key
        claude_model = getattr(app_config, "claude_model", "")
        client.claude_model = claude_model if _configured(claude_model) else None

    telegram_token = getattr(app_config, "telegram_token", "")
    telegram_chat_id = getattr(app_config, "telegram_chat_id", "")
    if _configured(telegram_token) and _configured(telegram_chat_id):
        client.telegram_token = telegram_token
        client.telegram_chat_id = str(telegram_chat_id)

    client.login("real", client_key, client_secret)


def _client_for(request: Request, response: Response):
    """요청 쿠키에서 WebClient를 찾고, 없으면 새로 만들어 쿠키를 심는다."""
    sid, client = get_or_create(request.cookies.get(COOKIE_NAME))
    is_new_session = request.cookies.get(COOKIE_NAME) != sid
    if is_new_session:
        # HttpOnly — 프론트 JS에서 쿠키 값을 읽을 필요가 없다(브라우저가 자동 첨부).
        response.set_cookie(COOKIE_NAME, sid, httponly=True, samesite="lax")
        if AUTOLOAD:
            _autoload_from_config(client)
    return client


# ── 요청 바디 모델 ──────────────────────────────────────────────────────


class SettingsBody(BaseModel):
    env: str = "real"
    client_key: str
    client_secret: str
    claude_api_key: str | None = None
    claude_model: str | None = None
    telegram_token: str | None = None
    telegram_chat_id: str | None = None


class CommandBody(BaseModel):
    text: str


class AnswerBody(BaseModel):
    # confirm 세션: value = "y" | "n", select 세션: value = "1"~"N" | "취소"
    value: str


class SpecExecuteBody(BaseModel):
    code: str
    data_body: dict


# ── 설정 (설정 저장 = KB 로그인) ───────────────────────────────────────


@app.get("/api/settings")
def get_settings(request: Request, response: Response):
    """현재 세션의 설정 상태 — 시크릿 원문은 절대 반환하지 않는다."""
    client = _client_for(request, response)
    session = client.session
    return {
        "logged_in": session.is_logged_in(),
        "env": session.trading_env,
        "env_name": session.get_env_name(),
        "token_remaining_seconds": session.get_remaining_seconds(),
        "claude_configured": bool(client.claude_api_key),
        "claude_model": client.claude_model,
        "telegram_configured": bool(client.telegram_token and client.telegram_chat_id),
    }


@app.post("/api/settings")
def post_settings(body: SettingsBody, request: Request, response: Response):
    # 주의: 이 엔드포인트에서 JSONResponse를 직접 return하면 안 된다 — _client_for가
    # 주입된 response에 심은 새 세션 쿠키(Set-Cookie)는 dict를 반환할 때만 FastAPI가
    # 최종 응답에 합쳐준다. JSONResponse를 새로 만들어 반환하면 쿠키가 유실되어,
    # 새 브라우저가 첫 요청으로 곧바로 POST하면 로그인한 세션에 다시는 접근할 수 없다.
    client = _client_for(request, response)

    client_key = body.client_key.strip()
    client_secret = body.client_secret.strip()
    if not client_key or not client_secret:
        response.status_code = 400
        return {"success": False, "message": "client_key와 client_secret은 필수입니다."}

    # 선택 설정은 빈 문자열이면 미설정(None) 취급
    client.claude_api_key = (body.claude_api_key or "").strip() or None
    client.claude_model = (body.claude_model or "").strip() or None
    client.telegram_token = (body.telegram_token or "").strip() or None
    client.telegram_chat_id = (body.telegram_chat_id or "").strip() or None

    result = client.login(body.env.strip().lower(), client_key, client_secret)
    if not result["success"]:
        response.status_code = 401
    return result


# ── 명령 실행 (터미널/텔레그램과 동일한 파이프라인) ─────────────────────


@app.post("/api/command")
def post_command(body: CommandBody, request: Request, response: Response):
    """텍스트 명령 실행 — '/'로 시작하면 직접 명령, 아니면 AI 자연어 변환.

    응답의 pending이 null이 아니면 확인(confirm)/선택(select) 세션이 열린 것 —
    프론트는 버튼을 렌더링하고 /api/answer로 응답을 보낸다.
    """
    client = _client_for(request, response)
    try:
        text = client.process_command(body.text)
    except Exception as e:
        return {"response": f"❌ 오류 발생: {e}", "pending": None}
    return {"response": text, "pending": client.describe_pending_session()}


@app.post("/api/answer")
def post_answer(body: AnswerBody, request: Request, response: Response):
    """확인/선택 세션에 대한 응답 — 버튼 클릭 결과를 세션 텍스트로 그대로 전달.

    main.py가 인라인 버튼 callback_data를, terminal.py가 화살표 프롬프트 결과를
    "y"/"n"/번호 텍스트로 변환해 process_command에 넘기는 것과 동일한 구조다.
    """
    client = _client_for(request, response)
    try:
        text = client.process_command(body.value)
    except Exception as e:
        return {"response": f"❌ 오류 발생: {e}", "pending": None}
    return {"response": text, "pending": client.describe_pending_session()}


# ── 종목 검색 (로컬 마스터, 로그인 불필요) ──────────────────────────────


def _domestic_json(s):
    return {
        "kind": "domestic", "name": s.name, "code": s.code, "market": s.market,
        "stock_type": s.stock_type, "managed": s.managed, "halted": s.halted,
        "order_unit": s.order_unit, "decimal_tradable": s.decimal_tradable,
        "decimal_state": s.decimal_state,
    }


def _overseas_json(s):
    return {
        "kind": "overseas", "name": s.name_kr or s.name_en, "code": s.ticker,
        "exchange": s.exchange, "exchange_name": s.exchange_name, "currency": s.currency,
        "stock_type": s.stock_type, "trade_restriction": s.trade_restriction,
        "buy_unit": s.buy_unit, "sell_unit": s.sell_unit,
        "decimal_tradable": s.decimal_tradable,
    }


@app.get("/api/stock/search")
def stock_search(q: str = "", exact: str = ""):
    """종목 증분 검색 — 두 글자 미만이면 빈 결과(프론트와 동일 규칙을 서버에서도 강제).

    exact=1이면 이름/코드/티커 정확일치(대소문자 무시)만 반환 — 검색창에서 Enter를
    눌렀을 때 완성된 종목명의 부분일치 잡음(관련 ETF/ETN 등)을 걷어내기 위한 모드.
    """
    q = q.strip()
    if len(q) < 2:
        return {"domestic": [], "overseas": []}
    if exact == "1":
        domestic, overseas = stock_master.search_exact(q)
    else:
        domestic, overseas = stock_master.search_any(q, limit=15)
    return {
        "domestic": [_domestic_json(s) for s in domestic],
        "overseas": [_overseas_json(s) for s in overseas],
    }


@app.get("/api/stock/detect")
def stock_detect(text: str = ""):
    """자유 문장(자연어 명령) 속 종목 인식 — '삼성전자 10주 사줘' → 삼성전자(005930)."""
    stocks = stock_master.detect_in_text(text, limit=5)
    return {
        "stocks": [
            _overseas_json(s) if hasattr(s, "ticker") else _domestic_json(s)
            for s in stocks
        ]
    }


# ── API 명세 탐색/테스트 호출 (docs/api/md 기반) ────────────────────────


@app.get("/api/spec/tree")
def spec_tree():
    """docs/api/md 폴더 구조 그대로의 카테고리/하위폴더/파일 트리."""
    return {"tree": spec_browser.build_tree()}


@app.get("/api/spec/detail")
def spec_detail(path: str = ""):
    """명세 상세 — md 원문 + 편집 폼 필드(기본값 포함) + 기본 dataBody."""
    detail = spec_browser.load_detail(path)
    if detail is None:
        return JSONResponse(status_code=404, content={"error": "명세 파일을 찾을 수 없습니다."})
    return detail


@app.post("/api/spec/execute")
def spec_execute(body: SpecExecuteBody, request: Request, response: Response):
    """명세 페이지의 테스트 호출 — 실제 KB API로 전송하고 원본 JSON 응답을 돌려준다.

    dataHeader(ipAddr/macAddr)는 일반 주문/조회 API 호출과 동일하게 서버에서 자동
    구성된다(src/api/client.py의 call_business_api). ⚠️ 실거래 환경이므로 주문 계열
    API는 실제 주문이 나간다 — 프론트에서도 경고를 표시한다.
    """
    # post_settings와 같은 이유로 JSONResponse 직접 반환 금지(세션 쿠키 유실).
    client = _client_for(request, response)
    if not client.session.is_logged_in():
        response.status_code = 401
        return {"success": False, "error": "로그인이 필요합니다. 설정 화면에서 앱키를 입력하세요."}

    spec = load_api_spec(body.code)
    if spec is None:
        response.status_code = 404
        return {"success": False, "error": f"알 수 없는 API 코드: {body.code}"}

    data_body = {k: str(v) for k, v in body.data_body.items()}
    result = execute_api_call(spec, data_body, client.session.access_token, client.session.host_url)
    return {"success": result.get("success"), "status_code": result.get("status_code"), "body": result.get("body")}


# ── 상태/알림 폴링 ──────────────────────────────────────────────────────


@app.get("/api/notifications")
def get_notifications(request: Request, response: Response):
    """자동매매 모니터(brk/wave/grid/hold 등)가 쌓아둔 알림을 가져간다(가져가면 비워짐)."""
    client = _client_for(request, response)
    return {"notifications": client.drain_notifications()}


@app.get("/api/apilog")
def get_api_log(since: int = 0):
    """KB API 요청/응답 로그 증분 폴링 — 터미널 콘솔 로그와 동일한 내용(마스킹 적용).

    api_logger의 프로세스 전역 링버퍼를 읽으므로 서버의 모든 사용자 로그가 공유된다
    (설정값과 동일한 서버 공용 제약, 화면에 안내됨).
    """
    from src.utils.api_logger import get_logs_since

    logs = get_logs_since(since)
    return {"logs": logs, "last_seq": logs[-1]["seq"] if logs else since}


@app.get("/api/help")
def get_help(request: Request, response: Response):
    client = _client_for(request, response)
    return {"help": client.handle_command_help([])}


# ── 정적 파일 (순수 HTML/CSS/JS 프론트엔드) ─────────────────────────────


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
