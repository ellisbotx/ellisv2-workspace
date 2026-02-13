#!/usr/bin/env python3
"""
Order Tracker v2 (Etsy + Shopify → MCF)
Scans Gmail for Etsy sale notifications, Shopify order emails, and Amazon MCF tracking emails.
Maintains an order tracker JSON and posts updates to #orders channel.

Features:
- Priority shipping detection (🚨 flag)
- Full customer name + address on new orders
- Auto-archive: SHIPPED orders archived after 3 days
- Posts to #orders only when something changes
"""

import imaplib
import email
from email.header import decode_header
import os
import re
import json
import subprocess
from datetime import datetime, timedelta

# Configuration
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_ACCOUNT = "ellisbotx@gmail.com"
WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
TRACKER_FILE = f"{WORKSPACE}/data/etsy_orders/tracker.json"
LOG_FILE = f"{WORKSPACE}/data/etsy_orders/etsy_tracker.log"
LAST_REPORT_FILE = f"{WORKSPACE}/data/etsy_orders/last_report_hash.txt"
EMAIL_HOURS = []  # DISABLED — Marco uses Discord #orders now (Feb 9, 2026)
LAST_SNAPSHOT_FILE = f"{WORKSPACE}/data/etsy_orders/last_snapshot.json"
HEALTH_FILE = f"{WORKSPACE}/data/etsy_orders/health.json"

# Discord channel for #orders
DISCORD_ORDERS_CHANNEL = "1468703293583785994"

# Email notification
NOTIFY_EMAIL = "mlgrier@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Brand mapping by sender email
BRAND_MAP = {
    "cardpluggames@gmail.com": "Card Plug",
    "kinfolkgamesllc@gmail.com": "Kinfolk",
    "mlgrier@gmail.com": "Black Owned"
}

# Shopify brand mapping by subject prefix
SHOPIFY_BRAND_MAP = {
    "[Kinfolk Games]": "Kinfolk",
    "[Black Owned Games]": "Black Owned",
}

# Shipping methods that count as priority/expedited
PRIORITY_KEYWORDS = [
    "priority", "express", "expedited", "overnight", "2-day", "two-day",
    "next day", "rush", "upgrade"
]

def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.now().isoformat()}: {msg}\n")
    print(msg)

def get_gmail_credentials():
    try:
        creds_path = f"{WORKSPACE}/.credentials.json"
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        return creds['gmail']['username'], creds['gmail']['password']
    except Exception as e:
        log(f"❌ Failed to get credentials: {e}")
        return None, None

def connect_to_gmail(password):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ACCOUNT, password)
        return mail
    except Exception as e:
        log(f"❌ Failed to connect: {e}")
        return None

def load_tracker():
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"orders": [], "last_check_etsy": None, "last_check_amazon": None}

def save_tracker(tracker):
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)

def decode_mime_header(header):
    if header is None:
        return ""
    decoded_parts = decode_header(header)
    result = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(charset or 'utf-8', errors='replace')
        else:
            result += part
    return result

def get_email_body(msg):
    """Extract text body from email. Prefer HTML for address parsing, fall back to plain."""
    html_body = ""
    plain_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                text = payload.decode('utf-8', errors='replace')
                if content_type == "text/html":
                    html_body = text
                elif content_type == "text/plain":
                    plain_body = text
            except:
                pass
    else:
        try:
            text = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            ct = msg.get_content_type()
            if ct == "text/html":
                html_body = text
            else:
                plain_body = text
        except:
            pass
    # Return HTML if available (better for address parsing), else plain
    return html_body or plain_body

def detect_shipping_method(body):
    """Detect shipping method from email body. Returns (method_name, is_priority)."""
    # Look for shipping method lines in email
    shipping_patterns = [
        # "USPS Priority Mail", "UPS 2-Day", etc.
        re.compile(r'(?:USPS|UPS|FedEx|DHL)\s+(?:Priority|Express|Expedited|Overnight|2-Day|Next Day)[^\n<]{0,30}', re.IGNORECASE),
        # Generic "Shipping upgrade: ..."
        re.compile(r'(?:Shipping upgrade|Shipping method|Ship via)[:\s]+([^\n<]{3,50})', re.IGNORECASE),
        # Etsy shipping lines in HTML
        re.compile(r'>([^<]*(?:Priority|Express|Expedited|Overnight)[^<]*)<', re.IGNORECASE),
    ]
    
    for pattern in shipping_patterns:
        match = pattern.search(body)
        if match:
            method = match.group(0) if match.lastindex is None else match.group(1)
            method = re.sub(r'<[^>]+>', '', method).strip()
            method = re.sub(r'\s+', ' ', method).strip()
            if method:
                is_priority = any(kw in method.lower() for kw in PRIORITY_KEYWORDS)
                return method, is_priority
    
    return "Standard", False

