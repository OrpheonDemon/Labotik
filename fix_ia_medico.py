"""
Script para agregar el Asistente IA completo al dashboard de médicos.
Copia la implementación del admin_dashboard.html y la adapta para medico_dashboard.html
"""

import re

# Botón del menú lateral para el Asistente IA
IA_MENU_BUTTON = '''                    <li class="menu-item">
                        <a href="#" onclick="navigateMenu(event, 'ia-assistant', 'Asistente IA')">
                            <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12a9 9 0 11-18 0 9 9 0 0118 0zm0 0h-1m-12 0H3m14.364 5.636l-.707-.707M12 21v-1m-6.364-1.636l.707-.707" />
                            </svg>
                            Asistente IA 🧠
                        </a>
                    </li>
'''

# Sección HTML del Asistente IA
IA_SECTION_HTML = '''
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
                    <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px;">
                        <h3 style="color: #fff; margin: 0 0 12px; font-size: 16px;">📊 Estado del Sistema IA</h3>
                        <p id="ia-system-status" style="color: rgba(255,255,255,0.8); margin: 0; line-height: 1.6;">Iniciando conexión con motor IA... Verifica que Ollama esté ejecutándose y selecciona un tipo de análisis para comenzar</p>
                    </div>
                    <!-- Modal para mostrar análisis en popup -->
                    <div id="ia-analysis-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; align-items: center; justify-content: center;" onclick="if(event.target.id === 'ia-analysis-modal') closeAnalysisModalMedico();">
                        <div style="background: rgba(255,255,255,0.95); border: 1px solid rgba(0,0,0,0.2); border-radius: 12px; padding: 30px; min-height: 300px; max-height: 85vh; width: 95%; max-width: 900px; color: #333; overflow-y: auto; position: relative; backdrop-filter: blur(8px);">
                            <button onclick="closeAnalysisModalMedico()" style="position: absolute; top: 10px; right: 10px; background: #fff; border: 1px solid #ccc; color: #333; font-size: 24px; cursor: pointer; width: 40px; height: 40px; border-radius: 50%;">×</button>
                            <!-- Análisis por Paciente -->
                            <div style="margin-top: 32px; display:block;">
                                <h2 style="color: #333; margin: 24px 0 16px; font-size: 18px;">👤 Análisis por Paciente</h2>
                                
                                <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                                    <label style="display: block; color: #333; margin-bottom: 12px; font-weight: 600;">Selecciona un paciente:</label>
                                    <select id="ia-paciente-select" onchange="this.value && (document.getElementById('ia-analyze-general').disabled = false, document.getElementById('ia-analyze-results').disabled = false)" style="width: 100%; padding: 12px; background: #fff; color: #333; border: 1px solid #ccc; border-radius: 8px; font-size: 14px;">
                                        <option value="">-- Cargando pacientes --</option>
                                    </select>
                                    
                                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 16px;">
                                        <button id="ia-analyze-general" disabled onclick="analyzePatientGeneral()" style="padding: 12px; background: linear-gradient(135deg, #c89666 0%, #dfaf7e 100%); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 5px 15px rgba(200, 150, 102, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">📊 Análisis General</button>
                                        <button id="ia-analyze-results" disabled onclick="analyzePatientResults()" style="padding: 12px; background: linear-gradient(135deg, #c89666 0%, #dfaf7e 100%); color: #fff; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 5px 15px rgba(200, 150, 102, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">🔬 Analizar Resultados</button>
                                    </div>
                                </div>
                                
                                <div id="ia-analysis-result" style="display: none; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 12px; padding: 20px; min-height: 100px; color: #333;">ℹ️ Selecciona un paciente y elige un tipo de análisis para comenzar</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
'''

