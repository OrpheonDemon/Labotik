from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db
from app.dependencies import require_admin_or_laboratorista
from app.models import AreaLaboratorio

router = APIRouter(prefix="/areas", tags=["Áreas"])

@router.get("/search", response_model=list[schemas.AreaOut])
async def search_areas(query: str = Query(None), db: AsyncSession = Depends(get_db)):
    # Si no hay query o es vacía, devolver todas las áreas
    if not query or query.strip() == '':
        return await crud.area_crud.get_multi(db, 0, 100)
    
    # Si hay query, buscar por id o nombre
    stmt = select(AreaLaboratorio).where(
        AreaLaboratorio.activo == 1,
        or_(AreaLaboratorio.id_area.ilike(f"%{query}%"), AreaLaboratorio.nombre.ilike(f"%{query}%"))
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/", response_model=list[schemas.AreaOut])
async def list_areas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.area_crud.get_multi(db, skip, limit)

@router.get("/{id_area}", response_model=schemas.AreaOut)
async def get_area(id_area: str, db: AsyncSession = Depends(get_db)):
    area = await crud.area_crud.get(db, id_area)
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return area

@router.post("/", response_model=schemas.AreaOut, status_code=201)
async def create_area(area_in: schemas.AreaCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_admin_or_laboratorista)):
    return await crud.area_crud.create(db, area_in)

@router.put("/{id_area}", response_model=schemas.AreaOut)
async def update_area(id_area: str, area_in: schemas.AreaUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_admin_or_laboratorista)):
    updated = await crud.area_crud.update(db, id_area, area_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return updated

@router.delete("/{id_area}")
async def delete_area(id_area: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_admin_or_laboratorista)):
    deleted = await crud.area_crud.soft_delete(db, id_area)
    if not deleted:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    return {"message": "Área desactivada (borrado lógico)"}