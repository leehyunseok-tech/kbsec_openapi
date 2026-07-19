# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# kbsec_api

KB증권 OpenAPI(REST) 기반 자동매매 시스템 — 텔레그램/터미널/웹 트리플 클라이언트.

## 개발 환경

- Python 프로젝트 의존성/가상환경은 `uv`로 관리한다 (`pyproject.toml`, `.venv`).
- 패키지 설치: `uv add <패키지명>`, 스크립트 실행: `uv run <파일>` 또는 `uv run python ...`.
- 최초 셋업: `config/config.example.py`를 `config/config.py`로 복사해 실제 키를 채운다 (`config.py`는 gitignore 대상 — 실제 앱키/텔레그램 토큰/Claude 키가 들어 있으므로 **어떤 응답/로그/커밋에도 원문을 노출하지 않는다**. 프로젝트는 GitHub 공개 예정).

## 자주 쓰는 명령어

```bash
# 클라이언트 실행 (모듈 실행 필수 — 아래 "소스 레이아웃" 참고)
uv run python -m src.run.terminal          # 터미널 클라이언트 (개발/테스트 시 기본)
uv run python -m src.run.main              # 텔레그램 봇
uv run python -m src.run.web               # 웹 (http://localhost:8000)
uv run python -m src.run.web token         # 웹 + config.py 키로 자동 로그인 (로컬 전용)

# 코드/데이터 재생성 (산출물 직접 수정 금지)
uv run python docs/api/generate_api_list.py    # docs/api/md → api-list.md/json
uv run python docs/api/generate_api_client.py  # docs/api/md → src/api/*.py + registry.py
uv run python -m src.manage.generate_mst       # mst/origin → 종목마스터 문서+런타임 데이터
```

- 자동화된 테스트 스위트/린터는 없다. 변경 검증은 `uv run python -m compileall -q src`(문법), `node --check src/web/static/js/*.js`(웹 JS), 그리고 터미널 클라이언트나 일회성 스크립트로 해당 기능을 직접 호출해 확인하는 방식이다. 실제 API 호출 검증은 운영환경(실거래) 계정이라 주문 계열은 특히 주의.

## 프롬프트 히스토리 기록 규칙

- 이 프로젝트에서 사용자와 나눈 질문/답변은 `docs/prompt/prompt-history.md`에 순서대로 기록한다.
- 새 대화가 시작되어도 이 규칙을 계속 적용하여 해당 파일에 이어서 기록한다.
- 형식: `## YYYY-MM-DD` 날짜 헤더 아래 `### Q: ...` / `### A: ...` 쌍으로 기록한다.

## 개발환경 문서 갱신 규칙

- 개발환경(패키지 관리자, 의존성, 실행/빌드 방법 등)과 관련된 변경사항이 생길 때마다 `docs/prompt/개발환경.md`에 내용을 계속 추가/갱신한다.
- 새 대화가 시작되어도 이 규칙을 계속 적용한다.

## 프로젝트 구조

KB증권 REST API를 활용한 텔레그램/터미널/웹 기반 자동매매 시스템. 전체 기능 목록은 `docs/features.md` 참고.

**중요한 특성**: KB API 74개는 전부 REST(POST)이며 실시간 웹소켓이 없다. 실시간 시세가 필요한
기능(트레일링 스탑, 자동 손절매 등)은 REST 폴링으로 구현했고, 조건검색식 실시간거래(jggs/cond)·VI감시·
테마분석·공매도분석은 KB에 대응 API가 없어 지원하지 않는다 (`docs/features.md` 8절 참고).

**개발환경(모의투자) 미제공**: KB증권은 아직 개발환경(`ddeveloper.kbsec.com`, 모의투자)을 제공하지 않으며
운영환경(`developer.kbsec.com`, 실거래)만 사용 가능하다. `src/run/main.py`/`src/run/terminal.py`의 로그인은
`real`만 안내하고 자동 로그인 기본값도 `real`이다. `dev_client_key`/`dev_client_secret`과 `login dev` 코드
경로는 KB가 추후 개발환경을 열 경우를 대비해 남겨뒀지만 현재는 정상 동작하지 않으므로, 문서·안내 메시지·
`docs/command_guide.md`(AI 참조 문서)에 새로 추가할 때도 `dev`를 정상 옵션처럼 노출하지 않는다.

**소스 레이아웃(`src/`)**: 실행 코드는 `src/` 하단에 있고, `config/`·`docs/`는 프로젝트 루트에 그대로 둔다.
`main.py`/`terminal.py`는 `src/run/`으로 옮기면서 `uv run python -m src.run.main`처럼 모듈 실행(`-m`)
방식으로 구동한다 — 프로젝트 루트가 `sys.path`에 올라와야 `from src.utils...`/`from src.api...`/
`from src.messenger...`/`from src.commands...` 형태의 절대 임포트가 동작하기 때문. `run-main.*`/`run-terminal.*` 스크립트가
이 호출 방식을 그대로 감싸고 있으니 직접 `python src/run/main.py`처럼 실행하지 말 것.

