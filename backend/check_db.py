import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import Medico
from app.config import settings

async def check():
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        stmt = select(Medico)
        result = await db.execute(stmt)
        medicos = result.scalars().all()
        for m in medicos:
            print(f"Medico: {m.email}, Password Hash: {m.password}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
