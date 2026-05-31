import asyncio
import aiomysql
import sys
sys.path.insert(0, 'backend')
from app.utils import verify_password, hash_password

TEST_PASSWORD = "admin123"

async def check_users():
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
            ok = verify_password(TEST_PASSWORD, pwd_hash) if pwd_hash else False
            print(f"  ID={a['id_administrador']} email={a['email']} activo={a['activo']} rol={a['rol_administrador']} hash_ok={ok} hash_prefix={str(pwd_hash)[:20]}")

        # Check laboratoristas
        await cur.execute("SELECT id_laboratorista, email, password, activo FROM laboratoristas LIMIT 10;")
        labs = await cur.fetchall()
        print("\n=== LABORATORISTAS ===")
        for l in labs:
            pwd_hash = l.get('password', '')
            ok = verify_password(TEST_PASSWORD, pwd_hash) if pwd_hash else False
            print(f"  ID={l['id_laboratorista']} email={l['email']} activo={l['activo']} hash_ok={ok} hash_prefix={str(pwd_hash)[:20]}")

        # Check pacientes  
        await cur.execute("SELECT id_paciente, email, password, activo FROM pacientes LIMIT 10;")
        pacs = await cur.fetchall()
        print("\n=== PACIENTES ===")
        for p in pacs:
            pwd_hash = p.get('password', '')
            ok = verify_password(TEST_PASSWORD, pwd_hash) if pwd_hash else False
            print(f"  ID={p['id_paciente']} email={p['email']} activo={p['activo']} hash_ok={ok} hash_prefix={str(pwd_hash)[:20]}")

    conn.close()

asyncio.run(check_users())
