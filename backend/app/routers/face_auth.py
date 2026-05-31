"""
Router para autenticación facial biométrica.
Proporciona endpoints para registro y autenticación con reconocimiento facial.
Usa FaceServiceV2 (método profesional con distancia coseno).
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
import json

from app.database import get_db
from app.models import Paciente, Medico, Laboratorista, Administrador
from app.models_face import FaceEmbedding, FaceAuthLog
from app.schemas import Token
from app.utils import create_access_token
from app.config import settings
from app.dependencies import get_current_user_from_token

# Usar FaceServiceV2 (más profesional, distancia coseno)
try:
    from app.services.face_service_v2 import FaceServiceV2 as FaceService
    logger = logging.getLogger(__name__)
    logger.info("✅ Usando FaceServiceV2 (método profesional con distancia coseno)")
except ImportError as e:
    from app.services.face_service import FaceService
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ FaceServiceV2 no disponible, usando V1: {e}")

router = APIRouter(
    prefix="/auth/face",
    tags=["Autenticación Facial"]
)

# Esquemas Pydantic para validación
from pydantic import BaseModel
from typing import Optional, List


class FaceRegisterRequest(BaseModel):
    """Solicitud para registrar rostro"""
    image_data: str  # Base64 de la imagen
    quality_threshold: Optional[float] = 0.3
    target_user_id: Optional[str] = None
    target_role: Optional[str] = None


class FaceLoginRequest(BaseModel):
    """Solicitud para login facial"""
    image_data: str  # Base64 de la imagen
    tabla_usuario: Optional[str] = None  # Filtrar por tabla: pacientes, medicos, laboratoristas, administradores


class FaceStatusResponse(BaseModel):
    """Respuesta del estado de registro facial"""
    has_face_registered: bool
    registration_count: int
    last_registration: Optional[datetime]
    can_register: bool


class FaceRegisterResponse(BaseModel):
    """Respuesta del registro facial"""
    success: bool
    message: str
    face_id: Optional[int]
    quality_score: Optional[float]


class FaceLoginResponse(BaseModel):
    """Respuesta del login facial"""
    success: bool
    message: str
    access_token: Optional[str]
    token_type: Optional[str]
    user_info: Optional[dict]


@router.get("/status", response_model=FaceStatusResponse)
async def get_face_registration_status(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Verifica si el usuario actual tiene un rostro registrado."""
    try:
        user_id = current_user.get("id_usuario")
        user_table = current_user.get("tabla_usuario")
        
        if not user_id or not user_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo identificar al usuario"
            )
        
        stmt = select(FaceEmbedding).where(
            and_(
                FaceEmbedding.id_usuario == str(user_id),
                FaceEmbedding.tabla_usuario == user_table,
                FaceEmbedding.activo == True
            )
        ).order_by(FaceEmbedding.creado_en.desc())
        
        result = await db.execute(stmt)
        embeddings = result.scalars().all()
        
        last_registration = None
        if embeddings:
            last_registration = embeddings[0].creado_en
        
        can_register = len(embeddings) < 3
        
        return FaceStatusResponse(
            has_face_registered=len(embeddings) > 0,
            registration_count=len(embeddings),
            last_registration=last_registration,
            can_register=can_register
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al verificar estado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar estado de registro facial"
        )


