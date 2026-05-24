from typing import Any


class LaboratoryRulesEngine:
    DEFAULT_THRESHOLDS = {
        'hemoglobina': {'min': 12.0, 'max': 17.5, 'unidad': 'g/dl'},
        'vcm': {'min': 80, 'max': 100, 'unidad': 'fl'},
        'ferritina': {'min': 15, 'max': 150, 'unidad': 'ng/ml'},
        'potasio': {'min': 3.5, 'max': 5.2, 'unidad': 'mmol/l'},
        'sodio': {'min': 135, 'max': 145, 'unidad': 'mmol/l'},
    }

    def evaluate_result(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        findings = []
        name = (result.get('nombre') or '').lower()
        value = result.get('resultado')
        unidad = (result.get('unidad') or '').lower()

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            findings.append({
                'tipo': 'inconsistencia',
                'mensaje': f"Valor no numérico para {result.get('nombre')}: {value}"
            })
            return findings

        # Reglas configurables básicas
        for key, threshold in self.DEFAULT_THRESHOLDS.items():
            if key in name:
                if numeric_value < threshold['min']:
                    findings.append({
                        'tipo': 'fuera_de_rango',
                        'mensaje': f"{result.get('nombre')} bajo ({numeric_value} {unidad}). Compatible con déficit correspondiente." 
                    })
                elif numeric_value > threshold['max']:
                    findings.append({
                        'tipo': 'fuera_de_rango',
                        'mensaje': f"{result.get('nombre')} alto ({numeric_value} {unidad}). Sugestivo de alteración clínica relevante." 
                    })

        if unidad and unidad not in ['g/dl', 'fl', 'ng/ml', 'mmol/l', 'mg/dl', 'l', '%', 'porcentaje', 'ug/dl', 'u/l']:
            findings.append({
                'tipo': 'unidad_incorrecta',
                'mensaje': f"Unidad inusual para {result.get('nombre')}: {unidad}. Verificar captura." 
            })

        if numeric_value < 0:
            findings.append({
                'tipo': 'improbable',
                'mensaje': f"Valor improbable para {result.get('nombre')}: {numeric_value}. Puede ser error de ingreso o muestra alterada." 
            })

        return findings
