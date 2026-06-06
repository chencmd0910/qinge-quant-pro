"""应用配置"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Qinge Quant Pro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qinge:qinge123@localhost:5432/qinge_quant"
    DATABASE_URL_SYNC: str = "postgresql://qinge:qinge123@localhost:5432/qinge_quant"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Trading
    INITIAL_CAPITAL: float = 10_000_000
    MAX_POSITIONS: int = 30
    COMMISSION_RATE: float = 0.0003
    SLIPPAGE_BPS: float = 2

    # Data
    DATA_DIR: str = "./data"
    STRATEGIES_DIR: str = "../strategies"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
