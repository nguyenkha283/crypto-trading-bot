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
                "options": {
                    "defaultType": "spot",
                    # Cho phép lệnh mua thị trường tính theo khối lượng (base), không bắt kèm giá.
                    "createMarketBuyOrderRequiresPrice": False,
                },
            }
        )

        # Bật chế độ testnet nếu cần — CCXT tự đổi sang các endpoint của testnet.
        if self.testnet:
            self.client.set_sandbox_mode(True)

        self._markets_loaded = False

    def _ensure_markets(self) -> None:
        if not self._markets_loaded:
            self.client.load_markets()
            self._markets_loaded = True

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> list[list]:
        """Lấy nến (công khai, không cần khóa)."""
        return self.client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_balance(self) -> dict:
        """Lấy số dư (cần khóa API)."""
        return self.client.fetch_balance()

    def fetch_last_price(self, symbol: str) -> float:
        """Giá khớp gần nhất (công khai)."""
        ticker = self.client.fetch_ticker(symbol)
        return float(ticker["last"])

    def create_market_order(self, symbol: str, side: str, amount: float) -> dict:
        """Đặt lệnh thị trường thật trên sàn (cần khóa API)."""
        self._ensure_markets()
        return self.client.create_order(symbol, "market", side, amount)

    def round_amount(self, symbol: str, amount: float) -> float:
        """Làm tròn khối lượng theo độ chính xác sàn yêu cầu."""
        self._ensure_markets()
        return float(self.client.amount_to_precision(symbol, amount))

    def min_cost(self, symbol: str) -> float:
        """Giá trị lệnh tối thiểu (minNotional)."""
        self._ensure_markets()
        market = self.client.market(symbol)
        cost = (market.get("limits", {}).get("cost", {}) or {}).get("min")
        return float(cost) if cost else 0.0

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
