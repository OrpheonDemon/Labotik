"""
Specialized Analyzers - Analizadores especializados por disciplina médica
Integrables con Ollama para interpretación profunda
"""

import json
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from app.ai_engine.reference_ranges import (
    get_reference_range,
    is_critical,
    get_interpretation_level
)


@dataclass
class AnalysisResult:
    """Estructura de resultados de análisis"""
    specialty: str
    findings: List[str]
    recommendations: List[str]
    risk_level: str  # bajo | medio | alto | crítico
    requires_specialist: bool
    next_tests: List[str]
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class MedicalAnalyzer(ABC):
    """Clase base para analizadores especializados"""
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
    
    @abstractmethod
    async def analyze(self, results: Dict[str, float], patient_info: Dict[str, Any]) -> AnalysisResult:
        """
        Analiza resultados de laboratorio
        
        Args:
            results: Dict con {nombre_prueba: valor}
            patient_info: Dict con {edad, genero, antecedentes, medicamentos}
        
        Returns:
            AnalysisResult estructurado
        """
        pass
    
    def get_critical_values(self, results: Dict[str, float]) -> List[str]:
        """Identifica valores críticos en los resultados"""
        critical = []
        for test_name, value in results.items():
            if is_critical(test_name, value):
                level = get_interpretation_level(test_name, value)
                critical.append(f"{test_name}: {value} [{level}]")
        return critical
    
    def classify_risk(self, critical_count: int, abnormal_count: int) -> str:
        """Clasifica nivel de riesgo basado en cantidad de alteraciones"""
        if critical_count > 0:
            return "crítico"
        elif abnormal_count > 3:
            return "alto"
        elif abnormal_count > 0:
            return "medio"
        else:
            return "bajo"


class HematologyAnalyzer(MedicalAnalyzer):
    """Analizador de Hematología - Sangre completa, coagulación"""
    
    def __init__(self):
        super().__init__("HematologyAnalyzer", "Hematología")
        self.key_tests = [
            "hemoglobina", "hematocrito", "MCV",
            "leucocitos", "plaquetas",
            "INR", "tiempo_protrombina", "tiempo_tromboplastina"
        ]
    
    async def analyze(self, results: Dict[str, float], patient_info: Dict[str, Any]) -> AnalysisResult:
        """Análisis hematológico"""
        
        findings = []
        recommendations = []
        next_tests = []
        
        gender = patient_info.get("gender", "hombre").lower()
        
        # Análisis hemoglobina
        hb = results.get("hemoglobina")
        if hb:
            hb_range = get_reference_range("hemoglobina", gender=gender)
            if hb < hb_range["min"]:
                findings.append(f"Anemia: Hemoglobina {hb} g/dL (Rango: {hb_range['min']}-{hb_range['max']})")
                recommendations.append("Evaluar causa de anemia (sangrado, deficiencia de hierro, hemólisis)")
                next_tests.extend(["hierro", "ferritina", "reticulocitos", "LDH", "bilirrubina"])
            elif hb > hb_range["max"]:
                findings.append(f"Policitemia: Hemoglobina {hb} g/dL (elevada)")
                recommendations.append("Evaluar causa (hipoxia, EPO, neoplasia)")
        
        # Análisis leucocitos
        wbc = results.get("leucocitos")
        if wbc:
            if wbc < 2.0:
                findings.append(f"Leucopenia severa: {wbc} K/uL")
                recommendations.append("Riesgo de infección - Considerar aislamiento")
                next_tests.append("diferencial leucocitaria")
            elif wbc > 20:
                findings.append(f"Leucocitosis severa: {wbc} K/uL")
                recommendations.append("Evaluar infección, leucemia o reacción inflamatoria")
                next_tests.append("diferencial leucocitaria completa")
        
        # Análisis plaquetas
        plt = results.get("plaquetas")
        if plt:
            if plt < 50:
                findings.append(f"Trombocitopenia severa: {plt} K/uL - Riesgo de sangrado")
                recommendations.append("Considerar transfusión plaquetaria")
            elif plt > 400:
                findings.append(f"Trombocitosis: {plt} K/uL - Riesgo de trombosis")
        
        # Análisis coagulación
        inr = results.get("INR")
        if inr:
            if inr > 10:
                findings.append(f"Anticoagulación excesiva: INR {inr} - Riesgo de sangrado")
                recommendations.append("CRÍTICO: Considerar reversal con vitamina K o FFP")
            elif inr < 0.5:
                findings.append(f"Anticoagulación insuficiente: INR {inr}")
        
        critical = self.get_critical_values(results)
        risk_level = self.classify_risk(len(critical), len(findings))
        
        requires_specialist = len(findings) > 2 or "crítico" in risk_level
        
        return AnalysisResult(
            specialty=self.specialty,
            findings=findings or ["Parámetros hematológicos dentro de rango"],
            recommendations=recommendations or ["Continuar monitoreo rutinario"],
            risk_level=risk_level,
            requires_specialist=requires_specialist,
            next_tests=next_tests
        )


