# YÊU CẦU HỆ THỐNG — Bot Giao Dịch Tiền Mã Hóa (Học Tập)

> Tài liệu này ghi lại **các quyết định đã chốt**. Đây là nguồn thông tin chính thức.
> Các ý tưởng chưa chốt nằm ở tệp `brainstorm.md`.
> Cập nhật lần cuối: 2026-10-18

---

## 1. Mục tiêu dự án

- Xây một bot tự động giao dịch để **học kiến thức giao dịch**, không phải để kiếm lời bằng mọi giá.
- Mục tiêu cuối: tích lũy đủ hiểu biết và sự tin tưởng để **đưa bot vào giao dịch thật** sau giai đoạn demo.
- Ưu tiên: bot phải **dạy được** người dùng qua từng quyết định, không chỉ chạy âm thầm.

## 2. Nền tảng & hạ tầng

| Hạng mục | Quyết định |
|---|---|
| Ngôn ngữ | Python |
| Nơi chạy | Oracle Free Tier — máy ảo Always Free ARM Ampere A1 |
| Chế độ chạy | 24/7, tự khởi động lại khi lỗi hoặc máy reboot (dùng systemd hoặc Docker) |
| Sàn giao dịch | Binance Testnet (giai đoạn demo), thiết kế tách lớp để chuyển sang Binance thật |

> ❌ **Không dùng Vercel**: đây là nền tảng serverless, không giữ được tiến trình chạy liên tục nên không hợp cho bot 24/7.

## 3. Lộ trình triển khai (bắt buộc đi theo thứ tự)

1. **Backtest** — chạy chiến lược trên dữ liệu lịch sử.
2. **Testnet** — tiền ảo, giá thật (Binance Testnet).
3. **Live vốn nhỏ** — tiền thật nhưng số lượng nhỏ.

> Không được bỏ qua bước nào.

## 4. Thị trường & cặp giao dịch

| Giai đoạn | Thị trường | Cặp |
|---|---|---|
| Học (3–6 tháng đầu) | **Chỉ Spot** | BTC/USDT, ETH/USDT, SOL/USDT |
| Sau này (khi đã hiểu bot) | Cân nhắc Futures | Xem `brainstorm.md` |

> Lý do loại Futures và meme coin khỏi giai đoạn học: meme coin không chạy theo phân tích kỹ thuật (chạy theo tin tức, tâm lý); Futures + đòn bẩy làm tăng rủi ro thanh lý trước khi bot kịp cắt lỗ.

## 5. Chiến lược

- **Chiến lược đầu tiên: EMA Crossover** (giao cắt đường trung bình) — đơn giản, dễ hiểu bản chất.
- **Chiến lược thứ hai: Grid Trading** (giao dịch theo lưới) — học tư duy phi hướng.
- Nguyên tắc: **không có chiến lược nào thắng trong mọi điều kiện thị trường**. Giá trị cốt lõi của bot là **đo lường và so sánh** chiến lược nào hợp điều kiện nào, không phải tìm "chén thánh".
- Mọi chiến lược đều phải gắn với backtest trước khi chạy demo.

## 6. Quản lý rủi ro (các con số mặc định — chỉnh được trong config)

| Hạng mục | Giá trị mặc định | Ghi chú |
|---|---|---|
| Khung thời gian nến | 1 giờ hoặc 4 giờ | Không scalping khung nhỏ (nhiều nhiễu, tốn phí) |
| Rủi ro mỗi lệnh | 1% vốn | Thua 10 lệnh liên tiếp vẫn còn ~90% vốn |
| Số lệnh mở cùng lúc | Tối đa 1 lệnh/cặp, 2–3 cặp | Dễ theo dõi |
| Stop-loss (cắt lỗ) | **Bắt buộc 100%** | Luật không thể phá: không lệnh nào thiếu SL |
| R:R tối thiểu (tỷ lệ lời/lỗ) | ≥ 1.5 | Không đủ thì bot bỏ qua lệnh |
| Phí giao dịch | ~0.1%, tính vào mô phỏng | Để backtest không bị "ảo tưởng" lợi nhuận |

### Ba "cầu dao ngắt" (circuit breaker) — bắt buộc

1. **Giới hạn lỗ trong ngày**: lỗ quá 3–5%/ngày → dừng giao dịch hết ngày + cảnh báo.
2. **Chuỗi thua**: thua 4–5 lệnh liên tiếp → tạm dừng + báo người dùng.
3. **Sụt vốn tối đa (max drawdown)**: sụt quá 20% so với đỉnh → ngắt toàn bộ, chờ người dùng xem lại.

## 7. Lớp Giải thích (Explainability) — chức năng học tập cốt lõi

- **Dùng LLM** (gọi AI) để viết lời giải thích tự nhiên, dễ hiểu.
- **Nhà cung cấp giai đoạn demo: OpenAI.** Khi lên giao dịch thật có thể đổi nhà cung cấp → thiết kế lớp gọi LLM tách riêng để đổi dễ dàng.
- ⚠️ **Luật sắt: LLM CHỈ giải thích, TUYỆT ĐỐI không quyết định giao dịch.** Quyết định mua/bán do luật rõ ràng (EMA, RSI...) đưa ra. LLM chỉ chạy *sau khi* đã có quyết định, để diễn giải.
- **Có phương án dự phòng (fallback)**: nếu gọi LLM lỗi/chậm, bot tự rơi về giải thích theo khuôn mẫu (template). Việc gọi LLM **không bao giờ được làm kẹt hay lỡ một lệnh**.
- **Chạy ở luồng tách biệt** với luồng giao dịch.
- **Chỉ gọi LLM lúc**: vào lệnh / đóng lệnh / báo cáo định kỳ (không gọi mỗi cây nến, để tiết kiệm chi phí).

