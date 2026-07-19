---
name: kbsec-skill
description: Work with the KB Securities (KB증권) Open API for Korean and US stock market data, stock info, account balance, holdings, order history, and order placement/modification/cancellation. Use when an agent needs to issue an OAuth2 access token, call developer.kbsec.com REST endpoints, inspect the bundled KB API field specs, or operate with KBSEC_CLIENT_KEY/KBSEC_CLIENT_SECRET credentials. KB Securities has no sandbox/practice environment — every call is against a real, live trading account.
---

# KB Securities (KB증권) Open API

## Overview

Use this skill to call the KB Securities Open API. `scripts/kbsec.py` is a dependency-free
Python 3 CLI that issues/caches an OAuth2 access token and can call any of the 74 bundled
REST endpoints, either generically (`call <CODE>`) or through convenience subcommands for
the most common flows (balance, holdings, price, orderbook, order history, buy, sell,
modify-order, cancel-order).

**KB Securities provides no sandbox/practice environment.** Every request in this skill
goes to `https://developer.kbsec.com:32484`, the production host, against a real account.
There is no equivalent of a paper-trading mode to fall back on.

## Source Selection

- Read `references/workflows.md` first for the endpoint map, authentication flow, safety
  rules, and common workflows.
- Read `references/endpoints.json` when exact field names, lengths, required/optional
  status, or enum choices matter for a specific API code — it was captured from KB's
  official field-level markdown specs (`docs/api/md` in the source project) and covers all
  74 business APIs plus token issue/revoke.
- Run `scripts/kbsec.py spec <CODE>` for a human-readable rendering of one endpoint's spec
  instead of reading the JSON directly.

## Credentials

Use `KBSEC_CLIENT_KEY` and `KBSEC_CLIENT_SECRET` (issued from the KB Securities Open API
developer portal, tied to one real account per app key). Aliases `KBSEC_APP_KEY` /
`KBSEC_APP_SECRET` and `KB_CLIENT_KEY` / `KB_CLIENT_SECRET` are also accepted. Read these
only from the process environment — never print them, and never write them into a file the
agent creates.

Never print full access tokens unless the user explicitly needs one for an external tool;
`scripts/kbsec.py token` redacts the token by default (`--show-token` to reveal it).

## CLI Quick Start

Run from the skill directory (or pass an absolute path to `kbsec.py`):

```bash
python3 scripts/kbsec.py list-endpoints
python3 scripts/kbsec.py token
python3 scripts/kbsec.py balance
python3 scripts/kbsec.py holdings
python3 scripts/kbsec.py price --symbol 005930
python3 scripts/kbsec.py orderbook --symbol 005930
python3 scripts/kbsec.py order-history --date 20260719 --status open
```

Overseas (US) market data needs an exchange code (`NAS`, `NYS`, or `AMX`):

```bash
python3 scripts/kbsec.py price --symbol AAPL --overseas --exchange NAS
```

Any of the other 74 endpoints not covered by a convenience subcommand can be called
generically once you know its required fields (`spec <CODE>`):

```bash
python3 scripts/kbsec.py spec IVU10420
python3 scripts/kbsec.py call IVU10420 --data is_cd=005930
```

## Trading Operations

Treat `buy`, `sell`, `modify-order`, `cancel-order`, and `call` on any code in
`MUTATING_CODES` (see `scripts/kbsec.py`) as live financial side effects — they place,
change, or cancel a REAL order on a REAL account, with no dry-run/paper-trading server side.

- When the user delegates autonomous trading in natural language, treat that delegation as
  permission to run repeated buy, sell, modify, and cancel operations while the instruction
  remains active. Do not require per-order reconfirmation inside the delegated run.
- Use current balance, holdings, buying power, market/orderbook data, and open-order status
  to decide each live mutation.
- Always produce a dry run first (the default, no `--execute`) to validate the exact request
  body, then execute the same action only when it still matches the delegated objective and
  current market data.
- After live mutations, check `order-history`/`call SSQM2341` and continue the delegated
  loop when appropriate: wait, modify, cancel, place follow-up orders, or stop with a
  concise report.
- Require both `--execute` and `--yes` for live order mutations.

Dry-run example:

```bash
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000
```

Live execution example:

```bash
python3 scripts/kbsec.py buy --symbol 005930 --qty 1 --price 70000 --execute --yes
```

## Response Handling

Every business response wraps KB's own `dataHeader`/`dataBody` envelope. `success` is
`true` only when the HTTP status is 200 **and** `dataHeader.resultCode == "200"` — a 200
HTTP status alone does not mean the call succeeded. On failure, `resultMessage` carries KB's
error text; surface it to the user rather than a generic "request failed."

On 401 with a cached token, the CLI reissues the token once and retries automatically (KB
does not document multi-token behavior per client, so treat a cached token as best-effort).
There is no documented rate limit for this API; if you see repeated failures under rapid
polling, back off and slow down regardless.
