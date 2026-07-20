> **투자 책임 고지:** 이 스킬을 활용해 투자 분석, 자동/자율 주문, 매수/매도 실행을 하는 모든 판단과 결과의 책임은 전적으로 사용자 본인에게 있습니다. **KB증권 Open API는 개발환경(모의투자)을 제공하지 않으며, 이 스킬의 모든 호출은 실거래 계좌를 대상으로 합니다.** 이 프로젝트와 에이전트는 수익을 보장하지 않으며, 손실 가능성을 없애지 않습니다.

# KB증권 Open API Agent Skill

Codex, Claude Code 같은 에이전트에서 KB증권 Open API를 바로 탐색하고 호출할 수 있도록 만든
Agent Skill입니다. 74개 REST API의 필드 명세, 표준 라이브러리 기반 CLI, 주문 dry-run, 그리고
사용자가 자연어로 위임한 자율 매수/매도 실행 흐름을 함께 묶었습니다.

표준 Agent Skill 구조(`SKILL.md` + `references/` + `scripts/`)로 만들어,
[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI(`npx skills`)로 그대로
설치할 수 있습니다.

```bash
npx skills add leehyunseok-tech/kbsec-skill
```

## 왜 쓰나요

- KB증권 Open API의 인증(토큰 발급), 시세, 계좌잔고, 주문내역, 주식주문 74개 API를 에이전트가
  문서와 번들된 필드 명세(`references/endpoints.json`) 기반으로 다룰 수 있습니다.
- `scripts/kbsec.py`로 문서 확인에서 끝나지 않고 실제 조회/주문 호출까지 바로 검증할 수 있습니다.
- 사용자가 자율거래를 위임하면 에이전트가 잔고, 보유주식, 시세, 호가, 미체결 주문을 확인하면서
  매수/매도/정정/취소를 반복 수행할 수 있습니다.
- 주문 생성/정정/취소는 CLI 기본값이 dry-run이며, 실제 실행은 `--execute --yes`가 있어야만
  동작합니다. **KB증권은 모의투자 환경을 제공하지 않으므로 dry-run이 유일한 안전장치입니다.**

## 빠른 데모

설치된 스킬 디렉터리 또는 이 저장소 루트에서 실행합니다.

```bash
python3 scripts/kbsec.py list-endpoints
python3 scripts/kbsec.py spec SSAM1802
```

주문 요청은 기본적으로 실제 주문을 넣지 않고 요청 본문만 보여줍니다.

```bash
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000
```

예상 출력:

```json
{
  "dryRun": true,
  "code": "SSAM1802",
  "name": "매수주문",
  "endpoint": "/api/v1/ssam1802",
  "dataBody": {
    "mkt_tm_clsf": "1",
    "is_cd": "005930",
    "ordr_q": "1",
    "ordr_uprc": "70000",
    "ordr_ccd": "00",
    "sor_ordr_ccd": " "
  },
  "executeHint": "Re-run with --execute --yes after explicit user confirmation, or while operating under a user-delegated autonomous trading instruction. KB Securities has no sandbox/practice environment — this places a REAL order with real funds."
}
```

## 설치

전체 지원 에이전트 대상으로 설치:

```bash
npx skills add leehyunseok-tech/kbsec-skill
```

Claude Code처럼 특정 에이전트만 지정:

```bash
npx skills add leehyunseok-tech/kbsec-skill --agent claude-code
```

설치 없이 프롬프트로 사용:

```bash
npx skills use leehyunseok-tech/kbsec-skill --skill kbsec-skill --agent claude-code
```

## 지원 에이전트

`npx skills`가 지원하는 에이전트(Claude Code, Codex 등)에서 사용할 수 있습니다. OpenAI/Codex
계열 UI를 위한 `agents/openai.yaml`도 포함되어 있지만, 핵심은 범용 `SKILL.md`, `references/`,
`scripts/` 구조입니다.

## 주요 기능

- KB증권 OAuth2 방식 접근토큰 발급/캐시/폐기 (`token`/`revoke`)
- 국내/해외 주식 현재가, 호가, 예수금내역, 보유주식, 체결미체결 조회
- 매수/매도/정정/취소주문 (국내, 전용 서브커맨드) + 74개 전체 API 범용 호출 (`call <코드>`)
- 자연어로 위임된 자율 매수/매도 주문 루프
- 주문 생성/정정/취소 dry-run 및 live 실행 (`--execute --yes` 필수)
- 만료된 캐시 토큰 자동 재발급 (401 재시도 1회)
- 번들된 필드 명세(`references/endpoints.json`) 기반 요청 검증 — 필수 필드 누락 시 실행 전에 차단

## 에이전트에게 시킬 수 있는 일

```text
Use $kbsec-skill to summarize available KB Securities Open API endpoints.
```

```text
Use $kbsec-skill to check my account balance and holdings.
```

```text
Use $kbsec-skill to prepare a dry-run buy order for Samsung Electronics (005930).
```

```text
Use $kbsec-skill to trade my KB account autonomously during today's KR market session.
```

## 자격증명

다음 환경변수를 설정합니다.

```bash
export KBSEC_CLIENT_KEY="..."
export KBSEC_CLIENT_SECRET="..."
```

CLI는 프로세스 환경변수만 읽습니다(다른 셸 설정 파일은 읽지 않습니다). 값은 KB증권 Open API
개발자센터(`https://developer.kbsec.com`)에서 발급받으며, 앱키 1개가 실거래 계좌 1개에 연결됩니다.

토큰은 기본 출력에서 마스킹됩니다. 전체 access token이 꼭 필요한 경우에만
`token --show-token`을 사용하세요.

## CLI 예시

```bash
python3 scripts/kbsec.py token
python3 scripts/kbsec.py balance
python3 scripts/kbsec.py holdings
python3 scripts/kbsec.py price --symbol 005930
python3 scripts/kbsec.py orderbook --symbol 005930
python3 scripts/kbsec.py price --symbol AAPL --overseas --exchange NAS
python3 scripts/kbsec.py order-history --date 20260719 --status open
```

번들되지 않은 나머지 API도 코드만 알면 바로 호출할 수 있습니다.

```bash
python3 scripts/kbsec.py list-endpoints --category 시세분석
python3 scripts/kbsec.py spec IVU10280
python3 scripts/kbsec.py call IVU10280 --data krx_cd=0
```

## 자율 주문 실행

`buy`, `sell`, `modify-order`, `cancel-order`, 그리고 `call`로 실행하는 주문 관련 API
(`SSAM*`, `SKAM*`, `SPAO*` 등)는 실제 금융 거래에 영향을 주므로 기본값은 dry-run입니다.
**KB증권은 모의투자 환경이 없어 이 dry-run 게이트가 유일한 안전장치입니다.**

사용자가 자연어로 자율거래를 위임하면 에이전트는 현재 잔고, 보유주식, 시세, 호가, 미체결
주문을 확인하면서 주문 생성/정정/취소를 반복 수행할 수 있습니다. 매 주문마다 다시 확인받는
방식이 아니라, 사용자의 위임이 유지되는 동안 에이전트가 live mutation에 `--execute --yes`를
붙여 실행할 수 있는 방식입니다.

```bash
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000 --execute --yes
```

## 저장소 구성

- `SKILL.md`: 에이전트가 읽는 스킬 진입점
- `agents/openai.yaml`: OpenAI/Codex 계열 UI 메타데이터
- `references/workflows.md`: 인증 흐름, 엔드포인트 맵, 안전 규칙, 자율 주문 루프
- `references/endpoints.json`: KB증권 공식 필드 명세를 파싱해 번들한 74개 API 스키마
- `scripts/kbsec.py`: 표준 라이브러리 기반 CLI 헬퍼 (토큰 발급/캐시, 범용 호출, 주문 서브커맨드)
- `PUBLISHING.md`: (메인테이너용) 이 스킬을 만들고 GitHub에 올리고 npx로 설치 가능하게 만든
  전체 과정 — 스킬 자체를 쓰는 데는 필요 없습니다.

## 검증

```bash
python3 scripts/kbsec.py list-endpoints
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000
```

## 주의

이 프로젝트는 수익을 보장하지 않습니다. 계좌 조회와 주문 API는 실제 금융 계정에 영향을 줄 수
있으며, KB증권은 모의투자 환경을 제공하지 않으므로 **모든 호출이 처음부터 실거래**입니다.
사용자가 자율거래를 위임하면 에이전트의 live 주문 실행 결과도 사용자 본인의 책임입니다.
