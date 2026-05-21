from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app import schemas, models
from app.database import get_db

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])

@router.get("/", response_model=List[schemas.AuditoriaLogOut])
async def list_auditoria(skip: int = 0, limit: int = 200, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.AuditoriaLog).order_by(models.AuditoriaLog.created_at.desc()).offset(skip).limit(limit))
    return result.scalars().all()
