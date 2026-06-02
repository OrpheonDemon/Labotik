"""
Script para:
1. Agregar Asistente IA al medico_dashboard (sin modal, sin sobreponer)
2. Revisar y corregir errores en laboratorista_dashboard
"""

import re

# ============================================
# PARTE 1: Agregar Asistente IA a medico_dashboard
# ============================================

medico_filepath = 'frontend/templates/dashboard/medico_dashboard.html'

with open(medico_filepath, 'r', encoding='utf-8') as f:
    medico_content = f.read()

# Verificar si ya tiene el asistente IA
if 'ia-assistant' not in medico_content:
    # 1. Agregar botón del menú lateral (antes de Cerrar Sesión)
    menu_button = '''                    <li class="menu-item">
                        <a href="#" onclick="navigateMenu(event, 'ia-assistant', 'Asistente IA')">
                            <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12a9 9 0 11-18 0 9 9 0 0118 0zm0 0h-1m-12 0H3m14.364 5.636l-.707-.707M12 21v-1m-6.364-1.636l.707-.707" />
                            </svg>
                            Asistente IA 🧠
                        </a>
                    </li>
'''
    # Insertar antes del botón de Cerrar Sesión
    cerrar_sesion_pattern = r'(<li class="menu-item" style="border-top: 1px solid rgba\(255,255,255,0\.1\); margin-top: 20px; padding-top: 20px;">)'
    medico_content = re.sub(cerrar_sesion_pattern, menu_button + r'\n\1', medico_content)
    print("✅ Botón del menú lateral agregado a medico_dashboard")

    # 2. Agregar sección HTML del Asistente IA (SIN MODAL, contenido directo)
    ia_section = '''
            <!-- ASISTENTE IA SECTION -->
            <section id="ia-assistant" class="dashboard-section" aria-hidden="true">
                <div class="profile-panel">
                    <div class="profile-panel-header">
                        <div>
                            <h1 class="profile-panel-title">🧠 Asistente IA Clínico</h1>
                            <p class="profile-panel-subtitle">Análisis inteligente de resultados de laboratorio con MedGem</p>
                        </div>
                    </div>

                    <!-- Estado del Sistema IA -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 16px;">
                            <p style="color: rgba(255,255,255,0.7); font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px;">Estado Servidor</p>
                            <h4 id="ollama-status" style="color: #fff; margin: 0; font-size: 16px;">
                                <span style="display: inline-block; width: 8px; height: 8px; background: #fbbf24; border-radius: 50%; margin-right: 8px;"></span>
                                Verificando...
                            </h4>
                        </div>
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 16px;">
                            <p style="color: rgba(255,255,255,0.7); font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px;">Modelo Activo</p>
                            <h4 id="model-name" style="color: #fff; margin: 0; font-size: 16px;">MedGem 7B</h4>
                        </div>
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 16px;">
                            <p style="color: rgba(255,255,255,0.7); font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px;">Análisis Hoy</p>
                            <h4 id="analysis-count" style="color: #fff; margin: 0; font-size: 16px;">0</h4>
                        </div>
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 16px;">
                            <p style="color: rgba(255,255,255,0.7); font-size: 12px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px;">Casos Críticos</p>
                            <h4 id="critical-count" style="color: #fff; margin: 0; font-size: 16px;">0</h4>
                        </div>
                    </div>

                    <!-- Opciones Principales -->
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px;">
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.2s ease;" onclick="openIAnalysisPopup()" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 10px 25px rgba(0,0,0,0.2)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                            <div style="font-size: 32px; margin-bottom: 12px;">🔬</div>
                            <h5 style="color: #fff; margin: 0 0 8px; font-size: 16px;">Analizar Resultados</h5>
                            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 13px;">Carga resultados para análisis inteligente</p>
                        </div>
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; text-align: center; cursor: pointer; transition: all 0.2s ease;" onclick="alert('Auditoría en desarrollo')" onmouseover="this.style.transform='translateY(-5px)'; this.style.boxShadow='0 10px 25px rgba(0,0,0,0.2)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                            <div style="font-size: 32px; margin-bottom: 12px;">📋</div>
                            <h5 style="color: #fff; margin: 0 0 8px; font-size: 16px;">Auditoría</h5>
                            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 13px;">Registro de decisiones y análisis</p>
                        </div>
                    </div>

                    <!-- Información del Sistema -->
                    <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                        <h3 style="color: #fff; margin: 0 0 12px; font-size: 16px;">📊 Estado del Sistema IA</h3>
                        <p id="ia-system-status" style="color: rgba(255,255,255,0.8); margin: 0; line-height: 1.6;">Iniciando conexión con motor IA... Verifica que Ollama esté ejecutándose y selecciona un tipo de análisis para comenzar</p>
                    </div>
                    
                    <!-- Análisis por Paciente (contenido directo, sin modal) -->
                    <div id="ia-analysis-container" style="display: none; margin-top: 24px;">
                        <h2 style="color: #fff; margin: 0 0 16px; font-size: 18px;">👤 Análisis por Paciente</h2>
                        <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                            <label style="display: block; color: var(--text-cream); margin-bottom: 12px; font-weight: 600;">Selecciona un paciente:</label>
                            <select id="ia-paciente-select" onchange="this.value && (document.getElementById('ia-analyze-general').disabled = false, document.getElementById('ia-analyze-results').disabled = false)" style="width: 100%; padding: 12px; background: rgba(255,255,255,0.1); color: var(--text-cream); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; font-size: 14px;">
                                <option value="">-- Cargando pacientes --</option>
                            </select>
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 16px;">
                                <button id="ia-analyze-general" disabled onclick="analyzePatientGeneral()" style="padding: 12px; background: linear-gradient(135deg, #c89666 0%, #dfaf7e 100%); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">📊 Análisis General</button>
                                <button id="ia-analyze-results" disabled onclick="analyzePatientResults()" style="padding: 12px; background: linear-gradient(135deg, #c89666 0%, #dfaf7e 100%); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">🔬 Analizar Resultados</button>
                            </div>
                        </div>
                        <div id="ia-analysis-result" style="display: none; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; min-height: 100px; color: var(--text-cream);">ℹ️ Selecciona un paciente y elige un tipo de análisis para comenzar</div>
                    </div>
                </div>
            </section>
'''
    # Insertar antes del ENTITY EDIT MODAL
    entity_modal_pattern = r'(<!-- ENTITY EDIT MODAL)'
    medico_content = re.sub(entity_modal_pattern, ia_section + r'\n            \1', medico_content)
    print("✅ Sección HTML del Asistente IA agregada (sin modal)")

    # 3. Agregar handler en loadSectionData para ia-assistant
    ia_handler = '''
            if (sectionId === 'ia-assistant') {
                checkOllamaStatus();
                await loadPatientsForAnalysis();
            }
'''
    # Buscar el final de loadSectionData y agregar el handler antes
    load_section_pattern = r"(if \(sectionId === 'dashboard'\) \{\s*await loadDashboardStats\(\);\s*\})"
    medico_content = re.sub(load_section_pattern, r'\1' + ia_handler, medico_content)
    print("✅ Handler en loadSectionData agregado")

    # 4. Agregar funciones JavaScript del Asistente IA (adaptadas sin modal)
    ia_js_functions = '''
        // ========== FUNCIONES PARA ASISTENTE IA ==========
        function checkOllamaStatus() {
            fetch(`${API_URL}/ai/status`)
                .then(res => res.json())
                .then(data => {
                    const statusEl = document.getElementById('ollama-status');
                    const modelEl = document.getElementById('model-name');
                    const systemEl = document.getElementById('ia-system-status');
                    if (data.status === 'running') {
                        statusEl.innerHTML = '<span style="display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; margin-right: 8px;"></span>Conectado';
                        modelEl.textContent = data.model || 'MedGem 7B';
                        systemEl.textContent = 'Sistema IA activo y listo para análisis clínico.';
                    } else {
                        statusEl.innerHTML = '<span style="display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; margin-right: 8px;"></span>Desconectado';
                        systemEl.textContent = 'Error: Ollama no está ejecutándose. Inicia el servidor de IA.';
                    }
                })
                .catch(err => {
                    const statusEl = document.getElementById('ollama-status');
                    statusEl.innerHTML = '<span style="display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%; margin-right: 8px;"></span>Error';
                    console.error('Error checking Ollama status:', err);
                });
        }

        async function loadPatientsForAnalysis() {
            const headers = getAuthHeaders();
            const select = document.getElementById('ia-paciente-select');
            try {
                const res = await fetch(`${API_URL}/pacientes?limit=1000`, { headers });
                const pacientes = await res.json();
                select.innerHTML = '<option value="">-- Selecciona un paciente --</option>';
                pacientes.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id_paciente;
                    opt.textContent = `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim();
                    select.appendChild(opt);
                });
            } catch (e) {
                console.error('Error loading patients:', e);
                select.innerHTML = '<option value="">Error cargando pacientes</option>';
            }
        }

        function openIAnalysisPopup() {
            const container = document.getElementById('ia-analysis-container');
            container.style.display = 'block';
            const analysisEl = document.getElementById('ia-analysis-result');
            analysisEl.style.display = 'block';
            analysisEl.innerHTML = 'ℹ️ Selecciona un paciente y elige un tipo de análisis para comenzar';
            checkOllamaStatus();
            loadPatientsForAnalysis();
        }

        async function analyzePatientGeneral() {
            const select = document.getElementById('ia-paciente-select');
            const pacienteId = select.value;
            if (!pacienteId) { alert('Selecciona un paciente primero'); return; }
            const headers = getAuthHeaders();
            const analysisEl = document.getElementById('ia-analysis-result');
            analysisEl.innerHTML = '<p style="color: #fbbf24;">⏳ Cargando análisis general...</p>';
            try {
                const resP = await fetch(`${API_URL}/pacientes?id_paciente=${pacienteId}`, { headers });
                const pacientes = await resP.json();
                const paciente = pacientes[0];
                const resSol = await fetch(`${API_URL}/solicitudes?limit=1000`, { headers });
                const solicitudes = await resSol.json();
                const solicitudesPaciente = solicitudes.filter(s => s.id_paciente === pacienteId);
                const resRes = await fetch(`${API_URL}/resultados?skip=0&limit=1000`, { headers });
                const resultados = await resRes.json();
                const resultadosPaciente = resultados.filter(r => solicitudesPaciente.map(s => s.id_solicitud).includes(r.id_solicitud));
                const analysis = { paciente, edad: new Date().getFullYear() - new Date(paciente.fecha_nacimiento).getFullYear(), genero: paciente.genero === 'M' ? 'Masculino' : 'Femenino', solicitudes_totales: solicitudesPaciente.length, solicitudes_completadas: solicitudesPaciente.filter(s => s.estado === 'completado').length, solicitudes_pendientes: solicitudesPaciente.filter(s => s.estado !== 'completado').length, resultados_totales: resultadosPaciente.length };
                if (resultadosPaciente.length === 0) {
                    analysisEl.innerHTML = `<div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px;"><h3>📊 Análisis General</h3><p><strong>Paciente:</strong> ${analysis.paciente.nombre}</p><p>⚠️ No hay resultados para este paciente.</p></div>`;
                    return;
                }
                const resultData = { id_paciente: pacienteId, edad: analysis.edad, sexo: paciente.genero === 'M' ? 'masculino' : 'femenino', historial_clinico: paciente.historial_clinico, resultados: {}, valores_criticos: [] };
                resultadosPaciente.forEach(r => { resultData.resultados[r.id_prueba] = r.resultado; });
                const resIA = await fetch(`${API_URL}/ai/interpret-results`, { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify(resultData) });
                const iaData = await resIA.json();
                const html = `<div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px;"><h3>📊 Análisis General del Paciente</h3><p><strong>Paciente:</strong> ${analysis.paciente.nombre} ${analysis.paciente.apellido_paterno}</p><p><strong>Edad:</strong> ${analysis.edad} años | <strong>Género:</strong> ${analysis.genero}</p><p>${iaData.interpretation?.resumen || 'Análisis completado'}</p></div>`;
                analysisEl.innerHTML = html;
            } catch (error) {
                console.error('Error in general analysis:', error);
                analysisEl.innerHTML = `<p style="color: #ef4444;">❌ Error: ${error.message}</p>`;
            }
        }

        async function analyzePatientResults() {
            const select = document.getElementById('ia-paciente-select');
            const pacienteId = select.value;
            if (!pacienteId) { alert('Selecciona un paciente primero'); return; }
            const headers = getAuthHeaders();
            const analysisEl = document.getElementById('ia-analysis-result');
            analysisEl.innerHTML = '<p style="color: #fbbf24;">⏳ Cargando resultados específicos...</p>';
            try {
                const resP = await fetch(`${API_URL}/pacientes?id_paciente=${pacienteId}`, { headers });
                const pacientes = await resP.json();
                const paciente = pacientes[0];
                const resSol = await fetch(`${API_URL}/solicitudes?limit=1000`, { headers });
                const solicitudes = await resSol.json();
                const solicitudesPaciente = solicitudes.filter(s => s.id_paciente === pacienteId);
                const resRes = await fetch(`${API_URL}/resultados?skip=0&limit=1000`, { headers });
                const resultados = await resRes.json();
                const resultadosPaciente = resultados.filter(r => solicitudesPaciente.map(s => s.id_solicitud).includes(r.id_solicitud));
                if (resultadosPaciente.length === 0) { analysisEl.innerHTML = '<p style="color: #fbbf24;">⚠️ No hay resultados registrados</p>'; return; }
                let html = `<div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px;"><h3>🔬 Resultados del Paciente</h3><p><strong>Paciente:</strong> ${paciente.nombre} | <strong>Total:</strong> ${resultadosPaciente.length}</p><table style="width:100%; margin-top:10px;"><thead><tr><th>Prueba</th><th>Valor</th><th>Estado</th></tr></thead><tbody>`;
                resultadosPaciente.forEach(r => {
                    const isAbnormal = r.resultado > 150 || r.resultado < 50;
                    html += `<tr><td>${r.id_prueba}</td><td>${r.resultado}</td><td style="color:${isAbnormal ? '#ef4444' : '#22c55e'}">${isAbnormal ? '⚠️ Anormal' : '✅ Normal'}</td></tr>`;
                });
                html += '</tbody></table></div>';
                analysisEl.innerHTML = html;
            } catch (error) {
                console.error('Error in results analysis:', error);
                analysisEl.innerHTML = `<p style="color: #ef4444;">❌ Error: ${error.message}</p>`;
            }
        }
'''
    # Insertar antes del script de chatbot
    chatbot_pattern = r'(<script src="\{% static \'js/chatbot\.js\' %\}"></script>)'
    medico_content = re.sub(chatbot_pattern, ia_js_functions + r'\n    \1', medico_content)
    print("✅ Funciones JavaScript del Asistente IA agregadas")

    with open(medico_filepath, 'w', encoding='utf-8') as f:
        f.write(medico_content)
    print(f"✅ medico_dashboard.html actualizado correctamente\n")
