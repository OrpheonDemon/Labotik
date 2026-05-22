from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app import schemas, crud
from app.database import get_db
from app.dependencies import get_current_active_user
from fastapi.responses import StreamingResponse
import io
from sqlalchemy import select, update
from app import models
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/", response_model=list[schemas.ReporteOut])
async def list_reportes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.reporte_crud.get_multi(db, skip, limit)


@router.get("/{id_reporte}", response_model=schemas.ReporteOut)
async def get_reporte(id_reporte: int, db: AsyncSession = Depends(get_db)):
    reporte = await crud.reporte_crud.get(db, id_reporte)
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return reporte


@router.post("/", response_model=schemas.ReporteOut, status_code=201)
async def create_reporte(reporte_in: schemas.ReporteCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Verificar si ya existe un reporte para esta solicitud
        id_solicitud = reporte_in.id_solicitud
        stmt = select(models.Reporte).where(
            models.Reporte.id_solicitud == id_solicitud,
            models.Reporte.activo == 1
        )
        result = await db.execute(stmt)
        existing_reporte = result.scalar_one_or_none()
        
        if existing_reporte:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un reporte para la solicitud {id_solicitud}. Use PUT para actualizar el reporte existente."
            )
        
        # Establecer fecha_entrega como fecha actual
        data = reporte_in.dict(exclude_unset=True)
        data['fecha_entrega'] = datetime.now().date()
        
        logger.info(f"Creating reporte with data: {data}")
        
        try:
            nuevo = await crud.reporte_crud.create(db, schemas.ReporteCreate(**data))
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating reporte: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error al crear el reporte: {str(e)}"
            )
        
        # Refresh el objeto para obtener los datos completos
        await db.refresh(nuevo)
        
        # info del usuario que generó el reporte (opcional)
        user = None
        generado_nombre = None
        generado_ap = None
        generado_am = None
        if user:
            generado_nombre = getattr(user, 'nombre', None)
            generado_ap = getattr(user, 'apellido_paterno', None)
            generado_am = getattr(user, 'apellido_materno', None)

        out = nuevo.__dict__.copy()
        out['generado_nombre'] = generado_nombre
        out['generado_apellido_paterno'] = generado_ap
        out['generado_apellido_materno'] = generado_am
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_reporte: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado al crear el reporte: {str(e)}"
        )