def parse_etsy_sale_email(subject, body, forwarded_from=None):
    """Parse Etsy sale notification email for order details."""
    result = {
        "brand": None,
        "customer_name": None,
        "street_address": None,
        "street_address_2": None,
        "city": None,
        "state": None,
        "zip_code": None,
        "shipping_address": None,
        "product": None,
        "quantity": 1,
        "order_number": None,
        "order_total": None,
        "shipping_method": "Standard",
        "is_priority": False,
    }
    
    # Determine brand from forwarded address
    if forwarded_from:
        for email_addr, brand in BRAND_MAP.items():
            if email_addr.lower() in forwarded_from.lower():
                result["brand"] = brand
                break
    
    # Extract order number from subject: "Ship by Feb 9 - [$28.34, Order #3971214441]"
    subj_order = re.search(r'Order\s*#(\d+)', subject, re.IGNORECASE)
    if subj_order:
        result["order_number"] = subj_order.group(1)
    
    # Extract order total from subject: "[$28.34, Order #..."
    subj_total = re.search(r'\[\$(\d+\.\d{2})', subject)
    if subj_total:
        result["order_total"] = f"${subj_total.group(1)}"
    
    # Fallback order number from body
    if not result["order_number"]:
        order_match = re.search(r'order number is (\d+)', body, re.IGNORECASE)
        if order_match:
            result["order_number"] = order_match.group(1)
    
    # Fallback order total from body
    if not result["order_total"]:
        total_match = re.search(r'Order Total:\s+\$(\d+\.\d{2})', body, re.IGNORECASE)
        if total_match:
            result["order_total"] = f"${total_match.group(1)}"
    
    # Extract product name
    # Method 1: "Item:" line (plain text emails)
    item_match = re.search(r'Item:\s+(.+?)(?:\n|$)', body, re.IGNORECASE)
    if item_match:
        result["product"] = re.sub(r'<[^>]+>', '', item_match.group(1)).strip()[:100]
    if not result["product"]:
        # Method 2: HTML — find product name before "Shop:" using " . " as segment separator
        clean_body = re.sub(r'<[^>]+>', ' ', body)
        clean_body = re.sub(r'&nbsp;|&amp;', ' ', clean_body)
        clean_body = re.sub(r'\s+', ' ', clean_body)
        shop_split = clean_body.split("Shop:")
        if len(shop_split) > 1:
            before_shop = shop_split[0].strip()
            # Etsy uses " . " to separate sections — product is the last segment
            segments = re.split(r'\s+\.\s+', before_shop)
            product_candidate = segments[-1].strip()
            if len(product_candidate) > 10:
                result["product"] = product_candidate[:100]
    if not result["product"]:
        # Method 3: HTML table pattern
        item_html = re.search(r"alt='Item image'.*?<td[^>]*>\s*(.+?)\s*</td>", body, re.DOTALL)
        if item_html:
            result["product"] = re.sub(r'<[^>]+>', '', item_html.group(1)).strip()[:100]
    
    # Extract quantity
    qty_match = re.search(r'Quantity:\s+(\d+)', body, re.IGNORECASE)
    if qty_match:
        result["quantity"] = int(qty_match.group(1))
    
    # Extract shipping address from HTML spans (Etsy format)
    name_span = re.search(r"class='name'>([^<]+)<", body)
    first_line = re.search(r"class='first-line'>([^<]+)<", body)
    second_line = re.search(r"class='second-line'>([^<]+)<", body)
    city_span = re.search(r"class='city'>([^<]+)<", body)
    state_span = re.search(r"class='state'>([^<]+)<", body)
    zip_span = re.search(r"class='zip'>([^<]+)<", body)
    
    if name_span:
        result["customer_name"] = name_span.group(1).strip()
    if first_line:
        result["street_address"] = first_line.group(1).strip()
    if second_line:
        result["street_address_2"] = second_line.group(1).strip()
    if city_span:
        result["city"] = city_span.group(1).strip()
    if state_span:
        result["state"] = state_span.group(1).strip()
    if zip_span:
        result["zip_code"] = zip_span.group(1).strip()
    
    # Build full shipping address string
    addr_parts = []
    if result["customer_name"]:
        addr_parts.append(result["customer_name"])
    if result["street_address"]:
        addr_parts.append(result["street_address"])
    if result["street_address_2"]:
        addr_parts.append(result["street_address_2"])
    city_state_zip = ""
    if result["city"]:
        city_state_zip = result["city"]
    if result["state"]:
        city_state_zip += f", {result['state']}"
    if result["zip_code"]:
        city_state_zip += f" {result['zip_code']}"
    if city_state_zip:
        addr_parts.append(city_state_zip)
    if addr_parts:
        result["shipping_address"] = '\n'.join(addr_parts)
    
    # Fallback: plain text address patterns
    if not result["street_address"]:
        name_match = re.search(r'(?:ship(?:ping)?\s+to|deliver(?:y)?\s+to|buyer|customer)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', body, re.IGNORECASE)
        if name_match:
            result["customer_name"] = name_match.group(1).strip()
    
    # Detect shipping method
    method, is_priority = detect_shipping_method(body)
    result["shipping_method"] = method
    result["is_priority"] = is_priority
    
    return result

def parse_shopify_order_email(subject, body):
    """Parse Shopify order notification email for order details."""
    result = {
        "brand": None,
        "customer_name": None,
        "street_address": None,
        "street_address_2": None,
        "city": None,
        "state": None,
        "zip_code": None,
        "shipping_address": None,
        "products": [],
        "product": None,
        "quantity": 0,
        "order_number": None,
        "order_total": None,
        "shipping_method": "Standard",
        "is_priority": False,
    }
    
    # Determine brand from subject prefix
    for prefix, brand in SHOPIFY_BRAND_MAP.items():
        if prefix in subject:
            result["brand"] = brand
            break
    
    # Extract order number: "Order #1023"
    order_match = re.search(r'Order\s*#(\d+)', subject)
    if order_match:
        result["order_number"] = order_match.group(1)
    
    # Extract customer name from subject: "...placed by Tawanda Thomas"
    name_match = re.search(r'placed by\s+(.+?)$', subject)
    if name_match:
        result["customer_name"] = name_match.group(1).strip()
    
    # Clean HTML
    clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'&nbsp;|&amp;|&#39;|&lt;|&gt;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Extract products: between "Order summary" and "Subtotal"
    summary_section = re.search(r'Order summary\s*(.*?)\s*Subtotal', clean, re.DOTALL)
    if summary_section:
        section = summary_section.group(1)
        product_pattern = re.finditer(
            r'([A-Z][^$]{5,120}?)\s+\$(\d+\.?\d*)\s*[×x]\s*(\d+)\s+SKU:\s*(\S+)\s+\$(\d+\.?\d*)',
            section
        )
        for m in product_pattern:
            result["products"].append({
                "name": m.group(1).strip(),
                "price": f"${m.group(2)}",
                "quantity": int(m.group(3)),
                "sku": m.group(4),
                "line_total": f"${m.group(5)}"
            })
    
    # Build product summary
    if result["products"]:
        result["quantity"] = sum(p["quantity"] for p in result["products"])
        if len(result["products"]) == 1:
            result["product"] = result["products"][0]["name"][:100]
        else:
            names = [f"{p['name'][:50]} x{p['quantity']}" for p in result["products"]]
            result["product"] = " + ".join(names)[:100]
    
    # Extract total
    total_match = re.search(r'Total\s+\$(\d+\.?\d*)\s*USD', clean)
    if total_match:
        result["order_total"] = f"${total_match.group(1)}"
    
    # Shipping method
    delivery_match = re.search(r'Delivery method\s+(\w+(?:\s+\w+)?)', clean)
    if delivery_match:
        method = delivery_match.group(1).strip()
        result["shipping_method"] = method
        result["is_priority"] = any(kw in method.lower() for kw in PRIORITY_KEYWORDS)
    
    # Shipping address: extract between "Shipping address" and "United States"
    us_match = re.search(r'Shipping address\s+(.*?)\s+(?:United States|US|Canada)', clean)
    if us_match:
        full_addr = us_match.group(1).strip()
        # Remove trailing phone number
        full_addr = re.sub(r'\s+[\+]?\d{10,}$', '', full_addr)
        
        # Find "City, State ZIP" at the end (comma separates city from state)
        comma_pos = full_addr.rfind(',')
        if comma_pos > 0:
            before_comma = full_addr[:comma_pos].strip()
            after_comma = full_addr[comma_pos+1:].strip()
            
            state_zip = re.match(r'([A-Za-z\s]+?)\s+(\d{5}(?:-\d+)?)', after_comma)
            if state_zip:
                result["state"] = state_zip.group(1).strip()
                result["zip_code"] = state_zip.group(2)
                
                # Split name from street+city (name is before first digit)
                ns = re.match(r'^(.*?)\s+(\d+.*)$', before_comma)
                if ns:
                    result["customer_name"] = ns.group(1).strip()
                    street_city = ns.group(2).strip()
                    
                    # Split street from city using street suffixes as boundary
                    suffixes = r'(?:Road|Rd|Street|St|Drive|Dr|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Court|Ct|Circle|Cir|Way|Place|Pl|Terrace|Ter|Trail|Trl|Parkway|Pkwy|Highway|Hwy|Loop|Run|Path|Pike|Row|Square|Sq)'
                    split = re.search(r'(' + suffixes + r')\s+(.+)$', street_city, re.IGNORECASE)
                    
                    if split:
                        result["street_address"] = street_city[:split.end(1)].strip()
                        city_part = split.group(2).strip()
                        # Handle "Apt 4B CityName" — check if next word is apt/suite/unit
                        apt_match = re.match(r'((?:Apt|Suite|Ste|Unit|#)\s*\S+)\s+(.*)', city_part, re.IGNORECASE)
                        if apt_match:
                            result["street_address_2"] = apt_match.group(1).strip()
                            result["city"] = apt_match.group(2).strip().upper()
                        else:
                            result["city"] = city_part.upper()
                    else:
                        # No suffix found — last word(s) before comma is city
                        words = street_city.rsplit(None, 1)
                        if len(words) == 2:
                            result["street_address"] = words[0]
                            result["city"] = words[1].upper()
                        else:
                            result["street_address"] = street_city
                
                if result["city"]:
                    addr_parts = [result["customer_name"]]
                    if result["street_address"]:
                        addr_parts.append(result["street_address"])
                    if result.get("street_address_2"):
                        addr_parts.append(result["street_address_2"])
                    addr_parts.append(f"{result['city']}, {result['state']} {result['zip_code']}")
                    result["shipping_address"] = '\n'.join(addr_parts)
    
    return result


