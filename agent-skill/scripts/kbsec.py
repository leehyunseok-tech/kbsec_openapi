#!/usr/bin/env python3
"""Standard-library CLI for the KB Securities (KB증권) Open API.

No third-party dependencies. Reads credentials from environment variables,
issues/caches an OAuth2-style access token, and can call any of the 74
bundled REST endpoints (see references/endpoints.json) either generically
(`call <CODE>`) or through a handful of convenience subcommands.

KB Securities has no sandbox/practice environment: every call in this
script hits the real, production API (https://developer.kbsec.com:32484).
Order-placing endpoints are dry-run by default and require --execute --yes
to actually submit a live order. See references/workflows.md for details.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
ENDPOINTS_PATH = SCRIPT_DIR.parent / "references" / "endpoints.json"

DEFAULT_BASE_URL = "https://developer.kbsec.com:32484"
TOKEN_PATH = "/oauth2/token"
REVOKE_PATH = "/oauth2/revoke"
USER_AGENT = "kbsec-skill/1.0"
TOKEN_SKEW_SECONDS = 60

CLIENT_KEY_ENV = ("KBSEC_CLIENT_KEY", "KBSEC_APP_KEY", "KB_CLIENT_KEY")
CLIENT_SECRET_ENV = ("KBSEC_CLIENT_SECRET", "KBSEC_APP_SECRET", "KB_CLIENT_SECRET")

# API codes that place, modify, or cancel a REAL order (real money, no sandbox).
# These are dry-run by default across `call` and every order convenience command.
MUTATING_CODES = {
    "SSAM0831",  # 예약주문접수
    "SSAM1801",  # 매도주문
    "SSAM1802",  # 매수주문
    "SSAM1805",  # 정정주문
    "SSAM1806",  # 취소주문
    "SSAM5762",  # 소수점 매도주문
    "SSAM5763",  # 소수점 매수주문
    "SSAM5764",  # 소수점 주문취소
    "SKAM2101",  # 매도_매수주문 (해외)
    "SKAM2102",  # 정정_취소주문 (해외)
    "SKAM2201",  # 소수점매도_매수주문 (해외)
    "SKAM2202",  # 소수점취소주문 (해외)
    "SPAO2104",  # 주식예약주문미국
    "SPAO2106",  # 예약주문취소미국
}

ORDER_TYPE_MAP = {"limit": "00", "market": "03", "best": "12", "priority": "13", "mid": "M3"}
MARKET_TIME_MAP = {"regular": "1", "pre-close": "2", "post-close": "3", "single": "4"}

TOKEN_FROM_CACHE = False


class KbsecApiError(Exception):
    def __init__(self, status: int, headers: dict[str, str], body: Any):
        self.status = status
        self.headers = headers
        self.body = body
        super().__init__(f"HTTP {status}: {json.dumps(body, ensure_ascii=False)[:500]}")


# ---------------------------------------------------------------- env/cache

def env_first(names: tuple[str, ...]) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def token_cache_path() -> Path | None:
    override = os.environ.get("KBSEC_TOKEN_CACHE")
    if override:
        if override.lower() in {"none", "off", "false", "0"}:
            return None
        return Path(override).expanduser()
    base = os.environ.get("XDG_CACHE_HOME")
    cache_root = Path(base).expanduser() if base else Path.home() / ".cache"
    return cache_root / "kbsec-skill" / "token.json"


def client_hash(client_key: str) -> str:
    return hashlib.sha256(client_key.encode("utf-8")).hexdigest()


def load_token_cache(client_key: str) -> str | None:
    path = token_cache_path()
    if path is None or not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if cached.get("client_key_sha256") != client_hash(client_key):
        return None
    expires_at = float(cached.get("expires_at", 0))
    if expires_at <= time.time() + TOKEN_SKEW_SECONDS:
        return None
    token = cached.get("access_token")
    return token if isinstance(token, str) and token else None


def save_token_cache(client_key: str, token: str, expires_in: int) -> None:
    path = token_cache_path()
    if path is None:
        return
    payload = {
        "client_key_sha256": client_hash(client_key),
        "access_token": token,
        "expires_at": int(time.time()) + int(expires_in),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def clear_token_cache() -> None:
    path = token_cache_path()
    if path and path.exists():
        path.unlink()


# ---------------------------------------------------------------- device info

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return "127.0.0.1"


def get_mac_address() -> str:
    node = uuid.getnode()
    return ":".join(f"{(node >> shift) & 0xFF:02X}" for shift in range(40, -1, -8))


def device_info() -> dict[str, str]:
    return {
        "udId": "",
        "subChannel": "",
        "deviceModel": "Server",
        "deviceOs": "Server",
        "carrier": "",
        "connectionType": "",
        "appName": "kbsec-skill",
        "appVersion": "1.0.0",
        "scrNo": "0000",
    }


# ---------------------------------------------------------------- HTTP

def decode_body(raw: bytes) -> Any:
    if not raw:
        return None
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def post_json(url: str, payload: dict[str, Any], token: str | None, args: argparse.Namespace) -> tuple[int, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["authorization"] = f"Bearer {token}"
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=args.timeout) as response:
            return response.status, decode_body(response.read())
    except HTTPError as exc:
        body = decode_body(exc.read())
        raise KbsecApiError(exc.code, {k.lower(): v for k, v in exc.headers.items()}, body) from exc
    except URLError as exc:
        raise SystemExit(f"Network error: {exc.reason}") from exc


def get_access_token(args: argparse.Namespace, *, force_refresh: bool = False) -> str:
    global TOKEN_FROM_CACHE
    client_key = env_first(CLIENT_KEY_ENV)
    client_secret = env_first(CLIENT_SECRET_ENV)
    if not client_key or not client_secret:
        raise SystemExit(
            "Missing KB Securities credentials. Set KBSEC_CLIENT_KEY and KBSEC_CLIENT_SECRET "
            "(issued from the KB Securities Open API developer portal)."
        )

    if not force_refresh and not getattr(args, "no_token_cache", False):
        cached = load_token_cache(client_key)
        if cached:
            TOKEN_FROM_CACHE = True
            return cached
    TOKEN_FROM_CACHE = False

    payload = {
        "dataHeader": device_info(),
        "dataBody": {
            "grantType": "client_credentials",
            "clientId": client_key,
            "clientSecret": client_secret,
        },
    }
    url = args.base_url.rstrip("/") + TOKEN_PATH
    status, body = post_json(url, payload, None, args)
    header = (body or {}).get("dataHeader", {}) if isinstance(body, dict) else {}
    data_body = (body or {}).get("dataBody", {}) if isinstance(body, dict) else {}
    if status != 200 or header.get("resultCode") != "200" or not data_body.get("access_token"):
        raise SystemExit(
            f"Token issuance failed: resultCode={header.get('resultCode')!r} "
            f"resultMessage={header.get('resultMessage')!r}"
        )
    token = str(data_body["access_token"])
    expires_in = int(data_body.get("expires_in", 0) or 0)
    if not getattr(args, "no_token_cache", False) and expires_in > TOKEN_SKEW_SECONDS:
        save_token_cache(client_key, token, expires_in)
    return token


def redact_token(token: str) -> str:
    if len(token) <= 16:
        return "***"
    return token[:8] + "..." + token[-6:]


def do_business_call(code: str, name: str, endpoint: str, data_body: dict[str, Any],
                      args: argparse.Namespace) -> dict[str, Any]:
    token = get_access_token(args)
    url = args.base_url.rstrip("/") + endpoint
    payload = {
        "dataBody": data_body,
        "dataHeader": {"ipAddr": get_local_ip(), "macAddr": get_mac_address()},
    }
    try:
        status, body = post_json(url, payload, token, args)
    except KbsecApiError as exc:
        # A cached token can go stale if it was reissued from another process/session
        # (KB documents no multi-token guarantee); refresh once and retry on 401.
        if exc.status == 401 and TOKEN_FROM_CACHE:
            token = get_access_token(args, force_refresh=True)
            status, body = post_json(url, payload, token, args)
        else:
            raise
    header = (body or {}).get("dataHeader", {}) if isinstance(body, dict) else {}
    success = status == 200 and header.get("resultCode") == "200"
    return {
        "success": success,
        "code": code,
        "name": name,
        "resultCode": header.get("resultCode"),
        "resultMessage": header.get("resultMessage"),
        "response": body,
    }


# ---------------------------------------------------------------- endpoint spec bundle

def load_endpoints() -> list[dict[str, Any]]:
    if not ENDPOINTS_PATH.exists():
        raise SystemExit(f"Bundled endpoint spec not found: {ENDPOINTS_PATH}")
    return json.loads(ENDPOINTS_PATH.read_text(encoding="utf-8"))


def find_spec(code: str) -> dict[str, Any] | None:
    code_upper = code.strip().upper()
    for entry in load_endpoints():
        if entry.get("code") and entry["code"].upper() == code_upper:
            return entry
    return None


def parse_key_value(items: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"Invalid --data value {item!r}; expected name=value")
        key, value = item.split("=", 1)
        result[key.strip()] = value
    return result


def build_data_body(spec: dict[str, Any], provided: dict[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {}
    missing: list[dict[str, Any]] = []
    for f in spec.get("fields", []):
        name = f["name_en"]
        if name in provided:
            body[name] = provided[name]
        elif f["required"]:
            missing.append(f)
        else:
            body[name] = " " * max(f["length"], 1)
    if missing:
        details = []
        for f in missing:
            note = f"{f['name_en']}({f['name_kr']})"
            if f["choices"]:
                note += " choices=" + ",".join(f"{c}:{label}" for c, label in f["choices"])
            details.append(note)
        raise SystemExit(
            "Missing required field(s):\n  " + "\n  ".join(details) +
            f"\nPass --data name=value for each, or run `spec {spec['code']}` for the full field list."
        )
    for key, value in provided.items():
        body.setdefault(key, value)
    return body


def describe_spec_text(spec: dict[str, Any]) -> str:
    lines = [f"{spec['code']} {spec['name']}  [{spec['category']}]", f"POST {spec['endpoint']}"]
    if spec["code"] in MUTATING_CODES:
        lines.append(
            "⚠ LIVE MUTATION — places/changes/cancels a REAL order. "
            "Dry-run by default; requires --execute --yes to actually run."
        )
    if not spec.get("fields"):
        lines.append("\nNo input fields — call directly.")
        return "\n".join(lines)
    lines.append("\nFields:")
    for f in spec["fields"]:
        req = "required" if f["required"] else "optional"
        if f["choices"]:
            choice_str = ", ".join(f"{c}:{label}" for c, label in f["choices"])
            lines.append(f"  {f['name_en']} ({f['name_kr']}) [{req}] choices: {choice_str}")
        else:
            note = f" — {f['description']}" if f["description"] else ""
            lines.append(f"  {f['name_en']} ({f['name_kr']}) [{req}], max {f['length']} chars{note}")
    return "\n".join(lines)


# ---------------------------------------------------------------- output

def emit(payload: Any, args: argparse.Namespace) -> None:
    if getattr(args, "compact", False):
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- generic commands

def cmd_list_endpoints(args: argparse.Namespace) -> None:
    entries = load_endpoints()
    if args.category:
        entries = [e for e in entries if args.category.lower() in (e.get("category") or "").lower()]
    if args.search:
        kw = args.search.lower()
        entries = [
            e for e in entries
            if kw in (e.get("code") or "").lower()
            or kw in (e.get("name") or "").lower()
            or kw in (e.get("category") or "").lower()
        ]
    if args.json:
        emit(entries, args)
        return
    for e in entries:
        code = e.get("code") or "-"
        mutating = " [LIVE]" if e.get("code") in MUTATING_CODES else ""
        print(f"{code:10s} {e.get('method', 'POST'):4s} {e.get('endpoint', ''):24s} {e.get('category', ''):24s} {e.get('name', '')}{mutating}")


def cmd_spec(args: argparse.Namespace) -> None:
    spec = find_spec(args.code)
    if spec is None:
        raise SystemExit(f"Unknown API code: {args.code}. Run `list-endpoints` to browse.")
    if args.json:
        emit(spec, args)
    else:
        print(describe_spec_text(spec))


def cmd_token(args: argparse.Namespace) -> None:
    token = get_access_token(args, force_refresh=args.force)
    payload = {"access_token": token if args.show_token else redact_token(token), "source": "cache" if TOKEN_FROM_CACHE else "issued"}
    emit(payload, args)


def cmd_revoke(args: argparse.Namespace) -> None:
    client_key = env_first(CLIENT_KEY_ENV)
    client_secret = env_first(CLIENT_SECRET_ENV)
    if not client_key or not client_secret:
        raise SystemExit("Missing KB Securities credentials. Set KBSEC_CLIENT_KEY and KBSEC_CLIENT_SECRET.")
    token = get_access_token(args)
    payload = {
        "dataHeader": device_info(),
        "dataBody": {"token": token, "clientId": client_key, "clientSecret": client_secret},
    }
    url = args.base_url.rstrip("/") + REVOKE_PATH
    status, body = post_json(url, payload, None, args)
    header = (body or {}).get("dataHeader", {}) if isinstance(body, dict) else {}
    success = status == 200 and header.get("resultCode") == "200"
    if success:
        clear_token_cache()
    emit({"success": success, "resultCode": header.get("resultCode"), "resultMessage": header.get("resultMessage")}, args)


def cmd_call(args: argparse.Namespace) -> None:
    spec = find_spec(args.code)
    if spec is None:
        raise SystemExit(f"Unknown API code: {args.code}. Run `list-endpoints` to browse or `spec {args.code}`.")
    provided = parse_key_value(args.data)
    if args.json_body:
        try:
            extra = json.loads(args.json_body)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--json-body is not valid JSON: {exc}") from exc
        provided.update({k: v for k, v in extra.items()})
    data_body = build_data_body(spec, provided)
    is_mutating = spec["code"] in MUTATING_CODES

    if is_mutating and not args.execute:
        emit(_dry_run_payload(spec, data_body), args)
        return
    if is_mutating and not args.yes:
        raise SystemExit("Live order mutations require both --execute and --yes")

    result = do_business_call(spec["code"], spec["name"], spec["endpoint"], data_body, args)
    emit(result, args)


def _dry_run_payload(spec: dict[str, Any], data_body: dict[str, Any]) -> dict[str, Any]:
    return {
        "dryRun": True,
        "code": spec["code"],
        "name": spec["name"],
        "endpoint": spec["endpoint"],
        "dataBody": data_body,
        "executeHint": (
            "Re-run with --execute --yes after explicit user confirmation, or while operating "
            "under a user-delegated autonomous trading instruction. KB Securities has no "
            "sandbox/practice environment — this places a REAL order with real funds."
        ),
    }


# ---------------------------------------------------------------- read-only convenience commands

def _run_query(args: argparse.Namespace, code: str, provided: dict[str, str]) -> None:
    spec = find_spec(code)
    if spec is None:
        raise SystemExit(f"Bundled spec missing for {code} — references/endpoints.json may be out of date.")
    data_body = build_data_body(spec, provided)
    result = do_business_call(code, spec["name"], spec["endpoint"], data_body, args)
    emit(result, args)


def cmd_balance(args: argparse.Namespace) -> None:
    _run_query(args, "SSQM0004", {})


def cmd_holdings(args: argparse.Namespace) -> None:
    _run_query(args, "SSQM1801", {})


def cmd_price(args: argparse.Namespace) -> None:
    if args.overseas:
        if not args.exchange:
            raise SystemExit("--exchange is required with --overseas (NAS, NYS, or AMX)")
        _run_query(args, "GSS10030", {"krx_cd": args.exchange, "is_cd": args.symbol})
    else:
        _run_query(args, "IVU10140", {"shrt_cd": args.symbol})


def cmd_orderbook(args: argparse.Namespace) -> None:
    if args.overseas:
        if not args.exchange:
            raise SystemExit("--exchange is required with --overseas (NAS, NYS, or AMX)")
        _run_query(args, "GSS10040", {"krx_cd": args.exchange, "is_cd": args.symbol})
    else:
        _run_query(args, "IVU10070", {"is_cd": args.symbol})


def cmd_order_history(args: argparse.Namespace) -> None:
    status_map = {"all": "0", "filled": "1", "open": "2"}
    _run_query(args, "SSQM2341", {"ccls_clsf": status_map[args.status], "ordr_dt": args.date})


# ---------------------------------------------------------------- domestic order convenience commands

def _order_type_body(args: argparse.Namespace) -> dict[str, str]:
    if args.order_type not in ORDER_TYPE_MAP:
        raise SystemExit(f"--order-type must be one of {sorted(ORDER_TYPE_MAP)}")
    if args.market_time not in MARKET_TIME_MAP:
        raise SystemExit(f"--market-time must be one of {sorted(MARKET_TIME_MAP)}")
    price = args.price if args.price is not None else 0
    return {
        "mkt_tm_clsf": MARKET_TIME_MAP[args.market_time],
        "is_cd": args.symbol,
        "ordr_q": str(args.qty),
        "ordr_uprc": str(price),
        "ordr_ccd": ORDER_TYPE_MAP[args.order_type],
    }


def _run_order_mutation(args: argparse.Namespace, code: str, provided: dict[str, str]) -> None:
    spec = find_spec(code)
    if spec is None:
        raise SystemExit(f"Bundled spec missing for {code} — references/endpoints.json may be out of date.")
    data_body = build_data_body(spec, provided)
    if not args.execute:
        emit(_dry_run_payload(spec, data_body), args)
        return
    if not args.yes:
        raise SystemExit("Live order mutations require both --execute and --yes")
    result = do_business_call(code, spec["name"], spec["endpoint"], data_body, args)
    emit(result, args)


def cmd_buy(args: argparse.Namespace) -> None:
    _run_order_mutation(args, "SSAM1802", _order_type_body(args))


def cmd_sell(args: argparse.Namespace) -> None:
    _run_order_mutation(args, "SSAM1801", _order_type_body(args))


def cmd_modify_order(args: argparse.Namespace) -> None:
    body = _order_type_body(args)
    body["crct_clsf"] = "1" if args.partial else "2"
    body["orgn_ordr_no"] = args.order_no
    _run_order_mutation(args, "SSAM1805", body)


def cmd_cancel_order(args: argparse.Namespace) -> None:
    body = {
        "is_cd": args.symbol,
        "crct_clsf": "1" if args.partial else "2",
        "orgn_ordr_no": args.order_no,
    }
    if args.qty is not None:
        body["ordr_q"] = str(args.qty)
    _run_order_mutation(args, "SSAM1806", body)


# ---------------------------------------------------------------- argparse plumbing

def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=os.environ.get("KBSEC_HOST_URL", DEFAULT_BASE_URL))
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("KBSEC_TIMEOUT", "10")))
    parser.add_argument("--no-token-cache", action="store_true")
    parser.add_argument("--compact", action="store_true", help="print single-line JSON")


def add_mutation_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--execute", action="store_true", help="actually submit (default is dry-run)")
    parser.add_argument("--yes", action="store_true", help="required together with --execute for live mutations")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kbsec.py", description="KB Securities (KB증권) Open API CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("list-endpoints", help="list all bundled endpoints")
    p.add_argument("--category", help="filter by category substring, e.g. '주식주문'")
    p.add_argument("--search", help="filter by code/name/category substring")
    p.add_argument("--json", action="store_true")
    add_common(p)
    p.set_defaults(func=cmd_list_endpoints)

    p = subparsers.add_parser("spec", help="show the field spec for one API code")
    p.add_argument("code")
    p.add_argument("--json", action="store_true")
    add_common(p)
    p.set_defaults(func=cmd_spec)

    p = subparsers.add_parser("token", help="issue or reuse a cached OAuth2 access token")
    p.add_argument("--force", action="store_true", help="force reissue, bypassing the cache")
    p.add_argument("--show-token", action="store_true", help="print the full token instead of a redacted form")
    add_common(p)
    p.set_defaults(func=cmd_token)

    p = subparsers.add_parser("revoke", help="revoke the current token (/oauth2/revoke) and clear the cache")
    add_common(p)
    p.set_defaults(func=cmd_revoke)

    p = subparsers.add_parser("call", help="call any bundled API code generically")
    p.add_argument("code")
    p.add_argument("--data", action="append", help="field=value, repeatable")
    p.add_argument("--json-body", help="JSON object merged on top of --data")
    add_mutation_flags(p)
    add_common(p)
    p.set_defaults(func=cmd_call)

    p = subparsers.add_parser("balance", help="GET-equivalent: 예수금내역 (SSQM0004)")
    add_common(p)
    p.set_defaults(func=cmd_balance)

    p = subparsers.add_parser("holdings", help="GET-equivalent: 보유주식 조회 (SSQM1801)")
    add_common(p)
    p.set_defaults(func=cmd_holdings)

    p = subparsers.add_parser("price", help="current price, domestic (IVU10140) or --overseas (GSS10030)")
    p.add_argument("--symbol", required=True)
    p.add_argument("--overseas", action="store_true")
    p.add_argument("--exchange", help="NAS/NYS/AMX, required with --overseas")
    add_common(p)
    p.set_defaults(func=cmd_price)

    p = subparsers.add_parser("orderbook", help="quote/orderbook, domestic (IVU10070) or --overseas (GSS10040)")
    p.add_argument("--symbol", required=True)
    p.add_argument("--overseas", action="store_true")
    p.add_argument("--exchange", help="NAS/NYS/AMX, required with --overseas")
    add_common(p)
    p.set_defaults(func=cmd_orderbook)

    p = subparsers.add_parser("order-history", help="체결미체결 조회 (SSQM2341), domestic")
    p.add_argument("--date", required=True, help="YYYYMMDD")
    p.add_argument("--status", choices=["all", "filled", "open"], default="all")
    add_common(p)
    p.set_defaults(func=cmd_order_history)

    for name, help_text, func in (
        ("buy", "매수주문 (SSAM1802), domestic — LIVE, dry-run by default", cmd_buy),
        ("sell", "매도주문 (SSAM1801), domestic — LIVE, dry-run by default", cmd_sell),
    ):
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument("--symbol", required=True, help="종목코드 (is_cd)")
        p.add_argument("--qty", required=True, type=int, help="주문수량")
        p.add_argument("--price", type=int, help="주문단가 (omit/0 for market orders)")
        p.add_argument("--order-type", default="limit", choices=sorted(ORDER_TYPE_MAP))
        p.add_argument("--market-time", default="regular", choices=sorted(MARKET_TIME_MAP))
        add_mutation_flags(p)
        add_common(p)
        p.set_defaults(func=func)

    p = subparsers.add_parser("modify-order", help="정정주문 (SSAM1805), domestic — LIVE, dry-run by default")
    p.add_argument("--symbol", required=True)
    p.add_argument("--order-no", required=True, help="원주문번호")
    p.add_argument("--qty", required=True, type=int)
    p.add_argument("--price", type=int)
    p.add_argument("--order-type", default="limit", choices=sorted(ORDER_TYPE_MAP))
    p.add_argument("--market-time", default="regular", choices=sorted(MARKET_TIME_MAP))
    p.add_argument("--partial", action="store_true", help="일부정정 (default is 전부정정)")
    add_mutation_flags(p)
    add_common(p)
    p.set_defaults(func=cmd_modify_order)

    p = subparsers.add_parser("cancel-order", help="취소주문 (SSAM1806), domestic — LIVE, dry-run by default")
    p.add_argument("--symbol", required=True)
    p.add_argument("--order-no", required=True, help="원주문번호")
    p.add_argument("--qty", type=int, help="omit for 전부취소")
    p.add_argument("--partial", action="store_true", help="일부취소 (default is 전부취소)")
    add_mutation_flags(p)
    add_common(p)
    p.set_defaults(func=cmd_cancel_order)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except KbsecApiError as exc:
        emit({"error": True, "status": exc.status, "body": exc.body}, args)
        return 1
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(str(exc), file=sys.stderr)
        return exc.code if isinstance(exc.code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())
