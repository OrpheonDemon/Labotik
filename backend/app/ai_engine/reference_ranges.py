"""
Reference Ranges - Base de datos de valores de referencia clínicos
Especializado para laboratorio médico - Valores estándar internacionales
"""

from typing import Dict, Any, Optional, Tuple

# RANGOS DE REFERENCIA CLÍNICOS ESTÁNDAR (OMS/ISO)
REFERENCE_RANGES = {
    # === HEMOGRAMA ===
    "hemoglobina": {
        "hombre": {"min": 13.5, "max": 17.5, "unidad": "g/dL"},
        "mujer": {"min": 12.0, "max": 15.5, "unidad": "g/dL"},
        "critico_bajo": 8.0,
        "critico_alto": 20.0,
        "descripcion": "Proteína transportadora de oxígeno en glóbulos rojos"
    },
    "hematocrito": {
        "hombre": {"min": 41, "max": 53, "unidad": "%"},
        "mujer": {"min": 36, "max": 46, "unidad": "%"},
        "critico_bajo": 20,
        "critico_alto": 60,
        "descripcion": "Porcentaje de volumen de glóbulos rojos en sangre"
    },
    "leucocitos": {
        "general": {"min": 4.5, "max": 11.0, "unidad": "K/uL"},
        "critico_bajo": 2.0,
        "critico_alto": 30.0,
        "descripcion": "Células de defensa del sistema inmunitario"
    },
    "plaquetas": {
        "general": {"min": 150, "max": 400, "unidad": "K/uL"},
        "critico_bajo": 50,
        "critico_alto": 1000,
        "descripcion": "Células responsables de la coagulación"
    },
    "MCV": {
        "general": {"min": 80, "max": 100, "unidad": "fL"},
        "descripcion": "Volumen corpuscular medio de glóbulo rojo"
    },
    
    # === BIOQUÍMICA BÁSICA ===
    "glucosa": {
        "ayunas": {"min": 70, "max": 100, "unidad": "mg/dL"},
        "post_prandial": {"min": 70, "max": 140, "unidad": "mg/dL"},
        "critico_bajo": 40,
        "critico_alto": 600,
        "descripcion": "Azúcar en sangre - Energía celular"
    },
    "creatinina": {
        "hombre": {"min": 0.7, "max": 1.3, "unidad": "mg/dL"},
        "mujer": {"min": 0.6, "max": 1.1, "unidad": "mg/dL"},
        "critico": 10.0,
        "descripcion": "Marcador primario de función renal"
    },
    "BUN": {
        "general": {"min": 7, "max": 20, "unidad": "mg/dL"},
        "critico": 100,
        "descripcion": "Nitrógeno de urea en sangre - Función renal"
    },
    "FGe": {
        "general": {"min": 60, "max": 120, "unidad": "mL/min/1.73m²"},
        "descripcion": "Filtrado glomerular estimado - Función renal"
    },
    
    # === ELECTROLITOS ===
    "sodio": {
        "general": {"min": 136, "max": 145, "unidad": "mEq/L"},
        "critico_bajo": 120,
        "critico_alto": 160,
        "descripcion": "Electrolito principal extracelular"
    },
    "potasio": {
        "general": {"min": 3.5, "max": 5.0, "unidad": "mEq/L"},
        "critico_bajo": 2.5,
        "critico_alto": 7.0,
        "descripcion": "Electrolito principal intracelular - Riesgo arritmia"
    },
    "cloro": {
        "general": {"min": 98, "max": 107, "unidad": "mEq/L"},
        "descripcion": "Electrolito principal extracelular"
    },
    "calcio": {
        "general": {"min": 8.5, "max": 10.5, "unidad": "mg/dL"},
        "critico_bajo": 6.5,
        "critico_alto": 13.0,
        "descripcion": "Mineral para huesos, músculos y función nerviosa"
    },
    "fosforo": {
        "general": {"min": 2.5, "max": 4.5, "unidad": "mg/dL"},
        "descripcion": "Mineral para huesos y metabolismo energético"
    },
    
    # === FUNCIÓN HEPÁTICA ===
    "AST": {
        "general": {"min": 0, "max": 40, "unidad": "U/L"},
        "critico": 400,
        "descripcion": "Aspartato aminotransferasa - Daño hepático"
    },
    "ALT": {
        "general": {"min": 0, "max": 44, "unidad": "U/L"},
        "critico": 400,
        "descripcion": "Alanino aminotransferasa - Daño hepático específico"
    },
    "bilirrubina_total": {
        "general": {"min": 0.1, "max": 1.2, "unidad": "mg/dL"},
        "critico": 20.0,
        "descripcion": "Pigmento biliar total - Función hepática"
    },
    "bilirrubina_directa": {
        "general": {"min": 0.0, "max": 0.3, "unidad": "mg/dL"},
        "descripcion": "Bilirrubina conjugada - Excreción biliar"
    },
    "fosfatasa_alcalina": {
        "general": {"min": 30, "max": 120, "unidad": "U/L"},
        "descripcion": "Enzima de metabolismo óseo y biliar"
    },
    "albumina": {
        "general": {"min": 3.5, "max": 5.5, "unidad": "g/dL"},
        "descripcion": "Proteína principal del plasma - Síntesis hepática"
    },
    
    # === LÍPIDOS ===
    "colesterol_total": {
        "deseable": {"min": 0, "max": 200, "unidad": "mg/dL"},
        "borderline": {"min": 200, "max": 240, "unidad": "mg/dL"},
        "alto": {"min": 240, "max": 999, "unidad": "mg/dL"},
        "descripcion": "Colesterol total - Riesgo cardiovascular"
    },
    "colesterol_HDL": {
        "hombre_bajo": {"min": 0, "max": 40, "unidad": "mg/dL"},
        "mujer_bajo": {"min": 0, "max": 50, "unidad": "mg/dL"},
        "optimo": {"min": 60, "max": 999, "unidad": "mg/dL"},
        "descripcion": "Colesterol bueno - Protector cardiovascular"
    },
    "colesterol_LDL": {
        "optimo": {"min": 0, "max": 100, "unidad": "mg/dL"},
        "alto_riesgo": {"min": 190, "max": 999, "unidad": "mg/dL"},
        "descripcion": "Colesterol malo - Riesgo aterosclerosis"
    },
    "trigliceridos": {
        "normal": {"min": 0, "max": 150, "unidad": "mg/dL"},
        "borderline": {"min": 150, "max": 200, "unidad": "mg/dL"},
        "alto": {"min": 200, "max": 999, "unidad": "mg/dL"},
        "descripcion": "Grasas triglicéridas en sangre"
    },
    
    # === COAGULACIÓN ===
    "tiempo_protrombina": {
        "general": {"min": 11, "max": 13.5, "unidad": "seg"},
        "critico": 30,
        "descripcion": "PT - Tiempo para coagular"
    },
    "INR": {
        "normal": {"min": 0.8, "max": 1.1, "unidad": "ratio"},
        "anticoagulado": {"min": 2.0, "max": 3.0, "unidad": "ratio"},
        "descripcion": "Índice normalizado internacional para warfarina"
    },
    "tiempo_tromboplastina": {
        "general": {"min": 25, "max": 35, "unidad": "seg"},
        "critico": 100,
        "descripcion": "APPT - Tiempo de tromboplastina activado"
    },
    "fibrinogeno": {
        "general": {"min": 200, "max": 400, "unidad": "mg/dL"},
        "critico_bajo": 100,
        "descripcion": "Factor de coagulación I"
    },
    
    # === HORMONAL ===
    "TSH": {
        "general": {"min": 0.4, "max": 4.0, "unidad": "mIU/L"},
        "hipertiroidismo": {"min": 0.0, "max": 0.4, "unidad": "mIU/L"},
        "hipotiroidismo": {"min": 5.0, "max": 999, "unidad": "mIU/L"},
        "descripcion": "Hormona estimulante del tiroides"
    },
    "T3_libre": {
        "general": {"min": 2.3, "max": 4.2, "unidad": "pg/mL"},
        "descripcion": "Triyodotironina libre"
    },
    "T4_libre": {
        "general": {"min": 0.89, "max": 1.76, "unidad": "ng/dL"},
        "descripcion": "Tiroxina libre"
    },
    
    # === INFLAMACIÓN ===
    "PCR": {
        "normal": {"min": 0, "max": 3.0, "unidad": "mg/L"},
        "inflamacion": {"min": 3.0, "max": 10.0, "unidad": "mg/L"},
        "infeccion": {"min": 10.0, "max": 999, "unidad": "mg/L"},
        "descripcion": "Proteína C reactiva - Marcador de inflamación"
    },
    "VSG": {
        "hombre": {"min": 0, "max": 15, "unidad": "mm/h"},
        "mujer": {"min": 0, "max": 20, "unidad": "mm/h"},
        "descripcion": "Velocidad de sedimentación globular"
    },
}

