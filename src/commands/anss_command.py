"""anss 명령 처리 - 체결 내역 AI 분석 (브로커 무관)."""

from src.utils.trade_analyzer import analyze_trades


def handle_anss(args, session):
    """
    anss 명령 처리 - 체결 내역 AI 분석

    사용법:
      /분석      → 최근 1일 분석
      /분석 7    → 최근 7일 분석 (최대 30일)
    """
    days = 1
    if args:
        try:
            days = int(args[0])
            if days < 1:
                return "❌ 일수는 1 이상의 양수를 입력하세요."
            if days > 30:
                return "❌ 최대 30일까지 분석 가능합니다."
        except ValueError:
            return "❌ 사용법: /분석 {일수}\n예: /분석 3 (최근 3일 분석)"

    result, error = analyze_trades(days)
    return error if error else result
