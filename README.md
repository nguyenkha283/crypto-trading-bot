# Crypto Trading Bot (học tập)

Bot tự động giao dịch tiền mã hóa để **học kiến thức giao dịch**, chạy trên Binance Testnet
(tiền ảo) trước khi tính tới giao dịch thật. Bot giải thích từng quyết định để người dùng hiểu.

> 📖 Muốn hiểu toàn bộ dự án, đọc `project_handle.md` trước, rồi `ARCHITECTURE.md`.

---

## Tiến độ

- [x] Tài liệu yêu cầu, kiến trúc, cấu trúc thư mục
- [x] **Bước 1:** kết nối Binance Testnet + lấy nến
- [x] **Bước 2:** chiến lược EMA Crossover + backtest
- [x] **Dashboard backtest** (phòng lab nghịch chiến lược — Streamlit)
- [x] **Bước 3:** vòng lặp chính + thực thi lệnh (paper/testnet) + lưu & khôi phục trạng thái
- [x] **Bước 4:** lớp giải thích (OpenAI + fallback mẫu) + dashboard theo dõi bot chạy
- [x] **Deploy Oracle:** tệp cài đặt + systemd + GitHub Actions (xem `deploy/README.md`)
- [ ] Tiếp theo: Telegram cảnh báo

---

## Chạy thử bước 1 (kiểm tra kết nối)

**1. Tải mã nguồn & vào thư mục**
```bash
git clone https://github.com/nguyenkha283/crypto-trading-bot
cd crypto-trading-bot
```

**2. Tạo môi trường ảo & cài thư viện**

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**3. (Tùy chọn) Điền khóa API để xem được số dư**

Lấy nến KHÔNG cần khóa. Chỉ khi muốn xem số dư / đặt lệnh mới cần:

macOS / Linux:
```bash
cp .env.example .env     # rồi mở .env, điền BINANCE_API_KEY và BINANCE_API_SECRET
```
Windows:
```bat
copy .env.example .env
```

> Khóa lấy ở https://testnet.binance.vision. Tệp `.env` không bị đẩy lên GitHub.

**4. Chạy kiểm tra**
```bash
python -m scripts.check_connection
```

Nếu thấy giá BTC/USDT (và số dư nếu đã điền khóa) in ra → kết nối OK.

---

## Chạy backtest (bước 2)

Sau khi đã cài thư viện như trên, chạy:
```bash
python -m scripts.run_backtest
```
Script lấy nến lịch sử, chạy chiến lược EMA Crossover và in báo cáo (lợi nhuận, tỷ lệ
thắng, sụt vốn tối đa...) kèm giải thích ý nghĩa từng con số. Lấy nến không cần khóa API.

Muốn kiểm tra nhanh không cần mạng:
```bash
python -m tests.test_backtest
```

---

## Dashboard nghịch chiến lược (phòng lab backtest)

Giao diện web để kéo thanh trượt đổi tham số và xem kết quả đổi ngay (biểu đồ giá có
đánh dấu lệnh, đường vốn, bảng lệnh).

```bash
streamlit run dashboard/app.py
```
Windows có thể bấm đúp `run_dashboard.bat`. Trình duyệt sẽ tự mở ở http://localhost:8501.

---

## Chạy bot (bước 3)

Bot có 2 chế độ (đặt trong `config/config.yaml`, mục `execution.mode`):
- **`paper`** *(mặc định)* — mô phỏng, KHÔNG đặt lệnh thật. Chạy xem bot cư xử trước.
- **`testnet`** — đặt lệnh THẬT trên Binance Testnet (tiền ảo). Cần điền khóa trong `.env`.

Chạy vòng lặp:
```bash
python -m bot.main
```
Bot sẽ: mỗi 60 giây lấy nến → ra tín hiệu → kiểm rủi ro & cầu dao ngắt → mở/đóng lệnh →
lưu trạng thái vào `data/bot.db`. Nhấn `Ctrl+C` để dừng. Khởi động lại sẽ đọc lại trạng thái cũ.

Dừng khẩn (đóng mọi lệnh rồi dừng ở chu kỳ kế tiếp):
```bash
python -m scripts.killswitch on     # bật;  off = tắt;  status = xem trạng thái
```

Kiểm thử logic (không cần mạng):
```bash
python -m tests.test_live_logic
```

## Lời giải thích của bot (bước 4)

Mỗi khi mở/đóng lệnh, bot sinh một **lời giải thích dễ hiểu** (vì sao vào/ra, bài học).
- Có `OPENAI_API_KEY` trong `.env` → dùng OpenAI viết lời giải thích tự nhiên.
- Không có khóa (hoặc OpenAI lỗi) → tự dùng **khuôn mẫu** có sẵn (không cần mạng).

LLM **chỉ giải thích**, không quyết định giao dịch. Lời giải thích hiện ở tab "Theo dõi Bot"
trên dashboard. Bật/tắt và đổi model trong `config/config.yaml` mục `explain`.

Dashboard giờ có 2 tab: **Phòng Lab Backtest** (nghịch chiến lược) và **Theo dõi Bot**
(vốn, lệnh đang mở, lịch sử, lời giải thích, nút dừng khẩn).

## Cấu hình

Mọi tham số (cặp coin, khung thời gian, ngưỡng rủi ro, chế độ chạy...) nằm trong
`config/config.yaml`. Không cần sửa code để đổi tham số.
