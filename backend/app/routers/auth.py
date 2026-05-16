from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.crud import authenticate_user
from app.utils import create_access_token
from app.schemas import Token
from app.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    En form_data.username se espera el email.
    """
    auth_result = await authenticate_user(db, form_data.username, form_data.password)
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_result["user"]
    rol = auth_result["rol"]
    
    # Determinar el ID del usuario según el rol
    user_id = None
    if rol == "laboratorista":
        user_id = user.id_laboratorista
    elif rol == "medico":
        user_id = user.id_medico
    elif rol == "paciente":
        user_id = user.id_paciente

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agregar 'sub' (subject -> email), 'rol' y el ID específico al token
    access_token = create_access_token(
        data={"sub": user.email, "rol": rol, "id_usuario": user_id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