def parse_amazon_tracking_email(subject, body):
    """Parse Amazon MCF shipment notification for tracking info."""
    result = {
        "tracking_number": None,
        "carrier": None,
        "order_id": None,
        "city_state_zip": None,
        "item_name": None
    }
    
    # Strip HTML tags for parsing
    clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'&nbsp;|&amp;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # Extract MCF order ID from subject
    mcf_match = re.search(r'(CONSUMER-[\d-]+)', subject)
    if mcf_match:
        result["order_id"] = mcf_match.group(1)
    
    # Extract city/state/zip
    city_match = re.search(r'to one of your customers:\s+([A-Z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d+)?)', clean)
    if city_match:
        result["city_state_zip"] = city_match.group(1).strip()
    
    # Extract carrier, tracking, item from table
    table_match = re.search(
        r'Carrier\s+Code\s+Tracking\s+Number\s+Quantity\s+Item\s+(\S+)\s+(\S+)\s+(\d+)\s+(.+?)(?:Please note|$)',
        clean
    )
    if table_match:
        result["carrier"] = table_match.group(1)
        result["tracking_number"] = table_match.group(2)
        result["item_name"] = table_match.group(4).strip()
    
    return result

def check_etsy_sales(mail, tracker):
    """Check for new Etsy sale emails."""
    new_orders = []
    mail.select("INBOX")
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    
    search_queries = [
        f'(SINCE {since_date} SUBJECT "You made a sale on Etsy")',
        f'(SINCE {since_date} SUBJECT "Etsy transaction")',
        f'(SINCE {since_date} SUBJECT "New order" FROM "etsy")',
    ]
    
    existing_ids = {o.get("email_id") for o in tracker["orders"] if o.get("email_id")}
    
    for query in search_queries:
        try:
            status, messages = mail.search(None, query)
            if status != "OK":
                continue
            for msg_id in messages[0].split():
                msg_id_str = msg_id.decode()
                if msg_id_str in existing_ids:
                    continue
                
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = decode_mime_header(msg["Subject"])
                body = get_email_body(msg)
                date_str = msg["Date"]
                
                # Detect brand
                forwarded_from = ""
                for hdr in ["To", "Delivered-To", "X-Forwarded-To", "X-Forwarded-For",
                            "X-Original-To", "Envelope-To", "Cc"]:
                    hdr_val = decode_mime_header(msg.get(hdr, ""))
                    if hdr_val:
                        for brand_email in BRAND_MAP:
                            if brand_email.lower() in hdr_val.lower():
                                forwarded_from = brand_email
                                break
                    if forwarded_from:
                        break
                if not forwarded_from:
                    raw_headers = str(msg)
                    for brand_email in BRAND_MAP:
                        if brand_email.lower() in raw_headers.lower() or brand_email.lower() in body.lower():
                            forwarded_from = brand_email
                            break
                
                parsed = parse_etsy_sale_email(subject, body, forwarded_from)
                
                if parsed["product"] or "etsy" in subject.lower():
                    order = {
                        "email_id": msg_id_str,
                        "status": "NEW",
                        "brand": parsed["brand"] or "Unknown",
                        "customer_name": parsed["customer_name"] or "See email",
                        "street_address": parsed.get("street_address") or "",
                        "street_address_2": parsed.get("street_address_2") or "",
                        "city": parsed.get("city") or "",
                        "state": parsed.get("state") or "",
                        "zip_code": parsed.get("zip_code") or "",
                        "shipping_address": parsed["shipping_address"] or "See email",
                        "product": parsed["product"] or subject,
                        "quantity": parsed["quantity"],
                        "etsy_order_number": parsed["order_number"],
                        "order_total": parsed["order_total"],
                        "shipping_method": parsed["shipping_method"],
                        "is_priority": parsed["is_priority"],
                        "mcf_order_id": None,
                        "tracking_number": None,
                        "carrier": None,
                        "received_at": date_str,
                        "placed_at": None,
                        "shipped_at": None,
                        "completed_at": None,
                        "archived_at": None,
                        "created_at": datetime.now().isoformat()
                    }
                    new_orders.append(order)
                    tracker["orders"].append(order)
                    priority_tag = " 🚨 PRIORITY" if parsed["is_priority"] else ""
                    log(f"🆕 New Etsy order{priority_tag}: {parsed['brand']} - {(parsed['product'] or '')[:50]}")
        except Exception as e:
            log(f"⚠️ Error searching '{query}': {e}")
    
    tracker["last_check_etsy"] = datetime.now().isoformat()
    return new_orders

