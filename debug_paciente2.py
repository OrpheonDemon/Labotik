with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find loadSectionData
start = content.find('async function loadSectionData(sectionId)')
if start > 0:
    # Count braces to find end
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
    print("=== loadSectionData ===")
    print(content[start:end])
    print()

# Find loadDashboardStats
start = content.find('async function loadDashboardStats')
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
    print("=== loadDashboardStats (first 500 chars) ===")
    print(content[start:end][:500])
    print("...")