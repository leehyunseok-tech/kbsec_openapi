"""gdcrs(골든크로스) 명령 처리 - 설정/목록 관리 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_gdcrs(args, session):
    """
    gdcrs 명령 처리

    사용법:
      /gdcrs intv {단기} {장기}      분봉 주기 설정 (예: /gdcrs intv 5 20)
      /gdcrs add {종목} {금액}       목록에 추가
      /gdcrs list                    목록 조회
      /gdcrs remove {번호}           항목 삭제
      /gdcrs clear                   목록 전체 비우기
    """
    if not args:
        return _show_menu()

    sub = args[0].lower().replace("()", "").strip()
    if sub == "intv":
        return _handle_intv(args[1:])
    if sub == "add":
        return _handle_add(args[1:])
    if sub == "list":
        return _handle_list()
    if sub == "remove":
        return _handle_remove(args[1:])
    if sub == "clear":
        return _handle_clear()
    return f"❌ 알 수 없는 부명령어: {sub}\n\n{_show_menu()}"


def _show_menu():
    return """📊 골든크로스(GDCRS) 설정

/gdcrs intv {단기} {장기}      분봉 주기 설정 (1~60, 예: /gdcrs intv 5 20)
/gdcrs add {종목} {금액}       목록에 추가 (예: /gdcrs add 005930 100000)
/gdcrs list                    목록 조회
/gdcrs remove {번호}           항목 삭제
/gdcrs clear                   목록 전체 비우기

📌 주의: /start gdcrs 명령으로 모니터링을 시작하세요.
(참고: /ddcrs 전용 설정 명령은 없으며, ddcrs는 gdcrs와 동일한 분봉 주기(기본 5/20분)를 사용합니다.)"""


def _handle_intv(args):
    if len(args) < 2:
        return "❌ 사용법: /gdcrs intv {단기} {장기}\n예: /gdcrs intv 5 20"
    try:
        intv_short, intv_long = int(args[0]), int(args[1])
        if not (1 <= intv_short <= 60) or not (1 <= intv_long <= 60):
            return "❌ 단기/장기는 1~60 사이의 정수여야 합니다."
        if intv_short >= intv_long:
            return "❌ 단기는 장기보다 작아야 합니다."
    except ValueError:
        return "❌ 값은 정수여야 합니다."

    settings = SettingsManager.load_settings()
    settings.setdefault("gdcrs", {"stocks": []})
    settings["gdcrs"]["intv_short"] = intv_short
    settings["gdcrs"]["intv_long"] = intv_long
    SettingsManager.save_settings(settings)
    return f"✅ 골든크로스 분봉 설정 완료\n\n단기 평균: {intv_short}분봉\n장기 평균: {intv_long}분봉"


def _handle_add(args):
    if len(args) < 2:
        return "❌ 사용법: /gdcrs add {종목코드} {금액}\n예: /gdcrs add 005930 100000"
    stk_cd = args[0].strip()
    try:
        amount = int(args[1])
    except ValueError:
        return "❌ 금액은 정수여야 합니다."
    if not stk_cd.isdigit() or len(stk_cd) != 6:
        return "❌ 종목코드는 6자리 숫자여야 합니다."
    if amount <= 0:
        return "❌ 금액은 0보다 커야 합니다."

    settings = SettingsManager.load_settings()
    settings.setdefault("gdcrs", {"stocks": []})
    stocks = settings["gdcrs"].get("stocks", [])
    if any(s["code"] == stk_cd for s in stocks):
        return f"❌ 종목 {stk_cd}은(는) 이미 목록에 있습니다."
    stocks.append({"code": stk_cd, "amount": amount})
    settings["gdcrs"]["stocks"] = stocks
    SettingsManager.save_settings(settings)
    return f"✅ 종목 추가 완료\n\n종목코드: {stk_cd}\n할당 금액: {amount:,}원\n\n현재 추적 종목 수: {len(stocks)}개"


def _handle_list():
    settings = SettingsManager.load_settings()
    stocks = settings.get("gdcrs", {}).get("stocks", [])
    if not stocks:
        return "📭 골든크로스 목록이 비어있습니다.\n\n/gdcrs add로 종목을 추가하세요."
    intv_short, intv_long = settings.get("gdcrs", {}).get("intv_short", 5), settings.get("gdcrs", {}).get("intv_long", 20)
    lines = [f"📊 골든크로스 모니터링 목록\n\n분봉 설정: {intv_short}분 × {intv_long}분\n추적 종목: {len(stocks)}개\n"]
    lines.extend(f"{i}. {s.get('code', 'N/A')}   |   {s.get('amount', 0):,}원" for i, s in enumerate(stocks, 1))
    return "\n".join(lines)


def _handle_remove(args):
    if not args:
        return "❌ 사용법: /gdcrs remove {번호}\n예: /gdcrs remove 1"
    try:
        idx = int(args[0]) - 1
    except ValueError:
        return "❌ 번호는 정수여야 합니다."
    settings = SettingsManager.load_settings()
    stocks = settings.get("gdcrs", {}).get("stocks", [])
    if idx < 0 or idx >= len(stocks):
        return f"❌ 유효하지 않은 번호입니다. (1~{len(stocks)})"
    removed = stocks.pop(idx)
    settings["gdcrs"]["stocks"] = stocks
    SettingsManager.save_settings(settings)
    return f"✅ 종목 삭제 완료\n\n삭제된 종목: {removed['code']}\n할당 금액: {removed['amount']:,}원\n\n남은 종목 수: {len(stocks)}개"


def _handle_clear():
    settings = SettingsManager.load_settings()
    count = len(settings.get("gdcrs", {}).get("stocks", []))
    if "gdcrs" in settings:
        settings["gdcrs"]["stocks"] = []
    SettingsManager.save_settings(settings)
    return f"✅ 골든크로스 목록을 비웠습니다.\n\n삭제된 종목 수: {count}개"
