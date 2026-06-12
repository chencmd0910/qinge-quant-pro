# 青鳄量化 Pro — 项目状态

> 最后更新: 2026-06-12 | 版本: v28 | 30+次迭代
> GitHub: [chencmd0910/qinge-quant-pro](https://github.com/chencmd0910/qinge-quant-pro) (main)
> 部署: 阿里云 47.83.18.132 / Docker qinge-pro-backend / 39ai.cc → 青鳄量化面板

---

## 一、当前架构

```
青鳄量化 Pro
├── backend/                          # 后端 (Python/FastAPI) — 生产运行
│   └── app/
│       ├── main.py                   # FastAPI 入口
│       ├── api/                      # API 路由层 (15个端点)
│       ├── backtest_engine/          # 回测引擎 (RealBacktest, 18因子)
│       ├── research_engine/          # 研究引擎 (lab/generator/lifecycle)
│       ├── alpha_factory/            # Alpha Factory (策略生命周期管理)
│       ├── strategy_engine/          # 策略引擎 (4个内置策略)
│       ├── risk_engine/              # 风控引擎 (三级回撤+Barra)
│       ├── data_engine/              # 数据引擎 (kline_parquet, providers)
│       ├── automation/               # 自动化模块 (12个)
│       ├── paper_trading/            # 模拟盘 (LivePaperRunner)
│       ├── trading_engine/           # 交易引擎 (占位接口)
│       ├── market_engine/            # 市场引擎 (交易日历)
│       ├── event_engine/             # ⚠️ 废弃 — 事件驱动架构，未使用
│       ├── portfolio/                # 组合管理 (占位)
│       ├── benchmark/                # 基准对比 (占位)
│       ├── mcp/                      # MCP协议 (占位)
│       └── websocket/                # WebSocket (占位)
│
├── frontend-next/                    # Next.js 前端(实验)
├── dashboard/                        # Flask 图表服务端(模板已弃用)
├── blog/                             # SEO 博客(39ai)
├── scripts/                          # 运维脚本
└── docker-compose.yml                # ⚠️ 39AI旧版，未使用
```

---

## 二、核心链路

```
AkShare采集 → Parquet缓存 → FactorEngine(24因子) → RealBacktest(18因子)
   → 策略生成(StrategyGenerator) → 批量回测(lab.py) → 验证评分
   → Alpha Factory(ACTIVE/WATCHLIST/RETIRED) → LivePaperRunner模拟盘
```

---

## 三、已完成模块 ✅

| 模块 | 完成度 | 说明 |
|------|--------|------|
| 数据引擎 | 82% | AkShare + Parquet缓存，baostock PE/PB，北向/融资/大单 |
| 回测引擎 | 88% | RealBacktest 18因子事件驱动，真实交易成本 |
| 研究引擎 | 90% | Walk Forward, Reality Check, 策略锦标赛 |
| AI研究实验室 | 85% | 批量生成+回测+验证，6个API端点，基因进化 |
| 模拟盘 | 90% | LivePaperRunner统一引擎，一级风控 |
| Alpha Factory | 80% | 策略生命周期（ACTIVE→WATCHLIST→RETIRED） |
| 风控引擎 | 80% | 三级回撤控制+持股相关性矩阵+行业合规看板 |
| API层 | 85% | 15个端点（含AI Lab/V25 Barra/Factor/Signals） |
| 前端Flask | 70% | Flask模板在生产运行 |
| 前端Next.js | 40% | 实验品，9个页面占位 |

---

## 四、预留/占位模块 🟡

以下模块接口已定义，但未实现或未接入：

| 模块 | 文件 | 状态 |
|------|------|------|
| 基准对比 | `benchmark/benchmark.py` | 未接入main.py |
| 多市场提供者 | `providers/{futu,alpaca,binance}` | 占位类 |
| 多市场券商 | `brokers/{qmt,futu,ibkr,okx}` | 占位类 |
| 事件驱动引擎v1 | `backtest_engine/engine.py` | 已被real_backtest替代 |
| A股市场规则 | `risk_engine/market_rules/a_share_rule.py` | 未接入风控 |
| 港股/美股/加密规则 | `risk_engine/market_rules/{hk,us,crypto}_rule.py` | 占位 |
| 策略引擎管理器 | `strategy_engine/manager.py` | 未接入 |
| WebSocket | `websocket/market_ws.py` | 已注册但未连接数据 |
| MCP协议 | `mcp/quant_server.py` | 实验代码 |
| 组合管理 | `portfolio/{portfolio,master_portfolio}` | 占位 |
| 纸盘旧版 | `paper_trading/{runner,portfolio,reports}` | 已被live_runner替代 |

---

## 五、废弃模块 ❌

以下模块已确认不再使用：

| 模块 | 文件 | 原因 |
|------|------|------|
| 事件驱动引擎 | `event_engine/*` (5个文件) | 架构已改为回测直连 |
| 旧版回测引擎 | `backtest_engine/engine.py` | 已被real_backtest替代 |
| 旧版事件引擎 | `backtest_engine/event_engine.py` | 同上 |
| SQLite存储 | `data_engine/storage/bar_storage.py` | 已被Parquet替代 |
| 数据引擎管理器 | `data_engine/manager.py` | 已被kline_parquet直连替代 |
| Parquet提供者 | `data_engine/providers/parquet_provider.py` | 功能重复 |
| 数据引擎服务 | `data_engine/service.py` | 未使用 |
| 旧版模拟盘 | `paper_trading/runner.py` | 已被live_runner替代 |
| 持仓管理器 | `automation/position_manager.py` | 重复组件(Order类冲突) |
| 旧版策略目录 | `strategies/etf_rotation/` `strategies/moving_average/` | 已迁移到strategy_engine |

---

## 六、当前因子体系 (V28)

**18个有效因子（RealBacktest使用）：**

| 类别 | 权重 | 因子 |
|------|------|------|
| 动量 | 0.32 | mom_5d(0.12), mom_10d(0.10), mom_3d(0.05), mom_20d(0.05) |
| 趋势 | 0.18 | ma_dev_20d(0.06), boll_pos(0.06), price_accel(0.06) |
| 质量 | 0.15 | consistency(0.05), daily_sharpe(0.05), vol_20d(0.05) |
| 另类 | 0.10 | northbound_flow(0.03), margin_change(0.03), big_deal_net(0.04) |
| 资金/情绪 | 0.09 | money_flow(0.04), macd_hist(0.03), rsi_14(0.02) |
| 基本面 | 0.10 | pe_ttm(0.05), pb_ttm(0.05) |
| 预留位 | 0.06 | turnover_mom(0.02), volume_ratio(0.02), atr_14(0.02) |

---

## 七、数据管道

```
AkShare (日线) ──→ kline_parquet.py ──→ /app/data/klines/*.parquet
baostock (PE/PB) ──→ _load_fundamentals() ──→ fundamentals.parquet
东财大单 (资金流) ──→ fund_flow_collector.py ──→ big_deal.parquet
北向资金 ──→ alternative_data.py ──→ northbound.parquet
融资融券 ──→ alternative_data.py ──→ margin.parquet
行业数据 ──→ alternative_data.py ──→ industry.parquet
```

---

## 八、API端点清单 (15个)

| 端点 | 用途 |
|------|------|
| `/api/health` | 健康检查 |
| `/api/backtest/result/{id}` | 回测报告 |
| `/api/agent/v1` | AI Agent网关 |
| `/api/dashboard` | 仪表盘 |
| `/api/portfolio` | 持仓查询 |
| `/api/strategy` | 策略管理 |
| `/api/market` | 行情查询 |
| `/api/ai/create-and-backtest` | AI策略创建+回测 |
| `/api/ai/evolve` | 基因进化研究 |
| `/api/ai/genealogy/summary` | 基因库总览 |
| `/api/v25/barra-risk` | Barra风控归因 |
| `/api/v25/factor-health` | 28因子权重+IC |
| `/api/v25/signals` | 每日信号 |
| `/api/v25/stress-test` | 压力测试 |
| `/api/v25/industry-breakdown` | 行业合规 |
| `/ws/market` | WebSocket行情 |

---

## 九、Cron定时任务

| 时间 | 任务 | 状态 |
|------|------|------|
| 08:00 每日 | 策略自动生成(100个) | ✅ active, v4-flash |
| 09:30 交易日 | A股选股-上午 | ✅ active, v4-flash |
| 14:00 交易日 | A股选股-下午 | ✅ active, v4-flash |

---

## 十、GitHub同步状态

| 状态 | 数量 | 说明 |
|------|------|------|
| 同步 | 140 | 当前head ada420e 与服务器一致 |
| 仅服务器 | 11 | 废弃组件（event_engine等），未同步 |
| 仅GitHub | 0 | 已无diff |
| 最近同步 | 2026-06-12 14:30 | commit ada420e |

---

## 十一、已知技术债务

1. `Order`/`Position`/`OrderSide`/`OrderStatus` 在 `trading_engine/broker_base` 和 `backtest_engine/core` 分别定义（重复模型）
2. 116个文件 CRLF vs LF 换行符差异（.gitattributes 已修复）
3. 北向资金/融资/大单数据每天需要手动采集
4. 验证门槛在真回测下通过率为0，需要重新校准
5. 后端无自动测试覆盖
6. 无 CI/CD 流程

---

> 🐊 青鳄量化 Pro — 从研究到实盘的完整量化链路
> 部署: [39ai.cc](https://39ai.cc)
