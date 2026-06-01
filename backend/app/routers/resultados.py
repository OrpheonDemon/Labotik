from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import logging
import traceback

from app import schemas, crud, models
from app.database import get_db
from app.dependencies import get_current_active_user, require_laboratorista, optional_current_user
from fastapi.responses import StreamingResponse
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resultados", tags=["Resultados"])


@router.get("/registered", response_model=list[schemas.ResultadoOut])
async def list_registered_resultados(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(optional_current_user),
    skip: int = 0,
    limit: int = 1000,
):
    """Devuelve todos los resultados cuyo estado sea 'registrado'."""
    stmt = (
        select(models.Resultado, models.Prueba, models.Paciente, models.DetalleSolicitud, models.Solicitud)
        .join(models.DetalleSolicitud, models.DetalleSolicitud.id_detalle == models.Resultado.id_detalle)
        .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba)
        .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud)
        .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
        .where(models.Resultado.estado == 'registrado', models.Resultado.activo == 1)
        .offset(skip).limit(limit)
    )
    res = await db.execute(stmt)
    rows = res.all()
    out = []
    for resultado, prueba, paciente, detalle, solicitud in rows:
        apellido = paciente.apellido_paterno if paciente else None
        am = paciente.apellido_materno if paciente else None
        out.append({
            'id_resultado': resultado.id_resultado,
            'id_detalle': resultado.id_detalle,
            'resultado': resultado.resultado,
            'observacion': resultado.observacion,
            'validado_por': resultado.validado_por,
            'fecha_validacion': resultado.fecha_validacion,
            'estado': resultado.estado,
            'es_anormal': resultado.es_anormal,
            'activo': resultado.activo,
            'created_at': resultado.created_at,
            'id_prueba': prueba.id_prueba if prueba else None,
            'prueba_nombre': prueba.nombre if prueba else None,
            'valor_referencia': prueba.valor_referencia if prueba else None,
            'id_solicitud': detalle.id_solicitud if detalle else None,
            'id_paciente': paciente.id_paciente if paciente else None,
            'paciente_nombre': paciente.nombre if paciente else None,
            'paciente_apellido_paterno': apellido,
            'paciente_apellido_materno': am,
        })
    return out


@router.get("/{id_resultado}/completo")
async def get_resultado_completo(
    id_resultado: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(models.Resultado, models.DetalleSolicitud, models.Prueba, models.Solicitud, models.Paciente, models.Medico, models.Laboratorista)
        .join(models.DetalleSolicitud, models.DetalleSolicitud.id_detalle == models.Resultado.id_detalle)
        .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba, isouter=True)
        .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud, isouter=True)
        .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
        .join(models.Medico, models.Medico.id_medico == models.Solicitud.id_medico, isouter=True)
        .join(models.Laboratorista, models.Laboratorista.id_laboratorista == models.Solicitud.id_laboratorista, isouter=True)
        .where(models.Resultado.id_resultado == id_resultado, models.Resultado.activo == 1)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    
    resultado, detalle, prueba, solicitud, paciente, medico, laboratorista = row
    
    return {
        'id_resultado': resultado.id_resultado,
        'id_detalle': resultado.id_detalle,
        'resultado': resultado.resultado,
        'observacion': resultado.observacion,
        'estado': resultado.estado,
        'es_anormal': resultado.es_anormal,
        'fecha_validacion': resultado.fecha_validacion,
        'prueba': {
            'id_prueba': prueba.id_prueba if prueba else None,
            'nombre': prueba.nombre if prueba else None,
            'valor_referencia': prueba.valor_referencia if prueba else None,
            'unidad': prueba.unidad if prueba else None,
        } if prueba else None,
        'solicitud': {
            'id_solicitud': solicitud.id_solicitud if solicitud else None,
            'prioridad': solicitud.prioridad if solicitud else None,
            'estado_pago': solicitud.estado_pago if solicitud else None,
            'observaciones': solicitud.observaciones if solicitud else None,
        } if solicitud else None,
        'paciente': {
            'id_paciente': paciente.id_paciente if paciente else None,
            'nombre': paciente.nombre if paciente else None,
            'apellido_paterno': paciente.apellido_paterno if paciente else None,
            'apellido_materno': paciente.apellido_materno if paciente else None,
        } if paciente else None,
        'medico': {
            'id_medico': medico.id_medico if medico else None,
            'nombre': medico.nombre if medico else None,
            'apellido_paterno': medico.apellido_paterno if medico else None,
            'apellido_materno': medico.apellido_materno if medico else None,
        } if medico else None,
        'laboratorista': {
            'id_laboratorista': laboratorista.id_laboratorista if laboratorista else None,
            'nombre': laboratorista.nombre if laboratorista else None,
            'apellido_paterno': laboratorista.apellido_paterno if laboratorista else None,
            'apellido_materno': laboratorista.apellido_materno if laboratorista else None,
        } if laboratorista else None,
    }


