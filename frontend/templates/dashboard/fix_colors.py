import re

file_path = 'c:/Users/Rothe/Rotherick/Laboratorio/frontend/templates/dashboard/admin_dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(3633, len(lines)):
    if 'ia-modal-content' in lines[i]:
        lines[i] = lines[i].replace('ia-modal-content', 'ia-analysis-result')
    if 'color: #fff' in lines[i]:
        lines[i] = re.sub(r'color:\s*#fff', 'color: #333', lines[i])
    if 'rgba(255,255,255,' in lines[i]:
        lines[i] = lines[i].replace('rgba(255,255,255,', 'rgba(0,0,0,')

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed IDs and colors successfully.')
