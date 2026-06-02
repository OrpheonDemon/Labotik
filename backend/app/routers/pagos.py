from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id
from app.dependencies import get_current_active_user, get_current_user_from_token, require_paciente, require_laboratorista, require_pagos_roles
from datetime import datetime

router = APIRouter(prefix="/pagos", tags=["Pagos"])

@router.get("/", response_model=list[schemas.PagoOut])
async def list_pagos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """Lista los pagos. Acceso exclusivo para Administrador, Recepcionista y Paciente."""
    return await crud.pago_crud.get_multi(db, skip, limit)

@router.get("/{id_pago}", response_model=schemas.PagoOut)
async def get_pago(
    id_pago: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """Obtiene un pago por ID. Acceso exclusivo para Administrador, Recepcionista y Paciente."""
    pago = await crud.pago_crud.get(db, id_pago)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago

@router.post("/", response_model=schemas.PagoOut, status_code=201)
async def create_pago(
    pago_in: schemas.PagoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """Crea un nuevo pago. Acceso exclusivo para Administrador, Recepcionista y Paciente."""
    return await crud.pago_crud.create(db, pago_in)

@router.put("/{id_pago}", response_model=schemas.PagoOut)
async def update_pago(
    id_pago: int,
    pago_in: schemas.PagoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """Actualiza un pago. Acceso exclusivo para Administrador, Recepcionista y Paciente."""
    updated = await crud.pago_crud.update(db, id_pago, pago_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return updated

@router.delete("/{id_pago}")
async def delete_pago(
    id_pago: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_pagos_roles),
):
    """Desactiva un pago (borrado lógico). Acceso exclusivo para Administrador, Recepcionista y Paciente."""
    deleted = await crud.pago_crud.soft_delete(db, id_pago)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return {"message": "Pago desactivado (borrado lógico)"}


@router.get("/factura/{id_factura}", response_model=list[schemas.PagoOut])
async def get_pagos_by_factura(id_factura: int, db: AsyncSession = Depends(get_db)):
    """Obtiene todos los pagos realizados para una factura específica"""
    stmt = select(models.Pago).where(
        models.Pago.activo == 1,
        models.Pago.id_factura == id_factura
    ).order_by(models.Pago.fecha_pago.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/paciente/{id_paciente}/historial", response_model=list[schemas.PagoOut])
async def get_historial_pagos_paciente(
    id_paciente: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_paciente)
):
    """Historial de pagos de un paciente"""
    # Buscar facturas del paciente y luego sus pagos
    stmt = select(models.Pago).join(
        models.Factura, models.Pago.id_factura == models.Factura.id_factura
    ).where(
        models.Pago.activo == 1,
        models.Factura.id_paciente == id_paciente,
        models.Factura.activo == 1
    ).order_by(models.Pago.fecha_pago.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/solicitudes/no-pagadas", response_model=list[schemas.SolicitudOut])
async def list_solicitudes_no_pagadas(
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Devuelve las solicitudes cuyo estado de pago NO es 'pagado_total'
    (es decir, 'no_pagado' o 'pagado_parcial'). Se utiliza para listar
    solicitudes pendientes de pago en los paneles de Recepcionista,
    Administrador y Paciente.

    Permisos:
    - Administrador / Recepcionista: ven todas las solicitudes no pagadas.
    - Paciente: ve únicamente sus propias solicitudes no pagadas.
    """
    rol = current_user.get("rol")
    user_obj = current_user.get("user")
    user_id = None
    if user_obj is not None:
        user_id = getattr(user_obj, "id_paciente", None) or getattr(user_obj, "id_administrador", None)

    stmt = select(models.Solicitud).where(
        models.Solicitud.activo == 1,
        models.Solicitud.estado_pago.in_(["no_pagado", "pagado_parcial"])
    )

    # Si es paciente, filtrar por id_paciente del usuario autenticado
    if rol == "paciente" and user_id:
        stmt = stmt.where(models.Solicitud.id_paciente == user_id)

    stmt = stmt.order_by(models.Solicitud.fecha_solicitud.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    solicitudes = result.scalars().all()

    # Enriquecer con datos del paciente y detalles
    for solicitud in solicitudes:
        # detalles
        stmt_d = select(models.DetalleSolicitud).where(
            models.DetalleSolicitud.id_solicitud == solicitud.id_solicitud,
            models.DetalleSolicitud.activo == 1
        )
        res_d = await db.execute(stmt_d)
        solicitud.detalles = res_d.scalars().all()
        # paciente
        stmt_p = select(models.Paciente).where(
            models.Paciente.id_paciente == solicitud.id_paciente,
            models.Paciente.activo == 1
        )
        res_p = await db.execute(stmt_p)
        pac = res_p.scalar_one_or_none()
        if pac:
            solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
            solicitud.paciente_nombre_nombre = pac.nombre
            solicitud.paciente_apellido_paterno = pac.apellido_paterno
            solicitud.paciente_apellido_materno = pac.apellido_materno

    return solicitudes


@router.post("/solicitudes/{id_solicitud}/pagar")
async def pagar_solicitud(
    id_solicitud: int,
    metodo_pago: str = "efectivo",
    monto: float = None,
    referencia: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """
    Realiza el pago completo de una solicitud.

    - Busca la factura asociada a la solicitud.
    - Crea un pago en estado 'completado' por el monto total de la factura.
    - Cambia el estado de la solicitud a 'pagado_total'.
    - Cambia el estado de la factura a 'pagada_total'.

    Permisos:
    - Administrador / Recepcionista: pueden cobrar cualquier solicitud.
    - Paciente: solo puede pagar solicitudes propias.
    """
    rol = current_user.get("rol")
    user_obj = current_user.get("user")
    user_id = None
    if user_obj is not None:
        user_id = getattr(user_obj, "id_paciente", None) or getattr(user_obj, "id_administrador", None)

    # Obtener solicitud
    solicitud = (await db.execute(
        select(models.Solicitud).where(
            models.Solicitud.id_solicitud == id_solicitud,
            models.Solicitud.activo == 1
        )
    )).scalar_one_or_none()

    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if solicitud.estado_pago == "pagado_total":
        raise HTTPException(status_code=400, detail="La solicitud ya está pagada totalmente")

    # Verificar permisos para pacientes
    if rol == "paciente" and user_id and solicitud.id_paciente != user_id:
        raise HTTPException(status_code=403, detail="No puedes pagar solicitudes de otros pacientes")

    # Buscar factura asociada
    factura = (await db.execute(
        select(models.Factura).where(
            models.Factura.id_solicitud == id_solicitud,
            models.Factura.activo == 1
        )
    )).scalar_one_or_none()

    if not factura:
        raise HTTPException(status_code=404, detail="No existe una factura asociada a esta solicitud")

    # Calcular monto (por defecto, el total de la factura)
    monto_pago = float(monto) if monto is not None else float(factura.total)

    # Crear el pago
    new_pago_id = await get_next_int_id(db, models.Pago, "id_pago")
    nuevo_pago = models.Pago(
        id_pago=new_pago_id,
        id_factura=factura.id_factura,
        monto=monto_pago,
        metodo_pago=metodo_pago or "efectivo",
        referencia_pago=referencia or f"SOL-{id_solicitud}-{new_pago_id}",
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
    await db.refresh(nuevo_pago)

    return {
        "mensaje": "Pago registrado exitosamente. La solicitud ha sido marcada como pagado_total.",
        "id_pago": new_pago_id,
        "id_solicitud": id_solicitud,
        "id_factura": factura.id_factura,
        "monto": monto_pago,
    }


@router.post("/{id_pago}/confirmar", response_model=schemas.ConfirmarPagoResponse)
async def confirmar_pago(
    id_pago: int,
    referencia: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Confirma un pago manualmente y actualiza estados de factura y solicitud.
    
    **Roles permitidos:**
    - Paciente: Solo puede confirmar pagos de sus propias facturas
    - Administrador/Laboratorista/Recepcionista: Puede confirmar cualquier pago
    """
    user_rol = current_user.get("rol")
    if user_rol not in ["paciente", "administrador", "recepcionista"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para confirmar pagos")

    pago = await crud.pago_crud.get(db, id_pago)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    # Verificar que el usuario paciente solo confirme su propio pago
    if current_user.get("rol") == "paciente":
        factura_check = (await db.execute(
            select(models.Factura).where(models.Factura.id_factura == pago.id_factura)
        )).scalar_one_or_none()
        if not factura_check:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        paciente_id = current_user.get("id_usuario")
        if factura_check.id_paciente != paciente_id:
            raise HTTPException(status_code=403, detail="No puedes confirmar pagos de otros pacientes")

    # Actualizar estado del pago
    pago.estado_pago = 'completado'
    if referencia:
        pago.referencia_pago = referencia

    # Actualizar estado de la factura
    factura = (await db.execute(
        select(models.Factura).where(models.Factura.id_factura == pago.id_factura)
    )).scalar_one_or_none()

    if not factura:
        raise HTTPException(status_code=404, detail="Factura asociada no encontrada")

    # Calcular total pagado en esta factura
    stmt_pagos = select(models.Pago).where(
        models.Pago.activo == 1,
        models.Pago.id_factura == pago.id_factura,
        models.Pago.estado_pago == 'completado'
    )
    result = await db.execute(stmt_pagos)
    pagos_completados = result.scalars().all()
    total_pagado = sum(p.monto for p in pagos_completados)

    # Actualizar factura según el total pagado
    if total_pagado >= factura.total:
        factura.estado_factura = 'pagada_total'
    else:
        factura.estado_factura = 'pagada_parcial'

    # Actualizar Solicitud.estado_pago
    solicitud = (await db.execute(
        select(models.Solicitud).where(models.Solicitud.id_solicitud == factura.id_solicitud)
    )).scalar_one_or_none()
    if solicitud:
        if total_pagado >= factura.total:
            solicitud.estado_pago = 'pagado_total'
        else:
            solicitud.estado_pago = 'pagado_parcial'

    await db.commit()
    return {"mensaje": "Pago confirmado exitosamente. Estados actualizados."}


@router.post("/webhook", response_model=schemas.ConfirmarPagoResponse)
async def webhook_pago(
    payload: schemas.WebhookPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook que recibe notificación automática de la pasarela de pago
    cuando un pago es exitoso.
    
    Integración con QR Simple, Mercado Pago, Stripe, etc.
    """
    id_transaccion = payload.id_transaccion
    estado = payload.estado
    referencia_externa = payload.referencia
    monto = payload.monto

    if estado != "completado":
        return {"mensaje": "Pago no completado, ignorado"}

    # Buscar pago existente por id_transaccion_externa
    pago = (await db.execute(
        select(models.Pago).where(
            models.Pago.id_transaccion_externa == id_transaccion,
            models.Pago.activo == 1
        )
    )).scalar_one_or_none()

    if not pago:
        # Si no existe, buscar por referencia externa (ej: "INV000123-00025050")
        if referencia_externa:
            stmt = select(models.Pago).where(
                models.Pago.referencia_pago == referencia_externa,
                models.Pago.activo == 1
            )
            pago = (await db.execute(stmt)).scalar_one_or_none()

    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado. Verifique la referencia.")

    # Actualizar estado del pago
    pago.estado_pago = 'completado'
    pago.referencia_pago = referencia_externa or pago.referencia_pago
    pago.id_transaccion_externa = id_transaccion

    # Buscar factura
    factura = (await db.execute(
        select(models.Factura).where(models.Factura.id_factura == pago.id_factura)
    )).scalar_one_or_none()

    if factura:
        # Calcular total pagado
        stmt_pagos = select(models.Pago).where(
            models.Pago.activo == 1,
            models.Pago.id_factura == pago.id_factura,
            models.Pago.estado_pago == 'completado'
        )
        result = await db.execute(stmt_pagos)
        pagos_completados = result.scalars().all()
        total_pagado = sum(p.monto for p in pagos_completados)

        if total_pagado >= factura.total:
            factura.estado_factura = 'pagada_total'
        else:
            factura.estado_factura = 'pagada_parcial'

        # Actualizar solicitud
        solicitud = (await db.execute(
            select(models.Solicitud).where(models.Solicitud.id_solicitud == factura.id_solicitud)
        )).scalar_one_or_none()
        if solicitud:
            solicitud.estado_pago = 'pagado_total' if total_pagado >= factura.total else 'pagado_parcial'

    await db.commit()
    return {"mensaje": "Pago procesado exitosamente via webhook"}
