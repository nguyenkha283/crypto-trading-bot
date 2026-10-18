"""Giao diện chung cho 'lớp sàn'.

Mọi sàn (Binance, hoặc sàn khác sau này) đều cài đặt các hàm trong lớp này.
Nhờ vậy, phần còn lại của bot chỉ gọi qua giao diện chung — đổi sàn hay đổi
testnet/thật không ảnh hưởng tới logic chiến lược hay rủi ro.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseExchange(ABC):
    """Lớp trừu tượng định nghĩa những gì một 'sàn' phải làm được."""

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[list]:
        """Lấy dữ liệu nến (dữ liệu công khai, không cần khóa).

        Trả về danh sách nến, mỗi nến là:
        [thời_gian(ms), mở, cao, thấp, đóng, khối_lượng]
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_balance(self) -> dict:
        """Lấy số dư tài khoản (cần khóa API)."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """Mô tả ngắn sàn đang kết nối (để in ra cho dễ hiểu)."""
        raise NotImplementedError
