"""stcd 명령 처리 - 종목명 키워드 검색 (로컬 mst 파일 이용)."""

from src.utils.stock_master import search_domestic, search_overseas


def handle_stcd(args: list[str], session) -> str:
    """
    stcd 명령 처리 - 종목명/종목코드 키워드 검색 (국내 + 해외)

    사용법:
      /종목검색 {키워드}              예: /종목검색 KB금융  또는  /종목검색 005930 (국내는 코드로도 검색됨)
      /종목검색 {키워드1} {키워드2} ...  OR 검색, 예: /종목검색 카카오 네이버
    """
    if not args:
        return "사용법: /종목검색 {키워드}\n예: /종목검색 KB금융  (또는 /종목검색 005930 — 국내는 코드로도 검색됩니다)\n예: /종목검색 카카오 네이버 (여러 키워드 OR 검색)"

    domestic_matches = []
    overseas_matches = []
    for keyword in args:
        domestic_matches.extend(search_domestic(keyword, limit=10))
        overseas_matches.extend(search_overseas(keyword, limit=10))

    seen = set()
    domestic_unique = [s for s in domestic_matches if not (s.code in seen or seen.add(s.code))]
    seen = set()
    overseas_unique = [s for s in overseas_matches if not (s.ticker in seen or seen.add(s.ticker))]

    if not domestic_unique and not overseas_unique:
        return f"❌ '{' '.join(args)}' 검색 결과가 없습니다."

    lines = [f"🔍 '{' '.join(args)}' 검색 결과"]
    if domestic_unique:
        lines.append(f"\n국내 ({len(domestic_unique)}건, 최대 20건 표시):")
        lines.append(
            "  [종목명] [종목코드] [시장구분] [종목구분] [관리종목여부] [거래정지여부] [매수주문단위] [소수점매매가능여부] [소수점매매상태]"
        )
        for s in domestic_unique[:20]:
            lines.append(
                f"  [{s.name}] [{s.code}] [{s.market}] [{s.stock_type}] "
                f"[{s.managed}] [{s.halted}] [{s.order_unit}] [{s.decimal_tradable}] [{s.decimal_state}]"
            )
    if overseas_unique:
        lines.append(f"\n해외 ({len(overseas_unique)}건, 최대 20건 표시):")
        lines.append(
            "  [종목명] [티커] [거래소명] [통화코드] [종목타입] [매매구분] [매수거래단위] [매도거래단위] [소수점매매가능여부]"
        )
        for s in overseas_unique[:20]:
            lines.append(
                f"  [{s.name_kr or s.name_en}] [{s.ticker}] [{s.exchange_name}] [{s.currency}] "
                f"[{s.stock_type}] [{s.trade_restriction}] [{s.buy_unit}] [{s.sell_unit}] [{s.decimal_tradable}]"
            )
    return "\n".join(lines)
