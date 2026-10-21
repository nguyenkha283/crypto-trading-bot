# PROJECT HANDLE — Điểm vào ngữ cảnh dự án

> **Mục đích tệp này:** giúp bất kỳ phiên làm việc mới nào (kể cả khi chuyển đoạn chat)
> chỉ cần **đọc repo là hiểu toàn bộ ngữ cảnh** và tiếp tục được ngay, không cần chat dài.
>
> **Cách dùng khi mở chat mới:** chỉ cần nói "Đọc repo để hiểu ngữ cảnh". Trợ lý sẽ đọc
> tệp này trước, rồi đọc `system_requirements.md` và `brainstorm.md`.
>
> Cập nhật lần cuối: 2026-10-18

---

## 1. Dự án là gì (một đoạn)

Xây một **bot tự động giao dịch tiền mã hóa** để **học kiến thức giao dịch**, với điểm đặc biệt
là bot **giải thích từng quyết định** cho người dùng hiểu (lớp Explainability dùng LLM). Chạy
demo trên **Binance Testnet** trước, mục tiêu cuối là **đưa vào giao dịch thật** sau khi đã hiểu
và tin tưởng bot. Ngôn ngữ **Python**, chạy **24/7 trên Oracle Free Tier**.

## 2. Bản đồ tài liệu trong repo

| Tệp | Vai trò |
|---|---|
| `project_handle.md` | **(Tệp này)** Điểm vào — đọc đầu tiên. |
| `system_requirements.md` | **Nguồn chính thức** — các quyết định ĐÃ CHỐT. |
| `brainstorm.md` | Ý tưởng CHƯA chốt, cần bàn thêm hoặc để giai đoạn sau. |
| `ARCHITECTURE.md` | Sơ đồ kiến trúc + cấu trúc thư mục + giải thích thành phần. |

> Quy tắc: khi một ý tưởng ở `brainstorm.md` được chốt → chuyển sang `system_requirements.md`.
> Mọi thay đổi tài liệu/code đều phải **đẩy lên GitHub**.

## 3. Trạng thái hiện tại

- **Giai đoạn:** ĐÃ DEPLOY — bot chạy 24/7 trên Oracle, dashboard xem qua Tailscale
  (HTTPS qua Tailscale Serve). Đang chuyển trọng tâm sang **cải thiện chiến lược giao dịch**.
- **Đã xong:** Tài liệu + kiến trúc; kết nối GitHub; nghiên cứu deploy Oracle;
  **Bước 1** (kết nối Testnet + lấy nến — chạy OK trên máy người dùng);
  **Bước 2** (EMA Crossover + rủi ro + backtester + báo cáo — đã kiểm thử);
  **Dashboard backtest** (Streamlit+Plotly — chạy OK trên máy người dùng);
  **Bước 3** (vòng lặp chính + thực thi paper/testnet + lưu & khôi phục trạng thái +
  cầu dao ngắt + cờ dừng khẩn + log xoay vòng — đã kiểm thử logic);
  **Bước 4** (lớp giải thích OpenAI + fallback mẫu, chạy luồng nền tách khỏi giao dịch;
  dashboard thêm tab "Theo dõi Bot": vốn, lệnh mở, lịch sử, lời giải thích, nút dừng khẩn —
  đã kiểm thử logic).
- **Bước tiếp theo:** Deploy lên Oracle (venv + systemd + GitHub Actions, học từ kindle-voice
  — xem mục 6); sau đó Telegram cảnh báo. Người dùng cần tham gia: tạo VM, thêm secrets SSH +
  API key (xem mục 6).
- **Quyết định bước 3:** mặc định chế độ `paper` (mô phỏng) cho an toàn; đổi `execution.mode`
  sang `testnet` trong config để đặt lệnh thật. SL/TP quản lý trong vòng lặp (kiểm mỗi chu kỳ
  theo giá hiện tại) — hạn chế: có khe hở giá giữa 2 lần polling (chấp nhận được với khung 1h/4h).
- **Code đã có:** `bot/` (exchange, data, strategy, risk, execution, storage, explain, utils,
  main.py), `backtest/`, `dashboard/app.py` (2 tab: backtest + theo dõi bot),
  `scripts/` (check_connection, run_backtest, killswitch),
  `tests/` (test_backtest, test_live_logic, test_explainer).
- **Deploy lên Oracle:** làm **sau cùng**, khi code đã chạy ổn trên Testnet.

## 4. Các quyết định lớn đã chốt (tóm tắt — chi tiết ở `system_requirements.md`)

- **Nền tảng:** Python; chạy 24/7 trên Oracle Free Tier (máy ảo ARM Ampere A1); KHÔNG dùng Vercel.
- **Sàn:** Binance Testnet (demo) → Binance thật (sau). Tách lớp để đổi dễ.
- **Thị trường giai đoạn học:** CHỈ Spot, cặp BTC/ETH/SOL (USDT). KHÔNG Futures, KHÔNG meme coin.
- **Chiến lược:** EMA Crossover trước, rồi Grid Trading. Luôn gắn backtest.
- **Quản lý rủi ro:** khung 1h/4h; rủi ro 1%/lệnh; SL bắt buộc; R:R ≥ 1.5; tính phí 0.1%;
  3 cầu dao ngắt (lỗ ngày 3-5%, chuỗi thua 4-5, max drawdown 20%).
