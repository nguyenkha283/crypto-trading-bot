#!/usr/bin/env bash
# ============================================================
# Cài đặt / cập nhật bot trên máy Oracle.
# Chạy được nhiều lần (idempotent): lần đầu chạy tay, các lần sau
# GitHub Actions tự gọi mỗi khi có code mới trên nhánh main.
#
# Việc script làm:
#   1. Tạo môi trường ảo .venv (nếu chưa có) và cài requirements.txt
#   2. Tạo .env từ .env.example nếu chưa có
#   3. Tắt các dịch vụ cũ không còn dùng (LEGACY_SERVICES)
#   4. Cài mọi dịch vụ systemd mô tả trong deploy/systemd/*.service,
#      bật và khởi động lại chúng
#
# Cách chạy (trên máy Oracle, trong thư mục repo đã clone):
#     bash deploy/install.sh
# ============================================================
set -e

APP_USER="$(whoami)"
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # thư mục gốc repo
PYTHON="python3"
UNIT_DIR="$APP_DIR/deploy/systemd"

# Dịch vụ của bot crypto cũ: tắt và gỡ nếu còn trên máy.
LEGACY_SERVICES="crypto-bot crypto-dashboard"

echo "============================================"
echo " Cài đặt bot"
echo " User     : $APP_USER"
echo " Thư mục  : $APP_DIR"
echo "============================================"

# --- 1. Môi trường ảo + thư viện ---
cd "$APP_DIR"
if [ ! -d ".venv" ]; then
  echo "• Tạo môi trường ảo .venv ..."
  $PYTHON -m venv .venv
fi
echo "• Cài thư viện ..."
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt

# --- 2. Nhắc tạo .env nếu chưa có ---
if [ ! -f ".env" ]; then
  echo "⚠ Chưa có tệp .env. Tạo từ mẫu, nhớ mở ra điền khóa:"
  cp .env.example .env
fi

# --- 3. Tắt dịch vụ cũ ---
for svc in $LEGACY_SERVICES; do
  if [ -f "/etc/systemd/system/$svc.service" ]; then
    echo "• Gỡ dịch vụ cũ: $svc ..."
    sudo systemctl disable --now "$svc" || true
    sudo rm -f "/etc/systemd/system/$svc.service"
  fi
done

# --- 4. Cài các dịch vụ trong deploy/systemd/ ---
# Mỗi tệp <tên>.service là một mẫu; các chỗ __USER__ và __APP_DIR__
# được thay bằng user và thư mục thật của máy này.
shopt -s nullglob
UNITS=("$UNIT_DIR"/*.service)
NAMES=()
for unit in "${UNITS[@]}"; do
  name="$(basename "$unit" .service)"
  NAMES+=("$name")
  echo "• Cài dịch vụ systemd: $name ..."
  sed -e "s|__USER__|$APP_USER|g" -e "s|__APP_DIR__|$APP_DIR|g" "$unit" \
    | sudo tee "/etc/systemd/system/$name.service" >/dev/null
done

sudo systemctl daemon-reload

if [ ${#NAMES[@]} -eq 0 ]; then
  echo "• Chưa có dịch vụ nào trong deploy/systemd/ — chỉ cập nhật code và thư viện."
else
  sudo systemctl enable "${NAMES[@]}"
  sudo systemctl restart "${NAMES[@]}"
  echo ""
  echo "✓ XONG. Kiểm tra: sudo systemctl status ${NAMES[*]}"
  echo "  Xem log:        journalctl -u ${NAMES[0]} -f"
fi
