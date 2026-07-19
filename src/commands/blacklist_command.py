"""blacklist 명령 처리 - 매매 금지 종목 관리 (브로커 무관)."""

from src.utils.settings_manager import SettingsManager


def handle_blacklist(args):
    """
    blacklist 명령 처리

    사용법:
      /blacklist add {종목코드}    - 블랙리스트 추가 (국내 6자리 코드 또는 해외 티커)
      /blacklist list              - 목록 조회
      /blacklist remove {번호}     - 항목 삭제
    """
    if not args:
        return _show_usage()

    sub = args[0].lower()
    if sub == "add":
        if len(args) < 2:
            return "❌ 사용법: /blacklist add {종목코드}"
        success, msg = SettingsManager.add_to_blacklist(args[1].strip())
        return msg if success else f"❌ {msg}"
    if sub == "list":
        return _show_list()
    if sub == "remove":
        if len(args) < 2:
            return "❌ 사용법: /blacklist remove {번호}"
        try:
            index = int(args[1])
        except ValueError:
            return "❌ 번호는 정수여야 합니다."
        success, msg = SettingsManager.remove_from_blacklist(index)
        return msg if success else f"❌ {msg}"
    return _show_usage()


def _show_list():
    blacklist = SettingsManager.get_blacklist()
    if not blacklist:
        return "블랙리스트가 비어 있습니다."
    lines = ["🚫 블랙리스트 종목\n"]
    lines.extend(f"  {i}. {code}" for i, code in enumerate(blacklist, 1))
    return "\n".join(lines)


def _show_usage():
    return "사용법:\n  /blacklist add {종목코드}   - 추가 (국내 6자리 코드 또는 해외 티커)\n  /blacklist list             - 목록 조회\n  /blacklist remove {번호}    - 삭제"
