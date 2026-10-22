"""Vòng lặp chính của bot — nơi mọi thành phần ghép lại.

Mỗi chu kỳ (mặc định 60 giây):
  0. Kiểm CỜ DỪNG KHẨN -> nếu bật: đóng mọi lệnh rồi dừng.
  1. Tính vốn hiện tại (equity) = vốn thực + lãi/lỗ tạm của các lệnh đang mở.
  2. Với mỗi cặp coin:
     - Nếu đang giữ lệnh: kiểm SL -> TP -> tín hiệu thoát; chạm thì ĐÓNG.
     - Nếu rảnh: kiểm CẦU DAO NGẮT + số vị thế; có tín hiệu MUA thì MỞ lệnh.
  3. Ghi 'còn sống' (heartbeat) + ngủ tới chu kỳ sau.

Trạng thái (vị thế, vốn, chuỗi thua...) lưu vào DB -> khởi động lại không mất.
Chế độ 'paper' mô phỏng, 'testnet' đặt lệnh thật trên testnet (chọn trong config).
"""
from __future__ import annotations

import time
from datetime import datetime

from bot.config_loader import load_config
from bot.data.market_data import get_candles
from bot.exchange.binance_exchange import create_exchange
from bot.execution.order_manager import OrderManager
from bot.execution.portfolio import Portfolio, Position
from bot.explain.explainer import Explainer
from bot.risk.circuit_breakers import CircuitBreakers
from bot.risk.risk_manager import RiskManager
from bot.storage.sqlite_store import create_store
from bot.strategy.base import SIGNAL_BUY, SIGNAL_EXIT
from bot.strategy.ema_crossover import build_from_config as build_strategy
from bot.utils.logging_setup import setup_logging


