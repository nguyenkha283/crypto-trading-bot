"""Cầu dao ngắt (circuit breaker) — tự dừng bot khi gặp nguy hiểm.

Ba loại (ngưỡng lấy từ config):
  1. Lỗ trong ngày quá mức      -> dừng vào lệnh mới hết ngày.
  2. Thua nhiều lệnh liên tiếp  -> tạm dừng, chờ người xem lại.
  3. Sụt vốn tổng quá sâu (drawdown) -> ngắt toàn bộ.

Trạng thái (vốn đầu ngày, đỉnh vốn, chuỗi thua, ngày hiện tại) được lưu qua 'store'
để sống sót khi bot khởi động lại.
"""
from __future__ import annotations

import logging
from datetime import date

log = logging.getLogger("bot")


class CircuitBreakers:
    def __init__(self, cfg: dict, store, current_equity: float):
        cb = cfg.get("circuit_breakers", {})
        self.daily_loss_limit = cb.get("daily_loss_limit", 0.05)
        self.max_consecutive = cb.get("consecutive_losses", 5)
        self.max_drawdown = cb.get("max_drawdown", 0.20)
        self.store = store
        self._init_state(current_equity)

    def _init_state(self, equity: float) -> None:
        today = date.today().isoformat()
        if self.store.get_meta("cb_date") != today:
            # Sang ngày mới: đặt lại mốc vốn đầu ngày.
            self.store.set_meta("cb_date", today)
            self.store.set_meta("cb_day_start_equity", equity)
        if self.store.get_meta("cb_peak_equity") is None:
            self.store.set_meta("cb_peak_equity", equity)
        if self.store.get_meta("cb_consecutive_losses") is None:
            self.store.set_meta("cb_consecutive_losses", 0)

    def on_trade_closed(self, is_win: bool, equity: float) -> None:
        """Gọi sau mỗi lệnh đóng để cập nhật chuỗi thua và đỉnh vốn."""
        streak = int(self.store.get_meta("cb_consecutive_losses", "0"))
        streak = 0 if is_win else streak + 1
        self.store.set_meta("cb_consecutive_losses", streak)

        peak = float(self.store.get_meta("cb_peak_equity", str(equity)))
        if equity > peak:
            self.store.set_meta("cb_peak_equity", equity)

    def check(self, equity: float) -> tuple[bool, str]:
        """Trả về (được_phép_vào_lệnh_mới, lý_do_nếu_bị_chặn)."""
        # Sang ngày mới thì làm mới mốc đầu ngày.
        today = date.today().isoformat()
        if self.store.get_meta("cb_date") != today:
            self.store.set_meta("cb_date", today)
            self.store.set_meta("cb_day_start_equity", equity)

        day_start = float(self.store.get_meta("cb_day_start_equity", str(equity)))
        if day_start > 0 and (day_start - equity) / day_start >= self.daily_loss_limit:
            return False, f"Lỗ trong ngày vượt {self.daily_loss_limit:.0%} -> dừng hết ngày"

        streak = int(self.store.get_meta("cb_consecutive_losses", "0"))
        if streak >= self.max_consecutive:
            return False, f"Thua {streak} lệnh liên tiếp -> tạm dừng, cần xem lại"

        peak = float(self.store.get_meta("cb_peak_equity", str(equity)))
        if peak > 0 and (peak - equity) / peak >= self.max_drawdown:
            return False, f"Sụt vốn vượt {self.max_drawdown:.0%} so với đỉnh -> ngắt toàn bộ"

        return True, ""
