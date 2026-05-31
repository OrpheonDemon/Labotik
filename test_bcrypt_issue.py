"""
Script to diagnose bcrypt password verification issue
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

# Test with different bcrypt schemes
pwd_context_default = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context_bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_PASSWORD = "admin123"

async def check_passwords():
    conn = await aiomysql.connect(
        host='localhost', port=3306,
        user='root', password='Rfcm1123581321',
        db='laboratorio'
    )
    
    async with conn.cursor(aiomysql.DictCursor) as cur:
        # Check administradores
        await cur.execute("SELECT id_administrador, email, password, activo, rol_administrador FROM administradores LIMIT 10;")
        admins = await cur.fetchall()
        print("=== ADMINISTRADORES ===")
        for a in admins:
            pwd_hash = a.get('password', '')
            if pwd_hash:
                # Try verification
                try:
                    ok_default = pwd_context_default.verify(pwd_hash, TEST_PASSWORD)
                except Exception as e:
                    ok_default = f"Error: {e}"
                
                print(f"  ID={a['id_administrador']} email={a['email']} rol={a['rol_administrador']}")
                print(f"    Hash: {pwd_hash[:50]}...")
                print(f"    Verify result: {ok_default}")
        
        print()
        
        # Check laboratoristas
        await cur.execute("SELECT id_laboratorista, email, password, activo FROM laboratoristas LIMIT 10;")
        labs = await cur.fetchall()
        print("=== LABORATORISTAS ===")
        for l in labs:
            pwd_hash = l.get('password', '')
            if pwd_hash:
                try:
                    ok = pwd_context_default.verify(pwd_hash, TEST_PASSWORD)
                except Exception as e:
                    ok = f"Error: {e}"
                
                print(f"  ID={l['id_laboratorista']} email={l['email']}")
                print(f"    Hash: {pwd_hash[:50]}...")
                print(f"    Verify result: {ok}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(check_passwords())