"""Dashboard backtest (Streamlit) — phòng lab để nghịch chiến lược.

Chạy (từ thư mục gốc dự án):
    streamlit run dashboard/app.py

Dùng lại đúng backtester + strategy + risk đã có — không viết lại logic giao dịch.
Đây cũng là nền để sau mở rộng thành dashboard theo dõi bot chạy thật (bước 4).
"""
from __future__ import annotations

import os
import sys

# Cho phép chạy bằng `streamlit run dashboard/app.py`: thêm thư mục gốc dự án vào
# đường dẫn tìm module, để import được 'bot' và 'backtest' dù chạy từ đâu.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go

from bot.config_loader import load_config
from bot.data.market_data import get_candles
from bot.exchange.binance_exchange import create_exchange
from bot.risk.risk_manager import RiskManager
from bot.strategy.ema_crossover import EMACrossover
from backtest.backtester import run_backtest

# Màu dùng chung
C_UP, C_DOWN = "#1D9E75", "#D85A30"      # xanh lá / cam
C_FAST, C_SLOW = "#378ADD", "#BA7517"    # xanh dương / vàng
C_EQUITY = "#534AB7"                      # tím

REASON_VI = {"TP": "Chạm chốt lời", "SL": "Chạm cắt lỗ",
             "cross": "Cắt xuống", "end": "Hết dữ liệu"}


# ------------------------- Hàm dựng biểu đồ (thuần, dễ kiểm thử) -------------------------

def build_price_fig(data: pd.DataFrame, trades, fast_n: int, slow_n: int) -> go.Figure:
    """Biểu đồ nến + 2 đường EMA + đánh dấu điểm vào/ra lệnh."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data["datetime"], open=data["open"], high=data["high"],
        low=data["low"], close=data["close"], name="Giá",
        increasing_line_color=C_UP, decreasing_line_color=C_DOWN,
    ))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["ema_fast"],
                             name=f"EMA {fast_n}", line=dict(color=C_FAST, width=1)))
    fig.add_trace(go.Scatter(x=data["datetime"], y=data["ema_slow"],
                             name=f"EMA {slow_n}", line=dict(color=C_SLOW, width=1)))

    if trades:
        fig.add_trace(go.Scatter(
            x=[t.entry_time for t in trades], y=[t.entry_price for t in trades],
            mode="markers", name="Vào lệnh",
            marker=dict(symbol="triangle-up", size=11, color="#185FA5"),
        ))
        wins = [t for t in trades if t.is_win]
        losses = [t for t in trades if not t.is_win]
        if wins:
            fig.add_trace(go.Scatter(
                x=[t.exit_time for t in wins], y=[t.exit_price for t in wins],
                mode="markers", name="Thoát (lời)",
                marker=dict(symbol="triangle-down", size=11, color=C_UP),
            ))
        if losses:
            fig.add_trace(go.Scatter(
                x=[t.exit_time for t in losses], y=[t.exit_price for t in losses],
                mode="markers", name="Thoát (lỗ)",
                marker=dict(symbol="triangle-down", size=11, color=C_DOWN),
            ))

    fig.update_layout(
        height=460, margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.0),
    )
    return fig


def build_equity_fig(equity: list[float]) -> go.Figure:
    """Biểu đồ đường vốn theo số lệnh đã đóng."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(equity))), y=equity,
        mode="lines+markers", name="Vốn", line=dict(color=C_EQUITY),
    ))
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="Số lệnh đã đóng", yaxis_title="Vốn (USDT)",
    )
    return fig


def trades_to_df(trades) -> pd.DataFrame:
    """Chuyển danh sách lệnh thành bảng dễ đọc."""
    rows = []
    for i, t in enumerate(trades, 1):
        rows.append({
            "#": i,
            "Vào lúc": t.entry_time,
            "Giá vào": round(t.entry_price, 2),
            "Ra lúc": t.exit_time,
            "Giá ra": round(t.exit_price, 2),
            "Lý do thoát": REASON_VI.get(t.reason, t.reason),
            "Lãi/Lỗ (USDT)": round(t.pnl, 2),
            "Kết quả": "Thắng" if t.is_win else "Thua",
        })
    return pd.DataFrame(rows)


# ------------------------------------- Giao diện -------------------------------------

