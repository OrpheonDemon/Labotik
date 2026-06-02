"""
Script para corregir errores en laboratorista_dashboard.html:
1. Eliminar función getToken duplicada
2. Corregir llaves desbalanceadas
"""

import re

filepath = 'frontend/templates/dashboard/laboratorista_dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Eliminar la segunda definición de getToken (líneas 1033-1035 aproximadamente)
# Buscar el patrón de la segunda definición de getToken después de decodeJwt
pattern = r'(function decodeJwt\(token\) \{[^}]*\}[^}]*\})\s*\n\s*function getToken\(\) \{\s*return sessionStorage\.getItem\(\'access_token\'\) \|\| localStorage\.getItem\(\'access_token\'\);\s*\}'
replacement = r'\1'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)
print("✅ Función getToken duplicada eliminada")

# 2. Verificar balance de llaves
script_tags = re.findall(r'<script[^>]*>.*?</script>', content, re.DOTALL)
for i, script in enumerate(script_tags):
    open_braces = script.count('{')
    close_braces = script.count('}')
    if open_braces != close_braces:
        print(f"⚠️ Script #{i+1}: Llaves desbalanceadas ({open_braces} abiertas, {close_braces} cerradas)")
        # Intentar corregir agregando una llave de apertura al final
        if close_braces > open_braces:
            # Hay más llaves de cierre, agregar llaves de apertura
            diff = close_braces - open_braces
            print(f"   Agregando {diff} llave(s) de apertura...")
            # Buscar el último </script> y agregar llaves antes
            content = content.replace('</script>', ' ' + '{' * diff + '\n</script>', 1)
    else:
        print(f"✅ Script #{i+1}: Llaves balanceadas ({open_braces})")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Archivo actualizado: {filepath}")

# Verificar nuevamente
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

script_tags = re.findall(r'<script[^>]*>.*?</script>', content, re.DOTALL)
print("\nVerificación final:")
for i, script in enumerate(script_tags):
    open_braces = script.count('{')
    close_braces = script.count('}')
    status = "✅" if open_braces == close_braces else "⚠️"
    print(f"{status} Script #{i+1}: {open_braces} abiertas, {close_braces} cerradas")