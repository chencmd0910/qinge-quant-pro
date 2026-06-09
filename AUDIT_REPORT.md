# 🔍 青鳄量化 Pro — 代码审查报告

**审查日期**: 2026-06-10  
**范围**: 全项目（backend / frontend-next / deploy / scripts / strategies）  
**审查维度**: API一致性、前后端匹配、数据流、错误处理、代码质量、安全、缺失功能、性能

---

## 📊 问题总览

| 严重程度 | 数量 | 说明 |
|---------|------|------|
| 🔴 严重 | 5 | 导致功能不可用或存在严重安全风险 |
| 🟡 中等 | 9 | 影响稳定性/可维护性/数据可靠性 |
| 🟢 轻微 | 6 | 代码质量/体验/未来隐患 |

---

## 🔴 严重问题（5项）

### 1. Alpha Factory API 路径前后端不一致 → 功能不可用

**位置**: 
- 后端: `backend/app/api/alpha_factory_api.py` — `router = APIRouter(prefix="/api/alpha-factory")`
- 前端服务层: `frontend-next/src/services/alpha-factory.ts`

**问题**: 前端服务文件使用下划线 `alpha_factory`，后端路由使用连字符 `alpha-factory`，导致所有服务层调用 404。

```
后端注册:  /api/alpha-factory/strategies?status=...
前端调用:  /api/alpha_factory?status=...          ← ❌ 路径不匹配
```

此外，`alpha-factory.ts` 调用了后端不存在的端点：
- `POST /api/alpha_factory/{id}/promote` — 后端无此端点
- `POST /api/alpha_factory/{id}/retire` — 后端无此端点

> 注：前端组件文件 `alpha-factory-layout.tsx` 直接使用 `/api/alpha-factory/dashboard`（连字符），该路径可正常工作。说明服务层文件未被组件使用，存在死代码。

**修复建议**: 统一为 `alpha-factory`（连字符），并在 `alpha_factory_api.py` 中添加 `promote` 和 `retire` 端点，或将前端调用改为走 `/api/ai/promote`。

---

### 2. AI_CHAT_KEY 默认值包含真实 API 密钥 → 安全泄露

**位置**: `backend/app/api/ai_chat.py:17`
```python
LLM_KEY = os.getenv("AI_CHAT_KEY", "sk-1020b96a41d743b2a008b3614d5fa564")
```

**问题**: 默认值中硬编码了真实的 DeepSeek API Key。任何人获取代码后可使用该密钥。即使 `.env` 覆盖了该值，如果 `.env` 丢失或未正确加载，密钥会暴露在日志/错误信息中。

**修复建议**: 
1. 立即在 DeepSeek 后台吊销此密钥并创建新密钥
2. 将默认值改为空字符串，未配置时报错退出
3. 添加 `.gitignore` 规则排除 `.env` 文件

---

### 3. CORS 配置无效 → 跨域请求可能被浏览器拒绝

