import base64
import json
import time
import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.urls import reverse

# Decodifica el payload de un JWT (sin verificar firma — la verificación real la hace FastAPI)
def decode_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)  # Añadir padding de base64
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        return json.loads(payload_json)
    except Exception as e:
        print(f"Error decodificando JWT: {e}")
        return {}

# Verifica si el JWT almacenado en sesión ha expirado usando el campo 'exp'
def is_token_expired(request):
    token = request.session.get('access_token')
    if not token:
        return True
    payload = decode_jwt(token)
    exp = payload.get('exp')
    if not exp:
        return True  # Sin expiración declarada, considerar inválido
    return time.time() > exp

# Helper para realizar llamadas a la API de FastAPI
def api_request(method, endpoint, token=None, json_data=None, params=None, data_data=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    url = f"{settings.API_BASE_URL}{endpoint}"
    
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.lower() == 'post':
            response = requests.post(url, headers=headers, json=json_data, data=data_data, params=params, timeout=10)
        elif method.lower() == 'put':
            response = requests.put(url, headers=headers, json=json_data, data=data_data, params=params, timeout=10)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers, timeout=10)
        return response
    except requests.exceptions.RequestException as e:
        # Usar repr(e) o ignorar el print en caso de problemas de codificación en consola
        try:
            print(f"Error al conectar con FastAPI: {repr(e)}")
        except UnicodeEncodeError:
            pass
        return None

# Vista index: Redirige según el estado de sesión
def index(request):
    if 'access_token' in request.session and not is_token_expired(request):
        return redirect('dashboard')
    request.session.flush()  # Limpiar sesión si el token expiró
    return redirect('login')

# Vista de inicio de sesión
def login_view(request):
    if 'access_token' in request.session and not is_token_expired(request):
        return redirect('dashboard')
    elif 'access_token' in request.session:
        request.session.flush()  # Limpiar sesión expirada silenciosamente
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Enviar petición a FastAPI
        response = api_request('post', '/auth/login/access-token', data_data={'username': email, 'password': password})
        
        if response is None:
            messages.error(request, "No se puede conectar con el servidor de la API. Verifica que FastAPI esté ejecutándose en la dirección configurada.")
        elif response.status_code == 200:
            try:
                token_data = response.json()
            except ValueError:
                messages.error(request, "La API devolvió una respuesta inválida al iniciar sesión.")
                return render(request, 'login.html')

            token = token_data.get('access_token')
            if not token:
                messages.error(request, "No se recibió un token de acceso válido del servidor.")
                return render(request, 'login.html')

            # Decodificar el token para extraer metadatos
            decoded = decode_jwt(token)
            if not decoded:
                messages.error(request, "El token recibido es inválido.")
                return render(request, 'login.html')

            # Guardar en sesión de Django
            request.session['access_token'] = token
            request.session['rol'] = decoded.get('rol')
            request.session['id_usuario'] = decoded.get('id_usuario')
            request.session['email'] = decoded.get('sub')
            request.session['admin_rol'] = decoded.get('admin_rol')
            
            # Obtener nombre real según el rol
            nombre_usuario = email.split('@')[0].capitalize()
            rol = decoded.get('rol')
            id_usuario = decoded.get('id_usuario')
            
            if rol in ['paciente', 'medico', 'laboratorista']:
                profile_endpoint = f"/{rol}s/{id_usuario}"
                profile_res = api_request('get', profile_endpoint, token=token)
                if profile_res and profile_res.status_code == 200:
                    user_profile = profile_res.json()
                    nombre_usuario = f"{user_profile.get('nombre')} {user_profile.get('apellido_paterno')}"
            elif rol == 'administrador':
                admin_rol = decoded.get('admin_rol')
                if admin_rol:
                    nombre_usuario = f"{admin_rol.replace('_', ' ').title()}"
            request.session['nombre_real'] = nombre_usuario
            
            messages.success(request, f"¡Bienvenido de nuevo, {nombre_usuario}!")
            return redirect('dashboard')
        elif response.status_code == 401:
            messages.error(request, "Correo o contraseña incorrectos. Por favor, verifica tus datos.")
        else:
            messages.error(request, f"Error de conexión con la API: código {response.status_code}.")
            
    return render(request, 'login.html')

# Vista de cerrar sesión
def logout_view(request):
    token = request.session.get('access_token')
    if token:
        # Call backend to audit logout
        api_request('post', '/auth/logout', token=token)
    
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')

# Dashboard Dinámico por Roles
def is_super_admin(request):
    return request.session.get('rol') == 'administrador' and request.session.get('admin_rol') == 'super_admin'


