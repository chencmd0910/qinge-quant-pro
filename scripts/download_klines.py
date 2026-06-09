#!/usr/bin/env python3
"""
青鳄量化 - 全A股K线数据采集脚本
数据源：腾讯K线（单次请求即可获取全部历史）
存储：Parquet 分片（每只股票一个文件）+ SQLite 元数据索引

预估：
- 5000只股票 × 500天 = 250万行
- Parquet 压缩后 ≈ 80-120MB
- 下载时间 ≈ 5-10分钟（20线程）
"""
import requests
import pandas as pd
import sqlite3
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# ===== 配置 =====
DATA_DIR = Path(__file__).parent / "klines"
PARQUET_DIR = DATA_DIR / "parquet"
INDEX_DB = DATA_DIR / "kline_index.db"
START_DATE = (datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")
MAX_WORKERS = 20  # 下载线程数
BATCH_SLEEP = 0.02  # 批次间暂停（秒），避免被限流

# ===== 创建目录 =====
PARQUET_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("  青鳄量化 - A股K线数据采集")
print(f"  时间范围: {START_DATE} ~ {END_DATE}")
print(f"  存储路径: {PARQUET_DIR}")
print("=" * 60)


def get_stock_list():
    """获取全A股股票列表"""
    print("\n[1/4] 获取股票列表...")
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        stocks = []
        for _, row in df.iterrows():
            code = row['code']
            name = row['name']
            if not code.startswith(('6', '0', '3', '8', '4')):
                continue
            if 'ST' in name or '退' in name or 'N' == name[0]:
                continue
            stocks.append((code, name))
        print(f"    共 {len(stocks)} 只股票")
        return stocks
    except Exception as e:
        print(f"    akshare失败: {e}")
        print("    使用备用方式获取...")
        return get_stock_list_fallback()


def get_stock_list_fallback():
    """备用：从东方财富API获取股票列表"""
    stocks = []
    markets = [
        ('sh', 'm:1 t:2'),
        ('sz', 'm:0 t:6'),
        ('sz', 'm:0 t:13'),
    ]
    for prefix, fs in markets:
        page = 1
        while True:
            try:
                url = f"https://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    'pn': page, 'pz': 500, 'po': 1, 'np': 1,
                    'fltt': 2, 'invt': 2, 'fid': 'f3',
                    'fs': f'{fs}', 'fields': 'f12,f14',
                }
                r = requests.get(url, params=params, timeout=15)
                data = r.json()
                items = data.get('data', {}).get('diff', [])
                if not items:
                    break
                for item in items:
                    code = item.get('f12', '')
                    name = item.get('f14', '')
                    if code and not any(kw in name for kw in ['ST', '退', 'N']):
                        if prefix == 'sh' or code.startswith('0') or code.startswith('3'):
                            stocks.append((code, name))
                if len(items) < 500:
                    break
                page += 1
                time.sleep(0.1)
            except:
                break
    print(f"    共 {len(stocks)} 只股票")
    return stocks


def fetch_kline(code):
    """获取单只股票的全部日K线（腾讯API）"""
    prefix = 'sh' if code.startswith(('6', '9')) else 'sz'
    days = 750  # 2年+缓冲
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix}{code},day,,,{days},qfq"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        kline = data.get('data', {}).get(f'{prefix}{code}', {})
        kdata = kline.get('qfqday') or kline.get('day') or []
        if not kdata:
            return None

        rows = []
        for k in kdata:
            date = k[0]
            if date < START_DATE or date > END_DATE:
                continue
            rows.append({
                'date': date,
                'open': float(k[1]),
                'close': float(k[2]),
                'high': float(k[3]),
                'low': float(k[4]),
                'volume': float(k[5]) if len(k) > 5 else 0,
            })
        if not rows:
            return None

        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except:
        return None


