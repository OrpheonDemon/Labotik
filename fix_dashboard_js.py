#!/usr/bin/env python3
"""
Move the injected JS function INSIDE the main <script> block.
The original inject script put it AFTER </script>, but it needs to be BEFORE.
"""

# The full JS block we want to inject (already inserted in the file, but in the wrong location)
INNER_JS = '''
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
                    container.innerHTML = '<div style="text-align:center; padding:40px; color:#e74c3c;">Error cargando solicitudes. C\u00f3digo: ' + res.status + '</div>';
                    return;
                }
                const items = await res.json();
                if (!Array.isArray(items) || items.length === 0) {
                    container.innerHTML = '<div style="text-align:center; padding:40px; color:#2ecc71;">\u2705 No hay solicitudes pendientes de pago.</div>';
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
                            <th style="padding:12px 14px; text-align:center; color:var(--text-cream); font-size:13px;">Acci\u00f3n</th>
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
                            <button onclick="pagarSolicitudUI(${s.id_solicitud})" style="padding:8px 16px; background:linear-gradient(135deg, var(--accent-gold), var(--chocolate-light)); color:#1e0f08; border:none; border-radius:8px; font-weight:600; cursor:pointer; font-size:12px;">\ud83d\udcb0 Pagar</button>
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
            const metodoPago = prompt('M\u00e9todo de pago (efectivo, tarjeta, qr_simple, transferencia):', 'efectivo');
            if (metodoPago === null) return;
            if (!confirm(`\u00bfConfirmar el pago total de la Solicitud #${idSolicitud}?\\n\\nM\u00e9todo: ${metodoPago}\\nEsto cambiar\u00e1 el estado a pagado_total.`)) {
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
                alert(`\u2705 ${data.mensaje || 'Pago registrado exitosamente'}\\n\\nID Pago: ${data.id_pago}\\nMonto: Bs ${data.monto.toFixed(2)}`);
                cargarSolicitudesNoPagadas();
            } catch (err) {
                console.error('Error al pagar solicitud:', err);
                alert('\u274c Error al pagar: ' + err.message);
            }
        }
'''


def fix_dashboard(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'pagarSolicitudUI' in content and 'async function cargarSolicitudesNoPagadas' in content:
        # Already correct
        print(f'  {path}: already correct')
        return

    # Find the malformed JS - it's after </script> and before <script src="...chatbot.js">
    # We need to remove it from there and insert before </script> of main script
    if '// SOLICITUDES NO PAGADAS' in content or 'cargarSolicitudesNoPagadas() {' in content:
        # Find and remove the bad section
        start = content.find('        // SOLICITUDES NO PAGADAS')
        if start == -1:
            start = content.find('// SOLICITUDES NO PAGADAS')
        if start == -1:
            start = content.find('async function cargarSolicitudesNoPagadas')
        if start > 0:
            # Find the end of the function (look for the last } before </script> reference)
            # We'll find the last pagarSolicitudUI function
            end_marker = "alert('\\u274c Error al pagar: ' + err.message);"
            # Or just go to the next </script> (since the bad code is between main </script> and chatbot)
            end_idx = content.find('</script>', start)
            if end_idx > start:
                # Remove from start to end_idx
                bad_block = content[start:end_idx]
                # Validate
                if 'cargarSolicitudesNoPagadas' in bad_block:
                    content = content[:start] + content[end_idx:]
                    print(f'  {path}: removed bad block ({len(bad_block)} chars)')

    # Now insert the proper JS before the main </script> tag
    # The main </script> closes the main <script> block. Find the one BEFORE the <script src="chatbot">
    chatbot_idx = content.find('<script src="{% static \'js/chatbot.js\' %}">')
    if chatbot_idx < 0:
        chatbot_idx = content.find('<script src="{% static "js/chatbot.js" %}">')
    if chatbot_idx > 0:
        # Find the </script> that comes BEFORE the chatbot script
        main_close = content.rfind('</script>', 0, chatbot_idx)
        if main_close > 0:
            # Insert INNER_JS before </script>
            content = content[:main_close] + INNER_JS + '\n' + content[main_close:]
            print(f'  {path}: inserted JS before main </script>')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    base = r'c:\Users\Rothe\Rotherick\Labotik Oficial\Labotik-Rotherick\frontend\templates\dashboard'
    for f in ['recepcionista_dashboard.html', 'admin_dashboard.html', 'paciente_dashboard.html']:
        fix_dashboard(f'{base}\\{f}')
    print('Done')