@router.post("/register", response_model=FaceRegisterResponse)
async def register_face(
    request: FaceRegisterRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Registra el rostro de un usuario autenticado.
    Usa FaceNet (128 dimensiones) - mismo modelo para registro y login.
    """
    try:
        if not FaceService.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de reconocimiento facial no disponible"
            )
        
        user_id = current_user.get("id_usuario")
        user_table = current_user.get("tabla_usuario")
        user_rol = current_user.get("rol")
        user_email = current_user.get("email")
        
        logger.info(f"Registro facial - Email: {user_email}, ID: {user_id}, Tabla: {user_table}, Rol: {user_rol}")
        
        if not user_id or not user_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo identificar al usuario"
            )
        
        # Verificar que el usuario existe
        user_exists = await get_user_info(db, str(user_id), user_table)
        if user_exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario no encontrado ({user_table})"
            )
        
        # Verificar límite (máx 3 rostros)
        stmt = select(FaceEmbedding).where(
            and_(
                FaceEmbedding.id_usuario == str(user_id),
                FaceEmbedding.tabla_usuario == user_table,
                FaceEmbedding.activo == True
            )
        )
        result = await db.execute(stmt)
        existing_embeddings = result.scalars().all()
        
        if len(existing_embeddings) >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo 3 rostros por usuario"
            )
        
        # Procesar imagen y extraer embedding
        extraction_result = FaceService.process_and_extract(request.image_data)
        
        if not extraction_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=extraction_result.get("error", "Error al procesar imagen")
            )
        
        if extraction_result["face_count"] > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Múltiples rostros detectados"
            )
        
        quality_score = extraction_result["quality_scores"][0] if extraction_result["quality_scores"] else 0.0
        if quality_score < request.quality_threshold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Calidad insuficiente ({quality_score:.2f})"
            )
        
        embedding_data = extraction_result["embeddings"][0]
        
        # Guardar embedding en BD
        new_embedding = FaceEmbedding(
            id_usuario=str(user_id),
            tabla_usuario=user_table,
            embedding_data=embedding_data,
            modelo_version="face_recognition_v2",
            calidad_promedio=quality_score,
            activo=True,
            notas=f"FaceNet - Email: {user_email} ({user_rol}) - Calidad: {quality_score:.2f}"
        )
        
        db.add(new_embedding)
        await db.commit()
        await db.refresh(new_embedding)
        
        logger.info(f"✅ Rostro registrado para {user_email} (ID: {user_id})")
        
        return FaceRegisterResponse(
            success=True,
            message=f"Rostro registrado exitosamente para {user_email}",
            face_id=new_embedding.id,
            quality_score=quality_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al registrar rostro: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar rostro"
        )


@router.post("/login", response_model=FaceLoginResponse)
async def login_with_face(
    request: FaceLoginRequest,
    db: AsyncSession = Depends(get_db),
    client_ip: str = None
):
    """
    Autentica a un usuario mediante reconocimiento facial.
    Usa distancia coseno para comparación (más precisa que euclidiana).
    """
    try:
        if not FaceService.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de reconocimiento facial no disponible"
            )
        
        client_ip = client_ip or "unknown"
        
        # Procesar imagen y extraer embedding
        extraction_result = FaceService.process_and_extract(request.image_data)
        
        if not extraction_result["success"]:
            await log_failed_attempt(db, None, None, extraction_result.get("error", "Error"), client_ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=extraction_result.get("error", "Error al procesar imagen")
            )
        
        if extraction_result["face_count"] == 0:
            await log_failed_attempt(db, None, None, "No se detectó rostro", client_ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se detectó ningún rostro en la imagen"
            )
        
        if extraction_result["face_count"] > 1:
            await log_failed_attempt(db, None, None, "Múltiples rostros", client_ip)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Múltiples rostros detectados"
            )
        
        query_embedding = extraction_result["embeddings"][0]
        logger.info(f"Embedding extraído para login - Dimensiones: {len(query_embedding)}")
        
        # Buscar embeddings activos (con filtro opcional por tabla_usuario)
        where_conditions = [
            FaceEmbedding.activo == True,
            FaceEmbedding.intentos_fallidos < FaceService.MAX_FAILED_ATTEMPTS
        ]
        if request.tabla_usuario:
            where_conditions.append(FaceEmbedding.tabla_usuario == request.tabla_usuario)
            logger.info(f"🔍 Buscando solo en tabla: {request.tabla_usuario}")
        
        stmt = select(FaceEmbedding).where(and_(*where_conditions))
        result = await db.execute(stmt)
        all_embeddings = result.scalars().all()
        
        if len(all_embeddings) == 0:
            await log_failed_attempt(db, None, None, "No hay rostros registrados", client_ip)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay usuarios con rostro registrado en el sistema"
            )
        
        # Preparar candidatos
        candidates = []
        for emb in all_embeddings:
            embedding = emb.embedding_data
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except:
                    logger.error(f"Error parseando embedding para usuario {emb.id_usuario}")
                    continue
            if not isinstance(embedding, (list, tuple)):
                continue
                
            candidates.append({
                "id_usuario": emb.id_usuario,
                "tabla_usuario": emb.tabla_usuario,
                "embedding": embedding,
                "face_id": emb.id,
                "failed_attempts": emb.intentos_fallidos,
                "last_failed": emb.ultimo_intento_fallido
            })
        
        logger.info(f"Comparando con {len(candidates)} candidatos")
        
        # Buscar mejor match
        best_match, best_distance = FaceService.find_best_match(
            query_embedding, 
            candidates
        )
        
        if best_match is None:
            await log_failed_attempt(db, None, None, 
                f"No match. Mejor distancia: {best_distance:.4f}", client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No se reconoció el rostro. Intente nuevamente o use credenciales tradicionales."
            )
        
        # Verificar bloqueo por intentos fallidos
        allowed, reason = FaceService.should_allow_attempt(
            best_match.get("last_failed"),
            best_match.get("failed_attempts", 0)
        )
        
        if not allowed:
            await log_failed_attempt(db, best_match["id_usuario"], best_match["tabla_usuario"], reason, client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=reason
            )
        
        # Resetear intentos fallidos
        await reset_failed_attempts(db, best_match["face_id"])
        
        # Registrar intento exitoso
        await log_successful_attempt(db, best_match["id_usuario"], best_match["tabla_usuario"], best_distance, client_ip)
        
        # Obtener información del usuario
        user_info = await get_user_info(db, best_match["id_usuario"], best_match["tabla_usuario"])
        
        if user_info is None:
            logger.error(f"Usuario no encontrado: {best_match['id_usuario']} en {best_match['tabla_usuario']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Determinar rol (debe ser 'administrador' para admins, no 'super_admin')
        rol = best_match["tabla_usuario"]
        if rol in ["administradores", "administrador"]:
            rol = "administrador"
        elif rol == "pacientes":
            rol = "paciente"
        elif rol == "medicos":
            rol = "medico"
        elif rol == "laboratoristas":
            rol = "laboratorista"
        
        # Generar token JWT (mismo formato que auth.py)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": user_info.email,
            "rol": rol,
            "id_usuario": best_match["id_usuario"],
            "auth_method": "face_recognition"
        }
        
        # Agregar rol_administrador si aplica
        if rol == "administrador":
            token_data["rol_administrador"] = getattr(user_info, 'rol_administrador', 'admin_general')
        
        access_token = create_access_token(data=token_data, expires_delta=access_token_expires)
        
        logger.info(f"✅ Login facial exitoso para {user_info.email}")
        
        return FaceLoginResponse(
            success=True,
            message="Autenticación facial exitosa",
            access_token=access_token,
            token_type="bearer",
            user_info={
                "email": user_info.email,
                "rol": rol,
                "id_usuario": best_match["id_usuario"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login facial: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en autenticación facial"
        )


@router.get("/users-by-role/{role}")
async def get_users_by_role(
    role: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene la lista de usuarios de un rol específico (solo admin)."""
    try:
        user_rol = current_user.get("rol")
        if user_rol not in ["administrador", "recepcionista"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos"
            )
        
        users = []
        
        if role == "paciente":
            stmt = select(Paciente).where(Paciente.activo == 1)
            result = await db.execute(stmt)
            for p in result.scalars().all():
                users.append({
                    "id": p.id_paciente,
                    "nombre": f"{p.nombre} {p.apellido_paterno} {p.apellido_materno or ''}".strip(),
                    "email": p.email
                })
        elif role == "medico":
            stmt = select(Medico).where(Medico.activo == 1)
            result = await db.execute(stmt)
            for m in result.scalars().all():
                users.append({
                    "id": m.id_medico,
                    "nombre": f"{m.nombre} {m.apellido_paterno} {m.apellido_materno or ''}".strip(),
                    "email": m.email
                })
        elif role == "laboratorista":
            stmt = select(Laboratorista).where(Laboratorista.activo == 1)
            result = await db.execute(stmt)
            for l in result.scalars().all():
                users.append({
                    "id": l.id_laboratorista,
                    "nombre": f"{l.nombre} {l.apellido_paterno} {l.apellido_materno or ''}".strip(),
                    "email": l.email
                })
        elif role == "administrador":
            stmt = select(Administrador).where(Administrador.activo == 1)
            result = await db.execute(stmt)
            for a in result.scalars().all():
                users.append({
                    "id": a.id_administrador,
                    "nombre": f"{a.nombre} {a.apellido_paterno} {a.apellido_materno or ''}".strip(),
                    "email": a.email
                })
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rol no válido: {role}")
        
        return {"users": users, "role": role}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener usuarios: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al obtener usuarios")


@router.post("/register-for-user", response_model=FaceRegisterResponse)
async def register_face_for_user(
    request: FaceRegisterRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    """Registra rostro para usuario específico (solo admin)."""
    try:
        user_rol = current_user.get("rol")
        if user_rol not in ["administrador", "recepcionista"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
        
        target_user_id = request.target_user_id
        target_role = request.target_role
        
        if not target_user_id or not target_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se requiere target_user_id y target_role")
        
        if not FaceService.is_available():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio no disponible")
        
        role_to_table = {"paciente": "pacientes", "medico": "medicos", "laboratorista": "laboratoristas", "administrador": "administradores"}
        user_table = role_to_table.get(target_role)
        
        if not user_table:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rol no válido: {target_role}")
        
        target_user = await get_user_info(db, target_user_id, user_table)
        if target_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario no encontrado ({user_table})")
        
        # Verificar límite
        stmt = select(FaceEmbedding).where(
            and_(FaceEmbedding.id_usuario == str(target_user_id), FaceEmbedding.tabla_usuario == user_table, FaceEmbedding.activo == True)
        )
        result = await db.execute(stmt)
        if len(result.scalars().all()) >= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Máximo 3 rostros")
        
        # Procesar imagen
        extraction_result = FaceService.process_and_extract(request.image_data)
        
        if not extraction_result["success"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=extraction_result.get("error", "Error"))
        
        if extraction_result["face_count"] > 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Múltiples rostros")
        
        quality_score = extraction_result["quality_scores"][0] if extraction_result["quality_scores"] else 0.0
        if quality_score < request.quality_threshold:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Calidad insuficiente ({quality_score:.2f})")
        
        embedding_data = extraction_result["embeddings"][0]
        
        # Guardar
        new_embedding = FaceEmbedding(
            id_usuario=str(target_user_id), tabla_usuario=user_table,
            embedding_data=embedding_data, modelo_version="face_recognition_v2",
            calidad_promedio=quality_score, activo=True,
            notas=f"Admin - Email: {target_user.email} ({target_role}) - Calidad: {quality_score:.2f}"
        )
        
        db.add(new_embedding)
        await db.commit()
        await db.refresh(new_embedding)
        
        logger.info(f"✅ Rostro registrado para {target_user.email} por admin")
        
        return FaceRegisterResponse(
            success=True, message=f"Rostro registrado para {target_user.email}",
            face_id=new_embedding.id, quality_score=quality_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registrando rostro para usuario: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al registrar rostro")


@router.get("/info")
async def get_face_auth_info():
    return FaceService.get_model_info()


# Funciones auxiliares

async def log_failed_attempt(db, user_id, user_table, reason, ip_address):
    try:
        log = FaceAuthLog(id_usuario=user_id, tabla_usuario=user_table, exito=False,
                         score_similitud=None, ip_address=ip_address, notas=reason)
        db.add(log)
        await db.commit()
        
        if user_id and user_table:
            stmt = select(FaceEmbedding).where(
                and_(FaceEmbedding.id_usuario == user_id, FaceEmbedding.tabla_usuario == user_table, FaceEmbedding.activo == True)
            ).limit(1)
            result = await db.execute(stmt)
            embedding = result.scalar_one_or_none()
            if embedding:
                embedding.intentos_fallidos += 1
                embedding.ultimo_intento_fallido = datetime.now()
                await db.commit()
    except Exception as e:
        logger.error(f"Error registrando intento fallido: {e}")


async def log_successful_attempt(db, user_id, user_table, score, ip_address):
    try:
        log = FaceAuthLog(id_usuario=user_id, tabla_usuario=user_table, exito=True,
                         score_similitud=score, ip_address=ip_address)
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.error(f"Error registrando intento exitoso: {e}")


async def reset_failed_attempts(db, face_id):
    try:
        stmt = select(FaceEmbedding).where(FaceEmbedding.id == face_id)
        result = await db.execute(stmt)
        embedding = result.scalar_one_or_none()
        if embedding:
            embedding.intentos_fallidos = 0
            embedding.ultimo_intento_fallido = None
            await db.commit()
    except Exception as e:
        logger.error(f"Error reseteando intentos: {e}")


async def get_user_info(db, user_id, user_table):
    try:
        if user_table == "pacientes":
            stmt = select(Paciente).where(and_(Paciente.id_paciente == user_id, Paciente.activo == 1))
        elif user_table == "medicos":
            stmt = select(Medico).where(and_(Medico.id_medico == user_id, Medico.activo == 1))
        elif user_table == "laboratoristas":
            stmt = select(Laboratorista).where(and_(Laboratorista.id_laboratorista == user_id, Laboratorista.activo == 1))
        elif user_table == "administradores":
            stmt = select(Administrador).where(and_(Administrador.id_administrador == int(user_id), Administrador.activo == 1))
        else:
            return None
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error obteniendo usuario: {e}")
        return None