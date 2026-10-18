"""Giao diện chung cho 'lớp lưu trữ'.

Tách riêng để sau đổi từ SQLite (học) sang Supabase (khi lên thật) chỉ bằng đổi config,
không sửa logic bot. Lưu trữ phục vụ 2 việc:
  - Khôi phục sau sự cố: lưu vị thế đang mở để khởi động lại không bỏ quên lệnh.
  - Lịch sử & trạng thái: lệnh đã đóng, và các giá trị trạng thái (meta) như cờ dừng khẩn,
    vốn đầu ngày, số lệnh thua liên tiếp...
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseStore(ABC):
    # --- Vị thế đang mở ---
    @abstractmethod
    def save_position(self, pos: dict) -> None: ...

    @abstractmethod
    def delete_position(self, pair: str) -> None: ...

    @abstractmethod
    def load_open_positions(self) -> list[dict]: ...

    # --- Lịch sử lệnh đã đóng ---
    @abstractmethod
    def record_trade(self, trade: dict) -> None: ...

    @abstractmethod
    def load_trades(self, limit: int = 100) -> list[dict]: ...

    # --- Trạng thái dạng khóa-giá trị (meta) ---
    @abstractmethod
    def set_meta(self, key: str, value: str) -> None: ...

    @abstractmethod
    def get_meta(self, key: str, default: str | None = None) -> str | None: ...
