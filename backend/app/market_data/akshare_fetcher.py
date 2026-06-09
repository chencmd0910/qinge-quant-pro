"""行情更新器 — akshare收盘拉取 + 追加Parquet

用法:
    python -m app.market_data.akshare_fetcher                    # 更新所有4965只到今天
    python -m app.market_data.akshare_fetcher --date 2026-06-09  # 更新指定日期
    python -m app.market_data.akshare_fetcher --codes 000001,600519  # 只更新指定股票
"""
import os
import sys
import time
import argparse
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import pandas as pd

DATA_DIR = os.environ.get("PAPER_TRADING_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                 "data", "klines", "parquet"))


def get_parquet_files(data_dir: str = DATA_DIR) -> List[str]:
    """获取所有现有parquet代码列表"""
    if not os.path.exists(data_dir):
        return []
    return sorted([
        f.replace('.parquet', '')
        for f in os.listdir(data_dir)
        if f.endswith('.parquet')
    ])


def last_date_for_code(code: str, data_dir: str = DATA_DIR) -> Optional[str]:
    """获取某只股票parquet中最新日期"""
    path = os.path.join(data_dir, f"{code}.parquet")
    if not os.path.exists(path):
        return None
    df = pd.read_parquet(path, columns=['date'])
    if df.empty:
        return None
    return str(df['date'].max())[:10]


def fetch_stock_kline(code: str, start_date: str, end_date: str = None) -> Optional[pd.DataFrame]:
    """通过akshare获取单只股票日K线（前复权）

    Args:
        code: 纯数字代码 (000001, 600519)
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD，默认今天

    Returns:
        DataFrame with columns: date, open, close, high, low, volume
        失败返回 None
    """
    try:
        import akshare as ak

        # akshare要求格式: YYYYMMDD
        start = start_date.replace('-', '')
        end = (end_date or date.today().isoformat()).replace('-', '')

        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start,
            end_date=end,
            adjust="qfq"  # 前复权
        )

        if df is None or df.empty:
            return None

        # 标准化列名
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
        })

        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df = df[['date', 'open', 'close', 'high', 'low', 'volume']].copy()

        return df

    except ImportError:
        raise RuntimeError("akshare 未安装: pip install akshare")
    except Exception as e:
        print(f"  [ERR] {code}: {e}")
        return None


def fetch_stock_info(code: str) -> Optional[dict]:
    """获取股票名称"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        if not row.empty:
            return {'code': code, 'name': row.iloc[0]['名称']}
        return {'code': code, 'name': code}
    except Exception:
        return {'code': code, 'name': code}


def update_single_stock(code: str, data_dir: str = DATA_DIR,
                        target_date: str = None, verbose: bool = True) -> dict:
    """更新单只股票的parquet文件

    Args:
        code: 股票代码
        data_dir: parquet存储目录
        target_date: 目标日期（默认今天）
        verbose: 是否打印日志

    Returns:
        {'code': code, 'status': 'updated'|'skipped'|'error', 'new_rows': int}
    """
    path = os.path.join(data_dir, f"{code}.parquet")

    # 确定起始日期
    if os.path.exists(path):
        existing = pd.read_parquet(path)
        last_dt = str(existing['date'].max())[:10]
        start_date = (pd.to_datetime(last_dt) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        existing_name = existing['name'].iloc[0] if 'name' in existing.columns else None
    else:
        start_date = "2024-01-01"  # 从头拉
        existing_name = None

    end_date = target_date or date.today().isoformat()

    # 检查是否需要更新
    if start_date > end_date:
        return {'code': code, 'status': 'skipped', 'new_rows': 0, 'reason': '已是最新'}

    # 拉取新数据
    new_df = fetch_stock_kline(code, start_date, end_date)
    if new_df is None or new_df.empty:
        return {'code': code, 'status': 'skipped', 'new_rows': 0, 'reason': '无新数据'}

    # 获取股票名称
    name = existing_name
    if not name:
        info = fetch_stock_info(code)
        name = info.get('name', code) if info else code

    # 添加code和name列
    new_df['code'] = code
    new_df['name'] = name

    # 合并写入
    if os.path.exists(path):
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        combined = combined.sort_values('date').reset_index(drop=True)
    else:
        combined = new_df

    combined.to_parquet(path, index=False)

    if verbose:
        print(f"  [OK] {code} {name}: +{len(new_df)}行  {new_df['date'].iloc[0]} → {new_df['date'].iloc[-1]}")

    return {
        'code': code,
        'name': name,
        'status': 'updated',
        'new_rows': len(new_df),
        'date_range': f"{new_df['date'].iloc[0]} ~ {new_df['date'].iloc[-1]}",
    }


def update_all_stocks(data_dir: str = DATA_DIR, target_date: str = None,
                      codes: List[str] = None, max_workers: int = 20,
                      verbose: bool = True) -> dict:
    """并发更新所有股票

    Args:
        data_dir: parquet目录
        target_date: 目标日期
        codes: 要更新的代码列表（默认全部）
        max_workers: 并发数（akshare免费，不用太激进）
        verbose: 是否打印日志

    Returns:
        统计结果
    """
    if codes is None:
        codes = get_parquet_files(data_dir)

    if not codes:
        return {'updated': 0, 'skipped': 0, 'errors': 0, 'total': 0}

    if verbose:
        print(f"[MarketData] 开始更新 {len(codes)} 只股票...")

    start_time = time.time()
    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(update_single_stock, code, data_dir, target_date, verbose): code
            for code in codes
        }
        for i, f in enumerate(as_completed(futures)):
            try:
                r = f.result()
                results.append(r)
                if i % 500 == 0 and i > 0 and verbose:
                    elapsed = time.time() - start_time
                    rate = i / elapsed
                    remaining = (len(codes) - i) / rate
                    print(f"  ...进度 {i}/{len(codes)}  ({rate:.1f}只/秒, 剩余{remaining:.0f}秒)")
            except Exception as e:
                code = futures[f]
                errors.append({'code': code, 'error': str(e)})
                if verbose:
                    print(f"  [ERR] {code}: {e}")

    elapsed = time.time() - start_time
    updated = [r for r in results if r['status'] == 'updated']
    skipped = [r for r in results if r['status'] == 'skipped']

    summary = {
        'updated': len(updated),
        'skipped': len(skipped),
        'errors': len(errors),
        'total': len(results),
        'elapsed_seconds': round(elapsed, 1),
        'new_rows_total': sum(r.get('new_rows', 0) for r in updated),
    }

    if verbose:
        print(f"\n[MarketData] 完成!")
        print(f"  更新: {summary['updated']}只")
        print(f"  跳过: {summary['skipped']}只（已最新）")
        print(f"  错误: {summary['errors']}只")
        print(f"  耗时: {elapsed:.1f}秒")

    return summary


# ═══════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='A股K线数据更新（akshare）')
    parser.add_argument('--date', type=str, default=None, help='目标日期 (YYYY-MM-DD)')
    parser.add_argument('--codes', type=str, default=None, help='股票代码列表，逗号分隔')
    parser.add_argument('--workers', type=int, default=20, help='并发数')
    parser.add_argument('--data-dir', type=str, default=DATA_DIR, help='parquet目录')
    parser.add_argument('--quiet', action='store_true', help='安静模式')

    args = parser.parse_args()

    codes = args.codes.split(',') if args.codes else None
    update_all_stocks(
        data_dir=args.data_dir,
        target_date=args.date,
        codes=codes,
        max_workers=args.workers,
        verbose=not args.quiet,
    )


if __name__ == '__main__':
    main()
