"""
Script cuidadoso para agregar la sección de pagos con 3 tablas en los dashboards.
No usa regex complejos que puedan dañar el código existente.
"""

# HTML de la sección de pagos completa
PAGOS_SECTION_HTML = '''
            <!-- PAGOS SECTION -->
            <section id="pagos" class="dashboard-section" aria-hidden="true">
                <div class="profile-panel">
                    <div class="profile-panel-header">
                        <div>
                            <h1 class="profile-panel-title">Pagos</h1>
                            <p class="profile-panel-subtitle">Gestión de pagos, facturas e historial de transacciones.</p>
                        </div>
                        <div>
                            <button class="btn btn-primary" onclick="cargarSeccionPagos()" style="font-size:13px;">&#x1F504; Actualizar</button>
                        </div>
                    </div>
                    
                    <!-- TABLA 1: Solicitudes Pendientes de Pago -->
                    <div style="margin-bottom:30px;">
                        <h3 style="color:#fff; margin:0 0 15px; font-size:18px; display:flex; align-items:center; gap:10px;">
                            <span style="background:rgba(231,76,60,0.15); color:#e74c3c; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600;">PENDIENTES</span>
                            Solicitudes Pendientes de Pago
                        </h3>
                        <div style="overflow-x:auto;">
                            <table style="width:100%; border-collapse:collapse; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.14); border-radius:12px; overflow:hidden;">
                                <thead>
                                    <tr style="background:rgba(255,255,255,0.1);">
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">ID</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Paciente</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Pruebas</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Total</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Estado Pago</th>
                                        <th style="padding:12px 14px; text-align:center; color:var(--text-cream); font-size:13px;">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody id="solicitudesPendientesTbody">
                                    <tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando solicitudes pendientes...</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <div id="solicitudesPendientesPagination" style="margin-top:12px; display:flex; align-items:center; gap:8px; justify-content:center;"></div>
                    </div>
                    
                    <!-- TABLA 2: Facturas -->
                    <div style="margin-bottom:30px;">
                        <h3 style="color:#fff; margin:0 0 15px; font-size:18px; display:flex; align-items:center; gap:10px;">
                            <span style="background:rgba(46,204,113,0.15); color:#2ecc71; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600;">FACTURAS</span>
                            Facturas Generadas
                        </h3>
                        <div style="overflow-x:auto;">
                            <table style="width:100%; border-collapse:collapse; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.14); border-radius:12px; overflow:hidden;">
                                <thead>
                                    <tr style="background:rgba(255,255,255,0.1);">
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">ID</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Paciente</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Solicitud</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Total</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Estado</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Fecha</th>
                                        <th style="padding:12px 14px; text-align:center; color:var(--text-cream); font-size:13px;">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody id="facturasTbody">
                                    <tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando facturas...</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <div id="facturasPagination" style="margin-top:12px; display:flex; align-items:center; gap:8px; justify-content:center;"></div>
                    </div>
                    
                    <!-- TABLA 3: Historial de Pagos -->
                    <div>
                        <h3 style="color:#fff; margin:0 0 15px; font-size:18px; display:flex; align-items:center; gap:10px;">
                            <span style="background:rgba(200,150,102,0.15); color:var(--accent-gold); padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600;">HISTORIAL</span>
                            Historial de Pagos
                        </h3>
                        <div style="overflow-x:auto;">
                            <table style="width:100%; border-collapse:collapse; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.14); border-radius:12px; overflow:hidden;">
                                <thead>
                                    <tr style="background:rgba(255,255,255,0.1);">
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">ID Pago</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Factura</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Monto</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Método</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Estado</th>
                                        <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Fecha</th>
                                    </tr>
                                </thead>
                                <tbody id="historialPagosTbody">
                                    <tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando historial...</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <div id="historialPagosPagination" style="margin-top:12px; display:flex; align-items:center; gap:8px; justify-content:center;"></div>
                    </div>
                </div>
                
                <!-- Modal QR para Pago -->
                <div id="pagoQRModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:999; align-items:center; justify-content:center;">
                    <div style="background:var(--glass-bg); border:1px solid var(--glass-border); border-radius:18px; padding:30px; max-width:450px; width:90%; text-align:center; box-shadow:0 20px 40px rgba(0,0,0,0.5);">
                        <h3 style="color:var(--text-white); margin-bottom:15px; font-size:20px;">&#x1F4B3; Pago con Código QR</h3>
                        <div id="pagoQRInfo" style="margin-bottom:15px;">
                            <p style="color:var(--text-cream); font-size:14px; margin:5px 0;">Solicitud: <strong id="pagoQRSolicitudId">-</strong></p>
                            <p style="color:var(--text-cream); font-size:14px; margin:5px 0;">Paciente: <strong id="pagoQRPaciente">-</strong></p>
                            <p style="color:var(--accent-gold); font-size:24px; font-weight:700; margin:10px 0;" id="pagoQRMonto">Bs 0.00</p>
                        </div>
                        <div id="pagoQRImageContainer" style="background:#fff; padding:15px; border-radius:12px; display:inline-block; margin:15px 0;">
                            <img id="pagoQRImage" src="" alt="QR de pago" style="width:200px; height:200px;">
                        </div>
                        <p style="color:var(--text-muted); font-size:12px; margin:10px 0;">Escanee el QR con su aplicación bancaria para realizar el pago</p>
                        <p style="color:var(--text-muted); font-size:11px; word-break:break-all;" id="pagoQRReferencia">Ref: ---</p>
                        <div id="pagoQRStatus" style="margin:15px 0; padding:10px; border-radius:8px; display:none;"></div>
                        <div style="display:flex; gap:10px; justify-content:center; margin-top:20px;">
                            <button class="btn btn-primary" onclick="simularEscaneoQR()" style="background:var(--success-green); color:#fff;">&#x2705; Simular Escaneo y Pagar</button>
                            <button class="btn btn-secondary" onclick="cerrarPagoQRModal()">Cancelar</button>
                        </div>
                    </div>
                </div>
            </section>
'''