def download_all(stocks):
    """批量下载所有股票的K线数据"""
    print(f"\n[2/4] 下载K线数据 ({len(stocks)} 只股票, {MAX_WORKERS}线程)...")
    results = {}
    failed = []
    downloaded = 0
    total = len(stocks)
    last_report = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_kline, code): (code, name) for code, name in stocks}
        for future in as_completed(futures):
            code, name = futures[future]
            try:
                df = future.result(timeout=15)
                if df is not None and len(df) > 0:
                    results[code] = (name, df)
                    downloaded += 1
                else:
                    failed.append(code)
            except:
                failed.append(code)

            # 进度报告
            now = time.time()
            if now - last_report > 2:
                pct = (downloaded + len(failed)) * 100 / total
                print(f"\r    进度: {downloaded + len(failed)}/{total} ({pct:.1f}%)  "
                      f"成功:{downloaded} 失败:{len(failed)}", end='')
                last_report = now

    print(f"\r    完成! 成功:{downloaded} 失败:{len(failed)}")
    return results, failed


def save_parquet(results):
    """保存为Parquet分片文件"""
    print(f"\n[3/4] 保存Parquet文件...")
    count = 0
    for code, (name, df) in results.items():
        filepath = PARQUET_DIR / f"{code}.parquet"
        # 添加代码列方便后续查询
        df = df.copy()
        df['code'] = code
        df['name'] = name
        df.to_parquet(filepath, index=False, compression='zstd')
        count += 1

    total_size = sum(f.stat().st_size for f in PARQUET_DIR.glob("*.parquet"))
    print(f"    保存了 {count} 个文件, 总大小: {total_size / 1024 / 1024:.1f} MB")
    return count


def build_index(results):
    """构建SQLite元数据索引"""
    print(f"\n[4/4] 构建索引...")
    # 删除旧索引
    if INDEX_DB.exists():
        INDEX_DB.unlink()

    db = sqlite3.connect(str(INDEX_DB))
    db.execute("""
        CREATE TABLE kline_index (
            code TEXT PRIMARY KEY,
            name TEXT,
            start_date TEXT,
            end_date TEXT,
            row_count INTEGER,
            file_size INTEGER,
            parquet_file TEXT
        )
    """)
    db.execute("""
        CREATE TABLE trade_calendar (
            trade_date TEXT PRIMARY KEY,
            stock_count INTEGER
        )
    """)

    for code, (name, df) in results.items():
        filepath = PARQUET_DIR / f"{code}.parquet"
        file_size = filepath.stat().st_size
        db.execute(
            "INSERT INTO kline_index VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, name, str(df['date'].min().date()), str(df['date'].max().date()),
             len(df), file_size, f"{code}.parquet")
        )

    # 交易日历
    all_dates = set()
    for _, (_, df) in results.items():
        all_dates.update(df['date'].dt.strftime('%Y-%m-%d').tolist())
    for d in sorted(all_dates):
        db.execute("INSERT INTO trade_calendar VALUES (?, ?)", (d, len(results)))

    db.commit()

    # 统计
    total_rows = db.execute("SELECT SUM(row_count) FROM kline_index").fetchone()[0]
    stock_cnt = db.execute("SELECT COUNT(*) FROM kline_index").fetchone()[0]
    print(f"    索引: {stock_cnt} 只股票, {total_rows:,} 行")
    print(f"    交易日: {len(all_dates)} 天")
    db.close()


def main():
    t0 = time.time()

    # 1. 股票列表
    stocks = get_stock_list()
    if not stocks:
        print("❌ 获取股票列表失败！")
        sys.exit(1)

    # 2. 下载K线
    results, failed = download_all(stocks)
    if not results:
        print("❌ 下载全部失败！")
        sys.exit(1)

    # 3. 保存Parquet
    saved = save_parquet(results)

    # 4. 构建索引
    build_index(results)

    # 汇总
    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  ✅ 采集完成!")
    print(f"  股票数: {saved} 只")
    print(f"  失败: {len(failed)} 只")
    print(f"  耗时: {elapsed:.0f} 秒")
    print(f"  数据目录: {PARQUET_DIR}")
    print(f"  索引文件: {INDEX_DB}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
