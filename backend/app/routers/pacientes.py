from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app import schemas, crud
from app.database import get_db
from app.dependencies import require_laboratorista, require_medico, get_current_active_user
from app.models import Paciente

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.get("/", response_model=list[schemas.PacienteOut])
async def list_pacientes(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    if current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para listar pacientes")
    return await crud.paciente_crud.get_multi(db, skip, limit)

@router.get("/search", response_model=list[schemas.PacienteOut])
async def search_pacientes(
    apellido_paterno: str = Query(None),
    apellido_materno: str = Query(None),
    nombre: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    if current_user["rol"] not in ["laboratorista", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para buscar pacientes")
    return await crud.paciente_crud.search_by_names(db, apellido_paterno, apellido_materno, nombre)

@router.get("/{id_paciente}", response_model=schemas.PacienteOut)
async def get_paciente(
    id_paciente: str, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    # Un paciente solo puede verse a sí mismo, a menos que sea laboratorista o médico
    user_obj = current_user["user"]
    if current_user["rol"] == "paciente" and user_obj.id_paciente != id_paciente:
        raise HTTPException(status_code=403, detail="No puedes ver información de otros pacientes")
    
    paciente = await crud.paciente_crud.get(db, id_paciente)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return paciente

@router.post("/", response_model=schemas.PacienteOut, status_code=201)
async def create_paciente(paciente_in: schemas.PacienteCreate, db: AsyncSession = Depends(get_db)):
    return await crud.paciente_crud.create(db, paciente_in)

@router.put("/{id_paciente}", response_model=schemas.PacienteOut)
async def update_paciente(
    id_paciente: str, 
    paciente_in: schemas.PacienteUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    user_obj = current_user["user"]
    if current_user["rol"] == "paciente" and user_obj.id_paciente != id_paciente:
        raise HTTPException(status_code=403, detail="No puedes modificar a otros pacientes")
    elif current_user["rol"] == "medico":
         raise HTTPException(status_code=403, detail="Los médicos no pueden modificar datos de pacientes")

    updated = await crud.paciente_crud.update(db, id_paciente, paciente_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return updated

@router.delete("/{id_paciente}")
async def delete_paciente(
    id_paciente: str, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_laboratorista)
):
    deleted = await crud.paciente_crud.soft_delete(db, id_paciente)
    if not deleted:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return {"message": "Paciente desactivado (borrado lógico)"}