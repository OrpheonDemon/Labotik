from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.dependencies import require_laboratorista
from app.id_generator import get_next_int_id

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


@router.post("/{id_pago}/confirmar")
async def confirmar_pago(
    id_pago: int, 
    referencia: str = None,
    db: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(require_laboratorista)
):
    """Confirma un pago y actualiza el estado de la factura"""
    pago = await crud.pago_crud.get(db, id_pago)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    # Obtener factura asociada
    stmt = select(models.Factura).where(models.Factura.id_factura == pago.id_factura)
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    
    if not factura:
        raise HTTPException(status_code=404, detail="Factura asociada no encontrada")
    
    # Actualizar estado del pago
    pago.estado_pago = 'completado'
    if referencia:
        pago.referencia_pago = referencia
    
    # Actualizar estado de factura
    if pago.monto >= factura.total:
        factura.estado_factura = 'pagada_total'
    else:
        factura.estado_factura = 'pagada_parcial'
    
    await db.commit()
    await db.refresh(pago)
    
    return {
        "id_pago": pago.id_pago,
        "id_factura": pago.id_factura,
        "monto": pago.monto,
        "estado_pago": pago.estado_pago,
        "referencia_pago": pago.referencia_pago,
        "estado_factura": factura.estado_factura,
        "mensaje": "Pago confirmado exitosamente"
    }