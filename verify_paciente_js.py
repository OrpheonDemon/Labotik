with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract main script block
import re
scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
main_script = None
for s in scripts:
    if 'API_URL' in s:
        main_script = s
        break

if not main_script:
    print("ERROR: No main script found!")
    exit()

# Check for functions called in HTML onclick that might not be defined
onclick_funcs = set(re.findall(r'onclick="(\w+)\(', main_script))
onclick_funcs_html = set(re.findall(r"onclick='(\w+)\(", content))
onclick_funcs.update(onclick_funcs_html)

# Find all defined functions
defined_funcs = set(re.findall(r'(?:async )?function (\w+)', main_script))

print("=== Functions called in onclick ===")
for f in sorted(onclick_funcs):
    status = "DEFINED" if f in defined_funcs else "MISSING!"
    print(f"  {f}: {status}")

print(f"\n=== Total defined functions: {len(defined_funcs)} ===")

# Check if key functions exist
key_funcs = ['loadProfileData', 'navigateMenu', 'showOnlyDashboardSection', 
             'loadSectionHtml', 'loadSectionData', 'loadDashboardStats',
             'checkOllamaStatus', 'loadPatientsForAnalysis', 'openIAnalysisPopup',
             'sendSmartChat', 'fillProfileForm', 'handleLogout', 'updateHeaderDateTime',
             'decodeJwt', 'getToken', 'getAuthHeaders']
print("\n=== Key functions check ===")
for f in key_funcs:
    status = "OK" if f in defined_funcs else "MISSING!"
    print(f"  {f}: {status}")

# Check if section IDs match between HTML and JS
html_sections = set(re.findall(r'<section id="([^"]+)"', content))
print(f"\n=== HTML sections: {html_sections} ===")

# Check navigateMenu calls
nav_calls = set(re.findall(r"navigateMenu\(event, '([^']+)'", content))
print(f"=== Sidebar nav targets: {nav_calls} ===")

missing_sections = nav_calls - html_sections
if missing_sections:
    print(f"WARNING: Nav targets without sections: {missing_sections}")
else:
    print("All nav targets have matching sections")