@router.get("/", response_model=list[schemas.ResultadoOut])
async def list_resultados(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(optional_current_user),
):
    """Devuelve resultados activos (paginado) incluyendo nombre de la prueba si está disponible."""
    stmt = (
        select(models.Resultado, models.Prueba, models.Paciente, models.DetalleSolicitud, models.Solicitud)
        .join(models.DetalleSolicitud, models.DetalleSolicitud.id_detalle == models.Resultado.id_detalle)
        .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba, isouter=True)
        .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud, isouter=True)
        .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
        .where(models.Resultado.activo == 1)
        .offset(skip).limit(limit)
    )
    res = await db.execute(stmt)
    rows = res.all()
    out = []
    for resultado, prueba, paciente, detalle, solicitud in rows:
        apellido = paciente.apellido_paterno if paciente else None
        am = paciente.apellido_materno if paciente else None
        out.append({
            'id_resultado': resultado.id_resultado,
            'id_detalle': resultado.id_detalle,
            'resultado': resultado.resultado,
            'observacion': resultado.observacion,
            'validado_por': resultado.validado_por,
            'fecha_validacion': resultado.fecha_validacion,
            'estado': resultado.estado,
            'es_anormal': resultado.es_anormal,
            'activo': resultado.activo,
            'created_at': resultado.created_at,
            'id_prueba': prueba.id_prueba if prueba else None,
            'prueba_nombre': prueba.nombre if prueba else None,
            'valor_referencia': prueba.valor_referencia if prueba else None,
            'id_solicitud': detalle.id_solicitud if detalle else None,
            'id_paciente': paciente.id_paciente if paciente else None,
            'paciente_nombre': paciente.nombre if paciente else None,
            'paciente_apellido_paterno': apellido,
            'paciente_apellido_materno': am,
        })
    return out


@router.get("/{id_resultado}", response_model=schemas.ResultadoOut)
async def get_resultado(
    id_resultado: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    # Permitimos acceso solo a laboratoristas y médicos por ahora
    if current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver resultados individuales")

    stmt = (
        select(models.Resultado, models.Prueba, models.Paciente, models.DetalleSolicitud, models.Solicitud)
        .join(models.DetalleSolicitud, models.DetalleSolicitud.id_detalle == models.Resultado.id_detalle)
        .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba, isouter=True)
        .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud, isouter=True)
        .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
        .where(models.Resultado.id_resultado == id_resultado, models.Resultado.activo == 1)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    resultado, prueba, paciente, detalle, solicitud = row
    apellido = paciente.apellido_paterno if paciente else None
    am = paciente.apellido_materno if paciente else None
    return {
        'id_resultado': resultado.id_resultado,
        'id_detalle': resultado.id_detalle,
        'resultado': resultado.resultado,
        'observacion': resultado.observacion,
        'validado_por': resultado.validado_por,
        'fecha_validacion': resultado.fecha_validacion,
        'estado': resultado.estado,
        'es_anormal': resultado.es_anormal,
        'activo': resultado.activo,
        'created_at': resultado.created_at,
        'id_prueba': prueba.id_prueba if prueba else None,
        'prueba_nombre': prueba.nombre if prueba else None,
        'valor_referencia': prueba.valor_referencia if prueba else None,
        'id_solicitud': detalle.id_solicitud if detalle else None,
        'id_paciente': paciente.id_paciente if paciente else None,
        'paciente_nombre': paciente.nombre if paciente else None,
        'paciente_apellido_paterno': apellido,
        'paciente_apellido_materno': am,
    }