**位置**: `backend/app/main.py:45`
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, ...)
```

**问题**: 根据 W3C CORS 规范，`allow_credentials=True` 与 `allow_origins=["*"]` 不能同时使用。浏览器会拒绝此配置，导致带 credentials 的跨域请求失败。

**修复建议**: 
- 开发环境: `allow_origins=["http://localhost:3000"]` + `allow_credentials=True`
- 生产环境: 从环境变量读取允许的域名列表

---

### 4. 数据库配置与实际实现不一致 / SQLite 硬编码

**位置**:
- `backend/app/core/config.py:14` — `DATABASE_URL: str = "postgresql+asyncpg://qinge:qinge123@localhost:5432/qinge_quant"`
- `backend/app/core/database.py:12` — `DATABASE_URL = f"sqlite:///{DB_PATH}"`

**问题**: 
1. `config.py` 定义了 PostgreSQL 连接串（含硬编码密码 `qinge123`），但 `database.py` 完全忽略配置，硬编码使用 SQLite
2. Docker Compose 启动 PostgreSQL 容器，密码同样硬编码为 `qinge123`
3. 配置与实际行为完全脱节，导致排查问题困难
4. `agent_gateway.py` 引用了 SQLAlchemy ORM 模型（`Strategy`, `BacktestReport`, `Position`），但 `init_db()` 创建的表可能为空壳

**修复建议**: 
1. 统一数据库选择（开发用 SQLite，生产用 PostgreSQL）
2. 从环境变量读取数据库密码
3. 删除 `config.py` 中硬编码的密码，改用 `os.getenv("DB_PASSWORD", "")`

---

### 5. AI 路由前缀冲突 → 端点可能覆盖

**位置**:
- `backend/app/api/ai_chat.py:15` — `router = APIRouter(prefix="/api/ai", tags=["AI Chat"])`
- `backend/app/api/ai_lab.py:22` — `router = APIRouter(prefix="/api/ai", tags=["AI Lab"])`

**问题**: 两个独立的路由模块使用了完全相同的 `/api/ai` 前缀。虽然 FastAPI 会合并路由，但存在路径冲突风险：
- `ai_lab.py` 定义了 `GET /strategies` → 最终路径 `/api/ai/strategies`
- `ai_chat.py` 使用 `@router.post("/chat")` → 最终路径 `/api/ai/chat`
- 当前可共存，但未来若两个文件定义同名端点会静默覆盖

**修复建议**: 
1. 将 `ai_chat.py` 的前缀改为 `/api/ai-chat`，或
2. 合并两个文件为一个模块

---

## 🟡 中等问题（9项）

### 6. 回测数据标记为合成数据但前端未区分

**位置**:
- `backend/app/api/backtest.py:138` — `"data_source": "synthetic"`
- `backend/app/api/dashboard.py` — 多处使用 `random.seed()` 生成权益曲线

**描述**: 
- `POST /api/backtest/run` 明确声明数据为 `synthetic`（GBM 模拟）
- `dashboard.py` 用 `random.seed(hash(...))` 生成所有策略的权益曲线
- 前端 `RealBacktestRunner` 组件可看到 `data_source` 字段但未突出标识
- 用户可能误将合成数据当作真实回测结果

**修复建议**: 
1. 前端对 `data_source: "synthetic"` 的结果显示醒目标识（如橙色角标"模拟数据"）
2. Dashboard 数据标注来源
3. 优先引导用户使用 `POST /api/backtest/run-real`（基于 Parquet 的真实回测）

---

### 7. research_api.py 线程安全问题

**位置**: `backend/app/api/research_api.py:25-33`

**描述**: `_run_state` 是模块级全局字典，在 `_run_pipeline_background` 中直接读写，但未对属性组操作加锁：
```python
_run_state["status"] = "running"   # 线程 A 写入
_run_state["progress"] = 5          # 线程 A 写入
# 若线程 B 同时调用 POST /run，可能读到中间态
```

虽然入口有 `_run_state["status"] == "running"` 检查，但检查与设置之间存在竞态条件（TOCTOU）。

**修复建议**: 使用 `threading.Lock` 保护 `_run_state` 的读写，或将状态管理改为 `asyncio.Lock` + `BackgroundTasks`。

---

### 8. 未做输入验证（缺乏 Pydantic Schema）

**位置**: 多个 API 文件
- `strategy.py` — `create_strategy(payload: dict)`
- `backtest.py` — `run_backtest(payload: dict)`
- `paper_trading_api.py` — `daily_update(payload: dict = None)`
- `ai_lab.py` — `batch_backtest(payload: dict)`

**描述**: 大量端点接受原始 `dict` 参数，没有使用 Pydantic 模型进行类型验证、范围检查和必填字段校验。攻击者可以注入任意字段。

**修复建议**: 创建 `backend/app/schemas/api_schemas.py`，为每个端点定义 Pydantic 模型。

---

### 9. 无任何认证/授权机制

**位置**: 全局

**描述**: 所有 API 端点对外开放，无 JWT/OAuth/API Key 认证。在生产环境中任何人都可以：
- 触发大量回测任务消耗服务器资源
- 删除策略注册表数据
- 调用 AI API 消耗 token 额度

**修复建议**: 至少为写入端点添加简单的 API Key 认证中间件。

---

### 10. Docker Compose 中密码硬编码

**位置**: `deploy/docker-compose.yml:9`
```yaml
POSTGRES_PASSWORD: qinge123
```

**描述**: 与 `config.py` 同样的问题，数据库密码 `qinge123` 硬编码在部署文件中。

**修复建议**: 使用 `.env` 文件或 Docker secrets 管理密码。

---

### 11. agent_gateway.py 依赖未初始化的 ORM 模型

**位置**: `backend/app/api/agent_gateway.py:12-14`
```python
from ..models.models import Strategy, BacktestReport, Position
from ..schemas.schemas import BacktestRequest, BacktestResponse
```

**描述**: `agent_gateway.py` 导入了 SQLAlchemy 模型并使用 `get_db` 依赖注入，但：
1. `init_db()` 仅调用 `Base.metadata.create_all(engine)`，依赖模型确实被导入过
2. 若 `models/models.py` 文件不存在或为空，该模块在启动时就会抛出 `ImportError`
3. 实际数据库是 SQLite，Docker Compose 中的 PostgreSQL 仅用于连接字符串

**修复建议**: 确认 `models/models.py` 和 `schemas/schemas.py` 文件存在且包含正确的模型定义。若使用文件存储为主，此文件可改为文件操作。

---

### 12. 代码重复：数据加载函数散落各处

**位置**:
- `dashboard.py` — `_load_registry()`, `_load_lifecycle()`, `_load_backtest()`
- `alpha_factory_api.py` — `_load_registry()`, `_load_lifecycle()`
- `portfolio.py` — `_load_registry()`, `_load_backtest()`
- `risk_api.py` — `_load_registry()`
- `strategy_lab_api.py` — `_load_registry()`, `_load_backtest()`
- `ai_lab.py` — `_load_registry()`, `_load_result()`, `_save_result()`
- `strategy.py` — `_load_registry()`, `_save_registry()`, `_load_code()`, `_save_code()`
- `research_api.py` — 类似功能

**描述**: 至少 8 个文件各自定义了相同的 JSON 文件读写函数。修改数据目录需同步修改所有文件。

**修复建议**: 创建 `backend/app/core/data_access.py` 统一数据层，提供单例的 registry/backtest/research 访问接口。

---

### 13. LivePaperRunner 每请求创建新实例

**位置**: `backend/app/api/paper_trading_api.py`

**描述**: 每个 API 端点都执行 `runner = LivePaperRunner()` 创建新实例，然后调用 `runner.load_state()` 从文件恢复状态。虽然状态持久化在文件中，但重复从文件反序列化存在性能开销，且并发请求可能导致文件读写竞争。

**修复建议**: 使用单例模式或模块级实例，配合文件锁保护状态文件。

---

### 14. Paper Trading 策略分配的 PnL 硬编码为 0

**位置**: `backend/app/api/paper_trading_api.py:114`
```python
"pnl_pct": 0,  # 需从历史净值反算，暂留0
```

**描述**: `/paper-trading/strategies` 端点返回的策略 PnL 恒为 0，注释明确标记为"暂留"。这是功能缺口。

**修复建议**: 按策略维度分拆权益曲线，计算每个策略的实际 PnL。

---

## 🟢 轻微问题（6项）

### 15. 前端 API baseURL 依赖未定义的环境变量

**位置**: `frontend-next/src/lib/axios.ts:4`
```typescript
baseURL: process.env.NEXT_PUBLIC_API_URL || "",
```

**描述**: 
1. `frontend-next` 目录下无 `.env` / `.env.local` 文件
2. `NEXT_PUBLIC_API_URL` 未设置时默认为空字符串 → 请求发到当前域名（相对路径）
3. 如果前端和后端不在同一域名，所有 API 调用都会失败

**修复建议**: 创建 `frontend-next/.env.local`，设置 `NEXT_PUBLIC_API_URL=http://localhost:8000`。

