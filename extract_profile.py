with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract loadProfileData
start = content.find('async function loadProfileData()')
depth = 0
i = content.find('{', start)
end = i
for j in range(i, len(content)):
    if content[j] == '{':
        depth += 1
    elif content[j] == '}':
        depth -= 1
        if depth == 0:
            end = j + 1
            break
print("=== loadProfileData ===")
print(content[start:end])
print()

# Also extract fillProfileForm
start = content.find('function fillProfileForm(admin)')
if start > 0:
    depth = 0
    i = content.find('{', start)
    end = i
    for j in range(i, len(content)):
        if content[j] == '{':
            depth += 1
        elif content[j] == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    print("=== fillProfileForm ===")
    print(content[start:end])
    print()

# Extract decodeJwt to see what fields the JWT has
start = content.find('function decodeJwt(token)')
if start > 0:
    depth = 0
    i = content.find('{', start)
    end = i
    for j in range(i, len(content)):
        if content[j] == '{':
            depth += 1
        elif content[j] == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    print("=== decodeJwt ===")
    print(content[start:end])