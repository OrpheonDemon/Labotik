import asyncio
from datetime import timedelta
from app.auth_utils import create_access_token

async def get_token():
    # Creamos un token falso para admin1
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": "admin1", "rol": "administrador"},
        expires_delta=access_token_expires
    )
    print("TOKEN:", access_token)

asyncio.run(get_token())
