"""
================================================================================
API 클라이언트 코드 생성 스크립트
================================================================================
docs/api/md 하위 개별 API 명세(.md)의 "## INPUT (요청 파라미터)" 표를 파싱해
src/api/ 디렉토리에 카테고리별 파이썬 모듈(함수 1개 = API 1개)과 src/api/registry.py를
자동 생성합니다.

생성 대상이 아닌 파일: src/api/client.py, src/api/auth.py (수기 작성, 공용 로직)
생성되는 파일은 모두 상단에 "자동 생성 파일 — 수동 수정 금지" 주석이 붙습니다.
명세(md)가 추가/변경되면 이 스크립트를 다시 실행해 갱신하세요.

사용법:
  uv run python -m manage.generate.generate_api_client
================================================================================
"""

import keyword
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # sys.path 부트스트랩 전용 — 경로 상수는 src/paths.py에서
sys.path.insert(0, str(PROJECT_ROOT))  # 파일 직접 실행(-m 없이) 시에도 src.paths/manage.generate import가 풀리도록
from src.paths import DOCS_API_DIR, SRC_API_DIR as API_DIR  # noqa: E402
from manage.generate.generate_api_list import SPEC_DIR, collect_entries, dedupe  # noqa: E402

# INPUT 표는 "### 요청 예시"(구형 md) 또는 "---"(신형 md, 요청 예시 없음) 앞에서 끝난다.
# "\n\n###"만 가정하면 요청 예시가 없는 md에서 표 전체를 못 찾아 파라미터가 전부
# 사라진 함수가 생성되므로 두 형태를 모두 종결자로 인정해야 한다.
INPUT_TABLE_RE = re.compile(r"## INPUT \(요청 파라미터\)\s*\n\n(.*?)\n\n(?:###|---)", re.S)
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 코드 -> 모듈 매핑 (74개, 토큰발급은 code=None이라 별도 처리하고 여기 없음)
CODE_TO_MODULE = {
    # price_info.py — 시세 조회 (현재가/호가/체결/시장종합)
    "GSS10030": "price_info", "GSS10040": "price_info", "GSA10020": "price_info",
    "IVU10070": "price_info", "IVU10080": "price_info", "IVU10140": "price_info",
    "IVSA0070": "price_info",
    # rank_info.py — 각종 상위/순위 조회
    "GSA10150": "rank_info", "GSA10170": "rank_info", "IVS10910": "rank_info",
    "IVS11190": "rank_info", "IVU10210": "rank_info", "IVU10240": "rank_info",
    "IVU10270": "rank_info", "IVU10280": "rank_info", "IVU10550": "rank_info",
    "IVM30010": "rank_info", "GSS10180": "rank_info", "IVS10920": "rank_info",
    "IVU10020": "rank_info",
    # chart.py — 통합차트
    "GSC10060": "chart", "IVS11560": "chart",
    # stock_info.py — 종목 기본정보/기업개요
    "SIAM4983": "stock_info", "SIQM4900": "stock_info", "IVM10050": "stock_info",
    # market_info.py — 시장/거시 정보
    "IVA10370": "market_info", "IVA60140": "market_info", "IVA60190": "market_info",
    "SZQM0771": "market_info", "GSA10600": "market_info",
    # investor_chart.py — 거래원/투자자/프로그램매매
    "IVU10420": "investor_chart", "IVU10430": "investor_chart", "IVU10450": "investor_chart",
    # order.py — 국내 매매주문 (소수점 포함)
    "SSAM1801": "order", "SSAM1802": "order", "SSAM1805": "order", "SSAM1806": "order",
    "SSAM5762": "order", "SSAM5763": "order", "SSAM5764": "order",
    "SKAM2101": "order", "SKAM2102": "order", "SKAM2201": "order", "SKAM2202": "order",
    # reserve_order.py — 예약주문 (국내/미국)
    "SSAM0831": "reserve_order", "SSQM0831": "reserve_order", "SSQM0834": "reserve_order",
    "SPAO2104": "reserve_order", "SPAO2106": "reserve_order", "SPQO2105": "reserve_order",
    # account.py — 계좌/잔고/손익/증거금/예수금 조회
    "SSQM0004": "account", "SSQM1801": "account", "SSQM1802": "account", "SSQM2121": "account",
    "SSQM2341": "account", "SSQM2392": "account", "SSQM2442": "account", "SSQM2932": "account",
    "SSQM2952": "account", "SSQM5765": "account", "SPQM2103": "account", "SPQM2106": "account",
    "SPQM2204": "account", "SPQM2205": "account", "SPQM2206": "account", "SPQM2207": "account",
    "SPQM3390": "account", "SPQN5472": "account", "SPQM2226": "account", "SRQM3051": "account",
    "SKQM2106": "account", "SKQM3350": "account",
    # withdraw.py — 거래내역/출금가능금액 조회
    "SWQA2301": "withdraw", "SWQM2412": "withdraw", "SWQN2302": "withdraw",
}

