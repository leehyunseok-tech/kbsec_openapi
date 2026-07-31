# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# kbsec_api

KB증권 OpenAPI(REST) 기반 자동매매 시스템 — 텔레그램/터미널/웹 트리플 클라이언트.

## 언어 규칙 (필수)

- 이 프로젝트에서 사용자와 나누는 모든 질문/응답은 **반드시 한글로** 한다 (계정 공통 규칙과 동일,
  이 프로젝트에도 강력히 적용).

## 개발 환경

- Python 프로젝트 의존성/가상환경은 `uv`로 관리한다 (`pyproject.toml`, `.venv`). `requires-python = ">=3.14"`.
- 패키지 설치: `uv add <패키지명>`, 스크립트 실행: `uv run <파일>` 또는 `uv run python ...`.
- 최초 셋업: `config/config.example.py`를 `config/config.py`로 복사해 실제 키를 채운다 (`config.py`는 gitignore 대상 — 실제 앱키/텔레그램 토큰/Claude 키가 들어 있으므로 **어떤 응답/로그/커밋에도 원문을 노출하지 않는다**. 프로젝트는 GitHub 공개 예정).

## 자주 쓰는 명령어

```bash
# 클라이언트 실행 (모듈 실행 필수 — 아래 "소스 레이아웃" 참고)
uv run python -m src.run.terminal          # 터미널 클라이언트 (개발/테스트 시 기본)
uv run python -m src.run.telegram          # 텔레그램 Agent
uv run python -m src.run.web               # 웹 (http://localhost:8000)
uv run python -m src.run.web token         # 웹 + config.py 키로 자동 로그인 (로컬 전용)

# 코드/데이터 재생성 (산출물 직접 수정 금지)
uv run python -m manage.generate.generate_api_docs    # docs/api/xlsx → md 변환 + api-list 재생성 (새 명세 추가 시 1단계)
uv run python -m manage.generate.generate_api_client  # docs/api/md → src/api/*.py + registry.py (2단계)
uv run python -m manage.generate.generate_api_list    # api-list.md/json만 재생성 (generate_api_docs에 포함됨)
uv run python -m manage.generate.generate_mst         # mst/origin → 종목마스터 문서+런타임 데이터
```

- **새 API 명세를 추가하는 표준 순서**: `docs/api/xlsx/<업무구분>/`에 xlsx를 넣고 → `generate_api_docs` → `generate_api_client`. `generate_api_docs`는 인자로 하위 경로/파일 하나만 지정해 부분 재변환도 된다(예: `... generate_api_docs "국내주식/계좌잔고"`).

- 프로젝트 루트의 통합 런처 `run-kbsec-openapi.bat`/`.sh`(인자: `telegram`/`terminal`/`web [token]`, 기본 `web`)는 `manage/run/run-*.*`를 감싸는 래퍼일 뿐이며 **gitignore 대상 — `manage/install/install-project.*` 실행 시 OS에 맞게 생성되는 로컬 산출물**이다. 저장소에 없다고 지우거나 다시 만들어 커밋하지 말 것.
- 프로젝트 루트의 `install-kbsec-openapi.bat`/`.sh`는 위 런처와 성격이 **정반대**다 — **커밋 대상(gitignore 아님)**이고, `manage/install/install-project.bat`/`.sh`를 실행하는 대표 진입점이며, **설치가 성공하면 어느 쪽을 실행했든 둘 다(`.bat`+`.sh`) 삭제**하도록 설계된 1회용 스크립트다(실패 시엔 둘 다 재시도를 위해 남겨둠 — 설치 성공 여부와 무관하게 한쪽만 지워지는 일은 없다). 따라서 정상 설치를 마친 로컬 작업 트리에는 이 두 파일이 없는 게 정상이고, 그 상태에서 `git status`는 둘 다 "deleted"로 보여준다 — 되살리거나 커밋하지 말 것(저장소/새 클론에는 그대로 남아 있다). 재설치가 필요하면 `manage/install/install-project.*`를 직접 실행하면 된다(멱등 — 이미 설치된 항목은 건너뜀).
- 자동화된 테스트 스위트/린터는 없다. 변경 검증은 `uv run python -m compileall -q src`(문법), `node --check src/web/static/js/*.js`(웹 JS), 그리고 터미널 클라이언트나 일회성 스크립트로 해당 기능을 직접 호출해 확인하는 방식이다. 실제 API 호출 검증은 운영환경(실거래) 계정이라 주문 계열은 특히 주의.