---

### 16. ai_chat.py 系统提示过大

**位置**: `backend/app/api/ai_chat.py:20-70`

**描述**: SYSTEM_PROMPT 约 4000+ 字符，包含完整的 API 列表和指令。每次 AI 对话都会消耗大量 token，增加延迟和成本。部分内容可用 Function Calling 替代。

**修复建议**: 精简系统提示，将 API 能力描述移至 Function Calling tools 定义。

---

### 17. Dashboard 硬编码魔法数字

**位置**: `backend/app/api/dashboard.py`

**描述**:
```python
total_asset = 10_000_000          # 硬编码总资产
daily_return = 0.12                # 硬编码日收益估算
position_count = 20                # 硬编码持仓数
```

**修复建议**: 从配置（`Settings.INITIAL_CAPITAL`）或实际数据源读取。

---

### 18. 脆弱的数据路径拼接

**位置**: 多个 API 文件使用模式：
```python
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data")
```

**描述**: 多层 `dirname` + 相对路径拼接容易出错，移动文件结构即失效。

**修复建议**: 在 `config.py` 中定义 `PROJECT_ROOT` 变量，统一路径计算。

---

### 19. WebSocket 无重连机制

**位置**: `backend/app/websocket/market_ws.py`

**描述**: 前端 WebSocket 连接断开后无自动重连逻辑，可能需要手动刷新页面才能恢复实时行情推送。

