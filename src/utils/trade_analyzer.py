"""Claude API로 체결 내역 CSV를 분석 (브로커 무관)."""

import csv
from datetime import datetime, timedelta
from pathlib import Path

from anthropic import Anthropic

from config.config import claude_api_key, claude_model

_LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

_ANALYSIS_PROMPT = """당신은 주식 자동매매 시스템의 거래 내역을 분석하는 전문가입니다.

아래는 최근 {days}일간의 체결 내역 CSV 데이터입니다.
컬럼: 체결시간, 종목코드, 종목명, 매수/매도, 체결가, 수량, 전략, 잔여수량

---
{csv_data}
---

다음 항목을 한국어로 분석해 주세요:

1. **거래 요약** - 총 매수/매도 금액, 수익금, 수익률
2. **전략별 성과** - 각 전략(골든크로스, 손절매, 수동 등)의 손익
3. **종목별 성과** - 수익/손실이 큰 종목과 그 원인
4. **패턴 분석** - 반복되는 매매 패턴, 시간대별 특징
5. **개선 제안** - 수익률 향상을 위한 구체적인 제안 2~3가지

응답은 간결하고 실용적으로 작성하고, 텔레그램에서 보기 좋도록 이모지를 적절히 활용하세요."""


def _load_csv_data(days: int) -> tuple:
    """최근 N일의 CSV 데이터를 합쳐서 반환 (data_str, file_count, date_range)"""
    today = datetime.now()
    all_rows, loaded_dates = [], []

    for i in range(days):
        target = today - timedelta(days=i)
        path = _LOGS_DIR / f"{target.strftime('%Y%m%d')}.csv"
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        if len(rows) <= 1:
            continue
        loaded_dates.append(target.strftime("%Y-%m-%d"))
        all_rows.extend(rows if not all_rows else rows[1:])

    if not all_rows:
        return "", 0, ""

    csv_str = "\n".join(",".join(row) for row in all_rows)
    date_range = f"{loaded_dates[-1]} ~ {loaded_dates[0]}" if len(loaded_dates) > 1 else loaded_dates[0]
    return csv_str, len(loaded_dates), date_range


def analyze_trades(days: int) -> tuple:
    """최근 N일 체결 내역을 Claude로 분석. 성공: (결과, ''), 실패: ('', 오류메시지)."""
    if not claude_api_key or claude_api_key.startswith("YOUR_"):
        return "", "❌ Claude API 키가 설정되지 않았습니다.\nconfig/config.py의 claude_api_key를 확인하세요."

    csv_data, file_count, date_range = _load_csv_data(days)
    if file_count == 0:
        return "", f"❌ 최근 {days}일 내 체결 내역 파일이 없습니다."

    try:
        client = Anthropic(api_key=claude_api_key)
        prompt = _ANALYSIS_PROMPT.format(days=days, csv_data=csv_data)
        message = client.messages.create(model=claude_model, max_tokens=2000, messages=[{"role": "user", "content": prompt}])
        result = message.content[0].text.strip()
        header = f"🤖 AI 거래 분석 결과 ({date_range}, {file_count}일치)\n\n"
        return header + result, ""
    except Exception as e:
        return "", f"❌ Claude API 오류: {str(e)}"
