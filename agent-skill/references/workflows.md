# KB Securities (KB증권) Open API Workflows

## Table of Contents

- [Official Sources](#official-sources)
- [No Sandbox Environment](#no-sandbox-environment)
- [Authentication](#authentication)
- [Request/Response Envelope](#requestresponse-envelope)
- [Endpoint Map](#endpoint-map)
- [Market Data and Stock Info](#market-data-and-stock-info)
- [Accounts and Balances](#accounts-and-balances)
- [Autonomous Trading Loop](#autonomous-trading-loop)
- [Order Workflows](#order-workflows)
- [Rate Limits](#rate-limits)
- [Errors](#errors)
- [Updating the Bundled Spec](#updating-the-bundled-spec)

## Official Sources

- Developer portal / app key issuance: `https://developer.kbsec.com`
- Production API host: `https://developer.kbsec.com:32484`
- This skill's `references/endpoints.json` was captured from KB's official field-level
  markdown specs (74 business APIs + token issue/revoke) at the time this skill was built.
  KB does not publish a single machine-readable OpenAPI/Swagger document; `endpoints.json`
  is this skill's own consolidated substitute, generated once and bundled for offline use.

## No Sandbox Environment

Unlike many broker APIs, KB Securities currently offers **no paper-trading / sandbox host**.
The only usable host is the production one, and every app key is tied to one real trading
account. There is no `--env dev` style switch in this CLI — treat every mutating call as
real money until KB ships a sandbox.

## Authentication

Exchange `KBSEC_CLIENT_KEY` and `KBSEC_CLIENT_SECRET` for an access token with
`POST /oauth2/token`.

Important behavior, different from a standard OAuth2 client-credentials flow:

- The request body is **not** form-encoded; it's JSON with KB's own envelope:
  ```json
  {
    "dataHeader": { "udId": "", "subChannel": "", "deviceModel": "Server", "deviceOs": "Server",
                     "carrier": "", "connectionType": "", "appName": "kbsec-skill",
                     "appVersion": "1.0.0", "scrNo": "0000" },
    "dataBody": { "grantType": "client_credentials", "clientId": "...", "clientSecret": "..." }
  }
  ```
- The response is **not** a standard OAuth2 token shape either — it's KB's envelope, with
  the token under `dataBody.access_token` / `dataBody.expires_in`, and success signaled by
  `dataHeader.resultCode == "200"` (not just HTTP 200).
- No refresh tokens are issued. Token lifetime is server-controlled (`expires_in` seconds).

Prefer `scripts/kbsec.py` so token caching avoids unnecessary reissuance:

```bash
python3 scripts/kbsec.py token
python3 scripts/kbsec.py token --show-token   # only when a raw token is actually needed
python3 scripts/kbsec.py revoke               # /oauth2/revoke + clears the local cache
```

## Request/Response Envelope

Every business (non-auth) call uses the same nested shape. Request:

```json
{
  "dataBody": { "...business fields, from the field spec for that code..." },
  "dataHeader": { "ipAddr": "auto-detected", "macAddr": "auto-detected" }
}
```

Response:

```json
{
  "dataHeader": { "resultCode": "200", "resultMessage": "정상처리", "processCode": "..." },
  "dataBody": { "...response fields..." }
}
```

A 200 HTTP status does **not** guarantee success — always check `dataHeader.resultCode`.
The CLI's convenience/`call` output already surfaces this as a top-level `success` boolean.

Fixed-width text fields that are optional and not supplied are blank-filled to their
documented length (KB's protocol expects the field present even when unused). Required
fields must always be supplied explicitly — the CLI refuses to blank-fill a required field,
since doing so for something like an order quantity or price would be actively wrong.

## Endpoint Map

All 74 business endpoints are under `https://developer.kbsec.com:32484/api/v1/<lowercase-code>`.
Full field-level detail lives in `references/endpoints.json`; the categories are:


| Category            | Examples                                                                     | Mutating? |
| --------------------- | ------------------------------------------------------------------------------ | ----------- |
| 국내주식 > 계좌잔고 | 예수금내역(SSQM0004), 보유주식 조회(SSQM1801), 잔고현황 조회                 | No        |
| 국내주식 > 기본시세 | 현재가(IVU10140), 호가(IVU10070), 체결(IVU10080), 차트(IVS11560)             | No        |
| 국내주식 > 시세분석 | 거래량 상위(IVU10280), 등락률 상위(IVU10240), 등 순위/랭킹류                 | No        |
| 국내주식 > 주문내역 | 체결미체결 조회(SSQM2341), 예약주문 조회                                     | No        |
| 국내주식 > 주식주문 | 매수(SSAM1802)/매도(SSAM1801)/정정(SSAM1805)/취소(SSAM1806)주문, 소수점 주문 | **Yes**   |
| 국내주식 > 투자정보 | 증시주변자금동향, 세계지수, 환율종합, 업종랭킹                               | No        |
| 해외주식 > 계좌잔고 | 매매손익, 해외주식계좌잔고평가조회(SPQM2226)                                 | No        |
| 해외주식 > 기본시세 | 현재가(GSS10030), 호가(GSS10040), 체결(GSA10020), 통합차트(GSC10060)         | No        |
| 해외주식 > 시세분석 | 거래량상위(GSA10150), 시가총액상위(GSA10170)                                 | No        |
| 해외주식 > 주문내역 | 주문체결조회(SPQM2103), 체결미체결 조회(SPQM2204)                            | No        |
| 해외주식 > 주식주문 | 매도_매수(SKAM2101)/정정_취소(SKAM2102)주문, 소수점 주문, 예약주문(미국)     | **Yes**   |

Run `python3 scripts/kbsec.py list-endpoints` for the full 76-row table (74 business + token
issue/revoke), or `--category`/`--search` to filter it. Rows tagged `[LIVE]` are in
`MUTATING_CODES` in `scripts/kbsec.py` and are dry-run gated.

## Market Data and Stock Info

Domestic (KRX) endpoints generally key off `is_cd` (종목코드) or `shrt_cd` (단축코드) — a
6-digit code such as `005930`. Overseas endpoints additionally need `krx_cd` (거래소코드):
`NAS` (Nasdaq), `NYS` (NYSE), or `AMX` (AMEX).

```bash
python3 scripts/kbsec.py price --symbol 005930
python3 scripts/kbsec.py orderbook --symbol 005930
python3 scripts/kbsec.py price --symbol AAPL --overseas --exchange NAS
python3 scripts/kbsec.py call IVS11560 --data is_cd=005930 --data chrt_clsf=D
```

## Accounts and Balances

Unlike some broker APIs, KB does not require an account-selector header — each app key
(`KBSEC_CLIENT_KEY`/`KBSEC_CLIENT_SECRET` pair) is already tied to exactly one real account
server-side.

```bash
python3 scripts/kbsec.py balance     # 예수금내역 (SSQM0004)
python3 scripts/kbsec.py holdings    # 보유주식 조회 (SSQM1801)
```

For buying-power-style checks before an order, call the dedicated inquiry codes directly,
e.g. `call SSQM1802` (매수주문가능금액, domestic) or `call SKQM2106` (해외 주문가능금액조회).

## Autonomous Trading Loop

Autonomous trading is a supported workflow for this skill, same as any delegated-trading
agent skill. When a user delegates trading in natural language, the agent may continue
without per-order reconfirmation while that instruction remains active.

Use this loop:

1. Read the current balance, holdings, buying power, open orders (`order-history --status open`), price, and orderbook for the target symbol(s).
2. Choose the next buy, sell, modify, cancel, wait, or stop action from the delegated
   objective and current data.
3. Produce a dry run for the exact order mutation (the CLI default — no `--execute`).
4. If the dry run still matches the delegated objective and current data, execute the same
   mutation with `--execute --yes`.
5. Inspect `order-history` for fills/rejections, then repeat the loop or report the final
   state.

The user is responsible for all investment outcomes from delegated live trading — KB
Securities has no sandbox, so every mutation in this loop is real money from the first call.

## Order Workflows

Domestic order type codes (`ordr_ccd`, used by `--order-type`):


| CLI value  | KB code | Meaning             |
| ------------ | --------- | --------------------- |
| `limit`    | `00`    | 지정가              |
| `market`   | `03`    | 시장가              |
| `best`     | `12`    | 최유리지정가        |
| `priority` | `13`    | 최우선지정가        |
| `mid`      | `M3`    | 중간가 (정정주문만) |

Market-time codes (`mkt_tm_clsf`, used by `--market-time`):


| CLI value    | KB code | Meaning              |
| -------------- | --------- | ---------------------- |
| `regular`    | `1`     | 정규장               |
| `pre-close`  | `2`     | 장개시전시간외종가   |
| `post-close` | `3`     | 장종료후시간외종가   |
| `single`     | `4`     | 장종료후시간외단일가 |

```bash
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000
python3 scripts/kbsec.py sell --symbol 005930 --qty 1 --price 71000 --order-type limit
python3 scripts/kbsec.py modify-order --symbol 005930 --order-no 1234567 --qty 1 --price 70500
python3 scripts/kbsec.py cancel-order --symbol 005930 --order-no 1234567
```

For live mutations, both flags are required:

```bash
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000 --execute --yes
```

`modify-order`/`cancel-order` default to 전부정정/전부취소 (full); pass `--partial` for
일부정정/일부취소 and include `--qty` for the partial amount.

Overseas order codes (`SKAM2101` 매도_매수, `SKAM2102` 정정_취소, plus the 소수점/예약주문
variants) are not wrapped by a dedicated subcommand — call them generically:

```bash
python3 scripts/kbsec.py spec SKAM2101
python3 scripts/kbsec.py call SKAM2101 \
  --data trd_dl_ccd=02 --data is_cd=AAPL \
  --data frgn_ordr_typ_cd=2 --data frgn_ordr_q=1 --data frgn_ordr_prc_p4=190.50
# review the dry run, then:
python3 scripts/kbsec.py call SKAM2101 \
  --data trd_dl_ccd=02 --data is_cd=AAPL \
  --data frgn_ordr_typ_cd=2 --data frgn_ordr_q=1 --data frgn_ordr_prc_p4=190.50 \
  --execute --yes
```

## Rate Limits

KB Securities does not publish documented per-endpoint rate limits for this API. Treat that as "undocumented," not "unlimited":
poll conservatively, especially inside an autonomous loop, and back off on repeated errors
rather than retrying tightly.

## Errors

Failures show up as `dataHeader.resultCode != "200"` with a human-readable
`dataHeader.resultMessage`, inside an otherwise-200 HTTP response — always check
`resultCode`, not just the HTTP status. Network-level failures (timeouts, TLS errors) and
non-200 HTTP statuses (e.g., 401 on a bad/expired token) surface as CLI errors with the raw
response body attached.

## Updating the Bundled Spec

`references/endpoints.json` is a point-in-time export of KB's field-level specs. If KB adds,
removes, or changes an endpoint, this file will drift. There is no automated puller bundled
here (KB has no public OpenAPI feed to diff against) — regenerating it means re-deriving the
field tables from KB's current developer-portal documentation and re-exporting in the same
shape: `{code, name, category, endpoint, method, fields: [{name_en, name_kr, length, required, description, choices}], output_labels}`.
