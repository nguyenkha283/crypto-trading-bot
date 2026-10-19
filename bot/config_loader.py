"""Đọc cấu hình: tham số từ config.yaml + khóa bí mật từ biến môi trường (.env).

Tách riêng việc đọc cấu hình để mọi nơi khác trong bot dùng chung một nguồn,
và để khóa bí mật không bao giờ nằm trong code.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Thư mục gốc của dự án (thư mục chứa file config.yaml)
ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config(config_path: str | None = None) -> dict:
    """Đọc file config.yaml và nạp biến môi trường từ .env.

    Trả về một dict cấu hình, trong đó phần 'secrets' chứa khóa đọc từ .env
    (không nằm trong file yaml).
    """
    # Nạp .env (nếu có) vào biến môi trường
    load_dotenv(ROOT_DIR / ".env")

    path = Path(config_path) if config_path else ROOT_DIR / "config" / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Gắn khóa bí mật đọc từ biến môi trường vào cấu hình
    config["secrets"] = {
        "binance_api_key": os.getenv("BINANCE_API_KEY", ""),
        "binance_api_secret": os.getenv("BINANCE_API_SECRET", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    }
    return config


def has_binance_keys(config: dict) -> bool:
    """Kiểm tra đã có đủ khóa Binance chưa (để biết có xem được số dư không)."""
    s = config.get("secrets", {})
    return bool(s.get("binance_api_key") and s.get("binance_api_secret"))
