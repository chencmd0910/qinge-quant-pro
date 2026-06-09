import pandas as pd, os, sys

parquet_dir = "/opt/qinge-quant-pro/backend/data/klines/parquet"
files = sorted([f for f in os.listdir(parquet_dir) if f.endswith('.parquet')])
print(f"文件总数: {len(files)}")

# 取第一个文件
f = os.path.join(parquet_dir, files[0])
d = pd.read_parquet(f)
print(f"\n文件: {files[0]}")
print(f"列: {d.columns.tolist()}")
print(f"行数: {len(d)}")
print(f"索引名: {d.index.name}")
print(f"索引类型: {d.index.dtype}")
print(f"日期范围: {d.index[0]} ~ {d.index[-1]}")
print(f"\n前2行:\n{d.head(2)}")
print(f"\n后2行:\n{d.tail(2)}")

# 检查volume字段
if 'volume' in d.columns:
    print(f"\nvolume 非空率: {d['volume'].notna().sum()}/{len(d)}")
