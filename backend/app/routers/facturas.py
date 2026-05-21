from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id
from app.dependencies import require_laboratorista
from fastapi.responses import StreamingResponse
import io
import os

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


@router.get('/pagadas', response_model=list[schemas.FacturaOut])
async def list_facturas_pagadas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    stmt = select(models.Factura).where(models.Factura.activo == 1, models.Factura.estado_factura == 'pagada_total').offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get('/{id_factura}/pdf')
async def factura_pdf(id_factura: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    factura = await crud.factura_crud.get(db, id_factura)
    if not factura:
        raise HTTPException(status_code=404, detail='Factura no encontrada')

    # Cargar detalles
    stmt = select(models.DetalleFactura).where(models.DetalleFactura.id_factura == id_factura, models.DetalleFactura.activo == 1)
    result = await db.execute(stmt)
    detalles = result.scalars().all()

    # Importar reportlab en tiempo de ejecución para no romper el arranque si falta la dependencia
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        raise HTTPException(status_code=500, detail="Dependencia requerida 'reportlab' no instalada. Instale con: pip install reportlab")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Logo (si existe)
    logo_path = os.path.join(os.getcwd(), 'frontend', 'static', 'images', 'logo.png')
    y = height - 50
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, y-40, width=120, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Header
    c.setFont('Helvetica-Bold', 16)
    c.drawString(180, y, 'Laboratorio Clínico - Factura')
    c.setFont('Helvetica', 10)
    c.drawString(40, y-60, f'ID Factura: {factura.id_factura}')
    c.drawString(200, y-60, f'ID Solicitud: {factura.id_solicitud or "-"}')
    c.drawString(40, y-75, f'Fecha emisión: {factura.fecha_emision}')
    c.drawString(200, y-75, f'Total: {factura.total:.2f}')

    # Tabla de items
    c.setFont('Helvetica-Bold', 11)
    table_y = y-110
    c.drawString(40, table_y, 'Prueba')
    c.drawString(300, table_y, 'Cantidad')
    c.drawString(380, table_y, 'Precio Unit.')
    c.drawString(480, table_y, 'Total')
    c.setFont('Helvetica', 10)
    cur_y = table_y - 20
    for d in detalles:
        # intentar obtener nombre de prueba
        pname = str(d.id_prueba)
        try:
            stmt = select(models.Prueba).where(models.Prueba.id_prueba == d.id_prueba)
            pr = await db.execute(stmt)
            p = pr.scalar_one_or_none()
            if p:
                pname = p.nombre
        except Exception:
            pass
        c.drawString(40, cur_y, pname)
        c.drawString(300, cur_y, str(d.cantidad))
        c.drawString(380, cur_y, f"{d.precio_unitario:.2f}")
        c.drawString(480, cur_y, f"{d.total_item:.2f}")
        cur_y -= 18

    c.setFont('Helvetica-Bold', 12)
    c.drawString(40, cur_y-20, f'Subtotal: {factura.subtotal:.2f}')
    c.drawString(200, cur_y-20, f'Impuesto: {factura.impuesto:.2f}')
    c.drawString(320, cur_y-20, f'Descuento: {factura.descuento:.2f}')
    c.drawString(420, cur_y-20, f'Total: {factura.total:.2f}')

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"inline; filename=factura_{id_factura}.pdf"})