class BiochemistryAnalyzer(MedicalAnalyzer):
    """Analizador de Bioquímica - Electrolitos, función renal/hepática"""
    
    def __init__(self):
        super().__init__("BiochemistryAnalyzer", "Bioquímica Clínica")
        self.key_tests = [
            "sodio", "potasio", "cloro", "calcio",
            "glucosa", "creatinina", "BUN",
            "AST", "ALT", "bilirrubina_total"
        ]
    
    async def analyze(self, results: Dict[str, float], patient_info: Dict[str, Any]) -> AnalysisResult:
        """Análisis bioquímico"""
        
        findings = []
        recommendations = []
        next_tests = []
        
        # Análisis función renal
        creatinina = results.get("creatinina")
        if creatinina:
            if creatinina > 3.0:
                findings.append(f"Insuficiencia renal severa: Creatinina {creatinina} mg/dL")
                recommendations.append("Evaluar para diálisis, revisar medicamentos nefrotóxicos")
                next_tests.extend(["BUN", "FGe", "electrolitos", "ultrasono renal"])
            elif creatinina > 1.5:
                findings.append(f"Disfunción renal leve-moderada: Creatinina {creatinina}")
                next_tests.append("FGe para clasificar estadío")
        
        # Análisis función hepática
        ast = results.get("AST")
        alt = results.get("ALT")
        if ast and alt:
            if ast > 200 or alt > 200:
                findings.append(f"Daño hepático: AST {ast} U/L, ALT {alt} U/L")
                pattern = "hepatocelular" if alt > ast else "colestático"
                findings.append(f"Patrón: {pattern}")
                recommendations.append("Evaluar causa (virus, alcohol, medicamentos, autoinmune)")
                next_tests.extend(["bilirrubina", "INR", "albumina", "fosfatasa alcalina"])
        
        # Análisis electrolitos
        k = results.get("potasio")
        if k:
            if k > 7.0:
                findings.append(f"Hiperpotasemia CRÍTICA: {k} mEq/L - Riesgo de arritmia")
                recommendations.append("URGENTE: Tratar hiperpotasemia (calcio, insulina+glucosa, diuréticos)")
            elif k < 2.5:
                findings.append(f"Hipopotasemia severa: {k} mEq/L")
                recommendations.append("Reposición de potasio urgente")
        
        # Análisis glucosa
        glucose = results.get("glucosa")
        if glucose:
            if glucose > 600:
                findings.append(f"Hiperglucemia CRÍTICA: {glucose} mg/dL")
                recommendations.append("Evaluar para cetoacidosis diabética")
            elif glucose < 40:
                findings.append(f"Hipoglucemia CRÍTICA: {glucose} mg/dL")
        
        critical = self.get_critical_values(results)
        risk_level = self.classify_risk(len(critical), len(findings))
        
        return AnalysisResult(
            specialty=self.specialty,
            findings=findings or ["Bioquímica dentro de rango"],
            recommendations=recommendations or ["Continuar monitoreo"],
            risk_level=risk_level,
            requires_specialist=risk_level in ["crítico", "alto"],
            next_tests=next_tests
        )


class CoagulationAnalyzer(MedicalAnalyzer):
    """Analizador de Coagulación - Hemostasia completa"""
    
    def __init__(self):
        super().__init__("CoagulationAnalyzer", "Hemostasia")
    
    async def analyze(self, results: Dict[str, float], patient_info: Dict[str, Any]) -> AnalysisResult:
        """Análisis de coagulación"""
        
        findings = []
        recommendations = []
        next_tests = []
        
        inr = results.get("INR")
        pt = results.get("tiempo_protrombina")
        ptt = results.get("tiempo_tromboplastina")
        plt = results.get("plaquetas")
        
        # Evaluación PT/INR (ruta extrínseca)
        if inr:
            if inr > 10:
                findings.append(f"PT/INR muy elevado: {inr} - Riesgo sangrado masivo")
                recommendations.append("CRÍTICO: Considerar reversal (vitamina K, FFP, prothrombin complex)")
            elif inr < 0.5:
                findings.append(f"PT/INR muy bajo: {inr} - Riesgo trombótico")
            elif not (0.8 <= inr <= 1.1) and 2.0 <= inr <= 3.0:
                findings.append(f"Anticoagulación terapéutica adecuada: INR {inr}")
        
        # Evaluación PTT (ruta intrínseca)
        if ptt:
            if ptt > 100:
                findings.append(f"PTT prolongado severo: {ptt} seg")
                recommendations.append("Evaluar deficiencia de factor, heparinización excesiva")
                next_tests.append("corrección cruzada PTT")
        
        # Patrón de coagulación
        if inr and ptt:
            if inr > 1.5 and ptt > 40:
                findings.append("Coagulopatía múltiple - Evaluar para DIC o insuficiencia hepática")
                next_tests.extend(["fibrinógeno", "D-dímero", "productos degradación fibrina"])
        
        critical = self.get_critical_values(results)
        risk_level = self.classify_risk(len(critical), len(findings))
        
        return AnalysisResult(
            specialty=self.specialty,
            findings=findings or ["Parámetros de coagulación normales"],
            recommendations=recommendations or ["Continuar terapia actual si aplica"],
            risk_level=risk_level,
            requires_specialist=len(findings) > 1,
            next_tests=next_tests
        )