## 커밋 메시지 규칙

- 형식은 `<타입>: <한글 요약>`이며 **제목·본문 모두 한글**로 쓴다(코드 주석도 한글이 기본).
- 실제로 쓰이는 타입: `feat`/`feat(web)`, `fix`, `docs`, `refactor`, `web`, `src`, `mst`, `skill`, `install`.
  범위가 웹이면 `web`, 종목마스터면 `mst`, `agent-skill/`이면 `skill`, 설치/실행 스크립트면 `install`.
- 본문에는 "무엇을 바꿨는지"보다 **왜 그렇게 했는지와 배경**을 적는 것이 이 저장소의 관례다(기존 커밋 참고).

## 프롬프트 히스토리 기록 규칙

- 이 프로젝트에서 사용자와 나눈 질문/답변은 `docs/prompt/prompt_history.md`에 순서대로 기록한다.
- 새 대화가 시작되어도 이 규칙을 계속 적용하여 해당 파일에 이어서 기록한다.
- 형식: `## YYYY-MM-DD` 날짜 헤더 아래 `### Q: ...` / `### A: ...` 쌍으로 기록한다.
- `docs/prompt/`는 **gitignore 대상**(공개 저장소에 대화 기록을 남기지 않는 정책)이다. 로컬에만 존재하는 것이 정상이므로 커밋 대상으로 삼지 말 것.

## 개발환경 문서 갱신 규칙

- 개발환경(패키지 관리자, 의존성, 실행/빌드 방법 등)과 관련된 변경사항이 생길 때마다 `docs/개발환경/개발환경.md`에 내용을 계속 추가/갱신한다.
- 새 대화가 시작되어도 이 규칙을 계속 적용한다.

## 프로젝트 구조

KB증권 REST API를 활용한 텔레그램/터미널/웹 기반 자동매매 시스템. 전체 기능 목록은 `docs/features.md` 참고.

**중요한 특성**: KB API 74개는 전부 REST(POST)이며 실시간 웹소켓이 없다. 실시간 시세가 필요한
기능(트레일링 스탑, 자동 손절매 등)은 REST 폴링으로 구현했고, 조건검색식 실시간거래(jggs/cond)·VI감시·
테마분석·공매도분석은 KB에 대응 API가 없어 지원하지 않는다 (`docs/features.md` 8절 참고).

**개발환경(모의투자) 미제공**: KB증권은 아직 개발환경(`ddeveloper.kbsec.com`, 모의투자)을 제공하지 않으며
운영환경(`developer.kbsec.com`, 실거래)만 사용 가능하다. `src/run/telegram.py`/`src/run/terminal.py`의 로그인은
`real`만 안내하고 자동 로그인 기본값도 `real`이다. `dev_client_key`/`dev_client_secret`과 `login dev` 코드
경로는 KB가 추후 개발환경을 열 경우를 대비해 남겨뒀지만 현재는 정상 동작하지 않으므로, 문서·안내 메시지·
`docs/command_guide_for_ai.md`(AI 참조 문서)에 새로 추가할 때도 `dev`를 정상 옵션처럼 노출하지 않는다.

