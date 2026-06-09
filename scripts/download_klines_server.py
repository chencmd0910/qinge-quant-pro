#!/usr/bin/env python3
"""
Server-side K-line data download script
Data source: Tencent K-line API (fast, batch-friendly)
Storage: Parquet shards + SQLite index
Python 3.6+ compatible
"""
import requests
import pandas as pd
import sqlite3
import time
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Config
DATA_DIR = Path("/opt/qinge-quant-pro/backend/data")
PARQUET_DIR = DATA_DIR / "klines" / "parquet"
INDEX_DB = DATA_DIR / "klines" / "kline_index.db"
START_DATE = (datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")
MAX_WORKERS = 20
FAIL_FILE = DATA_DIR / "klines" / "failed_stocks.txt"

PARQUET_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("  A-Share K-line Data Collector")
print("  Range: {} ~ {}".format(START_DATE, END_DATE))
print("  Output: {}".format(PARQUET_DIR))
print("=" * 60)


def get_stock_list_eastmoney():
    """Get A-share stock list from EastMoney API"""
    print("\n[1/4] Getting stock list...")
    stocks = {}
    seen = set()
    for sh, fs in [("sh", "m:1 t:2"), ("sz", "m:0 t:6"), ("sz", "m:0 t:13")]:
        page = 1
        while True:
            try:
                url = "https://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    "pn": page, "pz": 500, "po": 1, "np": 1,
                    "fltt": 2, "invt": 2, "fid": "f3",
                    "fs": fs, "fields": "f12,f14",
                }
                r = requests.get(url, params=params, timeout=15)
                data = r.json()
                items = data.get("data", {}).get("diff", [])
                if not items:
                    break
                for item in items:
                    code = item.get("f12", "")
                    name = item.get("f14", "")
                    if code and code not in seen:
                        skip = any(kw in name for kw in ["ST", "退", "N"])
                        if not skip and name and name[0] != "N":
                            stocks[code] = name
                            seen.add(code)
                if len(items) < 500:
                    break
                page += 1
                time.sleep(0.15)
            except Exception as e:
                print("    EastMoney error: {}".format(e))
                break
    result = [(code, name) for code, name in stocks.items()]
    print("    {} stocks found".format(len(result)))
    return result


def fetch_kline(code):
    """Fetch daily K-line for one stock via Tencent API"""
    prefix = "sh" if code.startswith(("6", "9")) else "sz"
    days = 750
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={}{},day,,,{},qfq".format(prefix, code, days)
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        kline = data.get("data", {}).get("{}{}".format(prefix, code), {})
        kdata = kline.get("qfqday") or kline.get("day") or []
        if not kdata:
            return None

        rows = []
        for k in kdata:
            date = k[0]
            if date < START_DATE or date > END_DATE:
                continue
            try:
                rows.append({
                    "date": date,
                    "open": float(k[1]),
                    "close": float(k[2]),
                    "high": float(k[3]),
                    "low": float(k[4]),
                    "volume": float(k[5]) if len(k) > 5 else 0,
                })
            except (ValueError, IndexError):
                continue
        if not rows:
            return None

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception:
        return None


def download_all(stocks):
    """Batch download with thread pool"""
    total = len(stocks)
    print("\n[2/4] Downloading {} stocks ({} workers)...".format(total, MAX_WORKERS))
    results = {}
    failed = []
    done = [0]
    last_report = [time.time()]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_kline, code): (code, name) for code, name in stocks}
        for future in as_completed(futures):
            code, name = futures[future]
            done[0] += 1
            try:
                df = future.result(timeout=15)
                if df is not None and len(df) > 0:
                    results[code] = (name, df)
                else:
                    failed.append(code)
            except Exception:
                failed.append(code)

            # Progress
            now = time.time()
            if now - last_report[0] > 3:
                pct = done[0] * 100.0 / total
                sys.stdout.write("\r    Progress: {}/{} ({:.1f}%) success:{} fail:{}".format(
                    done[0], total, pct, len(results), len(failed)))
                sys.stdout.flush()
                last_report[0] = now

    print("\r    Done! Success: {} Failed: {}".format(len(results), len(failed)))
    return results, failed


def save_parquet(results):
    """Save as Parquet shards"""
    print("\n[3/4] Saving Parquet files...")
    count = 0
    for code, (name, df) in results.items():
        filepath = PARQUET_DIR / "{}.parquet".format(code)
        df = df.copy()
        df["code"] = code
        df["name"] = name
        df.to_parquet(str(filepath), index=False, compression="zstd")
        count += 1

    total_size = sum(f.stat().st_size for f in PARQUET_DIR.glob("*.parquet"))
    print("    Saved {} files, total: {:.1f} MB".format(count, total_size / 1024.0 / 1024.0))
    return count


def build_index(results):
    """Build SQLite metadata index"""
    print("\n[4/4] Building index...")
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

    stock_cnt = len(results)
    for code, (name, df) in results.items():
        filepath = PARQUET_DIR / "{}.parquet".format(code)
        file_size = filepath.stat().st_size
        db.execute(
            "INSERT INTO kline_index VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, name,
             str(df["date"].min().date()),
             str(df["date"].max().date()),
             len(df), file_size, "{}.parquet".format(code))
        )

    # Trade calendar
    all_dates = set()
    for _, (_, df) in results.items():
        all_dates.update(df["date"].dt.strftime("%Y-%m-%d").tolist())
    for d in sorted(all_dates):
        db.execute("INSERT INTO trade_calendar VALUES (?, ?)", (d, stock_cnt))

    db.commit()
    total_rows = db.execute("SELECT SUM(row_count) FROM kline_index").fetchone()[0]
    print("    {} stocks, {:,} rows, {} trading days".format(stock_cnt, total_rows, len(all_dates)))
    db.close()


def main():
    t0 = time.time()
    stocks = get_stock_list_eastmoney()
    if not stocks:
        print("Failed to get stock list!")
        sys.exit(1)

    results, failed = download_all(stocks)
    if not results:
        print("All downloads failed!")
        sys.exit(1)

    saved = save_parquet(results)
    build_index(results)

    # Save failed list for retry
    if failed:
        with open(str(FAIL_FILE), "w") as f:
            f.write("\n".join(failed))
        print("\nFailed stocks saved to {}".format(FAIL_FILE))

    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("  Done!")
    print("  Stocks: {}, Failed: {}, Time: {:.0f}s".format(saved, len(failed), elapsed))
    print("  Data: {}".format(PARQUET_DIR))
    print("  Index: {}".format(INDEX_DB))
    print("=" * 60)


if __name__ == "__main__":
    main()
