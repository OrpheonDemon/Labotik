from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id
from app.dependencies import require_laboratorista

router = APIRouter(prefix="/facturas", tags=["Facturas"])

@router.get("/", response_model=list[schemas.FacturaOut])
async def list_facturas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    return await crud.factura_crud.get_multi(db, skip, limit)

@router.get("/{id_factura}", response_model=schemas.FacturaOut)
async def get_factura(id_factura: int, db: AsyncSession = Depends(get_db)):
    factura = await crud.factura_crud.get(db, id_factura)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    # Cargar detalles
    stmt = select(models.DetalleFactura).where(models.DetalleFactura.id_factura == id_factura, models.DetalleFactura.activo == 1)
    result = await db.execute(stmt)
    detalles = result.scalars().all()
    factura.detalles = detalles
    return factura

@router.post("/", response_model=schemas.FacturaOut, status_code=201)
async def create_factura(factura_in: schemas.FacturaCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    new_id = await get_next_int_id(db, models.Factura, 'id_factura')
    factura_data = factura_in.dict(exclude={'detalles'})
    factura_data['id_factura'] = new_id
    nueva_factura = models.Factura(**factura_data)
    db.add(nueva_factura)
    await db.flush()
    for detalle_in in factura_in.detalles:
        detalle_id = await get_next_int_id(db, models.DetalleFactura, 'id_detalle_factura')
        detalle = models.DetalleFactura(
            id_detalle_factura=detalle_id,
            id_factura=new_id,
            **detalle_in.dict()
        )
        db.add(detalle)
    await db.commit()
    await db.refresh(nueva_factura)
    return nueva_factura

@router.put("/{id_factura}", response_model=schemas.FacturaOut)
async def update_factura(id_factura: int, factura_in: schemas.FacturaUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    updated = await crud.factura_crud.update(db, id_factura, factura_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return updated

@router.delete("/{id_factura}")
async def delete_factura(id_factura: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    deleted = await crud.factura_crud.soft_delete(db, id_factura)
    if not deleted:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return {"message": "Factura desactivada (borrado lógico)"}