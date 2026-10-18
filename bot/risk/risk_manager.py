"""Lớp quản lý rủi ro — "cái phanh" bảo vệ tài khoản.

Nhiệm vụ: từ giá vào lệnh và vốn hiện có, tính ra:
  - giá cắt lỗ (SL) và giá chốt lời (TP),
  - khối lượng mua sao cho nếu dính SL chỉ mất đúng `risk_per_trade` (vd 1%) vốn,
  - kiểm tra tỷ lệ lời/lỗ (R:R) có đạt mức tối thiểu không.

Dùng CHUNG cho cả backtest và chạy thật, nên chiến lược backtest đúng với thực tế.
Hiện làm cho lệnh MUA (long) trên Spot — không dùng đòn bẩy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TradePlan:
    """Kế hoạch một lệnh sau khi qua kiểm duyệt rủi ro."""
    entry_price: float
    stop_loss: float
    take_profit: float
    quantity: float
    risk_amount: float      # số tiền tối đa sẽ mất nếu dính SL
    rr: float               # tỷ lệ lời/lỗ của kế hoạch
    ok: bool                # có được phép vào lệnh không
    reason: str = ""        # lý do nếu bị từ chối


class RiskManager:
    def __init__(self, risk_cfg: dict):
        self.risk_per_trade = risk_cfg.get("risk_per_trade", 0.01)
        self.stop_loss_pct = risk_cfg.get("stop_loss_pct", 0.02)
        self.take_profit_rr = risk_cfg.get("take_profit_rr", 2.0)
        self.min_rr = risk_cfg.get("min_rr", 1.5)

    def plan_long(self, entry_price: float, capital: float) -> TradePlan:
        """Lập kế hoạch cho một lệnh MUA tại `entry_price` với `capital` hiện có."""
        # Khoảng cách từ giá vào tới điểm cắt lỗ (tính theo %).
        risk_per_unit = entry_price * self.stop_loss_pct
        stop_loss = entry_price - risk_per_unit
        take_profit = entry_price + risk_per_unit * self.take_profit_rr
        rr = self.take_profit_rr

        # Số tiền tối đa chấp nhận mất cho lệnh này.
        risk_amount = capital * self.risk_per_trade
        # Khối lượng để nếu dính SL thì mất đúng risk_amount.
        quantity = risk_amount / risk_per_unit if risk_per_unit > 0 else 0.0

        # Trên Spot không mua quá số vốn đang có.
        max_affordable = capital / entry_price if entry_price > 0 else 0.0
        if quantity > max_affordable:
            quantity = max_affordable

        # Kiểm tra điều kiện vào lệnh.
        ok, reason = True, ""
        if rr < self.min_rr:
            ok, reason = False, f"R:R {rr:.2f} < tối thiểu {self.min_rr}"
        elif quantity <= 0:
            ok, reason = False, "khối lượng tính ra bằng 0"

        return TradePlan(
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            risk_amount=risk_amount,
            rr=rr,
            ok=ok,
            reason=reason,
        )
