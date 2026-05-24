#!/usr/bin/env python3
"""
Script para verificar si Ollama está instalado y el modelo medgemma está disponible.
Si no está instalado, proporciona instrucciones para instalarlo.
"""

import subprocess
import sys
import json
import urllib.request
import urllib.error
import time
from pathlib import Path

def check_ollama_running():
    """Verifica si Ollama está ejecutándose en localhost:11434"""
    try:
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2) as response:
            if response.status == 200:
                return True
    except (urllib.error.URLError, Exception):
        pass
    return False

def get_available_models():
    """Obtiene lista de modelos disponibles en Ollama"""
    try:
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2) as response:
            data = json.loads(response.read().decode())
            models = [m.get('name', '').split(':')[0] for m in data.get('models', [])]
            return models
    except (urllib.error.URLError, Exception):
        return []

def pull_model(model_name):
    """Descarga un modelo de Ollama"""
    print(f"\n📦 Descargando modelo {model_name}...")
    try:
        result = subprocess.run(
            ['ollama', 'pull', model_name],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode == 0:
            print(f"✅ Modelo {model_name} descargado correctamente")
            return True
        else:
            print(f"❌ Error descargando {model_name}: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Ollama no está instalado")
        return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  Timeout descargando {model_name}")
        return False

def main():
    print("🔍 Verificando configuración de Ollama y medgemma...\n")
    
    # 1. Verificar si Ollama está instalado
    print("1️⃣  Verificando instalación de Ollama...")
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ Ollama instalado: {result.stdout.strip()}")
        else:
            print("   ❌ Ollama no está disponible")
            print_install_instructions()
            sys.exit(1)
    except FileNotFoundError:
        print("   ❌ Ollama no está instalado")
        print_install_instructions()
        sys.exit(1)
    
    # 2. Verificar si Ollama está corriendo
    print("\n2️⃣  Verificando si Ollama está ejecutándose...")
    if check_ollama_running():
        print("   ✅ Ollama está corriendo en http://localhost:11434")
    else:
        print("   ⚠️  Ollama no está corriendo")
        print("   📝 Inicia Ollama con: ollama serve")
        print("   ⏳ Esperando a que se inicie...")
        
        # Intentar iniciar Ollama
        try:
            print("\n   🚀 Iniciando Ollama...")
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Esperar a que se inicie
            for i in range(30):
                time.sleep(1)
                if check_ollama_running():
                    print("   ✅ Ollama iniciado correctamente")
                    break
                sys.stdout.write(f"\r   ⏳ Esperando... ({i+1}/30)")
                sys.stdout.flush()
            else:
                print("\n   ❌ Ollama no pudo iniciar")
                sys.exit(1)
        except Exception as e:
            print(f"   ❌ Error iniciando Ollama: {e}")
            sys.exit(1)
    
    # 3. Verificar modelo medgemma
    print("\n3️⃣  Verificando modelo medgemma...")
    available_models = get_available_models()
    
    if 'medgemma' in available_models:
        print("   ✅ medgemma está disponible")
    else:
        print(f"   ⚠️  medgemma no encontrado")
        print(f"   📦 Modelos disponibles: {', '.join(available_models) if available_models else 'ninguno'}")
        
        print("\n   🔄 Descargando medgemma (esto puede tomar varios minutos)...")
        if pull_model('medgemma'):
            print("   ✅ medgemma descargado correctamente")
        else:
            print("   ❌ No se pudo descargar medgemma")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ Verificación completada correctamente")
    print("="*60)
    print("\n📋 Configuración actual:")
    print("   • Ollama: DISPONIBLE")
    print("   • Modelo medgemma: DISPONIBLE")
    print("   • URL API: http://localhost:11434/api")
    print("\n🚀 El sistema está listo para iniciar el Asistente Clínico IA")

def print_install_instructions():
    """Imprime instrucciones de instalación de Ollama"""
    print("\n" + "="*60)
    print("📥 INSTRUCCIONES DE INSTALACIÓN DE OLLAMA")
    print("="*60)
    print("""
Para Windows:
  1. Descargar desde: https://ollama.ai/download/windows
  2. Ejecutar el instalador
  3. Reiniciar la terminal
  4. Verificar: ollama --version

Para macOS:
  1. Descargar desde: https://ollama.ai/download/mac
  2. Ejecutar el instalador
  3. Verificar: ollama --version

Para Linux:
  curl https://ollama.ai/install.sh | sh

Después de instalar:
  1. Inicia Ollama: ollama serve
  2. En otra terminal: ollama pull medgemma
  3. Vuelve a ejecutar este script
""")
    print("="*60)

if __name__ == '__main__':
    main()
