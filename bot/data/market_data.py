"""Lớp dữ liệu thị trường: lấy nến từ sàn và trả về dưới dạng bảng (DataFrame).

Chiến lược và backtest sẽ làm việc trên DataFrame này cho tiện tính chỉ báo.
"""
from __future__ import annotations

import pandas as pd

from bot.exchange.base import BaseExchange

# Tên cột chuẩn của một bảng nến (OHLCV)
OHLCV_COLUMNS = ["time", "open", "high", "low", "close", "volume"]


def get_candles(
    exchange: BaseExchange,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 200,
) -> pd.DataFrame:
    """Lấy nến và trả về DataFrame với cột thời gian đã đổi sang dạng ngày giờ.

    Cột 'time' là mốc thời gian gốc (mili-giây); thêm cột 'datetime' cho dễ đọc.
    """
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=OHLCV_COLUMNS)
    df["datetime"] = pd.to_datetime(df["time"], unit="ms")
    return df
