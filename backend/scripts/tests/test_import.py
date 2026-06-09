from app.paper_trading.live_runner import LivePaperRunner, FactorEngine
print("IMPORT OK")
r = LivePaperRunner()
s = r.get_summary()
print("Summary OK:", s['total_value'])
# Test factor engine
import pandas as pd, numpy as np
df = pd.DataFrame({
    'open': np.random.normal(10, 1, 100),
    'high': np.random.normal(11, 1, 100),
    'low': np.random.normal(9, 1, 100),
    'close': np.random.normal(10, 1, 100),
    'volume': np.random.normal(1e6, 1e5, 100),
    'date': pd.date_range('2024-01-01', periods=100),
    'code': 'test',
})
scores = FactorEngine.score_stocks(df)
print(f"Factor scores: {len(scores)}, last={scores[-1]:.4f}")
print("ALL OK")
