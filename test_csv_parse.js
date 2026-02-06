const fs = require('fs');

function parseCSV(text){
    const lines = (text || '').split(/\r?\n/).filter(l => l.trim().length);
    if (!lines.length) return [];
    const headers = lines[0].split(',').map(h => h.trim());
    console.log('Headers:', headers);
    
    return lines.slice(1).map(line => {
        const cols = [];
        let cur = '', inQ = false;
        for (let i=0;i<line.length;i++){
            const ch = line[i];
            if (ch === '"') { inQ = !inQ; continue; }
            if (ch === ',' && !inQ) { cols.push(cur); cur=''; continue; }
            cur += ch;
        }
        cols.push(cur);
        const row = {};
        headers.forEach((h, idx) => row[h] = (cols[idx] || '').trim());
        return row;
    });
}

const csvText = fs.readFileSync('/Users/ellisbot/.openclaw/workspace/data/suppression_tracker.csv', 'utf8');
const rows = parseCSV(csvText);

console.log('\nTotal rows:', rows.length);
console.log('\nFirst 3 rows:');
rows.slice(0, 3).forEach(r => console.log(r));

const suppressed = rows.filter(r => {
    const statusField = r.Status || r.status || '';
    const statusLower = String(statusField).toLowerCase().trim();
    const isSuppressed = statusLower === 'suppressed';
    return isSuppressed;
});

console.log('\nSuppressed count:', suppressed.length);
console.log('\nSuppressed items:');
suppressed.forEach(r => console.log(r));
