# CLAUDE_CONTEXT.md — AI Assistant 快速上手指南

> 本文档为 Claude / GPT / DeepSeek 等 AI 编程助手准备，无需全量扫描即可理解项目。

---

## 项目概览

- **名称**: 青鳄量化 Pro (Qinge Quant Pro)
- **类型**: Python量化交易系统 + AI策略研究平台
- **Python版本**: 3.12+
- **框架**: FastAPI + Docker
- **部署**: 阿里云 2核2GB / Docker Compose / Nginx反向代理
- **域名**: https://39ai.cc

---

## 项目结构（只读核心文件）

```
backend/                          # ⚠️ 工作目录是 backend/，不是根目录
├── app/
│   ├── main.py                   # FastAPI入口，所有router注册点
│   ├── api/                      # API路由层
│   │   ├── research_api.py       # 研究流水线 /api/research/*
│   │   ├── ai_lab.py             # AI实验室 /api/ai/*
│   │   ├── backtest.py           # 回测 /api/backtest/*
│   │   ├── dashboard.py          # 仪表盘 /api/dashboard/*
│   │   ├── portfolio.py          # 持仓 /api/portfolio/*
│   │   ├── strategy.py           # 策略 /api/strategy/*
│   │   └── ...                   # 其他API端点
│   │
│   ├── backtest_engine/
│   │   └── real_backtest.py      # ⭐ 核心回测引擎 (18因子，事件驱动)
│   │
│   ├── research_engine/
│   │   ├── lab.py                # ⭐ AI研究实验室 (100策略批量)
│   │   ├── generator.py          # 策略生成器
│   │   ├── lifecycle.py          # 策略生命周期
│   │   └── validation.py         # 验证规则
│   │
│   ├── alpha_factory/
│   │   ├── factory.py            # ACTIVE/WATCHLIST/RETIRED管理
│   │   └── allocator.py          # 动态资金分配
│   │
│   ├── risk_engine/              # ⚚ 大部分未接入
│   ├── automation/               # 自动化模块
│   │   ├── alternative_data.py   # 另类数据采集
│   │   ├── factor_weight_adapter.py # IC监控权重适配
│   │   ├── barra_risk.py         # Barra风控
│   │   └── stress_tester.py      # 压力测试
│   │
│   ├── data_engine/
│   │   └── kline_parquet.py      # ⭐ Parquet数据引擎 (主数据源)
│   │
│   ├── paper_trading/
│   │   └── live_runner.py        # ⭐ LivePaperRunner模拟盘
│   │
│   └── models/models.py          # SQLAlchemy ORM模型
│
├── dashboard/                    # Flask 生产前端
│   └── templates/
│       └── index.html            # ⭐ 主前端页面 (深色主题)
│
└── scripts/
    └── daily_pipeline.py         # 每日自动化脚本
```

---

## 关键入口点

| 入口 | 路径 | 说明 |
|------|------|------|
| FastAPI | `backend/app/main.py` | 所有router注册处 |
| 回测 | `backend/app/backtest_engine/real_backtest.py::RealBacktest` | 18因子事件驱动回测 |
| 研究 | `backend/app/research_engine/lab.py::AIResearchLab` | 策略生成→回测→验证→锦标赛 |
| 模拟盘 | `backend/app/paper_trading/live_runner.py::LivePaperRunner` | 真实K线模拟交易 |
| 数据引擎 | `backend/app/data_engine/kline_parquet.py::get_kline_engine()` | Parquet数据读取 |

---

## 技术栈

- **后端**: Python 3.12, FastAPI, Pydantic, SQLAlchemy
- **数据**: pandas, numpy, pyarrow (Parquet)
- **数据源**: akshare, baostock (A股)
- **部署**: Docker, Docker Compose, Nginx, systemd
- **前端**: Flask + Chart.js (生产), Next.js 15 (实验)
- **ORM**: SQLite (开发) / PostgreSQL (计划)

---

## 命名约定

| 约定 | 示例 |
|------|------|
| 股票代码 | `600519.SH` (A股), `00700.HK` (港股), `AAPL.US` (美股) |
| 因子名称 | snake_case: `mom_5d`, `northbound_flow`, `pe_ttm` |
| 策略ID | `AUTO_XXXX_xxxxxxxx` (自动生成) 或 `Gen2_Strategy_XXX` (进化) |
| 状态枚举 | `RESEARCH → BACKTESTED → VALIDATED → ACTIVE → RETIRED` |

---

## 常见操作指引

### 运行回测
```python
from app.backtest_engine.real_backtest import RealBacktest
bt = RealBacktest(codes=["600519.SH"], start="2024-01-01", ...)
result = bt.run()
```

### 添加新因子
1. `real_backtest.py` → `FACTOR_WEIGHTS` 添加权重
2. `real_backtest.py` → `_select_top()` 添加计算逻辑
3. 如需新数据源 → 添加 `_load_xxx()` 方法
4. `lab.py` → `REAL_FACTORS` 集合同步

### 添加新API端点
1. 在 `app/api/` 创建路由文件
2. 在 `app/main.py` 注册 `app.include_router()`

---

## ⚠️ 已知陷阱

1. **不要用 `from app.xxx` import** — Docker容器内 `app/` 是包根目录，没有外层包
2. **K线数据在Parquet** — 不在SQLite，不要查数据库
3. **换行符统一LF** — .gitattributes 已配置
4. **不要修改PROJECT_STATUS.md** — 这是自动生成的状态文件
5. **Order/Position类重复** — 存在于 `trading_engine/broker_base.py` 和 `backtest_engine/core/`，接入实盘前需合并
6. **服务器是2核2GB** — 回测和数据处理注意性能

---

## 服务器信息

```
SSH: root@47.83.18.132
密码: Cmdqq141242!
容器: qinge-pro-backend (端口8000), qinge-pro-frontend (端口3001)
数据: /app/data/  (Parquet文件)
Python路径: /app/ (sys.path.insert(0, '/app'))
重启: docker restart qinge-pro-backend
```

---

## 项目当前版本

- **项目版本**: v28
- **迭代次数**: 30+
- **因子数**: 18 (有效), 3 (预留)
- **API端点**: 15
- **GitHub commit**: ada420e (2026-06-12)
