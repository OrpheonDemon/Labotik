# Módulo de IA Clínica - MedGemma

## Descripción General

Sistema de interpretación clínica basado en **MedGemma** (modelo LLM médico) ejecutándose localmente en **Ollama** para máxima privacidad y seguridad.

## Arquitectura

```
OllamaClient (Async HTTP to Ollama)
    ↓
ClinicalInterpreter (Analysis Engine)
    ↓
├── AnomalyDetector (Detección de errores)
├── PriorityEngine (Clasificación de urgencia)
├── ObservationGenerator (Observaciones clínicas)
├── ClinicalAssistant (Chat interactivo)
└── Specialized Analyzers (Anemia, Inflamación, Hígado, Riñones, Metabolismo)

Servicios de Soporte:
├── AuditService (Auditoría de decisiones)
├── EmbeddingsService (Búsqueda semántica)
├── RAGEngine (Recuperación aumentada de generación)
└── LaboratoryRulesEngine (Validación de reglas)
```

## Instalación y Configuración

### 1. Instalar Ollama

```bash
# Windows: Descargar desde https://ollama.ai
# Linux: curl https://ollama.ai/install.sh | sh
```

### 2. Descargar MedGemma

```bash
ollama pull medgemma
```

### 3. Verificar Disponibilidad

```bash
# Ollama debe estar ejecutándose en http://localhost:11434
curl http://localhost:11434/api/tags
```

### 4. Instalar Dependencias Python

```bash
pip install -r requirements.txt
# Las principales son: aiohttp, tenacity, pydantic
```

## Módulos Principales

### OllamaClient
**Ubicación:** `backend/app/ai_engine/ollama_client.py`

Cliente asíncrono para comunicación con Ollama. Incluye:
- Reintentos automáticos con backoff exponencial
- Pool de conexiones para eficiencia
- Manejo de timeouts (300 segundos por defecto)
- Extracción JSON robusta

```python
from app.ai_engine import OllamaClient

client = OllamaClient(model="medgemma", base_url="http://localhost:11434")
response = await client.generate_json(
    prompt="Analiza estos resultados...",
    system="Eres un asistente clínico...",
    temperature=0.3
)
```

### ClinicalInterpreter
**Ubicación:** `backend/app/ai_engine/clinical_interpreter.py`

Intérprete clínico con análisis especializados:

```python
from app.ai_engine import ClinicalInterpreter

interpreter = ClinicalInterpreter(ollama_client)

# Interpretación general
interpretation = await interpreter.interpret_results(
    results={"Hemoglobina": 12.5, "Leucocitos": 7.2},
    patient_context={"edad": 45, "sexo": "F"}
)

# Análisis especializados
anemia_analysis = await interpreter.analyze_anemia(
    hemogram={"hemoglobina": 11.0, "hematocrito": 33},
    iron_studies={"ferritina": 50}
)

inflammation = await interpreter.analyze_inflammation(
    inflammatory_markers={"pcr": 5.2, "leucocitos": 11.0}
)
```

### AnomalyDetector
**Ubicación:** `backend/app/ai_engine/anomaly_detector.py`

Detecta anomalías, errores de laboratorio, muestras comprometidas:

```python
detector = AnomalyDetector(ollama_client)

anomalies = await detector.detect_anomalies(
    results={"K": 8.5, "Hb": 9.2},  # K muy alto + Hb baja = hemólisis
    reference_ranges={"K": (3.5, 5.0), "Hb": (12, 16)}
)
# Detecta hemólisis automáticamente
```

### PriorityEngine
**Ubicación:** `backend/app/ai_engine/priority_engine.py`

Clasifica urgencia clínica:

```python
priority_engine = PriorityEngine(ollama_client)

priority = await priority_engine.prioritize(
    results={"Troponina": 2.5, "K": 7.0},
    critical_values={"Troponina": (0, 0.04), "K": (3.5, 5.0)}
)
# Retorna: {"prioridad": "CRÍTICO", "tiempo_respuesta_sugerido": "Inmediato"}
```

### ClinicalAssistant
**Ubicación:** `backend/app/ai_engine/clinical_assistant.py`

Chat clínico interactivo:

```python
assistant = ClinicalAssistant(ollama_client)

response = await assistant.ask_question(
    question="¿Por qué está bajo este valor?",
    patient_data={"nombre": "Juan", "edad": 45, "sexo": "M"},
    test_name="Hemoglobina",
    test_value=11.0,
    reference_range="12-16"
)

# Comparación histórica
comparison = await assistant.compare_with_history(
    current_results={"Hb": 11.5},
    previous_results=[{"Hb": 12.0}, {"Hb": 12.5}]
)
```

### LaboratoryRulesEngine
**Ubicación:** `backend/app/ai_engine/audit_service.py`

