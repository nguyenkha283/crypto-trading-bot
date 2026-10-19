"""Bộ điều phối lời giải thích — chạy ở LUỒNG NỀN, tách khỏi luồng giao dịch.

Cách hoạt động:
  - Luồng giao dịch (bot chính) chỉ gọi `enqueue(...)`: ghi nhanh một "yêu cầu giải thích"
    vào DB rồi đi tiếp ngay — KHÔNG chờ OpenAI, nên không bao giờ làm kẹt/lỡ lệnh.
  - Một luồng nền định kỳ lấy các yêu cầu đang chờ, gọi OpenAI để viết lời giải thích,
    và nếu lỗi/timeout thì tự rơi về giải thích theo khuôn mẫu (template).

Nhờ vậy giao dịch và giải thích hoàn toàn độc lập.
"""
from __future__ import annotations

import json
import logging
import threading
import time

from . import templates

log = logging.getLogger("bot")


class Explainer:
    def __init__(self, store, config: dict):
        self.store = store
        exp_cfg = config.get("explain", {})
        self.enabled_llm = bool(exp_cfg.get("use_llm", True))
        self.model = exp_cfg.get("model", "gpt-4o-mini")
        self.poll_seconds = int(exp_cfg.get("worker_poll_seconds", 5))

        api_key = config.get("secrets", {}).get("openai_api_key", "")
        self._llm = None
        if self.enabled_llm and api_key:
            try:
                from .llm_openai import OpenAIExplainer
                self._llm = OpenAIExplainer(api_key, model=self.model)
            except Exception as e:  # noqa: BLE001
                log.warning("Không khởi tạo được OpenAI (%s) -> dùng giải thích mẫu.", e)
        elif self.enabled_llm and not api_key:
            log.info("Chưa có OPENAI_API_KEY -> lời giải thích dùng khuôn mẫu.")

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # --- gọi từ luồng giao dịch (nhanh, không chờ) ---
    def enqueue(self, event_type: str, pair: str, facts: dict) -> None:
        try:
            self.store.enqueue_explanation(event_type, pair, json.dumps(facts, ensure_ascii=False))
        except Exception as e:  # noqa: BLE001 - lỗi ghi giải thích không được ảnh hưởng giao dịch
            log.error("Không thêm được yêu cầu giải thích: %s", e)

    # --- luồng nền xử lý ---
    def _process_one(self, row: dict) -> None:
        facts = json.loads(row["facts"])
        text, source = None, "template"
        if self._llm is not None:
            try:
                text = self._llm.explain(row["event_type"], facts)
                source = "llm"
            except Exception as e:  # noqa: BLE001 - LLM lỗi -> rơi về template
                log.warning("OpenAI lỗi (%s) -> dùng giải thích mẫu cho lần này.", e)
        if text is None:
            text = templates.render_template(row["event_type"], facts)
            source = "template"
        self.store.complete_explanation(row["id"], text, source)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                pending = self.store.fetch_pending_explanations(limit=5)
                for row in pending:
                    if self._stop.is_set():
                        break
                    self._process_one(row)
            except Exception as e:  # noqa: BLE001
                log.error("Lỗi luồng giải thích: %s", e)
            self._stop.wait(self.poll_seconds)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="explainer", daemon=True)
        self._thread.start()
        log.info("Luồng giải thích đã chạy (LLM=%s).", "bật" if self._llm else "tắt/template")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def process_pending_once(self) -> int:
        """Xử lý hết hàng chờ một lần (dùng cho kiểm thử, không cần luồng nền)."""
        count = 0
        for row in self.store.fetch_pending_explanations(limit=100):
            self._process_one(row)
            count += 1
        return count
