"""
Script to reset ALL user passwords to known values
"""
import sys
import os

# Set environment variables
os.environ['DATABASE_URL'] = 'mysql+aiomysql://root:Rfcm1123581321@localhost:3306/laboratorio'
os.environ['SECRET_KEY'] = 'clave_super_segura_cambiar_en_produccion_12345'
os.environ['ALGORITHM'] = 'HS256'
os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'

sys.path.insert(0, 'backend')

import asyncio
import aiomysql
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Default passwords
DEFAULT_PASSWORDS = {
    'administradores': 'admin123',
    'laboratoristas': '123456',
    'medicos': 'medico123',
    'pacientes': 'paciente123'
}

async def fix_all_passwords():
    conn = await aiomysql.connect(
        host='localhost', port=3306,
        user='root', password='Rfcm1123581321',
        db='laboratorio'
    )
    
    async with conn.cursor() as cur:
        # Fix administradores
        print("=== Fixing ADMINISTRADORES ===")
        await cur.execute("SELECT email FROM administradores WHERE activo = 1")
        admins = await cur.fetchall()
        for admin in admins:
            email = admin[0]
            hashed = pwd_context.hash(DEFAULT_PASSWORDS['administradores'])
            await cur.execute(
                "UPDATE administradores SET password = %s WHERE email = %s",
                (hashed, email)
            )
            print(f"  Updated {email}")
        
        # Fix laboratoristas
        print("\n=== Fixing LABORATORISTAS ===")
        await cur.execute("SELECT email FROM laboratoristas WHERE activo = 1")
        labs = await cur.fetchall()
        for lab in labs:
            email = lab[0]
            hashed = pwd_context.hash(DEFAULT_PASSWORDS['laboratoristas'])
            await cur.execute(
                "UPDATE laboratoristas SET password = %s WHERE email = %s",
                (hashed, email)
            )
            print(f"  Updated {email}")
        
        # Fix medicos
        print("\n=== Fixing MEDICOS ===")
        await cur.execute("SELECT email FROM medicos WHERE activo = 1")
        meds = await cur.fetchall()
        for med in meds:
            email = med[0]
            hashed = pwd_context.hash(DEFAULT_PASSWORDS['medicos'])
            await cur.execute(
                "UPDATE medicos SET password = %s WHERE email = %s",
                (hashed, email)
            )
            print(f"  Updated {email}")
        
        # Fix pacientes
        print("\n=== Fixing PACIENTES ===")
        await cur.execute("SELECT email FROM pacientes WHERE activo = 1")
        pacs = await cur.fetchall()
        for pac in pacs:
            email = pac[0]
            hashed = pwd_context.hash(DEFAULT_PASSWORDS['pacientes'])
            await cur.execute(
                "UPDATE pacientes SET password = %s WHERE email = %s",
                (hashed, email)
            )
            print(f"  Updated {email}")
        
        await conn.commit()
    
    conn.close()
    print("\n✅ All passwords have been reset successfully!")
    print("\nDefault credentials:")
    print(f"  Administradores: */{DEFAULT_PASSWORDS['administradores']}")
    print(f"  Laboratoristas: */{DEFAULT_PASSWORDS['laboratoristas']}")
    print(f"  Medicos: */{DEFAULT_PASSWORDS['medicos']}")
    print(f"  Pacientes: */{DEFAULT_PASSWORDS['pacientes']}")

if __name__ == "__main__":
    asyncio.run(fix_all_passwords())