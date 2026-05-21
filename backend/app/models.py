from sqlalchemy import Column, String, Integer, Text, Date, DateTime, Enum, Float, ForeignKey, TIMESTAMP, func
from app.database import Base

class AreaLaboratorio(Base):
    __tablename__ = "areas_laboratorio"
    id_area = Column(String(20), primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Prueba(Base):
    __tablename__ = "pruebas"
    id_prueba = Column(Integer, primary_key=True)
    id_area = Column(String(20), ForeignKey("areas_laboratorio.id_area"), nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(255))
    valor_referencia = Column(String(100))
    unidad = Column(String(50))
    precio = Column(Float, default=0.0)
    tiempo_estimado_minutos = Column(Integer, default=30)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Paciente(Base):
    __tablename__ = "pacientes"
    id_paciente = Column(String(20), primary_key=True)
    nombre = Column(String(80), nullable=False)
    apellido_paterno = Column(String(80), nullable=False)
    apellido_materno = Column(String(80))
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(Enum('M','F','O'))
    telefono = Column(String(20))
    email = Column(String(100), unique=True)
    direccion = Column(Text)
    tipo_sangre = Column(String(10))
    alergias = Column(Text)
    password = Column(String(255))
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Medico(Base):
    __tablename__ = "medicos"
    id_medico = Column(String(20), primary_key=True)
    nombre = Column(String(80), nullable=False)
    apellido_paterno = Column(String(80), nullable=False)
    apellido_materno = Column(String(80))
    fecha_nacimiento = Column(Date, nullable=False)
    especialidad = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100), unique=True)
    password = Column(String(255))
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Laboratorista(Base):
    __tablename__ = "laboratoristas"
    id_laboratorista = Column(String(20), primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido_paterno = Column(String(80), nullable=False)
    apellido_materno = Column(String(80))
    fecha_nacimiento = Column(Date, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    telefono = Column(String(20))
    id_area = Column(String(20), ForeignKey("areas_laboratorio.id_area"))
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Administrador(Base):
    __tablename__ = "administradores"
    id_admin = Column("id_administrador", String(20), primary_key=True)
    nombre = Column(String(80), nullable=False)
    apellido_paterno = Column(String(80), nullable=False)
    apellido_materno = Column(String(80))
    fecha_nacimiento = Column(Date, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    telefono = Column(String(20))
    rol = Column("rol_administrador", Enum('super_admin', 'admin_general', 'admin_financiero', 'admin_lab', name='admin_roles'), nullable=False, default='admin_general')
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Solicitud(Base):
    __tablename__ = "solicitudes"
    id_solicitud = Column(Integer, primary_key=True)
    fecha_solicitud = Column(DateTime, server_default=func.now())
    fecha_toma_muestra = Column(DateTime, nullable=True)
    id_paciente = Column(String(20), ForeignKey("pacientes.id_paciente"), nullable=False)
    id_medico = Column(String(20), ForeignKey("medicos.id_medico"), nullable=True)
    id_laboratorista = Column(String(20), ForeignKey("laboratoristas.id_laboratorista"), nullable=True)
    estado = Column(Enum('pendiente','en_proceso','completado','entregado','cancelado'), default='pendiente')
    prioridad = Column(Enum('baja','media','alta'), default='media')
    observaciones = Column(Text)
    estado_pago = Column(Enum('no_pagado','pagado_parcial','pagado_total'), default='no_pagado')
    fecha_inicio_procesamiento = Column(DateTime, nullable=True)
    fecha_fin_procesamiento = Column(DateTime, nullable=True)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DetalleSolicitud(Base):
    __tablename__ = "detalle_solicitud"
    id_detalle = Column(Integer, primary_key=True)
    id_solicitud = Column(Integer, ForeignKey("solicitudes.id_solicitud"), nullable=False)
    id_prueba = Column(Integer, ForeignKey("pruebas.id_prueba"), nullable=False)
    cantidad = Column(Integer, default=1)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Resultado(Base):
    __tablename__ = "resultados"
    id_resultado = Column(Integer, primary_key=True)
    id_detalle = Column(Integer, ForeignKey("detalle_solicitud.id_detalle"), nullable=False)
    resultado = Column(String(100), nullable=False)
    observacion = Column(Text)
    validado_por = Column(String(20), ForeignKey("laboratoristas.id_laboratorista"), nullable=True)
    fecha_validacion = Column(DateTime, nullable=True)
    es_anormal = Column(Integer, default=0)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Reporte(Base):
    __tablename__ = "reportes"
    id_reporte = Column(Integer, primary_key=True)
    id_solicitud = Column(Integer, ForeignKey("solicitudes.id_solicitud"), unique=True, nullable=False)
    fecha_entrega = Column(Date, nullable=True)
    estado = Column(Enum('borrador','finalizado','entregado'), default='borrador')
    observaciones = Column(Text)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Factura(Base):
    __tablename__ = "facturas"
    id_factura = Column(Integer, primary_key=True)
    id_solicitud = Column(Integer, ForeignKey("solicitudes.id_solicitud"), nullable=True)
    id_paciente = Column(String(20), ForeignKey("pacientes.id_paciente"), nullable=False)
    fecha_emision = Column(DateTime, server_default=func.now())
    fecha_vencimiento = Column(Date, nullable=True)
    subtotal = Column(Float, nullable=False)
    impuesto = Column(Float, default=0.0)
    descuento = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    estado_factura = Column(Enum('emitida','pagada_parcial','pagada_total','anulada'), default='emitida')
    tipo_comprobante = Column(Enum('boleta','factura','ticket'), default='boleta')
    nro_comprobante = Column(String(50), unique=True)
    activo = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DetalleFactura(Base):
    __tablename__ = "detalle_factura"
    id_detalle_factura = Column(Integer, primary_key=True)
    id_factura = Column(Integer, ForeignKey("facturas.id_factura"), nullable=False)
    id_prueba = Column(Integer, ForeignKey("pruebas.id_prueba"), nullable=False)
    id_detalle_solicitud = Column(Integer, ForeignKey("detalle_solicitud.id_detalle"), nullable=True)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False)
    descuento_item = Column(Float, default=0.0)
    total_item = Column(Float, nullable=False)
    activo = Column(Integer, default=1)

class Pago(Base):
    __tablename__ = "pagos"
    id_pago = Column(Integer, primary_key=True)
    id_factura = Column(Integer, ForeignKey("facturas.id_factura"), nullable=False)
    monto = Column(Float, nullable=False)
    fecha_pago = Column(DateTime, server_default=func.now())
    metodo_pago = Column(String(50), nullable=False)
    referencia_pago = Column(String(100))
    estado_pago = Column(Enum('pendiente','completado','fallido','reembolsado'), default='completado')
    activo = Column(Integer, default=1)

class AuditoriaLog(Base):
    __tablename__ = "auditoria_logs"
    id_auditoria = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(String(50), nullable=True, index=True)
    accion = Column(String(100), nullable=False)
    detalles = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)