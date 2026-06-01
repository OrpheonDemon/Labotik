from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db

router = APIRouter(prefix="/medicos", tags=["Médicos"])

@router.get("/", response_model=list[schemas.MedicoOut])
async def list_medicos(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.medico_crud.get_multi(db, skip, limit)

@router.get("/search", response_model=list[schemas.MedicoOut])
async def search_medicos(
    id_medico: str = Query(None),
    apellido_paterno: str = Query(None),
    apellido_materno: str = Query(None),
    nombre: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if id_medico:
        medico = await crud.medico_crud.get(db, id_medico)
        return [medico] if medico else []
    return await crud.medico_crud.search_by_names(db, apellido_paterno, apellido_materno, nombre)

@router.get("/by-email", response_model=schemas.MedicoOut)
async def get_medico_by_email(email: str = Query(...), db: AsyncSession = Depends(get_db)):
    medico = await crud.medico_crud.get_by_email(db, email)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico

@router.get("/{id_medico}", response_model=schemas.MedicoOut)
async def get_medico(id_medico: str, db: AsyncSession = Depends(get_db)):
    medico = await crud.medico_crud.get(db, id_medico)
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return medico

@router.post("/", response_model=schemas.MedicoOut, status_code=201)
async def create_medico(medico_in: schemas.MedicoCreate, db: AsyncSession = Depends(get_db)):
    return await crud.medico_crud.create(db, medico_in)

@router.put("/{id_medico}", response_model=schemas.MedicoOut)
async def update_medico(id_medico: str, medico_in: schemas.MedicoUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.medico_crud.update(db, id_medico, medico_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return updated

@router.delete("/{id_medico}")
async def delete_medico(id_medico: str, db: AsyncSession = Depends(get_db)):
    deleted = await crud.medico_crud.soft_delete(db, id_medico)
    if not deleted:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    return {"message": "Médico desactivado (borrado lógico)"}