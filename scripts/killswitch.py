"""Bật/tắt CỜ DỪNG KHẨN của bot.

Khi bật, ở chu kỳ kế tiếp bot sẽ đóng mọi lệnh và dừng lại.
(Sau này nút này sẽ nằm trên dashboard — hiện làm bằng dòng lệnh cho tiện.)

Cách dùng:
    python -m scripts.killswitch on     # bật dừng khẩn
    python -m scripts.killswitch off    # tắt (cho phép chạy lại)
    python -m scripts.killswitch status # xem trạng thái
"""
from __future__ import annotations

import sys

from bot.config_loader import load_config
from bot.storage.sqlite_store import create_store


def main() -> None:
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    store = create_store(load_config())

    if action == "on":
        store.set_meta("kill_switch", "1")
        print("✓ ĐÃ BẬT cờ dừng khẩn. Chu kỳ tới bot sẽ đóng mọi lệnh và dừng.")
    elif action == "off":
        store.set_meta("kill_switch", "0")
        print("✓ Đã TẮT cờ dừng khẩn. Có thể chạy lại bot.")
    else:
        state = store.get_meta("kill_switch", "0")
        print("Cờ dừng khẩn hiện:", "ĐANG BẬT" if state == "1" else "đang tắt")


if __name__ == "__main__":
    main()
