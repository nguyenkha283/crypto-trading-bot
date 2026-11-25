# Bot phân tích & gợi ý giao dịch — cuộc thi demo XM

Bot phân tích thị trường và gợi ý kế hoạch lệnh cho cuộc thi demo XM (Demo Weekly, Daily Arena).
Bot **chỉ gợi ý**; mọi lệnh do người dùng tự đặt bằng tay trên trang thi. Bot không đăng nhập,
đọc hay đặt lệnh trên XM.

- User stories: https://claude.ai/artifact/DkfRptxQ98bN2bwpfQeM6u
- Cách làm việc giữa các phiên Claude: tài liệu `claude/00-to-chuc-phien-chat.md` trong project "XM Trading"

## Trạng thái

Repo vừa được dọn: code bot crypto cũ đã xóa, chỉ giữ phần tự động deploy lên Oracle.
Code bot mới sẽ được thêm theo từng user story.

## Deploy lên Oracle

Đẩy code lên `main` → GitHub Actions SSH vào máy Oracle, đồng bộ code và chạy
`deploy/install.sh`. Script cài thư viện trong `requirements.txt` rồi cài và khởi động lại
mọi dịch vụ trong `deploy/systemd/`. Hướng dẫn cài lần đầu: `deploy/README.md`.
