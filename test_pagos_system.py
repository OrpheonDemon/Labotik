#!/usr/bin/env python
"""
Script de diagnóstico para verificar el sistema de pagos de Labotik.
Este script verifica:
1. Conexión con el backend
2. Endpoints de pagos disponibles
3. Datos de prueba en la base de datos
"""

import requests
import json
import sys

API_URL = "http://127.0.0.1:8000"

def test_backend_connection():
    """Verifica que el backend esté corriendo"""
    try:
        response = requests.get(f"{API_URL}/test")
        if response.status_code == 200:
            print("✅ Backend conectado correctamente")
            return True
        else:
            print(f"❌ Error conectando al backend: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ No se pudo conectar con el backend. ¿Está corriendo el servidor?")
        return False

def test_auth_endpoint():
    """Verifica que se pueda obtener un token de prueba"""
    try:
        # Intentar login con credenciales de prueba
        response = requests.post(f"{API_URL}/auth/login/access-token", data={
            "username": "admin@labotik.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token obtenido: {data['access_token'][:20]}...")
            return data['access_token']
        else:
            print(f"⚠️ No se pudo obtener token (esto es normal si no hay usuarios): {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Error en auth: {e}")
        return None

def test_pagos_endpoints(token=None):
    """Verifica los endpoints de pagos"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    endpoints = [
        ("GET /pagos/", "Lista de pagos"),
        ("GET /pagos/solicitudes/no-pagadas", "Solicitudes no pagadas"),
        ("GET /facturas/", "Lista de facturas"),
    ]
    
    print("\n🔍 Verificando endpoints de pagos:")
    for endpoint, description in endpoints:
        try:
            method, path = endpoint.split(" ", 1)
            url = f"{API_URL}{path}?skip=0&limit=5"
            
            if method == "GET":
                response = requests.get(url, headers=headers)
                status = response.status_code
                if status == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else "?"
                    print(f"  ✅ {description}: {status} ({count} items)")
                elif status == 401:
                    print(f"  ⚠️ {description}: {status} (Requiere autenticación)")
                else:
                    print(f"  ❌ {description}: {status}")
        except Exception as e:
            print(f"  ❌ {description}: Error - {e}")

def test_dashboard_files():
    """Verifica que los archivos del dashboard existan"""
    import os
    
    files_to_check = [
        "frontend/templates/dashboard/paciente_dashboard.html",
        "frontend/templates/dashboard/recepcionista_dashboard.html",
    ]
    
    print("\n📁 Verificando archivos del dashboard:")
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} no existe")

def check_pagos_section_in_dashboard():
    """Verifica que la sección de pagos esté en los dashboards"""
    print("\n🔍 Verificando sección de pagos en dashboards:")
    
    dashboards = [
        ("paciente_dashboard.html", "Pagos"),
        ("recepcionista_dashboard.html", "Pagos"),
    ]
    
    for file_name, search_term in dashboards:
        file_path = f"frontend/templates/dashboard/{file_name}"
        if not os.path.exists(file_path):
            print(f"  ❌ {file_name} no existe")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar sección de pagos
        has_section = 'id="pagos"' in content or "id='pagos'" in content
        has_menu = 'navigateMenu(event, \'pagos\'' in content or 'navigateMenu(event, "pagos"' in content
        has_script = 'cargarSeccionPagos' in content
        
        if has_section and has_menu and has_script:
            print(f"  ✅ {file_name}: Sección de pagos completa")
        else:
            print(f"  ⚠️ {file_name}:")
            if not has_section:
                print(f"     - Falta sección HTML con id='pagos'")
            if not has_menu:
                print(f"     - Falta botón de menú para pagos")
            if not has_script:
                print(f"     - Faltan funciones JavaScript de pagos")

def main():
    print("=" * 60)
    print("🏥 DIAGNÓSTICO DEL SISTEMA DE PAGOS - LABOTIK")
    print("=" * 60)
    
    # 1. Verificar conexión
    if not test_backend_connection():
        print("\n💡 Solución: Inicia el backend con 'python backend/run_server.py'")
        return
    
    # 2. Verificar autenticación
    token = test_auth_endpoint()
    
    # 3. Verificar endpoints
    test_pagos_endpoints(token)
    
    # 4. Verificar archivos
    test_dashboard_files()
    
    # 5. Verificar sección de pagos
    check_pagos_section_in_dashboard()
    
    print("\n" + "=" * 60)
    print("✅ Diagnóstico completado")
    print("=" * 60)

if __name__ == "__main__":
    import os
    main()