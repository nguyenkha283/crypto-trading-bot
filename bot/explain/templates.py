"""Giải thích theo KHUÔN MẪU (template) — phương án dự phòng khi không gọi được LLM.

Luôn chạy được, không cần mạng. Nhận 'facts' (dữ kiện thô) và ghép thành câu dễ hiểu.
"""
from __future__ import annotations


def explain_open(facts: dict) -> str:
    return (
        f"📈 MỞ LỆNH MUA {facts['pair']}\n"
        f"- Lý do: EMA nhanh ({facts['ema_fast']}) vừa cắt lên EMA chậm ({facts['ema_slow']}) "
        f"→ tín hiệu xu hướng tăng.\n"
        f"- Giá vào: {facts['entry_price']:.2f} | Cắt lỗ: {facts['stop_loss']:.2f} "
        f"| Chốt lời: {facts['take_profit']:.2f}\n"
        f"- Tỷ lệ lời/lỗ (R:R): {facts['rr']:.1f} — mạo hiểm 1 để kiếm {facts['rr']:.1f}.\n"
        f"- Khối lượng đặt sao cho nếu dính cắt lỗ chỉ mất ~{facts['risk_pct']:.0f}% vốn."
    )


def explain_close(facts: dict) -> str:
    result = "lời" if facts["pnl"] >= 0 else "lỗ"
    reason_map = {
        "TP": "giá chạm mức chốt lời như kế hoạch",
        "SL": "giá chạm mức cắt lỗ — lệnh được cắt để bảo vệ vốn",
        "cross": "EMA nhanh cắt xuống dưới EMA chậm — xu hướng tăng kết thúc",
        "killswitch": "người dùng bật dừng khẩn",
        "end": "kết thúc phiên",
    }
    quality = (
        "Quyết định TỐT: vào có lý do, có cắt lỗ đặt trước, đúng luật."
        if facts.get("had_plan", True)
        else "Cần xem lại kế hoạch vào lệnh."
    )
    lesson = (
        "Đây là khoản lỗ đúng luật — bình thường trong giao dịch, đừng vì một lệnh mà đổi chiến lược."
        if facts["pnl"] < 0
        else "Chiến lược theo xu hướng hiệu quả khi thị trường có xu hướng rõ."
    )
    return (
        f"{'✅' if facts['pnl'] >= 0 else '❌'} ĐÓNG LỆNH {facts['pair']} | {result} "
        f"{facts['pnl']:+.2f} USDT\n"
        f"- Diễn biến: {reason_map.get(facts['reason'], facts['reason'])}.\n"
        f"- Đánh giá quyết định: {quality}\n"
        f"- Bài học: {lesson}"
    )


def render_template(event_type: str, facts: dict) -> str:
    return explain_open(facts) if event_type == "open" else explain_close(facts)
