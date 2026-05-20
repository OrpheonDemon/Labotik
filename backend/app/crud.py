from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from typing import Type, TypeVar, Generic, Optional, List, Any
from app.models import *
from app.schemas import *
from app.id_generator import get_next_int_id, generate_persona_id, generate_area_id
from app.utils import hash_password, verify_password

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], pk_name: str = None):
        self.model = model
        self.pk_name = pk_name or model.__table__.primary_key.columns[0].name

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).where(
            getattr(self.model, self.pk_name) == id,
            self.model.activo == 1
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self.model).where(self.model.activo == 1).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        data = obj_in.dict(exclude_unset=True)
        # Generar ID según el modelo
        if self.model == Prueba:
            data['id_prueba'] = await get_next_int_id(db, Prueba, 'id_prueba')
        elif self.model == Solicitud:
            data['id_solicitud'] = await get_next_int_id(db, Solicitud, 'id_solicitud')
        elif self.model == DetalleSolicitud:
            data['id_detalle'] = await get_next_int_id(db, DetalleSolicitud, 'id_detalle')
        elif self.model == Resultado:
            data['id_resultado'] = await get_next_int_id(db, Resultado, 'id_resultado')
        elif self.model == Reporte:
            data['id_reporte'] = await get_next_int_id(db, Reporte, 'id_reporte')
        elif self.model == Factura:
            data['id_factura'] = await get_next_int_id(db, Factura, 'id_factura')
        elif self.model == DetalleFactura:
            data['id_detalle_factura'] = await get_next_int_id(db, DetalleFactura, 'id_detalle_factura')
        elif self.model == Pago:
            data['id_pago'] = await get_next_int_id(db, Pago, 'id_pago')
        elif self.model == Administrador:
            next_id = await get_next_int_id(db, Administrador, 'id_administrador')
            data['id_administrador'] = next_id
        elif self.model == AreaLaboratorio:
            nombre = data.get('nombre', '')
            if nombre:
                data['id_area'] = await generate_area_id(db, AreaLaboratorio, nombre)

        # Validación de email único y hashing de password para entidades de usuario
        if self.model in [Paciente, Medico, Laboratorista, Administrador]:
            if 'email' in data:
                if await check_email_exists(db, data['email']):
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=400, 
                        detail="El correo ya está registrado en el sistema (Administrador, Laboratorista, Médico o Paciente)"
                    )
            
            if 'password' in data:
                data['password'] = hash_password(data.pop('password'))

            if self.model == Paciente:
                data['id_paciente'] = await generate_persona_id(
                    db, Paciente, data['nombre'], data['apellido_paterno'],
                    data.get('apellido_materno', ''), data['fecha_nacimiento'], data.get('genero')
                )
            elif self.model == Medico:
                data['id_medico'] = await generate_persona_id(
                    db, Medico, data['nombre'], data['apellido_paterno'],
                    data.get('apellido_materno', ''), data['fecha_nacimiento'], data.get('genero', 'M')
                )
            elif self.model == Laboratorista:
                data['id_laboratorista'] = await generate_persona_id(
                    db, Laboratorista, data['nombre'], data['apellido_paterno'],
                    data.get('apellido_materno', ''), data['fecha_nacimiento'], data.get('genero', 'M')
                )
        # Para áreas, el ID lo envía el usuario (VARCHAR)
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, id: Any, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        stmt = select(self.model).where(
            getattr(self.model, self.pk_name) == id,
            self.model.activo == 1
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None
        update_data = obj_in.dict(exclude_unset=True)
        if 'password' in update_data and update_data['password']:
            update_data['password'] = hash_password(update_data['password'])
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def soft_delete(self, db: AsyncSession, id: Any) -> bool:
        stmt = update(self.model).where(getattr(self.model, self.pk_name) == id).values(activo=0)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

# CRUD específico con búsqueda por nombres
class CRUDPaciente(CRUDBase[Paciente, PacienteCreate, PacienteUpdate]):
    async def search_by_names(self, db: AsyncSession, apellido_paterno: str = "", apellido_materno: str = "", nombre: str = ""):
        conditions = []
        if apellido_paterno:
            conditions.append(Paciente.apellido_paterno.like(f"%{apellido_paterno}%"))
        if apellido_materno:
            conditions.append(Paciente.apellido_materno.like(f"%{apellido_materno}%"))
        if nombre:
            conditions.append(Paciente.nombre.like(f"%{nombre}%"))
        if not conditions:
            return []
        stmt = select(Paciente).where(Paciente.activo == 1).where(or_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

class CRUDMedico(CRUDBase[Medico, MedicoCreate, MedicoUpdate]):
    async def search_by_names(self, db: AsyncSession, apellido_paterno: str = "", apellido_materno: str = "", nombre: str = ""):
        conditions = []
        if apellido_paterno:
            conditions.append(Medico.apellido_paterno.like(f"%{apellido_paterno}%"))
        if apellido_materno:
            conditions.append(Medico.apellido_materno.like(f"%{apellido_materno}%"))
        if nombre:
            conditions.append(Medico.nombre.like(f"%{nombre}%"))
        if not conditions:
            return []
        stmt = select(Medico).where(Medico.activo == 1).where(or_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

class CRUDLaboratorista(CRUDBase[Laboratorista, LaboratoristaCreate, LaboratoristaUpdate]):
    async def search_by_names(self, db: AsyncSession, apellido_paterno: str = "", apellido_materno: str = "", nombre: str = ""):
        conditions = []
        if apellido_paterno:
            conditions.append(Laboratorista.apellido_paterno.like(f"%{apellido_paterno}%"))
        if apellido_materno:
            conditions.append(Laboratorista.apellido_materno.like(f"%{apellido_materno}%"))
        if nombre:
            conditions.append(Laboratorista.nombre.like(f"%{nombre}%"))
        if not conditions:
            return []
        stmt = select(Laboratorista).where(Laboratorista.activo == 1).where(or_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    async def search_by_area(self, db: AsyncSession, id_area: str):
        stmt = select(Laboratorista).where(
            Laboratorista.activo == 1,
            Laboratorista.id_area == id_area
        )
        result = await db.execute(stmt)
        return result.scalars().all()

class CRUDPrueba(CRUDBase[Prueba, PruebaCreate, PruebaUpdate]):
    async def search_by_area(self, db: AsyncSession, id_area: str):
        stmt = select(Prueba).where(
            Prueba.activo == 1,
            Prueba.id_area == id_area
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def search_by_name(self, db: AsyncSession, nombre: str):
        stmt = select(Prueba).where(
            Prueba.activo == 1,
            Prueba.nombre.like(f"%{nombre}%")
        )
        result = await db.execute(stmt)
        return result.scalars().all()

class CRUDAdministrador(CRUDBase[Administrador, AdministradorCreate, AdministradorUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str):
        stmt = select(Administrador).where(
            Administrador.email == email,
            Administrador.activo == 1
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_names(self, db: AsyncSession, apellido_paterno: str = "", apellido_materno: str = "", nombre: str = ""):
        conditions = []
        if apellido_paterno:
            conditions.append(Administrador.apellido_paterno.like(f"%{apellido_paterno}%"))
        if apellido_materno:
            conditions.append(Administrador.apellido_materno.like(f"%{apellido_materno}%"))
        if nombre:
            conditions.append(Administrador.nombre.like(f"%{nombre}%"))
        if not conditions:
            return []
        stmt = select(Administrador).where(Administrador.activo == 1).where(or_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

# Instancias
area_crud = CRUDBase(AreaLaboratorio, "id_area")
prueba_crud = CRUDPrueba(Prueba, "id_prueba")
paciente_crud = CRUDPaciente(Paciente, "id_paciente")
medico_crud = CRUDMedico(Medico, "id_medico")
laboratorista_crud = CRUDLaboratorista(Laboratorista, "id_laboratorista")
administrador_crud = CRUDAdministrador(Administrador, "id_administrador")
solicitud_crud = CRUDBase(Solicitud, "id_solicitud")
detalle_solicitud_crud = CRUDBase(DetalleSolicitud, "id_detalle")
resultado_crud = CRUDBase(Resultado, "id_resultado")
reporte_crud = CRUDBase(Reporte, "id_reporte")
factura_crud = CRUDBase(Factura, "id_factura")
detalle_factura_crud = CRUDBase(DetalleFactura, "id_detalle_factura")
pago_crud = CRUDBase(Pago, "id_pago")

# Función de Autenticación
async def authenticate_user(db: AsyncSession, email: str, password: str):
    # 1. Buscar en Laboratoristas (Suelen ser los de acceso más frecuente)
    stmt = select(Laboratorista).where(Laboratorista.email == email, Laboratorista.activo == 1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password):
        return {"user": user, "rol": "laboratorista"}

    # 2. Buscar en Médicos
    stmt = select(Medico).where(Medico.email == email, Medico.activo == 1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password):
        return {"user": user, "rol": "medico"}

    # 3. Buscar en Pacientes
    stmt = select(Paciente).where(Paciente.email == email, Paciente.activo == 1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password):
        return {"user": user, "rol": "paciente"}

    # 4. Buscar en Administradores
    stmt = select(Administrador).where(Administrador.email == email, Administrador.activo == 1)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.password):
        return {"user": user, "rol": "administrador"}

    return None

# Función para verificar si un email ya existe en cualquier tabla de usuarios
async def check_email_exists(db: AsyncSession, email: str):
    if not email:
        return False
        
    # Buscar en Laboratoristas
    stmt = select(Laboratorista).where(Laboratorista.email == email, Laboratorista.activo == 1)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return True
    
    # Buscar en Médicos
    stmt = select(Medico).where(Medico.email == email, Medico.activo == 1)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return True
        
    # Buscar en Pacientes
    stmt = select(Paciente).where(Paciente.email == email, Paciente.activo == 1)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return True
        
    # Buscar en Administradores
    stmt = select(Administrador).where(Administrador.email == email, Administrador.activo == 1)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        return True
        
    return False
