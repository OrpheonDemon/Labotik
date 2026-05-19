import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    creation_flags = 0
    if sys.platform == "win32":
        # 0x08000000 corresponds to CREATE_NO_WINDOW
        creation_flags = 0x08000000

    # Start FastAPI backend (run uvicorn as a python module to use the same interpreter environment)
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"]
    # Start Django frontend
    frontend_cmd = [sys.executable, "manage.py", "runserver", "3000"]

    pids = {}

    try:
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=backend_dir,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        pids["backend"] = backend_proc.pid
    except Exception as e:
        with open(os.path.join(base_dir, "error_start.log"), "a") as log:
            log.write(f"Error starting backend: {e}\n")

    try:
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        pids["frontend"] = frontend_proc.pid
    except Exception as e:
        with open(os.path.join(base_dir, "error_start.log"), "a") as log:
            log.write(f"Error starting frontend: {e}\n")

    # Store active PIDs to stop them clean later
    pid_file = os.path.join(base_dir, ".labotik_pids")
    with open(pid_file, "w") as f:
        for name, pid in pids.items():
            f.write(f"{name}:{pid}\n")

if __name__ == "__main__":
    main()
