"""
Direct test of bcrypt functionality
"""
import sys
import os

# Set environment variables
os.environ['DATABASE_URL'] = 'mysql+aiomysql://root:Rfcm1123581321@localhost:3306/laboratorio'
os.environ['SECRET_KEY'] = 'clave_super_segura_cambiar_en_produccion_12345'
os.environ['ALGORITHM'] = 'HS256'
os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'

sys.path.insert(0, 'backend')

from passlib.context import CryptContext
import bcrypt

print("=== Testing bcrypt directly ===")
password = "test123"

# Test 1: Using bcrypt library directly
print("\n1. Testing bcrypt library directly:")
try:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"   Hashed: {hashed}")
    result = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    print(f"   Verify: {result}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Using passlib with bcrypt
print("\n2. Testing passlib with bcrypt:")
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash(password)
    print(f"   Hashed: {hashed}")
    result = pwd_context.verify(hashed, password)
    print(f"   Verify: {result}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Check bcrypt version
print("\n3. Bcrypt version info:")
try:
    print(f"   bcrypt.__version__: {bcrypt.__version__}")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Test with the actual password from database
print("\n4. Testing with actual admin password:")
try:
    import asyncio
    import aiomysql
    
    async def test_db():
        conn = await aiomysql.connect(
            host='localhost', port=3306,
            user='root', password='Rfcm1123581321',
            db='laboratorio'
        )
        
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT password FROM administradores WHERE email = 'rotherickcalderon.admin@labotik.com'")
            result = await cur.fetchone()
            if result:
                stored_hash = result['password']
                print(f"   Stored hash: {stored_hash[:30]}...")
                
                # Test with bcrypt directly
                try:
                    bcrypt_result = bcrypt.checkpw(b'admin123', stored_hash.encode('utf-8'))
                    print(f"   bcrypt.checkpw result: {bcrypt_result}")
                except Exception as e:
                    print(f"   bcrypt.checkpw error: {e}")
                
                # Test with passlib
                try:
                    passlib_result = pwd_context.verify(stored_hash, 'admin123')
                    print(f"   passlib.verify result: {passlib_result}")
                except Exception as e:
                    print(f"   passlib.verify error: {e}")
        
        conn.close()
    
    asyncio.run(test_db())
except Exception as e:
    print(f"   Error: {e}")

print("\n=== Done ===")