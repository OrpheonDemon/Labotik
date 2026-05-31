import os
import sys
import subprocess
import time

def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

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

    # Start Ollama IA Engine
    ollama_cmd = "ollama serve"
    # Start FastAPI backend (run uvicorn as a python module to use the same interpreter environment)
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"]
    # Start Django frontend
    frontend_cmd = [sys.executable, "manage.py", "runserver", "3000"]

    pids = {}

    # Check if Ollama is already running
    ollama_running = False
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 11434))
        ollama_running = (result == 0)
        sock.close()
    except:
        pass

    if ollama_running:
        print("\n✅ Ollama ya está corriendo en http://localhost:11434")
        print("   (Reutilizando instancia existente)")
    else:
        try:
            print("\n🚀 Iniciando Ollama (IA Engine)...")
            ollama_proc = subprocess.Popen(
                ollama_cmd,
                shell=True,
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            pids["ollama"] = ollama_proc.pid
            print("✅ Ollama iniciado en http://localhost:11434")
            # Wait a bit for Ollama to start
            time.sleep(2)
        except Exception as e:
            with open(os.path.join(base_dir, "error_start.log"), "a") as log:
                log.write(f"Error starting ollama: {e}\n")
            print(f"❌ Error iniciando Ollama: {e}")
            print("   NOTA: Asegúrate de haber instalado Ollama primero")
            print("   Descargar desde: https://ollama.ai/download")

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
        print("\n🚀 Iniciando Frontend (Django)...")
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
    print("🦙 Ollama IA:  http://localhost:11434")
    print("📱 Accede a:   http://localhost:3000")
    print("🤖 API en:     http://localhost:8000")
    print("=" * 50)

    # Store active PIDs to stop them clean later
    pid_file = os.path.join(base_dir, ".labotik_pids")
    with open(pid_file, "w") as f:
        for name, pid in pids.items():
            f.write(f"{name}:{pid}\n")

if __name__ == "__main__":
    main()
