"""
investor 명령 처리 - 투자자별 누적 순매수 차트 (IVU10430 매핑).

KB IVU10430은 acml_clsf(누적구분)/trd_clsf(매매구분) 파라미터로 이미 누적 순매수를
직접 내려주므로, 일별 데이터를 받아 직접 누적합(cumsum)할 필요가 없다.
"""

import os
import tempfile
from datetime import datetime, timedelta

from src.api.investor_chart import ivu10430


def handle_investor(args, session, send_photo_fn=None):
    """
    investor {종목코드} {개월수} 명령 처리

    사용법: /투자자 {종목코드} {개월수}  (예: /투자자 005930 3)
    """
    if not session.is_logged_in():
        return "❌ 로그인이 필요합니다.\nlogin real로 로그인하세요."

    if len(args) < 2:
        return "❌ 사용법: investor {종목코드} {개월수}\n예: investor 005930 3  (삼성전자 3개월)"

    stk_cd = args[0].strip()
    if not stk_cd.isdigit() or len(stk_cd) != 6:
        return "❌ 종목코드는 6자리 숫자여야 합니다.\n예: investor 005930 3"

    try:
        months = int(args[1])
        if not (1 <= months <= 36):
            return "❌ 개월수는 1~36 사이여야 합니다."
    except ValueError:
        return "❌ 개월수는 정수여야 합니다."

    end_dt = datetime.now()
    strt_dt = end_dt - timedelta(days=months * 31)

    result = ivu10430(
        excg_clsf="0",
        is_cd=stk_cd,
        strt_dt=strt_dt.strftime("%Y%m%d"),
        end_dt=end_dt.strftime("%Y%m%d"),
        amt_q_clsf="2",
        trd_clsf="1",
        acml_clsf="1",
        token=session.access_token,
        host_url=session.host_url,
    )
    if not result["success"]:
        error_msg = result["body"].get("error") or result["body"].get("dataHeader", {}).get("resultMessage", "알 수 없는 오류")
        return f"❌ 투자자별 매매 조회 실패\n\n오류: {error_msg}"

    rows = result["body"].get("dataBody", {}).get("out", []) or []
    if not rows:
        return f"❌ {stk_cd}의 투자자별 매매 데이터가 없습니다."

    rows = sorted(rows, key=lambda r: r.get("dt", ""))

    img_path, err = _generate_chart(rows, stk_cd, months)
    if err:
        return f"❌ 차트 생성 실패: {err}"

    caption = f"📊 {stk_cd} 투자자별 누적 순매수 ({months}개월, {len(rows)}일치)"

    if send_photo_fn:
        result = send_photo_fn(img_path, caption)
        try:
            os.unlink(img_path)
        except OSError:
            pass
        if result["success"]:
            return f"✅ {stk_cd} 투자자별 차트 전송 완료"
        err_msg = result["body"].get("error") or result["body"].get("description", "알 수 없는 오류")
        return f"❌ 차트 전송 실패: {err_msg}"

    return f"📊 차트 생성 완료\n{caption}\n경로: {img_path}"


def _parse_int(val):
    try:
        return int(str(val).replace("+", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _generate_chart(rows, stk_cd, months):
    """투자자별 누적 순매수 선 그래프 생성 → 임시 PNG 경로 반환. (file_path, error_msg) 반환."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        import matplotlib.dates as mdates

        korean_fonts = ["Malgun Gothic", "NanumGothic", "AppleGothic", "Gulim", "Dotum"]
        available = {f.name for f in fm.fontManager.ttflist}
        for fn in korean_fonts:
            if fn in available:
                plt.rcParams["font.family"] = fn
                break
        plt.rcParams["axes.unicode_minus"] = False

        dates = [datetime.strptime(r["dt"], "%Y%m%d") for r in rows]
        cum_indv = [_parse_int(r.get("indv", 0)) for r in rows]
        cum_fgnr = [_parse_int(r.get("fgnr", 0)) for r in rows]
        cum_ogn = [_parse_int(r.get("ogn", 0)) for r in rows]

        fig, ax = plt.subplots(figsize=(13, 6))
        ax.plot(dates, cum_indv, label="개인", color="#2196F3", linewidth=1.8)
        ax.plot(dates, cum_fgnr, label="외국인", color="#F44336", linewidth=1.8)
        ax.plot(dates, cum_ogn, label="기관계", color="#4CAF50", linewidth=1.8)
        ax.axhline(0, color="#888888", linewidth=0.8, linestyle="--", alpha=0.6)
        ax.fill_between(dates, cum_indv, 0, alpha=0.06, color="#2196F3")
        ax.fill_between(dates, cum_fgnr, 0, alpha=0.06, color="#F44336")
        ax.fill_between(dates, cum_ogn, 0, alpha=0.06, color="#4CAF50")

        ax.set_title(f"{stk_cd}  투자자별 누적 순매수  ({months}개월)", fontsize=14, pad=14)
        ax.set_xlabel("날짜", fontsize=10)
        ax.set_ylabel("누적 순매수 (주)", fontsize=10)
        ax.legend(loc="best", fontsize=11)
        ax.grid(True, alpha=0.25)

        if months <= 1:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        elif months <= 6:
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y/%m"))

        fig.autofmt_xdate(rotation=40)
        plt.tight_layout()

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix=f"investor_{stk_cd}_")
        tmp_name = tmp.name
        tmp.close()
        fig.savefig(tmp_name, dpi=130, bbox_inches="tight")
        plt.close(fig)

        return tmp_name, ""
    except Exception as e:
        return "", str(e)
