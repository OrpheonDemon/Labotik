import re

# Read both files
with open('frontend/templates/dashboard/medico_dashboard.html', 'r', encoding='utf-8') as f:
    medico = f.read()

with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    paciente = f.read()

# 1. Add IA sidebar button before the logout button
ia_sidebar_button = '''
                    <li class="menu-item">
                        <a href="#" onclick="navigateMenu(event, 'ia-assistant', 'Asistente IA')">
                            <svg class="menu-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12a9 9 0 11-18 0 9 9 0 0118 0zm0 0h-1m-12 0H3m14.364 5.636l-.707-.707M12 21v-1m-6.364-1.636l.707-.707" />
                            </svg>
                            Asistente IA 🧠
                        </a>
                    </li>

'''

# Insert before the logout menu item
logout_marker = '<li class="menu-item" style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">'
if logout_marker in paciente and ia_sidebar_button.strip() not in paciente:
    paciente = paciente.replace(logout_marker, ia_sidebar_button + '                    ' + logout_marker, 1)
    print("✅ IA sidebar button added")

# 2. Extract IA HTML section from medico (between ASISTENTE IA SECTION and ENTITY EDIT MODAL)
ia_start = medico.find('<!-- ASISTENTE IA SECTION -->')
ia_end = medico.find('<!-- ENTITY EDIT MODAL')
if ia_start > 0 and ia_end > 0:
    ia_html_section = medico[ia_start:ia_end].strip()
    
    # Adapt for paciente - replace openIAnalysisPopup with openIAPopup (simpler version)
    # Insert before ENTITY EDIT MODAL in paciente
    modal_marker = '<!-- ENTITY EDIT MODAL'
    if modal_marker in paciente and 'ASISTENTE IA SECTION' not in paciente:
        paciente = paciente.replace(modal_marker, ia_html_section + '\n\n            ' + modal_marker, 1)
        print("✅ IA HTML section added")

# 3. Extract IA JavaScript functions from medico
# Find the IA functions block
ia_js_start = medico.find('// ========== FUNCIONES PARA ASISTENTE IA ==========')
ia_js_end = medico.find('        }\n    </script>', ia_js_start) if ia_js_start > 0 else -1

if ia_js_start > 0 and ia_js_end > 0:
    ia_js = medico[ia_js_start:ia_js_end]
    
    # Add IA navigation handling in navigateMenu function
    # Find the navigateMenu function and add ia-assistant case
    if "sectionId === 'ia-assistant'" not in paciente:
        # Add to the section loading logic
        navigate_check = "if (sectionId === 'dashboard') {"
        ia_nav_code = """
            if (sectionId === 'dashboard') {
                await loadDashboardStats();
            }
            if (sectionId === 'ia-assistant') {
                checkOllamaStatus();
                await loadPatientsForAnalysis();
            }"""
        
        # Check if navigateMenu exists in paciente
        if navigate_check in paciente:
            # Find the loadDashboardStats call and add IA after it
            old_pattern = "if (sectionId === 'dashboard') {\n                await loadDashboardStats();\n            }"
            if old_pattern in paciente:
                paciente = paciente.replace(old_pattern, ia_nav_code.strip(), 1)
                print("✅ IA navigation handling added")
    
    # Insert IA JS functions before the closing </script> tag
    # Find the last </script> that's not the chatbot one
    script_close_pattern = "        }\n    </script>"
    # Add IA functions before the handleLogout closing
    if '// ========== FUNCIONES PARA ASISTENTE IA' not in paciente:
        # Find the handleLogout function end and add IA functions after it
        logout_end = paciente.rfind('        }\n    </script>')
        if logout_end > 0:
            paciente = paciente[:logout_end] + '\n\n        // ========== FUNCIONES PARA ASISTENTE IA ==========\n\n' + ia_js + '\n\n        ' + paciente[logout_end:]
            print("✅ IA JavaScript functions added")

# Write the result
with open('frontend/templates/dashboard/paciente_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(paciente)

print("\n✅ paciente_dashboard.html updated with IA section")

# Verify
with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()
print(f"Total lines: {content.count(chr(10))}")
print(f"IA section present: {'ASISTENTE IA SECTION' in content}")
print(f"IA sidebar button: {'ia-assistant' in content}")
print(f"IA JS functions: {'FUNCIONES PARA ASISTENTE IA' in content}")