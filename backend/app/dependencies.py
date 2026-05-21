from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.config import settings
from app.schemas import TokenData
from app.models import Paciente, Medico, Laboratorista, Administrador

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
        admin_rol: str = payload.get("admin_rol")
        if email is None or rol is None:
            raise credentials_exception
        token_data = TokenData(email=email, rol=rol, admin_rol=admin_rol)
    except JWTError:
        raise credentials_exception


    user = None
    if token_data.rol == "paciente":
        stmt = select(Paciente).where(Paciente.email == token_data.email, Paciente.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    elif token_data.rol == "medico":
        stmt = select(Medico).where(Medico.email == token_data.email, Medico.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    elif token_data.rol == "laboratorista":
        stmt = select(Laboratorista).where(Laboratorista.email == token_data.email, Laboratorista.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    elif token_data.rol == "administrador":
        stmt = select(Administrador).where(Administrador.email == token_data.email, Administrador.activo == 1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
        
    return {"user": user, "rol": token_data.rol, "admin_rol": token_data.admin_rol}

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    user = current_user.get("user")
    if not hasattr(user, 'activo') or user.activo != 1:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

async def require_laboratorista(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") != "laboratorista":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Laboratorista)")
    return current_user

async def require_medico(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") != "medico":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Médico)")
    return current_user

async def require_paciente(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") != "paciente":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Paciente)")
    return current_user

async def require_administrador(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("rol") != "administrador":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Administrador)")
    return current_user

async def require_super_admin(current_user: dict = Depends(require_administrador)):
    if current_user.get("admin_rol") != "super_admin":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Super Admin)")
    return current_user

async def require_admin_general(current_user: dict = Depends(require_administrador)):
    if current_user.get("admin_rol") != "admin_general":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Admin General)")
    return current_user

async def require_admin_financiero(current_user: dict = Depends(require_administrador)):
    if current_user.get("admin_rol") != "admin_financiero":
        raise HTTPException(status_code=403, detail="No tienes permisos suficientes (Se requiere Admin Financiero)")
    return current_user
