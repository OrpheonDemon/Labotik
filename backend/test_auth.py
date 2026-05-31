"""
Test authentication with fixed bcrypt
"""
import asyncio
from app.database import AsyncSessionLocal
from app.crud import authenticate_user

async def test():
    async with AsyncSessionLocal() as db:
        print("Testing laboratorista auth...")
        result = await authenticate_user(db, 'maritzahuanca@labotik.com', '123456')
        if result:
            print(f"  OK: {result['rol']} - {result['user'].nombre} (ID: {result['user'].id_laboratorista})")
        else:
            print("  FAILED!")
        
        print("\nTesting admin auth...")
        result = await authenticate_user(db, 'rotherickcalderon.admin@labotik.com', 'admin123')
        if result:
            print(f"  OK: {result['rol']} - {result['user'].nombre} (ID: {result['user'].id_administrador})")
        else:
            print("  FAILED!")

if __name__ == "__main__":
    asyncio.run(test())