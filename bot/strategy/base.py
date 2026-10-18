"""Giao diện chung cho mọi chiến lược.

Quan trọng: chiến lược CHỈ ra tín hiệu (MUA / BÁN / ĐỨNG NGOÀI) bằng luật rõ ràng.
Cùng một đối tượng chiến lược được dùng cho CẢ backtest LẪN chạy thật — nhờ vậy
kết quả backtest đúng với hành vi khi chạy thật.

Quy ước tín hiệu trong cột 'signal':
   1  = tín hiệu MỞ lệnh mua
  -1  = tín hiệu ĐÓNG lệnh (thoát)
   0  = không làm gì
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

SIGNAL_BUY = 1
SIGNAL_EXIT = -1
SIGNAL_HOLD = 0


class BaseStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nhận bảng nến, trả về bảng đó kèm cột chỉ báo và cột 'signal'."""
        raise NotImplementedError

    def latest_signal(self, df: pd.DataFrame) -> int:
        """Lấy tín hiệu ở nến mới nhất (dùng khi chạy thật)."""
        out = self.generate_signals(df)
        return int(out["signal"].iloc[-1])
