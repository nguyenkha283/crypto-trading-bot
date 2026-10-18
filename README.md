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
- [ ] Bước 3: thực thi lệnh trên Testnet + vòng lặp chính
- [ ] Bước 4: lớp giải thích + dashboard theo dõi bot chạy + an toàn

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

## Cấu hình

Mọi tham số (cặp coin, khung thời gian, ngưỡng rủi ro...) nằm trong `config/config.yaml`.
Không cần sửa code để đổi tham số.
