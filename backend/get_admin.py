import asyncio
import aiomysql

async def get_admin():
    conn = await aiomysql.connect(host='localhost', port=3306,
                                  user='root', password='Rfcm1123581321',
                                  db='laboratorio')
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM administradores LIMIT 1;")
        print("ADMIN:", await cur.fetchall())
        
        await cur.execute("SELECT * FROM medicos LIMIT 1;")
        print("MEDICO:", await cur.fetchall())
    conn.close()

asyncio.run(get_admin())
