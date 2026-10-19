#!/usr/bin/env bash
# ============================================================
# Script cài đặt bot trên máy Oracle (chạy MỘT LẦN).
# Tự dò user + đường dẫn, tạo môi trường ảo, cài thư viện,
# rồi tạo 2 dịch vụ systemd: bot và dashboard.
#
# Cách chạy (trên máy Oracle, trong thư mục repo đã clone):
#     bash deploy/install.sh
# ============================================================
set -e

# --- Dò thông tin máy ---
APP_USER="$(whoami)"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # thư mục gốc repo
PYTHON="python3"

echo "============================================"
echo " Cài đặt crypto-trading-bot"
echo " User     : $APP_USER"
echo " Thư mục  : $APP_DIR"
echo "============================================"

# --- Môi trường ảo + thư viện ---
cd "$APP_DIR"
if [ ! -d ".venv" ]; then
  echo "• Tạo môi trường ảo .venv ..."
  $PYTHON -m venv .venv
fi
echo "• Cài thư viện ..."
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

# --- Nhắc tạo .env nếu chưa có ---
if [ ! -f ".env" ]; then
  echo "⚠ Chưa có tệp .env. Tạo từ mẫu — NHỚ điền khóa trước khi chạy testnet:"
  cp .env.example .env
  echo "  (đã tạo .env, mở ra điền BINANCE_API_KEY / SECRET / OPENAI_API_KEY)"
fi

VENV_PY="$APP_DIR/.venv/bin/python"
VENV_STREAMLIT="$APP_DIR/.venv/bin/streamlit"

# --- Dịch vụ systemd: BOT ---
echo "• Tạo dịch vụ systemd: crypto-bot ..."
sudo tee /etc/systemd/system/crypto-bot.service >/dev/null <<EOF
[Unit]
Description=Crypto Trading Bot (vong lap chinh)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_PY -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# --- Dịch vụ systemd: DASHBOARD ---
# Bind 0.0.0.0 để truy cập qua Tailscale. KHÔNG mở cổng 8501 ra Internet công khai
# (để firewall Oracle đóng) — chỉ máy trong mạng Tailscale của bạn vào được.
echo "• Tạo dịch vụ systemd: crypto-dashboard ..."
sudo tee /etc/systemd/system/crypto-dashboard.service >/dev/null <<EOF
[Unit]
Description=Crypto Trading Bot Dashboard (Streamlit)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_STREAMLIT run dashboard/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# --- Bật và khởi động ---
echo "• Bật và khởi động dịch vụ ..."
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot crypto-dashboard
sudo systemctl restart crypto-bot crypto-dashboard

echo ""
echo "✓ XONG. Kiểm tra trạng thái:"
echo "    sudo systemctl status crypto-bot"
echo "    sudo systemctl status crypto-dashboard"
echo ""
echo "Xem log bot:        journalctl -u crypto-bot -f"
echo "Dashboard (Tailscale): http://<tailscale-ip-cua-may-oracle>:8501"
