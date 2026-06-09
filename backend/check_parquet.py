import pandas as pd, os

# 检查本地 parquet 文件格式
local_dir = r"C:\Users\哒哒哒\.openclaw\workspace\qinge-quant-pro\backend\data\klines\parquet"
if os.path.exists(local_dir):
    files = [f for f in os.listdir(local_dir) if f.endswith('.parquet')]
    if files:
        f = os.path.join(local_dir, files[0])
        d = pd.read_parquet(f)
        print(f"文件: {files[0]}")
        print(f"列: {d.columns.tolist()}")
        print(f"行数: {len(d)}")
        print(f"索引: {d.index.name}")
        print(f"前2行:\n{d.head(2)}")
        print(f"后2行:\n{d.tail(2)}")
    else:
        print("本地无parquet文件")
else:
    # 从服务器读
    print("本地路径不存在，用服务器...")
