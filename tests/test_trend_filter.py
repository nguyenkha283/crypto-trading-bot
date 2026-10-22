"""Kiểm thử bộ lọc xu hướng của EMA Crossover — không cần mạng.

Chạy:  python -m tests.test_trend_filter
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bot.strategy.ema_crossover import EMACrossover, build_from_config
from bot.strategy.base import SIGNAL_BUY


def make_df(close: np.ndarray) -> pd.DataFrame:
    n = len(close)
    return pd.DataFrame({
        "time": np.arange(n), "open": close, "high": close + 1,
        "low": close - 1, "close": close, "volume": 1.0,
        "datetime": pd.date_range("2025-01-01", periods=n, freq="1h"),
    })


def run() -> None:
    # Chuỗi có cả đoạn giảm (whipsaw) rồi đoạn tăng mạnh:
    # mong đợi bộ lọc bỏ bớt lệnh mua ở đoạn giá còn dưới EMA dài.
    rng = np.random.default_rng(7)
    chop = 100 + np.sin(np.arange(250) / 5) * 4 + rng.normal(0, 1.5, 250)  # đi ngang/nhiễu
    up = np.linspace(100, 180, 150)                                        # tăng rõ
    close = np.concatenate([chop, up])
    df = make_df(close)

    no_filter = EMACrossover(9, 21, trend_ema=None).generate_signals(df)
    with_filter = EMACrossover(9, 21, trend_ema=200).generate_signals(df)

    n_buy_no = int((no_filter["signal"] == SIGNAL_BUY).sum())
    n_buy_yes = int((with_filter["signal"] == SIGNAL_BUY).sum())
    print(f"Số tín hiệu MUA — không lọc: {n_buy_no} | có lọc: {n_buy_yes}")

    assert "ema_trend" in with_filter.columns, "Có lọc phải tính cột ema_trend"
    assert n_buy_yes <= n_buy_no, "Bộ lọc không được làm TĂNG số lệnh mua"
    assert n_buy_yes < n_buy_no, "Trong dữ liệu whipsaw, bộ lọc phải CẮT bớt lệnh mua"

    # Mọi lệnh mua khi có lọc đều phải nằm trên EMA dài.
    buys = with_filter[with_filter["signal"] == SIGNAL_BUY]
    assert (buys["close"] > buys["ema_trend"]).all(), "Lệnh mua có lọc phải ở trên EMA dài"
    print("✓ Mọi lệnh mua (có lọc) đều nằm trên EMA xu hướng")

    # Factory từ config: bật/tắt đúng
    s_on = build_from_config({"ema_fast": 9, "ema_slow": 21, "trend_filter": True, "trend_ema": 200})
    s_off = build_from_config({"ema_fast": 9, "ema_slow": 21, "trend_filter": False, "trend_ema": 200})
    assert s_on.trend_ema == 200 and s_off.trend_ema is None
    print("✓ build_from_config bật/tắt bộ lọc đúng theo config")

    print("\n✓ TẤT CẢ KIỂM THỬ BỘ LỌC XU HƯỚNG ĐỀU QUA")


if __name__ == "__main__":
    run()