class Bot:
    def __init__(self, config: dict):
        self.cfg = config
        self.log = setup_logging(config.get("logging", {}))

        self.exchange = create_exchange(config)
        self.store = create_store(config)
        self.strategy = build_strategy(config["strategy"])
        self.risk = RiskManager(config["risk"])
        self.order = OrderManager(self.exchange, mode=config["execution"]["mode"])
        self.portfolio = Portfolio()

        self.pairs = config["market"]["pairs"]
        self.timeframe = config["market"]["timeframe"]
        self.candles_limit = config["market"].get("candles_limit", 200)
        self.fee_rate = config["risk"].get("fee_rate", 0.001)
        self.max_total = config["risk"].get("max_total_positions", 3)

        # Khôi phục vốn & vị thế từ DB (nếu đây là lần khởi động lại).
        init_cap = float(config["run"].get("initial_capital", 10000))
        if self.store.get_meta("capital") is None:
            self.store.set_meta("capital", init_cap)
        self.portfolio.load_from_store(self.store)

        self.breakers = CircuitBreakers(config["risk"], self.store, self._capital())
        self.explainer = Explainer(self.store, config)
        self._halt_logged = False

        self.log.info("Bot khởi động | sàn=%s | chế độ=%s | vốn=%.2f | vị thế đang giữ=%d",
                      self.exchange.describe(), self.order.mode, self._capital(),
                      self.portfolio.count())

    # ------------------- tiện ích vốn/trạng thái -------------------
    def _capital(self) -> float:
        return float(self.store.get_meta("capital", "0"))

    def _set_capital(self, value: float) -> None:
        self.store.set_meta("capital", value)

    def _equity(self) -> float:
        """Vốn thực + lãi/lỗ tạm tính của các lệnh đang mở."""
        eq = self._capital()
        for pair, pos in self.portfolio.positions.items():
            try:
                eq += pos.unrealized_pnl(self.exchange.fetch_last_price(pair))
            except Exception:  # noqa: BLE001
                pass
        return eq

    def _kill_switch_on(self) -> bool:
        return self.store.get_meta("kill_switch", "0") == "1"

    # ------------------- đóng / mở lệnh -------------------
    def _close_position(self, pos: Position, price: float, reason: str) -> None:
        result = self.order.sell(pos.pair, pos.quantity, price)
        if result is None:
            self.log.error("Không bán được %s để đóng lệnh", pos.pair)
            return
        exit_price, qty = result
        fees = (pos.entry_price * qty + exit_price * qty) * self.fee_rate
        pnl = (exit_price - pos.entry_price) * qty - fees
        new_cap = self._capital() + pnl
        self._set_capital(new_cap)
        self.portfolio.close(pos.pair, self.store)
        self.store.record_trade({
            "pair": pos.pair, "entry_price": pos.entry_price, "exit_price": exit_price,
            "quantity": qty, "pnl": pnl, "reason": reason, "is_win": 1 if pnl > 0 else 0,
            "entry_time": pos.entry_time, "exit_time": datetime.now().isoformat(timespec="seconds"),
        })
        self.breakers.on_trade_closed(pnl > 0, new_cap)
        self.log.info("ĐÓNG %s (%s) | lãi/lỗ %.2f USDT | vốn mới %.2f",
                      pos.pair, reason, pnl, new_cap)
        self.explainer.enqueue("close", pos.pair, {
            "pair": pos.pair, "entry_price": pos.entry_price, "exit_price": exit_price,
            "pnl": round(pnl, 2), "reason": reason, "had_plan": True,
            "ema_fast": self.cfg["strategy"]["ema_fast"], "ema_slow": self.cfg["strategy"]["ema_slow"],
        })

    def _open_position(self, pair: str, price: float) -> None:
        plan = self.risk.plan_long(entry_price=price, capital=self._capital())
        if not plan.ok:
            self.log.info("Bỏ qua %s: %s", pair, plan.reason)
            return
        result = self.order.buy(pair, plan.quantity, price)
        if result is None:
            return
        fill, qty = result
        # Tính lại SL/TP theo giá khớp thực tế.
        plan2 = self.risk.plan_long(entry_price=fill, capital=self._capital())
        pos = Position(
            pair=pair, entry_price=fill, quantity=qty,
            stop_loss=plan2.stop_loss, take_profit=plan2.take_profit,
            entry_time=datetime.now().isoformat(timespec="seconds"),
        )
        self.portfolio.open(pos, self.store)
        self.log.info("MỞ %s | vào %.2f | SL %.2f | TP %.2f | R:R %.1f",
                      pair, fill, pos.stop_loss, pos.take_profit, plan2.rr)
        self.explainer.enqueue("open", pair, {
            "pair": pair, "entry_price": fill, "stop_loss": pos.stop_loss,
            "take_profit": pos.take_profit, "rr": plan2.rr,
            "risk_pct": self.cfg["risk"]["risk_per_trade"] * 100,
            "ema_fast": self.cfg["strategy"]["ema_fast"], "ema_slow": self.cfg["strategy"]["ema_slow"],
        })

    # ------------------- một chu kỳ -------------------
    def run_cycle(self) -> None:
        # 0. Cờ dừng khẩn
        if self._kill_switch_on():
            self.log.warning("CỜ DỪNG KHẨN đang bật -> đóng mọi lệnh và dừng.")
            for pos in list(self.portfolio.positions.values()):
                try:
                    price = self.exchange.fetch_last_price(pos.pair)
                    self._close_position(pos, price, "killswitch")
                except Exception as e:  # noqa: BLE001
                    self.log.error("Lỗi đóng %s khi dừng khẩn: %s", pos.pair, e)
            raise KeyboardInterrupt("Dừng theo cờ dừng khẩn")

        equity = self._equity()
        allowed, why = self.breakers.check(equity)
        if not allowed:
            if not self._halt_logged:
                self.log.warning("CẦU DAO NGẮT: %s (chỉ quản lý lệnh đang mở, không vào lệnh mới)", why)
                self._halt_logged = True
        else:
            self._halt_logged = False

        for pair in self.pairs:
            try:
                df = get_candles(self.exchange, pair, self.timeframe, self.candles_limit)
                closed = df.iloc[:-1]  # bỏ nến chưa đóng
                price = self.exchange.fetch_last_price(pair)

                if self.portfolio.has_position(pair):
                    pos = self.portfolio.get(pair)
                    if price <= pos.stop_loss:
                        self._close_position(pos, pos.stop_loss, "SL")
                    elif price >= pos.take_profit:
                        self._close_position(pos, pos.take_profit, "TP")
                    elif self.strategy.latest_signal(closed) == SIGNAL_EXIT:
                        self._close_position(pos, price, "cross")
                else:
                    if allowed and self.portfolio.count() < self.max_total:
                        if self.strategy.latest_signal(closed) == SIGNAL_BUY:
                            self._open_position(pair, price)
            except Exception as e:  # noqa: BLE001 - lỗi 1 cặp không được làm chết bot
                self.log.error("Lỗi xử lý %s: %s", pair, e)

        # Heartbeat
        self.store.set_meta("last_heartbeat", datetime.now().isoformat(timespec="seconds"))

    def run_forever(self) -> None:
        interval = int(self.cfg["run"].get("poll_interval_seconds", 60))
        self.log.info("Bắt đầu vòng lặp, mỗi %d giây một chu kỳ. Nhấn Ctrl+C để dừng.", interval)
        self.explainer.start()
        try:
            while True:
                try:
                    self.run_cycle()
                except KeyboardInterrupt:
                    raise
                except Exception as e:  # noqa: BLE001
                    self.log.error("Lỗi trong chu kỳ: %s", e)
                time.sleep(interval)
        except KeyboardInterrupt:
            self.log.info("Đã dừng bot.")
        finally:
            self.explainer.stop()


def main() -> None:
    config = load_config()
    Bot(config).run_forever()


if __name__ == "__main__":
    main()