MODULE_LABELS = {
    "price_info": "시세 조회 (현재가/호가/체결/시장종합)",
    "rank_info": "각종 상위/순위 조회",
    "chart": "통합차트",
    "stock_info": "종목 기본정보/기업개요",
    "market_info": "시장/거시 정보 (세계지수/환율/증시주변자금동향/장운영상태/해외시세분석)",
    "investor_chart": "거래원/투자자/프로그램매매",
    "order": "국내 주식 매매주문 (매도/매수/정정/취소, 소수점 포함)",
    "reserve_order": "예약주문 (국내/미국)",
    "account": "계좌/잔고/손익/증거금/예수금 조회",
    "withdraw": "거래내역/출금가능금액 조회",
}

GENERATED_HEADER = (
    "# 자동 생성 파일 — 수동 수정 금지.\n"
    "# manage/generate/generate_api_client.py 재실행으로 갱신하세요.\n"
)


def parse_input_table(text):
    """'## INPUT (요청 파라미터)' 표를 파싱하여 필드 리스트 반환. 섹션 없으면 빈 리스트."""
    match = INPUT_TABLE_RE.search(text)
    if not match:
        return []
    fields = []
    seen = set()
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        name, label, type_len, required, desc = cells[:5]
        if not name or name == "항목영문명" or name in seen:
            continue
        seen.add(name)
        fields.append(
            {
                "name": name,
                "label": label,
                "type": type_len,
                "required": required.strip().upper() == "Y",
                "desc": desc,
            }
        )
    return fields


def safe_ident(name):
    """필드명을 안전한 파이썬 식별자로 변환 (일반적으로 원본과 동일)."""
    ident = name if IDENT_RE.match(name) else re.sub(r"\W", "_", name)
    if not ident or not re.match(r"[A-Za-z_]", ident[0]):
        ident = f"_{ident}"
    if keyword.iskeyword(ident):
        ident = f"{ident}_"
    return ident


def endpoint_path(url):
    return urlsplit(url).path


def build_entries():
    """docs/api/md 전체를 스캔해 코드별로 {entry, fields} 딕셔너리 생성."""
    entries = dedupe(collect_entries())
    result = []
    for e in entries:
        code = e["code"]
        if code is None:
            continue  # 토큰 발급 — api/auth.py에서 수기 처리
        module = CODE_TO_MODULE.get(code)
        if module is None:
            print(f"[경고] {code} 는 CODE_TO_MODULE에 매핑되지 않아 건너뜁니다.", file=sys.stderr)
            continue
        md_path = DOCS_API_DIR / e["source_file"]
        text = md_path.read_text(encoding="utf-8")
        fields = parse_input_table(text)
        result.append({"entry": e, "module": module, "fields": fields})
    return result


