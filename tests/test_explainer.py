"""Kiểm thử lớp giải thích — KHÔNG cần mạng/OpenAI.

Chạy:  python -m tests.test_explainer
"""
from __future__ import annotations

import os
import tempfile

from bot.explain.explainer import Explainer
from bot.explain import templates
from bot.storage.sqlite_store import SQLiteStore


def base_config(db_path):
    return {
        "explain": {"use_llm": False, "model": "gpt-4o-mini", "worker_poll_seconds": 1},
        "storage": {"backend": "sqlite", "sqlite_path": db_path},
        "secrets": {"openai_api_key": ""},
    }


def run() -> None:
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "e.db")
    store = SQLiteStore(db)

    # 1) Template chạy được cho cả open & close
    open_facts = {"pair": "BTC/USDT", "entry_price": 67000, "stop_loss": 65660,
                  "take_profit": 69680, "rr": 2.0, "risk_pct": 1.0, "ema_fast": 9, "ema_slow": 21}
    close_facts = {"pair": "BTC/USDT", "entry_price": 67000, "exit_price": 69680,
                   "pnl": 150.0, "reason": "TP", "had_plan": True, "ema_fast": 9, "ema_slow": 21}
    assert "MỞ LỆNH" in templates.render_template("open", open_facts)
    assert "ĐÓNG LỆNH" in templates.render_template("close", close_facts)
    # Lệnh lỗ phải có bài học "khoản lỗ đúng luật"
    loss = dict(close_facts); loss["pnl"] = -120; loss["reason"] = "SL"
    assert "khoản lỗ" in templates.render_template("close", loss)
    print("✓ Template sinh giải thích cho open/close/lỗ OK")

    # 2) Explainer không có LLM -> fallback template, xử lý hàng chờ
    ex = Explainer(store, base_config(db))
    assert ex._llm is None, "Không có khóa -> không khởi tạo LLM"
    ex.enqueue("open", "BTC/USDT", open_facts)
    ex.enqueue("close", "BTC/USDT", close_facts)
    assert len(store.fetch_pending_explanations()) == 2
    n = ex.process_pending_once()
    assert n == 2
    done = store.load_explanations()
    assert len(done) == 2 and all(d["source"] == "template" for d in done)
    assert len(store.fetch_pending_explanations()) == 0
    print(f"✓ Explainer (không LLM): xử lý {n} yêu cầu -> giải thích mẫu, hàng chờ trống")

    # 3) Giả lập LLM để kiểm nhánh LLM + ghi nguồn 'llm'
    db2 = os.path.join(tmp, "e2.db")
    store2 = SQLiteStore(db2)
    ex2 = Explainer(store2, base_config(db2))

    class FakeLLM:
        def explain(self, event_type, facts):
            return f"[AI] Giải thích {event_type} cho {facts['pair']}"

    ex2._llm = FakeLLM()
    ex2.enqueue("open", "ETH/USDT", open_facts)
    ex2.process_pending_once()
    done2 = store2.load_explanations()
    assert done2 and done2[0]["source"] == "llm" and done2[0]["text"].startswith("[AI]")
    print("✓ Nhánh LLM: dùng LLM khi có, ghi nguồn 'llm' đúng")

    # 4) LLM lỗi -> tự rơi về template
    class BrokenLLM:
        def explain(self, event_type, facts):
            raise RuntimeError("timeout giả lập")

    ex2._llm = BrokenLLM()
    ex2.enqueue("close", "ETH/USDT", close_facts)
    ex2.process_pending_once()
    latest = store2.load_explanations(limit=1)[0]
    assert latest["source"] == "template", "LLM lỗi phải rơi về template"
    print("✓ LLM lỗi -> tự rơi về giải thích mẫu (fallback) OK")

    print("\n✓ TẤT CẢ KIỂM THỬ LỚP GIẢI THÍCH ĐỀU QUA")


if __name__ == "__main__":
    run()