def check_shopify_orders(mail, tracker):
    """Check for new Shopify order emails (Kinfolk + Black Owned)."""
    new_orders = []
    mail.select("INBOX")
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    
    search_queries = [
        f'(SINCE {since_date} SUBJECT "[Kinfolk Games] Order")',
        f'(SINCE {since_date} SUBJECT "[Black Owned Games] Order")',
    ]
    
    existing_ids = {o.get("email_id") for o in tracker["orders"] if o.get("email_id")}
    
    for query in search_queries:
        try:
            status, messages = mail.search(None, query)
            if status != "OK":
                continue
            for msg_id in messages[0].split():
                msg_id_str = msg_id.decode()
                if msg_id_str in existing_ids:
                    continue
                
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = decode_mime_header(msg["Subject"])
                body = get_email_body(msg)
                date_str = msg["Date"]
                
                # Only process if it's a Shopify order email
                if "[Kinfolk Games] Order" not in subject and "[Black Owned Games] Order" not in subject:
                    continue
                
                parsed = parse_shopify_order_email(subject, body)
                
                if parsed["order_number"]:
                    order = {
                        "email_id": msg_id_str,
                        "source": "shopify",
                        "status": "NEW",
                        "brand": parsed["brand"] or "Unknown",
                        "customer_name": parsed["customer_name"] or "See email",
                        "street_address": parsed.get("street_address") or "",
                        "street_address_2": parsed.get("street_address_2") or "",
                        "city": parsed.get("city") or "",
                        "state": parsed.get("state") or "",
                        "zip_code": parsed.get("zip_code") or "",
                        "shipping_address": parsed["shipping_address"] or "See email",
                        "product": parsed["product"] or subject,
                        "products": parsed.get("products", []),
                        "quantity": parsed["quantity"] or 1,
                        "etsy_order_number": None,
                        "shopify_order_number": parsed["order_number"],
                        "order_total": parsed["order_total"],
                        "shipping_method": parsed["shipping_method"],
                        "is_priority": parsed["is_priority"],
                        "mcf_order_id": None,
                        "tracking_number": None,
                        "carrier": None,
                        "received_at": date_str,
                        "placed_at": None,
                        "shipped_at": None,
                        "completed_at": None,
                        "archived_at": None,
                        "created_at": datetime.now().isoformat()
                    }
                    new_orders.append(order)
                    tracker["orders"].append(order)
                    priority_tag = " 🚨 PRIORITY" if parsed["is_priority"] else ""
                    items = f" ({parsed['quantity']} items)" if parsed['quantity'] > 1 else ""
                    log(f"🆕 New Shopify order{priority_tag}: {parsed['brand']} - {(parsed['product'] or '')[:50]}{items}")
        except Exception as e:
            log(f"⚠️ Error searching Shopify '{query}': {e}")
    
    tracker["last_check_shopify"] = datetime.now().isoformat()
    return new_orders

def normalize_city_zip(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.upper().strip())

def match_tracking_to_order(parsed, orders):
    """Match a tracking email to an order using city+zip and item name."""
    if not parsed["city_state_zip"] or not parsed["item_name"]:
        return None
    
    tracking_city_zip = normalize_city_zip(parsed["city_state_zip"])
    tracking_item = parsed["item_name"].lower()[:40]
    
    best_match = None
    best_score = 0
    
    for order in orders:
        if order["tracking_number"] is not None:
            continue
        
        score = 0
        
        # Match on zip code
        order_zip = order.get("zip_code", "") or ""
        if not order_zip:
            addr = (order.get("shipping_address") or "").upper()
            zip_match = re.search(r'(\d{5})', addr)
            if zip_match:
                order_zip = zip_match.group(1)
        
        tracking_zip_match = re.search(r'(\d{5})', tracking_city_zip)
        tracking_zip = tracking_zip_match.group(1) if tracking_zip_match else ""
        
        if order_zip and tracking_zip and order_zip.startswith(tracking_zip):
            score += 3
        
        # Match on city
        order_city = (order.get("city") or "").upper()
        tracking_city = tracking_city_zip.split(',')[0].strip() if ',' in tracking_city_zip else ""
        if tracking_city and order_city and tracking_city in order_city:
            score += 2
        
        # Match on item/product name
        order_product = (order.get("product") or "").lower()[:40]
        if tracking_item and order_product:
            tracking_words = set(tracking_item.split()[:4])
            order_words = set(order_product.split()[:4])
            common = tracking_words & order_words
            if len(common) >= 2:
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = order
    
    if best_score >= 3:
        return best_match
    return None

def check_amazon_tracking(mail, tracker):
    """Check for Amazon MCF tracking emails."""
    updates = []
    mail.select("INBOX")
    since_date = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
    
    search_queries = [
        f'(SINCE {since_date} SUBJECT "Your order has shipped" SUBJECT "CONSUMER")',
    ]
    
    processed_mcf_ids = {o.get("mcf_order_id") for o in tracker["orders"] if o.get("mcf_order_id")}
    matchable_orders = [o for o in tracker["orders"] if o["status"] in ("NEW", "PLACED") and o["tracking_number"] is None]
    
    for query in search_queries:
        try:
            status, messages = mail.search(None, query)
            if status != "OK":
                continue
            for msg_id in messages[0].split():
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = decode_mime_header(msg["Subject"])
                body = get_email_body(msg)
                
                parsed = parse_amazon_tracking_email(subject, body)
                if not parsed["tracking_number"]:
                    continue
                if parsed["order_id"] and parsed["order_id"] in processed_mcf_ids:
                    continue
                
                matched_order = match_tracking_to_order(parsed, matchable_orders)
                if matched_order:
                    matched_order["tracking_number"] = parsed["tracking_number"]
                    matched_order["carrier"] = parsed["carrier"] or "Unknown"
                    matched_order["mcf_order_id"] = parsed["order_id"]
                    matched_order["status"] = "SHIPPED"
                    matched_order["shipped_at"] = datetime.now().isoformat()
                    updates.append(matched_order)
                    processed_mcf_ids.add(parsed["order_id"])
                    log(f"📦 Tracking matched: {matched_order['brand']} - {matched_order['product'][:30]} → {parsed['tracking_number']} ({parsed['carrier']})")
                else:
                    log(f"⚠️ Tracking unmatched: {parsed['order_id']} → {parsed['city_state_zip']} - {(parsed['item_name'] or '')[:40]}")
        except Exception as e:
            log(f"⚠️ Error checking Amazon tracking: {e}")
    
    tracker["last_check_amazon"] = datetime.now().isoformat()
    return updates