def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Phòng Lab Backtest", page_icon="📈", layout="wide")
    st.title("📈 Phòng Lab Backtest — nghịch chiến lược")
    st.caption("Đổi tham số bên trái rồi xem kết quả đổi theo. Lấy nến không cần khóa API.")

    config = load_config()

    @st.cache_data(ttl=300, show_spinner=False)
    def load_candles(pair: str, timeframe: str, limit: int) -> pd.DataFrame:
        cfg = load_config()
        cfg["exchange"]["testnet"] = True
        ex = create_exchange(cfg)
        return get_candles(ex, pair, timeframe=timeframe, limit=limit)

    # --- Thanh tham số ---
    sb = st.sidebar
    sb.header("Tham số")
    pair = sb.selectbox("Cặp coin", config["market"]["pairs"])
    timeframe = sb.selectbox("Khung thời gian", ["15m", "1h", "4h", "1d"], index=1)
    candles = sb.slider("Số nến lịch sử", 200, 1000, int(config["backtest"]["candles"]), step=100)

    sb.subheader("Chiến lược EMA")
    ema_fast = sb.slider("EMA nhanh", 3, 50, int(config["strategy"]["ema_fast"]))
    ema_slow = sb.slider("EMA chậm", 5, 200, int(config["strategy"]["ema_slow"]))

    sb.subheader("Rủi ro")
    sl_pct = sb.slider("Cắt lỗ (%)", 0.5, 10.0, float(config["risk"]["stop_loss_pct"]) * 100, step=0.5) / 100
    tp_rr = sb.slider("R:R chốt lời", 1.0, 5.0, float(config["risk"]["take_profit_rr"]), step=0.5)
    capital = sb.number_input("Vốn ban đầu (USDT)", 100, 1_000_000,
                              int(config["backtest"]["initial_capital"]), step=100)

    if ema_fast >= ema_slow:
        st.error("EMA nhanh phải NHỎ HƠN EMA chậm. Chỉnh lại bên trái.")
        st.stop()

    min_rr = float(config["risk"].get("min_rr", 1.5))
    if tp_rr < min_rr:
        st.warning(f"R:R = {tp_rr} nhỏ hơn mức tối thiểu {min_rr} trong cấu hình → "
                   "bot sẽ TỪ CHỐI mọi lệnh (sẽ không có giao dịch nào).")

    # --- Lấy dữ liệu ---
    try:
        with st.spinner("Đang lấy nến..."):
            df = load_candles(pair, timeframe, candles)
    except Exception as e:  # noqa: BLE001
        st.error(f"Không lấy được nến: {e}")
        st.info("Kiểm tra mạng rồi thử lại (testnet đôi khi bận).")
        st.stop()

    # --- Chạy backtest (dùng lại code đã có) ---
    strat = EMACrossover(ema_fast=ema_fast, ema_slow=ema_slow)
    risk_cfg = dict(config["risk"])
    risk_cfg["stop_loss_pct"] = sl_pct
    risk_cfg["take_profit_rr"] = tp_rr
    risk = RiskManager(risk_cfg)
    result = run_backtest(df, strat, risk, initial_capital=capital,
                          fee_rate=float(config["risk"].get("fee_rate", 0.001)))
    signals = strat.generate_signals(df)

    # --- Các ô chỉ số ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Lợi nhuận", f"{result.total_return_pct:+.2f}%")
    c2.metric("Số lệnh", result.num_trades)
    c3.metric("Tỷ lệ thắng", f"{result.win_rate:.1f}%")
    pf = result.profit_factor
    c4.metric("Profit factor", "∞" if pf == float("inf") else f"{pf:.2f}")
    c5.metric("Sụt vốn tối đa", f"{result.max_drawdown_pct:.2f}%")
    c6.metric("Chuỗi thua dài", result.longest_losing_streak)

    # --- Biểu đồ ---
    st.subheader(f"Giá {pair} · EMA {ema_fast}/{ema_slow} · điểm vào/ra lệnh")
    st.plotly_chart(build_price_fig(signals, result.trades, ema_fast, ema_slow),
                    use_container_width=True)

    st.subheader("Đường vốn (tài khoản thay đổi theo từng lệnh)")
    st.plotly_chart(build_equity_fig(result.equity_curve), use_container_width=True)

    # --- Bảng lệnh ---
    st.subheader("Danh sách lệnh")
    if result.trades:
        st.dataframe(trades_to_df(result.trades), use_container_width=True, hide_index=True)
    else:
        st.info("Không có lệnh nào trong giai đoạn này (không có giao cắt phù hợp, "
                "hoặc R:R thấp hơn mức tối thiểu).")

    # --- Ghi chú học tập ---
    with st.expander("💡 Đọc hiểu các con số (bấm để mở)"):
        st.markdown(
            "- **Tỷ lệ thắng cao chưa chắc tốt**: thua một lệnh to vẫn có thể âm tổng thể.\n"
            "- **Profit factor** = tổng lời / tổng lỗ. Lớn hơn 1 là có lãi; khoảng 1.5+ là ổn.\n"
            "- **Sụt vốn tối đa** cho biết lúc tệ nhất tài khoản mất bao nhiêu từ đỉnh.\n"
            "- Chiến lược theo xu hướng (EMA) thường **lỗ khi thị trường đi ngang**, "
            "**lời khi có xu hướng rõ** → kết quả phụ thuộc giai đoạn dữ liệu.\n"
            "- Hãy thử đổi khung thời gian (1h ↔ 4h) và cặp coin để thấy chiến lược "
            "hợp điều kiện nào."
        )


if __name__ == "__main__":
    main()