async def _actualizar_solicitud_con_laboratorista(db: AsyncSession, id_detalle: int, current_user: Optional[dict] = None, marcar_registrado: bool = False):
    """Actualiza la solicitud padre: fecha_toma_muestra, id_laboratorista y estado si procede."""
    stmt = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_detalle == id_detalle)
    result = await db.execute(stmt)
    detalle = result.scalar_one_or_none()
    if not detalle:
        return

    id_laboratorista = None
    if current_user:
        user = current_user.get("user")
        if user and hasattr(user, "id_laboratorista"):
            id_laboratorista = user.id_laboratorista

    values = {"fecha_toma_muestra": datetime.now()}
    if id_laboratorista is not None:
        values["id_laboratorista"] = id_laboratorista
    if marcar_registrado:
        values["estado"] = "completado"

    stmt_upd = (
        update(models.Solicitud)
        .where(models.Solicitud.id_solicitud == detalle.id_solicitud)
        .values(**values)
    )
    await db.execute(stmt_upd)
    await db.commit()


@router.post("/", response_model=schemas.ResultadoOut, status_code=201)
async def create_resultado(
    resultado_in: schemas.ResultadoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(optional_current_user),
):
    """Crea un resultado validando que el detalle exista y actualiza la solicitud si procede."""
    try:
        # Validar que el detalle exista
        detalle = await crud.detalle_solicitud_crud.get(db, resultado_in.id_detalle)
        if not detalle:
            raise HTTPException(status_code=400, detail=f"Detalle de solicitud {resultado_in.id_detalle} no encontrado")

        # Preparar payload y registrar laboratorista que valida si está disponible
        data = resultado_in.dict(exclude_unset=True)
        validado_nombre = validado_ap = validado_am = None
        if current_user:
            user = current_user.get('user')
            if user and hasattr(user, 'id_laboratorista') and user.id_laboratorista:
                data['validado_por'] = user.id_laboratorista
                validado_nombre = getattr(user, 'nombre', None)
                validado_ap = getattr(user, 'apellido_paterno', None)
                validado_am = getattr(user, 'apellido_materno', None)

        nuevo = await crud.resultado_crud.create(db, schemas.ResultadoCreate(**data))

        # Actualizar la solicitud padre sólo si el resultado quedó como 'registrado'
        result_estado = getattr(nuevo, "estado", "pendiente")
        marcar = result_estado == "registrado"
        if marcar:
            await _actualizar_solicitud_con_laboratorista(db, nuevo.id_detalle, current_user, marcar_registrado=True)

        # Obtener nombre de la prueba y paciente asociada al detalle
        stmt = (
            select(models.DetalleSolicitud, models.Prueba, models.Paciente)
            .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba)
            .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud)
            .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
            .where(models.DetalleSolicitud.id_detalle == nuevo.id_detalle)
        )
        r = await db.execute(stmt)
        row = r.first()
        detalle, prueba, paciente = (row if row else (None, None, None))

        return {
            'id_resultado': nuevo.id_resultado,
            'id_detalle': nuevo.id_detalle,
            'resultado': nuevo.resultado,
            'observacion': nuevo.observacion,
            'validado_por': nuevo.validado_por,
            'validado_nombre': validado_nombre,
            'validado_apellido_paterno': validado_ap,
            'validado_apellido_materno': validado_am,
            'fecha_validacion': nuevo.fecha_validacion,
            'estado': nuevo.estado,
            'es_anormal': nuevo.es_anormal,
            'activo': nuevo.activo,
            'created_at': nuevo.created_at,
            'id_prueba': prueba.id_prueba if prueba else None,
            'prueba_nombre': prueba.nombre if prueba else None,
            'id_paciente': paciente.id_paciente if paciente else None,
            'paciente_nombre': paciente.nombre if paciente else None,
            'paciente_apellido_paterno': paciente.apellido_paterno if paciente else None,
            'paciente_apellido_materno': paciente.apellido_materno if paciente else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creando resultado: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id_resultado}", response_model=schemas.ResultadoOut)
