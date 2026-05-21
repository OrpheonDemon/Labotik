from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id
from app.audit_logger import log_audit
from app.dependencies import get_current_user

router = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])

@router.get("/", response_model=list[schemas.SolicitudOut])
async def list_solicitudes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.solicitud_crud.get_multi(db, skip, limit)

@router.get("/{id_solicitud}", response_model=schemas.SolicitudOut)
async def get_solicitud(id_solicitud: int, db: AsyncSession = Depends(get_db)):
    solicitud = await crud.solicitud_crud.get(db, id_solicitud)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    # Cargar detalles
    stmt = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_solicitud == id_solicitud, models.DetalleSolicitud.activo == 1)
    result = await db.execute(stmt)
    detalles = result.scalars().all()
    solicitud.detalles = detalles
    return solicitud

@router.post("/", response_model=schemas.SolicitudOut, status_code=201)
async def create_solicitud(
    solicitud_in: schemas.SolicitudCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Generar ID de solicitud
    new_id = await get_next_int_id(db, models.Solicitud, 'id_solicitud')
    # Crear solicitud
    solicitud_data = solicitud_in.dict(exclude={'detalles'})
    solicitud_data['id_solicitud'] = new_id
    solicitud_data['estado'] = 'pendiente'
    nueva_solicitud = models.Solicitud(**solicitud_data)
    db.add(nueva_solicitud)
    await db.flush()
    # Crear detalles
    for detalle_in in solicitud_in.detalles:
        detalle_id = await get_next_int_id(db, models.DetalleSolicitud, 'id_detalle')
        detalle = models.DetalleSolicitud(
            id_detalle=detalle_id,
            id_solicitud=new_id,
            id_prueba=detalle_in.id_prueba,
            cantidad=detalle_in.cantidad
        )
        db.add(detalle)
    await db.commit()
    await db.refresh(nueva_solicitud)
    
    # Audit log
    user_id = current_user.get("user").id_paciente if current_user.get("rol") == "paciente" else current_user.get("user").id_medico if current_user.get("rol") == "medico" else getattr(current_user.get("user"), "id_admin", None) or getattr(current_user.get("user"), "id_laboratorista", None)
    await log_audit(db, user_id, "CREACION", f"Creó la solicitud #{new_id} para el paciente {solicitud_in.id_paciente}")
    
    return nueva_solicitud

@router.put("/{id_solicitud}", response_model=schemas.SolicitudOut)
async def update_solicitud(
    id_solicitud: int,
    solicitud_in: schemas.SolicitudUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    updated = await crud.solicitud_crud.update(db, id_solicitud, solicitud_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
    user_id = getattr(current_user.get("user"), f"id_{current_user.get('rol')}", getattr(current_user.get("user"), "id_admin", None))
    await log_audit(db, user_id, "ACTUALIZACION", f"Actualizó la solicitud #{id_solicitud}")
    
    return updated

@router.delete("/{id_solicitud}")
async def delete_solicitud(
    id_solicitud: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    deleted = await crud.solicitud_crud.soft_delete(db, id_solicitud)
    if not deleted:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
    user_id = getattr(current_user.get("user"), f"id_{current_user.get('rol')}", getattr(current_user.get("user"), "id_admin", None))
    await log_audit(db, user_id, "ELIMINACION", f"Eliminó lógicamente la solicitud #{id_solicitud}")
    
    return {"message": "Solicitud desactivada (borrado lógico)"}