Validación basada en reglas clínicas:

```python
rules = LaboratoryRulesEngine()

# Verificar valor crítico
is_critical = rules.is_critical_value("Potasio", 7.2)  # True

# Validar calidad de muestra
issues = rules.validate_sample_quality({"K": 6.5, "Hb": 9.0})
# ["Posible hemólisis (K elevado con Hb baja)"]
```

## API REST - Endpoints

Todos requieren autenticación (JWT token en header `Authorization: Bearer <token>`)

### `POST /ai/status`
Verifica estado de Ollama y MedGemma.

**Respuesta:**
```json
{
  "status": "available",
  "ollama_running": true,
  "models": ["medgemma:latest"],
  "model_active": true
}
```

### `POST /ai/interpret-results`
Interpreta resultados de laboratorio de una solicitud.

**Requiere:** Rol médico
**Body:**
```json
{
  "id_solicitud": 123,
  "clinical_history": "Historial relevante aquí"
}
```

**Respuesta:**
```json
{
  "status": "success",
  "interpretation": {
    "hallazgos_relevantes": [...],
    "interpretacion_clinica": "...",
    "alertas_criticas": [...],
    "prioridad": "REVISIÓN",
    "requiere_revision_humana": true,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

### `POST /ai/detect-anomalies`
Detecta anomalías en resultados.

**Body:**
```json
{
  "id_solicitud": 123,
  "results": {"Hemoglobina": 2.5, "Potasio": 8.0}
}
```

### `POST /ai/prioritize`
Clasifica urgencia del estudio.

**Body:**
```json
{
  "id_solicitud": 123,
  "results": {"Troponina": 0.15, "K": 7.2}
}
```

### `POST /ai/chat`
Chat clínico - responde preguntas sobre resultados.

**Body:**
```json
{
  "id_solicitud": 123,
  "question": "¿Por qué está bajo este valor?",
  "test_name": "Hemoglobina"
}
```

### `GET /ai/audit-log`
Obtiene log de decisiones IA (solo administradores).

### `POST /ai/explain-biomarker`
Explica un biomarcador específico.

**Query:** `biomarker=Hemoglobina`

### `POST /ai/validate-sample-quality`
Valida calidad de muestra.

**Body:**
```json
{
  "results": {"K": 6.5, "Hb": 9.0, "Glucosa": 100}
}
```

## Características de Seguridad Clínica

1. **Privacidad Local:** MedGemma ejecuta localmente - NINGÚN dato se envía a servidores externos
2. **Revisión Humana Obligatoria:** Todos los análisis incluyen flag `requiere_revision_humana`
3. **Nunca Emite Diagnósticos:** Prompts explícitamente prohíben diagnósticos definitivos
4. **Auditoría Completa:** Todas las decisiones se registran con timestamp y usuario
5. **Valores Críticos:** Sistema de alertas para valores clínicamente críticos
6. **Validación de Muestras:** Detecta hemólisis, lipemia y otros problemas

## Configuración de Prompts

Los prompts médicos se encuentran en `backend/app/ai_engine/prompts.py`.

Características clave:
- **SYSTEM_PROMPT:** Define rol de asistente clínico, restricciones éticas, idioma español
- **Temperatura:** 0.3 para JSON (precisión), 0.5-0.7 para texto (variabilidad)
- **Restricciones:** "NUNCA emites diagnósticos definitivos", "Siempre sugiere revisión médica"

## Testing

```bash
# Verificar conexión a Ollama
curl http://localhost:11434/api/tags

# Test de interpretación
curl -X POST http://localhost:8000/ai/interpret-results \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"id_solicitud": 123}'
```

## Troubleshooting

### Ollama no responde
```bash
# Reiniciar Ollama
ollama serve

# O en background:
ollama serve &
```

### MedGemma no está disponible
```bash
# Verificar
ollama list

# Descargar si falta
ollama pull medgemma
```

### Respuestas lentas
- Aumentar timeout en OllamaClient (default 300s)
- Considerar servidor con más recursos GPU
- Verificar que Ollama no esté procesando otras solicitudes

## Performance

- **Interpretación general:** 2-5 segundos
- **Análisis especializados:** 3-8 segundos
- **Detección de anomalías:** 1-3 segundos
- **Chat clínico:** 2-4 segundos

Tiempos dependen de:
- Hardware del servidor (GPU recomendada)
- Tamaño del prompt
- Complejidad del caso

## Próximas Mejoras

- [ ] RAG con base de conocimiento médico local
- [ ] Visualización de confianza del modelo
- [ ] Exportación de reportes generados por IA
- [ ] Integración con sistemas de orden PACS
- [ ] Análisis de tendencias con histórico