async def update_resultado(
    id_resultado: int,
    resultado_in: schemas.ResultadoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(optional_current_user),
):
    """Actualiza un resultado; si queda como 'registrado' actualiza la solicitud padre."""
    try:
        # Preparar payload y registrar laboratorista validador si está disponible
        payload = resultado_in.dict(exclude_unset=True)
        validado_nombre = validado_ap = validado_am = None
        if current_user:
            user = current_user.get('user')
            if user and hasattr(user, 'id_laboratorista') and user.id_laboratorista:
                payload['validado_por'] = user.id_laboratorista
                validado_nombre = getattr(user, 'nombre', None)
                validado_ap = getattr(user, 'apellido_paterno', None)
                validado_am = getattr(user, 'apellido_materno', None)

        updated = await crud.resultado_crud.update(db, id_resultado, schemas.ResultadoUpdate(**payload))
        if not updated:
            raise HTTPException(status_code=404, detail="Resultado no encontrado")

        # Si se actualizó el resultado y su estado es 'registrado', actualizar la solicitud padre
        if getattr(updated, "id_detalle", None) and getattr(updated, "estado", None) == "registrado":
            stmt = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_detalle == updated.id_detalle)
            r = await db.execute(stmt)
            detalle = r.scalar_one_or_none()
            if detalle:
                id_laboratorista = None
                if current_user:
                    user = current_user.get("user")
                    if user and hasattr(user, "id_laboratorista"):
                        id_laboratorista = user.id_laboratorista
                values = {"estado": "completado", "fecha_toma_muestra": datetime.now()}
                if id_laboratorista is not None:
                    values["id_laboratorista"] = id_laboratorista
                stmt_upd = (
                    update(models.Solicitud)
                    .where(models.Solicitud.id_solicitud == detalle.id_solicitud)
                    .values(**values)
                )
                await db.execute(stmt_upd)
                await db.commit()

        # Enriquecer con nombre de prueba y paciente
        stmt = (
            select(models.DetalleSolicitud, models.Prueba, models.Paciente)
            .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba)
            .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud)
            .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
            .where(models.DetalleSolicitud.id_detalle == updated.id_detalle)
        )
        r = await db.execute(stmt)
        row = r.first()
        detalle, prueba, paciente = (row if row else (None, None, None))

        return {
            'id_resultado': updated.id_resultado,
            'id_detalle': updated.id_detalle,
            'resultado': updated.resultado,
            'observacion': updated.observacion,
            'validado_por': updated.validado_por,
            'validado_nombre': validado_nombre,
            'validado_apellido_paterno': validado_ap,
            'validado_apellido_materno': validado_am,
            'fecha_validacion': updated.fecha_validacion,
            'estado': updated.estado,
            'es_anormal': updated.es_anormal,
            'activo': updated.activo,
            'created_at': updated.created_at,
            'id_prueba': prueba.id_prueba if prueba else None,
            'prueba_nombre': prueba.nombre if prueba else None,
            'id_paciente': paciente.id_paciente if paciente else None,
            'paciente_nombre': paciente.nombre if paciente else None,
            'paciente_apellido_paterno': paciente.apellido_paterno if paciente else None,
            'paciente_apellido_materno': paciente.apellido_materno if paciente else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error actualizando resultado: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id_resultado}")
async def delete_resultado(
    id_resultado: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista),
):
    deleted = await crud.resultado_crud.soft_delete(db, id_resultado)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return {"message": "Resultado desactivado (borrado lógico)"}

@router.post("/{id_resultado}/reportar")
async def reportar_resultado(
    id_resultado: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista),
):
    """Marca un resultado individual como 'reportado'."""
    stmt = (
        update(models.Resultado)
        .where(models.Resultado.id_resultado == id_resultado, models.Resultado.activo == 1)
        .values(estado='reportado', fecha_validacion=datetime.now())
    )
    res = await db.execute(stmt)
    await db.commit()
    return {"message": "Resultado marcado como reportado"}

