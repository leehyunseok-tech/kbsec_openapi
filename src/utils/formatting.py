"""텔레그램 명령 응답 포맷팅 공용 헬퍼.

숫자 포맷(format_number) 등 여러 명령이 공유하는 로직을 한 곳에 모아 재사용한다.
"""


def format_number(value):
    """KB 응답의 숫자 문자열(앞뒤 공백/0 패딩 포함)을 콤마 포함 형태로 정리."""
    if value is None:
        return "N/A"
    value_str = str(value).strip()
    if value_str in ("", "-"):
        return value_str or "N/A"

    sign = ""
    if value_str.startswith("+"):
        sign, value_str = "+", value_str[1:]
    elif value_str.startswith("-"):
        sign, value_str = "-", value_str[1:]

    if "." in value_str:
        integer_part, decimal_part = value_str.split(".", 1)
        try:
            return f"{sign}{int(integer_part):,}.{decimal_part}"
        except ValueError:
            return f"{sign}{value_str}"
    try:
        return f"{sign}{int(value_str):,}"
    except ValueError:
        return f"{sign}{value_str}"


def strip_field(value):
    """KB 응답 문자열 필드의 앞뒤 공백 제거 (빈 값이면 '')."""
    return str(value).strip() if value is not None else ""


# 전일대비구분코드: 1=상한 2=상승 3=보합 4=하한 5=하락
COMPARE_SIGN = {"1": "▲", "2": "▲", "3": "-", "4": "▼", "5": "▼"}


def compare_sign(ccd):
    return COMPARE_SIGN.get(strip_field(ccd), "")


def format_duration(seconds):
    """초 단위 정수를 'N시간 N분 N초' 형태로 변환 (예: 84420 → '23시간 27분 0초')."""
    if seconds is None:
        return "N/A"
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "N/A"
    if total < 0:
        return "N/A"

    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}시간")
    if hours or minutes:
        parts.append(f"{minutes}분")
    parts.append(f"{secs}초")
    return " ".join(parts)
