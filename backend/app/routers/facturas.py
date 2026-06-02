from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id
from app.dependencies import require_laboratorista, require_paciente, require_pagos_roles
from fastapi.responses import StreamingResponse
import io
import os
from datetime import datetime
from app.payment_qr import generate_payment_qr, generate_qr_reference

router = APIRouter(prefix="/facturas", tags=["Facturas"])

@router.get("/", response_model=list[schemas.FacturaOut])
async def list_facturas(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """
    Lista todas las facturas. Acceso exclusivo para:
    - Administrador
    - Recepcionista
    - Paciente
    """
    return await crud.factura_crud.get_multi(db, skip, limit)


@router.get("/paciente/{id_paciente}/pendientes", response_model=list[schemas.FacturaOut])
async def list_facturas_pendientes_paciente(
    id_paciente: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_paciente)
):
    """Lista facturas pendientes (no pagadas totalmente) de un paciente"""
    stmt = select(models.Factura).where(
        models.Factura.activo == 1,
        models.Factura.id_paciente == id_paciente,
        models.Factura.estado_factura.in_(['emitida', 'pagada_parcial'])
    ).order_by(models.Factura.fecha_emision.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{id_factura}/qr", response_model=schemas.FacturaQRResponse)
async def get_factura_qr(
    id_factura: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_paciente)
):
    """Genera un código QR con los datos de pago de la factura"""
    factura = await crud.factura_crud.get(db, id_factura)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Cargar paciente para obtener email
    stmt = select(models.Paciente).where(
        models.Paciente.id_paciente == factura.id_paciente,
        models.Paciente.activo == 1
    )
    result = await db.execute(stmt)
    paciente = result.scalar_one_or_none()

    base64_qr, _ = generate_payment_qr(
        invoice_id=factura.id_factura,
        amount=factura.total,
        patient_id=str(factura.id_paciente),
        patient_email=paciente.email if paciente else "no@especificado.com",
        description=f"Pago de Factura {factura.id_factura}"
    )

    return {
        "id_factura": factura.id_factura,
        "monto": factura.total,
        "estado": factura.estado_factura,
        "qr_base64": base64_qr,
        "referencia": generate_qr_reference(factura.id_factura, factura.total)
    }


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
async def list_facturas_pagadas(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """
    Lista las facturas pagadas. Acceso exclusivo para:
    - Administrador
    - Recepcionista
    - Paciente
    """
    stmt = select(models.Factura).where(models.Factura.activo == 1, models.Factura.estado_factura == 'pagada_total').offset(skip).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


def numero_a_letras(n):
    """Convierte un número a letras en español (para montos de factura)"""
    unidades = ['', 'Uno', 'Dos', 'Tres', 'Cuatro', 'Cinco', 'Seis', 'Siete', 'Ocho', 'Nueve']
    decenas = ['', 'Diez', 'Veinte', 'Treinta', 'Cuarenta', 'Cincuenta', 'Sesenta', 'Setenta', 'Ochenta', 'Noventa']
    centenas = ['', 'Cien', 'Doscientos', 'Trescientos', 'Cuatrocientos', 'Quinientos', 'Seiscientos', 'Setecientos', 'Ochocientos', 'Novecientos']
    
    def convertir_grupo(num):
        if num == 0:
            return ''
        elif num < 10:
            return unidades[num]
        elif num < 100:
            d = num // 10
            u = num % 10
            if num == 10:
                return 'Diez'
            elif num < 20:
                return 'Dieci' + unidades[u].lower()
            elif num == 20:
                return 'Veinte'
            elif num < 30:
                return 'Veinti' + unidades[u].lower()
            elif u == 0:
                return decenas[d]
            else:
                return decenas[d] + ' y ' + unidades[u].lower()
        else:
            c = num // 100
            resto = num % 100
            if c == 1 and resto == 0:
                return 'Cien'
            elif c == 1:
                return 'Ciento ' + convertir_grupo(resto).lower()
            elif resto == 0:
                return centenas[c]
            else:
                return centenas[c] + ' ' + convertir_grupo(resto).lower()
    
    if n == 0:
        return 'Cero'
    
    entero = int(n)
    centavos = int(round((n - entero) * 100))
    
    if entero == 0:
        resultado = 'Cero'
    elif entero < 1000:
        resultado = convertir_grupo(entero)
    elif entero < 1000000:
        miles = entero // 1000
        resto = entero % 1000
        if miles == 1:
            resultado = 'Mil'
        else:
            resultado = convertir_grupo(miles) + ' Mil'
        if resto > 0:
            resultado += ' ' + convertir_grupo(resto).lower()
    else:
        millones = entero // 1000000
        resto = entero % 1000000
        if millones == 1:
            resultado = 'Un Millón'
        else:
            resultado = convertir_grupo(millones) + ' Millones'
        if resto > 0:
            resultado += ' ' + convertir_grupo(resto).lower()
    
    # Capitalizar primera letra
    resultado = resultado[0].upper() + resultado[1:] if resultado else ''
    
    # Agregar centavos
    resultado += f' {centavos:02d}/100 Bolivianos'
    
    return resultado


@router.get('/{id_factura}/pdf')
async def factura_pdf(
    id_factura: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """
    Genera el PDF de la factura con formato Labotik. Acceso exclusivo para:
    - Administrador
    - Recepcionista
    - Paciente
    """
    factura = await crud.factura_crud.get(db, id_factura)
    if not factura:
        raise HTTPException(status_code=404, detail='Factura no encontrada')

    # Cargar detalles
    stmt = select(models.DetalleFactura).where(models.DetalleFactura.id_factura == id_factura, models.DetalleFactura.activo == 1)
    result = await db.execute(stmt)
    detalles = result.scalars().all()

    # Cargar paciente
    stmt_pac = select(models.Paciente).where(models.Paciente.id_paciente == factura.id_paciente)
    result_pac = await db.execute(stmt_pac)
    paciente = result_pac.scalar_one_or_none()

    # Cargar recepcionista/administrador que emitió la factura (si existe en current_user)
    recepcionista_nombre = current_user.get('nombre', '') + ' ' + current_user.get('apellido_paterno', '')
    recepcionista_nombre = recepcionista_nombre.strip() or 'Administrador'

    # Importar reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
    except ImportError:
        raise HTTPException(status_code=500, detail="Dependencia requerida 'reportlab' no instalada. Instale con: pip install reportlab")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # === ENCABEZADO LABOTIK ===
    y = height - 40
    
    # Logo (si existe)
    logo_path = os.path.join(os.getcwd(), 'frontend', 'static', 'images', 'LaboLogo.png')
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, y-50, width=100, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    
    # Título principal
    c.setFont('Helvetica-Bold', 24)
    c.drawCentredString(width/2, y, 'LABOTIK')
    c.setFont('Helvetica', 10)
    c.drawCentredString(width/2, y-15, 'Laboratorio Clínico')
    
    # Línea separadora
    y -= 40
    c.setLineWidth(1.5)
    c.line(40, y, width-40, y)
    
    # === DATOS DE FACTURA ===
    y -= 30
    c.setFont('Helvetica-Bold', 14)
    # Factura N° (empezar desde 1000)
    factura_numero = factura.id_factura + 999  # Para empezar desde 1000
    c.drawString(40, y, f'Factura N° {factura_numero}')
    
    # Fecha en formato AA/MM/DD
    fecha_str = factura.fecha_emision.strftime('%y/%m/%d') if hasattr(factura.fecha_emision, 'strftime') else str(factura.fecha_emision)
    c.drawRightString(width-40, y, f'Fecha: {fecha_str}')
    
    # === DATOS DE RECEPCIONISTA ===
    y -= 25
    c.setFont('Helvetica-Bold', 10)
    c.drawString(40, y, 'Atendido por:')
    c.setFont('Helvetica', 10)
    c.drawString(120, y, recepcionista_nombre)
    
    # === DATOS DE PACIENTE ===
    y -= 20
    c.setFont('Helvetica-Bold', 10)
    c.drawString(40, y, 'Paciente:')
    c.setFont('Helvetica', 10)
    if paciente:
        paciente_nombre = f'{paciente.nombre or ""} {paciente.apellido_paterno or ""} {paciente.apellido_materno or ""}'.strip()
        c.drawString(120, y, paciente_nombre or str(factura.id_paciente))
    else:
        c.drawString(120, y, str(factura.id_paciente))
    
    # === IMPORTE ===
    y -= 25
    c.setFont('Helvetica-Bold', 10)
    c.drawString(40, y, 'Importe:')
    c.setFont('Helvetica-Bold', 12)
    c.drawString(120, y, f'Bs {factura.total:.2f}')
    
    # === TABLA DE ANÁLISIS ===
    y -= 35
    c.setLineWidth(1)
    c.line(40, y, width-40, y)
    
    # Encabezados de tabla
    y -= 20
    c.setFont('Helvetica-Bold', 11)
    c.drawString(50, y, 'Cantidad')
    c.drawString(130, y, 'Descripción')
    c.drawRightString(width-50, y, 'Precio Unitario')
    
    # Línea bajo encabezados
    y -= 8
    c.line(40, y, width-40, y)
    
    # Items de la tabla
    c.setFont('Helvetica', 10)
    y -= 20
    for d in detalles:
        # Obtener nombre de prueba
        pname = str(d.id_prueba)
        try:
            stmt_prueba = select(models.Prueba).where(models.Prueba.id_prueba == d.id_prueba)
            pr = await db.execute(stmt_prueba)
            p = pr.scalar_one_or_none()
            if p:
                pname = p.nombre
        except Exception:
            pass
        
        c.drawString(70, y, str(d.cantidad))
        c.drawString(130, y, pname[:50])  # Limitar longitud del nombre
        c.drawRightString(width-50, y, f'Bs {d.precio_unitario:.2f}')
        y -= 18
        
        if y < 150:  # Evitar que se salga de la página
            c.showPage()
            y = height - 100
    
    # === LÍNEA ANTES DEL TOTAL ===
    y -= 10
    c.line(40, y, width-40, y)
    
    # === MONTO TOTAL ===
    y -= 25
    c.setFont('Helvetica-Bold', 14)
    c.drawRightString(width-50, y, f'Monto Total: Bs {factura.total:.2f}')
    
    # === MONTO TOTAL LITERAL ===
    y -= 25
    c.setFont('Helvetica', 11)
    monto_literal = numero_a_letras(factura.total)
    c.drawString(40, y, monto_literal)
    
    # === PIE DE PÁGINA ===
    c.setFont('Helvetica', 8)
    c.drawCentredString(width/2, 30, 'Labotik - Laboratorio Clínico | Gracias por su preferencia')
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"inline; filename=factura_{id_factura}.pdf"})