def dashboard_view(request):
    # Verificar expiración del JWT antes de continuar
    if is_token_expired(request):
        request.session.flush()
        messages.warning(request, "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
        return redirect('login')

    token = request.session.get('access_token')
    rol = request.session.get('rol')
    id_usuario = request.session.get('id_usuario')
    
    if not token or not rol:
        messages.warning(request, "Debes iniciar sesión para acceder al panel.")
        return redirect('login')
        
    context = {
        'rol': rol,
        'admin_rol': request.session.get('admin_rol'),
        'nombre_real': request.session.get('nombre_real', 'Usuario'),
        'email': request.session.get('email', ''),
        'id_usuario': id_usuario
    }
    
    # ------------------ ROL: PACIENTE ------------------
    if rol == 'paciente':
        # 1. Obtener perfil
        profile_res = api_request('get', f"/pacientes/{id_usuario}", token=token)
        if profile_res and profile_res.status_code == 200:
            context['perfil'] = profile_res.json()
            
        # 2. Obtener solicitudes del paciente
        solicitudes_res = api_request('get', "/solicitudes/", token=token)
        if solicitudes_res and solicitudes_res.status_code == 200:
            todas = solicitudes_res.json()
            # Filtrar las solicitudes que pertenecen a este paciente
            context['solicitudes'] = [s for s in todas if s.get('id_paciente') == id_usuario]
            
        # 3. Obtener facturas del paciente
        facturas_res = api_request('get', "/facturas/", token=token)
        if facturas_res and facturas_res.status_code == 200:
            todas_facturas = facturas_res.json()
            context['facturas'] = [f for f in todas_facturas if f.get('id_paciente') == id_usuario]
            
        return render(request, 'dashboards/paciente.html', context)
        
    # ------------------ ROL: MEDICO ------------------
    elif rol == 'medico':
        # 1. Obtener perfil
        profile_res = api_request('get', f"/medicos/{id_usuario}", token=token)
        if profile_res and profile_res.status_code == 200:
            context['perfil'] = profile_res.json()
            
        # 2. Obtener solicitudes generadas por el médico
        solicitudes_res = api_request('get', "/solicitudes/", token=token)
        solicitudes = []
        if solicitudes_res and solicitudes_res.status_code == 200:
            todas = solicitudes_res.json()
            solicitudes = [s for s in todas if s.get('id_medico') == id_usuario]
            context['solicitudes'] = solicitudes
        else:
            context['solicitudes'] = []

        # 3. Obtener resultados clínicos para detectar anomalías y estados
        resultados_res = api_request('get', "/resultados/", token=token)
        resultados_dict = {}
        if resultados_res and resultados_res.status_code == 200:
            context['resultados'] = resultados_res.json()
            resultados_dict = {r['id_detalle']: r for r in context['resultados']}
        else:
            context['resultados'] = []

        context['solicitudes_completadas'] = sum(1 for s in solicitudes if s.get('estado') == 'completado')
        context['solicitudes_pendientes'] = sum(1 for s in solicitudes if s.get('estado') != 'completado')
        context['pacientes_activos'] = len({s.get('id_paciente') for s in solicitudes})
        context['solicitudes_alerta'] = 0
        for sol in solicitudes:
            if sol.get('estado') == 'completado':
                for det in sol.get('detalles', []):
                    if resultados_dict.get(det.get('id_detalle'), {}).get('es_anormal') == 1:
                        context['solicitudes_alerta'] += 1
                        break

        # 4. Obtener lista de pacientes registrados (para el buscador / historial)
        pacientes_res = api_request('get', "/pacientes/", token=token)
        if pacientes_res and pacientes_res.status_code == 200:
            context['pacientes'] = pacientes_res.json()
            
        return render(request, 'dashboards/medico.html', context)
        
    # ------------------ ROL: LABORATORISTA ------------------
    elif rol == 'laboratorista':
        # 1. Obtener perfil
        profile_res = api_request('get', f"/laboratoristas/{id_usuario}", token=token)
        if profile_res and profile_res.status_code == 200:
            context['perfil'] = profile_res.json()
            
        # 2. Obtener catálogo de pruebas para conocer sus detalles
        pruebas_res = api_request('get', "/pruebas/", token=token)
        pruebas_cat = {}
        if pruebas_res and pruebas_res.status_code == 200:
            context['pruebas'] = pruebas_res.json()
            pruebas_cat = {p['id_prueba']: p for p in context['pruebas']}
            
        # 3. Obtener todos los resultados registrados (para saber qué items ya están procesados)
        resultados_res = api_request('get', "/resultados/", token=token)
        resultados_dict = {}
        if resultados_res and resultados_res.status_code == 200:
            context['resultados'] = resultados_res.json()
            resultados_dict = {r['id_detalle']: r for r in context['resultados']}
        else:
            context['resultados'] = []
            
        # 4. Obtener TODAS las solicitudes (para la cola de trabajo)
        solicitudes_res = api_request('get', "/solicitudes/", token=token)
        if solicitudes_res and solicitudes_res.status_code == 200:
            solicitudes = solicitudes_res.json()
            # Enriquecer solicitudes con nombres de pruebas y resultados
            for sol in solicitudes:
                for det in sol.get('detalles', []):
                    p_id = det.get('id_prueba')
                    prueba = pruebas_cat.get(p_id, {})
                    det['prueba_nombre'] = prueba.get('nombre', f"Prueba #{p_id}")
                    det['prueba_valor_ref'] = prueba.get('valor_referencia', '-')
                    det['prueba_unidad'] = prueba.get('unidad', '')
                    
                    # Buscar si ya tiene un resultado registrado
                    res_obj = resultados_dict.get(det.get('id_detalle'))
                    if res_obj:
                        det['resultado_obj'] = res_obj
            context['solicitudes'] = solicitudes
            
        return render(request, 'dashboards/laboratorista.html', context)
        
    # ------------------ ROL: SUPERADMIN ------------------
    elif rol == 'administrador':
        if request.session.get('admin_rol') != 'super_admin':
            messages.error(request, "Acceso administrativo limitado. Solo Super Admin puede ingresar al panel de gestión central.")
            return redirect('login')

        pacientes_res = api_request('get', "/pacientes/", token=token)
        medicos_res = api_request('get', "/medicos/", token=token)
        laboratoristas_res = api_request('get', "/laboratoristas/", token=token)
        
        context['stats'] = {
            'pacientes': len(pacientes_res.json()) if pacientes_res and pacientes_res.status_code == 200 else 0,
            'medicos': len(medicos_res.json()) if medicos_res and medicos_res.status_code == 200 else 0,
            'laboratoristas': len(laboratoristas_res.json()) if laboratoristas_res and laboratoristas_res.status_code == 200 else 0,
        }
        return render(request, 'dashboards/superadmin.html', context)
        
    else:
        messages.error(request, "Rol desconocido. Contacta al administrador.")
        return redirect('logout')


# Helpers de Superadmin

def superadmin_guard(request):
    if not is_super_admin(request):
        messages.error(request, "Solo el Super Admin puede acceder a esta sección.")
        return False
    return True


def superadmin_pacientes_view(request):
    if not superadmin_guard(request):
        return redirect('dashboard')

    token = request.session.get('access_token')
    is_super_admin = request.session.get('rol') == 'administrador' and request.session.get('admin_rol') == 'super_admin'

    if request.method == 'POST':
        toggle_paciente_id = request.POST.get('toggle_paciente_id')
        if toggle_paciente_id:
            destino_estado = int(request.POST.get('toggle_activo', 0))
            payload = {'activo': destino_estado}
            res = api_request('put', f'/pacientes/{toggle_paciente_id}', token=token, json_data=payload)
            if res and res.status_code == 200:
                estado_text = 'reactivado' if destino_estado == 1 else 'desactivado'
                messages.success(request, f"Paciente {toggle_paciente_id} {estado_text} correctamente.")
            else:
                messages.error(request, "No se pudo cambiar el estado del paciente. Intenta de nuevo.")
            return redirect('superadmin_pacientes')

        payload = {
            'nombre': request.POST.get('nombre'),
            'apellido_paterno': request.POST.get('apellido_paterno'),
            'apellido_materno': request.POST.get('apellido_materno'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'genero': request.POST.get('genero'),
            'telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'direccion': request.POST.get('direccion'),
            'tipo_sangre': request.POST.get('tipo_sangre'),
            'alergias': request.POST.get('alergias'),
            'password': request.POST.get('password'),
        }
        res = api_request('post', '/pacientes/', token=token, json_data=payload)
        if res and res.status_code in [200, 201]:
            messages.success(request, "Paciente creado con éxito.")
            return redirect('superadmin_pacientes')
        messages.error(request, "Error al crear paciente. Revisa los datos ingresados.")

    params = {'include_inactive': 1} if is_super_admin else None
    pacientes_res = api_request('get', '/pacientes/', token=token, params=params)
    context = {
        'pacientes': pacientes_res.json() if pacientes_res and pacientes_res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': request.session.get('rol'),
        'is_super_admin': is_super_admin
    }
    return render(request, 'superadmin/pacientes.html', context)


def superadmin_medicos_view(request):
    if not superadmin_guard(request):
        return redirect('dashboard')

    token = request.session.get('access_token')
    is_super_admin = request.session.get('rol') == 'administrador' and request.session.get('admin_rol') == 'super_admin'

    if request.method == 'POST':
        toggle_medico_id = request.POST.get('toggle_medico_id')
        if toggle_medico_id:
            destino_estado = int(request.POST.get('toggle_activo', 0))
            payload = {'activo': destino_estado}
            res = api_request('put', f'/medicos/{toggle_medico_id}', token=token, json_data=payload)
            if res and res.status_code == 200:
                estado_text = 'reactivado' if destino_estado == 1 else 'desactivado'
                messages.success(request, f"Médico {toggle_medico_id} {estado_text} correctamente.")
            else:
                messages.error(request, "No se pudo cambiar el estado del médico. Intenta de nuevo.")
            return redirect('superadmin_medicos')

        payload = {
            'nombre': request.POST.get('nombre'),
            'apellido_paterno': request.POST.get('apellido_paterno'),
            'apellido_materno': request.POST.get('apellido_materno'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'especialidad': request.POST.get('especialidad'),
            'telefono': request.POST.get('telefono'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
        }
        res = api_request('post', '/medicos/', token=token, json_data=payload)
        if res and res.status_code in [200, 201]:
            messages.success(request, "Médico creado con éxito.")
            return redirect('superadmin_medicos')
        messages.error(request, "Error al crear médico. Revisa los datos ingresados.")

    params = {'include_inactive': 1} if is_super_admin else None
    medicos_res = api_request('get', '/medicos/', token=token, params=params)
    context = {
        'medicos': medicos_res.json() if medicos_res and medicos_res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': request.session.get('rol'),
        'is_super_admin': is_super_admin
    }
    return render(request, 'superadmin/medicos.html', context)


def superadmin_laboratoristas_view(request):
    if not superadmin_guard(request):
        return redirect('dashboard')

    token = request.session.get('access_token')
    is_super_admin = request.session.get('rol') == 'administrador' and request.session.get('admin_rol') == 'super_admin'

    if request.method == 'POST':
        toggle_laboratorista_id = request.POST.get('toggle_laboratorista_id')
        if toggle_laboratorista_id:
            destino_estado = int(request.POST.get('toggle_activo', 0))
            payload = {'activo': destino_estado}
            res = api_request('put', f'/laboratoristas/{toggle_laboratorista_id}', token=token, json_data=payload)
            if res and res.status_code == 200:
                estado_text = 'reactivado' if destino_estado == 1 else 'desactivado'
                messages.success(request, f"Laboratorista {toggle_laboratorista_id} {estado_text} correctamente.")
            else:
                messages.error(request, "No se pudo cambiar el estado del laboratorista. Intenta de nuevo.")
            return redirect('superadmin_laboratoristas')

        payload = {
            'nombre': request.POST.get('nombre'),
            'apellido_paterno': request.POST.get('apellido_paterno'),
            'apellido_materno': request.POST.get('apellido_materno'),
            'fecha_nacimiento': request.POST.get('fecha_nacimiento'),
            'email': request.POST.get('email'),
            'telefono': request.POST.get('telefono'),
            'id_area': request.POST.get('id_area'),
            'password': request.POST.get('password'),
        }
        res = api_request('post', '/laboratoristas/', token=token, json_data=payload)
        if res and res.status_code in [200, 201]:
            messages.success(request, "Laboratorista creado con éxito.")
            return redirect('superadmin_laboratoristas')
        messages.error(request, "Error al crear laboratorista. Revisa los datos ingresados.")

    params = {'include_inactive': 1} if is_super_admin else None
    laboratoristas_res = api_request('get', '/laboratoristas/', token=token, params=params)
    context = {
        'laboratoristas': laboratoristas_res.json() if laboratoristas_res and laboratoristas_res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': request.session.get('rol'),
        'is_super_admin': is_super_admin
    }
    return render(request, 'superadmin/laboratoristas.html', context)


def superadmin_auditoria_view(request):
    if not superadmin_guard(request):
        return redirect('dashboard')

    token = request.session.get('access_token')
    is_super_admin = request.session.get('rol') == 'administrador' and request.session.get('admin_rol') == 'super_admin'

    # Fetch audit logs
    auditoria_res = api_request('get', '/auditoria/', token=token)
    auditoria_data = auditoria_res.json() if auditoria_res and auditoria_res.status_code == 200 else []

    # Fetch reportes and solicitudes for past history
    reportes_res = api_request('get', '/reportes/', token=token)
    solicitudes_res = api_request('get', '/solicitudes/', token=token)

    reportes = reportes_res.json() if reportes_res and reportes_res.status_code == 200 else []
    solicitudes = solicitudes_res.json() if solicitudes_res and solicitudes_res.status_code == 200 else []

    # Map to expected structure
    auditoria = []
    
    # New Audit Logs
    for a in auditoria_data:
        auditoria.append({
            'tipo': a.get('accion'),
            'id': a.get('id_auditoria'),
            'referencia': a.get('id_usuario', 'Sistema'),
            'estado': 'Registrado',
            'fecha': a.get('created_at'),
            'detalles': a.get('detalles', '')
        })

    # Restore old Reportes history
    for r in reportes:
        auditoria.append({
            'tipo': 'Reporte',
            'id': r.get('id_reporte'),
            'referencia': f"Solicitud #{r.get('id_solicitud')}",
            'estado': r.get('estado'),
            'fecha': r.get('created_at'),
            'detalles': r.get('observaciones', 'Generación de reporte (Histórico)')
        })

    # Restore old Solicitudes history
    for s in solicitudes:
        auditoria.append({
            'tipo': 'Solicitud',
            'id': s.get('id_solicitud'),
            'referencia': f"Paciente {s.get('id_paciente')}",
            'estado': s.get('estado'),
            'fecha': s.get('created_at'),
            'detalles': f"Prioridad: {s.get('prioridad')} (Histórico)"
        })
        
    # Sort by date descending
    auditoria.sort(key=lambda x: x['fecha'] if x['fecha'] else '', reverse=True)

    context = {
        'auditoria': auditoria,
        'nombre_real': request.session.get('nombre_real'),
        'rol': request.session.get('rol'),
        'is_super_admin': is_super_admin
    }
    return render(request, 'superadmin/auditoria.html', context)

# Crear Solicitud (Médico o Laboratorista)
def crear_solicitud_view(request):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    
    if not token or rol not in ['medico', 'laboratorista']:
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        id_paciente = request.POST.get('id_paciente')
        prioridad = request.POST.get('prioridad', 'media')
        observaciones = request.POST.get('observaciones', '')
        
        # Extraer las pruebas seleccionadas del formulario
        pruebas_ids = request.POST.getlist('pruebas[]')
        cantidades = request.POST.getlist('cantidades[]')
        
        detalles = []
        for p_id, cant in zip(pruebas_ids, cantidades):
            if p_id:
                detalles.append({
                    'id_prueba': int(p_id),
                    'cantidad': int(cant) if cant else 1
                })
                
        if not detalles:
            messages.error(request, "Debes seleccionar al menos una prueba de laboratorio.")
        else:
            payload = {
                'id_paciente': id_paciente,
                'id_medico': request.session.get('id_usuario'),
                'prioridad': prioridad,
                'observaciones': observaciones,
                'detalles': detalles
            }
            
            res = api_request('post', '/solicitudes/', token=token, json_data=payload)
            if res and res.status_code == 201:
                messages.success(request, "¡Solicitud médica creada con éxito en la cola del laboratorio!")
                return redirect('dashboard')
            else:
                detail = "Error interno al procesar la solicitud."
                if res:
                    try:
                        detail = res.json().get('detail', detail)
                    except:
                        pass
                messages.error(request, f"Error al crear solicitud: {detail}")
                
    # GET: Obtener catálogos de pacientes y pruebas para llenar los selects del formulario
    pacientes_res = api_request('get', '/pacientes/', token=token)
    pruebas_res = api_request('get', '/pruebas/', token=token)
    
    context = {
        'pacientes': pacientes_res.json() if pacientes_res and pacientes_res.status_code == 200 else [],
        'pruebas': pruebas_res.json() if pruebas_res and pruebas_res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': rol
    }
    
    return render(request, 'crear_solicitud.html', context)

# Detalle de Solicitud para Médico
def medico_solicitud_detalle_view(request, id_solicitud):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    id_usuario = request.session.get('id_usuario')

    if not token or rol not in ['medico', 'administrador']:
        messages.error(request, "No tienes permisos para ver esta página.")
        return redirect('dashboard')

    sol_res = api_request('get', f"/solicitudes/{id_solicitud}", token=token)
    if not sol_res or sol_res.status_code != 200:
        messages.error(request, "Solicitud no encontrada.")
        return redirect('dashboard')

    solicitud = sol_res.json()
    if rol == 'medico' and solicitud.get('id_medico') != id_usuario:
        messages.error(request, "No tienes acceso a esta solicitud.")
        return redirect('dashboard')

    pac_res = api_request('get', f"/pacientes/{solicitud.get('id_paciente')}", token=token)
    paciente = pac_res.json() if pac_res and pac_res.status_code == 200 else {}

    med_res = api_request('get', f"/medicos/{solicitud.get('id_medico')}", token=token)
    medico = med_res.json() if med_res and med_res.status_code == 200 else {}

    pruebas_res = api_request('get', "/pruebas/", token=token)
    pruebas_cat = {p['id_prueba']: p for p in pruebas_res.json()} if pruebas_res and pruebas_res.status_code == 200 else {}

    resultados_res = api_request('get', "/resultados/", token=token)
    todos_resultados = resultados_res.json() if resultados_res and resultados_res.status_code == 200 else []
    resultados_dict = {r['id_detalle']: r for r in todos_resultados}

    detalles_completos = []
    resultados_completos = 0
    anomalías = 0
    for det in solicitud.get('detalles', []):
        prueba = pruebas_cat.get(det.get('id_prueba'), {'nombre': f"Prueba #{det.get('id_prueba')}", 'valor_referencia': '-', 'unidad': '-'})
        res_obj = resultados_dict.get(det.get('id_detalle'))
        if res_obj:
            resultados_completos += 1
            if res_obj.get('es_anormal', 0) == 1:
                anomalías += 1

        detalles_completos.append({
            'nombre_prueba': prueba.get('nombre'),
            'descripcion': prueba.get('descripcion'),
            'valor_referencia': prueba.get('valor_referencia'),
            'unidad': prueba.get('unidad'),
            'cantidad': det.get('cantidad', 1),
            'resultado': res_obj.get('resultado') if res_obj else 'Pendiente',
            'observacion': res_obj.get('observacion') if res_obj else '-',
            'es_anormal': res_obj.get('es_anormal', 0) if res_obj else 0,
            'fecha_validacion': res_obj.get('fecha_validacion') if res_obj else None
        })

    context = {
        'solicitud': solicitud,
        'paciente': paciente,
        'medico': medico,
        'detalles': detalles_completos,
        'resultados_completos': resultados_completos,
        'total_pruebas': len(solicitud.get('detalles', [])),
        'anomalías': anomalías,
        'rol': rol,
        'nombre_real': request.session.get('nombre_real')
    }
    return render(request, 'dashboards/medico_solicitud_detalle.html', context)

# Solicitar Análisis (Paciente)
def solicitar_analisis_view(request):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    
    if not token or rol != 'paciente':
        messages.error(request, "No tienes permisos de paciente para realizar esta acción.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        prioridad = request.POST.get('prioridad', 'media')
        observaciones = request.POST.get('observaciones', '')
        
        # Extraer las pruebas seleccionadas del formulario
        pruebas_ids = request.POST.getlist('pruebas[]')
        cantidades = request.POST.getlist('cantidades[]')
        
        detalles = []
        for p_id, cant in zip(pruebas_ids, cantidades):
            if p_id:
                detalles.append({
                    'id_prueba': int(p_id),
                    'cantidad': int(cant) if cant else 1
                })
                
        if not detalles:
            messages.error(request, "Debes seleccionar al menos un examen de laboratorio.")
        else:
            payload = {
                'id_paciente': request.session.get('id_usuario'),
                'id_medico': None, # Sin derivación médica
                'prioridad': prioridad,
                'observaciones': observaciones,
                'detalles': detalles
            }
            
            res = api_request('post', '/solicitudes/', token=token, json_data=payload)
            if res and res.status_code == 201:
                messages.success(request, "¡Tu solicitud de análisis ha sido enviada con éxito a la cola del laboratorio!")
                return redirect('dashboard')
            else:
                detail = "Error interno al procesar tu solicitud."
                if res:
                    try:
                        detail = res.json().get('detail', detail)
                    except:
                        pass
                messages.error(request, f"Error al enviar solicitud: {detail}")
                
    # GET: Obtener catálogo de pruebas disponibles
    pruebas_res = api_request('get', '/pruebas/', token=token)
    
    context = {
        'pruebas': pruebas_res.json() if pruebas_res and pruebas_res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': rol
    }
    
    return render(request, 'solicitar_analisis.html', context)

# Ingresar Resultados (Laboratorista)
def ingresar_resultado_view(request, id_detalle):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    
    if not token or rol != 'laboratorista':
        messages.error(request, "No tienes permisos de laboratorista para realizar esta acción.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        resultado = request.POST.get('resultado')
        observacion = request.POST.get('observacion', '')
        es_anormal = int(request.POST.get('es_anormal', 0))
        
        payload = {
            'id_detalle': id_detalle,
            'resultado': resultado,
            'observacion': observacion,
            'validado_por': request.session.get('id_usuario'),
            'es_anormal': es_anormal
        }
        
        res = api_request('post', '/resultados/', token=token, json_data=payload)
        if res and res.status_code == 201:
            messages.success(request, f"Resultado registrado e ingresado con éxito para el item #{id_detalle}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Error al registrar el resultado. Inténtalo de nuevo.")
            
    # GET: Mostrar formulario de ingreso con información contextual
    # Encontrar a qué prueba corresponde buscando en solicitudes (cola)
    sol_res = api_request('get', '/solicitudes/', token=token)
    detalle_info = None
    if sol_res and sol_res.status_code == 200:
        solicitudes = sol_res.json()
        for sol in solicitudes:
            for det in sol.get('detalles', []):
                if det.get('id_detalle') == id_detalle:
                    detalle_info = det
                    # Buscar información de la prueba
                    pruebas_res = api_request('get', f"/pruebas/", token=token)
                    if pruebas_res and pruebas_res.status_code == 200:
                        for p in pruebas_res.json():
                            if p.get('id_prueba') == det.get('id_prueba'):
                                detalle_info['prueba_nombre'] = p.get('nombre')
                                detalle_info['prueba_valor_ref'] = p.get('valor_referencia')
                                detalle_info['prueba_unidad'] = p.get('unidad')
                                break
                    break
            if detalle_info:
                break
                
    if not detalle_info:
        messages.error(request, "No se encontró información para el item seleccionado.")
        return redirect('dashboard')
        
    context = {
        'detalle': detalle_info,
        'id_detalle': id_detalle,
        'nombre_real': request.session.get('nombre_real'),
        'rol': rol
    }
    
    return render(request, 'ingresar_resultado.html', context)

# Catálogo de Áreas (Laboratorista + Superadmin para creación)
def areas_catalog_view(request):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    admin_rol = request.session.get('admin_rol')
    is_super_admin = rol == 'administrador' and admin_rol == 'super_admin'

    if not token or rol not in ['laboratorista', 'administrador']:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        if not is_super_admin:
            messages.error(request, "Solo el Super Admin puede administrar las áreas clínicas.")
            return redirect('areas_catalog')

        toggle_area_id = request.POST.get('toggle_area_id')
        if toggle_area_id:
            destino_estado = int(request.POST.get('toggle_activo', 0))
            payload = {'activo': destino_estado}
            res = api_request('put', f'/areas/{toggle_area_id}', token=token, json_data=payload)
            if res and res.status_code == 200:
                estado_text = 'reactivada' if destino_estado == 1 else 'desactivada'
                messages.success(request, f"Área '{toggle_area_id}' {estado_text} correctamente.")
            else:
                messages.error(request, "No se pudo cambiar el estado del área. Verifica que exista y vuelve a intentar.")
            return redirect('areas_catalog')

        id_area = request.POST.get('id_area')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        
        payload = {'id_area': id_area, 'nombre': nombre, 'descripcion': descripcion}
        res = api_request('post', '/areas/', token=token, json_data=payload)
        if res and res.status_code in [200, 201]:
            messages.success(request, f"¡Área '{nombre}' agregada con éxito!")
        else:
            messages.error(request, "Error al crear área. Asegúrate de que el código de área sea único.")
            
    params = {'include_inactive': 1} if is_super_admin else None
    res = api_request('get', '/areas/', token=token, params=params)
    context = {
        'areas': res.json() if res and res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': rol,
        'is_super_admin': is_super_admin
    }
    return render(request, 'catalogos/areas.html', context)

# Catálogo de Pruebas (Laboratorista + Superadmin para creación)
def pruebas_catalog_view(request):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    admin_rol = request.session.get('admin_rol')
    is_super_admin = rol == 'administrador' and admin_rol == 'super_admin'

    if not token or rol not in ['laboratorista', 'administrador']:
        messages.error(request, "No tienes acceso a esta sección.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        if not is_super_admin:
            messages.error(request, "Solo el Super Admin puede registrar nuevas pruebas en el catálogo.")
            return redirect('pruebas_catalog')

        toggle_prueba_id = request.POST.get('toggle_prueba_id')
        if toggle_prueba_id:
            destino_estado = int(request.POST.get('toggle_activo', 0))
            payload = {'activo': destino_estado}
            res = api_request('put', f'/pruebas/{toggle_prueba_id}', token=token, json_data=payload)
            if res and res.status_code == 200:
                estado_text = 'reactivada' if destino_estado == 1 else 'desactivada'
                messages.success(request, f"Prueba #{toggle_prueba_id} {estado_text} correctamente.")
            else:
                messages.error(request, "No se pudo cambiar el estado de la prueba. Verifica que exista y vuelve a intentar.")
            return redirect('pruebas_catalog')

        id_area = request.POST.get('id_area')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        valor_referencia = request.POST.get('valor_referencia')
        unidad = request.POST.get('unidad')
        precio = float(request.POST.get('precio', 0.0))
        tiempo = int(request.POST.get('tiempo_estimado_minutos', 30))
        
        payload = {
            'id_area': id_area,
            'nombre': nombre,
            'descripcion': descripcion,
            'valor_referencia': valor_referencia,
            'unidad': unidad,
            'precio': precio,
            'tiempo_estimado_minutos': tiempo
        }
        
        res = api_request('post', '/pruebas/', token=token, json_data=payload)
        if res and res.status_code in [200, 201]:
            messages.success(request, f"¡Prueba '{nombre}' registrada con éxito en el catálogo!")
        else:
            messages.error(request, "Error al registrar la prueba en el catálogo.")
            
    params = {'include_inactive': 1} if is_super_admin else None
    areas_res = api_request('get', '/areas/', token=token, params=params)
    pruebas_res = api_request('get', '/pruebas/', token=token, params=params)
    
    context = {
        'areas': areas_res.json() if areas_res and areas_res.status_code == 200 else [],
        'pruebas': pruebas_res.json() if pruebas_res and pruebas_res.status_code == 200 else [],
        'nombre_real': request.session.get('nombre_real'),
        'rol': rol,
        'is_super_admin': is_super_admin
    }
    return render(request, 'catalogos/pruebas.html', context)

# Impresión de Resultados Clínicos (Paciente / Médico)
def imprimir_resultado_view(request, id_solicitud):
    token = request.session.get('access_token')
    if not token:
        return redirect('login')
        
    # Obtener detalles de la solicitud
    sol_res = api_request('get', f"/solicitudes/{id_solicitud}", token=token)
    if not sol_res or sol_res.status_code != 200:
        return render(request, 'errors/404.html', {'message': "Solicitud no encontrada."})
        
    solicitud = sol_res.json()
    
    # Obtener información del paciente
    pac_res = api_request('get', f"/pacientes/{solicitud.get('id_paciente')}", token=token)
    paciente = pac_res.json() if pac_res and pac_res.status_code == 200 else {}
    
    # Obtener médico si existe
    medico = {}
    if solicitud.get('id_medico'):
        med_res = api_request('get', f"/medicos/{solicitud.get('id_medico')}", token=token)
        if med_res and med_res.status_code == 200:
            medico = med_res.json()
            
    # Obtener los resultados clínicos de cada detalle
    resultados_res = api_request('get', '/resultados/', token=token)
    todos_resultados = resultados_res.json() if resultados_res and resultados_res.status_code == 200 else []
    
    # Obtener catálogo de pruebas para tener nombres y valores de referencia
    pruebas_res = api_request('get', '/pruebas/', token=token)
    pruebas_cat = {p['id_prueba']: p for p in pruebas_res.json()} if pruebas_res and pruebas_res.status_code == 200 else {}
    
    detalles_completos = []
    for det in solicitud.get('detalles', []):
        p_id = det.get('id_prueba')
        prueba = pruebas_cat.get(p_id, {'nombre': f"Prueba #{p_id}", 'valor_referencia': '-', 'unidad': '-'})
        
        # Encontrar resultado si existe
        res_obj = None
        for r in todos_resultados:
            if r.get('id_detalle') == det.get('id_detalle'):
                res_obj = r
                break
                
        detalles_completos.append({
            'nombre_prueba': prueba.get('nombre'),
            'descripcion': prueba.get('descripcion'),
            'valor_referencia': prueba.get('valor_referencia'),
            'unidad': prueba.get('unidad'),
            'resultado': res_obj.get('resultado') if res_obj else 'Pendiente',
            'observacion': res_obj.get('observacion') if res_obj else '',
            'es_anormal': res_obj.get('es_anormal', 0) if res_obj else 0,
            'fecha_validacion': res_obj.get('fecha_validacion') if res_obj else None
        })
        
    context = {
        'solicitud': solicitud,
        'paciente': paciente,
        'medico': medico,
        'detalles': detalles_completos
    }
    
    return render(request, 'impresiones/resultado_pdf.html', context)

# Impresión de Facturas (Paciente)
def imprimir_factura_view(request, id_factura):
    token = request.session.get('access_token')
    if not token:
        return redirect('login')
        
    # Obtener factura
    fac_res = api_request('get', f"/facturas/", token=token)
    if not fac_res or fac_res.status_code != 200:
        return render(request, 'errors/404.html', {'message': "Factura no encontrada."})
        
    factura = None
    for fac in fac_res.json():
        if fac.get('id_factura') == id_factura:
            factura = fac
            break
            
    if not factura:
        return render(request, 'errors/404.html', {'message': "Factura no encontrada."})
        
    # Obtener información del paciente
    pac_res = api_request('get', f"/pacientes/{factura.get('id_paciente')}", token=token)
    paciente = pac_res.json() if pac_res and pac_res.status_code == 200 else {}
    
    # Obtener catálogo de pruebas para tener nombres
    pruebas_res = api_request('get', '/pruebas/', token=token)
    pruebas_cat = {p['id_prueba']: p for p in pruebas_res.json()} if pruebas_res and pruebas_res.status_code == 200 else {}
    
    # Construir items de la factura
    detalles_completos = []
    for det in factura.get('detalles', []):
        p_id = det.get('id_prueba')
        prueba = pruebas_cat.get(p_id, {'nombre': f"Servicio Clínico #{p_id}"})
        
        detalles_completos.append({
            'nombre': prueba.get('nombre'),
            'cantidad': det.get('cantidad', 1),
            'precio_unitario': det.get('precio_unitario'),
            'descuento': det.get('descuento_item', 0.0),
            'total': det.get('total_item')
        })
        
    # Obtener pagos si existen
    pagos_res = api_request('get', '/pagos/', token=token)
    pagos = []
    if pagos_res and pagos_res.status_code == 200:
        pagos = [p for p in pagos_res.json() if p.get('id_factura') == id_factura]
        
    context = {
        'factura': factura,
        'paciente': paciente,
        'detalles': detalles_completos,
        'pagos': pagos
    }
    
    return render(request, 'impresiones/factura_pdf.html', context)

# ----------------- INTELIGENCIA ARTIFICIAL -----------------
from django.http import JsonResponse

def diagnostico_ia_view(request, id_solicitud):
    token = request.session.get('access_token')
    rol = request.session.get('rol')
    
    if not token or rol not in ['medico', 'administrador']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
        
    if request.method == 'POST':
        res = api_request('post', f'/ai/diagnostico/{id_solicitud}', token=token)
        if res and res.status_code == 200:
            return JsonResponse(res.json())
        else:
            err = res.json().get('detail', 'Error al consultar IA') if res else 'Error de conexión'
            return JsonResponse({'error': err}, status=res.status_code if res else 500)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)
