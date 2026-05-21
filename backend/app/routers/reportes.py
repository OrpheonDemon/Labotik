from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db
from app.audit_logger import log_audit
from app.dependencies import get_current_user

router = APIRouter(prefix="/reportes", tags=["Reportes"])

@router.get("/", response_model=list[schemas.ReporteOut])
async def list_reportes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.reporte_crud.get_multi(db, skip, limit)

@router.get("/{id_reporte}", response_model=schemas.ReporteOut)
async def get_reporte(id_reporte: int, db: AsyncSession = Depends(get_db)):
    reporte = await crud.reporte_crud.get(db, id_reporte)
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return reporte

@router.post("/", response_model=schemas.ReporteOut, status_code=201)
async def create_reporte(
    reporte_in: schemas.ReporteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    nuevo_reporte = await crud.reporte_crud.create(db, reporte_in)
    user_id = getattr(current_user.get("user"), f"id_{current_user.get('rol')}", getattr(current_user.get("user"), "id_admin", None))
    await log_audit(db, user_id, "CREACION", f"Generó un reporte para la solicitud #{reporte_in.id_solicitud}")
    return nuevo_reporte

@router.put("/{id_reporte}", response_model=schemas.ReporteOut)
async def update_reporte(
    id_reporte: int,
    reporte_in: schemas.ReporteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    updated = await crud.reporte_crud.update(db, id_reporte, reporte_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
    user_id = getattr(current_user.get("user"), f"id_{current_user.get('rol')}", getattr(current_user.get("user"), "id_admin", None))
    await log_audit(db, user_id, "ACTUALIZACION", f"Actualizó el reporte #{id_reporte}")
    
    return updated

@router.delete("/{id_reporte}")
async def delete_reporte(
    id_reporte: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    deleted = await crud.reporte_crud.soft_delete(db, id_reporte)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
        
    user_id = getattr(current_user.get("user"), f"id_{current_user.get('rol')}", getattr(current_user.get("user"), "id_admin", None))
    await log_audit(db, user_id, "ELIMINACION", f"Eliminó el reporte #{id_reporte}")
    
    return {"message": "Reporte desactivado (borrado lógico)"}