else:
    print("⚠️ medico_dashboard.html ya tiene Asistente IA\n")


# ============================================
# PARTE 2: Revisar y corregir laboratorista_dashboard
# ============================================

lab_filepath = 'frontend/templates/dashboard/laboratorista_dashboard.html'

with open(lab_filepath, 'r', encoding='utf-8') as f:
    lab_content = f.read()

print("=" * 60)
print("Revisando laboratorista_dashboard.html")
print("=" * 60)

# Buscar problemas comunes
issues_found = []

# 1. Verificar si hay funciones JavaScript fuera de etiquetas <script>
script_tags = re.findall(r'<script[^>]*>.*?</script>', lab_content, re.DOTALL)
print(f"✅ Se encontraron {len(script_tags)} bloques <script>")

# 2. Verificar si hay llaves desbalanceadas en JavaScript
for i, script in enumerate(script_tags):
    open_braces = script.count('{')
    close_braces = script.count('}')
    if open_braces != close_braces:
        issues_found.append(f"Script #{i+1}: Llaves desbalanceadas ({open_braces} abiertas, {close_braces} cerradas)")

if issues_found:
    print("⚠️ Problemas encontrados:")
    for issue in issues_found:
        print(f"  - {issue}")
else:
    print("✅ No se encontraron problemas de llaves desbalanceadas")

# 3. Verificar si el handler de loadSectionData está completo
if "async function loadSectionData" in lab_content:
    print("✅ Función loadSectionData encontrada")
else:
    print("⚠️ Función loadSectionData NO encontrada")

# 4. Verificar si hay secciones sin handler
sections = re.findall(r'<section id="([^"]+)"', lab_content)
print(f"✅ Secciones encontradas: {', '.join(sections)}")

# 5. Verificar si hay funciones duplicadas o mal cerradas
function_defs = re.findall(r'(?:async\s+)?function\s+(\w+)\s*\(', lab_content)
print(f"✅ Funciones JavaScript encontradas: {len(function_defs)}")

# Buscar funciones duplicadas
from collections import Counter
func_counts = Counter(function_defs)
duplicates = {k: v for k, v in func_counts.items() if v > 1}
if duplicates:
    print(f"⚠️ Funciones duplicadas: {duplicates}")
else:
    print("✅ No hay funciones duplicadas")

print("\n" + "=" * 60)
print("Revisión completada")
print("=" * 60)