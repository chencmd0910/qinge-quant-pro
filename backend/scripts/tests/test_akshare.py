import akshare as ak
import json

print("Testing alternative APIs...")

# Alt 1: Sina A-share spot
try:
    print("\n1. stock_zh_a_spot (新浪)")
    # check if this function exists
    if hasattr(ak, 'stock_zh_a_spot'):
        df = ak.stock_zh_a_spot()
        print(f"   OK: {len(df)} stocks")
    else:
        print("   Function not available")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

# Alt 2: Tencent sector
try:
    print("\n2. stock_board_industry_name_em (行业板块)")
    df = ak.stock_board_industry_name_em()
    print(f"   OK: {len(df)} sectors, top: {df.iloc[0]['板块名称']} {df.iloc[0]['涨跌幅']}%")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

# Alt 3: Individual stock via sina
try:
    print("\n3. stock_zh_index_spot_em (again with retry)")
    df = ak.stock_zh_index_spot_em()
    print(f"   OK: {len(df)} indices")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

# Alt 4: Try different money flow functions
try:
    print("\n4. stock_sector_fund_flow_rank (行业资金流)")
    if hasattr(ak, 'stock_sector_fund_flow_rank'):
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        print(f"   OK: {len(df)} sectors")
    else:
        print("   Function not available")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

# Alt 5: North-bound money
try:
    print("\n5. stock_hsgt_north_cash_em (北向资金)")
    if hasattr(ak, 'stock_hsgt_north_cash_em'):
        df = ak.stock_hsgt_north_cash_em(symbol="北上")
        print(f"   OK: {len(df)} rows")
    else:
        print("   Function not available")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

# Alt 6: Industry board
try:
    print("\n6. stock_board_industry_summary_ths (同花顺板块)")
    if hasattr(ak, 'stock_board_industry_summary_ths'):
        df = ak.stock_board_industry_summary_ths()
        print(f"   OK: {len(df)} sectors")
    else:
        print("   Function not available")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

# Alt 7: try with curl_cffi explicitly
try:
    print("\n7. stock_zh_a_spot_em with impersonate")
    # Try forcing impersonation
    import requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    })
    r = session.get('https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f12,f14', timeout=10)
    print(f"   HTTP {r.status_code}, data: {r.text[:200]}")
except Exception as e:
    print(f"   FAILED: {type(e).__name__}: {e}")

print("\nDone.")
