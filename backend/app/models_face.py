from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, Float, ForeignKey, TIMESTAMP, func, JSON, Boolean
from app.database import Base

class FaceEmbedding(Base):
    """
    Modelo para almacenar embeddings faciales de usuarios.
    Permite autenticación biométrica sin modificar las tablas existentes.
    """
    __tablename__ = "face_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia al usuario (puede ser de cualquier tabla)
    id_usuario = Column(String(50), nullable=False, index=True)
    
    # Tabla de origen del usuario
    tabla_usuario = Column(
        Enum('pacientes', 'medicos', 'laboratoristas', 'administradores'),
        nullable=False
    )
    
    # Embedding facial (vector de 128 dimensiones en formato JSON)
    # Se guarda como JSON array para compatibilidad
    embedding_data = Column(JSON, nullable=False)
    
    # Versión del modelo utilizado para generar el embedding
    modelo_version = Column(String(20), default="face_recognition_v1")
    
    # Metadatos de calidad
    calidad_promedio = Column(Float, default=0.0)  # 0.0 a 1.0
    
    # Estado
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, server_default=func.now())
    actualizado_en = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Intentos fallidos de autenticación (para seguridad)
    intentos_fallidos = Column(Integer, default=0)
    ultimo_intento_fallido = Column(DateTime, nullable=True)
    
    # Notas adicionales
    notas = Column(Text, nullable=True)


class FaceAuthLog(Base):
    """
    Modelo para registrar todos los intentos de autenticación facial.
    Importante para auditoría y seguridad.
    """
    __tablename__ = "face_auth_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia al usuario (puede ser NULL si el intento falló)
    id_usuario = Column(String(50), nullable=True, index=True)
    
    # Tabla de origen del usuario
    tabla_usuario = Column(
        Enum('pacientes', 'medicos', 'laboratoristas', 'administradores'),
        nullable=True
    )
    
    # Resultado del intento
    exito = Column(Boolean, nullable=False)
    
    # Puntuación de similitud (0.0 a 1.0)
    score_similitud = Column(Float, nullable=True)
    
    # Umbral utilizado
    umbral_utilizado = Column(Float, default=0.6)
    
    # Dirección IP y user agent
    ip_address = Column(String(45), nullable=True)  # IPv6 puede ser más largo
    user_agent = Column(Text, nullable=True)
    
    # Timestamp
    creado_en = Column(DateTime, server_default=func.now())
    
    # Notas de error o información adicional
    notas = Column(Text, nullable=True)