# Botón de menú de Pagos
PAGOS_MENU_BUTTON = '''                    <li class="menu-item">
                        <a href="#" onclick="navigateMenu(event, 'pagos', 'Pagos')">
                            <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                            Pagos
                        </a>
                    </li>
'''

# JavaScript para la sección de pagos
PAGOS_SECTION_JS = '''
        // ========== SECCIÓN DE PAGOS - VARIABLES Y FUNCIONES ==========
        let solicitudesPendientesPage = 0;
        let facturasPage = 0;
        let historialPagosPage = 0;
        const pagosPageSize = 5;
        let currentPagoSolicitudId = null;
        let currentPagoMonto = 0;
        let pacientesMap = {};
        let pruebasMap = {};

        async function cargarSeccionPagos() {
            await cargarPacientesMap();
            await cargarPruebasMap();
            await cargarSolicitudesPendientes();
            await cargarFacturas();
            await cargarHistorialPagos();
        }

        async function cargarPacientesMap() {
            const headers = getAuthHeaders();
            try {
                const res = await fetch(`${API_URL}/pacientes?limit=1000`, { headers });
                if (res.ok) {
                    const pacientes = await res.json();
                    pacientesMap = {};
                    pacientes.forEach(p => {
                        pacientesMap[p.id_paciente] = `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim();
                    });
                }
            } catch (e) { console.error('Error cargando pacientes:', e); }
        }

        async function cargarPruebasMap() {
            const headers = getAuthHeaders();
            try {
                const res = await fetch(`${API_URL}/pruebas?limit=1000`, { headers });
                if (res.ok) {
                    const pruebas = await res.json();
                    pruebasMap = {};
                    pruebas.forEach(p => { pruebasMap[p.id_prueba] = p.nombre; });
                }
            } catch (e) { console.error('Error cargando pruebas:', e); }
        }

        async function cargarSolicitudesPendientes(page = 0) {
            solicitudesPendientesPage = page;
            const tbody = document.getElementById('solicitudesPendientesTbody');
            const pagination = document.getElementById('solicitudesPendientesPagination');
            if (!tbody) return;
            
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando...</td></tr>';
            if (pagination) pagination.innerHTML = '';
            
            const headers = getAuthHeaders();
            try {
                const skip = page * pagosPageSize;
                const res = await fetch(`${API_URL}/pagos/solicitudes/no-pagadas?skip=${skip}&limit=${pagosPageSize + 1}`, { headers });
                
                if (!res.ok) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#e74c3c;">Error cargando solicitudes</td></tr>';
                    return;
                }
                
                const items = await res.json();
                const hasNext = items.length > pagosPageSize;
                const pagedItems = items.slice(0, pagosPageSize);
                
                if (!pagedItems.length) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--success-green);">No hay solicitudes pendientes de pago</td></tr>';
                    return;
                }
                
                tbody.innerHTML = '';
                pagedItems.forEach(s => {
                    const tr = document.createElement('tr');
                    tr.style.borderTop = '1px solid rgba(255,255,255,0.08)';
                    
                    const pacienteNombre = pacientesMap[s.id_paciente] || s.paciente_nombre || s.id_paciente;
                    let pruebasNombres = 'Ninguna';
                    if (s.detalles && s.detalles.length > 0) {
                        pruebasNombres = s.detalles.map(d => pruebasMap[d.id_prueba] || `Prueba #${d.id_prueba}`).join(', ');
                    }
                    
                    let total = 0;
                    if (s.detalles && s.detalles.length > 0) {
                        s.detalles.forEach(d => {
                            const cantidad = d.cantidad || 1;
                            total += cantidad * (d.precio_unitario || 0);
                        });
                    }
                    
                    const estadoColor = s.estado_pago === 'pagado_parcial' ? '#f1c40f' : '#e74c3c';
                    const estadoBg = s.estado_pago === 'pagado_parcial' ? 'rgba(241,196,15,0.12)' : 'rgba(231,76,60,0.08)';
                    
                    tr.innerHTML = `
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">${s.id_solicitud}</td>
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">${pacienteNombre}</td>
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px; max-width:200px; white-space:normal;">${pruebasNombres}</td>
                        <td style="padding:10px 14px; color:var(--accent-gold); font-size:13px; font-weight:700;">Bs ${total.toFixed(2)}</td>
                        <td style="padding:10px 14px;"><span style="background:${estadoBg}; color:${estadoColor}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600;">${s.estado_pago}</span></td>
                        <td style="padding:10px 14px; text-align:center;">
                            <button onclick="abrirPagoQRModal(${s.id_solicitud}, '${pacienteNombre.replace(/'/g, "\\'")}', ${total})" style="padding:8px 16px; background:linear-gradient(135deg, var(--accent-gold), var(--chocolate-light)); color:#1e0f08; border:none; border-radius:8px; cursor:pointer; font-size:12px; font-weight:600;">Pagar</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                
                if (pagination) {
                    pagination.style.display = (page > 0 || hasNext) ? 'flex' : 'none';
                    pagination.innerHTML = '';
                    if (page > 0 || hasNext) {
                        const prev = document.createElement('button');
                        prev.className = 'btn';
                        prev.textContent = 'Anterior';
                        prev.disabled = page === 0;
                        prev.onclick = () => cargarSolicitudesPendientes(page - 1);
                        const next = document.createElement('button');
                        next.className = 'btn';
                        next.textContent = 'Siguiente';
                        next.disabled = !hasNext;
                        next.onclick = () => cargarSolicitudesPendientes(page + 1);
                        pagination.appendChild(prev);
                        const pageInfo = document.createElement('span');
                        pageInfo.style.color = 'var(--text-cream)';
                        pageInfo.textContent = ` Página ${page + 1} `;
                        pagination.appendChild(pageInfo);
                        pagination.appendChild(next);
                    }
                }
            } catch (e) {
                console.error('Error:', e);
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#e74c3c;">Error: ' + e.message + '</td></tr>';
            }
        }

        async function cargarFacturas(page = 0) {
            facturasPage = page;
            const tbody = document.getElementById('facturasTbody');
            const pagination = document.getElementById('facturasPagination');
            if (!tbody) return;
            
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando facturas...</td></tr>';
            if (pagination) pagination.innerHTML = '';
            
            const headers = getAuthHeaders();
            try {
                const skip = page * pagosPageSize;
                const res = await fetch(`${API_URL}/facturas/?skip=${skip}&limit=${pagosPageSize + 1}`, { headers });
                
                if (!res.ok) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:#e74c3c;">Error cargando facturas</td></tr>';
                    return;
                }
                
                const items = await res.json();
                const hasNext = items.length > pagosPageSize;
                const pagedItems = items.slice(0, pagosPageSize);
                
                if (!pagedItems.length) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--text-muted);">No hay facturas registradas</td></tr>';
                    return;
                }
                
                tbody.innerHTML = '';
                pagedItems.forEach(f => {
                    const tr = document.createElement('tr');
                    tr.style.borderTop = '1px solid rgba(255,255,255,0.08)';
                    
                    const pacienteNombre = pacientesMap[f.id_paciente] || f.id_paciente;
                    const estadoColor = f.estado_factura === 'pagada_total' ? '#2ecc71' : (f.estado_factura === 'pagada_parcial' ? '#f1c40f' : '#e74c3c');
                    const estadoBg = f.estado_factura === 'pagada_total' ? 'rgba(46,204,113,0.15)' : (f.estado_factura === 'pagada_parcial' ? 'rgba(241,196,15,0.12)' : 'rgba(231,76,60,0.08)';
                    
                    tr.innerHTML = `
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">${f.id_factura}</td>
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">${pacienteNombre}</td>
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">#${f.id_solicitud || '-'}</td>
                        <td style="padding:10px 14px; color:var(--accent-gold); font-size:13px; font-weight:700;">Bs ${f.total.toFixed(2)}</td>
                        <td style="padding:10px 14px;"><span style="background:${estadoBg}; color:${estadoColor}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600;">${f.estado_factura}</span></td>
                        <td style="padding:10px 14px; color:var(--text-muted); font-size:13px;">${f.fecha_emision ? new Date(f.fecha_emision).toLocaleDateString('es-BO') : '-'}</td>
                        <td style="padding:10px 14px; text-align:center;">
                            <button onclick="generarFacturaPDF(${f.id_factura})" style="padding:6px 12px; background:rgba(255,255,255,0.08); color:var(--text-cream); border:1px solid rgba(255,255,255,0.2); border-radius:8px; cursor:pointer; font-size:12px;">PDF</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
                
                if (pagination) {
                    pagination.style.display = (page > 0 || hasNext) ? 'flex' : 'none';
                    pagination.innerHTML = '';
                    if (page > 0 || hasNext) {
                        const prev = document.createElement('button');
                        prev.className = 'btn';
                        prev.textContent = 'Anterior';
                        prev.disabled = page === 0;
                        prev.onclick = () => cargarFacturas(page - 1);
                        const next = document.createElement('button');
                        next.className = 'btn';
                        next.textContent = 'Siguiente';
                        next.disabled = !hasNext;
                        next.onclick = () => cargarFacturas(page + 1);
                        pagination.appendChild(prev);
                        const pageInfo = document.createElement('span');
                        pageInfo.style.color = 'var(--text-cream)';
                        pageInfo.textContent = ` Página ${page + 1} `;
                        pagination.appendChild(pageInfo);
                        pagination.appendChild(next);
                    }
                }
            } catch (e) {
                console.error('Error:', e);
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:#e74c3c;">Error: ' + e.message + '</td></tr>';
            }
        }

        async function cargarHistorialPagos(page = 0) {
            historialPagosPage = page;
            const tbody = document.getElementById('historialPagosTbody');
            const pagination = document.getElementById('historialPagosPagination');
            if (!tbody) return;
            
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">Cargando historial...</td></tr>';
            if (pagination) pagination.innerHTML = '';
            
            const headers = getAuthHeaders();
            try {
                const skip = page * pagosPageSize;
                const res = await fetch(`${API_URL}/pagos/?skip=${skip}&limit=${pagosPageSize + 1}`, { headers });
                
                if (!res.ok) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#e74c3c;">Error cargando historial</td></tr>';
                    return;
                }
                
                const items = await res.json();
                const hasNext = items.length > pagosPageSize;
                const pagedItems = items.slice(0, pagosPageSize);
                
                if (!pagedItems.length) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--text-muted);">No hay pagos registrados</td></tr>';
                    return;
                }
                
                tbody.innerHTML = '';
                pagedItems.forEach(p => {
                    const tr = document.createElement('tr');
                    tr.style.borderTop = '1px solid rgba(255,255,255,0.08)';
                    
                    const estadoColor = p.estado_pago === 'completado' ? '#2ecc71' : '#e74c3c';
                    const estadoBg = p.estado_pago === 'completado' ? 'rgba(46,204,113,0.15)' : 'rgba(231,76,60,0.08)';
                    
                    tr.innerHTML = `
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">${p.id_pago}</td>
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">#${p.id_factura}</td>
                        <td style="padding:10px 14px; color:var(--accent-gold); font-size:13px; font-weight:700;">Bs ${p.monto.toFixed(2)}</td>
                        <td style="padding:10px 14px; color:var(--text-muted); font-size:13px;">${p.metodo_pago}</td>
                        <td style="padding:10px 14px;"><span style="background:${estadoBg}; color:${estadoColor}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600;">${p.estado_pago}</span></td>
                        <td style="padding:10px 14px; color:var(--text-muted); font-size:13px;">${p.fecha_pago ? new Date(p.fecha_pago).toLocaleDateString('es-BO') : '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
                
                if (pagination) {
                    pagination.style.display = (page > 0 || hasNext) ? 'flex' : 'none';
                    pagination.innerHTML = '';
                    if (page > 0 || hasNext) {
                        const prev = document.createElement('button');
                        prev.className = 'btn';
                        prev.textContent = 'Anterior';
                        prev.disabled = page === 0;
                        prev.onclick = () => cargarHistorialPagos(page - 1);
                        const next = document.createElement('button');
                        next.className = 'btn';
                        next.textContent = 'Siguiente';
                        next.disabled = !hasNext;
                        next.onclick = () => cargarHistorialPagos(page + 1);
                        pagination.appendChild(prev);
                        const pageInfo = document.createElement('span');
                        pageInfo.style.color = 'var(--text-cream)';
                        pageInfo.textContent = ` Página ${page + 1} `;
                        pagination.appendChild(pageInfo);
                        pagination.appendChild(next);
                    }
                }
            } catch (e) {
                console.error('Error:', e);
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#e74c3c;">Error: ' + e.message + '</td></tr>';
            }
        }

        async function abrirPagoQRModal(solicitudId, pacienteNombre, monto) {
            currentPagoSolicitudId = solicitudId;
            currentPagoMonto = monto;
            
            document.getElementById('pagoQRSolicitudId').textContent = solicitudId;
            document.getElementById('pagoQRPaciente').textContent = pacienteNombre;
            document.getElementById('pagoQRMonto').textContent = `Bs ${monto.toFixed(2)}`;
            document.getElementById('pagoQRStatus').style.display = 'none';
            
            const qrData = `LABOTIK-PAGO|SOL:${solicitudId}|MONTO:${monto.toFixed(2)}|REF:SOL${solicitudId}-${Date.now()}`;
            const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrData)}`;
            document.getElementById('pagoQRImage').src = qrUrl;
            document.getElementById('pagoQRReferencia').textContent = `Ref: SOL${solicitudId}-${Date.now()}`;
            
            document.getElementById('pagoQRModal').style.display = 'flex';
        }

        function cerrarPagoQRModal() {
            document.getElementById('pagoQRModal').style.display = 'none';
            currentPagoSolicitudId = null;
            currentPagoMonto = 0;
        }

        async function simularEscaneoQR() {
            if (!currentPagoSolicitudId) {
                alert('Error: No hay solicitud seleccionada');
                return;
            }
            
            const statusDiv = document.getElementById('pagoQRStatus');
            statusDiv.style.display = 'block';
            statusDiv.style.background = 'rgba(200,150,102,0.15)';
            statusDiv.style.color = 'var(--accent-gold)';
            statusDiv.textContent = 'Procesando pago...';
            
            const headers = getAuthHeaders();
            
            try {
                const res = await fetch(`${API_URL}/pagos/solicitudes/${currentPagoSolicitudId}/pagar?metodo_pago=qr&monto=${currentPagoMonto}`, {
                    method: 'POST',
                    headers
                });
                
                if (!res.ok) {
                    const err = await res.json().catch(() => null);
                    throw new Error(err?.detail || 'Error al procesar pago');
                }
                
                const result = await res.json();
                
                statusDiv.style.background = 'rgba(46,204,113,0.15)';
                statusDiv.style.color = '#2ecc71';
                statusDiv.textContent = result.mensaje || 'Pago procesado exitosamente';
                
                setTimeout(() => {
                    cerrarPagoQRModal();
                    cargarSeccionPagos();
                }, 2000);
                
            } catch (e) {
                statusDiv.style.background = 'rgba(231,76,60,0.15)';
                statusDiv.style.color = '#e74c3c';
                statusDiv.textContent = 'Error: ' + e.message;
            }
        }

        function generarFacturaPDF(facturaId) {
            const token = getToken();
            const url = `${API_URL}/facturas/${facturaId}/pdf?access_token=${token}`;
            window.open(url, '_blank');
        }
'''


