import requests

login_data = {"username": "rotherickcalderon.admin@labotik.com", "password": "admin"}
r = requests.post("http://127.0.0.1:8000/auth/login/access-token", data=login_data)
if r.status_code == 200:
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test pacientes
    rp = requests.get("http://127.0.0.1:8000/pacientes?skip=0&limit=5", headers=headers)
    print("PACIENTES STATUS:", rp.status_code)
    try:
        print("PACIENTES RESULT:", rp.json())
    except:
        pass
    
    # Test laboratoristas
    rl = requests.get("http://127.0.0.1:8000/laboratoristas?skip=0&limit=5", headers=headers)
    print("LABORATORISTAS STATUS:", rl.status_code)
    try:
        print("LABORATORISTAS RESULT:", rl.json())
    except:
        pass
else:
    print("Login failed", r.status_code, r.text)
