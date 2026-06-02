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
    
    scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
    for i, script in enumerate(scripts):
        if 'API_URL' in script:
            paren_open = script.count('(')
            paren_close = script.count(')')
            bracket_open = script.count('[')
            bracket_close = script.count(']')
            
            issues = []
            if paren_open != paren_close:
                issues.append(f'Parentheses mismatch: ( = {paren_open}, ) = {paren_close}')
            if bracket_open != bracket_close:
                issues.append(f'Bracket mismatch: [ = {bracket_open}, ] = {bracket_close}')
            
            # Count backticks
            bt = script.count(chr(96))
            if bt % 2 != 0:
                issues.append(f'Odd number of backticks: {bt}')
            
            # Count semicolons after function defs (not critical but useful)
            # Check for unclosed strings by looking for odd quotes
            dq = script.count('"') - script.count('\\"')
            sq = script.count("'") - script.count("\\'")
            
            if issues:
                print(f'{f}: ISSUES FOUND')
                for issue in issues:
                    print(f'  - {issue}')
            else:
                print(f'{f}: OK')
            
            # Find any Django template tags inside script that might break JS
            django_tags = re.findall(r'\{%.*?%\}', script)
            if django_tags:
                print(f'  Django tags in JS: {django_tags[:5]}')
            
            # Check for common broken patterns
            # Look for fetch calls that might have issues
            fetch_calls = re.findall(r'fetch\(([^)]{0,200})\)', script)
            print(f'  Found {len(fetch_calls)} fetch calls')
            print()