**소스 레이아웃(`src/`)**: 실행 코드는 `src/` 하단에 있고, `config/`·`docs/`는 프로젝트 루트에 그대로 둔다.
`telegram.py`/`terminal.py`는 `src/run/`으로 옮기면서 `uv run python -m src.run.telegram`처럼 모듈 실행(`-m`)
방식으로 구동한다 — 프로젝트 루트가 `sys.path`에 올라와야 `from src.utils...`/`from src.api...`/
`from src.msgr...`/`from src.commands...` 형태의 절대 임포트가 동작하기 때문. `manage/run/run-telegram.*`/`manage/run/run-terminal.*` 스크립트가
이 호출 방식을 그대로 감싸고 있으니 직접 `python src/run/telegram.py`처럼 실행하지 말 것. 런처(`run-kbsec-openapi.bat`/`.sh`)의 인자도
`telegram`/`terminal`/`web`이며(과거엔 `main`이었으나 텔레그램과의 연결이 이름만으로 드러나도록 `telegram`으로 개명), `manage/run/run-telegram.*`가 그 인자에 대응한다.

- `config/` — `config.py`(gitignore 대상, 실제 키), `config.example.py`(템플릿). 운영/개발 호스트 URL, client_key/client_secret, 텔레그램/Claude API 키, 토큰 발급용 device_info.
- `src/paths.py` — **런타임 참조 파일/폴더 경로 상수의 단일 소스**. `docs/command_guide_for_ai.md`, `docs/api/`(md/api-list), `mst/api/`, `config/data/*.json`, `logs/`, `src/web/static/` 등 프로젝트 루트 기준 경로가 필요하면 반드시 여기서 import 한다 — 개별 모듈에서 `Path(__file__).resolve().parent...`로 루트를 다시 계산하지 말 것. 참조 파일을 옮길 때는 이 파일 한 줄만 고치면 된다(절차·상수 목록: `docs/개발환경/paths.md`). `manage/generate/*.py`는 파일 직접 실행 지원용 sys.path 부트스트랩만 자체 유지하고 경로 조합은 전부 `src.paths`를 쓴다.
- `src/api/client.py`, `src/api/auth.py` — **수기 작성**, 공용 요청 봉투(dataHeader/dataBody) 구성 및 토큰 발급 로직.
- `src/api/*.py`(그 외 10개 모듈), `src/api/registry.py` — **자동 생성 파일, 수동 수정 금지**. `manage/generate/generate_api_client.py` 재실행으로만 갱신.
- `src/utils/` — API 클라이언트 유틸(`api_logger.py`, `http_client.py`, `session.py`, `device_info.py`) + 브로커 무관 유틸(`settings_manager.py`, `schedule_manager.py`, `trade_logger.py`, `trade_analyzer.py`, `cooldown_log.py`, `command_executor.py`, `ai_command_converter.py`, `stock_resolver.py`, `api_resolver.py`) + API 직접호출(`api_spec.py` — `docs/api/md` 명세를 런타임 파싱해 `/api`·`/call`이 registry 없이 임의 API를 실행, `direct_api_command.py` — `api_spec.py`를 재사용해 74개 API를 `/{코드}-{API명}` 전용 슬래시 커맨드로 즉시 실행) + 터미널 대화형 입력(`terminal_ui.py` — Enter 확인/화살표+숫자 선택 메뉴, cross-platform raw 키 입력) + 자동매매 폴링 모니터(`monitor_base.py`와 이를 상속하는 `*_monitor.py`, `stoploss_manager.py`) + 조회 헬퍼(`stock_master.py`, `price_lookup.py`, `chart_analysis.py`, `holdings_valuation.py`, `formatting.py`).
- `mst/` (프로젝트 루트) — 종목마스터 `.mst` 파일(원본 `origin/` + 가공본 `api/`). `src/utils/stock_master.py`가 실제로 로드/검색하는 런타임 데이터는 `mst/api/openapi_field_kospi-kosdaq.mst`(코스피+코스닥 통합)/`mst/api/openapi_field_foren-us.mst`(해외) 두 파일이며, AI 자연어 변환이 생성한 종목명을 실제 코드로 바꾸는 결정적(deterministic) 근거로도 쓰인다(`src/utils/stock_resolver.py`). 이 두 파일은 코드값(예: `ST`, `Y/N`)을 사람이 읽기 좋은 텍스트(`주식`, `거래정지`)로 이미 바꿔둔 상태라 `/stcd` 등에서 그대로 표시해도 된다 — 단 해외 거래소코드(`NAS`/`NYS`/`AMX`)만은 예외로 원본을 유지한다(`buy_command.py`/`sell_command.py`/`srch_command.py`가 KB 주문/시세 API의 `krx_cd` 파라미터로 그대로 전달하기 때문; 표시용 한글명은 `OverseasStock.exchange_name`에 별도로 있음). **생성은 `manage/generate/generate_mst.py` 파이프라인이 전담**: `mst/origin/`에 KB 배포 원본만 갈아 놓고 `uv run python -m manage.generate.generate_mst`를 실행하면 필드 선별 문서(`docs/mst/xlsx/openapi_mst_*.xlsx` + `docs/mst/md/openapi_mst_*.md`)와 런타임 데이터(`mst/api/openapi_field_*.mst`)가 중간 파일 없이 전부 재생성된다. 필드 인덱스/코드표의 근거는 KB 공식 명세(`docs/mst/xlsx/mst_*.xlsx`)이며, 어떤 필드를 쓸지는 스크립트 안 `CURATION` 표가 단일 소스다. 산출 문서·데이터를 손으로 고치지 말 것(재실행 시 덮어써짐). (과거의 `mst/create_openapi_mst.py`+`generate_field_reference_mst.py` 2단계 구조는 타 증권사 레이아웃을 가정한 필드 라벨 오류 — 예: 소수점매매상태를 '주문유형'으로, 현금증거금율구분을 '매매수량단위코드'로 해석 — 가 있어 폐지·교정됨.)
- `manage/` (프로젝트 루트, **`src/`가 아님** — 런타임 코드가 전혀 아니므로 `config/`·`docs/`·`mst/`와 같은 층위의 독립 폴더) — 운영/관리 스크립트 전체를 모아둔 곳. 세 하위 폴더로 나뉜다: `manage/generate/`(데이터·코드 생성 스크립트, `uv run python -m manage.generate.<파일명>`으로 실행 — `generate_mst.py`는 종목마스터 파이프라인(위 `mst/` 항목 참고), 나머지 4종(`convert_xlsx_to_md.py`/`generate_api_list.py`/`generate_api_client.py`/`generate_api_docs.py`)은 `docs/api/xlsx/*.xlsx` → `docs/api/md/*.md` → `docs/api/api-list.md`/`.json` → `src/api/*.py`+`registry.py` 순으로 이어지는 API 명세 자동 생성 체인이며 `generate_api_docs.py`가 xlsx→md 변환+목록 갱신을 한 번에 묶어 실행함), `manage/run/`(텔레그램/터미널/웹 클라이언트 실행 스크립트, 과거 프로젝트 루트의 `run-*.bat`/`run-*.sh`), `manage/install/`(신규 클론 환경 설치 스크립트, 과거 루트의 `install-project.bat`/`.sh`) — `manage/run/`·`manage/install/`의 `.bat`/`.sh`는 프로젝트 루트에서 두 단계 아래로 옮겨졌으므로 내부 `cd`가 `%~dp0..\..`(bat)/`$(dirname ...)/../..`(sh)로 프로젝트 루트까지 되짚어가도록 되어 있다. `docs/`에는 `.py` 파일이 전혀 없다(전부 `manage/generate/`로 이동됨). 각 스크립트의 상세 역할·삭제 가능 여부·산출물·실행 시점은 `docs/개발환경/manage.md` 참고.
- `src/msgr/telegram/` — `tel_receive.py`/`tel_send.py`(텔레그램 Bot API 전송계층). 추후 다른 메신저(디스코드/슬랙 등)를 추가하면 `src/msgr/<백엔드>/`로 나란히 추가할 예정. (과거 `src/messenger/`였으나 `src/msgr/`로 리네임됨 — 상세는 `docs/개발환경/개발환경.md` 참고.)
- `src/commands/` — 명령 핸들러(`{name}_command.py`, 함수 1개 = 명령 1개). 메신저 종류와 무관한 공용 로직이라 `msgr/`가 아닌 `src/` 바로 아래 둠 — `telegram.py`/`terminal.py`/`web`이 동일하게 호출한다.
- `src/web/` — 웹 인터페이스 구현 전체. `app.py`(FastAPI — 정적 파일 서빙 + `/api/*` 순수 JSON 라우트, Jinja2 등 서버 템플릿 없음), `client.py`(`WebClient` — 브라우저 세션 1개당 인스턴스 1개, **다중 사용자**라 config.py 앱키로 자동 로그인하지 않고 설정 화면에서 사용자별 client_key/client_secret을 받아 메모리에만 보관), `session_store.py`(쿠키 `kbsec_web_sid` ↔ WebClient 인메모리 매핑), `spec_browser.py`(`docs/api/md` 폴더 구조를 그대로 읽어 웹 "API 명세" 화면 트리를 구성), `static/`(순수 HTML+CSS+JS 프론트엔드 — 외부 라이브러리/CDN 없음). **주의**: 설정값·자동매매 감시목록(`config/data/settings.json`)은 서버 공용이라 웹 사용자 간 공유된다(문서화된 제약).
  - **인증은 2계층이며 서로 별개다**: ① 화면 접속 관문 — `app.py`의 opt-in HTTP Basic Auth 미들웨어. `KBSEC_WEB_BASIC_AUTH_USER`/`..._PASS` 환경변수(없으면 config.py의 `web_basic_auth_user`/`web_basic_auth_pass`)를 **둘 다** 채웠을 때만 켜지며, 정적 파일과 `/api/*` 전 경로를 막는다. ② KB 계좌 로그인 — ①을 통과한 뒤 설정 화면에서 입력하는 client_key/client_secret. 기본 바인딩은 `127.0.0.1`이라 로컬에서는 ①이 꺼져 있어도 되지만, `KBSEC_WEB_HOST=0.0.0.0` 등으로 외부에 노출할 때는 ①을 반드시 켠다. 비밀번호 비교는 non-ASCII 때문에 `secrets.compare_digest`에 str을 넘기면 500이 나므로 UTF-8 바이트로 인코딩해 비교한다(회귀 주의).
