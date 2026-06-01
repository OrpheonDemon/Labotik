import asyncio
import aiomysql

async def check_db():
    conn = await aiomysql.connect(host='localhost', port=3306,
                                  user='root', password='0000',
                                  db='laboratorio')
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM pacientes LIMIT 5;")
        print("PACIENTES:", await cur.fetchall())
        
        await cur.execute("SELECT * FROM laboratoristas LIMIT 5;")
        print("LABORATORISTAS:", await cur.fetchall())
        
    conn.close()

asyncio.run(check_db())
