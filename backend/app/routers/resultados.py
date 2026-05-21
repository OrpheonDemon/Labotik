from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud, models
from app.database import get_db
from app.dependencies import require_laboratorista, get_current_active_user
from app.email_sender import send_result_email

router = APIRouter(prefix="/resultados", tags=["Resultados"])

@router.get("/", response_model=list[schemas.ResultadoOut])
async def list_resultados(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    if current_user["rol"] == "paciente":
        # Pacientes solo pueden ver sus propios resultados.
        # Hacemos JOIN seguro entre Resultado, DetalleSolicitud y Solicitud.
        from sqlalchemy import select
        stmt = (
            select(models.Resultado)
            .join(models.DetalleSolicitud, models.Resultado.id_detalle == models.DetalleSolicitud.id_detalle)
            .join(models.Solicitud, models.DetalleSolicitud.id_solicitud == models.Solicitud.id_solicitud)
            .where(
                models.Solicitud.id_paciente == current_user["user"].id_paciente,
                models.Resultado.activo == 1
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
        
    elif current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver el listado de resultados")
        
    return await crud.resultado_crud.get_multi(db, skip, limit)

@router.get("/{id_resultado}", response_model=schemas.ResultadoOut)
async def get_resultado(
    id_resultado: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    if current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver resultados individuales")
        
    resultado = await crud.resultado_crud.get(db, id_resultado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return resultado

@router.post("/", response_model=schemas.ResultadoOut, status_code=201)
async def create_resultado(
    resultado_in: schemas.ResultadoCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    # 1. Guardar resultado en DB
    nuevo_resultado = await crud.resultado_crud.create(db, resultado_in)
    
    # 2. Consultar metadatos contextuales de manera asíncrona segura
    try:
        from sqlalchemy import select
        
        # Buscar detalle
        stmt_det = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_detalle == nuevo_resultado.id_detalle)
        res_det = await db.execute(stmt_det)
        detalle = res_det.scalar_one_or_none()
        
        if detalle:
            # Buscar solicitud
            stmt_sol = select(models.Solicitud).where(models.Solicitud.id_solicitud == detalle.id_solicitud)
            res_sol = await db.execute(stmt_sol)
            solicitud = res_sol.scalar_one_or_none()
            
            if solicitud:
                # Buscar paciente
                stmt_pac = select(models.Paciente).where(models.Paciente.id_paciente == solicitud.id_paciente)
                res_pac = await db.execute(stmt_pac)
                paciente = res_pac.scalar_one_or_none()
                
                # Buscar prueba
                stmt_pru = select(models.Prueba).where(models.Prueba.id_prueba == detalle.id_prueba)
                res_pru = await db.execute(stmt_pru)
                prueba = res_pru.scalar_one_or_none()
                
                if paciente and prueba:
                    # Programar el correo en segundo plano para rapidez y evitar bloqueos en el UI
                    background_tasks.add_task(
                        send_result_email,
                        email_to=paciente.email,
                        patient_name=f"{paciente.nombre} {paciente.apellido_paterno}",
                        patient_id=paciente.id_paciente,
                        test_name=prueba.nombre,
                        result_value=nuevo_resultado.resultado,
                        is_anormal=nuevo_resultado.es_anormal,
                        observations=nuevo_resultado.observacion,
                        solicitud_id=solicitud.id_solicitud
                    )
    except Exception as e:
        print(f"[Resultados Router] Error al configurar correo de notificación: {e}")
        
    return nuevo_resultado

@router.put("/{id_resultado}", response_model=schemas.ResultadoOut)
async def update_resultado(
    id_resultado: int, 
    resultado_in: schemas.ResultadoUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    updated = await crud.resultado_crud.update(db, id_resultado, resultado_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return updated

@router.delete("/{id_resultado}")
async def delete_resultado(
    id_resultado: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    deleted = await crud.resultado_crud.soft_delete(db, id_resultado)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return {"message": "Resultado desactivado (borrado lógico)"}