# Valores críticos que requieren notificación inmediata
CRITICAL_VALUES = {
    "hemoglobina": {"bajo": 8.0, "alto": 20.0},
    "potasio": {"bajo": 2.5, "alto": 7.0},
    "glucosa": {"bajo": 40, "alto": 600},
    "sodio": {"bajo": 120, "alto": 160},
    "creatinina": {"alto": 10.0},
    "bilirrubina_total": {"alto": 20.0},
    "INR": {"bajo": 0.5, "alto": 10.0},
    "tiempo_protrombina": {"alto": 30},
    "calcio": {"bajo": 6.5, "alto": 13.0},
}


def get_reference_range(
    test_name: str,
    age: Optional[int] = None,
    gender: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Obtiene rango de referencia normalizado para una prueba
    
    Args:
        test_name: Nombre de la prueba (ej: "hemoglobina")
        age: Edad del paciente (opcional)
        gender: Género del paciente ("hombre" o "mujer")
    
    Returns:
        Dict con min, max, unidad o None si no existe
    """
    test_name = test_name.lower().strip()
    
    if test_name not in REFERENCE_RANGES:
        return None
    
    range_data = REFERENCE_RANGES[test_name]
    
    # Seleccionar por género si aplica
    if gender and gender.lower() in range_data:
        candidate = range_data[gender.lower()]
        if isinstance(candidate, dict) and "min" in candidate:
            return candidate
    
    # Seleccionar "general" si existe
    if "general" in range_data:
        candidate = range_data["general"]
        if isinstance(candidate, dict) and "min" in candidate:
            return candidate
    
    # Seleccionar "hombre" si existe
    if "hombre" in range_data:
        candidate = range_data["hombre"]
        if isinstance(candidate, dict) and "min" in candidate:
            return candidate
    
    # Buscar cualquier key que contenga min/max
    for key, value in range_data.items():
        if isinstance(value, dict) and "min" in value and "max" in value:
            return value
    
    return None


def is_critical(test_name: str, value: float) -> bool:
    """
    Verifica si un valor es crítico y requiere alerta inmediata
    
    Args:
        test_name: Nombre de la prueba
        value: Valor medido
    
    Returns:
        True si es crítico, False otherwise
    """
    test_name = test_name.lower().strip()
    
    if test_name not in CRITICAL_VALUES:
        return False
    
    critical = CRITICAL_VALUES[test_name]
    
    if "bajo" in critical and value < critical["bajo"]:
        return True
    
    if "alto" in critical and value > critical["alto"]:
        return True
    
    return False


def get_interpretation_level(test_name: str, value: float) -> str:
    """
    Retorna nivel de interpretación: CRÍTICO | ALTO | NORMAL | BAJO
    
    Args:
        test_name: Nombre de la prueba
        value: Valor medido
    
    Returns:
        String con el nivel de interpretación
    """
    
    if is_critical(test_name, value):
        return "CRÍTICO"
    
    range_data = get_reference_range(test_name)
    if not range_data:
        return "DESCONOCIDO"
    
    min_val = range_data.get("min", float('-inf'))
    max_val = range_data.get("max", float('inf'))
    
    if value < min_val:
        return "BAJO"
    elif value > max_val:
        return "ALTO"
    else:
        return "NORMAL"


def get_description(test_name: str) -> str:
    """Obtiene descripción clínica de una prueba"""
    test_name = test_name.lower().strip()
    
    if test_name in REFERENCE_RANGES:
        return REFERENCE_RANGES[test_name].get("descripcion", "Prueba de laboratorio")
    
    return "Prueba desconocida"


# Ejemplos de uso
if __name__ == "__main__":
    # Ejemplo 1: Hemoglobina baja en mujer
    print("Ejemplo 1: Hemoglobina mujer")
    rango = get_reference_range("hemoglobina", gender="mujer")
    print(f"  Rango: {rango}\n")
    
    # Ejemplo 2: Potasio crítico
    print("Ejemplo 2: ¿K 7.5 es crítico?")
    es_critico = is_critical('potasio', 7.5)
    print(f"  Crítico: {es_critico}\n")
    
    # Ejemplo 3: Nivel de interpretación
    print("Ejemplo 3: Nivel de glucosa 250")
    nivel = get_interpretation_level("glucosa", 250)
    print(f"  Nivel: {nivel}\n")
    
    # Ejemplo 4: Descripción
    print("Ejemplo 4: Descripción de PCR")
    desc = get_description("PCR")
    print(f"  Descripción: {desc}")
