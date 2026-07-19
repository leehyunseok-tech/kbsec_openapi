"""
================================================================================
API 명세 목록 생성 스크립트 (업무구분 포함, 폴더 재귀 스캔)
================================================================================
docs/api/md/ 폴더를 재귀적으로 스캔하여 전체 API 목록을 docs/api/api-list.md
(표 형태)와 docs/api/api-list.json(배열)으로 생성합니다.

md/ 폴더 구조가 `<업무1>/<업무2>/<파일>.md`(예: `국내주식/계좌잔고/SSQM0004-...md`)
형태이므로, md 루트 기준 파일의 상위 폴더 경로를 " > "로 이어붙여 "업무구분"
컬럼(JSON은 "category" 키)으로 기록합니다. (예: "국내주식 > 계좌잔고")

동일한 API 코드가 여러 파일로 중복 존재하는 경우(재수집 등으로 인한 중복
export) 파일명의 타임스탬프가 가장 최신인 파일 하나만 대표로 사용합니다.

사용법:
  uv run python -m manage.generate.generate_api_list

관련 스크립트: manage/generate/generate_api_client.py(SPEC_DIR/collect_entries/dedupe를
import해 재사용), manage/generate/generate_api_docs.py(convert_xlsx_to_md.py + 이
스크립트를 한 번에 실행하는 통합 스크립트) — 둘 다 이 모듈을
`from manage.generate.generate_api_list import ...`로 참조한다.
================================================================================
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # sys.path 부트스트랩 전용 — 경로 상수는 src/paths.py에서
sys.path.insert(0, str(PROJECT_ROOT))  # 파일 직접 실행(-m 없이) 시에도 src.paths import가 풀리도록
from src.paths import API_SPEC_MD_DIR as SPEC_DIR, API_LIST_MD as OUT_MD, API_LIST_JSON as OUT_JSON  # noqa: E402

# 파일명 형식: <코드?>-<이름>-YYYYMMDD-HHMMSS.md  (코드가 없는 경우도 있음, 예: "토큰 발급-...")
FILENAME_RE = re.compile(r"^(?P<title>.+)-(?P<date>\d{8})-(?P<time>\d{6})$")

FIELD_MAP = {
    "API 코드": "code",
    "API 명": "name",
    "API명": "name_raw",
    "API인증": "auth",
    "API보안": "security",
    "인터페이스": "interface",
    "데이터": "data_format",
    "버전": "version",
    "개발환경": "dev_url",
    "운영환경": "prod_url",
    "최종작성일": "written_at",
    "API설명": "description",
}


def parse_basic_info(text):
    """'## 기본 정보' 표를 파싱하여 {필드: 값} dict로 반환."""
    match = re.search(r"## 기본 정보\s*\n\n(.*?)\n\n---", text, re.S)
    if not match:
        return {}
    table = match.group(1)
    result = {}
    for line in table.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        key, value = cells[0], cells[1]
        value = value.strip("`").strip()
        field = FIELD_MAP.get(key)
        if field:
            result[field] = value
    return result


def collect_entries():
    entries = []
    for md_path in sorted(SPEC_DIR.rglob("*.md")):
        stem = md_path.stem
        m = FILENAME_RE.match(stem)
        title, date, time = (m.group("title"), m.group("date"), m.group("time")) if m else (stem, "", "")

        text = md_path.read_text(encoding="utf-8")
        info = parse_basic_info(text)

        code = info.get("code")
        name = info.get("name") or info.get("name_raw") or title

        rel_path = md_path.relative_to(SPEC_DIR)
        category = " > ".join(rel_path.parent.parts) if rel_path.parent.parts else ""

        entries.append(
            {
                "code": code,
                "name": name,
                "category": category,
                "description": info.get("description", ""),
                "interface": info.get("interface", ""),
                "data_format": info.get("data_format", ""),
                "version": info.get("version", ""),
                "dev_url": info.get("dev_url", ""),
                "prod_url": info.get("prod_url", ""),
                "written_at": info.get("written_at", ""),
                "source_file": f"md/{rel_path.as_posix()}",
                "_sort_key": f"{date}{time}",
            }
        )
    return entries


def dedupe(entries):
    """code(없으면 name)가 같은 항목 중 파일명 타임스탬프가 가장 최신인 것만 남김."""
    latest = {}
    for e in entries:
        key = e["code"] or e["name"]
        cur = latest.get(key)
        if cur is None or e["_sort_key"] > cur["_sort_key"]:
            latest[key] = e
    return sorted(latest.values(), key=lambda e: (e["category"], e["code"] or "", e["name"]))


def write_json(entries):
    payload = [{k: v for k, v in e.items() if k != "_sort_key"} for e in entries]
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(entries):
    lines = [
        "# KB증권 OpenAPI 목록",
        "",
        "`md` 폴더(업무구분별 하위 폴더) 내 개별 API 명세서를 스캔하여 자동 생성된 "
        "목록입니다. (생성 스크립트: `manage/generate/generate_api_list.py`)",
        "",
        f"총 {len(entries)}개 API",
        "",
        "| API 코드 | API 명 | 업무구분 | 설명 | 인터페이스 | 운영환경 URL | 최종작성일 | 명세 문서 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in entries:
        code = e["code"] or "-"
        name = e["name"]
        category = e["category"] or "-"
        desc = e["description"] or "-"
        interface = e["interface"] or "-"
        prod_url = e["prod_url"] or "-"
        written_at = e["written_at"] or "-"
        source = f"[{e['source_file']}]({e['source_file']})"
        lines.append(f"| {code} | {name} | {category} | {desc} | {interface} | {prod_url} | {written_at} | {source} |")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    entries = dedupe(collect_entries())
    write_md(entries)
    write_json(entries)
    print(f"{len(entries)}개 API 항목을 {OUT_MD.name}, {OUT_JSON.name}에 작성했습니다.")


if __name__ == "__main__":
    main()
