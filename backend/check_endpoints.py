"""Quick check: can we serialize Paciente and Laboratorista rows into their Out schemas?"""
import asyncio
from app.database import engine, AsyncSessionLocal
from app.models import Paciente, Laboratorista
from app.schemas import PacienteOut, LaboratoristaOut
from sqlalchemy import select, text

async def main():
    async with engine.connect() as conn:
        r = await conn.execute(text('SELECT COUNT(*) FROM pacientes WHERE activo=1'))
        print('Pacientes activos en DB:', r.scalar())
        r2 = await conn.execute(text('SELECT COUNT(*) FROM laboratoristas WHERE activo=1'))
        print('Laboratoristas activos en DB:', r2.scalar())

    async with AsyncSessionLocal() as db:
        # Test pacientes
        result = await db.execute(select(Paciente).where(Paciente.activo == 1).limit(3))
        pacientes = result.scalars().all()
        print(f"\nPacientes ORM objects: {len(pacientes)}")
        for p in pacientes:
            print(f"  Raw: id={p.id_paciente}, nombre={p.nombre}, genero={p.genero}, type(genero)={type(p.genero)}")
            try:
                out = PacienteOut.model_validate(p)
                print(f"  Schema OK: {out.id_paciente}")
            except Exception as e:
                print(f"  Schema ERROR: {e}")

        # Test laboratoristas
        result2 = await db.execute(select(Laboratorista).where(Laboratorista.activo == 1).limit(3))
        labs = result2.scalars().all()
        print(f"\nLaboratoristas ORM objects: {len(labs)}")
        for l in labs:
            print(f"  Raw: id={l.id_laboratorista}, nombre={l.nombre}")
            try:
                out = LaboratoristaOut.model_validate(l)
                print(f"  Schema OK: {out.id_laboratorista}")
            except Exception as e:
                print(f"  Schema ERROR: {e}")

asyncio.run(main())
