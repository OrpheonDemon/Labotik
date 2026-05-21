from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db
from app.dependencies import require_super_admin

router = APIRouter(prefix="/pruebas", tags=["Pruebas"])

@router.get("/", response_model=list[schemas.PruebaOut])
async def list_pruebas(skip: int = 0, limit: int = 100, include_inactive: bool = False, db: AsyncSession = Depends(get_db)):
    return await crud.prueba_crud.get_multi(db, skip, limit, include_inactive=include_inactive)

@router.get("/{id_prueba}", response_model=schemas.PruebaOut)
async def get_prueba(id_prueba: int, db: AsyncSession = Depends(get_db)):
    prueba = await crud.prueba_crud.get(db, id_prueba)
    if not prueba:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return prueba

@router.post("/", response_model=schemas.PruebaOut, status_code=201)
async def create_prueba(prueba_in: schemas.PruebaCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_super_admin)):
    return await crud.prueba_crud.create(db, prueba_in)

@router.put("/{id_prueba}", response_model=schemas.PruebaOut)
async def update_prueba(id_prueba: int, prueba_in: schemas.PruebaUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_super_admin)):
    updated = await crud.prueba_crud.update(db, id_prueba, prueba_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return updated

@router.delete("/{id_prueba}")
async def delete_prueba(id_prueba: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_super_admin)):
    deleted = await crud.prueba_crud.soft_delete(db, id_prueba)
    if not deleted:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return {"message": "Prueba desactivada (borrado lógico)"}