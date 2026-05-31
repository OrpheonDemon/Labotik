"""
Servicio de Auditoría - Registro de todas las decisiones y análisis de IA
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)


class AuditService:
    """Servicio de auditoría para registrar decisiones de IA."""

    def __init__(self, audit_file: str = "backend/ai_audit_log.json"):
        self.audit_file = audit_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Asegura que el archivo de auditoría existe."""
        if not os.path.exists(self.audit_file):
            os.makedirs(os.path.dirname(self.audit_file) or ".", exist_ok=True)
            with open(self.audit_file, 'w') as f:
                json.dump([], f)

    def log_analysis(
        self,
        analysis_type: str,
        user_email: str,
        patient_id: str,
        input_data: Dict[str, Any],
        ai_output: Dict[str, Any],
        confidence: float = 0.8,
        approved: bool = False
    ) -> Dict[str, Any]:
        """Registra un análisis de IA en el log de auditoría."""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": analysis_type,
            "usuario": user_email,
            "paciente_id": patient_id,
            "confianza": confidence,
            "aprobado": approved,
            "entrada": input_data,
            "salida": ai_output,
            "id_registro": self._generate_audit_id()
        }

        try:
            # Leer log existente
            with open(self.audit_file, 'r') as f:
                logs = json.load(f) if os.path.getsize(self.audit_file) > 0 else []

            # Agregar nueva entrada
            logs.append(entry)

            # Guardar actualizado
            with open(self.audit_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

            logger.info(f"Audit log entry added: {entry['id_registro']}")
            return entry
        except Exception as e:
            logger.error(f"Error logging analysis: {e}")
            return {"error": str(e)}

    def get_audit_logs(
        self,
        limit: int = 100,
        analysis_type: str = None,
        approved_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtiene registros de auditoría."""
        
        try:
            with open(self.audit_file, 'r') as f:
                logs = json.load(f) if os.path.getsize(self.audit_file) > 0 else []

            # Filtrar si es necesario
            if analysis_type:
                logs = [l for l in logs if l.get("tipo") == analysis_type]
            if approved_only:
                logs = [l for l in logs if l.get("aprobado", False)]

            # Devolver últimas N entradas
            return logs[-limit:]
        except Exception as e:
            logger.error(f"Error reading audit logs: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Calcula estadísticas del log de auditoría."""
        
        try:
            with open(self.audit_file, 'r') as f:
                logs = json.load(f) if os.path.getsize(self.audit_file) > 0 else []

            if not logs:
                return {
                    "total_analisis": 0,
                    "aprobados": 0,
                    "confianza_promedio": 0,
                    "tipos_analisis": {}
                }

            total = len(logs)
            approved = sum(1 for l in logs if l.get("aprobado", False))
            avg_confidence = sum(l.get("confianza", 0) for l in logs) / total if total > 0 else 0

            types = {}
            for log in logs:
                t = log.get("tipo", "unknown")
                types[t] = types.get(t, 0) + 1

            return {
                "total_analisis": total,
                "aprobados": approved,
                "pendientes": total - approved,
                "confianza_promedio": round(avg_confidence, 3),
                "tipos_analisis": types
            }
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def approve_analysis(self, audit_id: str) -> bool:
        """Marca un análisis como aprobado."""
        
        try:
            with open(self.audit_file, 'r') as f:
                logs = json.load(f) if os.path.getsize(self.audit_file) > 0 else []

            for log in logs:
                if log.get("id_registro") == audit_id:
                    log["aprobado"] = True
                    break

            with open(self.audit_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

            logger.info(f"Analysis {audit_id} approved")
            return True
        except Exception as e:
            logger.error(f"Error approving analysis: {e}")
            return False

    @staticmethod
    def _generate_audit_id() -> str:
        """Genera ID único para cada registro de auditoría."""
        import uuid
        return str(uuid.uuid4())[:8]
