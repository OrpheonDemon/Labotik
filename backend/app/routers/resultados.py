from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db
from app.dependencies import require_laboratorista, get_current_active_user

router = APIRouter(prefix="/resultados", tags=["Resultados"])

@router.get("/", response_model=list[schemas.ResultadoOut])
async def list_resultados(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    if current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver el listado de resultados")
    return await crud.resultado_crud.get_multi(db, skip, limit)

@router.get("/{id_resultado}", response_model=schemas.ResultadoOut)
async def get_resultado(
    id_resultado: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    # Por ahora permitimos a laboratoristas y médicos. 
    # Para pacientes se requeriría una lógica de propiedad más compleja (verificar solicitud).
    if current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver resultados individuales")
        
    resultado = await crud.resultado_crud.get(db, id_resultado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return resultado

@router.post("/", response_model=schemas.ResultadoOut, status_code=201)
async def create_resultado(
    resultado_in: schemas.ResultadoCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    return await crud.resultado_crud.create(db, resultado_in)

@router.put("/{id_resultado}", response_model=schemas.ResultadoOut)
async def update_resultado(
    id_resultado: int, 
    resultado_in: schemas.ResultadoUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    updated = await crud.resultado_crud.update(db, id_resultado, resultado_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return updated

@router.delete("/{id_resultado}")
async def delete_resultado(
    id_resultado: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    deleted = await crud.resultado_crud.soft_delete(db, id_resultado)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return {"message": "Resultado desactivado (borrado lógico)"}