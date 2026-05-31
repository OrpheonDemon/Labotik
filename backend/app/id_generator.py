from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
import re

async def generate_area_id(db: AsyncSession, model, nombre: str) -> str:
    """
    Genera ID para áreas de laboratorio con formato:
    - Base: primeras 3 letras del nombre en mayúscula
    - Número: siempre comienza en 1 y se incrementa si ya existen IDs con las mismas 3 letras
    - Ejemplo: "Cardiología" -> "CAR1", si ya existe -> "CAR2", "CAR3", etc.
                "Hematología" -> "HEM1"
    """
    from app.models import AreaLaboratorio
    
    # Extraer las primeras 3 letras del nombre
    base_letters = nombre[:3].upper()
    
    # Buscar todos los IDs que comienzan con las mismas 3 letras
    stmt = select(AreaLaboratorio).where(
        AreaLaboratorio.id_area.ilike(f"{base_letters}%")
    )
    result = await db.execute(stmt)
    existing_ids = [area.id_area for area in result.scalars().all()]
    
    # Extraer números existentes
    numbers = []
    for id_str in existing_ids:
        match = re.search(rf"{re.escape(base_letters)}(\d+)", id_str)
        if match:
            numbers.append(int(match.group(1)))
    
    # El siguiente número: máximo + 1, comenzando desde 1 si no hay números
    next_number = max(numbers) + 1 if numbers else 1
    return f"{base_letters}{next_number}"

async def get_next_int_id(db: AsyncSession, model, pk_column_name: str = "id") -> int:
    """Genera el siguiente ID para tablas con PK INT o VARCHAR representando INT (comienza en 1000)."""
    pk_column = getattr(model, pk_column_name)
    stmt = select(func.max(pk_column))
    result = await db.execute(stmt)
    max_id = result.scalar_one()
    if max_id is not None:
        try:
            return int(max_id) + 1
        except (ValueError, TypeError):
            pass
    return 1000

async def generate_persona_id(
    db: AsyncSession,
    model,
    nombre: str,
    apellido_paterno: str,
    apellido_materno: str = "",
    fecha_nac: date = None,
    genero: str = None
) -> str:
    """
    Genera ID con formato:
    Hombres: AAAAMMDD + inicial_nombre + inicial_apellido_paterno + inicial_apellido_materno
    Mujeres: AAAA(MM+50)DD + iniciales
    Ejemplo: Rotherick Calderón Molina, 1995-08-09, M -> 19950809RCM
             María López Gutiérrez, 1990-03-15, F -> 19905315MLG
    """
    # Parte de fecha con ajuste de mes para mujeres
    year = fecha_nac.strftime("%Y")
    month = fecha_nac.month
    day = fecha_nac.strftime("%d")
    if genero == 'F':
        month += 50
    month_str = f"{month:02d}"
    date_part = f"{year}{month_str}{day}"

    # Iniciales: primera letra de cada parte (solo la primera palabra)
    def first_letter(s: str) -> str:
        return s.strip().upper()[0] if s else ''
    init_nombre = first_letter(nombre.split()[0])
    init_apaterno = first_letter(apellido_paterno)
    init_amaterno = first_letter(apellido_materno) if apellido_materno else ''
    base_id = f"{date_part}{init_nombre}{init_apaterno}{init_amaterno}"

    # Verificar unicidad (asumimos que la columna PK se llama 'id' en el modelo, pero los modelos tienen nombres específicos)
    # En el CRUD pasaremos el nombre correcto de la columna.
    # Por simplicidad, aquí se usa 'id' genérico; lo ajustaremos llamando a esta función desde el CRUD con el campo correcto.
    final_id = base_id
    counter = 1
    while True:
        # Obtener el nombre real de la columna PK del modelo
        pk_col_name = model.__table__.primary_key.columns[0].name
        stmt = select(model).where(getattr(model, pk_col_name) == final_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            break
        final_id = f"{base_id}{counter}"
        counter += 1
    return final_id