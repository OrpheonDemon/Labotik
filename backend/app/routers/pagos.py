from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db

router = APIRouter(prefix="/pagos", tags=["Pagos"])

@router.get("/", response_model=list[schemas.PagoOut])
async def list_pagos(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.pago_crud.get_multi(db, skip, limit)

@router.get("/{id_pago}", response_model=schemas.PagoOut)
async def get_pago(id_pago: int, db: AsyncSession = Depends(get_db)):
    pago = await crud.pago_crud.get(db, id_pago)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago

@router.post("/", response_model=schemas.PagoOut, status_code=201)
async def create_pago(pago_in: schemas.PagoCreate, db: AsyncSession = Depends(get_db)):
    return await crud.pago_crud.create(db, pago_in)

@router.put("/{id_pago}", response_model=schemas.PagoOut)
async def update_pago(id_pago: int, pago_in: schemas.PagoUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.pago_crud.update(db, id_pago, pago_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return updated

@router.delete("/{id_pago}")
async def delete_pago(id_pago: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.pago_crud.soft_delete(db, id_pago)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return {"message": "Pago desactivado (borrado lógico)"}