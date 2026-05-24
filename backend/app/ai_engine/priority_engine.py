from typing import Any


class PriorityEngine:
    PRIORITY_BUCKETS = [
        ('crítico', 90),
        ('urgente', 70),
        ('revisión recomendada', 40),
        ('normal', 0)
    ]

    def score(self, results: list[dict], patient_info: dict | None = None) -> dict[str, Any]:
        score = 0
        alerts = []

        for item in results:
            if item.get('es_anormal'):
                score += 20
                alerts.append(f"Alteración detectada en {item.get('nombre')}")
            try:
                value = float(item.get('resultado'))
                if item.get('unidad', '').lower() in ['%', 'percent', 'porcentaje'] and value > 80:
                    score += 15
                if item.get('unidad', '').lower() in ['g/dl', 'g/l'] and value < 11:
                    score += 15
            except (TypeError, ValueError):
                continue

        if patient_info:
            age = patient_info.get('edad')
            sex = patient_info.get('sexo')
            if age and age >= 65:
                score += 10
            if sex and sex.lower() == 'mujer':
                score += 5

        score = min(score, 100)
        category = self._category(score)
        return {
            'priority': category,
            'score': score,
            'alerts': list(dict.fromkeys(alerts))
        }

    def _category(self, score: int) -> str:
        for label, threshold in self.PRIORITY_BUCKETS:
            if score >= threshold:
                return label
        return 'normal'
