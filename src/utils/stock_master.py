"""
종목마스터 로컬 조회 (코스피/코스닥/해외주식).

openapi_field_*.mst 파일이 이미 로컬에 있으므로 API 호출 없이 파일을 읽어 조회한다.
런타임 데이터 위치는 프로젝트 루트의 mst/api/ — manage/generate/generate_mst.py 파이프라인이
mst/origin/ 원본과 공식 명세(docs/mst/xlsx/mst_*.xlsx)로부터 생성한 파일을 그대로 읽는다.
원본이 갱신되면 `uv run python -m manage.generate.generate_mst` 재실행으로만 갱신한다.

파일 형식(파이프 구분, UTF-8, 첫 줄은 헤더):
  openapi_field_kospi-kosdaq.mst (코스피+코스닥 통합)
    시장구분|종목코드|종목명|종목구분|관리종목여부|거래정지여부|매수주문단위|소수점매매가능여부|소수점매매상태
  openapi_field_foren-us.mst (해외주식·미국)
    거래소코드|거래소명|종목코드|종목명_한글|종목명_영문|통화코드|종목타입|매매구분|매수거래단위|매도거래단위|소수점매매가능여부

주의: 해외 거래소코드(NAS/NYS/AMX)만은 원본 코드 그대로다 — buy_command.py/
sell_command.py/srch_command.py가 이 값을 KB 주문/시세 API의 krx_cd 파라미터로
그대로 전달하기 때문에(OverseasStock.exchange), 사람이 읽기 좋은 이름으로 바꾸면
실거래 API 호출이 깨진다. 표시용 한글명은 OverseasStock.exchange_name에 별도로 있다.
그 외 필드(종목구분/관리종목여부/거래정지여부/매수주문단위/소수점매매·종목타입·
매매구분·거래단위)는 아무 코드도 이 값을 그대로 API에 넘기지 않으므로 전부
사람이 읽기 좋은 텍스트로만 보관한다.
"""

from dataclasses import dataclass
from functools import lru_cache

from src.paths import MST_RUNTIME_DIR as MST_DIR


@dataclass(frozen=True)
class DomesticStock:
    market: str  # 'KOSPI' | 'KOSDAQ'
    code: str
    name: str
    stock_type: str  # 종목구분 (주식/ETF/ETN 등, 코스닥은 원본에 필드가 없어 항상 공란)
    managed: str  # 관리종목여부 (정상/관리종목)
    halted: str  # 거래정지여부 (정상/거래정지)
    order_unit: str  # 매수주문단위 (1주 등, 코스닥은 원본에 필드가 없어 항상 공란)
    decimal_tradable: str  # 소수점매매가능여부 (소수점매매가능/소수점매매불가)
    decimal_state: str  # 소수점매매상태 (정상/매수불가/매도불가/매수·매도불가)


@dataclass(frozen=True)
class OverseasStock:
    exchange: str  # 거래소코드 원본(NAS/NYS/AMX) — 실거래 API 파라미터로 그대로 쓰임
    exchange_name: str  # 거래소명(나스닥/뉴욕/아멕스, 표시용)
    ticker: str
    name_kr: str
    name_en: str
    currency: str  # 통화코드
    stock_type: str  # 종목타입 (주식/DR/미국우선주/ETF·ETN 등)
    trade_restriction: str  # 매매구분 (제한없음/매수불가(SELL ONLY)/매매불가)
    buy_unit: str  # 매수거래단위 (1주 등)
    sell_unit: str  # 매도거래단위 (1주 등)
    decimal_tradable: str  # 소수점매매가능여부 (소수점매매가능/소수점매매불가)


def _read_rows(filename):
    """헤더 행(첫 줄)을 건너뛰고 나머지를 파이프로 분리해 반환."""
    path = MST_DIR / filename
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines[1:]:
        if not line:
            continue
        fields = line.split("|")
        if not fields[0]:
            continue
        rows.append(fields)
    return rows


def _load_domestic():
    """openapi_field_kospi-kosdaq.mst 한 파일을 읽어 코스피/코스닥으로 나눠 반환.

    컬럼(0-based): 0시장구분 1종목코드 2종목명 3종목구분 4관리종목여부 5거래정지여부
    6매수주문단위 7소수점매매가능여부 8소수점매매상태
    """
    kospi, kosdaq = [], []
    for f in _read_rows("openapi_field_kospi-kosdaq.mst"):
        stock = DomesticStock(
            market=f[0],
            code=f[1],
            name=f[2],
            stock_type=f[3],
            managed=f[4],
            halted=f[5],
            order_unit=f[6],
            decimal_tradable=f[7],
            decimal_state=f[8],
        )
        (kospi if f[0] == "KOSPI" else kosdaq).append(stock)
    return kospi, kosdaq


