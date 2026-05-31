const fs = require('fs');
const file = 'c:/Users/Rothe/Rotherick/Laboratorio/frontend/templates/dashboard/admin_dashboard.html';
let content = fs.readFileSync(file, 'utf8');
const lines = content.split('\n');

// Replace everything between line 3633 (analyzePatientGeneral start) and the end of the script
for (let i = 3633; i < lines.length; i++) {
    if (lines[i]) {
        lines[i] = lines[i].replace(/ia-modal-content/g, 'ia-analysis-result');
        lines[i] = lines[i].replace(/color:\s*#fff/g, 'color: #333');
        lines[i] = lines[i].replace(/rgba\(255,255,255,/g, 'rgba(0,0,0,');
    }
}

fs.writeFileSync(file, lines.join('\n'));
console.log('Fixed IDs and colors successfully.');
