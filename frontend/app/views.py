import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm

# URL del backend FastAPI
BACKEND_URL = "http://127.0.0.1:8000"

def home_view(request):
    """Vista de la página de inicio o dashboard básico."""
    token = request.session.get('access_token')
    email = request.session.get('user_email')
    
    if not token:
        return redirect('login')
        
    return render(request, 'app/home.html', {
        'email': email,
        'token': token
    })

def login_view(request):
    """Vista para manejar el inicio de sesión."""
    # Si el usuario ya está autenticado, redirigir a inicio
    if request.session.get('access_token'):
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Preparar payload compatible con OAuth2PasswordRequestForm
            payload = {
                'username': email,
                'password': password
            }
            
            try:
                # Consumir el endpoint del backend de FastAPI
                response = requests.post(
                    f"{BACKEND_URL}/auth/login/access-token",
                    data=payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Guardar el token y correo en la sesión de Django
                    request.session['access_token'] = data.get('access_token')
                    request.session['user_email'] = email
                    
                    messages.success(request, "¡Sesión iniciada correctamente!")
                    return redirect('home')
                elif response.status_code == 401:
                    messages.error(request, "Correo o contraseña incorrectos.")
                else:
                    messages.error(request, "Ocurrió un error inesperado en el servidor backend.")
            except requests.exceptions.RequestException:
                messages.error(request, "No se pudo conectar con el servidor backend (FastAPI offline).")
    else:
        form = LoginForm()
        
    return render(request, 'app/login.html', {'form': form})

def logout_view(request):
    """Vista para cerrar la sesión."""
    request.session.flush()  # Limpia toda la sesión
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')
