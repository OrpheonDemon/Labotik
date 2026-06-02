#!/usr/bin/env python3
"""
Properly inject the UI section + JS for unpaid solicitudes into all 3 dashboards.
This version uses utf-8 strict mode (no surrogate issues) and inserts the JS
INSIDE the main <script> block.
"""

UNPAID_HTML = '''
            <!-- SOLICITUDES NO PAGADAS SECTION -->
            <section id="solicitudes-no-pagadas" class="dashboard-section" aria-hidden="true">
                <div class="profile-panel">
                    <div class="profile-panel-header">
                        <div>
                            <h1 class="profile-panel-title">Solicitudes No Pagadas</h1>
                            <p class="profile-panel-subtitle">Listado de solicitudes pendientes de pago. Permite registrar el pago y marcarlas como pagado_total.</p>
                        </div>
                        <div>
                            <button class="btn btn-primary" onclick="cargarSolicitudesNoPagadas()" style="font-size:13px;">&#x1F504; Actualizar</button>
                        </div>
                    </div>
                    <div id="solicitudesNoPagadasContent" style="min-height:300px;">
                        <div style="text-align:center; padding:40px; color:var(--text-muted);">Cargando solicitudes pendientes de pago...</div>
                    </div>
                </div>
            </section>
'''

# Note: using literal unicode to avoid any encoding issues
INNER_JS = r'''
        // ============================================================
        // SOLICITUDES NO PAGADAS - Listar, cobrar y cambiar a pagado_total
        // ============================================================
        async function cargarSolicitudesNoPagadas() {
            const container = document.getElementById('solicitudesNoPagadasContent');
            if (!container) return;
            const headers = getAuthHeaders();
            container.innerHTML = '<div style="text-align:center; padding:40px; color:var(--text-muted);">Cargando solicitudes pendientes de pago...</div>';
            try {
                const res = await fetch(`${API_URL}/pagos/solicitudes/no-pagadas?limit=500`, { headers });
                if (!res.ok) {
                    container.innerHTML = '<div style="text-align:center; padding:40px; color:#e74c3c;">Error cargando solicitudes. C&oacute;digo: ' + res.status + '</div>';
                    return;
                }
                const items = await res.json();
                if (!Array.isArray(items) || items.length === 0) {
                    container.innerHTML = '<div style="text-align:center; padding:40px; color:#2ecc71;">&#x2705; No hay solicitudes pendientes de pago.</div>';
                    return;
                }
                const noPagadoCount = items.filter(x => (x.estado_pago || 'no_pagado') === 'no_pagado').length;
                const parcialCount = items.filter(x => x.estado_pago === 'pagado_parcial').length;
                let html = `
                    <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:24px;">
                        <div style="background:rgba(231,76,60,0.08); border:1px solid rgba(231,76,60,0.25); border-radius:12px; padding:16px;">
                            <p style="color:rgba(255,255,255,0.7); font-size:12px; margin:0 0 8px; text-transform:uppercase;">No Pagadas</p>
                            <h4 style="color:#e74c3c; margin:0; font-size:22px;">${noPagadoCount}</h4>
                        </div>
                        <div style="background:rgba(241,196,15,0.12); border:1px solid rgba(241,196,15,0.25); border-radius:12px; padding:16px;">
                            <p style="color:rgba(255,255,255,0.7); font-size:12px; margin:0 0 8px; text-transform:uppercase;">Pago Parcial</p>
                            <h4 style="color:#f1c40f; margin:0; font-size:22px;">${parcialCount}</h4>
                        </div>
                        <div style="background:rgba(46,204,113,0.12); border:1px solid rgba(46,204,113,0.25); border-radius:12px; padding:16px;">
                            <p style="color:rgba(255,255,255,0.7); font-size:12px; margin:0 0 8px; text-transform:uppercase;">Total Pendientes</p>
                            <h4 style="color:#2ecc71; margin:0; font-size:22px;">${items.length}</h4>
                        </div>
                    </div>
                `;
                html += `
                    <div style="overflow-x:auto;">
                    <table style="width:100%; border-collapse:collapse; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.14); border-radius:12px; overflow:hidden;">
                        <thead><tr style="background:rgba(255,255,255,0.1);">
                            <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">ID</th>
                            <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Paciente</th>
                            <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Pruebas</th>
                            <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Prioridad</th>
                            <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Estado Pago</th>
                            <th style="padding:12px 14px; text-align:left; color:var(--text-cream); font-size:13px;">Fecha</th>
                            <th style="padding:12px 14px; text-align:center; color:var(--text-cream); font-size:13px;">Acci&oacute;n</th>
                        </tr></thead><tbody>
                `;
                items.forEach(s => {
                    const estadoPago = s.estado_pago || 'no_pagado';
                    const ec = estadoPago === 'pagado_total' ? '#2ecc71' : (estadoPago === 'pagado_parcial' ? '#f1c40f' : '#e74c3c');
                    const ecRgb = estadoPago === 'pagado_total' ? '46,204,113' : (estadoPago === 'pagado_parcial' ? '241,196,15' : '231,76,60');
                    const prioColor = s.prioridad === 'alta' ? '#e74c3c' : (s.prioridad === 'media' ? 'var(--accent-gold)' : '#2ecc71');
                    const prioBg = s.prioridad === 'alta' ? 'rgba(231,76,60,0.15)' : (s.prioridad === 'media' ? 'rgba(200,150,102,0.15)' : 'rgba(46,204,113,0.15)');
                    const pruebas = (s.detalles || []).map(d => `Prueba #${d.id_prueba}`).join(', ') || 'Sin pruebas';
                    const pacName = s.paciente_nombre || s.id_paciente || '-';
                    const fecha = s.fecha_solicitud ? new Date(s.fecha_solicitud).toLocaleDateString('es-BO') : (s.created_at ? new Date(s.created_at).toLocaleDateString('es-BO') : '-');
                    html += `<tr style="border-top:1px solid rgba(255,255,255,0.08);">
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px;">${s.id_solicitud}</td>
                        <td style="padding:10px 14px; color:var(--text-cream); font-size:13px; max-width:240px; word-wrap:break-word;">${pacName}</td>
                        <td style="padding:10px 14px; color:var(--text-muted); font-size:12px; max-width:280px; word-wrap:break-word;">${pruebas}</td>
                        <td style="padding:10px 14px;">
                            <span style="background:${prioBg}; color:${prioColor}; border:1px solid ${prioColor}40; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600; text-transform:uppercase;">${s.prioridad || 'media'}</span>
                        </td>
                        <td style="padding:10px 14px;">
                            <span style="background:rgba(${ecRgb},0.15); color:${ec}; padding:4px 10px; border-radius:20px; font-size:11px; font-weight:600; text-transform:uppercase;">${estadoPago}</span>
                        </td>
                        <td style="padding:10px 14px; color:var(--text-muted); font-size:13px;">${fecha}</td>
                        <td style="padding:10px 14px; text-align:center;">
                            <button onclick="pagarSolicitudUI(${s.id_solicitud})" style="padding:8px 16px; background:linear-gradient(135deg, var(--accent-gold), var(--chocolate-light)); color:#1e0f08; border:none; border-radius:8px; font-weight:600; cursor:pointer; font-size:12px;">&#x1F4B0; Pagar</button>
                        </td>
                    </tr>`;
                });
                html += '</tbody></table></div>';
                container.innerHTML = html;
            } catch (err) {
                console.error('Error cargando solicitudes no pagadas:', err);
                container.innerHTML = '<div style="text-align:center; padding:40px; color:#e74c3c;">Error al cargar solicitudes: ' + err.message + '</div>';
            }
        }

        async function pagarSolicitudUI(idSolicitud) {
            const metodoPago = prompt('M&eacute;todo de pago (efectivo, tarjeta, qr_simple, transferencia):', 'efectivo');
            if (metodoPago === null) return;
            if (!confirm('Confirmar el pago total de la Solicitud #' + idSolicitud + '? Metodo: ' + metodoPago + '. Esto cambiara el estado a pagado_total.')) {
                return;
            }
            try {
                const url = `${API_URL}/pagos/solicitudes/${idSolicitud}/pagar?metodo_pago=${encodeURIComponent(metodoPago)}&referencia=UI-${Date.now()}`;
                const res = await fetch(url, { method: 'POST', headers: getAuthHeaders() });
                if (!res.ok) {
                    const err = await res.json().catch(() => null);
                    throw new Error(err?.detail || 'Error al procesar el pago');
                }
                const data = await res.json();
                alert('Pago registrado: ' + (data.mensaje || 'OK') + '. ID Pago: ' + data.id_pago + '. Monto: Bs ' + data.monto.toFixed(2));
                cargarSolicitudesNoPagadas();
            } catch (err) {
                console.error('Error al pagar solicitud:', err);
                alert('Error al pagar: ' + err.message);
            }
        }
'''