def _load_overseas():
    """openapi_field_foren-us.mst를 읽어 OverseasStock 리스트로 반환.

    컬럼(0-based): 0거래소코드 1거래소명 2종목코드 3종목명_한글 4종목명_영문 5통화코드
    6종목타입 7매매구분 8매수거래단위 9매도거래단위 10소수점매매가능여부
    """
    stocks = []
    for f in _read_rows("openapi_field_foren-us.mst"):
        stocks.append(
            OverseasStock(
                exchange=f[0],
                exchange_name=f[1],
                ticker=f[2],
                name_kr=f[3],
                name_en=f[4],
                currency=f[5],
                stock_type=f[6],
                trade_restriction=f[7],
                buy_unit=f[8],
                sell_unit=f[9],
                decimal_tradable=f[10],
            )
        )
    return stocks


@lru_cache(maxsize=1)
def load_all():
    """전체 종목마스터를 한 번만 로드해 캐시. (KOSPI, KOSDAQ, 해외) 튜플 반환."""
    kospi, kosdaq = _load_domestic()
    overseas = _load_overseas()
    return kospi, kosdaq, overseas


def find_by_code(code):
    """국내 종목코드로 정확히 조회. 없으면 None."""
    kospi, kosdaq, _ = load_all()
    for stock in kospi + kosdaq:
        if stock.code == code:
            return stock
    return None


def find_overseas_by_ticker(ticker):
    """해외 티커로 정확히 조회 (대소문자 무시). 없으면 None."""
    _, _, overseas = load_all()
    ticker_upper = ticker.strip().upper()
    for stock in overseas:
        if stock.ticker.upper() == ticker_upper:
            return stock
    return None


def search_domestic(keyword, limit=20):
    """국내(코스피+코스닥) 종목명 또는 종목코드에 키워드가 포함된 종목 검색.

    키워드가 숫자로만 이루어져 있으면 종목코드도 검색 대상에 포함한다(예: "005930"이나
    "5930"으로도 삼성전자를 찾을 수 있다). 문자가 섞인 키워드는 기존과 동일하게
    종목명만 검색한다 — stock_resolver.py가 6자리 코드는 이미 확정된 값으로 보고 이
    함수를 호출하지 않으므로, buy/sell/srch 등의 종목명 해석 동작에는 영향이 없다.

    좋은 매치가 잘려나가지 않도록 정확도 순으로 정렬한 뒤 limit을 적용한다:
    코드/이름 정확일치 > 이름 전방일치 > 이름 부분일치 > 코드 부분일치.
    이름 비교는 대소문자를 무시한다("kb금융"으로도 "KB금융"이 검색되도록).
    """
    kospi, kosdaq, _ = load_all()
    keyword = keyword.strip()
    kw_upper = keyword.upper()
    by_code = keyword.isdigit()
    scored = []
    for s in kospi + kosdaq:
        name_upper = s.name.upper()
        if (by_code and s.code == keyword) or name_upper == kw_upper:
            score = 0
        elif name_upper.startswith(kw_upper):
            score = 1
        elif kw_upper in name_upper:
            score = 2
        elif by_code and keyword in s.code:
            score = 3
        else:
            continue
        scored.append((score, s))
    scored.sort(key=lambda pair: (pair[0], pair[1].name))
    return [s for _, s in scored[:limit]]


def search_overseas(keyword, limit=20):
    """해외 종목의 티커/한글명/영문명에 키워드가 포함된 종목 검색 (대소문자 무시).

    정확도 순으로 정렬한 뒤 limit을 적용한다: 티커 정확일치 > 티커 전방일치 >
    티커 부분일치 > 한글명 부분일치 > 영문명 부분일치. "IO"를 입력했을 때
    IONQ(티커 전방일치)가 영문명에 우연히 "IO"가 들어가는 종목(CORPORATION 등)보다
    먼저 오도록 하기 위함.
    """
    _, _, overseas = load_all()
    keyword_upper = keyword.strip().upper()
    scored = []
    for s in overseas:
        ticker_upper = s.ticker.upper()
        if ticker_upper == keyword_upper:
            score = 0
        elif ticker_upper.startswith(keyword_upper):
            score = 1
        elif keyword_upper in ticker_upper:
            score = 2
        elif keyword_upper in s.name_kr.upper():
            score = 3
        elif keyword_upper in s.name_en.upper():
            score = 4
        else:
            continue
        scored.append((score, s))
    scored.sort(key=lambda pair: (pair[0], pair[1].ticker))
    return [s for _, s in scored[:limit]]


def search_exact(keyword):
    """이름/코드/티커가 정확히 일치(대소문자 무시)하는 종목만 반환.

    웹 검색창에서 Enter를 눌렀을 때 "삼성전자"처럼 완성된 이름으로 부분일치
    잡음(ETF/ETN 등) 없이 그 종목만 남기기 위한 함수. (국내결과, 해외결과) 튜플.
    """
    kospi, kosdaq, overseas = load_all()
    kw = keyword.strip()
    kw_upper = kw.upper()
    if not kw:
        return [], []
    domestic = [s for s in kospi + kosdaq if s.code == kw or s.name.upper() == kw_upper]
    overseas_hits = [
        s
        for s in overseas
        if s.ticker.upper() == kw_upper or s.name_kr.upper() == kw_upper or s.name_en.upper() == kw_upper
    ]
    return domestic, overseas_hits