- **Lớp giải thích:** dùng LLM (OpenAI cho demo) nhưng CHỈ giải thích, KHÔNG quyết định; có
  fallback template; chạy luồng riêng; chỉ gọi lúc vào/đóng lệnh/báo cáo.
- **Giao diện:** Dashboard (Streamlit — đề xuất cho bản đầu, có mật khẩu) + Telegram cảnh báo khẩn.
- **Lưu trữ:** SQLite (học) → Supabase (khi lên thật, chuyển ngay khi được thông báo).
- **Độ bền:** tự khởi động lại + heartbeat + khôi phục trạng thái từ DB + công tắc dừng khẩn.
- **Dữ liệu:** polling (không WebSocket); lưu nến lịch sử vào DB; có phòng lab mô phỏng offline.

## 4b. Môi trường

- **Máy phát triển của người dùng:** Windows (dùng lệnh Windows khi hướng dẫn chạy).
- **Máy chạy 24/7:** Oracle Free Tier (Linux) — deploy theo mô hình ở mục 6.

## 5. Quy ước làm việc (cách cộng tác — áp dụng cho mọi phiên)

1. **Hỏi xác nhận các điểm chưa rõ trước khi thực hiện.** Nếu một yêu cầu còn mơ hồ, xác nhận
   lại trước, không vội làm phần rõ trong khi chờ làm rõ phần chưa rõ.
2. **Đóng vai chuyên gia giao dịch, thiên về phản biện** hơn là đồng tình — chỉ ra chỗ rủi ro.
3. **Giải thích cực kỳ dễ hiểu** cho người mới (mục tiêu của dự án là HỌC).
4. **Hạn chế từ tiếng Anh** nếu không phải thuật ngữ chuyên môn.
5. **Code:** chỉ tóm tắt chức năng đã làm, không giải thích dài dòng.
6. **Mọi thay đổi tài liệu/code đều đẩy lên GitHub.**
7. Nếu một yêu cầu khó vượt khả năng model/effort hiện tại → gợi ý nâng model/effort thay vì cố.

## 6. Cách deploy lên Oracle (học từ repo kindle-voice)

Người dùng đã có một repo chạy sẵn trên Oracle là `kindle-voice`, dùng mô hình deploy sau — bot
này sẽ **tái sử dụng đúng mô hình này** (đã kiểm chứng, ít rủi ro):

- Trên máy Oracle: repo được clone tại `~/<tên-repo>`, có môi trường ảo `.venv`.
- App chạy như một **dịch vụ systemd** (tự bật lại khi lỗi/reboot).
- **Tự động deploy:** tệp `.github/workflows/deploy.yml` — mỗi khi push vào nhánh `main`,
  GitHub Actions dùng SSH vào máy Oracle → `git pull` → cài lại thư viện → `systemctl restart`.
- **Khóa bí mật cần có trên GitHub (Settings → Secrets):** `ORACLE_HOST`, `ORACLE_USER`,
  `ORACLE_SSH_KEY`. Người dùng tự thêm các khóa này (trợ lý không nhập hộ khóa/bí mật).

> Khác biệt cần lưu ý: `kindle-voice` là web server chạy theo yêu cầu; bot giao dịch là tiến
> trình chạy liên tục — nhưng cùng mô hình venv + systemd + Actions là dùng được.

**ĐÃ DỰNG XONG phần deploy** (xem `deploy/README.md`):
- Chạy chung VM với kindle-voice; truy cập dashboard qua **Tailscale** (mạng riêng, không mở
  cổng ra Internet — thay cho phương án mật khẩu/nginx).
- `deploy/install.sh`: tự dò user/path, tạo venv, sinh 2 dịch vụ systemd (`crypto-bot`,
  `crypto-dashboard`), bật và khởi động.
- `.github/workflows/deploy.yml`: push main → SSH vào Oracle (qua IP công khai, như
  kindle-voice) → pull + cài + restart 2 dịch vụ.
- Secrets GitHub cần: `ORACLE_HOST`, `ORACLE_USER`, `ORACLE_SSH_KEY` (dùng lại của kindle-voice).
- Dashboard bind 0.0.0.0:8501 nhưng chỉ vào được qua Tailscale IP (100.x).

## 7. Việc đang mở / cần quyết tiếp

- Vẽ sơ đồ kiến trúc + cấu trúc thư mục (bước kế tiếp).
- Chốt framework dashboard (đề xuất: Streamlit).
- Ước lượng chi phí gọi LLM; thiết kế prompt giải thích.
- Xem thêm `brainstorm.md` để biết các mục chưa chốt.