def update_dashboard(filepath):
    """Actualiza un dashboard de manera segura"""
    print(f"Procesando: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Verificar si ya tiene la sección de pagos
    content = ''.join(lines)
    if 'solicitudesPendientesTbody' in content:
        print(f"  ⚠️ Ya tiene sección de pagos: {filepath}")
        return True
    
    # 1. Agregar botón de Pagos en el menú (antes de Cerrar Sesión)
    menu_inserted = False
    for i, line in enumerate(lines):
        if 'Cerrar Sesión' in line and not menu_inserted:
            # Buscar la línea del <li> que contiene Cerrar Sesión
            for j in range(i, max(0, i-10), -1):
                if '<li class="menu-item"' in lines[j]:
                    lines.insert(j, PAGOS_MENU_BUTTON)
                    menu_inserted = True
                    print(f"  ✅ Botón de menú agregado en línea {j}")
                    break
            break
    
    # 2. Agregar sección HTML antes de </main>
    section_inserted = False
    for i, line in enumerate(lines):
        if '</main>' in line:
            lines.insert(i, PAGOS_SECTION_HTML + '\n')
            section_inserted = True
            print(f"  ✅ Sección HTML agregada en línea {i}")
            break
    
    # 3. Agregar handler en loadSectionData
    handler_inserted = False
    for i, line in enumerate(lines):
        if "async function loadSectionData(sectionId)" in line:
            # Buscar la llave de cierre de la función
            brace_count = 0
            for j in range(i, len(lines)):
                if '{' in lines[j]:
                    brace_count += lines[j].count('{')
                if '}' in lines[j]:
                    brace_count -= lines[j].count('}')
                if brace_count == 0 and j > i:
                    # Insertar antes de la llave de cierre
                    handler_code = """
            if (sectionId === 'pagos' || sectionId === 'Pagos') {
                await cargarSeccionPagos();
            }
"""
                    lines.insert(j, handler_code)
                    handler_inserted = True
                    print(f"  ✅ Handler de loadSectionData agregado en línea {j}")
                    break
            break
    
    # 4. Agregar JavaScript antes del script de chatbot
    js_inserted = False
    for i, line in enumerate(lines):
        if "<script src=\"{% static 'js/chatbot.js' %}\"></script>" in line:
            lines.insert(i, PAGOS_SECTION_JS + '\n')
            js_inserted = True
            print(f"  ✅ JavaScript agregado en línea {i}")
            break
    
    # Si no se encontró el script de chatbot, insertar antes de </body>
    if not js_inserted:
        for i, line in enumerate(lines):
            if '</body>' in line:
                lines.insert(i, PAGOS_SECTION_JS + '\n')
                js_inserted = True
                print(f"  ✅ JavaScript agregado antes de </body> en línea {i}")
                break
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"  ✅ Actualizado: {filepath}")
    return True


if __name__ == '__main__':
    dashboards = [
        'frontend/templates/dashboard/admin_dashboard.html',
        'frontend/templates/dashboard/recepcionista_dashboard.html',
        'frontend/templates/dashboard/paciente_dashboard.html',
    ]
    
    print("=" * 60)
    print("Agregando sección de pagos a dashboards")
    print("=" * 60)
    
    for dashboard in dashboards:
        try:
            update_dashboard(dashboard)
        except Exception as e:
            print(f"  ❌ Error en {dashboard}: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print("Proceso completado")
    print("=" * 60)