"""
Router para generación de QR de pago y confirmación de pagos por pacientes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.database import get_db
from app.dependencies import get_current_active_user, require_pagos_roles
from app.payment_qr import generate_payment_qr, generate_qr_reference
from datetime import datetime
import io
import base64
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/pagos", tags=["Pagos QR"])


@router.get("/solicitudes/{id_solicitud}/qr")
async def generar_qr_solicitud(
    id_solicitud: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """
    Genera un código QR con los datos de pago de una solicitud.
    
    El QR contiene:
    - ID de la solicitud
    - Monto total a pagar
    - Referencia única de pago
    - Datos del paciente
    
    Retorna el QR en formato base64 para mostrar en el frontend.
    """
    # Obtener la solicitud
    stmt = select(models.Solicitud).where(
        models.Solicitud.id_solicitud == id_solicitud,
        models.Solicitud.activo == 1
    )
    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if solicitud.estado_pago == "pagado_total":
        raise HTTPException(status_code=400, detail="La solicitud ya está pagada totalmente")
    
    # Calcular el monto total de la solicitud
    stmt_detalles = select(models.DetalleSolicitud).where(
        models.DetalleSolicitud.id_solicitud == id_solicitud,
        models.DetalleSolicitud.activo == 1
    )
    result_detalles = await db.execute(stmt_detalles)
    detalles = result_detalles.scalars().all()
    
    total = 0
    for d in detalles:
        cantidad = d.cantidad or 1
        # Obtener precio de la prueba
        stmt_prueba = select(models.Prueba).where(models.Prueba.id_prueba == d.id_prueba)
        res_prueba = await db.execute(stmt_prueba)
        prueba = res_prueba.scalar_one_or_none()
        if prueba:
            total += cantidad * float(prueba.precio)
    
    if total <= 0:
        raise HTTPException(status_code=400, detail="No se pudo calcular el monto de la solicitud")
    
    # Obtener datos del paciente
    stmt_paciente = select(models.Paciente).where(
        models.Paciente.id_paciente == solicitud.id_paciente,
        models.Paciente.activo == 1
    )
    result_paciente = await db.execute(stmt_paciente)
    paciente = result_paciente.scalar_one_or_none()
    
    paciente_nombre = ""
    paciente_email = "no@especificado.com"
    if paciente:
        paciente_nombre = f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}".strip()
        paciente_email = paciente.email or "no@especificado.com"
    
    # Generar referencia única
    referencia = generate_qr_reference(id_solicitud, total)
    
    # Generar QR
    qr_data = (
        f"LABOTIK-PAGO|SOL:{id_solicitud}|MONTO:{total:.2f}|REF:{referencia}|"
        f"PACIENTE:{paciente_nombre}|EMAIL:{paciente_email}"
    )
    
    base64_qr, _ = generate_payment_qr(
        invoice_id=id_solicitud,
        amount=total,
        patient_id=str(solicitud.id_paciente),
        patient_email=paciente_email,
        description=f"Pago de Solicitud #{id_solicitud} - {paciente_nombre}"
    )
    
    return {
        "id_solicitud": id_solicitud,
        "monto": total,
        "referencia": referencia,
        "qr_base64": base64_qr,
        "qr_data": qr_data,
        "paciente": paciente_nombre,
        "estado_pago": solicitud.estado_pago,
    }


@router.post("/solicitudes/{id_solicitud}/confirmar-pago-qr")
async def confirmar_pago_qr(
    id_solicitud: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Confirma el pago de una solicitud después de que el paciente escanea el QR.
    
    Este endpoint:
    1. Marca la solicitud como pagada
    2. Crea la factura correspondiente (si no existe)
    3. Registra el pago
    4. Retorna los datos para generar la factura
    
    Permisos:
    - Paciente: solo puede confirmar sus propias solicitudes
    - Admin/Recepcionista: pueden confirmar cualquier solicitud
    """
    rol = current_user.get("rol")
    user_obj = current_user.get("user")
    user_id = None
    if user_obj is not None:
        user_id = getattr(user_obj, "id_paciente", None) or getattr(user_obj, "id_administrador", None)
    
    # Obtener solicitud
    stmt = select(models.Solicitud).where(
        models.Solicitud.id_solicitud == id_solicitud,
        models.Solicitud.activo == 1
    )
    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    if solicitud.estado_pago == "pagado_total":
        raise HTTPException(status_code=400, detail="La solicitud ya está pagada totalmente")
    
    # Verificar permisos para pacientes
    if rol == "paciente" and user_id and solicitud.id_paciente != user_id:
        raise HTTPException(status_code=403, detail="No puedes pagar solicitudes de otros pacientes")
    
    # Calcular el monto total de la solicitud
    stmt_detalles = select(models.DetalleSolicitud).where(
        models.DetalleSolicitud.id_solicitud == id_solicitud,
        models.DetalleSolicitud.activo == 1
    )
    result_detalles = await db.execute(stmt_detalles)
    detalles = result_detalles.scalars().all()
    
    total = 0
    items_factura = []
    for d in detalles:
        cantidad = d.cantidad or 1
        stmt_prueba = select(models.Prueba).where(models.Prueba.id_prueba == d.id_prueba)
        res_prueba = await db.execute(stmt_prueba)
        prueba = res_prueba.scalar_one_or_none()
        if prueba:
            precio_unitario = float(prueba.precio)
            total_item = cantidad * precio_unitario
            total += total_item
            items_factura.append({
                "id_prueba": prueba.id_prueba,
                "nombre": prueba.nombre,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "total_item": total_item,
            })
    
    if total <= 0:
        raise HTTPException(status_code=400, detail="No se pudo calcular el monto de la solicitud")
    
    # Buscar o crear factura
    stmt_factura = select(models.Factura).where(
        models.Factura.id_solicitud == id_solicitud,
        models.Factura.activo == 1
    )
    result_factura = await db.execute(stmt_factura)
    factura = result_factura.scalar_one_or_none()
    
    if not factura:
        # Crear nueva factura
        from app.id_generator import get_next_int_id
        
        # Obtener el siguiente ID de factura (empezando desde 1000 si es la primera)
        new_factura_id = await get_next_int_id(db, models.Factura, 'id_factura')
        
        # Si es la primera factura y el ID es menor a 1000, usar 1000
        if new_factura_id < 1000:
            # Verificar si ya existen facturas
            stmt_check = select(models.Factura).order_by(models.Factura.id_factura.desc()).limit(1)
            result_check = await db.execute(stmt_check)
            last_factura = result_check.scalar_one_or_none()
            if last_factura:
                new_factura_id = last_factura.id_factura + 1
            else:
                new_factura_id = 1000
        
        factura = models.Factura(
            id_factura=new_factura_id,
            id_solicitud=id_solicitud,
            id_paciente=solicitud.id_paciente,
            subtotal=total,
            impuesto=0.0,
            descuento=0.0,
            total=total,
            estado_factura="emitida",
            fecha_emision=datetime.now(),
            activo=1,
        )
        db.add(factura)
        await db.flush()
        
        # Crear detalles de factura
        for item in items_factura:
            from app.id_generator import get_next_int_id
            new_detalle_id = await get_next_int_id(db, models.DetalleFactura, 'id_detalle_factura')
            detalle_factura = models.DetalleFactura(
                id_detalle_factura=new_detalle_id,
                id_factura=new_factura_id,
                id_prueba=item["id_prueba"],
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"],
                total_item=item["total_item"],
                activo=1,
            )
            db.add(detalle_factura)
    
    # Crear el pago
    from app.id_generator import get_next_int_id
    new_pago_id = await get_next_int_id(db, models.Pago, 'id_pago')
    nuevo_pago = models.Pago(
        id_pago=new_pago_id,
        id_factura=factura.id_factura,
        monto=total,
        metodo_pago="qr",
        referencia_pago=generate_qr_reference(id_solicitud, total),
        estado_pago="completado",
        fecha_pago=datetime.now(),
        activo=1,
    )
    db.add(nuevo_pago)
    
    # Actualizar estado de la factura
    factura.estado_factura = "pagada_total"
    
    # Actualizar estado de la solicitud
    solicitud.estado_pago = "pagado_total"
    
    await db.commit()
    await db.refresh(factura)
    await db.refresh(nuevo_pago)
    
    # Obtener datos del recepcionista/admin que confirmó el pago
    recepcionista_nombre = ""
    if user_obj:
        nombre = getattr(user_obj, "nombre", "")
        apellido_p = getattr(user_obj, "apellido_paterno", "")
        apellido_m = getattr(user_obj, "apellido_materno", "")
        recepcionista_nombre = f"{nombre} {apellido_p} {apellido_m}".strip()
    
    # Obtener datos del paciente
    stmt_paciente = select(models.Paciente).where(
        models.Paciente.id_paciente == solicitud.id_paciente,
        models.Paciente.activo == 1
    )
    result_paciente = await db.execute(stmt_paciente)
    paciente = result_paciente.scalar_one_or_none()
    
    paciente_nombre = ""
    if paciente:
        paciente_nombre = f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}".strip()
    
    return {
        "mensaje": "Pago confirmado exitosamente",
        "id_pago": new_pago_id,
        "id_factura": factura.id_factura,
        "id_solicitud": id_solicitud,
        "monto": total,
        "fecha_pago": datetime.now().isoformat(),
        "recepcionista": recepcionista_nombre,
        "paciente": paciente_nombre,
        "items": items_factura,
    }