# Funciones JavaScript del Asistente IA
IA_JAVASCRIPT = '''
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
            const modal = document.getElementById('ia-analysis-modal');
            modal.style.display = 'flex';
            const analysisEl = document.getElementById('ia-analysis-result');
            analysisEl.style.display = 'block';
            analysisEl.innerHTML = 'ℹ️ Selecciona un paciente y elige un tipo de análisis para comenzar';
            checkOllamaStatus();
            loadPatientsForAnalysis();
        }

        async function analyzePatientGeneral() {
            const select = document.getElementById('ia-paciente-select');
            const pacienteId = select.value;
            
            if (!pacienteId) {
                alert('Selecciona un paciente primero');
                return;
            }
            
            const headers = getAuthHeaders();
            const analysisEl = document.getElementById('ia-analysis-result');
            const modal = document.getElementById('ia-analysis-modal');
            modal.style.display = 'flex';
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
                const resultadosPaciente = resultados.filter(r => 
                    solicitudesPaciente.map(s => s.id_solicitud).includes(r.id_solicitud)
                );
                
                const analysis = {
                    paciente: paciente,
                    edad: new Date().getFullYear() - new Date(paciente.fecha_nacimiento).getFullYear(),
                    genero: paciente.genero === 'M' ? 'Masculino' : 'Femenino',
                    solicitudes_totales: solicitudesPaciente.length,
                    solicitudes_completadas: solicitudesPaciente.filter(s => s.estado === 'completado').length,
                    solicitudes_pendientes: solicitudesPaciente.filter(s => s.estado !== 'completado').length,
                    resultados_totales: resultadosPaciente.length
                };
                
                if (resultadosPaciente.length === 0) {
                    analysisEl.innerHTML = `
                    <div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #333; margin-top: 0;">📊 Análisis General del Paciente</h3>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Paciente:</strong> ${analysis.paciente.nombre} ${analysis.paciente.apellido_paterno}</p>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Edad:</strong> ${analysis.edad} años | <strong>Género:</strong> ${analysis.genero}</p>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Historial Clínico:</strong> ${analysis.paciente.historial_clinico || 'No registrado'}</p>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 16px;">
                            <div style="background: rgba(59, 130, 246, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">SOLICITUDES</p><h4 style="color: #3b82f6; margin: 8px 0; font-size: 20px;">${analysis.solicitudes_totales}</h4></div>
                            <div style="background: rgba(34, 197, 94, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">COMPLETADAS</p><h4 style="color: #22c55e; margin: 8px 0; font-size: 20px;">${analysis.solicitudes_completadas}</h4></div>
                            <div style="background: rgba(251, 191, 36, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">PENDIENTES</p><h4 style="color: #fbbf24; margin: 8px 0; font-size: 20px;">${analysis.solicitudes_pendientes}</h4></div>
                            <div style="background: rgba(239, 68, 68, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">RESULTADOS</p><h4 style="color: #ef4444; margin: 8px 0; font-size: 20px;">${analysis.resultados_totales}</h4></div>
                        </div>
                        <p style="color: rgba(0,0,0,0.7); margin-top: 16px; font-size: 13px;">⚠️ No hay resultados para este paciente, solo se muestran estadísticas generales.</p>
                    </div>`;
                    return;
                }
                
                const resultData = {
                    id_paciente: pacienteId,
                    edad: analysis.edad,
                    sexo: paciente.genero === 'M' ? 'masculino' : 'femenino',
                    historial_clinico: paciente.historial_clinico,
                    resultados: {},
                    valores_criticos: []
                };
                
                resultadosPaciente.forEach(r => {
                    resultData.resultados[r.id_prueba] = r.resultado;
                    if (typeof r.resultado === 'number' && (r.resultado > 140 || r.resultado < 45)) {
                        resultData.valores_criticos.push(r.id_prueba);
                    }
                });
                
                const resIAInterpret = await fetch(`${API_URL}/ai/interpret-results`, {
                    method: 'POST',
                    headers: {
                        ...headers,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(resultData)
                });
                const iaData = await resIAInterpret.json();
                
                const patologiasActuales = parsePatologias(iaData.interpretation?.resumen || '');
                const patologiasFuturas = predictFuturePathologies(paciente, resultData);
                
                const html = `
                    <div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #333; margin-top: 0;">📊 Análisis General del Paciente</h3>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Paciente:</strong> ${analysis.paciente.nombre} ${analysis.paciente.apellido_paterno}</p>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Edad:</strong> ${analysis.edad} años | <strong>Género:</strong> ${analysis.genero}</p>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Historial Clínico:</strong> ${analysis.paciente.historial_clinico || 'No registrado'}</p>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 16px;">
                            <div style="background: rgba(59, 130, 246, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">SOLICITUDES</p><h4 style="color: #3b82f6; margin: 8px 0; font-size: 20px;">${analysis.solicitudes_totales}</h4></div>
                            <div style="background: rgba(34, 197, 94, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">COMPLETADAS</p><h4 style="color: #22c55e; margin: 8px 0; font-size: 20px;">${analysis.solicitudes_completadas}</h4></div>
                            <div style="background: rgba(251, 191, 36, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">PENDIENTES</p><h4 style="color: #fbbf24; margin: 8px 0; font-size: 20px;">${analysis.solicitudes_pendientes}</h4></div>
                            <div style="background: rgba(239, 68, 68, 0.3); padding: 12px; border-radius: 8px; text-align: center;"><p style="color: rgba(0,0,0,0.7); margin: 0; font-size: 12px;">RESULTADOS</p><h4 style="color: #ef4444; margin: 8px 0; font-size: 20px;">${analysis.resultados_totales}</h4></div>
                        </div>
                        <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
                            <div style="background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; padding: 16px; border-radius: 8px;">
                                <p style="color: rgba(0,0,0,0.9); margin: 0 0 12px; font-weight: 600;"><strong>🏥 Patologías Actuales</strong></p>
                                <div style="color: rgba(0,0,0,0.8); font-size: 14px;">
                                    ${patologiasActuales.length > 0 ? patologiasActuales.map(p => `<p style="margin: 6px 0;">• ${p}</p>`).join('') : '<p style="color: rgba(0,0,0,0.6);">No se detectan patologías significativas</p>'}
                                </div>
                            </div>
                            <div style="background: rgba(251, 191, 36, 0.15); border-left: 4px solid #fbbf24; padding: 16px; border-radius: 8px;">
                                <p style="color: rgba(0,0,0,0.9); margin: 0 0 12px; font-weight: 600;"><strong>🔮 Patologías Potenciales</strong></p>
                                <div style="color: rgba(0,0,0,0.8); font-size: 14px;">
                                    ${patologiasFuturas.length > 0 ? patologiasFuturas.map(p => `<p style="margin: 6px 0;">⚡ ${p}</p>`).join('') : '<p style="color: rgba(0,0,0,0.6);">Riesgo futuro bajo según datos actuales</p>'}
                                </div>
                            </div>
                        </div>
                        <p style="color: rgba(0,0,0,0.7); margin-top: 16px; font-size: 13px;">✅ Análisis general completado con IA sobre todos los resultados del paciente.</p>
                    </div>
                `;
                
                analysisEl.innerHTML = html;
            } catch (error) {
                console.error('Error in general analysis:', error);
                analysisEl.innerHTML = `<p style="color: #ef4444;">❌ Error: ${error.message}</p>`;
            }
        }

        async function analyzePatientResults() {
            const select = document.getElementById('ia-paciente-select');
            const pacienteId = select.value;
            
            if (!pacienteId) {
                alert('Selecciona un paciente primero');
                return;
            }
            
            const headers = getAuthHeaders();
            const analysisEl = document.getElementById('ia-analysis-result');
            const modal = document.getElementById('ia-analysis-modal');
            modal.style.display = 'flex';
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
                const resultadosPaciente = resultados.filter(r => 
                    solicitudesPaciente.map(s => s.id_solicitud).includes(r.id_solicitud)
                );
                
                if (resultadosPaciente.length === 0) {
                    analysisEl.innerHTML = '<p style="color: #fbbf24;">⚠️ No hay resultados registrados para este paciente</p>';
                    return;
                }
                
                let resultadosHTML = `
                    <div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #333; margin-top: 0;">🔬 Selecciona Resultados para Analizar</h3>
                        <p style="color: rgba(0,0,0,0.9);"><strong>Paciente:</strong> ${paciente.nombre} | <strong>Total de resultados:</strong> ${resultadosPaciente.length}</p>
                        
                        <div style="overflow-x: auto; margin: 16px 0;">
                            <table style="width: 100%; border-collapse: collapse; color: rgba(0,0,0,0.9);">
                                <thead>
                                    <tr style="background: rgba(200, 150, 102, 0.3); border-bottom: 2px solid #c89666;">
                                        <th style="padding: 12px; text-align: left; cursor: pointer;" onclick="toggleAllResultados()">✓</th>
                                        <th style="padding: 12px; text-align: left;">Prueba</th>
                                        <th style="padding: 12px; text-align: center;">Valor</th>
                                        <th style="padding: 12px; text-align: center;">Unidad</th>
                                        <th style="padding: 12px; text-align: center;">Estado</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;
                
                resultadosPaciente.forEach((r, idx) => {
                    const isAbnormal = r.resultado > 150 || r.resultado < 50;
                    const statusColor = isAbnormal ? '#ef4444' : '#22c55e';
                    const statusText = isAbnormal ? '⚠️ Anormal' : '✅ Normal';
                    
                    resultadosHTML += `
                        <tr style="border-bottom: 1px solid rgba(0,0,0,0.1); background: ${idx % 2 === 0 ? 'rgba(0,0,0,0.2)' : 'transparent'};">
                            <td style="padding: 12px;"><input type="checkbox" id="resultado-${r.id_resultado}" checked style="cursor: pointer; width: 18px; height: 18px; accent-color: #c89666;"></td>
                            <td style="padding: 12px;">${r.id_prueba}</td>
                            <td style="padding: 12px; text-align: center; font-weight: 600;">${r.resultado}</td>
                            <td style="padding: 12px; text-align: center;">mg/dL</td>
                            <td style="padding: 12px; text-align: center; color: ${statusColor};">${statusText}</td>
                        </tr>
                    `;
                });
                
                resultadosHTML += `
                                </tbody>
                            </table>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px;">
                            <button onclick="selectAllResults()" style="padding: 10px; background: #c89666; color: #333; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">✓ Seleccionar Todo</button>
                            <button onclick="deselectAllResults()" style="padding: 10px; background: #666; color: #333; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">✗ Deseleccionar Todo</button>
                            <button onclick="performAnalysisIA('${pacienteId}')" style="padding: 10px; background: linear-gradient(135deg, #c89666 0%, #dfaf7e 100%); color: #333; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">🧠 Analizar con IA</button>
                        </div>
                    </div>
                `;
                
                analysisEl.innerHTML = resultadosHTML;
                
            } catch (error) {
                console.error('Error in results analysis:', error);
                analysisEl.innerHTML = `<p style="color: #ef4444;">❌ Error: ${error.message}</p>`;
            }
        }

        function selectAllResults() {
            document.querySelectorAll('input[id^="resultado-"]').forEach(cb => cb.checked = true);
        }

        function deselectAllResults() {
            document.querySelectorAll('input[id^="resultado-"]').forEach(cb => cb.checked = false);
        }

        function toggleAllResultados() {
            const checkboxes = document.querySelectorAll('input[id^="resultado-"]');
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            checkboxes.forEach(cb => cb.checked = !allChecked);
        }

        async function performAnalysisIA(pacienteId) {
            const selectedResultados = Array.from(document.querySelectorAll('input[id^="resultado-"]:checked'))
                .map(cb => cb.id.replace('resultado-', ''));
            
            if (selectedResultados.length === 0) {
                alert('Selecciona al menos un resultado para analizar');
                return;
            }
            
            const headers = getAuthHeaders();
            document.getElementById('ia-analysis-result').innerHTML += '<p style="color: #fbbf24; margin-top: 20px;">⏳ Analizando patologías con IA...</p>';
            
            try {
                const resP = await fetch(`${API_URL}/pacientes?id_paciente=${pacienteId}`, { headers });
                const pacientes = await resP.json();
                const paciente = pacientes[0];
                
                const resSol = await fetch(`${API_URL}/solicitudes?limit=1000`, { headers });
                const solicitudes = await resSol.json();
                const solicitudesPaciente = solicitudes.filter(s => s.id_paciente === pacienteId);
                
                const resRes = await fetch(`${API_URL}/resultados?skip=0&limit=1000`, { headers });
                const resultados = await resRes.json();
                const resultadosPaciente = resultados.filter(r => 
                    solicitudesPaciente.map(s => s.id_solicitud).includes(r.id_solicitud)
                );
                
                const resultData = {
                    id_paciente: pacienteId,
                    edad: new Date().getFullYear() - new Date(paciente.fecha_nacimiento).getFullYear(),
                    sexo: paciente.genero === 'M' ? 'masculino' : 'femenino',
                    historial_clinico: paciente.historial_clinico,
                    resultados: {},
                    valores_criticos: []
                };
                
                resultadosPaciente.forEach(r => {
                    if (selectedResultados.includes(r.id_resultado.toString())) {
                        resultData.resultados[r.id_prueba] = r.resultado;
                    }
                });
                
                const resIA = await fetch(`${API_URL}/ai/interpret-results`, {
                    method: 'POST',
                    headers: {
                        ...headers,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(resultData)
                });
                
                const iaData = await resIA.json();
                
                if (iaData.status === 'success') {
                    const interpretation = iaData.interpretation;
                    const patologiasActuales = parsePatologias(interpretation.resumen);
                    const patologiasFuturas = predictFuturePathologies(paciente, resultData);
                    
                    let analysisHTML = `
                        <div style="background: rgba(0,0,0,0.08); border-radius: 12px; padding: 20px; margin-top: 20px;">
                            <h3 style="color: #333; margin-top: 0;">📊 Análisis IA Completado</h3>
                            
                            <div style="background: rgba(59, 130, 246, 0.2); border-left: 4px solid #3b82f6; padding: 12px; margin: 12px 0; border-radius: 4px;">
                                <p style="color: rgba(0,0,0,0.9); margin: 0;"><strong>📋 Interpretación Clínica:</strong></p>
                                <p style="color: rgba(0,0,0,0.8); margin-top: 8px;">${interpretation.resumen || 'Análisis completado'}</p>
                            </div>
                            
                            ${interpretation.hallazgos ? `
                            <div style="background: rgba(239, 68, 68, 0.2); border-left: 4px solid #ef4444; padding: 12px; margin: 12px 0; border-radius: 4px;">
                                <p style="color: rgba(0,0,0,0.9); margin: 0;"><strong>⚠️ Hallazgos Importantes:</strong></p>
                                <p style="color: rgba(0,0,0,0.8); margin-top: 8px;">${interpretation.hallazgos}</p>
                            </div>
                            ` : ''}
                            
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 16px;">
                                <div style="background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; padding: 16px; border-radius: 8px;">
                                    <p style="color: rgba(0,0,0,0.9); margin: 0 0 12px; font-weight: 600;"><strong>🏥 Patologías Actuales</strong></p>
                                    <div style="color: rgba(0,0,0,0.8); font-size: 14px;">
                                        ${patologiasActuales.length > 0 ? patologiasActuales.map(p => `<p style="margin: 6px 0;">• ${p}</p>`).join('') : '<p style="color: rgba(0,0,0,0.6);">No se detectan patologías significativas</p>'}
                                    </div>
                                </div>
                                
                                <div style="background: rgba(251, 191, 36, 0.15); border-left: 4px solid #fbbf24; padding: 16px; border-radius: 8px;">
                                    <p style="color: rgba(0,0,0,0.9); margin: 0 0 12px; font-weight: 600;"><strong>🔮 Patologías Potenciales (Futuro)</strong></p>
                                    <div style="color: rgba(0,0,0,0.8); font-size: 14px;">
                                        ${patologiasFuturas.length > 0 ? patologiasFuturas.map(p => `<p style="margin: 6px 0;">⚡ ${p}</p>`).join('') : '<p style="color: rgba(0,0,0,0.6);">Pronóstico favorable sin riesgos detectados</p>'}
                                    </div>
                                </div>
                            </div>
                            
                            <p style="color: rgba(0,0,0,0.7); margin-top: 16px; font-size: 12px;">✅ Análisis completado por IA Clínica | Resultados analizados: ${selectedResultados.length}</p>
                        </div>
                    `;
                    
                    document.getElementById('ia-analysis-result').innerHTML += analysisHTML;
                } else {
                    document.getElementById('ia-analysis-result').innerHTML += `<p style="color: #ef4444;">❌ Error en análisis: ${iaData.detail}</p>`;
                }
            } catch (error) {
                console.error('Error in AI analysis:', error);
                document.getElementById('ia-analysis-result').innerHTML += `<p style="color: #ef4444;">❌ Error: ${error.message}</p>`;
            }
        }

        function parsePatologias(texto) {
            const patologias = [];
            const keywords = ['anemia', 'diabetes', 'hipertensión', 'infección', 'inflamación', 'deshidratación', 'desnutrición', 'insuficiencia renal', 'hepatopatía', 'colesterol alto', 'triglicéridos altos', 'hipoglucemia', 'hiperglucemia'];
            
            keywords.forEach(keyword => {
                if (texto && texto.toLowerCase().includes(keyword)) {
                    patologias.push(keyword.charAt(0).toUpperCase() + keyword.slice(1));
                }
            });
            
            return [...new Set(patologias)];
        }

        function predictFuturePathologies(paciente, resultData) {
            const predicciones = [];
            const edad = resultData.edad;
            const resultados = resultData.resultados;
            
            if (edad > 40) {
                if (resultados['glucosa'] && resultados['glucosa'] > 100) predicciones.push('Prediabetes o Diabetes tipo 2');
                if (resultados['colesterol'] && resultados['colesterol'] > 200) predicciones.push('Dislipidemia y riesgo cardiovascular');
            }
            
            if (edad > 50) {
                predicciones.push('Monitoreo de hipertensión recomendado');
                predicciones.push('Evaluación de salud ósea en consideración');
            }
            
            if (paciente.historial_clinico && paciente.historial_clinico.toLowerCase().includes('diabetes')) {
                predicciones.push('Progresión de complicaciones diabéticas');
            }
            
            if (paciente.historial_clinico && paciente.historial_clinico.toLowerCase().includes('hipertensión')) {
                predicciones.push('Riesgo de enfermedad cardiovascular');
            }
            
            return [...new Set(predicciones)];
        }

        function closeAnalysisModalMedico() {
            document.getElementById('ia-analysis-modal').style.display = 'none';
            document.getElementById('ia-analysis-result').innerHTML = '';
        }
'''


