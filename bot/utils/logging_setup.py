"""Thiết lập ghi log: in ra màn hình + ghi vào tệp có TỰ XOAY VÒNG.

Xoay vòng (rotation) giúp log không phình to làm đầy ổ cứng: mỗi tệp tối đa vài MB,
đầy thì tạo tệp mới và tự xóa tệp cũ nhất.
"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_cfg: dict | None = None) -> logging.Logger:
    log_cfg = log_cfg or {}
    path = log_cfg.get("path", "logs/bot.log")
    max_bytes = int(log_cfg.get("max_bytes", 5_000_000))
    backup_count = int(log_cfg.get("backup_count", 3))

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # tránh nhân đôi handler khi gọi lại

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
