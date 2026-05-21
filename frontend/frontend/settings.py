import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-labotik-secret-key-2026-premium-client')

DEBUG = True

ALLOWED_HOSTS = ['*']

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'client', # Nuestra aplicación frontend
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'frontend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'frontend.wsgi.application'

# Base de datos ficticia (el frontend no almacena datos locales, consume de FastAPI)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validación de contraseñas (no requerida ya que autenticamos en FastAPI, pero dejamos por defecto de Django)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
]

# Configuración de idioma y zona horaria
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos (CSS, JavaScript, imágenes)
STATIC_URL = '/static/'

# Configuración de URLs del backend de FastAPI
API_BASE_URL = os.getenv('FASTAPI_API_URL', 'http://127.0.0.1:8000')

# Motor de sesiones basado en cookies firmadas criptográficamente
# Esto hace que el cliente de Django sea 100% libre de bases de datos y funcione sin migraciones
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# ----- Seguridad JWT/Sesión -----
# Expiración de sesión alineada con el ACCESS_TOKEN_EXPIRE_MINUTES del JWT (30 min)
SESSION_COOKIE_AGE = 1800           # 30 minutos en segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # La sesión expira por tiempo, no al cerrar el browser
SESSION_COOKIE_HTTPONLY = True      # Impide acceso al token via JavaScript (XSS)
SESSION_COOKIE_SAMESITE = 'Lax'    # Protección contra CSRF

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
