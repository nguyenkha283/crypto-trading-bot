"""Script kiểm tra kết nối — chạy đầu tiên để chắc mọi thứ hoạt động.

Việc nó làm:
  1. Đọc cấu hình.
  2. Kết nối sàn (Binance Testnet).
  3. Lấy nến gần nhất của cặp đầu tiên và in ra (dữ liệu công khai, không cần khóa).
  4. Nếu đã điền khóa API: thử lấy số dư testnet và in các tài sản có số dư.

Cách chạy (từ thư mục gốc dự án):
    python -m scripts.check_connection
"""
from __future__ import annotations

from bot.config_loader import load_config, has_binance_keys
from bot.data.market_data import get_candles
from bot.exchange.binance_exchange import create_exchange


def main() -> None:
    print("=" * 56)
    print(" KIỂM TRA KẾT NỐI BOT GIAO DỊCH")
    print("=" * 56)

    config = load_config()
    exchange = create_exchange(config)
    print(f"• Sàn kết nối: {exchange.describe()}")

    market = config["market"]
    symbol = market["pairs"][0]
    timeframe = market["timeframe"]
    limit = market.get("candles_limit", 200)

    # --- Bước 1: lấy nến (công khai) ---
    print(f"\n• Đang lấy {limit} nến {timeframe} của {symbol} ...")
    try:
        df = get_candles(exchange, symbol, timeframe=timeframe, limit=limit)
    except Exception as e:  # noqa: BLE001 - in lỗi thân thiện cho người mới
        print(f"  ✗ Không lấy được nến: {e}")
        print("  → Kiểm tra kết nối mạng, hoặc thử lại sau (testnet đôi khi bận).")
        return

    print(f"  ✓ Lấy được {len(df)} nến.")
    last = df.iloc[-1]
    print(f"\n  5 nến gần nhất ({symbol}, {timeframe}):")
    print("  " + "-" * 50)
    print(f"  {'Thời gian':<20}{'Giá đóng':>12}{'Khối lượng':>16}")
    for _, row in df.tail(5).iterrows():
        t = row["datetime"].strftime("%Y-%m-%d %H:%M")
        print(f"  {t:<20}{row['close']:>12.2f}{row['volume']:>16.2f}")
    print("  " + "-" * 50)
    print(f"  Giá hiện tại (nến mới nhất đóng ở): {last['close']:.2f} USDT")

    # --- Bước 2: số dư (cần khóa) ---
    print()
    if not has_binance_keys(config):
        print("• Chưa điền khóa API → bỏ qua phần số dư.")
        print("  (Lấy nến không cần khóa; số dư & đặt lệnh mới cần.)")
        print("  Để xem số dư: sao chép .env.example thành .env rồi điền khóa.")
    else:
        print("• Đã có khóa API → đang lấy số dư testnet ...")
        try:
            balance = exchange.fetch_balance()
            totals = {k: v for k, v in balance.get("total", {}).items() if v and v > 0}
            if totals:
                print("  ✓ Số dư (chỉ hiện tài sản > 0):")
                for asset, amount in sorted(totals.items()):
                    print(f"    {asset:<8}{amount:>18.8f}")
            else:
                print("  ✓ Kết nối được nhưng chưa có tài sản nào > 0.")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ Không lấy được số dư: {e}")
            print("  → Kiểm tra lại khóa API (đúng khóa testnet? còn hiệu lực?).")

    print("\n✓ Xong. Nếu thấy giá và/hoặc số dư ở trên là kết nối đã OK.")


if __name__ == "__main__":
    main()
