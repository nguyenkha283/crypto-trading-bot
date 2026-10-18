"""Chiến lược EMA Crossover (giao cắt hai đường trung bình).

Ý tưởng:
- EMA nhanh cắt LÊN trên EMA chậm  -> xu hướng tăng bắt đầu -> tín hiệu MUA.
- EMA nhanh cắt XUỐNG dưới EMA chậm -> xu hướng tăng kết thúc -> tín hiệu THOÁT.

Đây là chiến lược theo xu hướng, đơn giản, dễ hiểu bản chất — hợp để học đầu tiên.
Nhược điểm cần nhớ: khi thị trường đi ngang, hai đường cắt qua lại liên tục gây
nhiều lệnh thua nhỏ ("whipsaw").
"""
from __future__ import annotations

import pandas as pd

from .base import BaseStrategy, SIGNAL_BUY, SIGNAL_EXIT, SIGNAL_HOLD
from .indicators import ema


class EMACrossover(BaseStrategy):
    name = "ema_crossover"

    def __init__(self, ema_fast: int = 9, ema_slow: int = 21):
        if ema_fast >= ema_slow:
            raise ValueError("ema_fast phải nhỏ hơn ema_slow")
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ema(out["close"], self.ema_fast)
        out["ema_slow"] = ema(out["close"], self.ema_slow)

        # Chênh lệch hai đường; đổi dấu nghĩa là vừa có giao cắt.
        diff = out["ema_fast"] - out["ema_slow"]
        prev_diff = diff.shift(1)

        signal = pd.Series(SIGNAL_HOLD, index=out.index)
        # Cắt lên: trước đó <=0, bây giờ >0
        signal[(prev_diff <= 0) & (diff > 0)] = SIGNAL_BUY
        # Cắt xuống: trước đó >=0, bây giờ <0
        signal[(prev_diff >= 0) & (diff < 0)] = SIGNAL_EXIT

        # Vùng chưa đủ dữ liệu để tính EMA chậm thì không ra tín hiệu.
        signal[out["ema_slow"].isna()] = SIGNAL_HOLD
        out["signal"] = signal
        return out
