# 기능 현황

KB증권 OpenAPI를 활용한 텔레그램/터미널/웹 기반 자동매매 봇의 전체 기능 목록과 담당 파일,
매핑 API를 정리한 문서입니다.

**범례**: ✅ 지원 · 🔁 REST 폴링 기반 · ⚠️ 제약 있음 · ❌ 미지원(KB API 없음)

---

## 1. 인증 / 상태

| 기능 | 상태 | 담당 파일 | 비고 |
|---|---|---|---|
| 로그인 (토큰 발급) | ⚠️ | `src/api/auth.py`, `src/commands/login_command.py` | **KB증권 개발환경(모의투자)이 아직 제공되지 않아 `real`(운영환경)만 실제로 동작**. `dev` 코드 경로는 남아있지만 문서/안내에는 노출하지 않음 |
| 로그인 상태 조회 | ✅ | `src/commands/login_command.py` (`handle_status`) | |
| 토큰 자동 갱신 스케줄 | ❌ | — | 수동 재로그인만 지원 (자동 갱신 미구현) |

## 2. 조회

| 기능 | 상태 | 담당 파일 | 매핑 API |
|---|---|---|---|
| 종목 현재가/기본정보 (`srch`) | ✅ | `src/commands/srch_command.py` | `IVU10140`(국내) |
| 해외(미국) 현재가/기본정보 (`srch`) | ✅ | `src/commands/srch_command.py` | `GSS10030` — 종목코드 자리에 티커(예: `IONQ`) 입력. 시세는 15분 지연일 수 있음(`mrkt_prc_clsf` 필드) |
| 상위 종목 랭킹 (`rank`) | ✅ | `src/commands/rank_command.py` | `IVU10210`(거래대금) `IVU10240`(등락률) `IVU10280`(거래량) `IVM30010`(업종랭킹) |
| 계좌 현황 (`report`/`r`) | ✅ | `src/commands/report_command.py` | `SSQM1801`(보유) `SSQM2341`(체결/미체결) |
| 종목마스터 (`mst`) | ✅ | `src/commands/mst_command.py`, `src/utils/stock_master.py` | API 호출 없이 `mst/api/*.mst` 로컬 파일 사용 |
| 종목명 검색 (`stcd`) | ✅ | `src/commands/stcd_command.py`, `src/utils/stock_master.py` | 국내+해외 통합 검색, 로컬 파일 기반 |
| 투자자별 순매수 차트 (`investor`) | ✅ (국내만) | `src/commands/investor_command.py` | `IVU10430` — KB가 `acml_clsf`(누적)를 직접 지원해 수동 누적합 계산 불필요. **해외는 KB API 74개 전체에 대응 API가 없어 지원 불가**(거래원/투자자/프로그램 카테고리 3개 API 모두 국내 전용 `excg_clsf` 파라미터만 사용, 해외 버전 없음) |
| 랭킹 결과 일괄 명령 실행 (`rank N cmd`) | ✅ | `src/commands/rank_command.py` | |

### 2.1 API 직접호출

`docs/api/md/*.md`에 문서화된 API라면 코드만 알면 곧바로 실행할 수 있는 범용 명령.
`docs/api/generate_api_client.py`가 생성하는 `src/api/registry.py`(`CODE_TO_MODULE`을
수동으로 갱신해야 새 API가 반영됨)에 의존하지 않고, `docs/api/api-list.json` +
`docs/api/md/*.md`를 그때그때 직접 읽어 실행하므로 명세 문서만 최신이면 코드
재생성 없이 바로 쓸 수 있다. 조회 API뿐 아니라 주문 API(`SSAM1802` 매수주문 등)도
실행 가능하니 실거래 계좌에서 사용 시 주의할 것.

