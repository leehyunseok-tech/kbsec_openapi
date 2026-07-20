"""
웹 "API 명세" 페이지 백엔드 로직 — docs/api/md 폴더 트리를 그대로 탐색해
명세(md) 보기 + 테스트 호출용 기본 요청 본문 구성을 제공한다.

api_spec.py(런타임 /api·/call 실행용)와의 관계:
  - 트리/파일 목록은 api-list.json이 아니라 **폴더 구조 그대로**를 보여준다
    (사용자 요구: OAuth/국내주식/해외주식 → 하위 업무구분 → 파일명 목록).
  - 필드 파싱은 api_spec의 _parse_input_table을 재사용한다. KB 명세의 필수여부(Y/N)는
    부정확해 무시하며, 편집 폼 기본값은 선택지가 있으면 첫 번째 선택지, 없으면 빈
    문자열로 둔다(사용자가 값을 채워 넣도록).
"""

import re
from pathlib import Path

from src.utils.api_spec import (
    DOCS_API_DIR,
    _parse_choices,
    _parse_input_table,
    find_api_entry,
)

MD_ROOT = DOCS_API_DIR / "md"

# 파일명 끝의 "-YYYYMMDD-HHMMSS" 타임스탬프 (표시할 때 떼어냄)
_TS_RE = re.compile(r"-\d{8}-\d{6}$")
_CODE_RE = re.compile(r"^([A-Z]{2,4}[A-Z0-9]{4,8})-")


def _display_label(stem: str) -> str:
    """'SSQM0004-예수금내역-20260717-191349' → 'SSQM0004-예수금내역'"""
    return _TS_RE.sub("", stem)


def _extract_code(stem: str):
    """파일명 앞의 TR코드 추출. OAuth '토큰 발급-...'처럼 코드가 없으면 None."""
    m = _CODE_RE.match(stem)
    return m.group(1) if m else None


def build_tree():
    """docs/api/md 하위 폴더 구조를 재귀로 순회해 트리 JSON을 만든다."""

    def walk(directory: Path):
        node = {"name": directory.name, "dirs": [], "files": []}
        for child in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name)):
            if child.is_dir():
                node["dirs"].append(walk(child))
            elif child.suffix.lower() == ".md":
                stem = child.stem
                node["files"].append(
                    {
                        "label": _display_label(stem),
                        "code": _extract_code(stem),
                        "path": child.relative_to(MD_ROOT).as_posix(),
                    }
                )
        return node

    root = walk(MD_ROOT)
    return root["dirs"]  # 최상위(md/) 자체는 껍데기이므로 카테고리 목록만


def _safe_md_path(rel_path: str) -> Path | None:
    """경로 조작(..) 차단 — md 루트 밖이나 .md 아닌 파일은 거부."""
    try:
        p = (MD_ROOT / rel_path).resolve()
    except (OSError, ValueError):
        return None
    if not str(p).startswith(str(MD_ROOT.resolve())) or p.suffix.lower() != ".md":
        return None
    return p if p.exists() else None


def _field_default(field) -> str:
    """편집 폼의 기본값 — 선택지 있으면 첫 코드, 그 외 빈 문자열(필수여부는 무시)."""
    choices = field.choices or _parse_choices(field.description)
    if choices:
        return choices[0][0]
    return ""


def load_detail(rel_path: str):
    """명세 상세 — md 원문 + 편집 폼용 필드 목록 + 기본 요청 본문. 실패 시 None."""
    md_path = _safe_md_path(rel_path)
    if md_path is None:
        return None

    text = md_path.read_text(encoding="utf-8")
    stem = md_path.stem
    code = _extract_code(stem)

    entry = find_api_entry(code) if code else None
    endpoint = ""
    name = _display_label(stem)
    if entry:
        from urllib.parse import urlsplit

        endpoint = urlsplit(entry.get("prod_url", "")).path
        name = entry.get("name") or name

    fields = _parse_input_table(text)
    field_list = []
    data_body = {}
    for f in fields:
        choices = f.choices or _parse_choices(f.description)
        default = _field_default(f)
        data_body[f.name_en] = default
        field_list.append(
            {
                "name_en": f.name_en,
                "name_kr": f.name_kr,
                "length": f.length,
                "required": f.required,
                "description": f.description,
                "choices": [{"code": c, "label": l} for c, l in choices],
                "default": default,
            }
        )

    return {
        "label": _display_label(stem),
        "code": code,
        "name": name,
        "endpoint": endpoint,
        "executable": bool(code and entry and endpoint),
        "markdown": text,
        "fields": field_list,
        "data_body": data_body,
    }
