"""
Script para verificar embeddings faciales en la base de datos.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

async def check_embeddings():
    async with engine.connect() as conn:
        # Verificar si la tabla existe
        try:
            result = await conn.execute(text("SHOW TABLES LIKE 'face_embeddings'"))
            tables = result.fetchall()
            if not tables:
                print("❌ La tabla 'face_embeddings' no existe")
                return
            
            print("✓ Tabla 'face_embeddings' existe")
            
            # Contar embeddings
            result = await conn.execute(text("SELECT COUNT(*) as total FROM face_embeddings"))
            total = result.scalar()
            print(f"✓ Total de embeddings: {total}")
            
            if total > 0:
                # Mostrar los primeros 5
                result = await conn.execute(text("SELECT id, id_usuario, tabla_usuario, calidad_promedio, notas FROM face_embeddings LIMIT 5"))
                rows = result.fetchall()
                print("\nEmbeddings encontrados:")
                for row in rows:
                    print(f"  - ID: {row[0]}, Usuario: {row[1]}, Tabla: {row[2]}, Calidad: {row[3]}, Notas: {row[4]}")
            else:
                print("⚠️ No hay embeddings registrados")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_embeddings())