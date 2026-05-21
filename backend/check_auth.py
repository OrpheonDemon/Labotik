import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.config import settings
from app.models import Medico, Paciente, Laboratorista, Administrador
from app.utils import verify_password, hash_password

async def check():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # Verificar médico
        stmt = select(Medico).where(Medico.email == "medico@labotik.com")
        result = await db.execute(stmt)
        medico = result.scalar_one_or_none()

        if medico:
            print(f"[OK] Medico encontrado: {medico.nombre} {medico.apellido_paterno}")
            print(f"     Hash en DB: {medico.password[:30]}...")
            ok = verify_password("password", medico.password)
            print(f"     verify_password('password', hash) = {ok}")
            if not ok:
                print("     [FIX] Actualizando password del medico...")
                medico.password = hash_password("password")
                await db.commit()
                print("     [OK] Password actualizado correctamente.")
        else:
            print("[ERROR] No se encontro ningun medico con email medico@labotik.com")

        # Verificar paciente
        stmt = select(Paciente).where(Paciente.email == "paciente@labotik.com")
        result = await db.execute(stmt)
        paciente = result.scalar_one_or_none()
        if paciente:
            ok = verify_password("password", paciente.password)
            print(f"[OK] Paciente encontrado - verify_password = {ok}")
            if not ok:
                paciente.password = hash_password("password")
                await db.commit()
                print("     [FIX] Password de paciente actualizado.")
        else:
            print("[ERROR] No se encontro paciente@labotik.com")

        # Verificar laboratorista
        stmt = select(Laboratorista).where(Laboratorista.email == "laboratorista@labotik.com")
        result = await db.execute(stmt)
        lab = result.scalar_one_or_none()
        if lab:
            ok = verify_password("password", lab.password)
            print(f"[OK] Laboratorista encontrado - verify_password = {ok}")
            if not ok:
                lab.password = hash_password("password")
                await db.commit()
                print("     [FIX] Password de laboratorista actualizado.")
        else:
            print("[ERROR] No se encontro laboratorista@labotik.com")

        # Verificar admin
        stmt = select(Administrador).where(Administrador.email == "admin@labotik.com")
        result = await db.execute(stmt)
        admin = result.scalar_one_or_none()
        if admin:
            ok = verify_password("password", admin.password)
            print(f"[OK] Admin encontrado - verify_password = {ok}")
            if not ok:
                admin.password = hash_password("password")
                await db.commit()
                print("     [FIX] Password de admin actualizado.")
        else:
            print("[ERROR] No se encontro admin@labotik.com")

    await engine.dispose()
    print("\nDiagnostico completado.")

if __name__ == "__main__":
    asyncio.run(check())