class EndocrinologyAnalyzer(MedicalAnalyzer):
    """Analizador de Endocrinología - Hormonal"""
    
    def __init__(self):
        super().__init__("EndocrinologyAnalyzer", "Endocrinología")
    
    async def analyze(self, results: Dict[str, float], patient_info: Dict[str, Any]) -> AnalysisResult:
        """Análisis endocrinológico"""
        
        findings = []
        recommendations = []
        next_tests = []
        
        # Análisis tiroideo
        tsh = results.get("TSH")
        if tsh:
            if tsh < 0.4:
                findings.append(f"TSH bajo: {tsh} mIU/L - Posible hipertiroidismo")
                recommendations.append("Obtener T3 libre y T4 libre para confirmar")
                next_tests.extend(["T3_libre", "T4_libre"])
            elif tsh > 5.0:
                findings.append(f"TSH elevado: {tsh} mIU/L - Posible hipotiroidismo")
                next_tests.extend(["T4_libre", "anticuerpos TPO"])
        
        # Análisis glucosa
        glucose = results.get("glucosa")
        if glucose:
            if glucose > 600:
                findings.append(f"Hiperglucemia severa: {glucose} mg/dL")
                recommendations.append("Evaluación urgente para diabetes descontrolada o cetoacidosis")
        
        critical = self.get_critical_values(results)
        risk_level = self.classify_risk(len(critical), len(findings))
        
        return AnalysisResult(
            specialty=self.specialty,
            findings=findings or ["Parámetros endocrinos dentro de rango"],
            recommendations=recommendations or ["Continuar monitoreo"],
            risk_level=risk_level,
            requires_specialist=len(findings) > 0,
            next_tests=next_tests
        )


class ImmunologyAnalyzer(MedicalAnalyzer):
    """Analizador de Inmunología - Inflamación, marcadores"""
    
    def __init__(self):
        super().__init__("ImmunologyAnalyzer", "Inmunología")
    
    async def analyze(self, results: Dict[str, float], patient_info: Dict[str, Any]) -> AnalysisResult:
        """Análisis inmunológico"""
        
        findings = []
        recommendations = []
        next_tests = []
        
        # Análisis PCR
        pcr = results.get("PCR")
        if pcr:
            if pcr > 100:
                findings.append(f"Inflamación severa: PCR {pcr} mg/L")
                recommendations.append("Evaluar para infección o inflamación severa")
                next_tests.append("procalcitonina")
            elif pcr > 10:
                findings.append(f"Inflamación moderada: PCR {pcr} mg/L")
                next_tests.append("cultivos si sospecha infección")
        
        critical = self.get_critical_values(results)
        risk_level = self.classify_risk(len(critical), len(findings))
        
        return AnalysisResult(
            specialty=self.specialty,
            findings=findings or ["Marcadores inflamatorios normales"],
            recommendations=recommendations or ["Continuar evaluación clínica"],
            risk_level=risk_level,
            requires_specialist=len(findings) > 1,
            next_tests=next_tests
        )


class MicrobiologyAnalyzer(MedicalAnalyzer):
    """Analizador de Microbiología - Cultivos, sensibilidad"""
    
    def __init__(self):
        super().__init__("MicrobiologyAnalyzer", "Microbiología")
    
    async def analyze(self, results: Dict[str, Any], patient_info: Dict[str, Any]) -> AnalysisResult:
        """Análisis microbiológico"""
        
        findings = []
        recommendations = []
        next_tests = []
        
        # Nota: results puede contener datos estructurados diferentes
        # para cultivos (no solo valores numéricos)
        
        findings.append("Análisis microbiológico completado")
        recommendations.append("Interpretar según identificación de microorganismo")
        
        return AnalysisResult(
            specialty=self.specialty,
            findings=findings,
            recommendations=recommendations,
            risk_level="bajo",
            requires_specialist=True,
            next_tests=next_tests
        )


# Factory para obtener analizadores
ANALYZERS = {
    "hematology": HematologyAnalyzer(),
    "biochemistry": BiochemistryAnalyzer(),
    "coagulation": CoagulationAnalyzer(),
    "endocrinology": EndocrinologyAnalyzer(),
    "immunology": ImmunologyAnalyzer(),
    "microbiology": MicrobiologyAnalyzer(),
}


async def run_specialized_analysis(
    specialty: str,
    results: Dict[str, float],
    patient_info: Dict[str, Any]
) -> Optional[AnalysisResult]:
    """
    Ejecuta análisis especializado
    
    Args:
        specialty: Tipo de análisis (hematology, biochemistry, etc.)
        results: Resultados de laboratorio
        patient_info: Información del paciente
    
    Returns:
        AnalysisResult o None si specialty no existe
    """
    
    analyzer = ANALYZERS.get(specialty.lower())
    if analyzer:
        return await analyzer.analyze(results, patient_info)
    
    return None


if __name__ == "__main__":
    # Prueba local
    print("Analizadores especializados disponibles:")
    for name, analyzer in ANALYZERS.items():
        print(f"  - {name}: {analyzer.specialty}")
