"""
Script to reset all user passwords to known values
"""
import sys
import os

# Set environment variables before importing anything else
os.environ['DATABASE_URL'] = 'mysql+aiomysql://root:Rfcm1123581321@localhost:3306/laboratorio'
os.environ['SECRET_KEY'] = 'clave_super_segura_cambiar_en_produccion_12345'
os.environ['ALGORITHM'] = 'HS256'
os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'

# Add backend to path
sys.path.insert(0, 'backend')

import asyncio
import aiomysql
from passlib.context import CryptContext

# Use bcrypt to hash passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define default passwords for each role
DEFAULT_PASSWORDS = {
    'administradores': {
        'rotherickcalderon.admin@labotik.com': 'admin123',
        'armandoquito@labotik.com': 'admin123',
        'mariabonita@labotik.com': 'admin123'
    },
    'laboratoristas': {
        'maritzahuanca@labotik.com': '123456'
    },
    'medicos': {},
    'pacientes': {}
}

async def fix_passwords():
    conn = await aiomysql.connect(
        host='localhost', port=3306,
        user='root', password='Rfcm1123581321',
        db='laboratorio'
    )
    
    async with conn.cursor() as cur:
        # Fix administradores
        print("=== Fixing ADMINISTRADORES ===")
        for email, password in DEFAULT_PASSWORDS['administradores'].items():
            hashed = pwd_context.hash(password)
            await cur.execute(
                "UPDATE administradores SET password = %s WHERE email = %s",
                (hashed, email)
            )
            print(f"  Updated {email} with new password hash")
        
        # Fix laboratoristas
        print("\n=== Fixing LABORATORISTAS ===")
        for email, password in DEFAULT_PASSWORDS['laboratoristas'].items():
            hashed = pwd_context.hash(password)
            await cur.execute(
                "UPDATE laboratoristas SET password = %s WHERE email = %s",
                (hashed, email)
            )
            print(f"  Updated {email} with new password hash")
        
        await conn.commit()
    
    conn.close()
    print("\n✅ All passwords have been reset successfully!")
    print("\nDefault credentials:")
    print("  Administradores:")
    print("    - rotherickcalderon.admin@labotik.com / admin123")
    print("    - armandoquito@labotik.com / admin123")
    print("    - mariabonita@labotik.com / admin123")
    print("  Laboratoristas:")
    print("    - maritzahuanca@labotik.com / 123456")

if __name__ == "__main__":
    asyncio.run(fix_passwords())