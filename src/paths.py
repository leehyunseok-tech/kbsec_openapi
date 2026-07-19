"""
프로젝트 전역 경로 상수 — 런타임 참조 파일/폴더 위치의 단일 소스(Single Source of Truth).

과거에는 14개 모듈이 각자 `Path(__file__).resolve().parent...`로 프로젝트 루트를
독립 계산해 참조 파일 위치를 하드코딩하고 있었다. 이 모듈이 그 역할을 전담한다:

  - 어떤 파일이 런타임에 참조되는지 이 파일 하나만 보면 전부 파악할 수 있다.
  - 참조 파일/폴더를 옮기게 되면 여기 한 줄만 고치면 된다(사용처 전수 수정 불필요).

사용 규칙:
  - 프로젝트 루트 기준의 파일/폴더 경로가 필요하면 반드시 여기서 import 한다.
    새로 `Path(__file__).resolve().parent...`로 루트를 계산하는 코드를 만들지 말 것.
  - manage/generate 스크립트도 이 모듈을 쓴다(모듈 실행 `-m` 기준. 파일 직접 실행을
    지원하는 스크립트는 자기 위치로 sys.path를 부트스트랩한 뒤 import 한다).
  - 상세 설명·변경 절차: docs/개발환경/paths.md
"""

from pathlib import Path

# src/paths.py → src → 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── 설정 / 런타임 상태 (config/) ─────────────────────────────────────────────
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_DATA_DIR = CONFIG_DIR / "data"          # settings_manager 등 런타임 상태 저장 폴더
SETTINGS_JSON = CONFIG_DATA_DIR / "settings.json"      # 런타임 설정 (settings_manager.py)
SCHEDULES_JSON = CONFIG_DATA_DIR / "schedules.json"    # 명령 예약 (schedule_manager.py)
COOLDOWN_LOG_JSON = CONFIG_DATA_DIR / "cooldown_log.json"  # 재매수 쿨다운 (cooldown_log.py)

# ── 체결 로그 (logs/) ────────────────────────────────────────────────────────
LOGS_DIR = PROJECT_ROOT / "logs"  # YYYYMMDD.csv (trade_logger/trade_analyzer/log_command)

# ── AI 자연어 변환 런타임 참조 (docs/) ───────────────────────────────────────
# ai_command_converter.py가 Claude 시스템 프롬프트에 그대로 삽입하는 규칙 문서.
COMMAND_GUIDE_FOR_AI = PROJECT_ROOT / "docs" / "command_guide_for_ai.md"

# ── API 명세 파이프라인 (docs/api/ → src/api/) ───────────────────────────────
# xlsx(원본) → md(변환) → api-list.md/json(목록) → src/api/*.py(생성 코드) 순서.
DOCS_API_DIR = PROJECT_ROOT / "docs" / "api"
API_SPEC_XLSX_DIR = DOCS_API_DIR / "xlsx"      # KB 명세 원본 (업무구분별 폴더 구조)
API_SPEC_MD_DIR = DOCS_API_DIR / "md"          # 변환된 md — api_spec.py/spec_browser.py가 런타임 파싱
API_LIST_MD = DOCS_API_DIR / "api-list.md"     # 사람용 전체 API 목록 (generate_mst 검증에도 사용)
API_LIST_JSON = DOCS_API_DIR / "api-list.json" # 런타임용 전체 API 목록 (api_spec.py 등 6곳)
SRC_API_DIR = PROJECT_ROOT / "src" / "api"     # generate_api_client.py 산출물 위치

# ── 종목마스터 파이프라인 (mst/, docs/mst/) ──────────────────────────────────
# mst/origin(KB 배포 원본) → docs/mst(필드 선별 문서) + mst/api(런타임 데이터).
MST_ORIGIN_DIR = PROJECT_ROOT / "mst" / "origin"
MST_RUNTIME_DIR = PROJECT_ROOT / "mst" / "api"  # openapi_field_*.mst — stock_master.py가 로드
DOCS_MST_XLSX_DIR = PROJECT_ROOT / "docs" / "mst" / "xlsx"
DOCS_MST_MD_DIR = PROJECT_ROOT / "docs" / "mst" / "md"

# ── 웹 정적 파일 (src/web/static/) ───────────────────────────────────────────
WEB_STATIC_DIR = PROJECT_ROOT / "src" / "web" / "static"
