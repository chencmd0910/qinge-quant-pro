# 🐊 青鳄量化 Pro — 部署指南

## 前置要求

- Docker 20.10+
- 2核/2GB 以上服务器 (阿里云轻量验证通过)
- akshare 可正常访问 (需国内网络环境)

## 快速启动

```bash
# 1. 克隆项目
git clone <repo-url> qinge-quant-pro
cd qinge-quant-pro

# 2. 构建 + 启动
docker-compose -f deploy/docker-compose.yml up -d --build

# 3. 初始化行情数据 (首次运行必须)
curl -X POST http://localhost:8000/api/paper-trading/market/update
```

## 服务端口

| 服务 | 端口 | 说明 |
|:---|:---|:---|
| 后端 API | 8000 | FastAPI |
| 前端 | 3001 | Next.js (映射自 3000) |

## 目录结构

```
/opt/qinge-quant-pro/         # 宿主机项目路径
├── backend/
│   ├── data/                  # 数据目录
│   │   ├── klines/parquet/    # 4965只A股Parquet K线
│   │   ├── live_trading_state.json
│   │   ├── strategy_registry.json
│   │   └── qinge.db
│   ├── Dockerfile
│   └── app/
├── frontend-next/
│   └── Dockerfile
└── deploy/
    └── docker-compose.yml
```

## 手动部署 (当前使用)

```bash
# 后端
cd backend
docker build -t qinge-pro-backend .
docker run -d --name qinge-pro-backend \
  -p 8000:8000 \
  -v /opt/qinge-quant-pro/backend/data:/app/data \
  -e PAPER_TRADING_DATA_DIR=/app/data \
  qinge-pro-backend

# 前端
cd frontend-next
docker build -t qinge-pro-frontend .
docker run -d --name qinge-pro-frontend -p 3001:3000 qinge-pro-frontend
```

## Cron 定时任务

```bash
# 每个交易日 15:30 自动拉行情 + 跑模拟交易
crontab -e
# 添加:
30 15 * * 1-5 curl -s -X POST http://localhost:8000/api/paper-trading/market/update && curl -s -X POST http://localhost:8000/api/paper-trading/live/run-daily
```

## 日志查看

```bash
docker logs -f --tail 100 qinge-pro-backend
docker logs -f --tail 100 qinge-pro-frontend
```

## 环境变量

| 变量 | 默认 | 说明 |
|:---|:---|:---|
| PAPER_TRADING_DATA_DIR | /app/data | K线数据目录 |
| API_KEY | (空=不启用) | API认证密钥 |