def auto_archive(tracker):
    """Archive SHIPPED orders older than 3 days. Returns count archived."""
    archived = 0
    now = datetime.now()
    for order in tracker["orders"]:
        if order["status"] == "SHIPPED" and order.get("shipped_at"):
            try:
                shipped = datetime.fromisoformat(order["shipped_at"])
                if (now - shipped).days >= 3:
                    order["status"] = "ARCHIVED"
                    order["archived_at"] = now.isoformat()
                    archived += 1
                    log(f"🗄️ Auto-archived: {order['brand']} - {order['product'][:30]}")
            except:
                pass
    return archived

def generate_status_report(tracker):
    """Generate formatted status report for #orders channel."""
    orders = tracker["orders"]
    
    # Only show active orders (not ARCHIVED or COMPLETE)
    new_orders = [o for o in orders if o["status"] == "NEW"]
    placed_orders = [o for o in orders if o["status"] == "PLACED"]
    shipped_orders = [o for o in orders if o["status"] == "SHIPPED"]
    
    if not new_orders and not placed_orders and not shipped_orders:
        return None
    
    lines = []
    
    # Header
    lines.append(f"**Etsy → MCF Order Tracker** ({datetime.now().strftime('%m/%d %I:%M %p')})")
    lines.append(f"🆕 {len(new_orders)} new | ⏳ {len(placed_orders)} awaiting tracking | 📦 {len(shipped_orders)} ready to complete")
    lines.append("")
    
    # Helper: group orders by brand, with priority orders first within each brand
    def group_by_brand_source(order_list):
        """Group orders by brand + source (Etsy vs Website). Returns dict of display_name → orders."""
        groups = {}
        for o in order_list:
            brand = o.get("brand", "Unknown")
            source = o.get("source", "etsy")
            if source == "shopify":
                key = f"{brand} (Website)"
            else:
                key = f"{brand} (Etsy)"
            if key not in groups:
                groups[key] = []
            groups[key].append(o)
        # Sort groups alphabetically, priority orders first within each
        result = {}
        for key in sorted(groups.keys()):
            priority = [o for o in groups[key] if o.get("is_priority")]
            standard = [o for o in groups[key] if not o.get("is_priority")]
            result[key] = priority + standard
        return result
    
    # New orders section — grouped by brand
    if new_orders:
        lines.append("**🆕 NEW ORDERS — Action Required**")
        lines.append("")
        for brand, orders_in_brand in group_by_brand_source(new_orders).items():
            lines.append(f"__**{brand}**__")
            for o in orders_in_brand:
                is_priority = o.get("is_priority", False)
                priority_tag = "🚨 **PRIORITY** — " if is_priority else ""
                lines.append(f"• {priority_tag}{o['product'][:80]}")
                
                shipping_method = o.get("shipping_method", "Standard")
                if is_priority:
                    lines.append(f"  Shipping: **{shipping_method}**")
                
                # Full address
                name = o.get("customer_name", "See email")
                lines.append(f"  {name}")
                
                street = o.get("street_address", "")
                if street:
                    lines.append(f"  {street}")
                street2 = o.get("street_address_2", "")
                if street2:
                    lines.append(f"  {street2}")
                
                city = o.get("city", "")
                state = o.get("state", "")
                zip_code = o.get("zip_code", "")
                csz = ""
                if city:
                    csz = city
                if state:
                    csz += f", {state}"
                if zip_code:
                    csz += f" {zip_code}"
                if csz:
                    lines.append(f"  {csz}")
                
                # Order info
                order_info = []
                source = o.get("source", "etsy")
                if o.get("shopify_order_number"):
                    order_info.append(f"Shopify #{o['shopify_order_number']}")
                elif o.get("etsy_order_number"):
                    order_info.append(f"Etsy #{o['etsy_order_number']}")
                if o.get("order_total"):
                    order_info.append(o["order_total"])
                if o.get("quantity", 1) > 1:
                    order_info.append(f"Qty: {o['quantity']}")
                if order_info:
                    lines.append(f"  {' | '.join(order_info)}")
                
                # Show individual items for multi-product Shopify orders
                if o.get("products") and len(o["products"]) > 1:
                    for p in o["products"]:
                        lines.append(f"    → {p['name'][:60]} ({p['sku']}) x{p['quantity']}")
                
                if is_priority:
                    lines.append(f"  ⚡ **Place MCF order NOW — customer paid for priority**")
                else:
                    lines.append(f"  ⚡ Place MCF order in Seller Central")
                lines.append("")
    
    # Placed/awaiting tracking — grouped by brand
    if placed_orders:
        lines.append("**⏳ AWAITING TRACKING**")
        lines.append("")
        for brand, orders_in_brand in group_by_brand_source(placed_orders).items():
            lines.append(f"__**{brand}**__")
            for o in orders_in_brand:
                placed_date = ""
                if o.get("placed_at"):
                    try:
                        dt = datetime.fromisoformat(o["placed_at"])
                        placed_date = f" (placed {dt.strftime('%m/%d')})"
                    except:
                        pass
                lines.append(f"• {o['product'][:60]}{placed_date}")
            lines.append("")
    
    # Shipped/tracking ready — grouped by brand
    if shipped_orders:
        lines.append("**📦 TRACKING READY — Paste into Etsy**")
        lines.append("")
        for brand, orders_in_brand in group_by_brand_source(shipped_orders).items():
            lines.append(f"__**{brand}**__")
            for o in orders_in_brand:
                lines.append(f"• {o['product'][:60]}")
                # Customer name + city/state/zip
                name = o.get("customer_name", "")
                city = o.get("city", "")
                state = o.get("state", "")
                zip_code = o.get("zip_code", "")
                csz = ""
                if city:
                    csz = city
                if state:
                    csz += f", {state}"
                if zip_code:
                    csz += f" {zip_code}"
                if name and csz:
                    lines.append(f"  {name} — {csz}")
                elif name:
                    lines.append(f"  {name}")
                carrier = o.get("carrier", "")
                carrier_display = ""
                if carrier == "AMZN_US":
                    carrier_display = "Amazon"
                elif carrier:
                    carrier_display = carrier
                order_ref = ""
                if o.get("shopify_order_number"):
                    order_ref = f" — Shopify #{o['shopify_order_number']}"
                elif o.get("etsy_order_number"):
                    order_ref = f" — Etsy #{o['etsy_order_number']}"
                lines.append(f"  `{o['tracking_number']}` ({carrier_display}){order_ref}")
                lines.append("")
            lines.append("")
    
    return '\n'.join(lines)

