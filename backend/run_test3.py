import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app import crud

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_list():
    async with AsyncSessionLocal() as db:
        pacientes = await crud.paciente_crud.get_multi(db, skip=0, limit=10)
        laboratoristas = await crud.laboratorista_crud.get_multi(db, skip=0, limit=10)
        print('Pacientes loaded:', len(pacientes))
        print('Laboratoristas loaded:', len(laboratoristas))

asyncio.run(test_list())
