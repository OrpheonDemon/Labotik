from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.crud import authenticate_user
from app.utils import create_access_token
from app.schemas import Token
from app.config import settings
from app.audit_logger import log_audit
from app.dependencies import get_current_user

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
    if not auth_result or auth_result.get("error") == "duplicated_email":
        detail = "Correo o contraseña incorrectos"
        if auth_result and auth_result.get("error") == "duplicated_email":
            detail = "El correo está asociado a más de un tipo de usuario. Contacta al administrador para resolver el acceso."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_result["user"]
    rol = auth_result["rol"]
    
    # Determinar el ID del usuario según el rol
    user_id = None
    admin_rol = None
    if rol == "laboratorista":
        user_id = user.id_laboratorista
    elif rol == "medico":
        user_id = user.id_medico
    elif rol == "paciente":
        user_id = user.id_paciente
    elif rol == "administrador":
        user_id = user.id_admin
        admin_rol = user.rol

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agregar 'sub' (subject -> email), 'rol', 'id_usuario' y rol específico de administrador al token
    token_payload = {"sub": user.email, "rol": rol, "id_usuario": user_id}
    if admin_rol:
        token_payload["admin_rol"] = admin_rol

    access_token = create_access_token(
        data=token_payload,
        expires_delta=access_token_expires
    )
    
    # Audit log
    await log_audit(db, user_id, "LOGIN", f"Inicio de sesión exitoso (Rol: {rol})")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = current_user["user"]
    rol = current_user["rol"]
    
    user_id = None
    if rol == "laboratorista":
        user_id = user.id_laboratorista
    elif rol == "medico":
        user_id = user.id_medico
    elif rol == "paciente":
        user_id = user.id_paciente
    elif rol == "administrador":
        user_id = user.id_admin

    await log_audit(db, user_id, "LOGOUT", "Cierre de sesión")
    return {"message": "Logout auditado"}
