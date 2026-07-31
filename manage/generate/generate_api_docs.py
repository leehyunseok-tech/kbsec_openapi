"""
================================================================================
API 명세 자동 처리 스크립트 (xlsx 추가 → md 변환 + api-list 재생성)
================================================================================
docs/api/xlsx/ 하위(업무구분별 폴더 구조: OAuth, 국내주식/..., 해외주식/...)에
새 API 명세 xlsx 파일이 추가되면, 이 스크립트로 다음을 한 번에 처리합니다.

  1. 대상 xlsx 파일(들)을 docs/api/md/ 아래 동일한 상대 경로에 md로 변환
     (convert_xlsx_to_md.py 재사용 — 폴더 구조는 docs/api/xlsx와 동일하게 유지)
  2. docs/api/md/ 전체를 재스캔해 docs/api/api-list.json / api-list.md를
     최신 상태로 재생성 (manage/generate/generate_api_list.py 재사용 — 업무구분 컬럼 자동 포함)

--------------------------------------------------------------------------------
사용법
--------------------------------------------------------------------------------
  uv run python -m manage.generate.generate_api_docs
      → docs/api/xlsx/ 전체를 재변환 + api-list 재생성

  uv run python -m manage.generate.generate_api_docs "국내주식/계좌잔고"
      → docs/api/xlsx/국내주식/계좌잔고/ 폴더만 재변환 + api-list 재생성

  uv run python -m manage.generate.generate_api_docs "국내주식/계좌잔고/SSQM0004-예수금내역-20260717-191349.xlsx"
      → 해당 파일 하나만 재변환 + api-list 재생성

경로는 docs/api/xlsx 기준 상대경로 또는 절대경로 모두 허용합니다. api-list는
(부분 변환이더라도) 항상 docs/api/md 전체를 다시 스캔해 재생성하므로 결과가
항상 최신 상태로 일관됩니다.

새 업무구분 폴더(예: docs/api/xlsx/국내주식/새업무/)를 추가한 경우에도 그대로
동작합니다 — md 쪽에 동일한 폴더가 없으면 자동으로 생성됩니다.
================================================================================
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # sys.path 부트스트랩 전용 — 경로 상수는 src/paths.py에서
sys.path.insert(0, str(PROJECT_ROOT))  # 파일 직접 실행(-m 없이) 시에도 src.paths/manage.generate import가 풀리도록
from manage.generate import generate_api_list  # noqa: E402
from manage.generate.convert_xlsx_to_md import convert_single_file  # noqa: E402
from src.paths import API_SPEC_MD_DIR as MD_DIR
from src.paths import API_SPEC_XLSX_DIR as XLSX_DIR  # noqa: E402


def resolve_target(arg: str | None) -> Path:
    """인자를 실제 경로로 해석. 인자가 없으면 docs/api/xlsx 전체."""
    if arg is None:
        return XLSX_DIR

    candidate = Path(arg)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    # docs/api/xlsx 기준 상대경로로 우선 시도
    under_xlsx = XLSX_DIR / arg
    if under_xlsx.exists():
        return under_xlsx

    if candidate.exists():
        return candidate

    raise FileNotFoundError(f"경로를 찾을 수 없습니다: {arg} (docs/api/xlsx 기준 상대경로 또는 절대경로를 입력하세요)")


def xlsx_to_md_path(xlsx_path: Path) -> Path:
    """docs/api/xlsx/<업무구분...>/<파일>.xlsx → docs/api/md/<업무구분...>/<파일>.md"""
    rel = xlsx_path.resolve().relative_to(XLSX_DIR)
    return (MD_DIR / rel).with_suffix(".md")


def convert_target(target: Path) -> int:
    """target이 파일이면 1개, 폴더면 하위 모든 xlsx를 변환. 변환된 개수 반환."""
    xlsx_files = [target] if target.is_file() else sorted(target.rglob("*.xlsx"))

    if not xlsx_files:
        print(f"변환할 xlsx 파일이 없습니다: {target}")
        return 0

    for xlsx_path in xlsx_files:
        md_path = xlsx_to_md_path(xlsx_path)
        convert_single_file(str(xlsx_path), str(md_path))

    return len(xlsx_files)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    target = resolve_target(arg)

    print(f"대상: {target}")
    converted = convert_target(target)
    print(f"xlsx → md 변환 완료: {converted}개")

    print("api-list.json / api-list.md 재생성 중 (docs/api/md 전체 스캔)...")
    generate_api_list.main()


if __name__ == "__main__":
    main()
