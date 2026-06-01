from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db
from app.dependencies import require_laboratorista, get_current_active_user

router = APIRouter(prefix="/laboratoristas", tags=["Laboratoristas"])



@router.get("/search", response_model=list[schemas.LaboratoristaOut])
async def search_laboratoristas(
    id_laboratorista: str = Query(None),
    id_area: str = Query(None),
    apellido_paterno: str = Query(None),
    apellido_materno: str = Query(None),
    nombre: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    if id_laboratorista:
        laboratorista = await crud.laboratorista_crud.get(db, id_laboratorista)
        return [laboratorista] if laboratorista else []
    if id_area:
        return await crud.laboratorista_crud.search_by_area(db, id_area)
    if any([apellido_paterno, apellido_materno, nombre]):
        return await crud.laboratorista_crud.search_by_names(
            db, 
            apellido_paterno or "", 
            apellido_materno or "", 
            nombre or ""
        )
    return []

@router.get("/", response_model=list[schemas.LaboratoristaOut])
async def list_laboratoristas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.laboratorista_crud.get_multi(db, skip, limit)

@router.get("/{id_laboratorista}", response_model=schemas.LaboratoristaOut)
async def get_laboratorista(id_laboratorista: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    laboratorista = await crud.laboratorista_crud.get(db, id_laboratorista)
    if not laboratorista:
        raise HTTPException(status_code=404, detail="Laboratorista no encontrado")
    return laboratorista

@router.post("/", response_model=schemas.LaboratoristaOut, status_code=201)
async def create_laboratorista(laboratorista_in: schemas.LaboratoristaCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    return await crud.laboratorista_crud.create(db, laboratorista_in)

@router.put("/{id_laboratorista}", response_model=schemas.LaboratoristaOut)
async def update_laboratorista(id_laboratorista: str, laboratorista_in: schemas.LaboratoristaUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    updated = await crud.laboratorista_crud.update(db, id_laboratorista, laboratorista_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Laboratorista no encontrado")
    return updated

@router.delete("/{id_laboratorista}")
async def delete_laboratorista(id_laboratorista: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    deleted = await crud.laboratorista_crud.soft_delete(db, id_laboratorista)
    if not deleted:
        raise HTTPException(status_code=404, detail="Laboratorista no encontrado")
    return {"message": "Laboratorista desactivado (borrado lógico)"}