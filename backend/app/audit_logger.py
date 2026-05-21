from sqlalchemy.ext.asyncio import AsyncSession
from app import models

async def log_audit(db: AsyncSession, id_usuario: str, accion: str, detalles: str = None):
    """
    Registra una acción en la tabla de auditoría del sistema.
    """
    audit_entry = models.AuditoriaLog(
        id_usuario=id_usuario,
        accion=accion,
        detalles=detalles
    )
    db.add(audit_entry)
    await db.commit()
    await db.refresh(audit_entry)
    return audit_entry
