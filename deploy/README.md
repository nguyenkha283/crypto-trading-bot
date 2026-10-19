# Hướng dẫn deploy lên Oracle (chạy bot 24/7)

> Mô hình: chạy **chung máy ảo với `kindle-voice`**, truy cập dashboard qua **Tailscale**
> (mạng riêng, không mở cổng ra Internet). Tự động deploy bằng **GitHub Actions**: mỗi khi
> đẩy code lên `main`, máy Oracle tự cập nhật.
>
> 🧩 Các bước có dấu **[BẠN]** là việc chỉ bạn làm được (liên quan khóa bí mật / tài khoản).
> Trợ lý không nhập hộ khóa.

---

## Tổng quan 2 dịch vụ

Sau khi cài, trên máy Oracle sẽ có 2 dịch vụ chạy nền (systemd), tự bật lại khi lỗi/reboot:
- **`crypto-bot`** — vòng lặp giao dịch (`python -m bot.main`).
- **`crypto-dashboard`** — dashboard Streamlit (cổng 8501, xem qua Tailscale).

Cả hai dùng chung tệp `data/bot.db` nên dashboard thấy đúng trạng thái bot, và nút dừng
khẩn trên dashboard điều khiển được bot.

---

## Bước 1 — [BẠN] Cài Tailscale (nếu chưa có)

Mục tiêu: máy Oracle và máy bạn cùng một mạng riêng, để xem dashboard an toàn.

1. Trên **máy Oracle** (qua SSH):
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
   Màn hình in ra một đường link — mở link đó bằng trình duyệt và đăng nhập Tailscale để
   kết nối máy này vào mạng của bạn.
2. Trên **máy bạn (Windows)**: cài Tailscale (tailscale.com/download), đăng nhập cùng tài khoản.
3. Lấy địa chỉ Tailscale của máy Oracle:
   ```bash
   tailscale ip -4
   ```
   Ghi lại địa chỉ dạng `100.x.y.z` — đây là địa chỉ để mở dashboard.

> Vì sao an toàn: cổng 8501 KHÔNG mở ra Internet. Chỉ máy trong mạng Tailscale của bạn
> mới vào được dashboard, qua địa chỉ `100.x.y.z`.

## Bước 2 — [BẠN] Lấy mã nguồn về máy Oracle

```bash
cd ~
git clone https://github.com/nguyenkha283/crypto-trading-bot
cd crypto-trading-bot
```

## Bước 3 — [BẠN] Điền khóa vào tệp .env

```bash
cp .env.example .env
nano .env     # điền khóa, xong bấm Ctrl+O để lưu, Ctrl+X để thoát
```
Điền:
- `BINANCE_API_KEY`, `BINANCE_API_SECRET` — khóa Binance **Testnet**.
- `OPENAI_API_KEY` — nếu muốn bot giải thích bằng AI (bỏ trống cũng được, sẽ dùng mẫu).

> Tệp `.env` đã được `.gitignore` bỏ qua nên không bao giờ bị đẩy lên GitHub.

## Bước 4 — Chạy script cài đặt

```bash
bash deploy/install.sh
```
Script tự: tạo môi trường ảo, cài thư viện, tạo 2 dịch vụ systemd, bật và khởi động.

Kiểm tra:
```bash
sudo systemctl status crypto-bot
sudo systemctl status crypto-dashboard
journalctl -u crypto-bot -f      # xem log bot chạy (Ctrl+C để thoát xem)
```

## Bước 5 — Mở dashboard (qua Tailscale)

Trên trình duyệt **máy bạn**, mở:
```
http://<tailscale-ip-oracle>:8501
```
(thay bằng địa chỉ `100.x.y.z` lấy ở Bước 1). Bạn sẽ thấy dashboard như chạy ở nhà.

---

## Bước 6 — [BẠN] Bật tự động deploy (GitHub Actions)

Để mỗi lần đẩy code mới lên `main`, máy Oracle tự cập nhật. Cần thêm 3 "khóa bí mật" vào
GitHub: vào repo trên GitHub → **Settings → Secrets and variables → Actions → New repository secret**:

| Tên secret | Giá trị |
|---|---|
| `ORACLE_HOST` | Địa chỉ IP công khai của máy Oracle (dùng để GitHub SSH vào — giống kindle-voice) |
| `ORACLE_USER` | Tên user trên máy Oracle (thường `ubuntu` hoặc `opc`) |
| `ORACLE_SSH_KEY` | Nội dung khóa SSH riêng (private key) để đăng nhập máy Oracle |

> Đây chính là 3 secret mà `kindle-voice` đang dùng — nếu bot chạy chung máy, bạn có thể
> dùng lại đúng các giá trị đó.
>
> ⚠️ GitHub SSH vào qua **IP công khai** (cổng 22), còn dashboard xem qua **Tailscale**.
> Hai việc tách biệt — không ảnh hưởng nhau.

Sau khi thêm secret: mỗi `git push` lên `main` sẽ tự chạy deploy. Muốn bấm chạy tay: vào
tab **Actions** trên GitHub, chọn workflow "Deploy to Oracle" → **Run workflow**.

---

## Vận hành hằng ngày

| Việc | Lệnh / cách làm |
|---|---|
| Xem bot đang chạy | `journalctl -u crypto-bot -f` hoặc mở dashboard |
| Khởi động lại thủ công | `sudo systemctl restart crypto-bot crypto-dashboard` |
| Dừng khẩn | Bấm nút trên dashboard (tab "Theo dõi Bot"), hoặc `sudo systemctl stop crypto-bot` |
| Đổi chế độ paper ↔ testnet | Sửa `config/config.yaml` mục `execution.mode`, rồi `git push` (tự deploy) |

## Lưu ý quan trọng

- **Chạy thử `paper` trước** trên Oracle vài ngày cho chắc, rồi mới đổi sang `testnet`.
- **sudo không mật khẩu**: script dùng `sudo systemctl`. Máy Oracle chạy kindle-voice thường
  đã cấu hình sẵn điều này (deploy của kindle-voice cũng dùng `sudo`).
- **Khi lên giao dịch THẬT** (sau này): đổi sang Supabase, bật quyền rút tiền OFF trên sàn,
  và cân nhắc đặt lệnh cắt lỗ thật trên sàn (xem ghi chú trong `project_handle.md`).
