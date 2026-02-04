#!/usr/bin/env python3
"""
Fetch ALL Sellerboard report types from Gmail and organize by type.
Downloads and archives all automated reports.
"""

import imaplib
import email
from email.header import decode_header
import os
import json
from datetime import datetime
from pathlib import Path

# Configuration
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "ellisbotx@gmail.com"
BASE_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")

# Report type directories
REPORT_DIRS = {
    "dashboard": BASE_DIR / "dashboard",
    "orders": BASE_DIR / "orders",
    "stock": BASE_DIR / "stock",
    "cogs": BASE_DIR / "cogs",
    "advertising": BASE_DIR / "advertising",
    "fba_fees": BASE_DIR / "fba_fees",
    "other": BASE_DIR / "other",
}

# Create all directories
for dir_path in REPORT_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)

def get_gmail_credentials():
    """Fetch Gmail credentials from local credential file."""
    creds_path = "/Users/ellisbot/.openclaw/workspace/.credentials.json"
    with open(creds_path, 'r') as f:
        creds = json.load(f)
    return creds['gmail']['username'], creds['gmail']['password']

def connect_to_gmail(password):
    """Connect to Gmail via IMAP."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, password)
    print(f"✅ Connected to Gmail as {EMAIL_ACCOUNT}")
    return mail

def detect_brand(filename):
    """Detect brand from filename."""
    filename_lower = filename.lower()
    if "lewis_renee" in filename_lower or "blackowned" in filename_lower:
        return "blackowned"
    elif "card_plug" in filename_lower or "cardplug" in filename_lower:
        return "cardplug"
    elif "kinfolk" in filename_lower:
        return "kinfolk"
    return "unknown"

def detect_report_type(filename):
    """Detect report type from filename."""
    filename_lower = filename.lower()
    
    if "dashboardtotals" in filename_lower or "dashboard_by_product" in filename_lower:
        return "dashboard"
    elif "orderlist" in filename_lower or "orders" in filename_lower:
        return "orders"
    elif "stock" in filename_lower:
        return "stock"
    elif "cogs" in filename_lower or "cost_of_goods" in filename_lower:
        return "cogs"
    elif "advertising" in filename_lower or "ads" in filename_lower:
        return "advertising"
    elif "fbafeeschanges" in filename_lower or "fba_fee" in filename_lower:
        return "fba_fees"
    else:
        return "other"

def standardize_filename(original_filename, brand, report_type):
    """Create standardized filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".csv" if original_filename.endswith(".csv") else ".xlsx"
    return f"{brand}_{report_type}_{timestamp}{ext}"

def download_all_sellerboard_reports(mail):
    """Download all Sellerboard reports and organize by type."""
    mail.select("INBOX")
    
    # Search for all Sellerboard emails
    status, messages = mail.search(None, 'FROM "sellerboard.com"')
    
    if status != "OK":
        print("❌ Failed to search emails")
        return {}
    
    email_ids = messages[0].split()
    print(f"📧 Found {len(email_ids)} Sellerboard emails")
    
    downloaded = {}
    emails_to_archive = []
    
    # Process recent emails (last 50)
    for email_id in reversed(email_ids[-50:]):
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        
        if status != "OK":
            continue
        
        msg = email.message_from_bytes(msg_data[0][1])
        
        # Get subject
        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        
        print(f"\n📨 {subject}")
        
        # Check for attachments
        if msg.get_content_maintype() == "multipart":
            for part in msg.walk():
                if "attachment" in str(part.get("Content-Disposition")):
                    filename = part.get_filename()
                    
                    if filename and (filename.endswith(".csv") or filename.endswith(".xlsx")):
                        if isinstance(filename, bytes):
                            filename = filename.decode()
                        
                        print(f"  📎 {filename}")
                        
                        # Detect brand and report type
                        brand = detect_brand(filename)
                        report_type = detect_report_type(filename)
                        
                        print(f"  🏷️  Brand: {brand}, Type: {report_type}")
                        
                        # Get target directory
                        target_dir = REPORT_DIRS.get(report_type, REPORT_DIRS["other"])
                        
                        # Create standardized filename
                        new_filename = standardize_filename(filename, brand, report_type)
                        filepath = target_dir / new_filename
                        
                        # Download
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        
                        file_size = os.path.getsize(filepath)
                        print(f"  ✅ Saved: {filepath.name} ({file_size:,} bytes)")
                        
                        # Track downloads
                        key = f"{brand}_{report_type}"
                        if key not in downloaded:
                            downloaded[key] = []
                        downloaded[key].append(str(filepath))
                        
                        # Mark email for archiving
                        emails_to_archive.append(email_id)
    
    # Archive processed emails
    if emails_to_archive:
        print(f"\n📦 Archiving {len(set(emails_to_archive))} emails...")
        for email_id in set(emails_to_archive):
            mail.store(email_id, '+X-GM-LABELS', '\\Processed')
            mail.store(email_id, '+FLAGS', '\\Seen')
    
    return downloaded

def main():
    print("🔐 Loading credentials...")
    username, password = get_gmail_credentials()
    
    print("📧 Connecting to Gmail...")
    mail = connect_to_gmail(password)
    
    print("📥 Downloading all Sellerboard reports...")
    downloaded = download_all_sellerboard_reports(mail)
    
    mail.close()
    mail.logout()
    
    # Summary
    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    for key, files in sorted(downloaded.items()):
        print(f"  {key}: {len(files)} file(s)")
    
    print(f"\n✅ Complete! Downloaded {sum(len(f) for f in downloaded.values())} files total")
    return 0

if __name__ == "__main__":
    exit(main())