def render_function(item):
    entry, fields = item["entry"], item["fields"]
    code = entry["code"]
    func_name = code.lower()
    path = endpoint_path(entry["prod_url"] or entry["dev_url"])

    # KB 명세의 필수여부(Y/N)는 부정확해 무시한다 — 모든 필드를 INPUT 표 순서대로
    # 기본값("") 있는 선택 인자로 생성하고, call_business_api에는 required=[]를 넘겨
    # 사전 "필수 파라미터 누락" 검증도 하지 않는다(실제 필수 여부는 KB 서버가 판단).
    params = []
    for f in fields:
        params.append(f'{safe_ident(f["name"])}=""')
    params.append("*")
    params.append("extra: dict | None = None")
    params.append("token")
    params.append("host_url")
    sig = ", ".join(params)

    doc_lines = [f'{code} {entry["name"]} — {entry["description"]}', ""]
    if fields:
        doc_lines.append("Args:")
        for f in fields:
            desc = f' — {f["desc"]}' if f["desc"] else ""
            doc_lines.append(f'    {safe_ident(f["name"])}: {f["label"]}{desc}')
    else:
        doc_lines.append("Args: (문서화된 요청 파라미터 없음)")
    doc_lines.append("    extra: INPUT 표에 없는 추가 dataBody 필드")
    doc_lines.append("    token, host_url: 인증 토큰 및 호스트 URL")
    docstring = "\n    ".join(doc_lines)

    body_lines = ["data_body = {"]
    for f in fields:
        ident = safe_ident(f["name"])
        body_lines.append(f'        "{f["name"]}": {ident},')
    body_lines.append("    }")
    body = "\n    ".join(body_lines)

    required_list = ""  # 필수여부 무시 — 항상 빈 리스트

    return f'''def {func_name}({sig}) -> dict:
    """{docstring}
    """
    {body}
    if extra:
        data_body.update(extra)
    return call_business_api(
        api_name="{entry["name"]}",
        api_code="{code}",
        endpoint="{path}",
        data_body=data_body,
        required=[{required_list}],
        token=token,
        host_url=host_url,
    )
'''


def write_modules(items):
    by_module = {}
    for item in items:
        by_module.setdefault(item["module"], []).append(item)

    for module, module_items in by_module.items():
        module_items.sort(key=lambda it: it["entry"]["code"])
        label = MODULE_LABELS.get(module, module)
        codes = ", ".join(it["entry"]["code"] for it in module_items)
        parts = [
            GENERATED_HEADER,
            f'"""{label}\n\n포함 API: {codes}\n"""',
            "",
            "from src.api.client import call_business_api",
            "",
            "",
        ]
        parts.append("\n\n".join(render_function(it) for it in module_items))
        parts.append("")
        (API_DIR / f"{module}.py").write_text("\n".join(parts), encoding="utf-8")


def write_registry(items):
    lines = [
        GENERATED_HEADER,
        '"""API 코드 -> 함수 매핑 (CLI 등에서 코드로 함수를 동적으로 찾을 때 사용)."""',
        "",
    ]
    modules = sorted({it["module"] for it in items})
    for module in modules:
        lines.append(f"from src.api import {module}")
    lines.append("")
    lines.append("REGISTRY = {")
    for item in sorted(items, key=lambda it: it["entry"]["code"]):
        entry, module, fields = item["entry"], item["module"], item["fields"]
        code = entry["code"]
        # 필수여부 무시 — required는 항상 빈 리스트, 모든 필드를 optional로 기록
        optional = [f["name"] for f in fields]
        lines.append(f'    "{code}": {{')
        lines.append(f'        "function": {module}.{code.lower()},')
        lines.append(f'        "name": {entry["name"]!r},')
        lines.append(f'        "module": {module!r},')
        lines.append(f'        "required": [],')
        lines.append(f"        \"optional\": {optional!r},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def list_apis(module: str | None = None):")
    lines.append('    """등록된 API 코드/이름 목록. module 지정 시 해당 모듈만 필터링."""')
    lines.append("    items = REGISTRY.items()")
    lines.append("    if module:")
    lines.append('        items = [(c, v) for c, v in items if v["module"] == module]')
    lines.append("    else:")
    lines.append("        items = list(items)")
    lines.append('    return [(code, v["name"], v["module"]) for code, v in items]')
    lines.append("")
    (API_DIR / "registry.py").write_text("\n".join(lines), encoding="utf-8")


def main():
    items = build_entries()
    write_modules(items)
    write_registry(items)
    print(f"{len(items)}개 API 함수를 {len({it['module'] for it in items})}개 모듈 + registry.py에 생성했습니다.")


if __name__ == "__main__":
    main()
