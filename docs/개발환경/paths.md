# src/paths.py — 경로 상수 모듈 (참조 파일 위치의 단일 소스)

> 이 문서는 `src/paths.py`가 무엇인지, 왜 만들었는지, 그리고 **참조 파일/폴더 구조가
> 바뀔 때 무엇을 해야 하는지**를 설명한다. 프로젝트 전체 구조가 궁금하면
> [프로젝트구조.md](프로젝트구조.md), 초보자용 안내는 [초보자가이드.md](초보자가이드.md) 참고.

## 1. 무엇인가

`src/paths.py`는 프로젝트가 **런타임/생성 시점에 참조하는 모든 파일·폴더의 경로 상수를
한 곳에 모아둔 모듈**이다. 파일 자체는 각자의 파이프라인이 소유하는 원래 위치
(`docs/`, `mst/`, `config/` 등)에 그대로 두고, "그 파일이 어디에 있는가"라는 정보만
이 모듈로 통합했다 — 물리적 위치 통합(예: `ref/` 폴더로 파일을 모으는 방식) 대신
**논리적 통합(경로 정의 통합)** 을 택한 것이다.

```python
# 사용 예 — 경로가 필요한 모듈은 직접 계산하지 않고 import 한다
from src.paths import MST_RUNTIME_DIR, COMMAND_GUIDE_FOR_AI
```

## 2. 왜 만들었나 (도입 배경)

도입 전에는 **14개 모듈이 각자** 아래처럼 프로젝트 루트를 독립 계산해 참조 파일
경로를 하드코딩하고 있었다.

```python
# 도입 전 — 14개 파일에 이런 코드가 제각각 존재했다
_GUIDE_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "command_guide_for_ai.md"
MST_DIR = Path(__file__).resolve().parent.parent.parent / "mst" / "api"
```

이 방식의 문제:

- **파일을 옮기면 사용처를 전수 수색·수정해야 한다.** 실제로 `docs/command_guide.md` →
  `command_guide_for_ai.md` 리네임, `manage/` 폴더 재배치 때마다 여러 파일을 고쳐야 했고,
  한 곳이라도 놓치면 AI가 규칙 문서를 못 읽는 식의 조용한 회귀가 생긴다.
- **"이 프로젝트가 런타임에 어떤 파일을 참조하는가"를 한눈에 볼 방법이 없다.** grep으로
  전수 조사해야만 알 수 있었다.
- 모듈 위치가 바뀌면(예: `src/utils` → 다른 깊이) `parent.parent.parent` 계산식 자체가
  틀어진다.

## 3. 장점 (디자인 패턴 관점)

| 관점 | 설명 |
|---|---|
| **단일 진실 공급원(SSoT)** | 참조 파일 위치의 정의가 `src/paths.py` 한 곳뿐 — 정의가 흩어져서 생기는 불일치(드리프트)가 원천적으로 불가능하다. |
| **변경 비용 최소화** | 파일/폴더를 옮겨도 `paths.py` 한 줄만 고치면 모든 사용처가 자동으로 따라온다. |
| **가시성** | "런타임 참조 파일 전체 목록"이 이 파일 하나에 주석과 함께 정리되어 있다 — 신규 참여자가 grep 없이 파악 가능. |
| **파이프라인 보존** | `docs/api/md`(xlsx 미러 + 웹 API 명세 트리), `mst/`(원본→가공본) 같은 "원본과 산출물이 짝으로 묶인" 폴더 구조를 깨지 않는다. 물리적으로 `ref/`에 모았다면 이 결합이 깨졌을 것이다. |

## 4. 현재 정의된 상수와 사용처

