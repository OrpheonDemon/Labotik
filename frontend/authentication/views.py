from django.shortcuts import render

def login_view(request):
    return render(request, 'login.html')

def face_login_view(request):
    """Vista para login con reconocimiento facial"""
    return render(request, 'face_login.html')

def face_register_view(request):
    """Vista para registro de rostro (requiere autenticación previa)"""
    return render(request, 'face_register.html')

def admin_dashboard_view(request):
    return render(request, 'dashboard/admin_dashboard.html')


def medico_dashboard_view(request):
    return render(request, 'dashboard/medico_dashboard.html')


def recepcionista_dashboard_view(request):
    return render(request, 'dashboard/recepcionista_dashboard.html')


def paciente_dashboard_view(request):
    return render(request, 'dashboard/paciente_dashboard.html')


def laboratorista_dashboard_view(request):
    return render(request, 'dashboard/laboratorista_dashboard.html')
