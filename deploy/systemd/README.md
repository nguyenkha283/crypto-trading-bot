# Dịch vụ systemd

Mỗi tệp `<tên>.service` trong thư mục này là một dịch vụ chạy nền trên máy Oracle.
`deploy/install.sh` tự cài, bật và khởi động lại tất cả mỗi lần deploy.

Trong tệp mẫu, dùng hai chỗ giữ chỗ:

- `__USER__` — user trên máy Oracle
- `__APP_DIR__` — thư mục gốc repo trên máy Oracle

Ví dụ `signal-alert.service`:

```ini
[Unit]
Description=Bot canh bao tin hieu
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=__USER__
WorkingDirectory=__APP_DIR__
EnvironmentFile=__APP_DIR__/.env
ExecStart=__APP_DIR__/.venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Xóa một tệp ở đây không tự gỡ dịch vụ trên máy; thêm tên đó vào `LEGACY_SERVICES`
trong `deploy/install.sh` để gỡ.
