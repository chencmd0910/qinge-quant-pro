"""青鳄量化 MCP Server — 独立启动脚本

运行方式:
    python run_mcp.py
    python run_mcp.py --port 8001

MCP 端点地址: http://localhost:8001/mcp
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.mcp import mcp

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="青鳄量化 Pro MCP Server")
    parser.add_argument("--port", type=int, default=8001, help="MCP 端口 (默认 8001)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="绑定 IP")
    args = parser.parse_args()

    print(f"[QingeMCP] MCP Server for 青鳄量化 Pro")
    print(f"   端点: http://{args.host}:{args.port}/mcp")
    print(f"   工具: dashboard, equity, strategies, alerts, positions, alpha_factory, backtest, risk, market")

    mcp.run(transport="streamable-http")
