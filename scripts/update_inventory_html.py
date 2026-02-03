#!/usr/bin/env python3
"""
Updates the inventory HTML dashboard with embedded data.
Call this after updating inventory_dashboard.json
"""

import json
import re
from pathlib import Path

DATA_FILE = Path("/Users/ellisbot/.openclaw/workspace/data/inventory_dashboard.json")
HTML_FILE = Path("/Users/ellisbot/.openclaw/workspace/trifecta/inventory.html")

def update_html():
    if not DATA_FILE.exists():
        print("No data file found")
        return
    
    data = json.loads(DATA_FILE.read_text())
    html = HTML_FILE.read_text()
    
    # Replace the embedded data
    pattern = r'const DASHBOARD_DATA = \{.*?\};'
    replacement = f'const DASHBOARD_DATA = {json.dumps(data)};'
    
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    HTML_FILE.write_text(new_html)
    print("✓ Inventory HTML updated with latest data")

if __name__ == "__main__":
    update_html()
