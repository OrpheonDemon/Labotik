"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from authentication.views import (
    login_view,
    face_login_view,
    face_register_view,
    admin_dashboard_view,
    recepcionista_dashboard_view,
    medico_dashboard_view,
    paciente_dashboard_view,
    laboratorista_dashboard_view,
)
from authentication.ia_views import (
    ia_dashboard_view,
    ia_analysis_view,
    ia_chat_view,
    ia_audit_view,
    api_health_check,
    api_interpret_results,
    api_detect_anomalies,
    api_prioritize,
    api_chat_message,
    api_audit_log,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", login_view, name="login"),
    path("face-login/", face_login_view, name="face_login"),
    path("face-register/", face_register_view, name="face_register"),
    path("admin-dashboard/", admin_dashboard_view, name="admin_dashboard"),
    path("medico-dashboard/", medico_dashboard_view, name="medico_dashboard"),
    path("paciente-dashboard/", paciente_dashboard_view, name="paciente_dashboard"),
    path("laboratorista-dashboard/", laboratorista_dashboard_view, name="laboratorista_dashboard"),
    path("recepcionista-dashboard/", recepcionista_dashboard_view, name="recepcionista_dashboard"),
    
    # IA Clínica Routes
    path("ia/dashboard/", ia_dashboard_view, name="ia_dashboard"),
    path("ia/analysis/", ia_analysis_view, name="ia_analysis"),
    path("ia/chat/", ia_chat_view, name="ia_chat"),
    path("ia/audit/", ia_audit_view, name="ia_audit"),
    
    # API Proxy Routes (Frontend <-> FastAPI Backend)
    path("api/ia/health/", api_health_check, name="api_health_check"),
    path("api/ia/interpret/", api_interpret_results, name="api_interpret"),
    path("api/ia/anomalies/", api_detect_anomalies, name="api_anomalies"),
    path("api/ia/prioritize/", api_prioritize, name="api_prioritize"),
    path("api/ia/chat/", api_chat_message, name="api_chat"),
    path("api/ia/audit-log/", api_audit_log, name="api_audit_log"),
]
