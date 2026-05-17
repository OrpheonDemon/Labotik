from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db

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
async def create_reporte(reporte_in: schemas.ReporteCreate, db: AsyncSession = Depends(get_db)):
    return await crud.reporte_crud.create(db, reporte_in)

@router.put("/{id_reporte}", response_model=schemas.ReporteOut)
async def update_reporte(id_reporte: int, reporte_in: schemas.ReporteUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.reporte_crud.update(db, id_reporte, reporte_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return updated

@router.delete("/{id_reporte}")
async def delete_reporte(id_reporte: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.reporte_crud.soft_delete(db, id_reporte)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"message": "Reporte desactivado (borrado lógico)"}