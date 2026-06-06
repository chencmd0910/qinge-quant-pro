"""数据迁移：从quant.db导入到PostgreSQL"""
import sqlite3
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import Base
from app.models.models import MarketData, Position

OLD_DB = "../quant-trading-system/data/quant.db"
NEW_DB = "postgresql+asyncpg://qinge:qinge123@localhost:5432/qinge_quant"


async def migrate():
    """迁移数据"""
    # 读旧数据
    old = sqlite3.connect(OLD_DB)
    klines = old.execute(
        "SELECT code, trade_date, open, high, low, close, volume, amount, change_pct FROM daily_kline"
    ).fetchall()
    old.close()

    print(f"Read {len(klines)} kline rows from old DB")

    # 写新数据库
    engine = create_async_engine(NEW_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    batch_size = 5000
    for i in range(0, len(klines), batch_size):
        batch = klines[i:i + batch_size]
        async with session_factory() as session:
            for row in batch:
                session.add(MarketData(
                    symbol=row[0], trade_date=row[1],
                    open=row[2], high=row[3], low=row[4], close=row[5],
                    volume=row[6], amount=row[7], change_pct=row[8],
                ))
            await session.commit()
        print(f"  Migrated {min(i + batch_size, len(klines))}/{len(klines)}")

    await engine.dispose()
    print("Migration done!")


if __name__ == "__main__":
    asyncio.run(migrate())
