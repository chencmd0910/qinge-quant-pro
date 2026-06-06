# 青鳄量化 Pro

专业量化交易工作站。

## 架构

```
backend/          FastAPI 后端
  app/
    api/          API 路由
    core/         配置、数据库
    models/       SQLAlchemy 模型
    schemas/      Pydantic 模型
    backtest_engine/  回测引擎
    strategy_engine/  策略引擎
    risk_engine/      风控引擎
    trading_engine/   交易引擎
    websocket/        WebSocket
frontend/         Next.js 前端
strategies/       策略目录
deploy/           Docker 部署
```

## 快速开始

```bash
# 启动数据库
cd deploy && docker-compose up -d postgres redis

# 启动后端
cd backend && pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# 迁移数据
cd backend && python migrate_data.py
```

## API

- `GET  /api/dashboard/summary` - 仪表盘总览
- `GET  /api/portfolio/positions` - 持仓列表
- `GET  /api/portfolio/trades` - 交易记录
- `GET  /api/strategy/list` - 策略列表
- `POST /api/strategy/create` - 创建策略
- `POST /api/strategy/{id}/run` - 运行策略
- `POST /api/backtest/run` - 运行回测
- `GET  /api/market/kline/{symbol}` - K线数据
- `WS   /ws/market` - 行情WebSocket