| 기능 | 상태 | 담당 파일 | 비고 |
|---|---|---|---|
| API 직접 실행 (`/api {코드}`) | ✅ | `src/commands/api_command.py`, `src/utils/api_spec.py` | INPUT 표에서 필수(Y)+설명에 "코드:라벨" 선택지가 있는 필드는 번호로 선택(대화형), 그 외(선택지 없거나 필수 아님)는 타입(길이)만큼 공백으로 자동 채움 |
| 파라미터 미리보기 (`/api info {코드}`) | ✅ | 〃 | 실행하지 않고 어떤 필드가 선택 대상이고 어떤 필드가 공백 채움인지 보여줌 |
| API 검색 (`/api list [키워드]`) | ✅ | 〃 | 코드/API명/업무구분(`docs/api/api-list.json`의 `category`)으로 검색 |
| 자연어로 API 직접호출 (`"보유주식조회 해줘"` 등) | ✅ (조회 전용) | `src/utils/api_resolver.py`, `src/utils/ai_command_converter.py` | `docs/api/md` 파일명의 한글 API명을 그대로 말하면 `api {코드}`로 변환. AI는 `docs/api/api-list.json` 기반 전체 API명 목록을 시스템 프롬프트로 받아 인식하고, 실제 코드 매칭은 `stock_resolver.py`와 동일하게 로컬에서 결정적으로 처리(이름이 겹치면 번호 선택 세션). **주문/취소/정정 계열 API는 이 경로로 자동 실행되지 않음** — 선택이 필요한 필수 파라미터가 있으면 "AI 확인 후 일괄 실행" 흐름 안에서는 세션을 새로 열 수 없어 안내 메시지만 반환하고(대화형 세션은 사용자가 `/api {코드}`를 직접 입력했을 때만 생성됨), 실제 주문 API 11개(매수/매도/정정/취소/소수점주문 전체)는 전수 확인 결과 예외 없이 선택 필드를 최소 1개 이상 갖고 있어 이 경로로 절대 자동 실행되지 않음이 확인됨 |

## 3. 매매

| 기능 | 상태 | 담당 파일 | 매핑 API |
|---|---|---|---|
| 매수 (시장가/지정가/금액기반 max) | ✅ | `src/commands/buy_command.py` | `SSAM1802`(국내) |
| 매도 (전량/수량지정/`sell all`) | ✅ | `src/commands/sell_command.py` | `SSAM1801`(국내), `SSQM1801`(보유조회) |
| 해외(미국) 매수/매도 (시장가·지정가·금액기반) | ✅ | `src/commands/buy_command.py`/`sell_command.py` | `SKAM2101`, 현재가는 `GSS10030` — 종목코드 자리에 티커(예: `IONQ`) 입력. 해외 시장가는 KB 명세에 가격 필드 처리 방식이 안 나와 있어 현재가 조회 후 지정가로 제출해 흉내냄. 블랙리스트/쿨다운 가드는 국내·해외 모두 적용(`settings_manager.py`가 티커도 저장 가능) |
| 해외(미국) 전량 매도 / `sell all` | ❌ (KB API 미제공) | — | KB API 74개 전체에 **종목별 해외 보유수량 조회 API가 없음**(계좌 통화별 예수금 조회인 `SPQM2226`뿐, 종목 단위 보유수량 아님) — 그래서 해외 매도는 수량을 반드시 명시해야 하고 전량 매도는 구현 불가. 국내는 `SSQM1801`로 정상 지원 |
| 미체결 주문 취소 (`ccl pend`) | ✅ | `src/commands/ccl_command.py` | `SSAM1806`, `SSQM2341` |
| tick 조정 지정가 매수 (`buy ... tick N`) | ❌ | — | 호가단위 기반 가격 보정 로직 미구현 (개선 예정) |
| 자동매매 중복매수 방지 가드 (`--auto`) | ❌ | — | 별도 중복매수/최대보유 옵션 미구현 — 블랙리스트/쿨다운 가드는 지원됨 |
| 주문 타임아웃 자동 재주문/취소 감시 스레드 | ❌ | — | `time` 명령으로 설정값 저장은 되지만, 실제로 타임아웃을 감시해 자동 취소/재주문하는 백그라운드 스레드는 미구현 |

## 4. 설정 (브로커 무관 공용 로직)

| 기능 | 상태 | 담당 파일 |
|---|---|---|
| 장 시간 (`mkhr`) | ✅ | `src/commands/mkhr_command.py` |
| 익절/손절 기준 (`익절`/`손절`) | ✅ | `src/commands/profit_command.py`, `loss_command.py` |
| 주문 타임아웃 설정값 (`time`) | ✅ (설정값만) | `src/commands/time_command.py` |
| 재매수 쿨다운 (`cooldown`) | ✅ | `src/commands/cooldown_command.py`, `src/utils/cooldown_log.py` |
| 블랙리스트 (`blacklist`) | ✅ | `src/commands/blacklist_command.py`, `src/utils/settings_manager.py` (국내 6자리 코드 + 해외 티커 등록 가능) |
| 최대 보유 종목 수 (`mxhold`) | ✅ | `src/commands/mxhold_command.py` |
| 전체 설정값 조회 (`stts`) | ✅ | `src/commands/stts_command.py` |

## 5. 예약 / 기록 (브로커 무관 공용 로직)

