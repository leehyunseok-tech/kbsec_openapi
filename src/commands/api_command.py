"""
docs/api/md에 정의된 임의의 KB증권 API를 코드만으로 직접 호출하는 명령 ("API 직접호출").

md의 INPUT 표에서 필수(Y)이면서 설명에 선택지가 있는 필드는 사용자가 번호로 고르고,
그 외(설명은 있지만 선택지가 없거나 필수가 아닌 필드)는 타입(길이)만큼 공백으로
채워 그대로 요청한다 (src/utils/api_spec.py 참고). registry.py(자동 생성,
CODE_TO_MODULE 수동 갱신 필요)에 의존하지 않고 docs/api/api-list.json +
docs/api/md/*.md를 직접 읽으므로, 명세 문서만 최신이면 코드 재생성 없이
곧바로 새 API도 실행할 수 있다.

사용법:
  /api {API코드}          해당 API 실행 (선택 필요 필드가 있으면 대화형으로 이어짐)
  /api info {API코드}     실행 전 파라미터 미리보기 (실행하지 않음)
  /api list [키워드]      코드/API명/업무구분으로 검색
"""

from src.utils.api_spec import (
    default_data_body,
    describe_spec,
    execute_api_call,
    format_api_result,
    load_api_spec,
    search_api_entries,
    selection_fields,
)


def handle_api(args, session, session_mgr=None, chat_id=None):
    if not args:
        return (
            "❌ 사용법: /api {API코드}\n"
            "  /api info {API코드}   파라미터 미리보기\n"
            "  /api list [키워드]    코드/이름/업무구분 검색\n\n"
            "전체 목록: docs/api/api-list.md"
        )

    sub = args[0].lower()
    if sub == "list":
        return _handle_list(args[1:])
    if sub == "info":
        return _handle_info(args[1:])

    return _handle_execute(args, session, session_mgr, chat_id)


def _handle_list(args):
    keyword = args[0] if args else None
    entries = search_api_entries(keyword)
    if not entries:
        return f"검색 결과가 없습니다 (키워드: {keyword})" if keyword else "등록된 API가 없습니다."

    lines = [f"{e['code']:<10} {e['name']}  [{e['category']}]" for e in entries]
    lines.append(f"\n총 {len(entries)}건. '/api info {{코드}}'로 파라미터를 확인하세요.")
    return "\n".join(lines)


def _handle_info(args):
    if not args:
        return "❌ 사용법: /api info {API코드}"
    spec = load_api_spec(args[0])
    if spec is None:
        return f"❌ '{args[0]}' API를 찾을 수 없습니다. /api list 로 검색해보세요."
    return describe_spec(spec)


def _handle_execute(args, session, session_mgr, chat_id):
    if not session.is_logged_in():
        return "❌ 로그인이 필요합니다. /login real 을 먼저 실행하세요."

    code = args[0].strip().upper()
    spec = load_api_spec(code)
    if spec is None:
        return f"❌ '{code}' API를 찾을 수 없습니다. /api list 로 검색해보세요."

    pending_fields = selection_fields(spec)
    base_body = default_data_body(spec)

    if not pending_fields:
        result = execute_api_call(spec, base_body, session.access_token, session.host_url)
        return format_api_result(spec, result)

    if session_mgr is None or chat_id is None:
        return (
            f"❌ {spec.code} {spec.name}은(는) 선택이 필요한 필수 파라미터가 있어 "
            "대화형 세션이 필요합니다. 텔레그램/터미널 채팅에서 '/api "
            f"{spec.code}'로 직접 실행해주세요."
        )

    api_session = session_mgr.create_api_call_session(chat_id, chat_id, spec, base_body, pending_fields)
    return api_session.get_selection_message()
