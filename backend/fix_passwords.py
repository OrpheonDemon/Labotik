"""
Fix passwords in the database - rehash them with compatible bcrypt version 3.x
"""
import asyncio
from app.database import engine
from app.utils import hash_password, verify_password
from sqlalchemy import text

async def fix_passwords():
    async with engine.begin() as conn:
        # Fix laboratoristas
        result = await conn.execute(text("SELECT id_laboratorista, email, password FROM laboratoristas WHERE activo = 1"))
        users = result.fetchall()
        print(f"LABORATORISTAS: {len(users)} found")
        for u in users:
            old_hash = u[2]
            # if can't verify with "123456", rehash it
            if not verify_password("123456", old_hash):
                new_hash = hash_password("123456")
                await conn.execute(
                    text("UPDATE laboratoristas SET password = :pwd WHERE id_laboratorista = :id"),
                    {"pwd": new_hash, "id": u[0]}
                )
                print(f"  Fixed: {u[1]} -> rehashed password to '123456'")
            else:
                print(f"  OK: {u[1]} -> password works")

        # Fix pacientes
        result = await conn.execute(text("SELECT id_paciente, email, password FROM pacientes WHERE activo = 1"))
        users = result.fetchall()
        print(f"\nPACIENTES: {len(users)} found")
        for u in users:
            old_hash = u[2]
            if not verify_password("123456", old_hash):
                new_hash = hash_password("123456")
                await conn.execute(
                    text("UPDATE pacientes SET password = :pwd WHERE id_paciente = :id"),
                    {"pwd": new_hash, "id": u[0]}
                )
                print(f"  Fixed: {u[1]} -> rehashed password to '123456'")
            else:
                print(f"  OK: {u[1]} -> password works")

        # Fix administradores
        result = await conn.execute(text("SELECT id_administrador, email, password FROM administradores WHERE activo = 1"))
        users = result.fetchall()
        print(f"\nADMINISTRADORES: {len(users)} found")
        for u in users:
            old_hash = u[2]
            # Try common passwords
            for pwd_attempt in ["admin123", "123456", "admin"]:
                if verify_password(pwd_attempt, old_hash):
                    print(f"  OK: {u[1]} -> password works with '{pwd_attempt}'")
                    break
            else:
                # Rehash with a default password
                new_hash = hash_password("admin123")
                await conn.execute(
                    text("UPDATE administradores SET password = :pwd WHERE id_administrador = :id"),
                    {"pwd": new_hash, "id": u[0]}
                )
                print(f"  Fixed: {u[1]} -> rehashed password to 'admin123'")

    print("\n=== VERIFICATION ===")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT email, password FROM laboratoristas WHERE activo = 1 LIMIT 1"))
        u = result.fetchone()
        print(f"Laboratorista {u[0]}: verify '123456' = {verify_password('123456', u[1])}")
        
        result = await conn.execute(text("SELECT email, password FROM administradores WHERE activo = 1 LIMIT 1"))
        u = result.fetchone()
        print(f"Admin {u[0]}: verify 'admin123' = {verify_password('admin123', u[1])}")

asyncio.run(fix_passwords())