- `src/run/telegram.py` — `TelegramBot`: 텔레그램 폴링 기반 운영 클라이언트. (과거 `main.py`였으나 런처 인자 `telegram`과 이름을 맞추기 위해 `telegram.py`로 리네임됨.)
- `src/run/terminal.py` — `TerminalClient`: `telegram.py`와 동일한 명령 핸들러를 공유하는 터미널 클라이언트(텔레그램 불필요) + API 코드 기반 저수준 직접 호출(`call`/`info`/`list`).
- `src/run/web.py` — 웹 클라이언트 실행 진입점(uvicorn 구동만 담당, 구현은 전부 `src/web/`). `manage/run/run-web.bat`/`manage/run/run-web.sh`, 기본 http://localhost:8000, `KBSEC_WEB_HOST`/`KBSEC_WEB_PORT` 환경변수로 변경.
- `src/run/command_pipeline.py` — `CommandPipelineMixin`: 세 클라이언트(telegram/terminal/web)가 공유하는 AI 변환 이후 처리(종목명/API명 로컬 해석 → 선택/확인 세션 → 일괄 실행)와 모니터 콜백의 **단일 소스**. 파이프라인 로직을 고칠 때는 개별 클라이언트가 아니라 이 파일을 고친다 (양쪽에 복사돼 있던 시절 드리프트 버그가 실제로 발생했음).
- `docs/command_guide_for_ai.md` — AI 자연어 변환이 **런타임에 참조**하는 명령어 규칙 문서 (아래 필수 규칙 참고).
- `docs/개발환경/` — 사람이 읽는 참고 문서. `개발환경.md`(패키지 관리자/의존성/실행 방법, 변경 시마다 계속 갱신), `command_summary.md`(`/`로 시작하는 슬래시 명령어 전체 요약/예시), `manage.md`(`manage/` 폴더에 있는 관리 스크립트 전체의 역할·삭제 가능 여부·산출물·런타임 사용처·실행 시점), `paths.md`(`src/paths.py` 경로 상수 모듈의 배경/상수 목록/변경 절차), `프로젝트구조.md`(전체 구조·데이터 흐름 mermaid 다이어그램 — 구조가 바뀌면 함께 갱신), `초보자가이드.md`(프로그래밍 초보자용 안내). `docs/command_guide_for_ai.md`(AI 런타임 참조용)와는 목적이 다르므로 혼동하지 말 것 — 명령어 추가/변경 시 이 폴더의 `command_summary.md`도 함께 갱신하는 것을 권장한다.
- `docs/features.md` — 전체 기능 목록과 담당 파일/매핑 API.
- `docs/api/` — API 명세 파이프라인. 자세한 내용은 `docs/api/README.md` 참고.
- `agent-skill/` (프로젝트 루트, 커밋 대상) — 이 저장소의 런타임 코드가 **아니라**, 외부 코딩 에이전트(Claude Code/Codex 등)용으로 별도 공개 저장소(`kbsec-skill`, `npx skills add`)에 배포하는 Agent Skill 패키지다. `SKILL.md`(진입점) + `references/workflows.md`·`references/endpoints.json` + `scripts/kbsec.py`(표준 라이브러리만 쓰는 독립 CLI — 이 프로젝트의 `src/`를 import 하지 않으므로 `src/` 변경이 자동 반영되지 않는다) 구조. **`references/endpoints.json`은 `docs/api/md`에서 파생된 산출물**이라 API 명세가 바뀌면 함께 재생성해야 한다(절차: `agent-skill/PUBLISHING.md` 5절 — `src/utils/api_spec.py` 파서를 돌리는 임시 스크립트). 주문 계열은 CLI 기본값이 dry-run이고 `--execute --yes`가 있어야 실제 실행된다 — 모의투자 환경이 없으므로 이 dry-run이 유일한 안전장치이니 약화시키지 말 것.
- `.claude/agents/` — 이 프로젝트 전용 서브에이전트 4종(`agent-api-spec-pipeline`, `agent-command-consistency`, `agent-trading-logic-reviewer`, `agent-docs-commit-helper`). `.claude/`는 gitignore 대상이라 로컬에만 있다.

