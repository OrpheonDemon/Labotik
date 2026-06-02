#!/usr/bin/env python3
"""Verify the dashboards contain the new UI."""

for f in [
    r'frontend\templates\dashboard\recepcionista_dashboard.html',
    r'frontend\templates\dashboard\admin_dashboard.html',
    r'frontend\templates\dashboard\paciente_dashboard.html',
]:
    with open(f, 'r', encoding='utf-8') as fp:
        c = fp.read()
    has_section = 'solicitudes-no-pagadas' in c
    has_js = 'cargarSolicitudesNoPagadas' in c
    has_menu = 'Solicitudes No Pagadas' in c
    has_pay = 'pagarSolicitudUI' in c
    print(f)
    print('  section:', has_section, 'js:', has_js, 'menu:', has_menu, 'payfn:', has_pay)