### Hai thời điểm giải thích
- **Khi vào lệnh**: giải thích lý do, số liệu lúc vào, kế hoạch SL/TP, tỷ lệ R:R.
- **Khi đóng lệnh**: diễn biến, đánh giá chất lượng quyết định, bài học.

### Nguyên tắc quan trọng: tách "kết quả" khỏi "chất lượng quyết định"
- Một lệnh **thắng tiền vẫn có thể là quyết định tồi** (ăn may); một lệnh **thua tiền vẫn có thể là quyết định đúng** (xui).
- Báo cáo phải có **2 cột riêng**: *kết quả (lời/lỗ)* và *chất lượng quyết định (có tuân thủ luật không)*.

## 8. Giao diện người dùng

| Kênh | Mục đích |
|---|---|
| **Dashboard (bảng điều khiển web)** | Phân tích, xem báo cáo, đọc lời giải thích. **Công nghệ đã chốt: Streamlit + Plotly.** Làm "chế độ backtest" trước (phòng lab nghịch chiến lược), sau mở rộng sang theo dõi bot chạy thật. **Phải có bảo mật/mật khẩu** khi mở ra mạng (giai đoạn chạy cục bộ chưa cần). |
| **Telegram** | Cảnh báo khẩn: bot chết, chạm giới hạn lỗ, cầu dao ngắt kích hoạt. |

> Nguyên tắc: Dashboard để *phân tích*, Telegram để *báo động* (vì không thể ngồi nhìn dashboard 24/7).

## 9. Độ bền & an toàn vận hành

| Chức năng | Quyết định |
|---|---|
| **Khôi phục sau sự cố** | Lưu trạng thái vào cơ sở dữ liệu sau mỗi hành động. Khi khởi động lại, bot đọc lại vị thế đang giữ và SL/TP để không bỏ quên lệnh. |
| **Cơ sở dữ liệu** | Giai đoạn học: **SQLite** (tệp trên máy ảo). Khi lên thật: **Supabase** (bên ngoài máy ảo, bền hơn). Thiết kế lớp lưu trữ tách riêng để đổi dễ dàng. ⚠️ **Ngay khi người dùng thông báo "lên giao dịch thật" → chuyển sang Supabase ngay lập tức.** |
| **Công tắc dừng khẩn (kill switch)** | Có. Nút "dừng hết, đóng mọi lệnh ngay" bấm từ dashboard/Telegram. |
| **Điểm danh sức khỏe (heartbeat)** | Có. Bot báo "còn sống" định kỳ; im quá lâu → cảnh báo. |
| **Module backtest** | Có, làm sớm (ngay trong phiên bản đầu). |
| **Cách lấy dữ liệu giá** | **Polling** (bot hỏi giá mỗi vài phút), không dùng WebSocket. Lý do: khung 1h/4h không cần dữ liệu từng giây; polling đơn giản và nhẹ hơn nhiều. |

## 10. Bảo mật (áp dụng khi lên giao dịch thật)

- API key để trong **biến môi trường**, không ghi trong code, không commit lên Git.
- Trên sàn: chỉ cấp quyền **giao dịch**, **tắt quyền rút tiền (withdraw)**.

## 11. Dữ liệu lịch sử & Phòng lab mô phỏng offline

- **Lưu dữ liệu nến lịch sử vào cơ sở dữ liệu**: để backtest nhanh hơn, không phải tải lại từ sàn mỗi lần.
- **Phòng lab mô phỏng offline**: một chế độ chạy chiến lược hoàn toàn offline (không cần kết nối sàn), dùng dữ liệu nến đã lưu. Mục đích: thử nghiệm chiến lược cực nhanh, không phụ thuộc mạng/sàn. Coi như "phòng thí nghiệm" để nghịch ý tưởng trước khi đưa lên Testnet.

## 12. Xử lý sự cố — các trường hợp bot ngừng chạy

| Nguyên nhân | Biện pháp chống |
|---|---|
| Máy ảo khởi động lại | systemd/Docker tự bật lại bot |
| Lỗi chưa lường trước trong code | Bọc vòng lặp chính bằng xử lý lỗi (try/except), ghi log lỗi, gửi cảnh báo Telegram, systemd tự bật lại. Khi bật lại, cơ chế khôi phục trạng thái đọc lại vị thế đang giữ |
| Hết bộ nhớ (RAM) | systemd tự bật lại; giữ bộ nhớ gọn, không tích lũy dữ liệu vô hạn; theo dõi mức dùng RAM |
| Mất mạng / sàn Binance tạm sập | Thử lại có giãn cách (retry + backoff), không để lỗi mạng làm văng bot; mất kết nối kéo dài → tạm dừng giao dịch + cảnh báo; không đặt lệnh khi dữ liệu đã cũ |
| Bị sàn chặn do gọi quá dày (rate limit) | Bật giới hạn tốc độ gọi của CCXT (enableRateLimit); polling thưa (vài phút/lần, hợp khung 1h-4h); gặp lỗi 429 thì giãn cách |
| Đầy ổ cứng do log quá nhiều | **Tự động dọn log (log rotation)**: giới hạn dung lượng mỗi tệp log, tự xóa log cũ; theo dõi kích thước cơ sở dữ liệu |

---

## Nguyên tắc kiến trúc xuyên suốt

1. **Tách lớp "sàn" riêng** — chuyển testnet ↔ thật chỉ bằng đổi config.
2. **Tách lớp "lưu trữ" riêng** — chuyển SQLite ↔ Supabase chỉ bằng đổi config.
3. **Tách luồng "giao dịch" và luồng "giải thích"** — giải thích lỗi không được ảnh hưởng giao dịch.
4. **Mọi tham số quan trọng nằm trong file config**, không viết cứng trong code.