- `config/` — `config.py`(gitignore 대상, 실제 키), `config.example.py`(템플릿). 운영/개발 호스트 URL, client_key/client_secret, 텔레그램/Claude API 키, 토큰 발급용 device_info.
- `src/api/client.py`, `src/api/auth.py` — **수기 작성**, 공용 요청 봉투(dataHeader/dataBody) 구성 및 토큰 발급 로직.
- `src/api/*.py`(그 외 10개 모듈), `src/api/registry.py` — **자동 생성 파일, 수동 수정 금지**. `docs/api/generate_api_client.py` 재실행으로만 갱신.
- `src/utils/` — API 클라이언트 유틸(`api_logger.py`, `http_client.py`, `session.py`, `device_info.py`) + 브로커 무관 유틸(`settings_manager.py`, `schedule_manager.py`, `trade_logger.py`, `trade_analyzer.py`, `cooldown_log.py`, `command_executor.py`, `ai_command_converter.py`, `stock_resolver.py`, `api_resolver.py`) + API 직접호출(`api_spec.py` — `docs/api/md` 명세를 런타임 파싱해 `/api`·`/call`이 registry 없이 임의 API를 실행) + 터미널 대화형 입력(`terminal_ui.py` — Enter 확인/화살표+숫자 선택 메뉴, cross-platform raw 키 입력) + 자동매매 폴링 모니터(`monitor_base.py`와 이를 상속하는 `*_monitor.py`, `stoploss_manager.py`) + 조회 헬퍼(`stock_master.py`, `price_lookup.py`, `chart_analysis.py`, `holdings_valuation.py`, `formatting.py`).
- `mst/` (프로젝트 루트) — 종목마스터 `.mst` 파일(원본 `origin/` + 가공본 `api/`). `src/utils/stock_master.py`가 실제로 로드/검색하는 런타임 데이터는 `mst/api/openapi_field_kospi-kosdaq.mst`(코스피+코스닥 통합)/`mst/api/openapi_field_foren-us.mst`(해외) 두 파일이며, AI 자연어 변환이 생성한 종목명을 실제 코드로 바꾸는 결정적(deterministic) 근거로도 쓰인다(`src/utils/stock_resolver.py`). 이 두 파일은 코드값(예: `ST`, `Y/N`)을 사람이 읽기 좋은 텍스트(`주식`, `거래정지`)로 이미 바꿔둔 상태라 `/stcd` 등에서 그대로 표시해도 된다 — 단 해외 거래소코드(`NAS`/`NYS`/`AMX`)만은 예외로 원본을 유지한다(`buy_command.py`/`sell_command.py`/`srch_command.py`가 KB 주문/시세 API의 `krx_cd` 파라미터로 그대로 전달하기 때문; 표시용 한글명은 `OverseasStock.exchange_name`에 별도로 있음). **생성은 `src/manage/generate_mst.py` 파이프라인이 전담**: `mst/origin/`에 KB 배포 원본만 갈아 놓고 `uv run python -m src.manage.generate_mst`를 실행하면 필드 선별 문서(`docs/mst/xlsx/openapi_mst_*.xlsx` + `docs/mst/md/openapi_mst_*.md`)와 런타임 데이터(`mst/api/openapi_field_*.mst`)가 중간 파일 없이 전부 재생성된다. 필드 인덱스/코드표의 근거는 KB 공식 명세(`docs/mst/xlsx/mst_*.xlsx`)이며, 어떤 필드를 쓸지는 스크립트 안 `CURATION` 표가 단일 소스다. 산출 문서·데이터를 손으로 고치지 말 것(재실행 시 덮어써짐). (과거의 `mst/create_openapi_mst.py`+`generate_field_reference_mst.py` 2단계 구조는 타 증권사 레이아웃을 가정한 필드 라벨 오류 — 예: 소수점매매상태를 '주문유형'으로, 현금증거금율구분을 '매매수량단위코드'로 해석 — 가 있어 폐지·교정됨.)
- `src/manage/` — 런타임 코드가 아닌 관리(생성/갱신) 스크립트 모음. `generate_mst.py`: 종목마스터 파이프라인(위 `mst/` 항목 참고), `uv run python -m src.manage.generate_mst`로 실행.
- `src/messenger/telegram/` — `tel_receive.py`/`tel_send.py`(텔레그램 Bot API 전송계층). 추후 다른 메신저(디스코드/슬랙 등)를 추가하면 `src/messenger/<백엔드>/`로 나란히 추가할 예정.
- `src/commands/` — 명령 핸들러(`{name}_command.py`, 함수 1개 = 명령 1개). 메신저 종류와 무관한 공용 로직이라 `messenger/`가 아닌 `src/` 바로 아래 둠 — `main.py`/`terminal.py`/`web`이 동일하게 호출한다.
- `src/web/` — 웹 인터페이스 구현 전체. `app.py`(FastAPI — 정적 파일 서빙 + `/api/*` 순수 JSON 라우트, Jinja2 등 서버 템플릿 없음), `client.py`(`WebClient` — 브라우저 세션 1개당 인스턴스 1개, **다중 사용자**라 config.py 앱키로 자동 로그인하지 않고 설정 화면에서 사용자별 client_key/client_secret을 받아 메모리에만 보관), `session_store.py`(쿠키 `kbsec_web_sid` ↔ WebClient 인메모리 매핑), `static/`(순수 HTML+CSS+JS 프론트엔드 — 외부 라이브러리/CDN 없음). **주의**: 설정값·자동매매 감시목록(`config/data/settings.json`)은 서버 공용이라 웹 사용자 간 공유된다(문서화된 제약).
- `src/run/main.py` — `TelegramBot`: 텔레그램 폴링 기반 운영 클라이언트.
- `src/run/terminal.py` — `TerminalClient`: `main.py`와 동일한 명령 핸들러를 공유하는 터미널 클라이언트(텔레그램 불필요) + API 코드 기반 저수준 직접 호출(`call`/`info`/`list`).
- `src/run/web.py` — 웹 클라이언트 실행 진입점(uvicorn 구동만 담당, 구현은 전부 `src/web/`). `run-web.bat`/`run-web.sh`, 기본 http://localhost:8000, `KBSEC_WEB_HOST`/`KBSEC_WEB_PORT` 환경변수로 변경.
- `src/run/command_pipeline.py` — `CommandPipelineMixin`: 세 클라이언트(main/terminal/web)가 공유하는 AI 변환 이후 처리(종목명/API명 로컬 해석 → 선택/확인 세션 → 일괄 실행)와 모니터 콜백의 **단일 소스**. 파이프라인 로직을 고칠 때는 개별 클라이언트가 아니라 이 파일을 고친다 (양쪽에 복사돼 있던 시절 드리프트 버그가 실제로 발생했음).
- `docs/command_guide.md` — AI 자연어 변환이 **런타임에 참조**하는 명령어 규칙 문서 (아래 필수 규칙 참고).
- `docs/features.md` — 전체 기능 목록과 담당 파일/매핑 API.
- `docs/api/` — API 명세 파이프라인. 자세한 내용은 `docs/api/README.md` 참고.

