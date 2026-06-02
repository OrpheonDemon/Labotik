import requests, json, base64

BASE = 'http://127.0.0.1:8000'

# Login as patient
data = {'username': 'rotherickcalderon@gmail.com', 'password': '123456'}
r = requests.post(f'{BASE}/auth/login/access-token', data=data, timeout=10)
print(f'Login: {r.status_code}')
if r.status_code == 200:
    token = r.json()['access_token']
    # Decode JWT
    parts = token.split('.')
    padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
    try:
        payload = json.loads(base64.b64decode(padded))
        print(f'JWT payload: {json.dumps(payload, indent=2)}')
    except Exception as e:
        print(f'JWT decode error: {e}')
        payload = {}
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Try by sub (email)
    sub = payload.get('sub', '')
    print(f'\n--- Try fetch by sub/email: {sub} ---')
    r2 = requests.get(f'{BASE}/pacientes/{sub}', headers=headers, timeout=10)
    print(f'Status: {r2.status_code}')
    if r2.status_code == 200:
        print(f'Data keys: {list(r2.json().keys())}')
    else:
        print(f'Error: {r2.text[:200]}')
    
    # Try by id_usuario  
    uid = payload.get('id_usuario')
    print(f'\n--- Try fetch by id_usuario: {uid} ---')
    if uid:
        r3 = requests.get(f'{BASE}/pacientes/{uid}', headers=headers, timeout=10)
        print(f'Status: {r3.status_code}')
        if r3.status_code == 200:
            data = r3.json()
            print(f'Data keys: {list(data.keys())}')
            print(f'nombre: {data.get("nombre")}')
            print(f'apellido_paterno: {data.get("apellido_paterno")}')
        else:
            print(f'Error: {r3.text[:200]}')
    
    # Try by-email endpoint
    print(f'\n--- Try pacientes/by-email ---')
    r4 = requests.get(f'{BASE}/pacientes/by-email?email={sub}', headers=headers, timeout=10)
    print(f'Status: {r4.status_code}')
    if r4.status_code == 200:
        d = r4.json()
        print(f'Data keys: {list(d.keys()) if isinstance(d, dict) else "list"}')
        if isinstance(d, dict):
            print(f'nombre: {d.get("nombre")}')
    else:
        print(f'Error: {r4.text[:200]}')
else:
    print(f'Login failed: {r.text[:200]}')