def load_last_snapshot():
    """Load previous order states to detect what changed."""
    try:
        with open(LAST_SNAPSHOT_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_snapshot(tracker):
    """Save current order states for next comparison."""
    snapshot = {}
    for o in tracker["orders"]:
        eid = o.get("email_id")
        if eid:
            snapshot[eid] = {"status": o["status"], "tracking_number": o.get("tracking_number")}
    os.makedirs(os.path.dirname(LAST_SNAPSHOT_FILE), exist_ok=True)
    with open(LAST_SNAPSHOT_FILE, 'w') as f:
        json.dump(snapshot, f)

def detect_changes(tracker):
    """Compare current orders against last snapshot. Returns list of (change_type, order) tuples."""
    prev = load_last_snapshot()
    changes = []
    for o in tracker["orders"]:
        eid = o.get("email_id")
        if not eid:
            continue
        
        if eid not in prev:
            changes.append(("new", o))
        else:
            old = prev[eid]
            if old["status"] != o["status"]:
                if o["status"] == "SHIPPED" and old["status"] in ("NEW", "PLACED"):
                    changes.append(("tracking", o))
                elif o["status"] == "ARCHIVED":
                    changes.append(("archived", o))
    return changes

def format_changes_section(changes):
    """Build the full-detail highlighted section for recent changes."""
    if not changes:
        return ""
    
    lines = []
    
    # New orders
    new_orders = [o for t, o in changes if t == "new"]
    if new_orders:
        for o in new_orders:
            is_priority = o.get("is_priority", False)
            source = "Website" if o.get("source") == "shopify" else "Etsy"
            priority_tag = "🚨 **PRIORITY** — " if is_priority else ""
            
            lines.append(f"> 🆕 {priority_tag}**{o.get('brand', 'Unknown')} ({source})**")
            lines.append(f"> {o.get('product', '')[:80]}")
            
            if is_priority:
                lines.append(f"> Shipping: **{o.get('shipping_method', 'Priority')}**")
            
            lines.append(f"> {o.get('customer_name', 'See email')}")
            if o.get("street_address"):
                lines.append(f"> {o['street_address']}")
            if o.get("street_address_2"):
                lines.append(f"> {o['street_address_2']}")
            csz = ""
            if o.get("city"):
                csz = o["city"]
            if o.get("state"):
                csz += f", {o['state']}"
            if o.get("zip_code"):
                csz += f" {o['zip_code']}"
            if csz:
                lines.append(f"> {csz}")
            
            order_info = []
            if o.get("shopify_order_number"):
                order_info.append(f"Shopify #{o['shopify_order_number']}")
            elif o.get("etsy_order_number"):
                order_info.append(f"Etsy #{o['etsy_order_number']}")
            if o.get("order_total"):
                order_info.append(o["order_total"])
            if o.get("quantity", 1) > 1:
                order_info.append(f"Qty: {o['quantity']}")
            if order_info:
                lines.append(f"> {' | '.join(order_info)}")
            
            if o.get("products") and len(o["products"]) > 1:
                for p in o["products"]:
                    lines.append(f">   → {p['name'][:60]} ({p['sku']}) x{p['quantity']}")
            
            if is_priority:
                lines.append(f"> ⚡ **Place MCF order NOW — customer paid for priority**")
            else:
                lines.append(f"> ⚡ Place MCF order in Seller Central")
            lines.append(">")
    
    # Tracking updates
    tracking_orders = [o for t, o in changes if t == "tracking"]
    if tracking_orders:
        for o in tracking_orders:
            source = "Website" if o.get("source") == "shopify" else "Etsy"
            carrier = o.get("carrier", "")
            if carrier == "AMZN_US":
                carrier = "Amazon"
            
            lines.append(f"> 📦 **{o.get('brand', 'Unknown')} ({source})** — Tracking Ready")
            lines.append(f"> {o.get('product', '')[:60]}")
            lines.append(f"> {o.get('customer_name', '')} — {o.get('city', '')}, {o.get('state', '')} {o.get('zip_code', '')}")
            
            order_ref = ""
            if o.get("shopify_order_number"):
                order_ref = f" — Shopify #{o['shopify_order_number']}"
            elif o.get("etsy_order_number"):
                order_ref = f" — Etsy #{o['etsy_order_number']}"
            lines.append(f"> `{o.get('tracking_number', '')}` ({carrier}){order_ref}")
            lines.append(">")
    
    if not lines:
        return ""
    
    return f">>> **✨ LATEST UPDATES**\n" + '\n'.join(lines) + "\n\n"

def get_report_hash(report):
    """Hash report content, ignoring the timestamp line so time-only changes don't trigger updates."""
    if not report:
        return "empty"
    import hashlib
    # Strip the first line (contains timestamp) before hashing
    lines = report.split('\n')
    # Remove the header line with the timestamp
    content = '\n'.join(line for line in lines if not line.startswith('**Etsy → MCF Order Tracker**'))
    return hashlib.md5(content.encode()).hexdigest()

def load_last_report_hash():
    try:
        with open(LAST_REPORT_FILE, 'r') as f:
            return f.read().strip()
    except:
        return ""

def save_last_report_hash(h):
    os.makedirs(os.path.dirname(LAST_REPORT_FILE), exist_ok=True)
    with open(LAST_REPORT_FILE, 'w') as f:
        f.write(h)

def send_email_notification(report, new_count, tracking_count):
    """Send email notification when orders change."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        username, password = get_gmail_credentials()
        if not username or not password:
            log("❌ No credentials for email")
            return False
        
        # Build subject line
        parts = []
        if new_count:
            parts.append(f"{new_count} new order{'s' if new_count > 1 else ''}")
        if tracking_count:
            parts.append(f"{tracking_count} tracking update{'s' if tracking_count > 1 else ''}")
        subject = f"🛒 Etsy Orders: {' + '.join(parts)}" if parts else "🛒 Etsy Order Update"
        
        # Convert markdown-ish report to plain text email
        plain = report.replace("**", "").replace("`", "")
        
        # Build HTML version with highlighted "What's New" section
        html_body = report
        
        # Extract and highlight the "LATEST UPDATES" section
        updates_match = re.search(r'>>> \*\*✨ LATEST UPDATES\*\*\n(.*?)\n\n\*\*', html_body, re.DOTALL)
        if updates_match:
            updates_content = updates_match.group(1)
            # Strip leading "> " from each line
            updates_lines = []
            for line in updates_content.split('\n'):
                line = re.sub(r'^>\s?', '', line)
                updates_lines.append(line)
            updates_clean = '\n'.join(updates_lines)
            updates_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', updates_clean)
            updates_html = re.sub(r'`(.+?)`', r'<code style="background:#e8e8e8; padding:2px 6px; border-radius:3px;">\1</code>', updates_html)
            updates_html = updates_html.replace('\n', '<br>\n')
            highlighted = f"""<div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 12px 16px; margin-bottom: 20px; border-radius: 4px;">
<b style="font-size: 16px;">✨ LATEST UPDATES</b><br><br>
{updates_html}
</div>"""
            # Remove the raw updates section and prepend highlighted version
            html_body = re.sub(r'>>> \*\*✨ LATEST UPDATES\*\*\n.*?\n\n', '', html_body, flags=re.DOTALL)
            html_body = highlighted + html_body
        
        html_body = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html_body)
        html_body = re.sub(r'__(.+?)__', r'<u>\1</u>', html_body)
        html_body = re.sub(r'`(.+?)`', r'<code style="background:#f0f0f0; padding:2px 6px; border-radius:3px; font-size:13px;">\1</code>', html_body)
        html_body = html_body.replace('\n', '<br>\n')
        html = f"""<html><body style="font-family: -apple-system, Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
{html_body}
</body></html>"""
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_ACCOUNT
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(EMAIL_ACCOUNT, NOTIFY_EMAIL, msg.as_string())
        
        log(f"📧 Email sent to {NOTIFY_EMAIL}")
        return True
    except Exception as e:
        log(f"❌ Email failed: {e}")
        return False

DISCORD_ALERTS_CHANNEL = "1468708462949978243"

def load_health():
    try:
        with open(HEALTH_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"last_success": None, "consecutive_failures": 0, "last_failure_reason": None}

def save_health(health):
    os.makedirs(os.path.dirname(HEALTH_FILE), exist_ok=True)
    with open(HEALTH_FILE, 'w') as f:
        json.dump(health, f, indent=2)

def record_success():
    health = load_health()
    health["last_success"] = datetime.now().isoformat()
    health["consecutive_failures"] = 0
    health["last_failure_reason"] = None
    save_health(health)

def record_failure(reason):
    health = load_health()
    health["consecutive_failures"] = health.get("consecutive_failures", 0) + 1
    health["last_failure_reason"] = reason
    save_health(health)
    if health["consecutive_failures"] >= 3:
        alert = f"🚨 **Etsy Order Tracker DOWN** — {health['consecutive_failures']} consecutive failures\nLast error: {reason}\n\nOrders may be missed. Auto-diagnosing now."
        post_to_discord(DISCORD_ALERTS_CHANNEL, alert)
        log(f"🚨 ALERT: {health['consecutive_failures']} consecutive failures — triggering auto-fix")
        # Trigger Ellis to investigate and fix via openclaw wake event
        try:
            subprocess.run(
                ["openclaw", "cron", "wake",
                 "--text", f"URGENT: Etsy Order Tracker has failed {health['consecutive_failures']} times in a row. Last error: {reason}. Diagnose and fix immediately — orders may be getting missed. Check the script at /workspace/scripts/etsy_order_tracker.py, the log at /workspace/data/etsy_orders/etsy_tracker.log, and Gmail credentials. Fix the issue, run a manual --check to verify, and report to Marco in #general what happened and that it's resolved.",
                 "--mode", "now"],
                capture_output=True, text=True, timeout=10
            )
        except Exception as e:
            log(f"⚠️ Failed to trigger wake event: {e}")

def integrity_check():
    """Full scan: compare all Etsy sale emails from last 7 days against tracker. Alert on misses."""
    log("🔍 Running integrity check...")
    username, password = get_gmail_credentials()
    if not username or not password:
        log("❌ Integrity check: no credentials")
        return
    
    mail = connect_to_gmail(password)
    if not mail:
        log("❌ Integrity check: can't connect")
        return
    
    tracker = load_tracker()
    existing_ids = {o.get("email_id") for o in tracker["orders"] if o.get("email_id")}
    
    mail.select("INBOX")
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    
    missed = []
    search_queries = [
        f'(SINCE {since_date} SUBJECT "You made a sale on Etsy")',
        f'(SINCE {since_date} SUBJECT "Etsy transaction")',
        f'(SINCE {since_date} SUBJECT "New order" FROM "etsy")',
        f'(SINCE {since_date} SUBJECT "[Kinfolk Games] Order")',
        f'(SINCE {since_date} SUBJECT "[Black Owned Games] Order")',
    ]
    
    seen_ids = set()
    for query in search_queries:
        try:
            status, messages = mail.search(None, query)
            if status != "OK":
                continue
            for msg_id in messages[0].split():
                msg_id_str = msg_id.decode()
                if msg_id_str in seen_ids:
                    continue
                seen_ids.add(msg_id_str)
                if msg_id_str not in existing_ids:
                    # Fetch subject for the alert
                    status, msg_data = mail.fetch(msg_id, "(RFC822)")
                    if status == "OK":
                        msg = email.message_from_bytes(msg_data[0][1])
                        subject = decode_mime_header(msg["Subject"])
                        date_str = msg["Date"]
                        missed.append({"email_id": msg_id_str, "subject": subject, "date": date_str})
        except Exception as e:
            log(f"⚠️ Integrity check error: {e}")
    
    mail.logout()
    
    if missed:
        alert_lines = [f"🚨 **MISSED ORDERS DETECTED** — {len(missed)} Etsy sale email(s) not in tracker!\n"]
        for m in missed:
            alert_lines.append(f"• {m['subject'][:80]}")
            alert_lines.append(f"  Date: {m['date']}")
            alert_lines.append("")
        alert_lines.append("Running full re-check now to capture them.")
        alert = '\n'.join(alert_lines)
        post_to_discord(DISCORD_ALERTS_CHANNEL, alert)
        # Email disabled — Marco uses Discord now (Feb 9, 2026)
        log(f"🚨 Integrity check: {len(missed)} missed orders detected!")
        
        # Auto-recover: run a full check to pick them up
        mail2 = connect_to_gmail(password)
        if mail2:
            check_etsy_sales(mail2, tracker)
            check_shopify_orders(mail2, tracker)
            check_amazon_tracking(mail2, tracker)
            mail2.logout()
            save_tracker(tracker)
            report = generate_status_report(tracker)
            if report:
                post_to_discord(DISCORD_ORDERS_CHANNEL, report)
                save_last_report_hash(get_report_hash(report))
            log(f"✅ Integrity check: auto-recovered {len(missed)} orders")
    else:
        log(f"✅ Integrity check passed: all {len(seen_ids)} emails accounted for")
    
    # Also check health: has it been too long since last success?
    health = load_health()
    if health.get("last_success"):
        try:
            last = datetime.fromisoformat(health["last_success"])
            hours_ago = (datetime.now() - last).total_seconds() / 3600
            if hours_ago > 2:
                alert = f"⚠️ **Etsy Order Tracker Stale** — Last successful run was {hours_ago:.1f} hours ago. Checking if cron is running."
                post_to_discord(DISCORD_ALERTS_CHANNEL, alert)
                log(f"⚠️ Stale: last success {hours_ago:.1f}h ago")
        except:
            pass

def post_to_discord(channel_id, message):
    """Post message to Discord channel via openclaw CLI."""
    try:
        result = subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "discord",
             "--target", channel_id,
             "--message", message],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            log(f"✅ Posted to Discord #{channel_id}")
            return True
        else:
            log(f"⚠️ Discord post failed: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Discord post error: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Etsy Order Tracker v2")
    parser.add_argument("--check", action="store_true", help="Check for new orders and tracking")
    parser.add_argument("--quiet", action="store_true", help="Capture orders silently — no Discord/email notifications")
    parser.add_argument("--status", action="store_true", help="Print current status")
    parser.add_argument("--post", action="store_true", help="Post status to #orders (even if unchanged)")
    parser.add_argument("--email-digest", action="store_true", help="Send email digest with current status")
    parser.add_argument("--integrity", action="store_true", help="Run integrity check (compare Gmail vs tracker)")
    parser.add_argument("--mark-placed", type=int, help="Mark order index as placed in MCF")
    parser.add_argument("--mark-complete", type=int, help="Mark order index as complete")
    parser.add_argument("--mcf-id", type=str, help="MCF order ID when marking as placed")
    args = parser.parse_args()
    
    tracker = load_tracker()
    
    if args.integrity:
        integrity_check()
        return
    
    if args.check:
        try:
            username, password = get_gmail_credentials()
            if not username or not password:
                record_failure("No credentials")
                log("❌ No credentials")
                return
            
            mail = connect_to_gmail(password)
            if not mail:
                record_failure("Gmail connection failed")
                return
            
            log("Checking for new Etsy sales...")
            new_orders = check_etsy_sales(mail, tracker)
            
            log("Checking for new Shopify orders...")
            shopify_orders = check_shopify_orders(mail, tracker)
            new_orders.extend(shopify_orders)
            
            log("Checking for Amazon tracking updates...")
            tracking_updates = check_amazon_tracking(mail, tracker)
            
            mail.logout()
            
            # Auto-archive old shipped orders
            archived = auto_archive(tracker)
            
            save_tracker(tracker)
            record_success()
            
            # Generate report
            report = generate_status_report(tracker)
            
            if report:
                # Only post to Discord if something changed
                current_hash = get_report_hash(report)
                last_hash = load_last_report_hash()
                
                if current_hash != last_hash:
                    if args.quiet:
                        # Silent mode: save tracker but don't notify
                        # DON'T update the hash or snapshot — let the next daytime run
                        # detect these as "new" and send the full notification
                        log(f"🌙 Quiet mode: {len(new_orders)} new, {len(tracking_updates)} tracking captured silently")
                    else:
                        # Detect what changed and only notify for actionable deltas
                        # (new orders or newly available tracking numbers).
                        changes = detect_changes(tracker)
                        actionable_changes = [c for c in changes if c[0] in ("new", "tracking")]

                        if actionable_changes:
                            changes_section = format_changes_section(actionable_changes)
                            report_with_changes = changes_section + report if changes_section else report

                            # Post to Discord #orders in real-time
                            post_to_discord(DISCORD_ORDERS_CHANNEL, report_with_changes)
                            log(f"📬 Report posted to Discord (new/tracking changes)")
                        else:
                            log("📭 Hash changed from non-actionable updates only (e.g., auto-archive) — no Discord post")

                        # Always advance hash/snapshot in non-quiet mode so archived-only
                        # churn doesn't repeatedly appear as a change.
                        save_last_report_hash(current_hash)
                        save_snapshot(tracker)
                else:
                    log(f"📭 No changes — skipping Discord post")
                
                print(report)
            else:
                log("No pending orders.")
                print("No pending orders.")
            
            summary_parts = []
            if new_orders:
                summary_parts.append(f"{len(new_orders)} new")
            if tracking_updates:
                summary_parts.append(f"{len(tracking_updates)} tracking")
            if archived:
                summary_parts.append(f"{archived} archived")
            log(f"✅ Check complete: {', '.join(summary_parts) if summary_parts else 'no changes'}")
        except Exception as e:
            record_failure(str(e))
            log(f"❌ Check failed: {e}")
            raise
    
    elif args.email_digest:
        # Only send email if something changed since the last email digest
        LAST_DIGEST_HASH = f"{WORKSPACE}/data/etsy_orders/last_digest_hash.txt"
        
        report = generate_status_report(tracker)
        if not report:
            log(f"📧 Email digest skipped — no pending orders")
            print("Nothing to report — no email sent.")
        else:
            current_hash = get_report_hash(report)
            try:
                with open(LAST_DIGEST_HASH, 'r') as f:
                    last_hash = f.read().strip()
            except:
                last_hash = ""
            
            if current_hash != last_hash:
                orders = tracker["orders"]
                new_orders = [o for o in orders if o["status"] == "NEW"]
                shipped_orders = [o for o in orders if o["status"] == "SHIPPED"]
                # Email disabled — Marco uses Discord now (Feb 9, 2026)
                log(f"📧 Email digest skipped — email notifications disabled")
                print("Email notifications disabled — use Discord #orders instead.")
            else:
                log(f"📧 Email digest skipped — nothing changed since last digest")
                print("Nothing changed since last digest — no email sent.")
    
    elif args.status or args.post:
        report = generate_status_report(tracker)
        if report:
            print(report)
            if args.post:
                post_to_discord(DISCORD_ORDERS_CHANNEL, report)
        else:
            print("No pending orders.")
    
    elif args.mark_placed is not None:
        idx = args.mark_placed
        if 0 <= idx < len(tracker["orders"]):
            tracker["orders"][idx]["status"] = "PLACED"
            tracker["orders"][idx]["placed_at"] = datetime.now().isoformat()
            if args.mcf_id:
                tracker["orders"][idx]["mcf_order_id"] = args.mcf_id
            save_tracker(tracker)
            log(f"✅ Order {idx} marked as PLACED")
        else:
            print(f"Invalid index: {idx}")
    
    elif args.mark_complete is not None:
        idx = args.mark_complete
        if 0 <= idx < len(tracker["orders"]):
            tracker["orders"][idx]["status"] = "COMPLETE"
            tracker["orders"][idx]["completed_at"] = datetime.now().isoformat()
            save_tracker(tracker)
            log(f"✅ Order {idx} marked as COMPLETE")
        else:
            print(f"Invalid index: {idx}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