**修复建议**: 前端添加 WebSocket 自动重连（指数退避）。

---

### 20. Static 前端资源路径引用

**位置**: Dockerfile 中引用 `frontend` 目录
```yaml
context: ./frontend
```

**描述**: 项目实际前端目录名为 `frontend-next`，但 Docker Compose 构建路径为 `./frontend`（无 `-next` 后缀）。存在目录名不匹配。

**修复建议**: 统一目录名称为 `frontend-next` 或 `frontend`。

---

## 📋 数据流链路分析

### 完整链路: K线数据 → 因子计算 → 策略选股 → 模拟交易

```
┌──────────────────┐     ┌─────────────────────┐     ┌────────────────────┐
│ scripts/klines/  │────▶│ KlineParquetEngine   │────▶│ RealBacktest       │
│ parquet/*.parquet│     │ (get_kline_engine)   │     │ (run-real 端点)    │
│ (4965只A股)      │     │ - get_available_stocks│     │ - v25 多因子排名    │
└──────────────────┘     │ - load_stock_range   │     │ - 月度调仓+止损     │
                         └─────────────────────┘     └─────────┬──────────┘
                                                              │
                                                  ┌───────────▼──────────┐
                                                  │ 回测结果 (metrics +   │
                                                  │ equity_curve + trades)│
                                                  └───────────┬──────────┘
                                                              │
                              ┌───────────────────────────────┤
                              │                               │
                 ┌────────────▼──────────┐      ┌────────────▼──────────┐
                 │ strategy_registry.json│      │ backtest_results/     │
                 │ (策略基因库)           │      │ *.json (完整回测报告)  │
                 └────────────┬──────────┘      └───────────────────────┘
                              │
                 ┌────────────▼──────────┐
                 │ LivePaperRunner       │
                 │ - run_daily()         │
                 │ - 模拟逐日调仓        │
                 │ - portfolio_state.json│
                 └───────────────────────┘
```

**链路状态**:
| 环节 | 状态 | 备注 |
|------|------|------|
| K线数据读取 | ✅ 可用 | 约 4965 只 A 股，2024-06 至 2026-06，Parquet 格式 |
| 因子计算 | ✅ 可用 | v25 多因子（7个因子），RealBacktest 内部计算 |
| 策略选股 | ✅ 可用 | 根据因子排名选 Top N，月度调仓 |
| Paper Trading | ⚠️ 部分 | 日推进可用，但策略级 PnL 计算未实现 |
| 实盘交易 | ❌ 未实现 | 项目无实盘券商接口 |

---

## 🔒 安全检查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 硬编码密钥 | 🔴 | `ai_chat.py` 含真实 DeepSeek API Key |
| 数据库密码 | 🔴 | `config.py` + `docker-compose.yml` 硬编码 `qinge123` |
| CORS 安全 | 🔴 | `allow_origins=["*"]` + `allow_credentials=True` 无效配置 |
| DEBUG 模式 | 🟡 | 默认 `True`，生产环境需关闭 |
| 认证机制 | ❌ | 无任何认证 |
| 输入验证 | 🟡 | 大部分端点接受 raw dict |
| SQL 注入 | ✅ | 使用 SQLAlchemy ORM（仅 agent_gateway.py 使用） |
| XSS | ✅ | Next.js 默认转义 |
| HTTPS | ❌ | Docker Compose 无 TLS 配置 |
| 日志泄露 | ⚠️ | `ai_chat.py` 中 API Key 可能出现在错误信息中 |

---

## 📊 总结

该项目整体架构清晰，功能模块划分合理。主要风险集中在：
1. **前后端 API 路径不一致** — Alpha Factory 服务层直接不可用
2. **安全硬编码** — API Key 和数据库密码泄露
3. **数据可信度** — 多个 API 返回合成/估算数据但前端未标识

优先修复前 3 项严重问题，中等问题在迭代中逐步解决。

---

*审查工具: OpenClaw Agent · 审查范围: 42 个核心源文件*
