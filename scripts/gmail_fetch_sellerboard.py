#!/usr/bin/env python3
"""
Fetch Sellerboard CSV exports from Gmail via IMAP.
Downloads attachments from emails matching Sellerboard export pattern.
"""

import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime
import json

# Configuration
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "ellisbotx@gmail.com"
DOWNLOAD_DIR = "/Users/ellisbot/.openclaw/workspace/data/sellerboard"

def get_gmail_credentials():
    """Fetch Gmail credentials from local credential file."""
    try:
        creds_path = "/Users/ellisbot/.openclaw/workspace/.credentials.json"
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        return creds['gmail']['username'], creds['gmail']['password']
    except Exception as e:
        print(f"❌ Failed to get credentials: {e}")
        return None, None

def connect_to_gmail(password):
    """Connect to Gmail via IMAP."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ACCOUNT, password)
        print(f"✅ Connected to Gmail as {EMAIL_ACCOUNT}")
        return mail
    except Exception as e:
        print(f"❌ Failed to connect to Gmail: {e}")
        return None

def detect_brand_from_filename(filename):
    """
    Detect which brand this export is for based on filename patterns.
    
    Returns: 'blackowned', 'cardplug', 'kinfolk', or 'unknown'
    """
    filename_lower = filename.lower()
    
    # Brand identifiers in Sellerboard email filenames
    if "lewis_renee" in filename_lower or "blackowned" in filename_lower:
        return "blackowned"
    elif "card_plug" in filename_lower or "cardplug" in filename_lower:
        return "cardplug"
    elif "kinfolk" in filename_lower:
        return "kinfolk"
    else:
        return "unknown"

def standardize_filename(original_filename, brand):
    """
    Convert Sellerboard export filename to our standard naming convention.
    
    Args:
        original_filename: Original filename from email
        brand: Brand identifier (blackowned, cardplug, kinfolk)
    
    Returns: Standardized filename or None if not a Dashboard export
    """
    # Only process "Dashboard by product" exports
    if "dashboard" not in original_filename.lower() and "Dashboard_by_product" not in original_filename:
        print(f"  ⚠️  Skipping non-Dashboard export: {original_filename}")
        return None
    
    # Standard naming: {brand}_dashboard_by_product_90d.csv
    # Note: Sellerboard sends 30-day reports, but we keep the _90d naming for consistency
    return f"{brand}_dashboard_by_product_90d.csv"

def download_sellerboard_attachments(mail, days_back=7):
    """
    Download Sellerboard CSV attachments from recent emails.
    
    Args:
        mail: IMAP connection object
        days_back: How many days back to search for emails
    """
    try:
        # Select inbox
        mail.select("INBOX")
        
        # Search for Sellerboard emails (adjust sender as needed)
        # You may need to adjust the search criteria based on actual email sender
        status, messages = mail.search(None, 'FROM "sellerboard.com"')
        
        if status != "OK":
            print("❌ Failed to search emails")
            return
        
        email_ids = messages[0].split()
        print(f"📧 Found {len(email_ids)} emails from Sellerboard")
        
        downloaded = 0
        brands_found = set()
        
        # Process most recent emails first
        for email_id in reversed(email_ids[-20:]):  # Last 20 emails
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                continue
            
            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Get subject
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            print(f"\n📨 Processing: {subject}")
            
            # Check if email has attachments
            if msg.get_content_maintype() == "multipart":
                for part in msg.walk():
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Look for CSV attachments
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        
                        if filename and filename.endswith(".csv"):
                            # Decode filename if needed
                            if isinstance(filename, bytes):
                                filename = filename.decode()
                            
                            print(f"  📎 Found attachment: {filename}")
                            
                            # Detect brand
                            brand = detect_brand_from_filename(filename)
                            print(f"  🏷️  Detected brand: {brand}")
                            
                            # Skip if we already have this brand
                            if brand in brands_found:
                                print(f"  ⏭️  Already have {brand}, skipping")
                                continue
                            
                            # Standardize filename
                            standard_filename = standardize_filename(filename, brand)
                            if not standard_filename:
                                continue
                            
                            # Download attachment
                            filepath = os.path.join(DOWNLOAD_DIR, standard_filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            
                            file_size = os.path.getsize(filepath)
                            print(f"  ✅ Downloaded: {standard_filename} ({file_size:,} bytes)")
                            downloaded += 1
                            brands_found.add(brand)
        
        print(f"\n✅ Downloaded {downloaded} CSV file(s) for brands: {', '.join(sorted(brands_found))}")
        
        # Check if we got all 3 brands
        missing_brands = {'blackowned', 'cardplug', 'kinfolk'} - brands_found
        if missing_brands:
            print(f"⚠️  Missing brands: {', '.join(sorted(missing_brands))}")
        
    except Exception as e:
        print(f"❌ Error downloading attachments: {e}")
        raise

def main():
    """Main execution."""
    print("🔐 Loading Gmail credentials...")
    username, password = get_gmail_credentials()
    
    if not username or not password:
        print("❌ Could not retrieve Gmail credentials")
        return 1
    
    print("📧 Connecting to Gmail...")
    mail = connect_to_gmail(password)
    
    if not mail:
        print("❌ Could not connect to Gmail")
        return 1
    
    print("📥 Downloading Sellerboard attachments...")
    download_sellerboard_attachments(mail)
    
    # Cleanup
    mail.close()
    mail.logout()
    
    print("\n✅ Email fetch complete!")
    return 0

if __name__ == "__main__":
    exit(main())
