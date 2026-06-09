from app.paper_trading.live_runner import KLINE_DIR
import os
print(f"KLINE_DIR={KLINE_DIR}")
print(f"exists={os.path.exists(KLINE_DIR)}")
if os.path.exists(KLINE_DIR):
    fs = [f for f in os.listdir(KLINE_DIR) if f.endswith('.parquet')]
    print(f"files={len(fs)} sample={fs[:3]}")
