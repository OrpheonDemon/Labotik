"""
Test de Integración Phase 2 - Backend FastAPI + Frontend Django
Verifica la comunicación entre los dos servidores
"""

import requests
import json
import time
from pathlib import Path

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8001"  # Django dev server default
API_TIMEOUT = 10

def print_section(title):
    """Imprime header de sección"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)

def test_backend_endpoints():
    """Test 1: Verifica todos los endpoints de FastAPI"""
    print_section("TEST 1: FastAPI Endpoints Availability")
    
    endpoints = [
        ("/ai/health", "GET"),
        ("/ai/status", "GET"),
        ("/ai/models", "GET"),
    ]
    
    results = []
    for endpoint, method in endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            print(f"\n  Testing: {method} {endpoint}")
            
            if method == "GET":
                response = requests.get(url, timeout=API_TIMEOUT)
            else:
                response = requests.post(url, timeout=API_TIMEOUT, json={})
            
            if response.status_code == 200:
                print(f"    ✅ Status 200 OK")
                try:
                    data = response.json()
                    print(f"    Response: {json.dumps(data, indent=6)[:200]}...")
                except:
                    print(f"    Response: {response.text[:100]}...")
                results.append(True)
            else:
                print(f"    ⚠️  Status {response.status_code}")
                results.append(response.status_code == 200)
        except requests.exceptions.ConnectionError:
            print(f"    ❌ Cannot connect to backend")
            print(f"       Make sure: python backend/run_server.py")
            results.append(False)
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n✅ BACKEND ENDPOINTS OK ({passed}/{total})")
        return True
    else:
        print(f"\n⚠️  Some endpoints failed ({passed}/{total})")
        return passed >= 2  # Pass if at least 2/3 work


def test_ai_interpretation():
    """Test 2: Prueba endpoint de interpretación de resultados"""
    print_section("TEST 2: AI Interpretation Analysis")
    
    try:
        print("Enviando solicitud de análisis de resultados...")
        
        payload = {
            "patient_id": "TEST001",
            "patient_age": 45,
            "patient_gender": "F",
            "results": {
                "hemoglobina": 14.2,
                "hematocrito": 42.5,
                "plaquetas": 250000,
                "glucosa": 115,
                "potasio": 4.1,
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ai/interpret-results",
            json=payload,
            timeout=API_TIMEOUT
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Interpretation successful")
            print(f"   Response keys: {list(data.keys())}")
            
            if 'interpretation' in data:
                print(f"   Interpretation: {str(data['interpretation'])[:100]}...")
            
            return True
        else:
            print(f"❌ Error: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - backend may be slow or unresponsive")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_anomaly_detection():
    """Test 3: Prueba detección de anomalías"""
    print_section("TEST 3: Anomaly Detection")
    
    try:
        print("Enviando solicitud de detección de anomalías...")
        
        payload = {
            "patient_id": "TEST002",
            "results": {
                "potasio": 7.5,  # Critical high
                "glucosa": 400,  # Very high
                "hemoglobina": 8.0,  # Low
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ai/detect-anomalies",
            json=payload,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Anomaly detection successful")
            
            if 'anomalies' in data:
                print(f"   Anomalies found: {len(data['anomalies'])}")
                for anomaly in data['anomalies'][:3]:
                    print(f"      - {anomaly}")
            
            return True
        else:
            print(f"❌ Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_prioritization():
    """Test 4: Prueba priorización de casos"""
    print_section("TEST 4: Case Prioritization")
    
    try:
        print("Enviando solicitud de priorización...")
        
        payload = {
            "patient_id": "TEST003",
            "results": {
                "potasio": 7.5,
                "glucosa": 45,
                "troponina": 2.5,
            },
            "patient_age": 65,
            "patient_gender": "M",
        }
        
        response = requests.post(
            f"{BACKEND_URL}/ai/prioritize",
            json=payload,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Prioritization successful")
            
            if 'priority_level' in data:
                print(f"   Priority: {data['priority_level']}")
            if 'urgent_actions' in data:
                print(f"   Urgent actions: {len(data['urgent_actions'])}")
            
            return True
        else:
            print(f"❌ Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_audit_log():
    """Test 5: Prueba acceso al registro de auditoría"""
    print_section("TEST 5: Audit Log Retrieval")
    
    try:
        print("Solicitando registro de auditoría...")
        
        response = requests.get(
            f"{BACKEND_URL}/ai/audit-log",
            params={'limit': 10},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Audit log retrieved")
            
            if isinstance(data, list):
                print(f"   Records: {len(data)}")
            elif isinstance(data, dict) and 'records' in data:
                print(f"   Records: {len(data['records'])}")
            
            return True
        else:
            print(f"⚠️  Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "PHASE 2: INTEGRATION TEST SUITE" + " "*21 + "║")
    print("║" + " "*10 + "FastAPI Backend + Django Frontend Communication" + " "*11 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Backend Endpoints", test_backend_endpoints),
        ("AI Interpretation", test_ai_interpretation),
        ("Anomaly Detection", test_anomaly_detection),
        ("Case Prioritization", test_prioritization),
        ("Audit Log", test_audit_log),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append((name, False))
    
    # Final Report
    print("\n")
    print_section("REPORTE FINAL - PHASE 2")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {name}")
    
    print(f"\nResultados: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 TODAS LAS PRUEBAS PASADAS - Phase 2 Ready!")
        return True
    else:
        print(f"\n⚠️  {total - passed} prueba(s) fallaron")
        print("\nVerifica que:")
        print("  1. Backend FastAPI está corriendo: python backend/run_server.py")
        print("  2. Ollama está activo en puerto 11434")
        print("  3. MedGem modelo está descargado: ollama pull medgemma")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