def search_any(keyword, limit=20):
    """국내+해외 통합 키워드 검색. (국내결과, 해외결과) 튜플 반환."""
    return search_domestic(keyword, limit), search_overseas(keyword, limit)


def _is_word_char(ch: str) -> bool:
    """단어 경계 판정용 — 한글 음절/영숫자면 단어의 일부로 본다."""
    return ch.isalnum() or "가" <= ch <= "힣"


def _name_at_word_boundary(name_upper: str, text_upper: str) -> bool:
    """종목명이 문장 안에서 '단어 시작 위치'에 등장하는지 확인.

    단순 부분 문자열 검사는 "하이닉스 사줘"에서 실제 종목 "이닉스"(452400)가
    (하'이닉스') 단어 중간에 매칭되는 오탐을 낸다 — 매칭 위치 바로 앞 글자가
    한글/영숫자면 단어 중간이므로 거부한다.
    """
    idx = text_upper.find(name_upper)
    while idx != -1:
        if idx == 0 or not _is_word_char(text_upper[idx - 1]):
            return True
        idx = text_upper.find(name_upper, idx + 1)
    return False


def detect_in_text(text, limit=5):
    """
    자유 문장 안에 포함된 종목을 찾아 반환 (웹의 자연어 명령 종목 미리보기용).

    "KB금융 10주 사줘" → KB금융(105560)을 인식하는 식으로, AI 변환을 호출하기
    전에 로컬 마스터만으로 문장 속 종목을 미리 보여주기 위한 함수다.

    매칭 규칙 (정확 매칭이 하나라도 있으면 그것만 반환):
      1) 정확 매칭 — 6자리 숫자 토큰의 코드 일치 / 종목명이 문장의 단어 경계에서
         등장("삼성전자 10주" → 삼성전자·삼성전자우, 긴 이름 우선) / 해외 티커가
         토큰과 정확 일치(짧은 티커 A·F 등의 오탐 방지를 위해 부분일치는 안 씀).
      2) 폴백(부분어) — 토큰(2자 이상, 숫자 제외)이 종목명의 일부인 경우:
         "하이닉스 사줘"의 "하이닉스" ⊂ "SK하이닉스" → SK하이닉스를 보여준다.
         이름이 짧을수록(토큰과 가까울수록) 먼저.
    반환은 DomesticStock/OverseasStock 혼합 리스트.
    """
    text = (text or "").strip()
    if len(text) < 2:
        return []
    kospi, kosdaq, overseas = load_all()
    text_upper = text.upper()  # 이름 매칭은 대소문자 무시 ("kb금융 사줘" → KB금융)
    tokens = text.replace(",", " ").split()
    tokens_upper = {t.upper() for t in tokens}
    name_tokens = [t.upper() for t in tokens if len(t) >= 2 and not t.isdigit()]

    exact = []  # (우선순위, 정렬키, stock)
    partial = []
    seen = set()

    def add(bucket, priority, kind, ident, stock, sort_len):
        if (kind, ident) in seen:
            return
        seen.add((kind, ident))
        bucket.append((priority, sort_len, stock))

    for token in tokens:
        if token.isdigit() and len(token) == 6:
            stock = find_by_code(token)
            if stock:
                add(exact, 0, "D", stock.code, stock, 0)

    for s in kospi + kosdaq:
        name_upper = s.name.upper()
        if len(s.name) >= 2 and _name_at_word_boundary(name_upper, text_upper):
            add(exact, 1, "D", s.code, s, -len(s.name))  # 긴 이름 우선(삼성전자우 > 삼성전자)
        elif name_tokens and any(t in name_upper for t in name_tokens):
            add(partial, 2, "D", s.code, s, len(s.name))  # 짧은 이름 우선(SK하이닉스 > 관련 ETF)

    for s in overseas:
        name_upper = s.name_kr.upper()
        ticker_hit = s.ticker.upper() in tokens_upper
        name_hit = len(s.name_kr) >= 2 and _name_at_word_boundary(name_upper, text_upper)
        if ticker_hit or name_hit:
            add(exact, 1, "O", s.ticker, s, -(len(s.name_kr) if name_hit else len(s.ticker)))
        elif s.name_kr and name_tokens and any(t in name_upper for t in name_tokens):
            add(partial, 2, "O", s.ticker, s, len(s.name_kr))

    # 정확 매칭이 있으면 그것만(잡음 방지), 없을 때만 부분어 폴백을 보여준다
    chosen = exact if exact else partial
    chosen.sort(key=lambda item: (item[0], item[1]))
    return [s for _, _, s in chosen[:limit]]
