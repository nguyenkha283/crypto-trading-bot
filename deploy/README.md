# Deploy lên Oracle

Mỗi lần đẩy code lên `main`, GitHub Actions SSH vào máy Oracle, đồng bộ code
(`git reset --hard origin/main`) rồi chạy `deploy/install.sh`.

> Các bước có dấu **[BẠN]** chỉ bạn làm được (liên quan khóa bí mật / tài khoản).

## Cài lần đầu (máy đã chạy bot crypto cũ thì bỏ qua bước 1–2)

1. **[BẠN]** Lấy mã nguồn về máy Oracle:
   ```bash
   cd ~
   git clone https://github.com/nguyenkha283/crypto-trading-bot
   cd crypto-trading-bot
   ```
2. **[BẠN]** Tạo và điền `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
3. Chạy cài đặt:
   ```bash
   bash deploy/install.sh
   ```

## Bật tự động deploy — [BẠN]

GitHub → repo → **Settings → Secrets and variables → Actions**, cần 3 secret:

| Secret | Giá trị |
|---|---|
| `ORACLE_HOST` | IP công khai của máy Oracle |
| `ORACLE_USER` | User trên máy Oracle (thường `ubuntu` hoặc `opc`) |
| `ORACLE_SSH_KEY` | Khóa SSH riêng để đăng nhập máy Oracle |

Chạy tay: tab **Actions** → "Deploy to Oracle" → **Run workflow**.

## Thêm dịch vụ chạy nền

Thêm tệp `deploy/systemd/<tên>.service` (xem `deploy/systemd/README.md`), đẩy lên `main`.
Lần deploy sau, dịch vụ được cài, bật và khởi động.

## Vận hành

| Việc | Lệnh |
|---|---|
| Xem log | `journalctl -u <tên-dịch-vụ> -f` |
| Khởi động lại | `sudo systemctl restart <tên-dịch-vụ>` |
| Dừng | `sudo systemctl stop <tên-dịch-vụ>` |

## Lưu ý

- Script dùng `sudo systemctl`, cần sudo không mật khẩu trên máy Oracle.
- `.env`, `data/`, `logs/` nằm ngoài git nên không bị deploy ghi đè. Dữ liệu cũ của bot
  crypto (`data/bot.db`) vẫn còn trên máy; xóa tay nếu không cần.
- Lần deploy đầu sau khi dọn repo sẽ tắt và gỡ 2 dịch vụ cũ `crypto-bot`, `crypto-dashboard`.
