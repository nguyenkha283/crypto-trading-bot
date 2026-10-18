"""Cài đặt lớp sàn cho Binance, dùng thư viện CCXT.

Chuyển giữa Testnet và sàn thật chỉ bằng cờ `testnet` trong config:
- testnet=True  -> gọi set_sandbox_mode(True), tự trỏ tới testnet.binance.vision
- testnet=False -> dùng sàn Binance thật
"""
from __future__ import annotations

import ccxt

from .base import BaseExchange


class BinanceExchange(BaseExchange):
    def __init__(self, config: dict):
        ex_cfg = config.get("exchange", {})
        secrets = config.get("secrets", {})
        self.testnet: bool = ex_cfg.get("testnet", True)

        # Khởi tạo client CCXT cho Binance Spot.
        # enableRateLimit=True: CCXT tự giãn cách để không bị sàn chặn (rate limit).
        self.client = ccxt.binance(
            {
                "apiKey": secrets.get("binance_api_key", ""),
                "secret": secrets.get("binance_api_secret", ""),
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )

        # Bật chế độ testnet nếu cần — CCXT tự đổi sang các endpoint của testnet.
        if self.testnet:
            self.client.set_sandbox_mode(True)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> list[list]:
        """Lấy nến (công khai, không cần khóa)."""
        return self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_balance(self) -> dict:
        """Lấy số dư (cần khóa API)."""
        return self.client.fetch_balance()

    def describe(self) -> str:
        return "Binance Testnet" if self.testnet else "Binance (thật)"


def create_exchange(config: dict) -> BaseExchange:
    """Nhà máy tạo sàn: đọc config -> trả về đối tượng sàn phù hợp.

    Hiện chỉ có Binance; sau này thêm sàn khác thì mở rộng ở đây.
    """
    name = config.get("exchange", {}).get("name", "binance").lower()
    if name == "binance":
        return BinanceExchange(config)
    raise ValueError(f"Chưa hỗ trợ sàn: {name}")
