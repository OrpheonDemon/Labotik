import os
import sys
import subprocess

def free_port(port):
    if sys.platform == "win32":
        try:
            # Find PIDs using netstat
            output = subprocess.check_output(f'netstat -aon | findstr ":{port}"', shell=True).decode()
            lines = output.strip().split("\n")
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:
                    addr = parts[1]
                    state = parts[3]
                    pid = parts[4]
                    # Ensure it is the listening server on the target port
                    if state == "LISTENING" and f":{port}" in addr:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"Liberado puerto {port} (Proceso PID {pid} terminado)")
        except Exception:
            pass

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pid_file = os.path.join(base_dir, ".labotik_pids")

    print("Deteniendo servidores de Labotik...")

    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            lines = f.readlines()
        
        for line in lines:
            if ":" in line:
                name, pid_str = line.strip().split(":")
                try:
                    pid = int(pid_str)
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        import signal
                        os.kill(pid, signal.SIGTERM)
                    print(f"Detenido {name} (PID {pid})")
                except Exception:
                    pass
        try:
            os.remove(pid_file)
        except:
            pass
    
    # Run netstat cleanups to ensure no orphan reloaders are keeping the ports busy
    free_port(8000)
    free_port(3000)
    print("Todos los servidores se han detenido exitosamente.")

if __name__ == "__main__":
    main()
