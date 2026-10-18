"""Kiểm thử logic vòng lặp sống (bước 3) — KHÔNG cần mạng, dùng sàn giả.

Chạy:  python -m tests.test_live_logic
"""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pandas as pd

from bot.main import Bot
from bot.storage.sqlite_store import SQLiteStore


# ---- Sàn giả: cho phép điều khiển giá & nến để dựng kịch bản ----
class FakeExchange:
    def __init__(self):
        self.price = 100.0
        self._candles = None

    def set_bullish_cross_at_end(self):
        """Dựng chuỗi giảm rồi tăng, rồi CẮT để giao cắt tăng rơi đúng nến đóng cuối."""
        from bot.strategy.ema_crossover import EMACrossover
        close = np.concatenate([np.linspace(110, 95, 60), np.linspace(95, 140, 60)])
        candles = [[i, c, c + 1, c - 1, c, 1.0] for i, c in enumerate(close)]
        df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
        sig = EMACrossover(9, 21).generate_signals(df)
        buys = list(sig.index[sig["signal"] == 1])
        last_buy = buys[-1]
        # Giữ tới last_buy+1: khi bỏ nến chưa đóng (iloc[:-1]) thì nến đóng cuối = last_buy (tín hiệu MUA).
        self._candles = candles[: last_buy + 2]

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=200):
        return self._candles[-limit:]

    def fetch_last_price(self, symbol):
        return self.price

    def round_amount(self, symbol, amount):
        return round(amount, 6)

    def min_cost(self, symbol):
        return 0.0

    def create_market_order(self, symbol, side, amount):
        return {"average": self.price, "filled": amount}

    def describe(self):
        return "Sàn giả (test)"


def make_config(db_path, mode="paper"):
    return {
        "exchange": {"name": "binance", "testnet": True},
        "market": {"pairs": ["BTC/USDT"], "timeframe": "1h", "candles_limit": 200},
        "strategy": {"ema_fast": 9, "ema_slow": 21},
        "risk": {"risk_per_trade": 0.01, "stop_loss_pct": 0.02, "take_profit_rr": 2.0,
                 "min_rr": 1.5, "fee_rate": 0.001, "max_total_positions": 3,
                 "circuit_breakers": {"daily_loss_limit": 0.05, "consecutive_losses": 5,
                                      "max_drawdown": 0.20}},
        "storage": {"backend": "sqlite", "sqlite_path": db_path},
        "execution": {"mode": mode},
        "run": {"poll_interval_seconds": 1, "initial_capital": 10000},
        "logging": {"path": os.path.join(tempfile.gettempdir(), "test_bot.log")},
        "secrets": {"binance_api_key": "", "binance_api_secret": ""},
    }


def build_bot(cfg, fake):
    """Dựng Bot nhưng thay sàn thật bằng sàn giả."""
    bot = Bot.__new__(Bot)
    from bot.utils.logging_setup import setup_logging
    from bot.execution.order_manager import OrderManager
    from bot.execution.portfolio import Portfolio
    from bot.risk.circuit_breakers import CircuitBreakers
    from bot.risk.risk_manager import RiskManager
    from bot.storage.sqlite_store import create_store
    from bot.strategy.ema_crossover import EMACrossover

    bot.cfg = cfg
    bot.log = setup_logging(cfg["logging"])
    bot.exchange = fake
    bot.store = create_store(cfg)
    bot.strategy = EMACrossover(9, 21)
    bot.risk = RiskManager(cfg["risk"])
    bot.order = OrderManager(fake, mode=cfg["execution"]["mode"])
    bot.portfolio = Portfolio()
    bot.pairs = cfg["market"]["pairs"]
    bot.timeframe = "1h"
    bot.candles_limit = 200
    bot.fee_rate = 0.001
    bot.max_total = 3
    if bot.store.get_meta("capital") is None:
        bot.store.set_meta("capital", 10000)
    bot.portfolio.load_from_store(bot.store)
    bot.breakers = CircuitBreakers(cfg["risk"], bot.store, bot._capital())
    bot._halt_logged = False
    return bot


def run() -> None:
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "t.db")

    # 1) Lưu trữ: ghi/đọc meta & trạng thái
    s = SQLiteStore(db)
    s.set_meta("capital", 12345)
    assert s.get_meta("capital") == "12345"
    s.save_position({"pair": "BTC/USDT", "entry_price": 100, "quantity": 1,
                     "stop_loss": 98, "take_profit": 104, "entry_time": "t"})
    assert len(s.load_open_positions()) == 1
    s.delete_position("BTC/USDT")
    assert len(s.load_open_positions()) == 0
    print("✓ Lưu trữ SQLite: ghi/đọc/xóa OK")

    # 2) Mở lệnh khi có tín hiệu mua (chế độ paper)
    cfg = make_config(os.path.join(tmp, "bot.db"))
    fake = FakeExchange(); fake.set_bullish_cross_at_end(); fake.price = 130.0
    bot = build_bot(cfg, fake)
    bot.run_cycle()
    assert bot.portfolio.has_position("BTC/USDT"), "Phải mở lệnh khi có giao cắt tăng"
    pos = bot.portfolio.get("BTC/USDT")
    print(f"✓ Mở lệnh: vào {pos.entry_price:.2f}, SL {pos.stop_loss:.2f}, TP {pos.take_profit:.2f}")

    # 3) Giá chạm TP -> đóng lệnh, lời
    fake.price = pos.take_profit + 1
    cap_before = bot._capital()
    bot.run_cycle()
    assert not bot.portfolio.has_position("BTC/USDT"), "Chạm TP phải đóng lệnh"
    assert bot._capital() > cap_before, "Đóng ở TP phải có lãi"
    trades = bot.store.load_trades()
    assert trades and trades[0]["reason"] == "TP"
    print(f"✓ Chạm TP -> đóng, vốn {cap_before:.2f} -> {bot._capital():.2f}")

    # 4) Khôi phục trạng thái: Bot mới đọc lại vốn từ DB
    bot2 = build_bot(cfg, fake)
    assert abs(bot2._capital() - bot._capital()) < 1e-6, "Vốn phải được khôi phục từ DB"
    print("✓ Khôi phục vốn từ DB sau 'khởi động lại' OK")

    # 5) Cầu dao ngắt: ép chuỗi thua -> chặn vào lệnh mới
    bot2.store.set_meta("cb_consecutive_losses", 5)
    allowed, why = bot2.breakers.check(bot2._capital())
    assert not allowed and "liên tiếp" in why
    print(f"✓ Cầu dao ngắt chặn đúng: {why}")

    print("\n✓ TẤT CẢ KIỂM THỬ BƯỚC 3 ĐỀU QUA")


if __name__ == "__main__":
    run()
