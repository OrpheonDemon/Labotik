from typing import Any
from .laboratory_rules_engine import LaboratoryRulesEngine


class AnomalyDetector:
    def __init__(self, rules_engine: LaboratoryRulesEngine | None = None):
        self.rules_engine = rules_engine or LaboratoryRulesEngine()

    def detect(self, results: list[dict]) -> list[dict[str, Any]]:
        findings = []
        for item in results:
            findings.extend(self.rules_engine.evaluate_result(item))

        # Detect duplicates and inconsistencias generales
        seen = set()
        for item in results:
            key = (item.get('nombre'), str(item.get('resultado')))
            if key in seen:
                findings.append({
                    'tipo': 'duplicado',
                    'mensaje': f"Resultado duplicado detectado para {item.get('nombre')}"
                })
            else:
                seen.add(key)

        return findings
