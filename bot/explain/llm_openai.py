"""Gọi OpenAI để viết lời giải thích tự nhiên, dễ hiểu.

LUẬT SẮT: LLM chỉ DIỄN GIẢI quyết định đã có sẵn — KHÔNG quyết định mua/bán.
Dữ kiện (facts) được truyền vào; LLM chỉ diễn đạt lại cho dễ hiểu, không bịa thêm số liệu.

Tách riêng lớp này để sau đổi nhà cung cấp LLM chỉ cần sửa ở đây.
"""
from __future__ import annotations

import json

SYSTEM_PROMPT = (
    "Bạn là một người thầy dạy giao dịch, nói tiếng Việt, giải thích CỰC KỲ dễ hiểu cho "
    "người mới. Bạn CHỈ diễn giải lại một quyết định giao dịch đã được đưa ra bằng luật rõ "
    "ràng — TUYỆT ĐỐI không tự đề xuất mua/bán, không dự đoán giá, không bịa thêm số liệu "
    "ngoài dữ kiện được cung cấp. Giữ giọng điềm tĩnh, khách quan. Nhấn mạnh tư duy xác suất: "
    "kết quả một lệnh (lời/lỗ) khác với chất lượng quyết định (có tuân thủ luật không). "
    "Trả lời ngắn gọn 3-5 gạch đầu dòng."
)


class OpenAIExplainer:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout: float = 20.0):
        self.model = model
        self.timeout = timeout
        # Import trong hàm để không bắt buộc cài openai khi chỉ chạy chế độ template.
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, timeout=timeout)

    def explain(self, event_type: str, facts: dict) -> str:
        user_msg = (
            f"Hãy giải thích cho người mới về sự kiện '{event_type}' sau đây. "
            f"Chỉ dùng đúng các dữ kiện này, không thêm số liệu mới:\n"
            f"{json.dumps(facts, ensure_ascii=False, indent=2)}"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.4,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
