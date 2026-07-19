# kbsec_api

## 개발 환경

- Python 프로젝트 의존성/가상환경은 `uv`로 관리한다 (`pyproject.toml`, `.venv`).
- 패키지 설치: `uv add <패키지명>`, 스크립트 실행: `uv run <파일>` 또는 `uv run python ...`.

## 프롬프트 히스토리 기록 규칙

- 이 프로젝트에서 사용자와 나눈 질문/답변은 `docs/prompt/prompt-history.md`에 순서대로 기록한다.
- 새 대화가 시작되어도 이 규칙을 계속 적용하여 해당 파일에 이어서 기록한다.
- 형식: `## YYYY-MM-DD` 날짜 헤더 아래 `### Q: ...` / `### A: ...` 쌍으로 기록한다.

## 개발환경 문서 갱신 규칙

- 개발환경(패키지 관리자, 의존성, 실행/빌드 방법 등)과 관련된 변경사항이 생길 때마다 `docs/prompt/개발환경.md`에 내용을 계속 추가/갱신한다.
- 새 대화가 시작되어도 이 규칙을 계속 적용한다.

## 프로젝트 구조

KB증권 REST API를 활용한 텔레그램 기반 자동매매 시스템. 전체 기능 목록은 `docs/features.md` 참고.

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
- `src/mst/` — 종목마스터 원본(코스피/코스닥/해외) `.mst` 파일. `src/utils/stock_master.py`가 이 파일들을 로드/검색하며, AI 자연어 변환이 생성한 종목명을 실제 코드로 바꾸는 결정적(deterministic) 근거로도 쓰인다(`src/utils/stock_resolver.py`). 파이프라인 산출 원본은 `docs/mst/mst/for-api/`에 그대로 있음.
- `src/messenger/telegram/` — `tel_receive.py`/`tel_send.py`(텔레그램 Bot API 전송계층). 추후 다른 메신저(디스코드/슬랙 등)를 추가하면 `src/messenger/<백엔드>/`로 나란히 추가할 예정.
- `src/commands/` — 명령 핸들러(`{name}_command.py`, 함수 1개 = 명령 1개). 메신저 종류와 무관한 공용 로직이라 `messenger/`가 아닌 `src/` 바로 아래 둠 — `main.py`/`terminal.py`가 동일하게 호출한다.
- `src/run/main.py` — `TelegramBot`: 텔레그램 폴링 기반 운영 클라이언트.
- `src/run/terminal.py` — `TerminalClient`: `main.py`와 동일한 명령 핸들러를 공유하는 터미널 클라이언트(텔레그램 불필요) + API 코드 기반 저수준 직접 호출(`call`/`info`/`list`).
- `src/run/command_pipeline.py` — `CommandPipelineMixin`: 두 클라이언트가 공유하는 AI 변환 이후 처리(종목명/API명 로컬 해석 → 선택/확인 세션 → 일괄 실행)와 모니터 콜백의 **단일 소스**. 파이프라인 로직을 고칠 때는 main/terminal이 아니라 이 파일을 고친다 (양쪽에 복사돼 있던 시절 드리프트 버그가 실제로 발생했음).
- `docs/command_guide.md` — AI 자연어 변환이 **런타임에 참조**하는 명령어 규칙 문서 (아래 필수 규칙 참고).
- `docs/features.md` — 전체 기능 목록과 담당 파일/매핑 API.
- `docs/api/` — API 명세 파이프라인. 자세한 내용은 `docs/api/README.md` 참고.

### ⚠️ 필수 규칙 — 명령어 추가/변경 시 반드시 지켜야 할 것

명령어를 추가/변경/삭제할 때마다 **아래를 항상 동시에 완료**해야 합니다. 하나라도 빠지면 코드·도움말·AI 가이드가 불일치해 오작동합니다.

1. `src/commands/{name}_command.py`에 `handle_{name}(args, session, ...)` 구현
2. `src/run/main.py`의 `self.commands` 딕셔너리와 `HELP_TEXT`에 등록
3. `src/run/terminal.py`의 `TerminalClient.commands` 딕셔너리에도 동일하게 등록 (듀얼 클라이언트 아키텍처 — `main.py`/`terminal.py`는 같은 핸들러를 공유해야 함)
4. **`docs/command_guide.md`에 해당 명령어 섹션 추가/수정** — 이 문서는 `src/utils/ai_command_converter.py`가 Claude API 시스템 프롬프트에 그대로 삽입하는 실제 런타임 참조 문서다. 갱신하지 않으면 AI가 자연어를 잘못된 명령어로 변환한다.
5. `docs/features.md`의 해당 기능 상태도 필요시 갱신

### 코드 생성 규칙

- `src/api/` 디렉토리에서 `client.py`, `auth.py`, `__init__.py`를 **제외한 모든 파일**(`price_info.py`, `order.py`, `account.py` 등 카테고리별 모듈, `registry.py`)은 `docs/api/generate_api_client.py`가 `docs/api/md/*.md`를 파싱해 생성한다.
- `docs/api/md`에 API 명세가 추가/변경되면 `uv run python docs/api/generate_api_client.py`를 재실행해 갱신한다. 생성된 파일을 직접 손으로 고치지 않는다(재실행 시 덮어써짐).
- 새 API를 카테고리 모듈에 배정하려면 `docs/api/generate_api_client.py`의 `CODE_TO_MODULE` 딕셔너리를 수정한다.
