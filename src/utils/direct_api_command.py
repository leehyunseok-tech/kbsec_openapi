"""
docs/api/md 하위 74개 API 전부를 "{API코드}-{API명}" 형태의 전용 슬래시 커맨드로
즉시 실행할 수 있게 해주는 유틸 ("API 전체 자동 실행 커맨드" 기능의 핵심).

/api {코드}(src/commands/api_command.py)와 달리 대화형 번호 선택 세션을 만들지
않는다 — INPUT 표의 **모든 입력 필드**를 값으로 받아 즉시 실행한다. 입력 형식은
두 가지를 모두 지원한다:

  1) 위치(bare) 방식 — INPUT 표 순서대로 공백으로 띄워 값만 나열
       /IVM10050-기업개요 000660
       /IVU10280-거래량_상위 0 1
  2) JSON 방식 — {"항목한글명":"값"} 토큰을 필드명으로 매핑 (웹 트리 클릭이 채워주는 형식)
       /IVM10050-기업개요 {"종목코드":"000660"}
       /IVU10280-거래량_상위 {"거래소구분":"0"} {"시장구분":"1"}

두 방식 모두 넘기지 않은 필드는 기존 /api·/call과 동일하게 타입(길이)만큼 공백으로
자동 채운다. JSON 방식에서 값이 빈 문자열("")이면 미입력으로 보고 공백을 유지한다
(웹 placeholder를 채우지 않고 그대로 실행한 경우).

KB 명세의 필수여부(Y/N)는 부정확해(조회 API의 종목코드 등 핵심 파라미터도 N으로
표기하는 경우가 많음) **완전히 무시**하고, 모든 입력 필드를 받는다(api_spec.py 참고).
이 덕분에 매수/매도처럼 종목코드·수량 같은 값도 실제로 채워 넣을 수 있는 대신,
주문 계열 API도 그대로 실행 가능하다는 뜻이므로 호출 시 사용자가 실거래를 정확히
인지하고 있어야 한다.

커맨드 토큰은 src/web/spec_browser.py가 만드는 표시 라벨("{코드}-{API명}",
타임스탬프 제거됨)에서 공백을 '_'로 바꾼 것과 동일한 규칙이다 — 웹 트리(미션4)
쪽 클릭 채움 문자열과 백엔드 실행 판정이 같은 문자열 규칙을 공유한다.
"""

import json
import re

from src.utils.api_spec import (
    ApiSpec,
    _parse_choices,
    execute_api_call,
    format_api_result,
    full_blank_body,
    load_api_spec,
    search_api_entries,
)

# {"한글명":"값"} 형태의 JSON 오브젝트 토큰을 뽑아낸다 (내부 공백/콤마 포함 가능).
_JSON_OBJ_RE = re.compile(r"\{.*?\}")


def command_token(entry: dict) -> str:
    """api-list.json 항목 → 커맨드 토큰 ('IVU10280-거래량_상위' 형태, 소문자)."""
    return f"{entry['code']}-{entry['name']}".replace(" ", "_").lower()


def build_token_index() -> dict:
    """커맨드 토큰(소문자) → api-list.json 항목. 코드가 없는 항목(OAuth 등)은 제외."""
    return {command_token(e): e for e in search_api_entries() if e.get("code")}


def resolve_direct_command(token: str):
    """입력 토큰이 등록된 API 전용 커맨드면 api-list.json 항목을 반환, 아니면 None."""
    return build_token_index().get(token.strip().lower())


def effective_choices(f) -> list:
    """필드의 선택지 목록. api_spec이 필수여부와 무관하게 이미 파싱해 두므로
    f.choices를 그대로 쓰면 되고, 만일을 대비해 설명 재파싱을 폴백으로 둔다."""
    return f.choices or _parse_choices(f.description)


def positional_fields(spec: ApiSpec):
    """순차 파라미터 위치와 1:1 대응하는 필드 목록 (INPUT 표 등장 순서 그대로 전부).

    KB 명세가 핵심 파라미터도 N(선택)으로 표기하는 경우가 많아 필수여부로 거르지
    않고 모든 입력 필드를 위치 파라미터로 삼는다. 사용자가 넘기지 않은 뒤쪽 필드는
    _build_body()가 full_blank_body()로 공백 채운다.
    """
    return list(spec.fields)


