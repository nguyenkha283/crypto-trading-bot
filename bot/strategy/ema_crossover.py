"""Chiến lược EMA Crossover (giao cắt hai đường trung bình).

Ý tưởng:
- EMA nhanh cắt LÊN trên EMA chậm  -> xu hướng tăng bắt đầu -> tín hiệu MUA.
- EMA nhanh cắt XUỐNG dưới EMA chậm -> xu hướng tăng kết thúc -> tín hiệu THOÁT.

Đây là chiến lược theo xu hướng, đơn giản, dễ hiểu bản chất — hợp để học đầu tiên.
Nhược điểm cần nhớ: khi thị trường đi ngang, hai đường cắt qua lại liên tục gây
nhiều lệnh thua nhỏ ("whipsaw").

BỘ LỌC XU HƯỚNG (tùy chọn): chỉ cho phép MUA khi giá đang nằm TRÊN một đường EMA dài
(ví dụ EMA 200). Mục đích: bỏ qua các cú cắt lên xảy ra lúc thị trường đi ngang/giảm —
đây là phần lớn tín hiệu giả gây lỗ vặt. Bật/tắt qua tham số `trend_ema`.
"""
from __future__ import annotations

import pandas as pd

from .base import BaseStrategy, SIGNAL_BUY, SIGNAL_EXIT, SIGNAL_HOLD
from .indicators import ema


class EMACrossover(BaseStrategy):
    name = "ema_crossover"

    def __init__(self, ema_fast: int = 9, ema_slow: int = 21, trend_ema: int | None = None):
        """trend_ema: chu kỳ EMA dùng làm bộ lọc xu hướng. None = tắt bộ lọc."""
        if ema_fast >= ema_slow:
            raise ValueError("ema_fast phải nhỏ hơn ema_slow")
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.trend_ema = trend_ema

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ema(out["close"], self.ema_fast)
        out["ema_slow"] = ema(out["close"], self.ema_slow)

        # Chênh lệch hai đường; đổi dấu nghĩa là vừa có giao cắt.
        diff = out["ema_fast"] - out["ema_slow"]
        prev_diff = diff.shift(1)

        signal = pd.Series(SIGNAL_HOLD, index=out.index)
        buy_cross = (prev_diff <= 0) & (diff > 0)
        exit_cross = (prev_diff >= 0) & (diff < 0)

        # Bộ lọc xu hướng: chỉ giữ tín hiệu MUA khi giá trên EMA dài.
        if self.trend_ema:
            out["ema_trend"] = ema(out["close"], self.trend_ema)
            uptrend = out["close"] > out["ema_trend"]
            buy_cross = buy_cross & uptrend

        signal[buy_cross] = SIGNAL_BUY
        signal[exit_cross] = SIGNAL_EXIT

        # Vùng chưa đủ dữ liệu để tính EMA chậm thì không ra tín hiệu.
        signal[out["ema_slow"].isna()] = SIGNAL_HOLD
        out["signal"] = signal
        return out


def build_from_config(strategy_cfg: dict) -> "EMACrossover":
    """Tạo chiến lược EMA từ phần 'strategy' trong config (gồm cả bộ lọc xu hướng)."""
    trend_ema = strategy_cfg.get("trend_ema") if strategy_cfg.get("trend_filter") else None
    return EMACrossover(
        ema_fast=strategy_cfg["ema_fast"],
        ema_slow=strategy_cfg["ema_slow"],
        trend_ema=trend_ema,
    )
