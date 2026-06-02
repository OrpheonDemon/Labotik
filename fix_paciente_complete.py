import re

with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add IA section before ENTITY EDIT MODAL
ia_html = '''            <!-- ASISTENTE IA SECTION -->
            <section id="ia-assistant" class="dashboard-section" aria-hidden="true">
                <div class="profile-panel">
                    <div class="profile-panel-header">
                        <div>
                            <h1 class="profile-panel-title">🧠 Asistente IA Clínico</h1>
                            <p class="profile-panel-subtitle">Análisis inteligente de resultados de laboratorio con MedGem</p>
                        </div>
                    </div>
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
                    <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
                        <h3 style="color: #fff; margin: 0 0 12px; font-size: 16px;">📊 Estado del Sistema IA</h3>
                        <p id="ia-system-status" style="color: rgba(255,255,255,0.8); margin: 0; line-height: 1.6;">Iniciando conexión con motor IA... Verifica que Ollama esté ejecutándose y selecciona un tipo de análisis para comenzar</p>
                    </div>
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
                    <div style="margin-top: 24px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px;">
                        <h3 style="color: #fff; margin: 0 0 12px; font-size: 16px;">💬 Chat con Asistente IA</h3>
                        <p style="color: rgba(255,255,255,0.6); font-size: 12px; margin: 0 0 12px;">Haz preguntas sobre enfermedades, resultados de laboratorio, biomarcadores y más. Usa el paciente seleccionado para contexto.</p>
                        <div id="ia-chat-messages" style="max-height: 300px; overflow-y: auto; padding: 12px; background: rgba(0,0,0,0.15); border-radius: 10px; margin-bottom: 12px;">
                            <div style="color: rgba(255,255,255,0.4); font-size: 13px; text-align: center; padding: 20px;">💬 Escribe tu pregunta para comenzar</div>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <input id="ia-chat-input" type="text" placeholder="Ej: ¿Qué significa una hemoglobina baja?" onkeydown="if(event.key==='Enter')sendSmartChat()" style="flex: 1; padding: 12px; background: rgba(255,255,255,0.1); color: var(--text-cream); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; font-size: 14px; font-family: 'Inter', sans-serif;">
                            <button onclick="sendSmartChat()" style="padding: 12px 20px; background: linear-gradient(135deg, var(--accent-gold), var(--chocolate-light)); color: #1e0f08; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; white-space: nowrap;">Enviar</button>
                        </div>
                    </div>
                </div>
            </section>

'''

# Insert IA section before ENTITY EDIT MODAL
modal_marker = '            <!-- ENTITY EDIT MODAL'
if modal_marker in content:
    content = content.replace(modal_marker, ia_html + '            ' + modal_marker, 1)
    print("✅ IA HTML section added")
else:
    print("❌ ENTITY EDIT MODAL not found")

# 2. Add IA navigation handling in loadSectionData
old_load_section = '''            if (sectionId === 'dashboard') {
                await loadDashboardStats();
            }
        }'''
new_load_section = '''            if (sectionId === 'dashboard') {
                await loadDashboardStats();
            }
            if (sectionId === 'ia-assistant') {
                checkOllamaStatus();
                await loadPatientsForAnalysis();
            }
        }'''
if old_load_section in content:
    content = content.replace(old_load_section, new_load_section, 1)
    print("✅ IA navigation handler added")
else:
    print("❌ loadSectionData pattern not found")

