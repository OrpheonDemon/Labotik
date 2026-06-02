import requests
import json

BASE = "http://127.0.0.1:8000"

# 1. Login to get token
print("=== LOGGING IN ===")
login_data = {"email": "admin@labotik.com", "password": "admin123"}
try:
    r = requests.post(f"{BASE}/auth/login", json=login_data, timeout=10)
    print(f"Login: {r.status_code}")
    if r.status_code == 200:
        token = r.json().get("access_token", "")
        print(f"Token obtained: {token[:30]}...")
    else:
        print(f"Login response: {r.text[:200]}")
        token = None
except Exception as e:
    print(f"Login error: {e}")
    token = None

headers = {"Authorization": f"Bearer {token}"} if token else {}

# 2. Test all key endpoints
endpoints = [
    ("GET", "/pacientes/?limit=1"),
    ("GET", "/medicos/?limit=1"),
    ("GET", "/laboratoristas/?limit=1"),
    ("GET", "/administradores/?limit=1"),
    ("GET", "/pruebas/?limit=1"),
    ("GET", "/solicitudes/?limit=1"),
    ("GET", "/resultados/?limit=1"),
    ("GET", "/reportes/?limit=1"),
    ("GET", "/pagos/?limit=1"),
    ("GET", "/areas/?limit=1"),
    ("GET", "/facturas/?limit=1"),
    ("GET", "/ai/status"),
]

print("\n=== TESTING ENDPOINTS ===")
for method, path in endpoints:
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{path}", headers=headers, timeout=10)
        else:
            r = requests.post(f"{BASE}{path}", headers=headers, timeout=10)
        status = r.status_code
        symbol = "OK" if status < 400 else "FAIL"
        print(f"  [{status}] {symbol} {method} {path}")
        if status >= 400:
            print(f"       Error: {r.text[:200]}")
    except Exception as e:
        print(f"  [ERR] {method} {path}: {e}")