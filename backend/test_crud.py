import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.crud import paciente_crud, laboratorista_crud
from app.database import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_crud():
    async with async_session() as db:
        print("Testing Pacientes...")
        try:
            pacientes = await paciente_crud.get_multi(db)
            print("Pacientes loaded:", len(pacientes))
        except Exception as e:
            print("Error loading pacientes:", e)
            
        print("Testing Laboratoristas...")
        try:
            laboratoristas = await laboratorista_crud.get_multi(db)
            print("Laboratoristas loaded:", len(laboratoristas))
        except Exception as e:
            print("Error loading laboratoristas:", e)

asyncio.run(test_crud())
