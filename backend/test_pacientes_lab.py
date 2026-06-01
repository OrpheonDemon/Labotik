"""
Test the pacientes and laboratoristas endpoints
"""
import asyncio
import sys
from app.database import engine
from app import crud
from sqlalchemy import text

async def test():
    async with engine.connect() as conn:
        # Test pacientes
        result = await conn.execute(text("SELECT id_paciente, nombre, apellido_paterno, email, activo FROM pacientes LIMIT 5"))
        rows = result.fetchall()
        print(f"Pacientes found: {len(rows)}")
        for r in rows:
            print(f"  ID={r[0]}, nombre={r[1]}, activo={r[2]}")
        
        # Test laboratoristas
        result = await conn.execute(text("SELECT id_laboratorista, nombre, apellido_paterno, email, activo FROM laboratoristas LIMIT 5"))
        rows = result.fetchall()
        print(f"Laboratoristas found: {len(rows)}")
        for r in rows:
            print(f"  ID={r[0]}, nombre={r[1]}, activo={r[3]}")
        
        # Check if any table has SELECT restrictions
        result = await conn.execute(text("SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='laboratorio' AND TABLE_NAME IN ('pacientes','laboratoristas') AND COLUMN_NAME='activo'"))
        rows = result.fetchall()
        print(f"Column 'activo' check: {len(rows)} rows")
        for r in rows:
            print(f"  Table {r[0]} has column {r[1]}")
    
    # Test the CRUD functions
    async with engine.connect() as db:
        pacientes = await crud.paciente_crud.get_multi(db, 0, 100)
        print(f"\nCRUD pacientes.get_multi: {len(pacientes)} items")
        for p in pacientes:
            print(f"  ID={p.id_paciente}, nombre={p.nombre}, activo={p.activo}")
        
        laboratoristas = await crud.laboratorista_crud.get_multi(db, 0, 100)
        print(f"\nCRUD laboratoristas.get_multi: {len(laboratoristas)} items")
        for l in laboratoristas:
            print(f"  ID={l.id_laboratorista}, nombre={l.nombre}, activo={l.activo}")

if __name__ == "__main__":
    asyncio.run(test())