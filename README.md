# 青鳄量化 Pro 🐊

AI 量化研究实验室 | 全球多市场架构 | 从研究到实盘的完整链路

## 核心能力

```
研究 → 回测 → 验证 → 模拟盘 → 实盘
 ✅     ✅     ✅      ✅       ⬜
```

**已完成 11 个 Sprint，17 次迭代，85+ 个 Python 模块。**

## 架构总览

```
┌─────────────────────────────────────────────────┐
│  Alpha Factory (自动化研究工厂)                   │
│  ├── Strategy Generator (自动策略生成)            │
│  ├── Batch Backtest (批量回测)                    │
│  ├── Auto Validation (自动验证)                   │
│  ├── ACTIVE / WATCHLIST / RETIRED (生命周期)      │
│  └── Capital Allocation Engine (动态资金分配)      │
├─────────────────────────────────────────────────┤
│  Research Engine (研究引擎)                       │
│  ├── Walk Forward Test (滚动窗口验证)             │
│  ├── Monte Carlo (1000次随机打乱)                 │
│  ├── Factor Attribution (因子归因)                │
│  ├── Strategy Clustering (聚类去重)               │
│  └── Alpha Decay Monitor (策略衰减监控)           │
├─────────────────────────────────────────────────┤
│  Risk Engine 2.0 (风控引擎)                       │
│  ├── Position Sizer (5种仓位管理)                 │
│  ├── Portfolio Risk (VaR/Beta/行业暴露)           │
│  ├── Dynamic Drawdown Control (三级回撤控制)       │
│  ├── Correlation Matrix (相关性矩阵)              │
│  └── Daily Risk Monitor (每日风险报告)            │
├─────────────────────────────────────────────────┤
│  Core Engines (核心引擎)                          │
│  ├── Event Engine (事件驱动)                      │
│  ├── Data Engine (多数据源)                       │
│  ├── Strategy Engine (双模式策略)                  │
│  ├── Backtest Engine (事件驱动回测)                │
│  ├── Trading Engine (统一券商接口)                 │
│  └── Market Engine (多市场抽象)                   │
└─────────────────────────────────────────────────┘
```

## 模块完成度

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 数据引擎 | 80% | AkShare(A股) ✅ / Futu(港股) / Alpaca(美股) / Binance(加密) |
| 回测引擎 | 85% | 事件驱动回测 + 绩效指标 |
| 研究引擎 | 90% | 策略注册表 / Walk Forward / Reality Check |
| 自动生成 | 80% | 100个策略批量生成+回测+验证 |
| 验证层 | 90% | OOS / Monte Carlo / Factor Attribution / Clustering |
| 模拟盘 | 85% | Top5组合 / Daily Runner / 日报/周报/30天验证 |
| 风控引擎 | 80% | 5种仓位管理 / 三级回撤控制 / 相关性矩阵 |
| Alpha Factory | 85% | ACTIVE/WATCHLIST/RETIRED / 动态资金分配 |
| 实盘层 | 10% | QMT占位 |

## 全球多市场架构

接口一次设计到位，实现分阶段推进：

| 版本 | 市场 | 数据源 | 券商 | 状态 |
|------|------|--------|------|------|
| V1 | A股 | AkShare | PaperBroker | ✅ |
| V2 | A股实盘 | AkShare | QMT | ⬜ |
| V3 | 港股 | Futu | FutuBroker | ⬜ |
| V4 | 美股 | Alpaca | IBKR | ⬜ |
| V5 | 加密 | Binance | Binance/OKX | ⬜ |

## 快速开始

```bash
# 安装依赖
cd backend && pip install -r requirements.txt

# 启动后端
python -m uvicorn app.main:app --reload --port 8000

# 运行ETF轮动回测
python run_sprint3_backtest.py

# 运行AI研究实验室 (100个策略)
python run_batch_research.py
```

## 内置策略

| 策略 | 类型 | 年化 | Sharpe | Alpha | 状态 |
|------|------|------|--------|-------|------|
| 量价_6F | 量价/动量 | +19.6% | 2.500 | +16.9% | ACTIVE |
| 基本面_5F | 基本面/行业 | +15.0% | 1.594 | +12.6% | WATCHLIST |
| 资金流_4F | 资金流 | +11.7% | 1.704 | +11.0% | RETIRED |
| 动量_5F | 动量 | +11.1% | 1.612 | +10.1% | ACTIVE |
| 北向_4F | 北向资金 | +10.5% | 1.500 | +8.2% | WATCHLIST |

## API

- `GET  /api/health` - 健康检查
- `GET  /api/backtest/result/{id}` - 回测报告
- `GET  /api/dashboard/summary` - 仪表盘
- `GET  /api/portfolio/positions` - 持仓
- `GET  /api/strategy/list` - 策略列表
- `POST /api/backtest/run` - 运行回测
- `GET  /api/market/kline/{symbol}` - K线
- `POST /api/agent/v1` - AI Agent Gateway
- `WS   /ws/market` - 行情 WebSocket

## 研究数据库

```bash
# 查看策略排行榜
cat backend/data/strategy_registry.json

# 查看研究结果
cat backend/data/research/research_runs.json

# 查看策略生命周期
cat backend/data/strategy_lifecycle.json
```

## 技术栈

- **后端:** Python 3.13 / FastAPI / SQLAlchemy
- **数据:** AkShare / baostock / SQLite
- **前端:** Chart.js (回测报告)
- **部署:** Docker / docker-compose

## 飞书文档

[青鳄量化 Pro - 功能全览](https://feishu.cn/docx/QUOLdd1H2ojt93xbAkXcr8GAnte)

---

> 🐊 从量化软件到 AI 量化研究实验室的进化