### ⚠️ 필수 규칙 — 명령어 추가/변경 시 반드시 지켜야 할 것

명령어를 추가/변경/삭제할 때마다 **아래를 항상 동시에 완료**해야 합니다. 하나라도 빠지면 코드·도움말·AI 가이드가 불일치해 오작동합니다.

1. `src/commands/{name}_command.py`에 `handle_{name}(args, session, ...)` 구현
2. `src/run/telegram.py`의 `self.commands` 딕셔너리와 `HELP_TEXT`에 등록
3. `src/run/terminal.py`의 `TerminalClient.commands` 딕셔너리에도 동일하게 등록
4. `src/web/client.py`의 `WebClient.commands` 딕셔너리에도 동일하게 등록 (트리플 클라이언트 아키텍처 — `telegram.py`/`terminal.py`/`web/client.py`는 같은 핸들러를 공유해야 함)
5. **`docs/command_guide_for_ai.md`에 해당 명령어 섹션 추가/수정** — 이 문서는 `src/utils/ai_command_converter.py`가 Claude API 시스템 프롬프트에 그대로 삽입하는 실제 런타임 참조 문서다. 갱신하지 않으면 AI가 자연어를 잘못된 명령어로 변환한다.
6. `docs/features.md`의 해당 기능 상태도 필요시 갱신
7. **`src/commands/command_meta.py`의 `COMMANDS_META`에 한글 명령 항목 추가** — 명령어는 **한글이 기본, 영문은 숨김 별칭** 체계다(`login`과 저수준 `/api`·`/call`·`/info`·`/list`만 영문 예외). 각 클라이언트는 `self.commands`(영문 키)를 만든 뒤 `self.commands.update(korean_command_map(self.commands))` 한 줄로 한글 별칭을 일괄 등록한다. `command_meta.py`는 이 한글↔영문 매핑의 단일 소스이자, 웹 "/" 자동완성 드롭다운(`GET /api/commands`)의 데이터 소스다. 새 명령을 추가하면 여기에도 등록해야 자동완성·한글 별칭이 반영된다. (AI 변환기는 계속 영문을 출력하고 별칭으로 실행되므로 `docs/command_guide_for_ai.md`는 영문 기준을 유지한다.)

