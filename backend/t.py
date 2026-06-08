import baostock as bs
import pandas as pd
from datetime import datetime, timedelta

lg = bs.login()
print(f"Login: {lg.error_code} {lg.error_msg}")

today = datetime.now().strftime("%Y-%m-%d")
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

# 1. Index K-line
print("\n=== 指数行情 ===")
for code, name in [("sh.000001","上证"), ("sz.399001","深证"), ("sz.399006","创业板"),
                    ("sh.000688","科创50"), ("sh.000300","沪深300"), ("sh.000905","中证500")]:
    rs = bs.query_history_k_data_plus(code, "date,close,volume,amount", end_date=today, frequency="d", adjustflag="3")
    rows = []
    while (rs.error_code == '0') & rs.next():
        rows.append(rs.get_row_data())
    if rows:
        r = rows[-1]
        print(f"  {name}: {r[0]} close={r[1]} vol={r[2]}")

# 2. All-stock breadth
print("\n=== 涨跌分布 ===")
rs = bs.query_all_stock(day=yesterday)
rows = []
while (rs.error_code == '0') & rs.next():
    rows.append(rs.get_row_data())

if rows:
    df = pd.DataFrame(rows, columns=rs.fields)
    print(f"  {len(df)} stocks on {yesterday}")
    print(f"  columns: {list(df.columns)}")
else:
    print("  No data for yesterday, trying 2 days ago...")
    d2 = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=d2)
    rows = []
    while (rs.error_code == '0') & rs.next():
        rows.append(rs.get_row_data())
    if rows:
        df = pd.DataFrame(rows, columns=rs.fields)
        print(f"  {len(df)} stocks on {d2}")

# 3. Industry classification
print("\n=== 行业分类 ===")
rs = bs.query_stock_industry()
rows = []
while (rs.error_code == '0') & rs.next():
    rows.append(rs.get_row_data())
if rows:
    df = pd.DataFrame(rows, columns=rs.fields)
    print(f"  {len(df)} industry records, {df['industry'].nunique()} unique industries")
    print(f"  Top industries: {df['industry'].value_counts().head(5).to_dict()}")

bs.logout()
print("\nDone.")
