"""
Views para los módulos de IA Clínica - Dashboards y interfaces
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import requests
import json

# Configuración del API Backend (FastAPI)
BACKEND_URL = "http://localhost:8000"
API_TIMEOUT = 10


@login_required
def ia_dashboard_view(request):
    """
    Dashboard principal de IA Clínica
    Muestra estado del sistema Ollama, estadísticas de uso, y acceso a módulos
    """
    context = {
        'page_title': 'IA Clínica - Dashboard',
        'user': request.user,
        'user_role': request.user.groups.first().name if request.user.groups.exists() else 'usuario'
    }
    return render(request, 'ai/ai_dashboard.html', context)


@login_required
def ia_analysis_view(request):
    """
    Panel de análisis avanzado de resultados
    Interfaz para solicitar análisis especializados
    """
    context = {
        'page_title': 'Análisis IA - Resultados',
        'user': request.user,
    }
    return render(request, 'ai/ai_analysis.html', context)


@login_required
def ia_chat_view(request):
    """
    Interfaz de chat con asistente clínico
    Consultas interactivas sobre resultados y biomarcadores
    """
    context = {
        'page_title': 'Chat Clínico - Asistente IA',
        'user': request.user,
    }
    return render(request, 'ai/ai_chat.html', context)


@login_required
def ia_audit_view(request):
    """
    Visualización de auditoría y trazabilidad de decisiones IA
    Registro de análisis realizados, decisiones y recomendaciones
    """
    context = {
        'page_title': 'Auditoría IA - Decisiones',
        'user': request.user,
    }
    return render(request, 'ai/ai_audit.html', context)


# API Proxy Endpoints - Para comunicación frontend <-> backend FastAPI


@login_required
@require_http_methods(["GET"])
def api_health_check(request):
    """
    Verifica el estado de los servidores (Ollama y FastAPI)
    """
    try:
        # Check Ollama
        ollama_response = requests.get(
            f"{BACKEND_URL}/ai/health",
            timeout=API_TIMEOUT
        )
        
        if ollama_response.status_code == 200:
            data = ollama_response.json()
            return JsonResponse({
                'status': 'success',
                'ollama_status': data.get('ollama_status', 'unknown'),
                'models': data.get('models', []),
                'timestamp': data.get('timestamp')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Backend health check failed',
                'status_code': ollama_response.status_code
            }, status=500)
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'status': 'error',
            'message': 'Backend connection timeout',
        }, status=503)
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'status': 'error',
            'message': 'Cannot connect to backend server',
        }, status=503)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}',
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_interpret_results(request):
    """
    Solicita interpretación de resultados de laboratorio
    """
    try:
        data = json.loads(request.body)
        
        # Validar datos
        if not data.get('results'):
            return JsonResponse({
                'status': 'error',
                'message': 'No results provided'
            }, status=400)
        
        # Forward to FastAPI
        response = requests.post(
            f"{BACKEND_URL}/ai/interpret-results",
            json=data,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                'status': 'error',
                'message': response.text
            }, status=response.status_code)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_detect_anomalies(request):
    """
    Detecta anomalías y valores críticos en resultados
    """
    try:
        data = json.loads(request.body)
        
        response = requests.post(
            f"{BACKEND_URL}/ai/detect-anomalies",
            json=data,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                'status': 'error',
                'message': response.text
            }, status=response.status_code)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_prioritize(request):
    """
    Obtiene priorización de análisis y urgencia clínica
    """
    try:
        data = json.loads(request.body)
        
        response = requests.post(
            f"{BACKEND_URL}/ai/prioritize",
            json=data,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                'status': 'error',
                'message': response.text
            }, status=response.status_code)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_chat_message(request):
    """
    Envía mensaje al asistente clínico de IA
    """
    try:
        data = json.loads(request.body)
        
        if not data.get('message'):
            return JsonResponse({
                'status': 'error',
                'message': 'No message provided'
            }, status=400)
        
        response = requests.post(
            f"{BACKEND_URL}/ai/chat",
            json=data,
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                'status': 'error',
                'message': response.text
            }, status=response.status_code)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_audit_log(request):
    """
    Obtiene el registro de auditoría de decisiones IA
    """
    try:
        limit = request.GET.get('limit', 100)
        offset = request.GET.get('offset', 0)
        
        response = requests.get(
            f"{BACKEND_URL}/ai/audit-log",
            params={'limit': limit, 'offset': offset},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({
                'status': 'error',
                'message': response.text
            }, status=response.status_code)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
