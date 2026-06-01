from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id
from app.dependencies import require_laboratorista
from app.utils.payment_qr import generate_payment_qr, generate_qr_reference
from fastapi.responses import StreamingResponse
import io
import os
from datetime import datetime

router = APIRouter(prefix="/facturas", tags=["Facturas"])

@router.get("/", response_model=list[schemas.FacturaOut])
async def list_facturas(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    return await crud.factura_crud.get_multi(db, skip, limit)


@router.get("/sus/pendientes", response_model=list[schemas.FacturaOut])
async def list_facturas_sus_pendientes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    """Lista facturas pendientes de reembolso del SUS/Ministerio de Salud"""
    stmt = select(models.Factura).where(
        models.Factura.activo == 1,
        models.Factura.tipo_pago_fuente.in_(['SUS', 'ministerio_salud']),
        models.Factura.estado_reembolso_sus.in_(['pendiente', 'enviado'])
    ).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/sus/resumen")
async def resumen_sus(db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_laboratorista)):
    """Resumen de facturación SUS: total pendiente, enviado, reembolsado"""
    # Total pendiente de envío
    stmt_pend = select(models.Factura).where(
        models.Factura.activo == 1,
        models.Factura.tipo_pago_fuente.in_(['SUS', 'ministerio_salud']),
        models.Factura.estado_reembolso_sus == 'pendiente'
    )
    result_pend = await db.execute(stmt_pend)
    facturas_pend = result_pend.scalars().all()
    total_pendiente = sum(f.total for f in facturas_pend)

    # Total enviado al SUS
    stmt_env = select(models.Factura).where(
        models.Factura.activo == 1,
        models.Factura.tipo_pago_fuente.in_(['SUS', 'ministerio_salud']),
        models.Factura.estado_reembolso_sus == 'enviado'
    )
    result_env = await db.execute(stmt_env)
    facturas_env = result_env.scalars().all()
    total_enviado = sum(f.total for f in facturas_env)

    # Total reembolsado
    stmt_remb = select(models.Factura).where(
        models.Factura.activo == 1,
        models.Factura.tipo_pago_fuente.in_(['SUS', 'ministerio_salud']),
        models.Factura.estado_reembolso_sus == 'reembolsado'
    )
    result_remb = await db.execute(stmt_remb)
    facturas_remb = result_remb.scalars().all()
    total_reembolsado = sum(f.total for f in facturas_remb)

    # Total facturado a pacientes privados
    stmt_priv = select(models.Factura).where(
        models.Factura.activo == 1,
        models.Factura.tipo_pago_fuente == 'paciente',
        models.Factura.estado_factura == 'pagada_total'
    )
    result_priv = await db.execute(stmt_priv)
    facturas_priv = result_priv.scalars().all()
    total_cobrado_pacientes = sum(f.total for f in facturas_priv)

    return {
        "sus_pendientes_envio": len(facturas_pend),
        "sus_total_pendiente": total_pendiente,
        "sus_enviados": len(facturas_env),
        "sus_total_enviado": total_enviado,
        "sus_reembolsados": len(facturas_remb),
        "sus_total_reembolsado": total_reembolsado,
        "privados_pagados": len(facturas_priv),
        "privados_total_cobrado": total_cobrado_pacientes,
        "pendiente_cobro_total_sus": total_pendiente + total_enviado
    }


@router.put("/{id_factura}/marcar-reembolso-sus")
async def marcar_reembolso_sus(
    id_factura: int,
    numero_reclamacion: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    """Marca una factura SUS como enviada al Ministerio o reembolsada"""
    factura = await crud.factura_crud.get(db, id_factura)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    if factura.tipo_pago_fuente == 'paciente':
        raise HTTPException(status_code=400, detail="Esta factura no es al SUS")
    
    # Cambiar estado según el flujo
    if factura.estado_reembolso_sus == 'pendiente':
        factura.estado_reembolso_sus = 'enviado'
        if numero_reclamacion:
            factura.numero_reclamacion_sus = numero_reclamacion
    elif factura.estado_reembolso_sus == 'enviado':
        factura.estado_reembolso_sus = 'reembolsado'
    else:
        raise HTTPException(status_code=400, detail=f"No se puede cambiar estado desde '{factura.estado_reembolso_sus}'")
    
    await db.commit()
    await db.refresh(factura)
    return factura

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
    
    # Si no se enviaron montos explícitos, calcular según tipo de afiliación
    if factura_data.get('monto_paciente', 0) == 0 and factura_data.get('monto_sus', 0) == 0:
        stmt_paciente = select(models.Paciente).where(models.Paciente.id_paciente == factura_data['id_paciente'])
        res = await db.execute(stmt_paciente)
        paciente = res.scalar_one_or_none()
        
        if paciente and paciente.tipo_afiliacion == 'SUS':
            factura_data['tipo_pago_fuente'] = 'SUS'
            factura_data['monto_paciente'] = 0.0
            factura_data['monto_sus'] = factura_data['total']
            factura_data['estado_reembolso_sus'] = 'pendiente'
        else:
            factura_data['tipo_pago_fuente'] = 'paciente'
            factura_data['monto_paciente'] = factura_data['total']
            factura_data['monto_sus'] = 0.0
            factura_data['estado_reembolso_sus'] = 'no_aplica'
    
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


@router.get('/{id_factura}/qr')
async def get_factura_qr(id_factura: int, db: AsyncSession = Depends(get_db)):
    """Genera código QR para pago de factura"""
    factura = await crud.factura_crud.get(db, id_factura)
    if not factura:
        raise HTTPException(status_code=404, detail='Factura no encontrada')
    
    # Obtener datos del paciente
    stmt = select(models.Paciente).where(models.Paciente.id_paciente == factura.id_paciente)
    result = await db.execute(stmt)
    paciente = result.scalar_one_or_none()
    
    if not paciente:
        raise HTTPException(status_code=404, detail='Paciente no encontrado')
    
    # Generar QR
    base64_qr, png_bytes = generate_payment_qr(
        invoice_id=factura.id_factura,
        amount=factura.monto_paciente if factura.monto_paciente > 0 else factura.total,
        patient_id=str(paciente.id_paciente),
        patient_email=paciente.email or "no@especificado.com",
        currency="BOB",
        description=f"Pago de Factura {factura.id_factura}"
    )
    
    return {
        "id_factura": id_factura,
        "monto": factura.monto_paciente if factura.monto_paciente > 0 else factura.total,
        "estado": factura.estado_factura,
        "qr_base64": base64_qr,
        "referencia": generate_qr_reference(factura.id_factura, factura.monto_paciente if factura.monto_paciente > 0 else factura.total)
    }


@router.get('/paciente/{id_paciente}/pendientes')
async def get_paciente_pending_invoices(id_paciente: int, db: AsyncSession = Depends(get_db)):
    """Lista facturas pendientes de pago para un paciente"""
    stmt = select(models.Factura).where(
        models.Factura.id_paciente == id_paciente,
        models.Factura.activo == 1,
        models.Factura.estado_factura.in_(['emitida', 'pagada_parcial'])
    )
    result = await db.execute(stmt)
    facturas = result.scalars().all()
    
    return [
        {
            "id_factura": f.id_factura,
            "monto": f.monto_paciente if f.monto_paciente > 0 else f.total,
            "estado": f.estado_factura,
            "fecha_emision": f.fecha_emision,
            "total": f.total
        }
        for f in facturas
    ]