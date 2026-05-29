from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

# ---------- Áreas ----------
class AreaBase(BaseModel):
    id_area: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class AreaOut(AreaBase):
    activo: int
    created_at: datetime
    updated_at: datetime

# ---------- Pruebas ----------
class PruebaBase(BaseModel):
    id_prueba: Optional[int] = None
    id_area: str
    nombre: str
    descripcion: Optional[str] = None
    valor_referencia: Optional[str] = None
    unidad: Optional[str] = None
    precio: float = 0.0
    tiempo_estimado_minutos: int = 30

class PruebaCreate(PruebaBase):
    pass

class PruebaUpdate(BaseModel):
    id_area: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    valor_referencia: Optional[str] = None
    unidad: Optional[str] = None
    precio: Optional[float] = None
    tiempo_estimado_minutos: Optional[int] = None

class PruebaOut(PruebaBase):
    activo: int
    created_at: datetime
    updated_at: datetime

# ---------- Pacientes ----------
class PacienteBase(BaseModel):
    id_paciente: Optional[str] = None
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: date
    genero: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    tipo_sangre: Optional[str] = None
    alergias: Optional[str] = None
    tipo_afiliacion: Optional[str] = "Privado"
    numero_afiliado_sus: Optional[str] = None
    entidad_aseguradora: Optional[str] = None

class PacienteCreate(PacienteBase):
    password: str

class PacienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    direccion: Optional[str] = None
    tipo_sangre: Optional[str] = None
    alergias: Optional[str] = None
    password: Optional[str] = None
    tipo_afiliacion: Optional[str] = None
    numero_afiliado_sus: Optional[str] = None
    entidad_aseguradora: Optional[str] = None

class PacienteOut(PacienteBase):
    activo: int
    created_at: datetime
    updated_at: datetime

# ---------- Médicos ----------
class MedicoBase(BaseModel):
    id_medico: Optional[str] = None
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: date
    especialidad: Optional[str] = None
    telefono: Optional[str] = None
    email: EmailStr

class MedicoCreate(MedicoBase):
    password: str

class MedicoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    especialidad: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class MedicoOut(MedicoBase):
    activo: int
    created_at: datetime
    updated_at: datetime

# ---------- Laboratoristas ----------
class LaboratoristaBase(BaseModel):
    id_laboratorista: Optional[str] = None
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: date
    email: EmailStr
    telefono: Optional[str] = None
    id_area: Optional[str] = None

class LaboratoristaCreate(LaboratoristaBase):
    password: str

class LaboratoristaUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    id_area: Optional[str] = None
    password: Optional[str] = None

class LaboratoristaOut(LaboratoristaBase):
    activo: int
    created_at: datetime
    updated_at: datetime

# ---------- Detalle de Solicitud ----------
class DetalleSolicitudBase(BaseModel):
    id_detalle: Optional[int] = None
    id_prueba: int
    cantidad: int = 1

class DetalleSolicitudCreate(DetalleSolicitudBase):
    pass

class DetalleSolicitudUpdate(BaseModel):
    cantidad: Optional[int] = None

class DetalleSolicitudOut(DetalleSolicitudBase):
    created_at: datetime
    activo: int

# ---------- Solicitudes ----------
class SolicitudBase(BaseModel):
    id_solicitud: Optional[int] = None
    fecha_solicitud: Optional[datetime] = None
    fecha_toma_muestra: Optional[datetime] = None
    id_paciente: str
    id_medico: Optional[str] = None
    id_laboratorista: Optional[str] = None
    estado: Optional[str] = "pendiente"
    prioridad: Optional[str] = "media"
    observaciones: Optional[str] = None
    estado_pago: Optional[str] = "no_pagado"
    fecha_inicio_procesamiento: Optional[datetime] = None
    fecha_fin_procesamiento: Optional[datetime] = None

class SolicitudCreate(BaseModel):
    id_paciente: str
    id_medico: Optional[str] = None
    prioridad: Optional[str] = "media"
    observaciones: Optional[str] = None
    detalles: List[DetalleSolicitudCreate]

class SolicitudUpdate(BaseModel):
    id_paciente: Optional[str] = None
    id_medico: Optional[str] = None
    fecha_toma_muestra: Optional[datetime] = None
    id_laboratorista: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    observaciones: Optional[str] = None
    estado_pago: Optional[str] = None
    fecha_inicio_procesamiento: Optional[datetime] = None
    fecha_fin_procesamiento: Optional[datetime] = None
    detalles: Optional[List[DetalleSolicitudCreate]] = None

class SolicitudOut(SolicitudBase):
    activo: int
    created_at: datetime
    updated_at: datetime
    detalles: List[DetalleSolicitudOut] = []
    paciente_nombre: Optional[str] = None
    paciente_nombre_nombre: Optional[str] = None
    paciente_apellido_paterno: Optional[str] = None
    paciente_apellido_materno: Optional[str] = None

# ---------- Resultados ----------
class ResultadoBase(BaseModel):
    id_resultado: Optional[int] = None
    id_detalle: int
    resultado: str
    observacion: Optional[str] = None
    validado_por: Optional[str] = None
    fecha_validacion: Optional[datetime] = None
    estado: Optional[str] = 'pendiente'
    es_anormal: int = 0

class ResultadoCreate(ResultadoBase):
    pass

class ResultadoUpdate(BaseModel):
    resultado: Optional[str] = None
    observacion: Optional[str] = None
    validado_por: Optional[str] = None
    fecha_validacion: Optional[datetime] = None
    es_anormal: Optional[int] = None
    estado: Optional[str] = None

