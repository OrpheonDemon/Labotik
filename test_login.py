import requests

url = "http://127.0.0.1:8000/auth/login/access-token"
data = {
    "username": "medico@labotik.com",
    "password": "password"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
