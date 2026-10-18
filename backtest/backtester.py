"""Backtester — chạy thử chiến lược trên nến lịch sử.

Cách hoạt động (đi qua từng nến, giống hệt lúc chạy thật):
  - Khi đang RẢNH (không giữ lệnh): nếu có tín hiệu MUA và rủi ro cho phép -> vào lệnh
    tại giá đóng của nến đó; đặt sẵn SL và TP.
  - Khi ĐANG GIỮ lệnh: mỗi nến kiểm tra
        1) giá có chạm SL không (dùng giá thấp nhất của nến) -> thoát, lỗ;
        2) giá có chạm TP không (dùng giá cao nhất của nến) -> thoát, lời;
        3) có tín hiệu THOÁT (cắt xuống) không -> thoát tại giá đóng.
    (Ưu tiên kiểm SL trước cho an toàn/bảo thủ.)
  - Hết dữ liệu mà còn lệnh mở -> đóng ở giá đóng cuối cùng.

Có tính PHÍ mỗi chiều để kết quả sát thực tế (người mới hay quên phí).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from bot.risk.risk_manager import RiskManager
from bot.strategy.base import BaseStrategy, SIGNAL_BUY, SIGNAL_EXIT


@dataclass
class Trade:
    entry_time: object
    entry_price: float
    exit_time: object
    exit_price: float
    quantity: float
    pnl: float            # lãi/lỗ bằng tiền (đã trừ phí)
    pnl_pct: float        # lãi/lỗ so với vốn lúc vào lệnh
    reason: str           # vì sao thoát: SL / TP / cross / end
    is_win: bool


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    initial_capital: float = 0.0
    final_capital: float = 0.0

    # --- các chỉ số tính sẵn ---
    @property
    def total_return_pct(self) -> float:
        if self.initial_capital == 0:
            return 0.0
        return (self.final_capital - self.initial_capital) / self.initial_capital * 100

    @property
    def num_trades(self) -> int:
        return len(self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.is_win)

    @property
    def losses(self) -> int:
        return self.num_trades - self.wins

    @property
    def win_rate(self) -> float:
        return (self.wins / self.num_trades * 100) if self.num_trades else 0.0

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = -sum(t.pnl for t in self.trades if t.pnl < 0)
        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @property
    def max_drawdown_pct(self) -> float:
        """Mức sụt sâu nhất của đường vốn so với đỉnh trước đó."""
        peak = -float("inf")
        max_dd = 0.0
        for eq in self.equity_curve:
            peak = max(peak, eq)
            if peak > 0:
                dd = (peak - eq) / peak
                max_dd = max(max_dd, dd)
        return max_dd * 100

    @property
    def longest_losing_streak(self) -> int:
        streak = best = 0
        for t in self.trades:
            if not t.is_win:
                streak += 1
                best = max(best, streak)
            else:
                streak = 0
        return best


def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    risk: RiskManager,
    initial_capital: float = 10000.0,
    fee_rate: float = 0.001,
) -> BacktestResult:
    data = strategy.generate_signals(df).reset_index(drop=True)

    capital = initial_capital
    result = BacktestResult(initial_capital=initial_capital)
    result.equity_curve.append(capital)

    in_position = False
    plan = None
    entry_time = None

    def close_trade(exit_price: float, exit_time, reason: str):
        nonlocal capital, in_position, plan, entry_time
        qty = plan.quantity
        fees = (plan.entry_price * qty + exit_price * qty) * fee_rate
        pnl = (exit_price - plan.entry_price) * qty - fees
        capital += pnl
        result.trades.append(
            Trade(
                entry_time=entry_time,
                entry_price=plan.entry_price,
                exit_time=exit_time,
                exit_price=exit_price,
                quantity=qty,
                pnl=pnl,
                pnl_pct=pnl / initial_capital * 100,
                reason=reason,
                is_win=pnl > 0,
            )
        )
        result.equity_curve.append(capital)
        in_position = False
        plan = None
        entry_time = None

    for i in range(len(data)):
        row = data.iloc[i]
        sig = int(row["signal"])
        t = row.get("datetime", i)

        if not in_position:
            if sig == SIGNAL_BUY:
                candidate = risk.plan_long(entry_price=float(row["close"]), capital=capital)
                if candidate.ok:
                    plan = candidate
                    entry_time = t
                    in_position = True
            continue

        # Đang giữ lệnh: kiểm SL -> TP -> tín hiệu thoát.
        low = float(row["low"])
        high = float(row["high"])
        if low <= plan.stop_loss:
            close_trade(plan.stop_loss, t, "SL")
        elif high >= plan.take_profit:
            close_trade(plan.take_profit, t, "TP")
        elif sig == SIGNAL_EXIT:
            close_trade(float(row["close"]), t, "cross")

    # Còn lệnh mở lúc hết dữ liệu -> đóng ở giá cuối.
    if in_position and plan is not None:
        last = data.iloc[-1]
        close_trade(float(last["close"]), last.get("datetime", len(data) - 1), "end")

    result.final_capital = capital
    return result
