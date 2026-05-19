from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db

router = APIRouter(prefix="/administradores", tags=["Administradores"])

@router.get("/", response_model=list[schemas.AdministradorOut])
async def list_administradores(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.administrador_crud.get_multi(db, skip, limit)

@router.get("/search", response_model=list[schemas.AdministradorOut])
async def search_administradores(
    apellido_paterno: str = Query(None),
    apellido_materno: str = Query(None),
    nombre: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await crud.administrador_crud.search_by_names(db, apellido_paterno, apellido_materno, nombre)

@router.get("/by-email", response_model=schemas.AdministradorOut)
async def get_administrador_by_email(email: str = Query(...), db: AsyncSession = Depends(get_db)):
    administrador = await crud.administrador_crud.get_by_email(db, email)
    if not administrador:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return administrador

@router.get("/{id_administrador}", response_model=schemas.AdministradorOut)
async def get_administrador(id_administrador: str, db: AsyncSession = Depends(get_db)):
    administrador = await crud.administrador_crud.get(db, id_administrador)
    if not administrador:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return administrador

@router.post("/", response_model=schemas.AdministradorOut, status_code=201)
async def create_administrador(administrador_in: schemas.AdministradorCreate, db: AsyncSession = Depends(get_db)):
    return await crud.administrador_crud.create(db, administrador_in)

@router.put("/{id_administrador}", response_model=schemas.AdministradorOut)
async def update_administrador(id_administrador: str, administrador_in: schemas.AdministradorUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.administrador_crud.update(db, id_administrador, administrador_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return updated

@router.delete("/{id_administrador}")
async def delete_administrador(id_administrador: str, db: AsyncSession = Depends(get_db)):
    deleted = await crud.administrador_crud.soft_delete(db, id_administrador)
    if not deleted:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return {"message": "Administrador desactivado (borrado lógico)"}