@router.put("/{id_reporte}", response_model=schemas.ReporteOut)
async def update_reporte(id_reporte: int, reporte_in: schemas.ReporteUpdate, db: AsyncSession = Depends(get_db)):
    updated = await crud.reporte_crud.update(db, id_reporte, reporte_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return updated


@router.delete("/{id_reporte}")
async def delete_reporte(id_reporte: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.reporte_crud.soft_delete(db, id_reporte)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return {"message": "Reporte desactivado (borrado lógico)"}


@router.post("/{id_reporte}/generar")
async def generar_reporte(id_reporte: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_active_user)):
    # Obtener reporte
    reporte = await crud.reporte_crud.get(db, id_reporte)
    if not reporte:
        raise HTTPException(status_code=404, detail='Reporte no encontrado')

    # Obtener solicitud y datos de paciente, médico y laboratorista
    id_solicitud = getattr(reporte, 'id_solicitud', None)
    solicitud_stmt = (
        select(models.Solicitud, models.Paciente, models.Medico, models.Laboratorista)
        .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente)
        .outerjoin(models.Medico, models.Medico.id_medico == models.Solicitud.id_medico)
        .outerjoin(models.Laboratorista, models.Laboratorista.id_laboratorista == models.Solicitud.id_laboratorista)
        .where(models.Solicitud.id_solicitud == id_solicitud)
    )
    res = await db.execute(solicitud_stmt)
    row = res.first()
    solicitud, paciente, medico, laboratorista = (row if row else (None, None, None, None))

    if not solicitud:
        raise HTTPException(status_code=404, detail='Solicitud asociada no encontrada')

    # Consultar detalles de solicitud con prueba, área y resultado
    detalles_stmt = (
        select(models.DetalleSolicitud, models.Prueba, models.AreaLaboratorio, models.Resultado)
        .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba)
        .join(models.AreaLaboratorio, models.AreaLaboratorio.id_area == models.Prueba.id_area)
        .outerjoin(models.Resultado, models.Resultado.id_detalle == models.DetalleSolicitud.id_detalle)
        .where(models.DetalleSolicitud.id_solicitud == id_solicitud, models.DetalleSolicitud.activo == 1)
    )
    res = await db.execute(detalles_stmt)
    detalle_rows = res.all()

    # Organizar resultados por área
    areas = {}
    for detalle, prueba, area, resultado in detalle_rows:
        area_nombre = area.nombre if area else 'Sin área'
        if area_nombre not in areas:
            areas[area_nombre] = []

        areas[area_nombre].append({
            'prueba_nombre': prueba.nombre if prueba else f'Prueba {detalle.id_prueba}',
            'valor_referencia': prueba.valor_referencia if prueba else '',
            'unidad': prueba.unidad if prueba else '',
            'resultado': resultado.resultado if resultado else '',
            'observacion': resultado.observacion if resultado else '',
            'estado': resultado.estado if resultado else 'pendiente',
        })

    # Marcar resultados como 'reportado' para los detalles relacionados
    for detalle, _, _, resultado in detalle_rows:
        if resultado and resultado.activo == 1:
            upd = (
                update(models.Resultado)
                .where(models.Resultado.id_resultado == resultado.id_resultado)
                .values(estado='reportado', fecha_validacion=datetime.now())
            )
            await db.execute(upd)

    # Marcar reporte como entregado
    upd_rep = update(models.Reporte).where(models.Reporte.id_reporte == id_reporte).values(estado='entregado', fecha_entrega=datetime.now().date())
    await db.execute(upd_rep)
    await db.commit()

    # Generar PDF (importar reportlab en tiempo de ejecución para no romper el arranque si falta la dependencia)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.utils import ImageReader
    except ImportError:
        raise HTTPException(status_code=500, detail="Dependencia requerida 'reportlab' no instalada. Instale con: pip install reportlab")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin

    # Fondo del encabezado en tonos café chocolate oscuro
    c.setFillColor(colors.HexColor('#3d2b1f'))
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)
    c.setFillColor(colors.HexColor('#f8efdd'))
    c.setFont('Helvetica-Bold', 26)
    c.drawString(margin, height - 70, 'LABOTIK')
    c.setFont('Helvetica', 12)
    c.drawString(margin, height - 92, 'Laboratorio Clínico - Reporte de Resultados')

    # Logo desde ruta absoluta del proyecto
    import os
    logo_path = r'C:\Users\Rothe\Rotherick\Laboratorio\frontend\static\images\LaboLogo.png'
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.getcwd(), 'frontend', 'static', 'images', 'LaboLogo.png')
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            c.drawImage(logo, width - 170, height - 112, width=120, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    y = height - 140
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(margin, y, f'Paciente: {paciente.nombre} {paciente.apellido_paterno or ""} {paciente.apellido_materno or ""}'.strip())
    c.drawRightString(width - margin, y, f'ID Reporte: {id_reporte}')
    y -= 16
    c.setFont('Helvetica', 10)
    c.drawRightString(width - margin, y, f'ID Solicitud: {solicitud.id_solicitud}')
    y -= 16
    medico_nombre = f'{medico.nombre} {medico.apellido_paterno or ""} {medico.apellido_materno or ""}'.strip() if medico else 'Sin médico'
    laboratorista_nombre = f'{laboratorista.nombre} {laboratorista.apellido_paterno or ""} {laboratorista.apellido_materno or ""}'.strip() if laboratorista else 'Sin laboratorista'
    c.drawString(margin, y, f'Médico: {medico_nombre}')
    c.drawRightString(width - margin, y, f'Fecha entrega: {reporte.fecha_entrega or datetime.now().date()}')
    y -= 16
    c.drawString(margin, y, f'Laboratorista: {laboratorista_nombre}')
    y -= 16
    c.drawString(margin, y, f'Observaciones: {reporte.observaciones or "Sin observaciones"}')
    y -= 24

    # Tabla de resultados por área
    for area_nombre, items in areas.items():
        if y < 120:
            c.showPage()
            y = height - margin
        c.setFillColor(colors.HexColor('#6a4f39'))
        c.rect(margin, y - 22, width - 2 * margin, 22, fill=True, stroke=False)
        c.setFillColor(colors.HexColor('#f8efdd'))
        c.setFont('Helvetica-Bold', 12)
        c.drawString(margin + 4, y - 16, f'Área: {area_nombre}')
        y -= 32
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(colors.HexColor('#3d2b1f'))
        c.drawString(margin, y, 'Prueba')
        c.drawString(margin + 220, y, 'Resultado')
        c.drawString(margin + 320, y, 'Valor Ref')
        c.drawString(margin + 400, y, 'Unidad')
        c.drawString(margin + 470, y, 'Observación')
        y -= 14
        c.setStrokeColor(colors.HexColor('#d1c4a5'))
        c.setLineWidth(0.5)
        c.line(margin, y + 2, width - margin, y + 2)
        y -= 10

        c.setFont('Helvetica', 10)
        for idx, item in enumerate(items):
            if y < 100:
                c.showPage()
                y = height - margin
            if idx % 2 == 0:
                c.setFillColorRGB(0.98, 0.96, 0.92)
                c.rect(margin, y - 2, width - 2 * margin, 16, fill=True, stroke=False)
            c.setFillColor(colors.black)
            c.drawString(margin + 4, y, item['prueba_nombre'] or '-')
            c.drawString(margin + 220, y, str(item['resultado'] or '-'))
            c.drawString(margin + 320, y, str(item['valor_referencia'] or '-'))
            c.drawString(margin + 400, y, str(item['unidad'] or '-'))
            c.drawString(margin + 470, y, item['observacion'] or '-')
            y -= 18
        y -= 12

    # Firma del laboratorista
    if y < 180:
        c.showPage()
        y = height - margin
    else:
        y -= 36

    c.setStrokeColor(colors.HexColor('#d1c4a5'))
    c.setLineWidth(0.7)
    c.line(margin, y, width - margin, y)
    y -= 24

    c.setFont('Helvetica-Bold', 10)
    c.drawString(margin, y, 'Firma del laboratorista:')
    c.drawRightString(width - margin, y, f'ID Reporte: {id_reporte}')
    y -= 20
    c.line(margin + 140, y, margin + 380, y)
    c.setFont('Helvetica', 9)
    c.drawString(margin + 142, y - 14, laboratorista_nombre)

    c.save()
    buffer.seek(0)
    filename_date = datetime.now().strftime('%Y%m%d')
    filename = f"labotik_{filename_date}_{id_reporte}.pdf"
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"inline; filename={filename}"})