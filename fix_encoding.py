import re

filepath = 'frontend/templates/dashboard/laboratorista_dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix mojibake: the file has UTF-8 bytes interpreted as Latin-1
# We need to re-encode as Latin-1 then decode as UTF-8
try:
    fixed = content.encode('latin-1').decode('utf-8')
    print("Fixed using latin-1 -> utf-8 decode")
except Exception as e:
    print(f"latin-1 approach failed: {e}")
    # Fallback: fix specific patterns
    replacements = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã\xad': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã±': 'ñ', 'Ã\x81': 'Á', 'Â¿': '¿', 'Ã': 'ó', '\xad': 'í',
        'Ã\u0081': 'Á', 'Ã\u00b1': 'ñ',
    }
    fixed = content
    for bad, good in replacements.items():
        fixed = fixed.replace(bad, good)

# Verify fix
remaining = re.findall(r'[\x80-\xff]{2,}', fixed)
if remaining:
    print(f"Still {len(remaining)} mojibake instances remaining")
    for m in set(remaining):
        print(f"  {m!r}")
else:
    print("All mojibake fixed!")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed)

print(f"File saved: {filepath}")