"""log 명령 처리 - 체결 내역 CSV 파일 전송 (브로커 무관)."""

from datetime import datetime, timedelta

from src.paths import LOGS_DIR as _LOGS_DIR


def _resolve_log_path(days_ago: int):
    target = datetime.now() - timedelta(days=days_ago)
    return _LOGS_DIR / f"{target.strftime('%Y%m%d')}.csv", target.strftime("%Y-%m-%d")


def handle_log(args, session, send_document_fn=None):
    """
    log 명령 처리 - 지정한 날짜의 체결 내역 CSV 파일 전송

    사용법:
      /체결기록        → 당일
      /체결기록 3      → 3일 전
    """
    days_ago = 0
    if args:
        try:
            days_ago = abs(int(args[0]))
        except ValueError:
            return "❌ 사용법: /체결기록 {일수}\n예: /체결기록 0 (오늘), /체결기록 3 (3일 전)"

    path, date_label = _resolve_log_path(days_ago)
    if not path.exists():
        return f"❌ {date_label} 체결 내역 파일이 없습니다.\n(경로: logs/{path.name})"

    size_kb = path.stat().st_size / 1024
    caption = f"📋 {date_label} 체결 내역\n파일: {path.name} ({size_kb:.1f} KB)"

    if send_document_fn:
        result = send_document_fn(str(path), caption)
        if result["success"]:
            return f"✅ {date_label} 체결 내역 파일 전송 완료"
        err = result["body"].get("error") or result["body"].get("description", "알 수 없는 오류")
        return f"❌ 파일 전송 실패: {err}"

    return f"📋 {date_label} 체결 내역\n경로: {path}\n크기: {size_kb:.1f} KB"
