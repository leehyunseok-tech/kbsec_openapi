"""
docs/api/md 명세를 런타임에 직접 파싱해, 코드만 알면 임의의 KB증권 API를
바로 호출할 수 있게 해주는 유틸 ("API 직접호출" 기능의 핵심).

src/api/*.py + registry.py(manage/generate/generate_api_client.py 자동 생성)는
CODE_TO_MODULE을 수동으로 갱신해야 새 API가 반영되지만, 이 모듈은
docs/api/api-list.json + docs/api/md/*.md를 그때그때 직접 읽으므로 명세
문서만 최신이면 코드 재생성 없이 곧바로 "/api {코드}"로 실행할 수 있다.

INPUT 파라미터 채움 규칙:
  - **필수여부(Y/N) 컬럼은 신뢰할 수 없어 완전히 무시한다** (KB 명세가 조회 API의
    핵심 파라미터 — 종목코드 등 — 도 N으로 표기하는 등 실제와 어긋나는 경우가 많음).
  - 설명에서 "코드:라벨" 형태의 선택지가 2개 이상 파싱되면(필수여부 무관)
    → 사용자가 번호로 선택 (ApiField.choices)
  - 그 외(설명에 선택지가 없는 필드) → 타입(길이)만큼 공백(" ")으로 채워 요청 (blank_fill)
  - 요청 전 "필수 파라미터 누락" 검증도 하지 않는다(필수여부가 부정확하므로) —
    실제 필수 여부는 KB 서버 응답으로 판단한다.

ApiField.required는 파싱은 해두되(원본 표기 참고용) 어떤 로직/표시에도 쓰지 않는다.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from src.api.client import call_business_api
from src.paths import API_LIST_JSON, DOCS_API_DIR  # noqa: F401 — DOCS_API_DIR은 spec_browser.py가 여기서 재수입

_LENGTH_RE = re.compile(r"\((\d+)\)")
# "1:오프라인 2:온라인", "01-매도, 02-매수", "0.전체 1.일반 2.소수점" 등
# "<코드><구분자><라벨>" 반복 패턴을 찾는다. 구분자는 : - . 를 인정하되, 점(.)은 뒤에
# (공백 후) 숫자가 오면 소수점("1.0", "0.5%")으로 보고 구분자에서 제외해 오탐을 막는다.
# 코드 앞이 한글/영문/숫자면 오탐이므로 제외.
_CHOICE_RE = re.compile(r"(?<![0-9A-Za-z가-힣])([A-Za-z0-9]{1,4})\s*(?::|-|\.(?!\s*\d))\s*")


@dataclass(frozen=True)
class ApiField:
    name_en: str
    name_kr: str
    length: int
    required: bool  # 원본 표기 참고용 — 신뢰할 수 없어 로직/표시에 쓰지 않음
    description: str
    choices: list  # list[tuple[str, str]] — 설명에서 선택지가 2개 이상 파싱될 때 채워짐(필수여부 무관)


@dataclass(frozen=True)
class ApiSpec:
    code: str
    name: str
    category: str
    endpoint: str
    md_path: Path
    fields: list  # list[ApiField]
    output_labels: dict = field(default_factory=dict)  # {영문필드명: 한글필드명} (OUTPUT 표 기반)


_api_list_cache = {"mtime": None, "entries": []}


def _load_api_list():
    """api-list.json을 mtime 기반으로 캐싱해 로드.

    이 함수는 AI 자연어 변환 매 호출(_build_api_name_list), 변환 결과의 api 명령
    해석(api_resolver), /api·/call 실행마다 불리므로 매번 재파싱하지 않는다.
    generate_api_docs.py 재실행 등으로 파일이 갱신되면 mtime이 바뀌어 자동 리로드된다.
    """
    if not API_LIST_JSON.exists():
        return []
    mtime = API_LIST_JSON.stat().st_mtime
    if _api_list_cache["mtime"] != mtime:
        _api_list_cache["entries"] = json.loads(API_LIST_JSON.read_text(encoding="utf-8"))
        _api_list_cache["mtime"] = mtime
    return _api_list_cache["entries"]


def find_api_entry(code: str):
    """api-list.json에서 코드로 항목을 찾는다 (대소문자 무시). 없으면 None."""
    code_upper = code.strip().upper()
    for entry in _load_api_list():
        if entry.get("code") and entry["code"].upper() == code_upper:
            return entry
    return None


def search_api_entries(keyword: str | None = None):
    """코드/API명/업무구분에 keyword가 포함된 항목 검색 (대소문자 무시). keyword 없으면 전체."""
    entries = [e for e in _load_api_list() if e.get("code")]
    if not keyword:
        return entries
    kw = keyword.strip().lower()
    return [
        e
        for e in entries
        if kw in (e.get("code") or "").lower()
        or kw in (e.get("name") or "").lower()
        or kw in (e.get("category") or "").lower()
    ]


def _parse_choices(description: str):
    if not description:
        return []
    matches = list(_CHOICE_RE.finditer(description))
    if len(matches) < 2:
        # 선택지가 1개 이하로 파싱되면 열거형이 아니라 단순 예시/안내문일 가능성이 높아
        # 오탐으로 보고 버린다 (예: "ex)TSLA", "client_credentials").
        return []
    choices = []
    for i, m in enumerate(matches):
        code = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(description)
        label = description[start:end].strip().strip(",").strip()
        if label:
            choices.append((code, label))
    return choices


def _parse_length(type_len: str) -> int:
    m = _LENGTH_RE.search(type_len or "")
    return int(m.group(1)) if m else 1


def _parse_input_table(text: str):
    match = re.search(r"## INPUT \(요청 파라미터\)\s*\n\n(.*?)\n\n(?:###|---)", text, re.S)
    if not match:
        return []
    fields = []
    seen_names = set()
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] in ("항목영문명", ""):
            continue
        name_en = cells[0]
        if name_en in seen_names:
            # 원본 xlsx 명세에 동일 필드가 중복 행으로 들어간 경우가 있어(예: SSAM5764),
            # 사용자에게 같은 선택을 두 번 묻지 않도록 첫 등장만 남긴다.
            continue
        seen_names.add(name_en)
        name_kr = cells[1] if len(cells) > 1 else ""
        type_len = cells[2] if len(cells) > 2 else ""
        required = (cells[3] if len(cells) > 3 else "").strip().upper() == "Y"
        description = cells[4] if len(cells) > 4 else ""
        fields.append(
            ApiField(
                name_en=name_en,
                name_kr=name_kr,
                length=_parse_length(type_len),
                required=required,
                description=description,
                choices=_parse_choices(description),  # 필수여부 무관하게 항상 파싱
            )
        )
    return fields


def _parse_output_table(text: str):
    match = re.search(r"## OUTPUT \(응답 데이터\)\s*\n\n(.*?)\n\n(?:###|---)", text, re.S)
    if not match:
        return {}
    labels = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("항목영문명", ""):
            continue
        labels[cells[0]] = cells[1]
    return labels


def load_api_spec(code: str) -> "ApiSpec | None":
    """API 코드로 docs/api/md 명세를 찾아 파싱한다. 없으면 None."""
    entry = find_api_entry(code)
    if entry is None:
        return None
    md_path = DOCS_API_DIR / entry["source_file"]
    if not md_path.exists():
        return None
    text = md_path.read_text(encoding="utf-8")
    return ApiSpec(
        code=entry["code"],
        name=entry.get("name", entry["code"]),
        category=entry.get("category", ""),
        endpoint=urlsplit(entry.get("prod_url", "")).path,
        md_path=md_path,
        fields=_parse_input_table(text),
        output_labels=_parse_output_table(text),
    )


def blank_fill(api_field: ApiField) -> str:
    return " " * max(api_field.length, 1)


def selection_fields(spec: ApiSpec):
    """사용자가 번호로 골라야 하는 필드만 반환 (선택지가 있는 필드 — 필수여부 무관)."""
    return [f for f in spec.fields if f.choices]


def default_data_body(spec: ApiSpec) -> dict:
    """선택이 필요 없는 필드는 전부 기본값(공백 채움)으로 채운 dataBody. 선택지 있는 필드는 제외."""
    body = {}
    for f in spec.fields:
        if f.choices:
            continue
        body[f.name_en] = blank_fill(f)
    return body


def full_blank_body(spec: ApiSpec) -> dict:
    """모든 INPUT 필드를 선택지 유무와 무관하게 타입(길이)만큼 공백으로 채운 dataBody.

    `/call`(저수준 직접 호출)처럼 사용자가 원하는 필드만 값을 지정하고 나머지는
    전부 자동으로 채워야 하는 경우에 쓴다 — `default_data_body()`와 달리 선택지가
    있는 필드도 제외하지 않고 blank_fill한다(대화형 선택 UI가 없는 맥락이라서).
    """
    return {f.name_en: blank_fill(f) for f in spec.fields}


def execute_api_call(spec: ApiSpec, data_body: dict, token: str, host_url: str) -> dict:
    # 필수여부(Y/N)가 부정확하므로 사전 "필수 파라미터 누락" 검증을 하지 않는다 —
    # 실제 필수 여부는 KB 서버 응답으로 판단한다(required=[]).
    return call_business_api(
        api_name=spec.name,
        api_code=spec.code,
        endpoint=spec.endpoint,
        data_body=data_body,
        required=[],
        token=token,
        host_url=host_url,
    )


def describe_spec(spec: ApiSpec) -> str:
    """실행 전 미리보기: 어떤 필드가 선택 대상이고 어떤 필드가 공백으로 채워지는지 설명."""
    lines = [f"📋 {spec.code} {spec.name}  [{spec.category}]", f"엔드포인트: {spec.endpoint}"]
    if not spec.fields:
        lines.append("\nINPUT 파라미터 없음 — 바로 실행 가능합니다.")
        lines.append(f"\n/api {spec.code} 로 실행하세요.")
        return "\n".join(lines)

    lines.append("\nINPUT 파라미터: (KB 명세의 필수여부는 부정확해 표시하지 않음)")
    for f in spec.fields:
        if f.choices:
            choice_str = ", ".join(f"{c}:{label}" for c, label in f.choices)
            lines.append(f"  • {f.name_en}({f.name_kr}) → 실행 시 선택 필요: {choice_str}")
        else:
            desc_note = f" — {f.description}" if f.description else ""
            lines.append(f"  • {f.name_en}({f.name_kr}) → 공백 {f.length}자 자동 입력{desc_note}")

    lines.append(f"\n/api {spec.code} 로 실행하세요.")
    return "\n".join(lines)


def format_api_result(spec: ApiSpec, result: dict) -> str:
    """call_business_api() 반환값을 사람이 읽기 좋은 형태로 정리."""
    header = (result.get("body") or {}).get("dataHeader", {}) if isinstance(result.get("body"), dict) else {}
    body = (result.get("body") or {}).get("dataBody", {}) if isinstance(result.get("body"), dict) else {}

    ok = result.get("success")
    lines = [f"{'✅' if ok else '❌'} {spec.code} {spec.name} 실행 결과"]

    result_code = header.get("resultCode")
    result_message = header.get("resultMessage")
    if result_code or result_message:
        lines.append(f"결과코드: {result_code or '-'}  {result_message or ''}".rstrip())

    if not ok:
        error = (result.get("body") or {}).get("error") if isinstance(result.get("body"), dict) else None
        if error:
            lines.append(f"오류: {error}")

    labels = spec.output_labels
    lines.append("")
    if isinstance(body, dict) and body:
        for key, value in body.items():
            label = labels.get(key, key)
            if isinstance(value, list):
                lines.append(f"[{label}] {len(value)}건")
                for i, row in enumerate(value[:20], 1):
                    if isinstance(row, dict):
                        row_str = ", ".join(f"{labels.get(k, k)}={v}" for k, v in row.items())
                    else:
                        row_str = str(row)
                    lines.append(f"  {i}. {row_str}")
                if len(value) > 20:
                    lines.append(f"  ... 외 {len(value) - 20}건")
            else:
                lines.append(f"{label}: {value}")
    elif not body:
        lines.append("(응답 데이터 없음)")
    else:
        lines.append(str(body))

    return "\n".join(lines)