def fix_dashboard(path):
    # Read as bytes to avoid any surrogate issues
    with open(path, 'rb') as f:
        raw = f.read()
    # Decode ignoring errors, replace surrogateescape back to normal replacement
    content = raw.decode('utf-8', errors='replace')

    # 1) If already injected (has 'pagarSolicitudUI' function), skip
    if 'async function pagarSolicitudUI' in content:
        print(f'  {path}: already injected')
        return

    # 2) Add HTML section if not present
    if 'id="solicitudes-no-pagadas"' not in content:
        # Insert before </main>
        marker = '</main>'
        idx = content.find(marker)
        if idx > 0:
            content = content[:idx] + UNPAID_HTML + content[idx:]
            print(f'  {path}: added HTML section')

    # 3) Add menu item to sidebar if not present
    if 'navigateMenu(event, \'solicitudes-no-pagadas\'' not in content and 'navigateMenu(event, "solicitudes-no-pagadas"' not in content:
        marker = 'Cerrar Sesi&oacute;n'
        idx = content.find(marker)
        if idx == -1:
            marker = 'Cerrar Sesión'
            idx = content.find(marker)
        if idx > 0:
            li_start = content.rfind('<li class="menu-item"', 0, idx)
            if li_start > 0:
                menu_item = '''                    <li class="menu-item">
                        <a href="#" onclick="navigateMenu(event, 'solicitudes-no-pagadas', 'Solicitudes No Pagadas')">
                            <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Solicitudes No Pagadas
                        </a>
                    </li>
'''
                content = content[:li_start] + menu_item + content[li_start:]
                print(f'  {path}: added menu item')

    # 4) Add JS inside the main <script> block (before its </script>)
    # Find the FIRST <script> tag and its matching </script>
    if 'cargarSolicitudesNoPagadas' not in content:
        # Find first <script>
        first_script = content.find('<script>')
        if first_script > 0:
            # Find the matching </script> for this first <script>
            end_script = content.find('</script>', first_script)
            if end_script > 0:
                content = content[:end_script] + INNER_JS + '\n' + content[end_script:]
                print(f'  {path}: inserted JS before main </script>')

    # 5) Add navigation case in loadSectionData (if has pagos case)
    if 'sectionId === \'solicitudes-no-pagadas\'' not in content:
        pattern = "if (sectionId === 'pagos') {"
        idx = content.find(pattern)
        if idx > 0:
            # find the matching close brace
            i = content.find('{', idx)
            brace_count = 0
            j = i
            while j < len(content):
                if content[j] == '{':
                    brace_count += 1
                elif content[j] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                j += 1
            block_end = j + 1
            addition = "\n            if (sectionId === 'solicitudes-no-pagadas') {\n                cargarSolicitudesNoPagadas();\n            }"
            content = content[:block_end] + addition + content[block_end:]
            print(f'  {path}: added loadSectionData case')

    # Write back as utf-8
    with open(path, 'wb') as f:
        f.write(content.encode('utf-8', errors='replace'))
    print(f'  {path}: saved')


if __name__ == '__main__':
    base = r'c:\Users\Rothe\Rotherick\Labotik Oficial\Labotik-Rotherick\frontend\templates\dashboard'
    for f in ['recepcionista_dashboard.html', 'admin_dashboard.html', 'paciente_dashboard.html']:
        fix_dashboard(f'{base}\\{f}')
    print('Done')
