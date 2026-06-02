"""
Script para eliminar completamente el Asistente IA del dashboard de médicos.
"""

import re

filepath = 'frontend/templates/dashboard/medico_dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Eliminar botón del menú lateral (el <li> completo)
menu_button_pattern = r'<li class="menu-item">\s*<a href="#" onclick="navigateMenu\(event, \'ia-assistant\', \'Asistente IA\'\)">.*?</li>'
content = re.sub(menu_button_pattern, '', content, flags=re.DOTALL)
print("✅ Botón del menú lateral eliminado")

# 2. Eliminar sección HTML completa del asistente IA (desde <!-- ASISTENTE IA SECTION --> hasta </section>)
section_pattern = r'<!-- ASISTENTE IA SECTION -->.*?</section>'
content = re.sub(section_pattern, '', content, flags=re.DOTALL)
print("✅ Sección HTML del asistente IA eliminada")

# 3. Eliminar handler en loadSectionData para 'ia-assistant'
handler_pattern = r"if \(sectionId === 'ia-assistant'\) \{[^}]*checkOllamaStatus\(\);[^}]*await loadPatientsForAnalysis\(\);[^}]*\}"
content = re.sub(handler_pattern, '', content, flags=re.DOTALL)
print("✅ Handler en loadSectionData eliminado")

# 4. Eliminar todas las funciones JavaScript del asistente IA
# Desde "// ========== FUNCIONES PARA ASISTENTE IA ==========" hasta "function closeAnalysisModalMedico()"
js_functions_pattern = r'// ========== FUNCIONES PARA ASISTENTE IA ==========.*?function closeAnalysisModalMedico\(\) \{[^}]*\}'
content = re.sub(js_functions_pattern, '', content, flags=re.DOTALL)
print("✅ Funciones JavaScript del asistente IA eliminadas")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Archivo actualizado: {filepath}")
print("\nAsistente IA eliminado completamente del dashboard de médicos.")