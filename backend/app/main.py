"""青鳄量化 Pro - FastAPI 后端入口"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "strategies"))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import init_db
from app.api.dashboard import router as dashboard_router
from app.api.portfolio import router as portfolio_router
from app.api.strategy import router as strategy_router
from app.api.backtest import router as backtest_router
from app.api.market import router as market_router
from app.api.agent_gateway import router as agent_router
from app.websocket.market_ws import market_websocket

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[{settings.APP_NAME}] v{settings.APP_VERSION} starting...")
    init_db()
    yield
    print(f"[{settings.APP_NAME}] shutting down...")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(dashboard_router)
app.include_router(portfolio_router)
app.include_router(strategy_router)
app.include_router(backtest_router)
app.include_router(market_router)
app.include_router(agent_router)


@app.websocket("/ws/market")
async def ws_market(websocket):
    await market_websocket(websocket)


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
