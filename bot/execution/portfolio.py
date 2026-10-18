"""Theo dõi vị thế đang mở và tính lãi/lỗ.

Một 'Position' là một lệnh MUA đang giữ, kèm điểm cắt lỗ (SL) và chốt lời (TP).
Portfolio giữ các vị thế theo cặp coin, nạp lại từ lưu trữ khi bot khởi động lại.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Position:
    pair: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    entry_time: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Position":
        return Position(
            pair=d["pair"], entry_price=d["entry_price"], quantity=d["quantity"],
            stop_loss=d["stop_loss"], take_profit=d["take_profit"], entry_time=str(d["entry_time"]),
        )

    def unrealized_pnl(self, current_price: float) -> float:
        """Lãi/lỗ tạm tính nếu đóng ở giá hiện tại (chưa trừ phí)."""
        return (current_price - self.entry_price) * self.quantity


class Portfolio:
    def __init__(self):
        self.positions: dict[str, Position] = {}

    def load_from_store(self, store) -> None:
        self.positions.clear()
        for row in store.load_open_positions():
            pos = Position.from_dict(row)
            self.positions[pos.pair] = pos

    def has_position(self, pair: str) -> bool:
        return pair in self.positions

    def get(self, pair: str) -> Position | None:
        return self.positions.get(pair)

    def open(self, pos: Position, store) -> None:
        self.positions[pos.pair] = pos
        store.save_position(pos.to_dict())

    def close(self, pair: str, store) -> None:
        self.positions.pop(pair, None)
        store.delete_position(pair)

    def count(self) -> int:
        return len(self.positions)