| 기능 | 상태 | 담당 파일 |
|---|---|---|
| 명령 예약 (`rsv`) | ✅ | `src/commands/rsv_command.py`, `src/utils/schedule_manager.py` |
| 체결 내역 CSV (`log`) | ✅ | `src/commands/log_command.py`, `src/utils/trade_logger.py` |
| 체결 내역 AI 분석 (`anss`) | ✅ | `src/commands/anss_command.py`, `src/utils/trade_analyzer.py` |
| 일일 거래 요약 자동 전송 (매일 15:31) | ✅ | `src/run/main.py` (`_daily_report_job`) |

## 6. AI 자연어 명령 변환

| 기능 | 상태 | 담당 파일 | 비고 |
|---|---|---|---|
| `/` 유무로 커맨드·자연어 구분 | ✅ | `src/run/main.py`/`src/run/terminal.py`의 `process_command`/`_dispatch_direct` | `/`로 시작하면 AI를 거치지 않고 곧바로 실행(예: `/buy 005930 10`), `/` 없으면 단어가 실제 명령어와 같아도 무조건 자연어로 취급해 Claude로 보낸다(예: `buy 005930 10`도 자연어). rsv 예약 재실행처럼 이미 해석된 문자열을 신뢰하고 즉시 실행해야 하는 내부 호출은 `_dispatch_direct()`로 이 판단 자체를 우회한다 |
| 자연어 → 명령어 변환 (Claude API) | ✅ | `src/utils/ai_command_converter.py` | `docs/command_guide.md`를 시스템 프롬프트에 삽입, ephemeral 프롬프트 캐싱 |
| 종목명 → 종목코드 로컬 해석 | ✅ | `src/utils/stock_resolver.py` | `buy`/`sell`/`srch`/`investor`는 Claude가 종목코드를 직접 추측하지 않고 종목명을 그대로 넘기면, `mst/api/` 로컬 검색으로 결정적으로 코드를 확정한다(코드 오추측 방지). `buy`/`sell`/`srch`는 국내 검색이 비면 해외(미국) 티커로 한 번 더 검색한다(`investor`는 해외 API 자체가 없어 국내 전용 유지). 검색 결과가 2건 이상이면 번호 선택 세션(`StockSelectionPending`)으로 사용자에게 후보를 보여주고 선택받는다. `rsv`에 중첩된 명령은 예외(기존처럼 Claude가 직접 코드로 변환) |
| 실행 전 확인/선택 UI | ✅ | `src/utils/command_executor.py`, `src/run/command_pipeline.py`, `src/utils/terminal_ui.py`, `src/web/static/js/app.js` | 확인은 **터미널에서 Enter(그 외 키는 취소)**, **텔레그램에서 ✅/❌ 인라인 버튼 탭**, **웹에서 화면 버튼 클릭**으로 한다. 후보가 여럿인 선택(종목명/API명/`/api` 필드값)은 터미널은 화살표 `↑↓`+Enter 또는 번호 직접 입력, 텔레그램은 후보별 인라인 버튼 탭, 웹은 후보별 버튼 클릭으로 고른다. 세션 해석 로직 자체는 세 클라이언트가 공유하는 텍스트("y"/"n"/1-based 번호) 기반이라 변하지 않고, 그 텍스트를 어떻게 입력받는지만 클라이언트별로 다르다 |
| `command_guide.md` 런타임 참조 문서 | ✅ | `docs/command_guide.md` | **명령어 변경 시 반드시 같이 갱신** (CLAUDE.md 필수 규칙) |

## 7. 자동매매 전략 (폴링 기반, 09:00~15:30)

KB증권 API에는 실시간 웹소켓이 없어, 실시간 시세가 필요한 전략(트레일링 스탑, 자동 손절 등)도
모두 REST 폴링(`src/utils/monitor_base.py` 기반)으로 구현했다.