def numero_a_letras_bolivianos(numero):
    """
    Convierte un número a letras en formato boliviano.
    Ejemplo: 250.50 -> "DOSCIENTOS CINCUENTA 50/100 Bolivianos"
    """
    if numero == 0:
        return "CERO 00/100 Bolivianos"
    
    # Separar parte entera y decimal
    parte_entera = int(numero)
    centavos = int(round((numero - parte_entera) * 100))
    
    # Convertir parte entera a letras
    letras = numero_a_letras(parte_entera)
    
    return f"{letras} {centavos:02d}/100 Bolivianos"


def numero_a_letras(numero):
    """
    Convierte un número entero a letras en español.
    """
    unidades = ["", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"]
    especiales = ["DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"]
    decenas = ["", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
    centenas = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]
    
    if numero == 0:
        return "CERO"
    
    if numero == 100:
        return "CIEN"
    
    resultado = ""
    
    # Miles
    if numero >= 1000:
        miles = numero // 1000
        resto = numero % 1000
        
        if miles == 1:
            resultado += "MIL"
        else:
            resultado += numero_a_letras(miles) + " MIL"
        
        if resto > 0:
            resultado += " " + numero_a_letras(resto)
        
        return resultado
    
    # Centenas
    if numero >= 100:
        centena = numero // 100
        resto = numero % 100
        
        if centena == 1 and resto == 0:
            return "CIEN"
        
        resultado += centenas[centena]
        
        if resto > 0:
            resultado += " " + numero_a_letras(resto)
        
        return resultado
    
    # Decenas y unidades
    if numero >= 20:
        decena = numero // 10
        unidad = numero % 10
        
        if unidad == 0:
            return decenas[decena]
        
        if decena == 2:
            return "VEINTI" + unidades[unidad]
        
        return decenas[decena] + " Y " + unidades[unidad]
    
    if numero >= 10:
        return especiales[numero - 10]
    
    return unidades[numero]


@router.get("/facturas/{id_factura}/pdf-labotik")
async def generar_factura_pdf_labotik(
    id_factura: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """
    Genera el PDF de la factura con el formato específico de Labotik.
    
    Formato:
    - Labotik (logo/título)
    - Factura N° (empezando desde 1000)
    - Fecha (AA/MM/DD)
    - Datos de recepcionista
    - Importe
    - Cantidad | Descripción | Precio unitario
    - Monto Total
    - Monto Total de forma literal (xx/100 Bolivianos)
    """
    # Obtener factura
    stmt = select(models.Factura).where(
        models.Factura.id_factura == id_factura,
        models.Factura.activo == 1
    )
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Obtener detalles de la factura
    stmt_detalles = select(models.DetalleFactura).where(
        models.DetalleFactura.id_factura == id_factura,
        models.DetalleFactura.activo == 1
    )
    result_detalles = await db.execute(stmt_detalles)
    detalles = result_detalles.scalars().all()
    
    # Obtener datos del paciente
    stmt_paciente = select(models.Paciente).where(
        models.Paciente.id_paciente == factura.id_paciente,
        models.Paciente.activo == 1
    )
    result_paciente = await db.execute(stmt_paciente)
    paciente = result_paciente.scalar_one_or_none()
    
    paciente_nombre = ""
    if paciente:
        paciente_nombre = f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}".strip()
    
    # Obtener datos del recepcionista (último usuario que confirmó el pago)
    stmt_pago = select(models.Pago).where(
        models.Pago.id_factura == id_factura,
        models.Pago.activo == 1
    ).order_by(models.Pago.fecha_pago.desc()).limit(1)
    result_pago = await db.execute(stmt_pago)
    pago = result_pago.scalar_one_or_none()
    
    # Generar PDF
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        raise HTTPException(status_code=500, detail="Dependencia requerida 'reportlab' no instalada. Instale con: pip install reportlab")
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Colores
    color_primary = colors.HexColor('#C89666')  # Dorado/chocolate
    color_dark = colors.HexColor('#1E0F08')  # Chocolate oscuro
    color_text = colors.HexColor('#333333')
    color_light = colors.HexColor('#F5F5F5')
    
    y = height - 40
    
    # Header - Labotik
    c.setFillColor(color_primary)
    c.rect(40, y - 60, width - 80, 60, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 24)
    c.drawString(60, y - 25, 'Labotik')
    c.setFont('Helvetica', 10)
    c.drawString(60, y - 42, 'Laboratorio Clínico')
    
    # Factura N°
    c.setFillColor(color_dark)
    c.setFont('Helvetica-Bold', 14)
    c.drawRightString(width - 60, y - 25, f'Factura N° {factura.id_factura}')
    c.setFont('Helvetica', 10)
    c.drawRightString(width - 60, y - 42, f'Fecha: {factura.fecha_emision.strftime("%y/%m/%d") if factura.fecha_emision else datetime.now().strftime("%y/%m/%d")}')
    
    y -= 80
    
    # Datos del paciente
    c.setFillColor(color_text)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(40, y, 'PACIENTE:')
    c.setFont('Helvetica', 10)
    c.drawString(120, y, paciente_nombre)
    
    y -= 20
    c.setFont('Helvetica-Bold', 11)
    c.drawString(40, y, 'ATENDIDO POR:')
    c.setFont('Helvetica', 10)
    c.drawString(120, y, 'Recepción Labotik')
    
    y -= 30
    
    # Tabla de items
    # Header de tabla
    c.setFillColor(color_primary)
    c.rect(40, y - 25, width - 80, 25, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(50, y - 18, 'Cant.')
    c.drawString(100, y - 18, 'Descripción')
    c.drawRightString(width - 120, y - 18, 'P. Unitario')
    c.drawRightString(width - 50, y - 18, 'Total')
    
    y -= 35
    
    # Items
    c.setFillColor(color_text)
    c.setFont('Helvetica', 10)
    
    for d in detalles:
        # Obtener nombre de la prueba
        stmt_prueba = select(models.Prueba).where(models.Prueba.id_prueba == d.id_prueba)
        res_prueba = await db.execute(stmt_prueba)
        prueba = res_prueba.scalar_one_or_none()
        nombre_prueba = prueba.nombre if prueba else f'Prueba #{d.id_prueba}'
        
        # Fila alternada
        if detalles.index(d) % 2 == 0:
            c.setFillColor(color_light)
            c.rect(40, y - 18, width - 80, 20, fill=1, stroke=0)
            c.setFillColor(color_text)
        
        c.setFont('Helvetica', 10)
        c.drawString(50, y - 12, str(d.cantidad))
        c.drawString(100, y - 12, nombre_prueba)
        c.drawRightString(width - 120, y - 12, f'Bs {d.precio_unitario:.2f}')
        c.drawRightString(width - 50, y - 12, f'Bs {d.total_item:.2f}')
        
        y -= 22
    
    y -= 10
    
    # Total
    c.setFillColor(color_primary)
    c.rect(40, y - 30, width - 80, 30, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(50, y - 20, 'MONTO TOTAL:')
    c.drawRightString(width - 50, y - 20, f'Bs {factura.total:.2f}')
    
    y -= 40
    
    # Monto en letras
    c.setFillColor(color_text)
    c.setFont('Helvetica', 10)
    monto_letras = numero_a_letras_bolivianos(factura.total)
    c.drawString(40, y, f'Son: {monto_letras}')
    
    y -= 30
    
    # Pie de página
    c.setFillColor(colors.grey)
    c.setFont('Helvetica', 8)
    c.drawString(40, 40, 'Labotik - Laboratorio Clínico')
    c.drawRightString(width - 40, 40, f'Factura N° {factura.id_factura}')
    
    c.showPage()
    c.save()
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type='application/pdf',
        headers={"Content-Disposition": f"inline; filename=factura_labotik_{id_factura}.pdf"}
    )
