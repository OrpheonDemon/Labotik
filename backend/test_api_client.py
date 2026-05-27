import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_active_user

# override dependency
app.dependency_overrides[get_current_active_user] = lambda: {"rol": "administrador", "user": type('obj', (object,), {'id_administrador': 'admin1'})()}

client = TestClient(app)

print("Testing /pacientes?limit=5")
response = client.get("/pacientes?limit=5")
print("PACIENTES", response.status_code)
try:
    print(response.json())
except:
    print(response.text)

print("Testing /laboratoristas?limit=5")
response = client.get("/laboratoristas?limit=5")
print("LABORATORISTAS", response.status_code)
try:
    print(response.json())
except:
    print(response.text)