| 기능 | 상태 | 담당 파일 | 비고 |
|---|---|---|---|
| 골든크로스 자동매수 (`gdcrs`) | 🔁 | `src/utils/golden_cross_monitor.py`, `src/commands/gdcrs_command.py` | `IVS11560`(분봉) 20초 폴링 기반 이동평균 교차 감지 (`src/utils/chart_analysis.py`) |
| 데드크로스 자동매도 (`ddcrs`) | 🔁 | `src/utils/dead_cross_monitor.py` | 보유종목을 `SSQM1801`로 직접 조회 |
| 트레일링 스탑 (`trst`) | 🔁 ⚠️ | `src/utils/trailing_stop_monitor.py`, `src/commands/trst_command.py` | 15초 REST 폴링. 평가손익은 `SSQM2952`의 `val_yld`를 그대로 사용(KB가 직접 제공) |
| 자동 손절/익절 (`stls`) | 🔁 ⚠️ | `src/utils/stoploss_manager.py` | `SSQM2952` 기반 폴링. MonitorBase 기반 단일 폴링 클래스 |
| 돌파매수 감시 (`brk`) | ✅ | `src/utils/brk_monitor.py`, `src/commands/brk_command.py` | `IVU10140`의 `up_dwn_r_p2`(등락율)를 직접 사용 |
| 분할매매 (`wave`) | ✅ | `src/utils/wave_monitor.py`, `src/commands/wave_command.py` | |
| 그리드 트레이딩 (`grid`) | ✅ | `src/utils/grid_monitor.py`, `src/commands/grid_command.py` | |
| 보유종목 변경 감지 (`hold`) | ✅ | `src/utils/holdings_monitor.py` | `SSQM1801`(보유) + `SSQM2341`(체결내역 매칭 후 CSV 기록) |
| `start`/`stop` 통합 디스패치 | ✅ | `src/run/main.py`/`src/run/terminal.py`의 `_dispatch_monitor` | |

### 폴링 모니터 공용 인프라

brk/wave/grid/holdings 등 각 모니터가 공통으로 쓰는 threading 폴링 루프·시작/중단·장중판별
로직을 `src/utils/monitor_base.py`(`MonitorBase`)에 모아, 각 모니터가 `_check_all()`만
구현하면 되도록 정리했다.

## 8. 미지원 기능 (KB API 없음)

아래 기능들은 `docs/api/api-list.json` 74건 전수 검색 결과 KB증권 OpenAPI에 대응 API가 없어
지원하지 않습니다.

| 기능 | 사유 |
|---|---|
| 조건검색식 실시간거래 | 서버 저장 조건식 + 실시간 푸시 방식이 필요한데, KB에는 조건검색 API 자체가 없음 |
| VI(변동성완화장치) 감시 | 시장 전체 VI 발동종목 조회 API 없음 |
| 테마 분석 | 테마그룹/구성종목 조회 API 없음 |
| 공매도 분석/감시, 대차거래 상위 | 공매도추이/대차상위 조회 API 없음 |

## 9. 아키텍처 참고

| 항목 | 구현 방식 |
|---|---|
| 실시간 데이터 | KB증권 API에 웹소켓이 없어 전부 REST 폴링으로 처리 |
| 모의투자(개발환경) | **아직 미제공** — `real`(운영환경)만 사용 가능, 실거래 주의 |
| 평균매입가/평가손익 조회 | `SSQM2952`(잔고현황 조회, 체결기준) — `val_yld` 필드로 수익률 직접 제공 |
| 종목마스터 | 로컬 파일(`mst/api/openapi_field_*.mst`) — API 호출 불필요 |
| src/api/ 모듈 생성 방식 | `docs/api/generate_api_client.py`가 명세(md)에서 자동 생성 |
| 자동매매 모니터 구조 | `src/utils/monitor_base.py` 공용 베이스 상속 |
| 트리플 클라이언트 공용 파이프라인 | `src/run/command_pipeline.py`(`CommandPipelineMixin`) — main.py(텔레그램)/terminal.py(터미널)/web(브라우저) 공유 |
| 웹 인터페이스 | `src/web/`(FastAPI JSON API + 순수 HTML/CSS/JS, 서버 템플릿 없음), 실행은 `src/run/web.py`(`run-web.*`) — 브라우저 쿠키당 `WebClient` 1개(다중 사용자, 각자 앱키로 로그인), 시크릿은 서버 메모리에만 보관. 단 설정값/자동매매 감시목록(`config/data/settings.json`)은 서버 공용 |
| 웹 API 명세 탐색/테스트 | `src/web/spec_browser.py` + `src/web/static/api.html` — `docs/api/md` 폴더 구조 그대로 트리 탐색, 명세 md 열람, INPUT 폼(기본값: 선택지 첫 코드/필수는 공백 채움/그 외 빈 문자열) 편집 후 실제 KB API 테스트 호출(JSON 응답 원문 표시). 주문 계열(SSAM/SKAM)은 경고+확인 대화상자 |

---

## 참고: 전체 명령어 목록

`login, status, help, power, srch, rank, buy, sell, ccl, report/r, mst, stcd, api, mkhr, stts,
time, cooldown, blacklist, mxhold, 익절, 손절, rsv, log, anss, investor, gdcrs, ddcrs, trst,
brk, wave, grid, start, stop`