class ResultadoOut(ResultadoBase):
    activo: int
    created_at: datetime
    estado: str
    id_prueba: Optional[int] = None
    prueba_nombre: Optional[str] = None
    id_solicitud: Optional[int] = None
    valor_referencia: Optional[str] = None
    id_paciente: Optional[str] = None
    paciente_nombre: Optional[str] = None
    paciente_apellido_paterno: Optional[str] = None
    paciente_apellido_materno: Optional[str] = None
    validado_por: Optional[str] = None
    validado_nombre: Optional[str] = None
    validado_apellido_paterno: Optional[str] = None
    validado_apellido_materno: Optional[str] = None

# ---------- Reportes ----------
class ReporteBase(BaseModel):
    id_reporte: Optional[int] = None
    id_solicitud: int
    fecha_entrega: Optional[date] = None
    estado: Optional[str] = "borrador"
    observaciones: Optional[str] = None

class ReporteCreate(ReporteBase):
    pass

class ReporteUpdate(BaseModel):
    fecha_entrega: Optional[date] = None
    estado: Optional[str] = None
    observaciones: Optional[str] = None

class ReporteOut(ReporteBase):
    activo: int
    created_at: datetime
    updated_at: datetime
    generado_nombre: Optional[str] = None
    generado_apellido_paterno: Optional[str] = None
    generado_apellido_materno: Optional[str] = None

# ---------- Detalle Factura ----------
class DetalleFacturaBase(BaseModel):
    id_detalle_factura: Optional[int] = None
    id_prueba: int
    id_detalle_solicitud: Optional[int] = None
    cantidad: int = 1
    precio_unitario: float
    descuento_item: float = 0.0
    total_item: float

class DetalleFacturaCreate(DetalleFacturaBase):
    pass

class DetalleFacturaUpdate(BaseModel):
    cantidad: Optional[int] = None
    precio_unitario: Optional[float] = None
    descuento_item: Optional[float] = None
    total_item: Optional[float] = None

class DetalleFacturaOut(DetalleFacturaBase):
    pass

# ---------- Facturas ----------
class FacturaBase(BaseModel):
    id_factura: Optional[int] = None
    id_solicitud: Optional[int] = None
    id_paciente: str
    fecha_emision: Optional[datetime] = None
    fecha_vencimiento: Optional[date] = None
    subtotal: float
    impuesto: float = 0.0
    descuento: float = 0.0
    total: float
    estado_factura: Optional[str] = "emitida"
    tipo_comprobante: Optional[str] = "boleta"
    nro_comprobante: str
    tipo_pago_fuente: Optional[str] = "paciente"
    monto_paciente: float = 0.0
    monto_sus: float = 0.0
    estado_reembolso_sus: Optional[str] = "no_aplica"
    numero_reclamacion_sus: Optional[str] = None

class FacturaCreate(FacturaBase):
    detalles: List[DetalleFacturaCreate]

class FacturaUpdate(BaseModel):
    fecha_vencimiento: Optional[date] = None
    estado_factura: Optional[str] = None
    nro_comprobante: Optional[str] = None
    tipo_pago_fuente: Optional[str] = None
    monto_paciente: Optional[float] = None
    monto_sus: Optional[float] = None
    estado_reembolso_sus: Optional[str] = None
    numero_reclamacion_sus: Optional[str] = None

class FacturaOut(FacturaBase):
    activo: int
    created_at: datetime
    updated_at: datetime
    detalles: List[DetalleFacturaOut] = []

# ---------- Pagos ----------
class PagoBase(BaseModel):
    id_pago: Optional[int] = None
    id_factura: int
    monto: float
    fecha_pago: Optional[datetime] = None
    metodo_pago: str
    referencia_pago: Optional[str] = None
    estado_pago: Optional[str] = "completado"

class PagoCreate(PagoBase):
    pass

class PagoUpdate(BaseModel):
    monto: Optional[float] = None
    metodo_pago: Optional[str] = None
    referencia_pago: Optional[str] = None
    estado_pago: Optional[str] = None

class PagoOut(PagoBase):
    activo: int

# ---------- Administradores ----------
class AdministradorBase(BaseModel):
    id_administrador: Optional[int | str] = None
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: date
    email: EmailStr
    telefono: Optional[str] = None
    rol_administrador: Optional[str] = "admin_general"

class AdministradorCreate(AdministradorBase):
    password: str

class AdministradorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    rol_administrador: Optional[str] = None
    password: Optional[str] = None

class AdministradorOut(AdministradorBase):
    activo: int
    created_at: datetime
    updated_at: datetime

# ---------- Autenticación ----------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id_usuario: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None

# ---------- Diagnósticos Preventivos ----------
class DiagnosticoPreventivoBase(BaseModel):
    id_diagnostico: Optional[int] = None
    id_solicitud: int
    id_paciente: str
    id_medico: str
    diagnostico_actual: Optional[str] = None
    confianza_actual: Optional[float] = 0.0
    predicciones: Optional[dict] = None
    factores_riesgo: Optional[dict] = None
    recomendaciones: Optional[str] = None
    modelo_version: Optional[str] = None

class DiagnosticoPreventivoCreate(BaseModel):
    id_solicitud: int
    id_paciente: str
    id_medico: str
    diagnostico_actual: Optional[str] = None
    confianza_actual: Optional[float] = 0.0

class DiagnosticoPreventivoUpdate(BaseModel):
    diagnostico_actual: Optional[str] = None
    confianza_actual: Optional[float] = None
    predicciones: Optional[dict] = None
    factores_riesgo: Optional[dict] = None
    recomendaciones: Optional[str] = None

class DiagnosticoPreventivoOut(DiagnosticoPreventivoBase):
    activo: int
    fecha_generacion: datetime
    created_at: datetime
    updated_at: datetime