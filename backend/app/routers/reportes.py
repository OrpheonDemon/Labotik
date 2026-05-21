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
async def create_reporte(reporte_in: schemas.ReporteCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_active_user)):
    # Establecer fecha_entrega como fecha actual y registrar quien lo genera (en la respuesta)
    data = reporte_in.dict(exclude_unset=True)
    data['fecha_entrega'] = datetime.now()
    nuevo = await crud.reporte_crud.create(db, schemas.ReporteCreate(**data))

    # info del usuario que generó el reporte
    user = current_user.get('user') if current_user else None
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

    # Obtener solicitud y detalles
    id_solicitud = getattr(reporte, 'id_solicitud', None)
    detalles_stmt = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_solicitud == id_solicitud, models.DetalleSolicitud.activo == 1)
    res = await db.execute(detalles_stmt)
    detalles = res.scalars().all()

    # Marcar resultados como 'reportado' para los detalles relacionados
    for d in detalles:
        upd = (
            update(models.Resultado)
            .where(models.Resultado.id_detalle == d.id_detalle, models.Resultado.activo == 1)
            .values(estado='reportado')
        )
        await db.execute(upd)

    # Marcar reporte como entregado
    upd_rep = update(models.Reporte).where(models.Reporte.id_reporte == id_reporte).values(estado='entregado', fecha_entrega=datetime.now())
    await db.execute(upd_rep)
    await db.commit()

    # Consultar resultados para incluir en el PDF
    resultados_data = []
    for d in detalles:
        stmt = select(models.Resultado, models.Prueba).where(models.Resultado.id_detalle == d.id_detalle).join(models.Prueba, models.Prueba.id_prueba == d.id_prueba, isouter=True)
        r = await db.execute(stmt)
        for resultado, prueba in r.all():
            resultados_data.append({
                'id_resultado': resultado.id_resultado,
                'id_detalle': resultado.id_detalle,
                'prueba_nombre': prueba.nombre if prueba else None,
                'resultado': resultado.resultado,
                'observacion': resultado.observacion,
            })

    # Generar PDF (importar reportlab en tiempo de ejecución para no romper el arranque si falta la dependencia)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        raise HTTPException(status_code=500, detail="Dependencia requerida 'reportlab' no instalada. Instale con: pip install reportlab")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Logo
    import os
    logo_path = os.path.join(os.getcwd(), 'frontend', 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, y-40, width=120, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.setFont('Helvetica-Bold', 16)
    c.drawString(180, y, 'Laboratorio Clínico - Reporte de Resultados')
    c.setFont('Helvetica', 10)
    c.drawString(40, y-60, f'ID Reporte: {reporte.id_reporte}')
    c.drawString(200, y-60, f'ID Solicitud: {reporte.id_solicitud or "-"}')
    c.drawString(40, y-75, f'Fecha generación: {datetime.now()}')
    c.drawString(40, y-90, f'Observaciones: {reporte.observaciones or ""}')

    # Tabla
    c.setFont('Helvetica-Bold', 11)
    table_y = y-120
    c.drawString(40, table_y, 'Prueba')
    c.drawString(300, table_y, 'Resultado')
    c.drawString(420, table_y, 'Observación')
    c.setFont('Helvetica', 10)
    cur_y = table_y - 20
    for row in resultados_data:
        c.drawString(40, cur_y, row.get('prueba_nombre') or ('Prueba #' + str(row.get('id_detalle'))))
        c.drawString(300, cur_y, str(row.get('resultado') or ''))
        c.drawString(420, cur_y, str(row.get('observacion') or ''))
        cur_y -= 16
        if cur_y < 60:
            c.showPage()
            cur_y = height - 60

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"inline; filename=reporte_{id_reporte}.pdf"})