@router.post("/{id_resultado}/generar_pdf")
async def generar_pdf_resultado(
    id_resultado: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista),
):
    """Genera un PDF para un único resultado y marca el resultado como reportado."""
    # Consultar resultado y datos relacionados
    stmt = (
        select(models.Resultado, models.DetalleSolicitud, models.Prueba, models.Solicitud, models.Paciente, models.Medico, models.Laboratorista)
        .join(models.DetalleSolicitud, models.DetalleSolicitud.id_detalle == models.Resultado.id_detalle)
        .join(models.Prueba, models.Prueba.id_prueba == models.DetalleSolicitud.id_prueba, isouter=True)
        .join(models.Solicitud, models.Solicitud.id_solicitud == models.DetalleSolicitud.id_solicitud, isouter=True)
        .join(models.Paciente, models.Paciente.id_paciente == models.Solicitud.id_paciente, isouter=True)
        .join(models.Medico, models.Medico.id_medico == models.Solicitud.id_medico, isouter=True)
        .join(models.Laboratorista, models.Laboratorista.id_laboratorista == models.Solicitud.id_laboratorista, isouter=True)
        .where(models.Resultado.id_resultado == id_resultado, models.Resultado.activo == 1)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")

    resultado, detalle, prueba, solicitud, paciente, medico, laboratorista = row

    # Marcar resultado como reportado
    upd = (
        update(models.Resultado)
        .where(models.Resultado.id_resultado == id_resultado)
        .values(estado='reportado', fecha_validacion=datetime.now())
    )
    await db.execute(upd)
    await db.commit()

    # Generar PDF
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        raise HTTPException(status_code=500, detail="Dependencia requerida 'reportlab' no instalada. Instale con: pip install reportlab")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Encabezado
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, y, 'Laboratorio Clínico - Resultado')
    c.setFont('Helvetica', 10)
    c.drawString(40, y-20, f'ID Resultado: {resultado.id_resultado}')
    c.drawString(200, y-20, f'ID Detalle: {resultado.id_detalle}')
    c.drawString(40, y-35, f'Fecha validación: {resultado.fecha_validacion or "-"}')

    # Datos del paciente / médico / laboratorista
    c.setFont('Helvetica-Bold', 12)
    c.drawString(40, y-60, 'Datos del paciente:')
    c.setFont('Helvetica', 10)
    pac_name = (f"{paciente.nombre} {paciente.apellido_paterno} {paciente.apellido_materno or ''}".strip()) if paciente else '-'
    c.drawString(60, y-75, f'Nombre: {pac_name}')
    c.drawString(300, y-75, f'ID Paciente: {solicitud.id_paciente if solicitud else "-"}')

    c.setFont('Helvetica-Bold', 12)
    c.drawString(40, y-95, 'Solicitante / Laboratorista:')
    c.setFont('Helvetica', 10)
    medico_name = (f"{medico.nombre} {medico.apellido_paterno} {medico.apellido_materno or ''}".strip()) if medico else '-'
    lab_name = (f"{laboratorista.nombre} {laboratorista.apellido_paterno} {laboratorista.apellido_materno or ''}".strip()) if laboratorista else '-'
    c.drawString(60, y-110, f'Médico: {medico_name}')
    c.drawString(60, y-125, f'Laboratorista: {lab_name}')

    # Resultado y observaciones
    c.setFont('Helvetica-Bold', 12)
    c.drawString(40, y-150, 'Resultado:')
    c.setFont('Helvetica', 10)
    c.drawString(60, y-165, f'Prueba: {prueba.nombre if prueba else "-"}')
    c.drawString(60, y-180, f'Valor: {resultado.resultado}')
    c.drawString(60, y-195, f'Observación: {resultado.observacion or ""}')

    c.showPage()
    c.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type='application/pdf', headers={"Content-Disposition": f"inline; filename=resultado_{id_resultado}.pdf"})