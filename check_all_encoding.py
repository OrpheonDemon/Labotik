import re

files = [
    'frontend/templates/dashboard/medico_dashboard.html',
    'frontend/templates/dashboard/admin_dashboard.html',
    'frontend/templates/dashboard/recepcionista_dashboard.html',
    'frontend/templates/dashboard/paciente_dashboard.html',
    'frontend/templates/dashboard/laboratorista_dashboard.html'
]

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    mojibake = re.findall(r'[\xc0-\xff][\x80-\xff]', content)
    name = f.split('/')[-1]
    print(f'{name}: {len(mojibake)} potential mojibake')