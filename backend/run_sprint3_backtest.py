"""ETF轮动回测 - Sprint-3 Task-1

使用从阿里云获取的真实指数数据（代理ETF）进行回测。
指数收益 ≈ ETF收益（误差<0.5%/年）。
"""
import sys, json, os
from datetime import datetime
sys.path.insert(0, '.')

from app.strategy_engine.strategies.etf_rotation.strategy import ETFRotationStrategy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, 'etf_data.json')

START_DATE = "2018-01-01"
END_DATE = "2026-06-06"
COMMISSION = 0.0003  # 万3
SLIPPAGE = 0.001     # 0.1%

print("=" * 60)
print("ETF Rotation Backtest - Sprint-3")
print("=" * 60)
print(f"  Data source: baostock index (proxy for ETF)")
print(f"  Period: {START_DATE} to {END_DATE}")
print(f"  Commission: {COMMISSION*10000:.0f}/10000 (per side)")
print(f"  Slippage: {SLIPPAGE*100:.1f}%")
print()

# 加载数据
print("Loading data...")
with open(DATA_FILE, 'r') as f:
    raw_data = json.load(f)

all_data = {}
for symbol, bars in raw_data.items():
    data = [(b['date'], b['close']) for b in bars if b['close'] > 0]
    all_data[symbol] = data
    print(f"  {symbol}: {len(data)} bars ({data[0][0]} to {data[-1][0]})")

available_symbols = list(all_data.keys())
print(f"\nAvailable: {available_symbols}")

# 构建日期索引
all_dates = sorted(set(d for sym_data in all_data.values() for d, _ in sym_data))
print(f"Trading days: {len(all_dates)}")

price_index = {}
for symbol in available_symbols:
    price_index[symbol] = {d: c for d, c in all_data[symbol]}

# 运行策略
print("\nRunning backtest...")
strategy = ETFRotationStrategy(
    symbols=available_symbols,
    lookback=60,
    commission_rate=COMMISSION,
    slippage_pct=SLIPPAGE,
)
strategy.initialize(initial_cash=1_000_000)

pending_signal = None

for date_str in all_dates:
    # Execute pending signal from previous Friday (execute on Monday)
    if pending_signal:
        exec_prices = {}
        for s in available_symbols:
            p = price_index[s].get(date_str, 0)
            if p > 0:
                exec_prices[s] = p
        if exec_prices:
            strategy.execute_trade(pending_signal, date_str, exec_prices)
        pending_signal = None

    # Process bars
    for symbol in available_symbols:
        close = price_index[symbol].get(date_str, 0)
        if close > 0:
            signal = strategy.on_bar(symbol, date_str, close)
            if signal:
                pending_signal = signal

    strategy.snapshot(date_str)

# 输出结果
metrics = strategy.get_metrics()

print()
print("=" * 60)
print("BACKTEST RESULTS - ETF Rotation V1")
print("=" * 60)
print(f"  Initial Cash:    {metrics['initial_cash']:>12,.2f}")
print(f"  Final Value:     {metrics['final_value']:>12,.2f}")
print(f"  Total Return:    {metrics['total_return']:>11.2f}%")
print(f"  Annual Return:   {metrics['annual_return']:>11.2f}%")
print(f"  Max Drawdown:    {metrics['max_drawdown']:>11.2f}%")
print(f"  Sharpe Ratio:    {metrics['sharpe_ratio']:>11.2f}")
print(f"  Win Rate:        {metrics['win_rate']:>11.1f}%")
print(f"  Trade Count:     {metrics['trade_count']:>11d}")
print(f"  Trading Days:    {metrics['trading_days']:>11d}")
print(f"  Years:           {metrics['years']:>11.1f}")
print()

# 最近15笔交易
print("Recent trades (last 15):")
print("-" * 80)
print(f"{'Date':<12} {'Side':<6} {'Symbol':<12} {'Qty':>8} {'Price':>10} {'Commission':>10}")
print("-" * 80)
for t in strategy.trades[-15:]:
    print(f"{t['date']:<12} {t['side']:<6} {t['symbol']:<12} {t['quantity']:>8d} {t['price']:>10.4f} {t['commission']:>10.2f}")
print()

# 年度收益
print("Annual returns:")
equity = metrics['equity_curve']
years = {}
for e in equity:
    y = e['date'][:4]
    if y not in years:
        years[y] = {'start': e['total'], 'end': e['total']}
    years[y]['end'] = e['total']

prev_end = None
for y in sorted(years):
    yr = years[y]
    if prev_end:
        ret = (yr['end'] - prev_end) / prev_end * 100
    else:
        ret = (yr['end'] - 1000000) / 1000000 * 100
    print(f"  {y}: {ret:+.2f}%")
    prev_end = yr['end']
print()

# 保存JSON
result = {
    "strategy": "ETF Rotation V1",
    "symbols": available_symbols,
    "period": f"{START_DATE} to {END_DATE}",
    "commission": COMMISSION,
    "slippage": SLIPPAGE,
    "lookback": 60,
    "metrics": {k: v for k, v in metrics.items() if k not in ['equity_curve', 'drawdown_curve', 'trades']},
    "equity_curve_sample": metrics['equity_curve'][::max(1, len(metrics['equity_curve'])//100)],
    "drawdown_curve_sample": metrics['drawdown_curve'][::max(1, len(metrics['drawdown_curve'])//100)],
    "trades": metrics['trades'],
    "annual_returns": {y: round((years[y]['end'] - (years[str(int(y)-1)]['end'] if str(int(y)-1) in years else 1000000)) / (years[str(int(y)-1)]['end'] if str(int(y)-1) in years else 1000000) * 100, 2) for y in sorted(years)},
    "generated_at": datetime.now().isoformat(),
}

output_path = os.path.join(SCRIPT_DIR, 'backtest_result.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Result saved to: backtest_result.json")
print(f"\nBacktest complete!")