**예외 — `commands` 딕셔너리를 거치지 않는 명령들**: `/call`·`/info`·`/list`(저수준 직접 호출)와 `/{API코드}-{API명}` 형태의 API 전체 자동 실행 커맨드 74개는 위 2~4번(`commands` 딕셔너리 등록)을 따르지 않는다. 이들은 각 클라이언트 `_dispatch_direct()`의 "알 수 없는 명령어" 폴백 직전에서 하드코딩 분기(`/call`류) 또는 동적 판정(`src/utils/direct_api_command.py`의 `resolve_direct_command`)으로 처리된다. 74개 전용 커맨드는 `docs/api/api-list.json` + `docs/api/md/*.md`만 읽어 `api_spec.py` 로직을 재사용하므로, 명세가 추가/변경되면 코드 수정 없이 자동으로 새 커맨드가 생긴다. 이들은 5번(`docs/command_guide_for_ai.md`)에도 **의도적으로 등록하지 않는다** — AI 자연어 변환이 이 토큰을 스스로 만들어 실거래 주문을 잘못 실행하는 것을 막기 위함. 사람이 읽는 요약은 `docs/개발환경/command_summary.md` 9절에 있다.

### 코드 생성 규칙

- `src/api/` 디렉토리에서 `client.py`, `auth.py`, `__init__.py`를 **제외한 모든 파일**(`price_info.py`, `order.py`, `account.py` 등 카테고리별 모듈, `registry.py`)은 `manage/generate/generate_api_client.py`가 `docs/api/md/*.md`를 파싱해 생성한다.
- `docs/api/md`에 API 명세가 추가/변경되면 `uv run python -m manage.generate.generate_api_client`를 재실행해 갱신한다. 생성된 파일을 직접 손으로 고치지 않는다(재실행 시 덮어써짐).
- 새 API를 카테고리 모듈에 배정하려면 `manage/generate/generate_api_client.py`의 `CODE_TO_MODULE` 딕셔너리를 수정한다.
- **INPUT 표의 필수여부(Y/N) 컬럼은 신뢰할 수 없어 코드 전반에서 무시한다** — KB 명세가 조회 API의 핵심 파라미터(종목코드 등)도 N으로 표기하는 등 실제와 어긋난다. 그래서 ① 생성기는 모든 필드를 기본값 있는 선택 인자로 만들고 `required=[]`로 고정하며, ② 런타임 파서(`src/utils/api_spec.py`)도 선택지는 필수여부와 무관하게 파싱하고 요청 전 "필수 파라미터 누락" 검증을 하지 않는다(`required=[]`). 실제 필수 여부는 KB 서버 응답으로 판단한다. `docs/api/md`에 새 명세를 넣을 때 필수여부가 틀려도 무방하다(어차피 무시됨).
- **`docs/api/xlsx/`에 새 명세를 추가할 때는 TR 성격에 맞는 업무구분 폴더에 넣을 것** — 이 폴더 구조가 그대로 웹 "API 명세"(`/api.html`) 화면의 트리 분류로 표시된다(`src/web/spec_browser.py`가 `docs/api/md` 폴더 구조를 그대로 읽는다).