### ⚠️ 필수 규칙 — 명령어 추가/변경 시 반드시 지켜야 할 것

명령어를 추가/변경/삭제할 때마다 **아래를 항상 동시에 완료**해야 합니다. 하나라도 빠지면 코드·도움말·AI 가이드가 불일치해 오작동합니다.

1. `src/commands/{name}_command.py`에 `handle_{name}(args, session, ...)` 구현
2. `src/run/main.py`의 `self.commands` 딕셔너리와 `HELP_TEXT`에 등록
3. `src/run/terminal.py`의 `TerminalClient.commands` 딕셔너리에도 동일하게 등록
4. `src/web/client.py`의 `WebClient.commands` 딕셔너리에도 동일하게 등록 (트리플 클라이언트 아키텍처 — `main.py`/`terminal.py`/`web/client.py`는 같은 핸들러를 공유해야 함)
5. **`docs/command_guide.md`에 해당 명령어 섹션 추가/수정** — 이 문서는 `src/utils/ai_command_converter.py`가 Claude API 시스템 프롬프트에 그대로 삽입하는 실제 런타임 참조 문서다. 갱신하지 않으면 AI가 자연어를 잘못된 명령어로 변환한다.
6. `docs/features.md`의 해당 기능 상태도 필요시 갱신

### 코드 생성 규칙

- `src/api/` 디렉토리에서 `client.py`, `auth.py`, `__init__.py`를 **제외한 모든 파일**(`price_info.py`, `order.py`, `account.py` 등 카테고리별 모듈, `registry.py`)은 `docs/api/generate_api_client.py`가 `docs/api/md/*.md`를 파싱해 생성한다.
- `docs/api/md`에 API 명세가 추가/변경되면 `uv run python docs/api/generate_api_client.py`를 재실행해 갱신한다. 생성된 파일을 직접 손으로 고치지 않는다(재실행 시 덮어써짐).
- 새 API를 카테고리 모듈에 배정하려면 `docs/api/generate_api_client.py`의 `CODE_TO_MODULE` 딕셔너리를 수정한다.
