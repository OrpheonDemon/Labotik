import re

with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The issue: loadProfileData tries to fetch the patient by ID, but the endpoint
# routes may cause 307 redirects. Let's change to use /search endpoint instead
# which is more reliable.

# Find and fix loadProfileData - change the fetch to use /pacientes/search?id_paciente=
old_fetch = '''const response = await fetch(`${API_URL}/pacientes/${encodeURIComponent(patientId)}`, {
                    headers: getAuthHeaders()
                });
                if (!response.ok) throw new Error('Error al obtener perfil');
                const patientData = await response.json();'''

new_fetch = '''let response = await fetch(`${API_URL}/pacientes/${encodeURIComponent(patientId)}/`, {
                    headers: getAuthHeaders()
                });
                if (!response.ok) {
                    response = await fetch(`${API_URL}/pacientes/search?id_paciente=${encodeURIComponent(patientId)}`, {
                        headers: getAuthHeaders()
                    });
                }
                if (!response.ok) throw new Error('Error al obtener perfil');
                let patientData = await response.json();
                if (Array.isArray(patientData)) {
                    patientData = patientData[0];
                }'''

if old_fetch in content:
    content = content.replace(old_fetch, new_fetch)
    print("✅ loadProfileData fetch fixed - added trailing slash and fallback to /search")
else:
    print("❌ Could not find old fetch pattern")
    # Try to find it with different indentation
    if 'encodeURIComponent(patientId)' in content:
        # Extract the exact text
        idx = content.find('encodeURIComponent(patientId)')
        # Find start of line
        line_start = content.rfind('\n', 0, idx) + 1
        line_end = content.find('\n', idx)
        print(f"Found at line: {content[line_start:line_end]}")
    else:
        print("encodeURIComponent(patientId) not found in file")
        # Check if patientId is used
        if 'patientId' in content:
            idx = content.find('patientId')
            print(f"patientId found at position {idx}")
            print(f"Context: {content[idx-50:idx+100]}")

# Also add a fallback in fillProfileForm if admin is an array
old_fill = '''function fillProfileForm(admin) {'''
new_fill = '''function fillProfileForm(admin) {
            if (Array.isArray(admin)) {
                admin = admin[0];
            }'''
if old_fill in content:
    content = content.replace(old_fill, new_fill, 1)
    print("✅ fillProfileForm fixed - handles array response")
else:
    print("✅ fillProfileForm already has array handling or not needed")

with open('frontend/templates/dashboard/paciente_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ File saved")