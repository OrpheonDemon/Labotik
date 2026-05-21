from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app import schemas, crud, models
from app.database import get_db
from app.id_generator import get_next_int_id

router = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])

@router.get("/", response_model=list[schemas.SolicitudOut])
async def list_solicitudes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Mostrar todas las solicitudes activas (no filtrar por estado)
    from sqlalchemy import select as sa_select
    stmt = sa_select(models.Solicitud).where(models.Solicitud.activo == 1).offset(skip).limit(limit)
    result = await db.execute(stmt)
    solicitudes = result.scalars().all()
    for solicitud in solicitudes:
        stmt_d = sa_select(models.DetalleSolicitud).where(
            models.DetalleSolicitud.id_solicitud == solicitud.id_solicitud,
            models.DetalleSolicitud.activo == 1
        )
        res_d = await db.execute(stmt_d)
        solicitud.detalles = res_d.scalars().all()
        # Añadir nombre completo del paciente para facilitar el frontend
        stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == solicitud.id_paciente, models.Paciente.activo == 1)
        res_p = await db.execute(stmt_p)
        pac = res_p.scalar_one_or_none()
        if pac:
            solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
            solicitud.paciente_nombre_nombre = pac.nombre
            solicitud.paciente_apellido_paterno = pac.apellido_paterno
            solicitud.paciente_apellido_materno = pac.apellido_materno
    return solicitudes

@router.get("/search", response_model=list[schemas.SolicitudOut])
async def search_solicitudes(
    id_solicitud: int = Query(None),
    id_paciente: str = Query(None),
    nombre: str = Query(None),
    apellido_paterno: str = Query(None),
    apellido_materno: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select as sa_select, or_, and_

    # Búsqueda por ID de solicitud
    if id_solicitud:
        stmt = sa_select(models.Solicitud).where(
            models.Solicitud.id_solicitud == id_solicitud,
            models.Solicitud.activo == 1
        )
        result = await db.execute(stmt)
        solicitud = result.scalar_one_or_none()
        if solicitud:
            stmt_d = sa_select(models.DetalleSolicitud).where(
                models.DetalleSolicitud.id_solicitud == id_solicitud,
                models.DetalleSolicitud.activo == 1
            )
            res_d = await db.execute(stmt_d)
            solicitud.detalles = res_d.scalars().all()
            # Añadir nombre paciente
            stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == solicitud.id_paciente, models.Paciente.activo == 1)
            res_p = await db.execute(stmt_p)
            pac = res_p.scalar_one_or_none()
            if pac:
                solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
                solicitud.paciente_nombre_nombre = pac.nombre
                solicitud.paciente_apellido_paterno = pac.apellido_paterno
                solicitud.paciente_apellido_materno = pac.apellido_materno
            return [solicitud]
        return []

    # Búsqueda por id_paciente directo o por nombre/apellido del paciente
    conditions = [models.Solicitud.activo == 1]

    if id_paciente and id_paciente.strip():
        conditions.append(models.Solicitud.id_paciente.ilike(f"%{id_paciente}%"))
        stmt = sa_select(models.Solicitud).where(*conditions)
        result = await db.execute(stmt)
        solicitudes = result.scalars().all()
    elif nombre or apellido_paterno or apellido_materno:
        # JOIN con Paciente para buscar por nombre
        pac_conditions = []
        if nombre and nombre.strip():
            pac_conditions.append(models.Paciente.nombre.ilike(f"%{nombre}%"))
        if apellido_paterno and apellido_paterno.strip():
            pac_conditions.append(models.Paciente.apellido_paterno.ilike(f"%{apellido_paterno}%"))
        if apellido_materno and apellido_materno.strip():
            pac_conditions.append(models.Paciente.apellido_materno.ilike(f"%{apellido_materno}%"))

        stmt = (
            sa_select(models.Solicitud)
            .join(models.Paciente, models.Solicitud.id_paciente == models.Paciente.id_paciente)
            .where(*conditions, *pac_conditions)
        )
        result = await db.execute(stmt)
        solicitudes = result.scalars().all()
    else:
        return []

    for sol in solicitudes:
        stmt_d = sa_select(models.DetalleSolicitud).where(
            models.DetalleSolicitud.id_solicitud == sol.id_solicitud,
            models.DetalleSolicitud.activo == 1
        )
        res_d = await db.execute(stmt_d)
        sol.detalles = res_d.scalars().all()
        # Añadir nombre paciente
        stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == sol.id_paciente, models.Paciente.activo == 1)
        res_p = await db.execute(stmt_p)
        pac = res_p.scalar_one_or_none()
        if pac:
            sol.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
            sol.paciente_nombre_nombre = pac.nombre
            sol.paciente_apellido_paterno = pac.apellido_paterno
            sol.paciente_apellido_materno = pac.apellido_materno
    return solicitudes


