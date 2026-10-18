"""Lưu trữ bằng SQLite — một tệp cơ sở dữ liệu ngay trên máy, không cần server.

Ba bảng:
  - positions : các vị thế đang mở (mỗi cặp coin tối đa 1 dòng).
  - trades    : lịch sử các lệnh đã đóng.
  - meta      : trạng thái dạng khóa-giá trị (cờ dừng khẩn, vốn đầu ngày...).
"""
from __future__ import annotations

import os
import sqlite3


class SQLiteStore:
    def __init__(self, path: str = "data/bot.db"):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                pair TEXT PRIMARY KEY,
                entry_price REAL, quantity REAL,
                stop_loss REAL, take_profit REAL,
                entry_time TEXT
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair TEXT, entry_price REAL, exit_price REAL, quantity REAL,
                pnl REAL, reason TEXT, is_win INTEGER,
                entry_time TEXT, exit_time TEXT
            )""")
        c.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        self.conn.commit()

    # --- Vị thế ---
    def save_position(self, pos: dict) -> None:
        self.conn.execute("""
            INSERT INTO positions (pair, entry_price, quantity, stop_loss, take_profit, entry_time)
            VALUES (:pair, :entry_price, :quantity, :stop_loss, :take_profit, :entry_time)
            ON CONFLICT(pair) DO UPDATE SET
                entry_price=excluded.entry_price, quantity=excluded.quantity,
                stop_loss=excluded.stop_loss, take_profit=excluded.take_profit,
                entry_time=excluded.entry_time
        """, pos)
        self.conn.commit()

    def delete_position(self, pair: str) -> None:
        self.conn.execute("DELETE FROM positions WHERE pair = ?", (pair,))
        self.conn.commit()

    def load_open_positions(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM positions").fetchall()
        return [dict(r) for r in rows]

    # --- Lịch sử lệnh ---
    def record_trade(self, trade: dict) -> None:
        self.conn.execute("""
            INSERT INTO trades (pair, entry_price, exit_price, quantity, pnl, reason, is_win, entry_time, exit_time)
            VALUES (:pair, :entry_price, :exit_price, :quantity, :pnl, :reason, :is_win, :entry_time, :exit_time)
        """, trade)
        self.conn.commit()

    def load_trades(self, limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Meta ---
    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def create_store(config: dict):
    """Nhà máy tạo lớp lưu trữ theo config (hiện chỉ có SQLite)."""
    st_cfg = config.get("storage", {})
    backend = st_cfg.get("backend", "sqlite").lower()
    if backend == "sqlite":
        return SQLiteStore(st_cfg.get("sqlite_path", "data/bot.db"))
    raise ValueError(f"Chưa hỗ trợ lưu trữ: {backend} (Supabase sẽ thêm khi lên thật)")
