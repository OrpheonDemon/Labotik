from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Médicos
    path('solicitudes/crear/', views.crear_solicitud_view, name='crear_solicitud'),
    path('solicitudes/<int:id_solicitud>/', views.medico_solicitud_detalle_view, name='medico_solicitud_detalle'),
    
    # Pacientes
    path('solicitudes/solicitar/', views.solicitar_analisis_view, name='solicitar_analisis'),
    
    # Laboratoristas
    path('resultados/ingresar/<int:id_detalle>/', views.ingresar_resultado_view, name='ingresar_resultado'),
    path('areas/', views.areas_catalog_view, name='areas_catalog'),
    path('pruebas/', views.pruebas_catalog_view, name='pruebas_catalog'),
    path('superadmin/pacientes/', views.superadmin_pacientes_view, name='superadmin_pacientes'),
    path('superadmin/medicos/', views.superadmin_medicos_view, name='superadmin_medicos'),
    path('superadmin/laboratoristas/', views.superadmin_laboratoristas_view, name='superadmin_laboratoristas'),
    
    # Impresión / Descargas
    path('imprimir/resultado/<int:id_solicitud>/', views.imprimir_resultado_view, name='imprimir_resultado'),
    path('imprimir/factura/<int:id_factura>/', views.imprimir_factura_view, name='imprimir_factura'),
    
    # Inteligencia Artificial
    path('ai/diagnostico/<int:id_solicitud>/', views.diagnostico_ia_view, name='diagnostico_ia'),
]