| 상수 | 실제 경로 | 주요 사용처 |
|---|---|---|
| `PROJECT_ROOT` | 프로젝트 루트 | (다른 상수의 기준점) |
| `CONFIG_DIR` / `CONFIG_DATA_DIR` | `config/`, `config/data/` | `settings_manager.py` |
| `SETTINGS_JSON` | `config/data/settings.json` | `settings_manager.py` (런타임 설정) |
| `SCHEDULES_JSON` | `config/data/schedules.json` | `schedule_manager.py` (명령 예약) |
| `COOLDOWN_LOG_JSON` | `config/data/cooldown_log.json` | `cooldown_log.py` (재매수 쿨다운) |
| `LOGS_DIR` | `logs/` | `trade_logger.py` / `trade_analyzer.py` / `log_command.py` |
| `COMMAND_GUIDE_FOR_AI` | `docs/command_guide_for_ai.md` | `ai_command_converter.py` (AI 시스템 프롬프트에 삽입) |
| `DOCS_API_DIR` | `docs/api/` | `api_spec.py` / `generate_api_client.py` |
| `API_SPEC_XLSX_DIR` | `docs/api/xlsx/` | `generate_api_docs.py` (명세 원본) |
| `API_SPEC_MD_DIR` | `docs/api/md/` | `api_spec.py` / `spec_browser.py` / generate 스크립트 |
| `API_LIST_MD` | `docs/api/api-list.md` | `generate_api_list.py` / `generate_mst.py` (코드 검증) |
| `API_LIST_JSON` | `docs/api/api-list.json` | `api_spec.py` (→ `/api`·`/call`·AI api 이름 목록 등 6곳) |
| `SRC_API_DIR` | `src/api/` | `generate_api_client.py` (산출물 위치) |
| `MST_ORIGIN_DIR` | `mst/origin/` | `generate_mst.py` (KB 배포 원본) |
| `MST_RUNTIME_DIR` | `mst/api/` | `stock_master.py` (종목마스터 런타임 데이터) |
| `DOCS_MST_XLSX_DIR` / `DOCS_MST_MD_DIR` | `docs/mst/xlsx`, `docs/mst/md` | `generate_mst.py` (필드 선별 문서) |
| `WEB_STATIC_DIR` | `src/web/static/` | `web/app.py` (정적 파일 서빙) |

`LOGS_DIR`, `SCHEDULES_JSON`, `COOLDOWN_LOG_JSON`은 최초 기록 시점에 생성되는
파일/폴더라 처음에는 존재하지 않을 수 있다(정상).

## 5. 참조 구조가 바뀔 때 해야 할 일

### 5-1. 참조 파일/폴더를 **옮기거나 이름을 바꿀 때**

1. 실제 파일/폴더를 이동·리네임한다 (`git mv`).
2. `src/paths.py`에서 **해당 상수 한 줄만** 새 경로로 고친다. (사용처는 고칠 필요 없음)
3. 검증: `uv run python -m compileall -q src manage` + 터미널 클라이언트로 해당 기능 1회 실행.
4. 관련 문서(`CLAUDE.md`, 이 문서의 4절 표, `manage.md` 등)에서 경로 표기를 갱신한다.

### 5-2. **새 참조 파일**이 생길 때

1. `src/paths.py`에 성격에 맞는 구역(설정/로그/AI/API 명세/종목마스터/웹)에 상수를 추가하고,
   무엇이 어디서 쓰는 파일인지 주석을 단다.
2. 사용하는 모듈에서는 `from src.paths import ...`로 가져다 쓴다.
   **`Path(__file__).resolve().parent...`로 루트를 다시 계산하는 코드를 새로 만들지 말 것.**
3. 이 문서 4절 표에 한 줄 추가한다.

### 5-3. `src/paths.py` 자체를 옮기거나 폴더 깊이가 바뀔 때

`PROJECT_ROOT = Path(__file__).resolve().parent.parent`는 "`src/paths.py` → `src` →
프로젝트 루트" 2단계 상향을 전제한다. `paths.py`의 위치가 바뀌면 이 한 줄의
`parent` 개수만 맞춰 고치면 된다.

### 5-4. `manage/generate` 스크립트에서 쓸 때 (주의)

`manage/generate/*.py`는 `uv run python -m manage.generate.<이름>`(모듈 실행)이 표준이지만,
파일 직접 실행도 지원하기 위해 **import 전에 sys.path 부트스트랩**을 유지한다:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # sys.path 부트스트랩 전용
sys.path.insert(0, str(PROJECT_ROOT))
from src.paths import API_SPEC_MD_DIR as SPEC_DIR  # noqa: E402
```

이 `PROJECT_ROOT`는 **sys.path 등록에만** 쓰고, 파일 경로 조합에는 절대 쓰지 않는다
(경로 조합은 전부 `src.paths` 상수로).

## 6. 하지 말아야 할 것

- ❌ 개별 모듈에서 `Path(__file__)...`로 루트를 계산해 참조 경로를 만드는 것
  (= 도입 전 방식으로의 회귀).
- ❌ `paths.py`에 경로가 아닌 설정값(숫자/문자열 설정)을 넣는 것 — 설정은
  `config/config.py`와 `config/data/settings.json`의 영역이다.
- ❌ 상수를 우회해 문자열 리터럴로 경로를 조합하는 것 (`"docs/api/md"` 등).