# 3. Add IA JavaScript functions before the closing </script> tag
ia_js = '''
        // ========== FUNCIONES PARA ASISTENTE IA ==========

        // Cache de pruebas para resolver nombres
        let iaPruebasCache = {};

        async function loadIaPruebasCache() {
            if (Object.keys(iaPruebasCache).length > 0) return;
            try {
                const res = await fetch(`${API_URL}/pruebas?limit=1000`, { headers: getAuthHeaders() });
                if (res.ok) {
                    const pruebas = await res.json();
                    if (Array.isArray(pruebas)) {
                        pruebas.forEach(p => { iaPruebasCache[p.id_prueba] = p.nombre; });
                    }
                }
            } catch (e) { console.error("Error loading pruebas cache:", e); }
        }

        function checkOllamaStatus() {
            fetch(`${API_URL}/ai/status`, { headers: getAuthHeaders() })
                .then(res => res.json())
                .then(data => {
                    const el = document.getElementById('ollama-status');
                    if (el) {
                        const status = data.status || 'desconocido';
                        const isOnline = status === 'online' || status === 'ok';
                        el.innerHTML = `<span style="display:inline-block; width:8px; height:8px; background:${isOnline ? '#22c55e' : '#ef4444'}; border-radius:50%; margin-right:8px;"></span>${isOnline ? 'Conectado' : 'Desconectado'}`;
                    }
                })
                .catch(() => {
                    const el = document.getElementById('ollama-status');
                    if (el) el.innerHTML = `<span style="display:inline-block; width:8px; height:8px; background:#ef4444; border-radius:50%; margin-right:8px;"></span>Error de conexión`;
                });
        }

        async function loadPatientsForAnalysis() {
            const headers = getAuthHeaders();
            try {
                await loadIaPruebasCache();
                const res = await fetch(`${API_URL}/pacientes?limit=1000`, { headers });
                if (!res.ok) throw new Error('Error al cargar pacientes');
                const pacientes = await res.json();
                const select = document.getElementById('ia-paciente-select');
                if (!select) return;
                select.innerHTML = '<option value="">-- Selecciona un paciente --</option>';
                if (Array.isArray(pacientes)) {
                    pacientes.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.id_paciente;
                        opt.textContent = `${p.nombre} ${p.apellido_paterno || ''} ${p.apellido_materno || ''} - ${p.id_paciente}`;
                        select.appendChild(opt);
                    });
                }
            } catch (e) { console.error("Error loading patients:", e); }
        }

        function openIAnalysisPopup() {
            const container = document.getElementById('ia-analysis-container');
            if (container) container.style.display = container.style.display === 'none' ? 'block' : 'none';
        }

        async function analyzePatientGeneral() {
            const pacienteId = document.getElementById('ia-paciente-select')?.value;
            if (!pacienteId) { alert('Selecciona un paciente primero'); return; }
            const resultDiv = document.getElementById('ia-analysis-result');
            if (!resultDiv) return;
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '🔍 Analizando paciente...';
            try {
                const headers = getAuthHeaders();
                const resP = await fetch(`${API_URL}/pacientes/search?id_paciente=${encodeURIComponent(pacienteId)}`, { headers });
                if (!resP.ok) throw new Error('No se pudo cargar el paciente');
                const pacientes = Array.isArray(await resP.json()) ? await resP.json() : [await resP.json()];
                const paciente = pacientes[0] || pacientes;
                
                const resSol = await fetch(`${API_URL}/solicitudes?limit=1000`, { headers });
                const solicitudes = resSol.ok ? await resSol.json() : [];
                const solicitudesPaciente = (Array.isArray(solicitudes) ? solicitudes : []).filter(s => s.id_paciente === pacienteId);
                
                const resRes = await fetch(`${API_URL}/resultados?skip=0&limit=1000`, { headers });
                const resultados = resRes.ok ? await resRes.json() : [];
                const resultadosPaciente = (Array.isArray(resultados) ? resultados : []).filter(r => {
                    return solicitudesPaciente.some(s => s.id_solicitud === r.id_solicitud);
                });
                
                const resIA = await fetch(`${API_URL}/ai/interpret-results`, {
                    method: 'POST',
                    headers: { ...headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pacienteId,
                        patient_name: `${paciente.nombre || ''} ${paciente.apellido_paterno || ''}`.trim(),
                        solicitudes: solicitudesPaciente,
                        resultados: resultadosPaciente
                    })
                });
                const data = await resIA.json();
                resultDiv.innerHTML = `<div style="white-space:pre-wrap; line-height:1.7;">${data.analysis || data.respuesta || data.detail || 'Sin respuesta'}</div>`;
            } catch (e) {
                resultDiv.innerHTML = `❌ Error: ${e.message}`;
            }
        }

        async function analyzePatientResults() {
            const pacienteId = document.getElementById('ia-paciente-select')?.value;
            if (!pacienteId) { alert('Selecciona un paciente primero'); return; }
            const resultDiv = document.getElementById('ia-analysis-result');
            if (!resultDiv) return;
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '🔬 Analizando resultados de laboratorio...';
            try {
                const headers = getAuthHeaders();
                const resP = await fetch(`${API_URL}/pacientes/search?id_paciente=${encodeURIComponent(pacienteId)}`, { headers });
                if (!resP.ok) throw new Error('No se pudo cargar el paciente');
                const pacientes = Array.isArray(await resP.json()) ? await resP.json() : [await resP.json()];
                const paciente = pacientes[0] || pacientes;

                const resSol = await fetch(`${API_URL}/solicitudes?limit=1000`, { headers });
                const solicitudes = resSol.ok ? await resSol.json() : [];
                const solicitudesPaciente = (Array.isArray(solicitudes) ? solicitudes : []).filter(s => s.id_paciente === pacienteId);
                
                const resRes = await fetch(`${API_URL}/resultados?skip=0&limit=1000`, { headers });
                const resultados = resRes.ok ? await resRes.json() : [];
                const resultadosPaciente = (Array.isArray(resultados) ? resultados : []).filter(r => {
                    return solicitudesPaciente.some(s => s.id_solicitud === r.id_solicitud);
                });

                const resIA = await fetch(`${API_URL}/ai/validate-results`, {
                    method: 'POST',
                    headers: { ...headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        patient_id: pacienteId,
                        patient_name: `${paciente.nombre || ''} ${paciente.apellido_paterno || ''}`.trim(),
                        resultados: resultadosPaciente
                    })
                });
                const data = await resIA.json();
                resultDiv.innerHTML = `<div style="white-space:pre-wrap; line-height:1.7;">${data.analysis || data.respuesta || data.detail || 'Sin respuesta'}</div>`;
            } catch (e) {
                resultDiv.innerHTML = `❌ Error: ${e.message}`;
            }
        }

        async function sendSmartChat() {
            const input = document.getElementById('ia-chat-input');
            const question = input?.value?.trim();
            if (!question) return;
            input.value = '';
            const messagesDiv = document.getElementById('ia-chat-messages');
            if (!messagesDiv) return;
            messagesDiv.innerHTML += `<div style="margin-bottom:10px; text-align:right;"><span style="display:inline-block; background:rgba(200,150,102,0.15); color:var(--text-cream); padding:10px 16px; border-radius:14px 14px 4px 14px; max-width:80%; font-size:13px; line-height:1.6; border:1px solid rgba(200,150,102,0.2);">${question}</span></div>`;
            messagesDiv.innerHTML += `<div id="chat-typing" style="margin-bottom:10px;"><span style="display:inline-block; background:rgba(255,255,255,0.05); color:var(--text-muted); padding:10px 16px; border-radius:14px; font-size:13px;">Escribiendo...</span></div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            try {
                const pacSelect = document.getElementById('ia-paciente-select');
                const patientId = pacSelect ? pacSelect.value : null;
                const res = await fetch(`${API_URL}/ai/smart-chat`, {
                    method: 'POST',
                    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question, patient_id: patientId || undefined })
                });
                const typingEl = document.getElementById('chat-typing');
                if (typingEl) typingEl.remove();
                if (!res.ok) {
                    const errData = await res.json().catch(() => null);
                    throw new Error(errData?.detail || `Error ${res.status}`);
                }
                const data = await res.json();
                const respuesta = data.respuesta || data.detail || 'Sin respuesta del asistente.';
                messagesDiv.innerHTML += `<div style="margin-bottom:10px;"><span style="display:inline-block; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.12); color:var(--text-cream); padding:10px 16px; border-radius:14px 14px 14px 4px; max-width:80%; font-size:13px; line-height:1.6;">${respuesta}</span></div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch (error) {
                const typingEl = document.getElementById('chat-typing');
                if (typingEl) typingEl.remove();
                messagesDiv.innerHTML += `<div style="margin-bottom:10px;"><span style="display:inline-block; background:rgba(239,68,68,0.1); color:#ef4444; padding:10px 16px; border-radius:14px; font-size:13px;">❌ ${error.message}</span></div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }
'''

# Insert IA functions before the final </script> tag
script_close = '\n    </script>\n\n    <script src="{% static \'js/chatbot.js\' %}"></script>\n</body>\n</html>'
if script_close in content:
    content = content.replace(script_close, ia_js + '\n    </script>\n\n    <script src="{% static \'js/chatbot.js\' %}"></script>\n</body>\n</html>', 1)
    print("✅ IA JavaScript functions added")
else:
    print("❌ Script closing tag not found")
    # Try alternate pattern
    script_close2 = '    </script>\n\n    <script src="{% static'
    if script_close2 in content:
        idx = content.find(script_close2)
        content = content[:idx] + '\n' + ia_js + '\n' + content[idx:]
        print("✅ IA JS added (alternate pattern)")

with open('frontend/templates/dashboard/paciente_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ File saved successfully")