def _usage_message(token: str, spec: ApiSpec, fields: list, extra: str = "") -> str:
    lines = []
    if extra:
        lines.append(extra + "\n")
    lines.append(f"📋 {spec.code} {spec.name} 사용법")
    if not fields:
        lines.append(f"  /{token}   (입력 파라미터 없음)")
        return "\n".join(lines)

    # 위치 방식과 JSON 방식 두 가지 입력 형식을 첫 필드 기준으로 함께 보여준다.
    lines.append(f"  ① 값만 순서대로: /{token} " + " ".join(f"[{f.name_kr}]" for f in fields))
    lines.append(f"  ② 항목명 지정  : /{token} " + " ".join(f'{{"{f.name_kr}":"값"}}' for f in fields))
    lines.append("  (앞쪽 필요한 값만 주면 되고, 나머지 필드는 공백으로 자동 채워집니다.)")
    lines.append(f"\n입력 필드 (총 {len(fields)}개, INPUT 표 순서):")
    for f in fields:
        choices = effective_choices(f)
        if choices:
            choice_str = ", ".join(f"{c}:{label}" for c, label in choices)
            lines.append(f"  • {f.name_kr}({f.name_en}) → {choice_str}")
        else:
            desc_note = f" — {f.description}" if f.description else ""
            lines.append(f"  • {f.name_kr}({f.name_en}){desc_note}")
    return "\n".join(lines)


def _build_body(spec: ApiSpec, fields: list, args: list):
    """args(위치 방식 또는 JSON 방식)를 dataBody로 변환. 반환: (body, error_msg | None).

    - args에 '{'로 시작하는 토큰이 하나라도 있으면 JSON 방식으로 해석한다.
      (공백으로 이미 쪼개진 args를 다시 이어붙여 {"한글명":"값"} 오브젝트를 복원)
    - 그 외에는 위치(bare) 방식: INPUT 표 순서대로 앞에서부터 채운다.
    - 어느 방식이든 넘기지 않은 필드는 full_blank_body()의 공백을 유지한다.
    """
    body = full_blank_body(spec)
    if not args:
        return body, None

    raw = " ".join(args).strip()
    if "{" in raw:
        kr_to_en = {f.name_kr: f.name_en for f in fields}
        matches = _JSON_OBJ_RE.findall(raw)
        if not matches:
            return body, f'파라미터 형식 오류: \'{raw}\'  (예: {{"{fields[0].name_kr}":"값"}})'
        for token in matches:
            try:
                obj = json.loads(token)
            except (json.JSONDecodeError, ValueError):
                return body, f'파라미터 형식 오류: {token}  (예: {{"{fields[0].name_kr}":"값"}})'
            if not isinstance(obj, dict):
                return body, f'파라미터 형식 오류: {token}  (예: {{"{fields[0].name_kr}":"값"}})'
            for key, value in obj.items():
                if key not in kr_to_en:
                    return body, f"알 수 없는 항목명: '{key}'  (사용 가능: {', '.join(kr_to_en)})"
                # 빈 값은 미입력(placeholder 그대로)으로 보고 공백 유지
                if value != "" and value is not None:
                    body[kr_to_en[key]] = str(value)
        return body, None

    # 위치(bare) 방식
    if len(args) > len(fields):
        return body, "TOO_MANY"
    # strict=False 의도적 — 위에서 args가 fields보다 많은 경우만 막았고, 적게 준 경우는
    # "나머지 필드는 미입력(공백 유지)"이라는 정상 동작이라 길이 불일치를 허용해야 한다.
    for f, value in zip(fields, args, strict=False):
        body[f.name_en] = value
    return body, None


def execute_direct_command(entry: dict, args: list, access_token: str, host_url: str) -> str:
    """토큰이 가리키는 API를 위치/JSON 파라미터로 즉시 실행한다.

    entry는 resolve_direct_command()가 반환한 api-list.json 항목이어야 한다.
    """
    spec = load_api_spec(entry["code"])
    if spec is None:
        return f"❌ '{entry['code']}' 명세를 찾을 수 없습니다."

    fields = positional_fields(spec)
    token = command_token(entry)

    body, err = _build_body(spec, fields, args)
    if err == "TOO_MANY":
        return _usage_message(token, spec, fields, extra=f"❌ 값을 필드 수({len(fields)}개)보다 많이 입력했습니다.")
    if err is not None:
        return _usage_message(token, spec, fields, extra=f"❌ {err}")

    result = execute_api_call(spec, body, access_token, host_url)
    return format_api_result(spec, result)
