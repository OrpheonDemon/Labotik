with open('frontend/templates/dashboard/paciente_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find loadProfileData
start = content.find('async function loadProfileData()')
if start > 0:
    # Find the end (next function at same indent level)
    end = content.find('\n        async function ', start + 10)
    if end < 0:
        end = content.find('\n        function ', start + 10)
    print("=== loadProfileData ===")
    print(content[start:end][:1000])
    print("...")

# Find navigateMenu
start = content.find('async function navigateMenu(event, sectionId, title)')
if start > 0:
    end = content.find('\n        async function ', start + 10)
    if end < 0:
        end = content.find('\n        function ', start + 10)
    print("\n=== navigateMenu ===")
    print(content[start:end][:1500])
    print("...")

# Find loadSectionHtml
start = content.find('async function loadSectionHtml(sectionId)')
if start > 0:
    end = content.find('\n        async function ', start + 10)
    if end < 0:
        end = content.find('\n        function ', start + 10)
    print("\n=== loadSectionHtml ===")
    print(content[start:end][:1500])
    print("...")

# Check if navigateMenu has ia-assistant handling
if "sectionId === 'ia-assistant'" in content:
    print("\n=== IA navigation: PRESENT ===")
else:
    print("\n=== IA navigation: MISSING ===")

# Check section IDs in HTML
import re
sections = re.findall(r'<section id="([^"]+)"', content)
print(f"\n=== HTML sections: {sections} ===")

# Check sidebar menu items
menu_items = re.findall(r"navigateMenu\(event, '([^']+)'", content)
print(f"=== Sidebar menu items: {menu_items} ===")