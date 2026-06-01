import asyncio
import aiomysql
from app.utils import hash_password

async def reset_pwd():
    conn = await aiomysql.connect(host='localhost', port=3306,
                                  user='root', password='Rfcm1123581321',
                                  db='laboratorio')
    async with conn.cursor() as cur:
        new_pwd = hash_password("admin")
        await cur.execute("UPDATE administradores SET password=%s WHERE email='rotherickcalderon.admin@labotik.com'", (new_pwd,))
        await conn.commit()
    conn.close()

asyncio.run(reset_pwd())
