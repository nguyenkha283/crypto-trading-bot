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

## D. Lớp Giải thích bằng LLM — còn lại cần quyết

- ~~Chọn nhà cung cấp LLM nào?~~ → **ĐÃ CHỐT: OpenAI cho giai đoạn demo** (xem `system_requirements.md`). Khi lên thật có thể đổi.
- **Ước lượng chi phí API** theo tần suất gọi (vào/đóng lệnh + báo cáo). Cần tính thử.
- **Thiết kế câu lệnh (prompt)** cho LLM để lời giải thích vừa dễ hiểu vừa chính xác, không "bịa" lý do.

## E. Dashboard — đang chờ người dùng chọn công nghệ

Các phương án được tư vấn (chi tiết trong phần trả lời chat):
- **Streamlit** — nhanh nhất, thuần Python, hợp giai đoạn học. *(đề xuất cho bản đầu)*
- **FastAPI + giao diện nhẹ** — mạnh hơn, hợp khi lên thật.
- **Grafana** — biểu đồ giám sát đẹp, nhưng chỉ để xem (không bấm nút điều khiển được).

Lưu ý kiến trúc: dashboard chạy ở tiến trình (process) riêng, tách khỏi bot. Nút dừng khẩn hoạt động bằng cách dashboard ghi "cờ dừng" vào DB/tệp, bot đọc cờ này mỗi vòng lặp.

Còn cần quyết:
- Chốt framework nào.
- Có cần biểu đồ nến kèm đánh dấu điểm vào/ra lệnh không? (rất hữu ích để học, nhưng tốn công).

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
