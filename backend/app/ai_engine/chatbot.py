"""
Smart Clinical Chatbot - Consultas inteligentes usando datos de la app + MedGema
Combina información de pacientes, resultados, rangos de referencia y el modelo Ollama medgemma
"""
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartClinicalChatbot:
    """
    Chatbot clínico inteligente que utiliza datos de la aplicación 
    (pacientes, resultados, rangos) junto con MedGema/Ollama 
    para responder consultas sobre enfermedades, resultados y más.
    """

    def __init__(self, ollama_client, db_session=None):
        self.ollama = ollama_client
        self.db = db_session
        # Mantener historial de conversación
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 20

    async def ask(self, 
                  question: str,
                  user_info: Optional[Dict] = None,
                  patient_context: Optional[Dict] = None,
                  lab_results: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Procesa una pregunta y genera respuesta usando datos del contexto.
        
        Args:
            question: Pregunta del usuario
            user_info: Info del usuario que pregunta (rol, nombre)
            patient_context: Datos del paciente si está en contexto
            lab_results: Resultados de laboratorio si están disponibles
        
        Returns:
            Dict con respuesta, fuentes usadas y metadatos
        """
        
        # Actualizar historial
        self.conversation_history.append({"role": "user", "content": question})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        # Determinar el tipo de consulta
        query_type = self._classify_query(question.lower())

        # Construir el contexto enriquecido
        enriched_context = self._build_context(question, patient_context, lab_results, query_type)
        
        # Elegir el prompt del sistema basado en el tipo
        system_prompt = self._get_system_prompt(query_type, user_info)
        
        # Generar respuesta con Ollama
        full_prompt = f"""{enriched_context}

Historial de la conversación:
{self._format_history()}

Pregunta del usuario: {question}

INSTRUCCIONES:
1. Responde de forma clara, profesional y educativa
2. Usa los datos clínicos proporcionados en el contexto si están disponibles
3. Si la pregunta es sobre enfermedades, explica síntomas, causas y cuándo consultar al médico
4. Si la pregunta es sobre resultados, interpreta usando los rangos de referencia
5. NO diagnostiques enfermedades específicas
6. Siempre incluye: "Consulta a tu médico para una evaluación completa"
7. Responde en español
8. Máximo 5 párrafos
9. Usa lenguaje claro pero profesional"""

        try:
            response = await self.ollama.generate_text(
                prompt=full_prompt,
                system=system_prompt,
                temperature=0.3
            )
            
            # Agregar al historial
            self.conversation_history.append({"role": "assistant", "content": response})
            
            sources_used = []
            if patient_context:
                sources_used.append("datos del paciente")
            if lab_results:
                sources_used.append("resultados de laboratorio")
            
            return {
                "respuesta": response,
                "tipo_consulta": query_type,
                "fuentes": sources_used,
                "hay_resultados": bool(lab_results),
                "hay_paciente": bool(patient_context),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return {
                "respuesta": "Lo siento, no pude procesar tu pregunta en este momento. " 
                            "Por favor, verifica que el motor de IA esté disponible e intenta de nuevo.",
                "tipo_consulta": "error",
                "fuentes": [],
                "error": str(e)
            }

    async def ask_stream(self, 
                         question: str,
                         user_info: Optional[Dict] = None,
                         patient_context: Optional[Dict] = None,
                         lab_results: Optional[Dict] = None) -> AsyncGenerator[str, None]:
        """
        Procesa una pregunta y genera respuesta usando datos del contexto con streaming.
        """
        # Actualizar historial
        self.conversation_history.append({"role": "user", "content": question})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        # Determinar el tipo de consulta primero
        query_type = self._classify_query(question.lower())

        # Construir el contexto enriquecido pasándole el query_type
        enriched_context = self._build_context(question, patient_context, lab_results, query_type)
        
        # Elegir el prompt del sistema basado en el tipo
        system_prompt = self._get_system_prompt(query_type, user_info)
        
        # Generar respuesta con Ollama
        full_prompt = f"""{enriched_context}

Historial de la conversación:
{self._format_history()}

Pregunta del usuario: {question}

INSTRUCCIONES:
1. Responde de forma clara, profesional y educativa
2. Usa los datos clínicos proporcionados en el contexto si están disponibles
3. Si la pregunta es sobre enfermedades, explica síntomas, causas y cuándo consultar al médico
4. Si la pregunta es sobre resultados, interpreta usando los rangos de referencia
5. NO diagnostiques enfermedades específicas
6. Siempre incluye: "Consulta a tu médico para una evaluación completa"
7. Responde en español
8. Máximo 5 párrafos
9. Usa lenguaje claro pero profesional"""

        try:
            full_response = []
            async for chunk in self.ollama.generate_text_stream(
                prompt=full_prompt,
                system=system_prompt,
                temperature=0.3
            ):
                full_response.append(chunk)
                yield chunk
            
            # Agregar al historial completo
            response_str = "".join(full_response)
            self.conversation_history.append({"role": "assistant", "content": response_str})
            
        except Exception as e:
            logger.error(f"Chatbot stream error: {e}")
            yield "Lo siento, no pude procesar tu pregunta en este momento. Por favor, verifica que el motor de IA esté disponible e intenta de nuevo."

    def _build_context(self, question: str, 
                       patient: Optional[Dict],
                       results: Optional[Dict],
                       query_type: str = "general_qa") -> str:
        """Construye el contexto enriquecido con datos de la app."""
        parts = ["CONTEXTO DISPONIBLE:\n"]
        
        # Contexto del paciente
        if patient:
            parts.append(f"""--- DATOS DEL PACIENTE ---
Nombre: {patient.get('nombre', 'Desconocido')} {patient.get('apellido_paterno', '')}
Edad: {patient.get('edad', 'No especificada')} años
Género: {patient.get('genero', 'No especificado')}
ID: {patient.get('id_paciente', 'N/A')}""")
            if patient.get('alergias'):
                parts.append(f"Alergias: {patient['alergias']}")
            if patient.get('tipo_sangre'):
                parts.append(f"Tipo de sangre: {patient['tipo_sangre']}")
            parts.append("")

        # Resultados de laboratorio
        if results:
            parts.append("--- RESULTADOS DE LABORATORIO ---")
            from app.ai_engine.reference_ranges import REFERENCE_RANGES
            for nombre, valor in results.items():
                nombre_lower = nombre.lower().strip()
                rango_info = REFERENCE_RANGES.get(nombre_lower)
                if rango_info:
                    # Determinar el rango según género
                    if patient and patient.get('genero'):
                        gen = 'hombre' if patient['genero'] in ['M', 'Masculino'] else 'mujer'
                        if gen in rango_info:
                            rango = rango_info[gen]
                        elif 'general' in rango_info:
                            rango = rango_info['general']
                        else:
                            rango = rango_info.get('hombre', {})
                    elif 'general' in rango_info:
                        rango = rango_info['general']
                    else:
                        rango = rango_info.get('hombre', {})
                    
                    unidad = rango.get('unidad', '')
                    min_v = rango.get('min', 'N/A')
                    max_v = rango.get('max', 'N/A')
                    desc = rango_info.get('descripcion', '')
                    
                    # Evaluar estado
                    try:
                        val = float(valor)
                        if val < min_v:
                            estado = "⬇️ BAJO"
                        elif val > max_v:
                            estado = "⬆️ ALTO"
                        else:
                            estado = "✅ NORMAL"
                    except (ValueError, TypeError):
                        estado = "⚠️ Revisar"
                        val = valor
                    
                    parts.append(f"{nombre}: {val} {unidad} (Rango: {min_v}-{max_v}) {estado}")
                    parts.append(f"  → {desc}")
                else:
                    parts.append(f"{nombre}: {valor}")
            parts.append("")
        
        # Rangos de referencia clave (solo si es relevante)
        if query_type in ('result_interpretation', 'biomarker_explanation'):
            parts.append("--- RANGOS DE REFERENCIA CLAVE DISPONIBLES ---")
            key_tests = [
                ("Hemoglobina", "Hombre: 13.5-17.5 g/dL, Mujer: 12.0-15.5 g/dL"),
                ("Glucosa", "70-100 mg/dL (ayunas)"),
                ("Potasio", "3.5-5.0 mEq/L"),
                ("Leucocitos", "4.5-11.0 K/uL"),
                ("Plaquetas", "150-400 K/uL"),
                ("Creatinina", "0.7-1.3 mg/dL (hombre), 0.6-1.1 mg/dL (mujer)"),
                ("TSH", "0.4-4.0 mIU/L"),
                ("PCR", "0-3 mg/L (normal)"),
                ("Colesterol total", "<200 mg/dL (deseable)"),
                ("INR", "0.8-1.1 (normal)")
            ]
            for test, rango in key_tests:
                parts.append(f"  • {test}: {rango}")
        
        return "\n".join(parts)

    def _classify_query(self, question: str) -> str:
        """Clasifica el tipo de consulta para elegir el prompt adecuado."""
        disease_keywords = [
            'enfermedad', 'enfermedades', 'síntoma', 'síntomas', 'diagnóstico',
            'cáncer', 'diabetes', 'hipertensión', 'infección', 'virus', 'bacteria',
            'anemia', 'leucemia', 'hepatitis', 'covid', 'gripe', 'dolor',
            'tratamiento', 'causa', 'prevención', 'riesgo', 'contagio'
        ]
        result_keywords = [
            'resultado', 'análisis', 'prueba', 'examen', 'valor', 'nivel',
            'hemoglobina', 'glucosa', 'colesterol', 'potasio', 'sodio',
            'leucocitos', 'plaquetas', 'creatinina', 'TSH', 'PCR', 'INR',
            'alto', 'bajo', 'normal', 'elevado', 'disminuido', 'crítico',
            'rango', 'referencia'
        ]
        biomarker_keywords = [
            'qué es', 'significa', 'para qué sirve', 'explica', 'qué mide',
            'qué indica', 'biomarcador', 'marcador'
        ]
        general_medical = [
            'salud', 'médico', 'consulta', 'recomendación', 'consejo',
            'debería', 'cuándo', 'cómo saber', 'es normal'
        ]

        score_disease = sum(1 for k in disease_keywords if k in question)
        score_result = sum(1 for k in result_keywords if k in question)
        score_biomarker = sum(1 for k in biomarker_keywords if k in question)
        score_general = sum(1 for k in general_medical if k in question)

        if score_biomarker >= 2 or (score_biomarker >= 1 and score_result >= 1):
            return "biomarker_explanation"
        elif score_result >= 2:
            return "result_interpretation"
        elif score_disease >= 2:
            return "disease_info"
        elif score_general >= 1:
            return "general_medical"
        else:
            return "general_qa"

    def _get_system_prompt(self, query_type: str, user_info: Optional[Dict] = None) -> str:
        """Obtiene el prompt del sistema adecuado según el tipo de consulta."""
        
        user_role = user_info.get('rol', 'usuario') if user_info else 'usuario'
        user_name = user_info.get('nombre', 'Usuario') if user_info else 'Usuario'
        
        base_prompt = f"""Eres MedGema, un asistente de inteligencia artificial especializado en medicina de laboratorio clínico.
Estás ayudando a {user_name} (rol: {user_role}) en un sistema de laboratorio.

REGLAS FUNDAMENTALES:
1. Proporciona información educativa y profesional
2. Usa los datos clínicos disponibles en el contexto
3. NO realices diagnósticos médicos específicos
4. Siempre recomienda consultar a un médico para decisiones clínicas
5. Sé claro, conciso y preciso
6. Responde en español"""

        prompts = {
            "disease_info": base_prompt + """

ESPECIALIZACIÓN: Información sobre enfermedades
- Explica qué es la enfermedad (definición médica clara)
- Menciona síntomas comunes y factores de riesgo
- Describe cómo se diagnostica (qué pruebas de laboratorio se usan)
- Opciones de tratamiento generales (sin prescribir)
- Prevención y recomendaciones
- NO diagnostiques al usuario. Si menciona síntomas, sugiere consultar a un médico.""",

            "result_interpretation": base_prompt + """

ESPECIALIZACIÓN: Interpretación de resultados de laboratorio
- Analiza los valores usando los rangos de referencia proporcionados
- Explica qué significa cada resultado en lenguaje claro
- Identifica patrones entre múltiples resultados
- Señala valores críticos o preocupantes
- Sugiere qué otros exámenes podrían ser útiles
- Siempre contextualiza: "Esto es una interpretación educativa. Consulta a tu médico.""",

            "biomarker_explanation": base_prompt + """

ESPECIALIZACIÓN: Explicación de biomarcadores
- Explica qué mide el biomarcador y su función en el cuerpo
- Qué significa cuando está alto, bajo o normal
- Relación con enfermedades específicas
- Rangos de referencia típicos
- Usa un tono educativo y accesible""",

            "general_medical": base_prompt + """

ESPECIALIZACIÓN: Consulta médica general
- Responde preguntas generales sobre salud y medicina
- Proporciona información basada en evidencia
- Recomienda estilos de vida saludables cuando aplique
- Siempre deriva a un médico para casos específicos o síntomas
- Sé empático pero profesional""",

            "general_qa": base_prompt + """

ESPECIALIZACIÓN: Preguntas generales
- Responde preguntas médicas generales de forma educativa
- Si no sabes la respuesta, admítelo y sugiere consultar fuentes médicas
- Mantén un tono amable y profesional
- Relaciona la respuesta con el laboratorio clínico cuando sea posible"""
        }
        
        return prompts.get(query_type, prompts["general_qa"])

    def _format_history(self) -> str:
        """Formatea el historial de conversación para incluirlo en el prompt."""
        if not self.conversation_history[:-1]:  # Excluir la última pregunta
            return "No hay historial previo."
        
        lines = []
        for msg in self.conversation_history[-6:-1]:  # Últimos 6 mensajes (excluyendo actual)
            role = "Usuario" if msg["role"] == "user" else "Asistente"
            lines.append(f"{role}: {msg['content'][:150]}")
        
        return "\n".join(lines)

    def clear_history(self):
        """Limpia el historial de conversación."""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Retorna el historial de conversación."""
        return self.conversation_history