def update_medico_dashboard(filepath):
    """Actualiza el dashboard de médicos con el Asistente IA"""
    print(f"Procesando: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya tiene el asistente IA
    if 'ia-assistant' in content and 'Asistente IA' in content:
        print(f"  ⚠️ Ya tiene Asistente IA: {filepath}")
        return True
    
    # 1. Agregar botón del menú lateral (antes de Cerrar Sesión)
    cerrar_sesion_pattern = r'(<li class="menu-item" style="border-top: 1px solid rgba\(255,255,255,0\.1\); margin-top: 20px; padding-top: 20px;">\s*<a href="#" onclick="handleLogout\(\)")'
    content = re.sub(cerrar_sesion_pattern, IA_MENU_BUTTON + r'\n                    \1', content)
    print(f"  ✅ Botón del menú agregado")
    
    # 2. Agregar sección HTML (después de la sección dashboard, antes del ENTITY EDIT MODAL)
    entity_modal_pattern = r'(<!-- ENTITY EDIT MODAL)'
    content = re.sub(entity_modal_pattern, IA_SECTION_HTML + r'\n            \1', content)
    print(f"  ✅ Sección HTML agregada")
    
    # 3. Agregar handler en loadSectionData para ia-assistant
    load_section_pattern = r"(if \(sectionId === 'dashboard'\) \{\s*await loadDashboardStats\(\);\s*\})"
    ia_handler = r"""\1
            if (sectionId === 'ia-assistant') {
                checkOllamaStatus();
                await loadPatientsForAnalysis();
            }"""
    content = re.sub(load_section_pattern, ia_handler, content)
    print(f"  ✅ Handler en loadSectionData agregado")
    
    # 4. Agregar funciones JavaScript antes del script de chatbot
    chatbot_pattern = r'(<script src="\{% static \'js/chatbot\.js\' %\}"></script>)'
    content = re.sub(chatbot_pattern, IA_JAVASCRIPT + r'\n    \1', content)
    print(f"  ✅ Funciones JavaScript agregadas")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✅ Actualizado: {filepath}")
    return True


if __name__ == '__main__':
    filepath = 'frontend/templates/dashboard/medico_dashboard.html'
    
    print("=" * 60)
    print("Agregando Asistente IA al dashboard de médicos")
    print("=" * 60)
    
    try:
        update_medico_dashboard(filepath)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("Proceso completado")
    print("=" * 60)