@router.get("/paid", response_model=list[schemas.SolicitudOut])
async def list_paid_solicitudes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Devuelve solicitudes cuyo estado de pago es 'pagado_total' (listas para generar resultados)."""
    from sqlalchemy import select as sa_select
    stmt = sa_select(models.Solicitud).where(models.Solicitud.activo == 1, models.Solicitud.estado_pago == 'pagado_total').offset(skip).limit(limit)
    result = await db.execute(stmt)
    solicitudes = result.scalars().all()
    for solicitud in solicitudes:
        stmt_d = sa_select(models.DetalleSolicitud).where(
            models.DetalleSolicitud.id_solicitud == solicitud.id_solicitud,
            models.DetalleSolicitud.activo == 1
        )
        res_d = await db.execute(stmt_d)
        solicitud.detalles = res_d.scalars().all()
        # Añadir nombre paciente
        stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == solicitud.id_paciente, models.Paciente.activo == 1)
        res_p = await db.execute(stmt_p)
        pac = res_p.scalar_one_or_none()
        if pac:
            solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
            solicitud.paciente_nombre_nombre = pac.nombre
            solicitud.paciente_apellido_paterno = pac.apellido_paterno
            solicitud.paciente_apellido_materno = pac.apellido_materno
    return solicitudes

@router.get("/{id_solicitud}", response_model=schemas.SolicitudOut)
async def get_solicitud(id_solicitud: int, db: AsyncSession = Depends(get_db)):
    solicitud = await crud.solicitud_crud.get(db, id_solicitud)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    # Cargar detalles
    stmt = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_solicitud == id_solicitud, models.DetalleSolicitud.activo == 1)
    result = await db.execute(stmt)
    detalles = result.scalars().all()
    solicitud.detalles = detalles
    # Añadir nombre paciente
    from sqlalchemy import select as sa_select
    stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == solicitud.id_paciente, models.Paciente.activo == 1)
    res_p = await db.execute(stmt_p)
    pac = res_p.scalar_one_or_none()
    if pac:
        solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
        solicitud.paciente_nombre_nombre = pac.nombre
        solicitud.paciente_apellido_paterno = pac.apellido_paterno
        solicitud.paciente_apellido_materno = pac.apellido_materno
    return solicitud

@router.post("/", response_model=schemas.SolicitudOut, status_code=201)
async def create_solicitud(solicitud_in: schemas.SolicitudCreate, db: AsyncSession = Depends(get_db)):
    # Generar ID de solicitud
    new_id = await get_next_int_id(db, models.Solicitud, 'id_solicitud')
    # Crear solicitud
    solicitud_data = solicitud_in.dict(exclude={'detalles'})
    solicitud_data['id_solicitud'] = new_id
    solicitud_data['estado'] = 'pendiente'
    nueva_solicitud = models.Solicitud(**solicitud_data)
    db.add(nueva_solicitud)
    await db.flush()
    # Crear detalles
    for detalle_in in solicitud_in.detalles:
        detalle_id = await get_next_int_id(db, models.DetalleSolicitud, 'id_detalle')
        detalle = models.DetalleSolicitud(
            id_detalle=detalle_id,
            id_solicitud=new_id,
            id_prueba=detalle_in.id_prueba,
            cantidad=detalle_in.cantidad
        )
        db.add(detalle)
    await db.commit()
    await db.refresh(nueva_solicitud)
    
    # Cargar detalles
    stmt = select(models.DetalleSolicitud).where(models.DetalleSolicitud.id_solicitud == new_id, models.DetalleSolicitud.activo == 1)
    result = await db.execute(stmt)
    nueva_solicitud.detalles = result.scalars().all()
    # Añadir nombre paciente
    from sqlalchemy import select as sa_select
    stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == nueva_solicitud.id_paciente, models.Paciente.activo == 1)
    res_p = await db.execute(stmt_p)
    pac = res_p.scalar_one_or_none()
    if pac:
        nueva_solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
        nueva_solicitud.paciente_nombre_nombre = pac.nombre
        nueva_solicitud.paciente_apellido_paterno = pac.apellido_paterno
        nueva_solicitud.paciente_apellido_materno = pac.apellido_materno
    return nueva_solicitud

@router.put("/{id_solicitud}", response_model=schemas.SolicitudOut)
async def update_solicitud(id_solicitud: int, solicitud_in: schemas.SolicitudUpdate, db: AsyncSession = Depends(get_db)):
    # 1. Obtener la solicitud existente
    solicitud = await crud.solicitud_crud.get(db, id_solicitud)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # 2. Separar detalles si vienen en el update
    solicitud_data = solicitud_in.dict(exclude_unset=True)
    detalles_in = solicitud_data.pop('detalles', None)
    
    # 3. Actualizar campos de la solicitud principal
    for key, value in solicitud_data.items():
        setattr(solicitud, key, value)
    
    await db.flush()
    
    # 4. Si se especificaron nuevos detalles, los actualizamos
    if detalles_in is not None:
        # Borrado lógico de todos los detalles existentes
        stmt_del = update(models.DetalleSolicitud).where(
            models.DetalleSolicitud.id_solicitud == id_solicitud
        ).values(activo=0)
        await db.execute(stmt_del)
        
        # Crear los nuevos detalles
        for detalle_in in detalles_in:
            detalle_id = await get_next_int_id(db, models.DetalleSolicitud, 'id_detalle')
            detalle = models.DetalleSolicitud(
                id_detalle=detalle_id,
                id_solicitud=id_solicitud,
                id_prueba=detalle_in['id_prueba'],
                cantidad=detalle_in.get('cantidad', 1)
            )
            db.add(detalle)
            
    await db.commit()
    await db.refresh(solicitud)
    
    # Cargar detalles activos
    stmt = select(models.DetalleSolicitud).where(
        models.DetalleSolicitud.id_solicitud == id_solicitud,
        models.DetalleSolicitud.activo == 1
    )
    result = await db.execute(stmt)
    solicitud.detalles = result.scalars().all()
    # Añadir nombre paciente
    from sqlalchemy import select as sa_select
    stmt_p = sa_select(models.Paciente).where(models.Paciente.id_paciente == solicitud.id_paciente, models.Paciente.activo == 1)
    res_p = await db.execute(stmt_p)
    pac = res_p.scalar_one_or_none()
    if pac:
        solicitud.paciente_nombre = f"{pac.nombre} {pac.apellido_paterno} {pac.apellido_materno or ''}".strip()
        solicitud.paciente_nombre_nombre = pac.nombre
        solicitud.paciente_apellido_paterno = pac.apellido_paterno
        solicitud.paciente_apellido_materno = pac.apellido_materno
    
    return solicitud

@router.delete("/{id_solicitud}")
async def delete_solicitud(id_solicitud: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud.solicitud_crud.soft_delete(db, id_solicitud)
    if not deleted:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"message": "Solicitud desactivada (borrado lógico)"}