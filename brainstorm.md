# BRAINSTORM — Ý tưởng & điểm cần cân nhắc thêm

> Tài liệu này ghi các ý tưởng **chưa chốt**, cần bàn thêm hoặc để dành cho giai đoạn sau.
> Khi một mục được chốt, chuyển nó sang `system_requirements.md`.
> Cập nhật lần cuối: 2026-10-18

---

## A. Chức năng học tập — mở rộng (chưa chốt)

- **Chế độ giải thích khi KHÔNG vào lệnh**: ghi lại cả những lúc bot *bỏ qua* cơ hội (ví dụ RSI đã quá mua) và giải thích vì sao đứng ngoài. Biết *khi nào không nên đánh* cũng quan trọng ngang biết khi nào nên đánh.
- **Báo cáo định kỳ (tuần/tháng)**: tổng hợp và giải thích ý nghĩa của các chỉ số:
  - Tỷ lệ thắng (win rate)
  - R:R trung bình
  - Sụt vốn tối đa (max drawdown)
  - Chuỗi thua dài nhất
  - Lợi nhuận tổng sau phí
- **Report "nghịch lý" làm công cụ dạy**: cố ý làm nổi bật các lệnh "thua nhưng quyết định đúng" và "thắng nhưng quyết định sai" để rèn tư duy xác suất.

## B0. Cải thiện chiến lược — ĐÃ LÀM / đang theo đuổi

- **Chẩn đoán từ report thật:** đa số lệnh đóng bằng "cross" (EMA cắt xuống) → bệnh whipsaw:
  vào quá nhiều lệnh chất lượng kém khi thị trường đi ngang → lỗ vặt + phí.
- **ĐÃ THÊM: bộ lọc xu hướng** (chỉ mua khi giá trên EMA dài, vd 200) — bật/tắt trong config
  và trên dashboard. Nhắm đúng điểm yếu đầu vào. Người dùng tự so sánh có/không lọc.
- **Lever tiếp theo (chưa làm):** "để lãi chạy" — trailing stop / TP rộng hơn, để vài cú trend
  lớn bù cho nhiều lệnh lỗ nhỏ (bản chất trend-following: win rate thấp nhưng R lớn ở lệnh thắng).
- **Nguyên tắc:** sửa MỘT thứ, so sánh trên cùng dữ liệu; kiểm out-of-sample để tránh overfit.

## B. Chiến lược tương lai (sau EMA Crossover + Grid)

- **MACD** — phiên bản tinh vi hơn của giao cắt đường trung bình.
- **Breakout** (giao dịch phá vỡ vùng giá) — mạnh khi có xu hướng, nhưng nhiều "phá vỡ giả".
- **RSI** — chỉ nên dùng kết hợp, **không bao giờ dùng một mình**.
- **Bollinger Bands** — hợp thị trường đi ngang.
- **DCA** (trung bình giá) — đơn giản, ít rủi ro, ít "chất kỹ thuật" để học.
- **Ghép nhiều chiến lược (multi-strategy)** — nâng cao, để rất sau.
- **Phát hiện chế độ thị trường (regime detection)** — tự nhận biết đang "có xu hướng" hay "đi ngang" để chọn chiến lược phù hợp. Nâng cao, nhưng rất đáng học về lâu dài.

## C. Futures — giai đoạn sau (KHÔNG làm trong giai đoạn học)

- Chỉ xét sau khi đã có vài tháng dữ liệu thật và hiểu rõ hành vi bot.
- Nếu dùng đòn bẩy: **tối đa 2x–3x cho người mới**, không phải 10x.
- Cân nhắc cho coin trend/meme — nhưng nhớ: bot kỹ thuật yếu trên meme coin.

## D. Lớp Giải thích bằng LLM — ĐÃ LÀM (bước 4)

- ~~Chọn nhà cung cấp~~ → **OpenAI, model mặc định `gpt-4o-mini`** (đổi trong config `explain`).
- ~~Thiết kế prompt~~ → **ĐÃ LÀM** trong `bot/explain/llm_openai.py` (có luật sắt: chỉ diễn giải,
  không quyết định, không bịa số liệu). Fallback template trong `bot/explain/templates.py`.
- Còn lại cần làm dần:
  - **Ước lượng chi phí API** thực tế theo tần suất mở/đóng lệnh (chưa đo).
  - **Báo cáo định kỳ** (tuần/tháng) tổng hợp chỉ số + giải thích (mục A) — chưa làm.
  - Chế độ giải thích khi KHÔNG vào lệnh (mục A) — chưa làm.

## E. Dashboard — ĐÃ CHỐT công nghệ

- ~~Chọn framework~~ → **ĐÃ CHỐT: Streamlit + Plotly** (xem `system_requirements.md`).
- ~~Biểu đồ nến kèm đánh dấu lệnh~~ → **ĐÃ LÀM** trong dashboard backtest (`dashboard/app.py`).
- Đã làm "chế độ backtest" trước (phòng lab). Còn lại cho bước 4:
  - Mở rộng dashboard sang theo dõi bot chạy thật (số dư, vị thế, PnL, lời giải thích).
  - Nút dừng khẩn (dashboard ghi "cờ dừng" vào DB, bot đọc mỗi vòng lặp).
  - Thêm mật khẩu khi mở dashboard ra mạng.

## F. Thư viện dự kiến (cần xác nhận khi dựng code)

| Việc | Thư viện dự kiến |
|---|---|
| Kết nối sàn | CCXT |
| Chỉ báo kỹ thuật | pandas-ta hoặc TA-Lib |
| Backtest | backtesting.py hoặc backtrader |

## G. Câu hỏi mở khác

- ~~Mô phỏng offline~~ → **ĐÃ CHỐT: làm, coi như phòng lab thử chiến lược** (xem `system_requirements.md`).
- ~~Lưu dữ liệu nến lịch sử vào DB~~ → **ĐÃ CHỐT: có lưu** (xem `system_requirements.md`).
- Chiến lược **xử lý khi mất kết nối giữa lúc có lệnh mở** cần chi tiết hơn (ngoài việc lưu trạng thái).
