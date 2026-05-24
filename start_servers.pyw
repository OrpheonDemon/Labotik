import os
import sys
import subprocess
import urllib.request
import urllib.error
import time
import json

def check_ollama_running():
    """Verifica si Ollama está ejecutándose en localhost:11434"""
    try:
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, Exception):
        return False

def start_ollama():
    """Inicia el servicio Ollama"""
    print("🚀 Iniciando Ollama...")
    try:
        # Inicia Ollama en background
        if sys.platform == "win32":
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Esperar a que Ollama esté listo
        max_retries = 30
        for i in range(max_retries):
            if check_ollama_running():
                print("✅ Ollama iniciado correctamente")
                return True
            time.sleep(1)
            print(f"⏳ Esperando Ollama... ({i+1}/{max_retries})")
        
        print("❌ Ollama no responde después de 30 segundos")
        return False
    except FileNotFoundError:
        print("❌ Ollama no está instalado. Descárgalo desde: https://ollama.ai")
        return False
    except Exception as e:
        print(f"❌ Error iniciando Ollama: {e}")
        return False

def verify_model_available():
    """Verifica si el modelo medgemma está disponible"""
    try:
        with urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2) as response:
            data = json.loads(response.read().decode())
            models = [m.get('name', '').split(':')[0] for m in data.get('models', [])]
            return 'medgemma' in models
    except:
        return False

def pull_model():
    """Descarga el modelo medgemma si no está disponible"""
    if verify_model_available():
        print("✅ Modelo medgemma ya está disponible")
        return True
    
    print("📦 Descargando modelo medgemma (esto puede tomar varios minutos)...")
    try:
        result = subprocess.run(
            ['ollama', 'pull', 'medgemma'],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode == 0:
            print("✅ Modelo medgemma descargado correctamente")
            return True
        else:
            print(f"⚠️  Advertencia al descargar modelo: {result.stderr}")
            return True  # Continuar de todas formas
    except Exception as e:
        print(f"⚠️  Error descargando modelo: {e}")
        return True  # Continuar de todas formas

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    creation_flags = 0
    if sys.platform == "win32":
        # 0x08000000 corresponds to CREATE_NO_WINDOW
        creation_flags = 0x08000000

    print("=" * 50)
    print("🔧 INICIANDO LABORATORIO CLÍNICO")
    print("=" * 50)

    # 1. Verificar y iniciar Ollama
    if not check_ollama_running():
        if not start_ollama():
            print("⚠️  Continuando sin Ollama (algunas funciones no funcionarán)")
    else:
        print("✅ Ollama ya está corriendo")

    # 2. Verificar modelo
    pull_model()

    # Start FastAPI backend (run uvicorn as a python module to use the same interpreter environment)
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"]
    # Start Django frontend
    frontend_cmd = [sys.executable, "manage.py", "runserver", "3000"]

    pids = {}

    try:
        print("\n🚀 Iniciando Backend (FastAPI)...")
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        pids["backend"] = backend_proc.pid
        print("✅ Backend iniciado en http://localhost:8000")
    except Exception as e:
        with open(os.path.join(base_dir, "error_start.log"), "a") as log:
            log.write(f"Error starting backend: {e}\n")
        print(f"❌ Error iniciando backend: {e}")

    try:
        print("🚀 Iniciando Frontend (Django)...")
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        pids["frontend"] = frontend_proc.pid
        print("✅ Frontend iniciado en http://localhost:3000")
    except Exception as e:
        with open(os.path.join(base_dir, "error_start.log"), "a") as log:
            log.write(f"Error starting frontend: {e}\n")
        print(f"❌ Error iniciando frontend: {e}")

    print("\n" + "=" * 50)
    print("🎉 LABORATORIO CLÍNICO INICIADO")
    print("=" * 50)
    print("📱 Accede a: http://localhost:3000")
    print("🤖 API en: http://localhost:8000")
    print("🦙 Ollama en: http://localhost:11434")
    print("=" * 50)

    # Store active PIDs to stop them clean later
    pid_file = os.path.join(base_dir, ".labotik_pids")
    with open(pid_file, "w") as f:
        for name, pid in pids.items():
            f.write(f"{name}:{pid}\n")

if __name__ == "__main__":
    main()
