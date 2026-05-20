from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.config import settings
from app.schemas import TokenData
from app.crud import paciente_crud, medico_crud, laboratorista_crud

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/access-token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        rol: str = payload.get("rol")
        if email is None or rol is None:
            raise credentials_exception
        token_data = TokenData(email=email, rol=rol)
    except JWTError:
        raise credentials_exception

    user = None
    if token_data.rol == "paciente":
        # Necesitamos buscar por email, pero los CRUD base que tenemos por defecto buscan por ID en get()
        # Así que mejor usamos select() o creamos un método get_by_email. Por ahora, buscaremos manual o con el crud si tiene método.
        # En crud.py no tenemos get_by_email genérico. Lo haremos directamente:
        from sqlalchemy import select
        from app.models import Paciente, Medico, Laboratorista
        
        stmt = select(Paciente).where(Paciente.email == token_data.email, Paciente.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    elif token_data.rol == "medico":
        from sqlalchemy import select
        from app.models import Medico
        stmt = select(Medico).where(Medico.email == token_data.email, Medico.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    elif token_data.rol == "laboratorista":
        from sqlalchemy import select
        from app.models import Laboratorista
        stmt = select(Laboratorista).where(Laboratorista.email == token_data.email, Laboratorista.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    elif token_data.rol == "administrador":
        from sqlalchemy import select
        from app.models import Administrador
        stmt = select(Administrador).where(Administrador.email == token_data.email, Administrador.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
        
    return {"user": user, "rol": token_data.rol}

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    user = current_user.get("user")
    if not hasattr(user, 'activo') or user.activo != 1:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

async def require_laboratorista(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") not in ["laboratorista", "administrador"]:
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Laboratorista)")
    return current_user

async def require_medico(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") not in ["medico", "administrador"]:
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Médico)")
    return current_user

async def require_paciente(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") not in ["paciente", "administrador"]:
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Paciente)")
    return current_user

async def require_admin(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") != "administrador":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Administrador)")
    return current_user

async def require_admin_or_laboratorista(current_user: dict = Depends(get_current_active_user)):
    rol = current_user.get("rol")
    if rol not in ["administrador", "laboratorista"]:
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Administrador o Laboratorista)")
    return current_user
