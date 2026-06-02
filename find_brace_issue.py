"""
Script para encontrar exactamente dónde están las llaves desbalanceadas
en laboratorista_dashboard.html
"""

filepath = 'frontend/templates/dashboard/laboratorista_dashboard.html'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar el inicio y fin del Script #3 (script principal)
script_starts = []
script_ends = []
for i, line in enumerate(lines):
    if '<script>' in line and 'src=' not in line:
        script_starts.append(i)
    if '</script>' in line:
        script_ends.append(i)

print(f"Scripts encontrados: {len(script_starts)}")
for i, (start, end) in enumerate(zip(script_starts, script_ends)):
    print(f"  Script #{i+1}: líneas {start+1} a {end+1}")

# Analizar el Script #3 (índice 2)
if len(script_starts) >= 3:
    start = script_starts[2]
    end = script_ends[2]
    
    print(f"\nAnalizando Script #3 (líneas {start+1} a {end+1})...")
    
    brace_count = 0
    paren_count = 0
    bracket_count = 0
    
    for i in range(start, end + 1):
        line = lines[i]
        
        # Contar llaves
        for char in line:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
        
        # Reportar cuando el conteo de llaves se desbalancea
        if brace_count < 0:
            print(f"  ⚠️ Línea {i+1}: Llaves desbalanceadas (count={brace_count})")
            print(f"      Contenido: {line.strip()[:80]}")
            break
    
    print(f"\n  Balance final de llaves: {brace_count}")
    print(f"  Balance final de paréntesis: {paren_count}")
    print(f"  Balance final de corchetes: {bracket_count}")
    
    # Si el balance es -1, hay una llave de cierre extra
    # Buscar la última línea con una llave de cierre
    if brace_count == -1:
        print("\n  Buscando la llave de cierre extra...")
        # Empezar desde el final y buscar la primera llave de cierre
        for i in range(end, start - 1, -1):
            line = lines[i]
            if '}' in line and line.strip().startswith('}'):
                print(f"  Posible llave extra en línea {i+1}: {line.strip()[:60]}")
                # Verificar si esta llave cierra algo necesario
                # Contar llaves desde el inicio hasta esta línea
                test_count = 0
                for j in range(start, i):
                    test_count += lines[j].count('{') - lines[j].count('}')
                print(f"    Balance hasta línea {i}: {test_count}")
                if test_count == 0:
                    print(f"    ✅ Esta es la llave extra! Línea {i+1}")
                    break