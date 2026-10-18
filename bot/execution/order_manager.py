"""Thực thi lệnh — có 2 chế độ an toàn:

  - 'paper'  : MÔ PHỎNG, không gọi sàn. Khớp ngay ở giá truyền vào. Dùng để xem bot
               cư xử thế nào trước khi đụng tới lệnh thật.
  - 'testnet': Đặt lệnh THẬT trên Binance Testnet (tiền ảo) qua CCXT.

Trả về (giá_khớp, khối_lượng_thực). Luôn làm tròn khối lượng theo chuẩn sàn và kiểm
giá trị lệnh tối thiểu để tránh bị từ chối.
"""
from __future__ import annotations

import logging

from bot.exchange.base import BaseExchange

log = logging.getLogger("bot")


class OrderManager:
    def __init__(self, exchange: BaseExchange, mode: str = "paper"):
        self.exchange = exchange
        self.mode = mode.lower()

    def _prepare_amount(self, pair: str, amount: float, price: float) -> float | None:
        """Làm tròn khối lượng và kiểm giá trị lệnh tối thiểu. Trả None nếu quá nhỏ."""
        try:
            amount = self.exchange.round_amount(pair, amount)
            min_cost = self.exchange.min_cost(pair)
        except Exception:  # noqa: BLE001 - chế độ paper có thể chưa nạp markets
            min_cost = 0.0
        if amount <= 0:
            return None
        if min_cost and amount * price < min_cost:
            log.warning("Lệnh %s quá nhỏ (%.2f < tối thiểu %.2f USDT) -> bỏ qua",
                        pair, amount * price, min_cost)
            return None
        return amount

    def buy(self, pair: str, amount: float, ref_price: float) -> tuple[float, float] | None:
        """Mua. ref_price là giá tham chiếu (để mô phỏng / kiểm tối thiểu)."""
        amount = self._prepare_amount(pair, amount, ref_price)
        if amount is None:
            return None
        if self.mode == "paper":
            log.info("[PAPER] MUA %s: %.6f @ ~%.2f", pair, amount, ref_price)
            return ref_price, amount
        order = self.exchange.create_market_order(pair, "buy", amount)
        fill = float(order.get("average") or order.get("price") or ref_price)
        filled = float(order.get("filled") or amount)
        log.info("[TESTNET] MUA %s: %.6f @ %.2f", pair, filled, fill)
        return fill, filled

    def sell(self, pair: str, amount: float, ref_price: float) -> tuple[float, float] | None:
        """Bán (đóng lệnh)."""
        if amount <= 0:
            return None
        if self.mode == "paper":
            log.info("[PAPER] BÁN %s: %.6f @ ~%.2f", pair, amount, ref_price)
            return ref_price, amount
        order = self.exchange.create_market_order(pair, "sell", amount)
        fill = float(order.get("average") or order.get("price") or ref_price)
        filled = float(order.get("filled") or amount)
        log.info("[TESTNET] BÁN %s: %.6f @ %.2f", pair, filled, fill)
        return fill, filled
