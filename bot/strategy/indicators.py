"""Các chỉ báo kỹ thuật dùng chung cho mọi chiến lược.

Giữ ở một nơi để chiến lược nào cũng gọi được, và dễ kiểm thử.
"""
from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Đường trung bình động hàm mũ (EMA).

    EMA cho trọng số lớn hơn vào các nến gần đây nên phản ứng nhanh hơn
    trung bình thường (SMA). `period` càng nhỏ thì càng nhạy.
    """
    return series.ewm(span=period, adjust=False).mean()
