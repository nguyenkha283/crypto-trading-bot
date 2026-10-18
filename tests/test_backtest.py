"""Kiểm thử nhanh chuỗi: chiến lược -> rủi ro -> backtester, bằng dữ liệu mẫu.

Không cần mạng. Chạy:  python -m tests.test_backtest
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bot.risk.risk_manager import RiskManager
from bot.strategy.ema_crossover import EMACrossover
from backtest.backtester import run_backtest


def make_fake_candles(n: int = 300) -> pd.DataFrame:
    """Tạo chuỗi giá giả: tăng rồi giảm rồi tăng, để chắc chắn có giao cắt EMA."""
    t = np.arange(n)
    # Ghép vài đoạn xu hướng + dao động nhỏ cho giống thật.
    trend = np.concatenate([
        np.linspace(100, 160, n // 3),
        np.linspace(160, 110, n // 3),
        np.linspace(110, 180, n - 2 * (n // 3)),
    ])
    noise = np.sin(t / 5) * 2
    close = trend + noise
    high = close + 1.5
    low = close - 1.5
    times = pd.date_range("2025-01-01", periods=n, freq="1h")
    return pd.DataFrame({
        "time": (times.astype("int64") // 10**6),
        "open": close,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1.0,
        "datetime": times,
    })


def run() -> None:
    df = make_fake_candles(300)

    strat = EMACrossover(ema_fast=9, ema_slow=21)
    signals = strat.generate_signals(df)
    n_buy = int((signals["signal"] == 1).sum())
    n_exit = int((signals["signal"] == -1).sum())
    print(f"Tín hiệu: MUA={n_buy}, THOÁT={n_exit}")
    assert n_buy > 0, "Phải có ít nhất một tín hiệu mua"

    risk = RiskManager({
        "risk_per_trade": 0.01, "stop_loss_pct": 0.02,
        "take_profit_rr": 2.0, "min_rr": 1.5,
    })
    result = run_backtest(df, strat, risk, initial_capital=10000, fee_rate=0.001)

    print(f"Số lệnh      : {result.num_trades}")
    print(f"Thắng/Thua   : {result.wins}/{result.losses}")
    print(f"Tỷ lệ thắng  : {result.win_rate:.1f}%")
    print(f"Lợi nhuận    : {result.total_return_pct:+.2f}%")
    print(f"Sụt vốn tối đa: {result.max_drawdown_pct:.2f}%")
    print(f"Chuỗi thua dài: {result.longest_losing_streak}")

    assert result.num_trades > 0, "Phải có ít nhất một lệnh"
    assert len(result.equity_curve) == result.num_trades + 1
    assert all(t.reason in {"SL", "TP", "cross", "end"} for t in result.trades)
    print("\n✓ TẤT CẢ KIỂM THỬ ĐỀU QUA")


if __name__ == "__main__":
    run()
