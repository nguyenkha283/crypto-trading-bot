"""Chạy backtest chiến lược EMA Crossover trên nến lịch sử và in báo cáo dễ hiểu.

Cách chạy (từ thư mục gốc dự án):
    python -m scripts.run_backtest

Lấy nến từ sàn (công khai, không cần khóa), chạy chiến lược, rồi in các chỉ số
kèm giải thích ý nghĩa cho người mới.
"""
from __future__ import annotations

from bot.config_loader import load_config
from bot.data.market_data import get_candles
from bot.exchange.binance_exchange import create_exchange
from bot.risk.risk_manager import RiskManager
from bot.strategy.ema_crossover import EMACrossover
from backtest.backtester import run_backtest


def print_report(symbol, timeframe, strat, result) -> None:
    print("\n" + "=" * 60)
    print(f" BÁO CÁO BACKTEST — {symbol} · khung {timeframe}")
    print(f" Chiến lược: EMA Crossover ({strat.ema_fast}/{strat.ema_slow})")
    print("=" * 60)

    print(f"\n  Vốn ban đầu : {result.initial_capital:>12,.2f} USDT")
    print(f"  Vốn cuối    : {result.final_capital:>12,.2f} USDT")
    sign = "+" if result.total_return_pct >= 0 else ""
    print(f"  Lợi nhuận   : {sign}{result.total_return_pct:>11.2f} %")

    print(f"\n  Số lệnh         : {result.num_trades}")
    print(f"  Thắng / Thua    : {result.wins} / {result.losses}")
    print(f"  Tỷ lệ thắng     : {result.win_rate:.1f} %")
    pf = result.profit_factor
    pf_str = "∞" if pf == float("inf") else f"{pf:.2f}"
    print(f"  Profit factor   : {pf_str}")
    print(f"  Sụt vốn tối đa  : {result.max_drawdown_pct:.2f} %")
    print(f"  Chuỗi thua dài  : {result.longest_losing_streak} lệnh")

    # Thống kê lý do thoát lệnh
    reasons: dict[str, int] = {}
    for t in result.trades:
        reasons[t.reason] = reasons.get(t.reason, 0) + 1
    if reasons:
        label = {"TP": "chạm chốt lời", "SL": "chạm cắt lỗ",
                 "cross": "cắt xuống", "end": "hết dữ liệu"}
        parts = [f"{label.get(k, k)}: {v}" for k, v in reasons.items()]
        print(f"  Lý do thoát     : " + ", ".join(parts))

    _print_learning_notes(result)


def _print_learning_notes(result) -> None:
    print("\n  ─ Đọc hiểu các con số ─")
    print("  • Tỷ lệ thắng CAO chưa chắc tốt: thua 1 lệnh to vẫn có thể âm tổng thể.")
    print("  • Profit factor = tổng lời / tổng lỗ. >1 là có lãi; ~1.5+ là ổn.")
    print("  • Sụt vốn tối đa cho biết lúc tệ nhất tài khoản mất bao nhiêu từ đỉnh.")
    print("  • Nhớ: một chiến lược theo xu hướng như EMA thường LỖ khi thị trường đi ngang,")
    print("    và LỜI khi có xu hướng rõ. Kết quả phụ thuộc giai đoạn dữ liệu backtest.")
    if result.num_trades == 0:
        print("\n  (Không có lệnh nào: giai đoạn này không có giao cắt, hoặc dữ liệu quá ngắn.)")


def main() -> None:
    config = load_config()
    exchange = create_exchange(config)
    market = config["market"]
    symbol = market["pairs"][0]
    timeframe = market["timeframe"]
    bt_cfg = config.get("backtest", {})
    limit = bt_cfg.get("candles", 1000)

    print(f"Đang lấy {limit} nến {timeframe} của {symbol} để backtest ...")
    try:
        df = get_candles(exchange, symbol, timeframe=timeframe, limit=limit)
    except Exception as e:  # noqa: BLE001
        print(f"✗ Không lấy được nến: {e}")
        print("→ Kiểm tra mạng rồi chạy lại.")
        return
    print(f"✓ Có {len(df)} nến (từ {df['datetime'].iloc[0]} đến {df['datetime'].iloc[-1]}).")

    strat = EMACrossover(
        ema_fast=config["strategy"]["ema_fast"],
        ema_slow=config["strategy"]["ema_slow"],
    )
    risk = RiskManager(config["risk"])
    result = run_backtest(
        df,
        strategy=strat,
        risk=risk,
        initial_capital=bt_cfg.get("initial_capital", 10000),
        fee_rate=config["risk"].get("fee_rate", 0.001),
    )
    print_report(symbol, timeframe, strat, result)


if __name__ == "__main__":
    main()
