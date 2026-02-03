#!/usr/bin/env python3
"""
Etsy → Amazon MCF Fulfillment Automation
Card Plug Brand

Polls Etsy for new orders, creates MCF fulfillment requests on Amazon,
and updates Etsy with tracking info.
"""

import os
import json
import time
import hashlib
import hmac
import requests
from datetime import datetime, timezone
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

BRAND = "cardplug"
DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/fulfillment")
CREDS_DIR = Path("/Users/ellisbot/.openclaw/workspace/credentials")
LOG_FILE = DATA_DIR / f"{BRAND}_fulfillment.log"
STATE_FILE = DATA_DIR / f"{BRAND}_processed_orders.json"
SKU_MAP_FILE = DATA_DIR / f"{BRAND}_sku_map.json"

# Amazon SP-API endpoints
AMAZON_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
AMAZON_SP_API_BASE = "https://sellingpartnerapi-na.amazon.com"

# Etsy API endpoints
ETSY_API_BASE = "https://api.etsy.com/v3"

# =============================================================================
# CREDENTIALS LOADER
# =============================================================================

def load_credentials():
    """Load credentials from files"""
    creds = {"amazon": {}, "etsy": {}}
    
    # Load Amazon credentials
    amazon_file = CREDS_DIR / f"{BRAND}_amazon.txt"
    if amazon_file.exists():
        for line in amazon_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                creds["amazon"][key.strip()] = value.strip()
    
    # Load Etsy credentials
    etsy_file = CREDS_DIR / f"{BRAND}_etsy.txt"
    if etsy_file.exists():
        for line in etsy_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                creds["etsy"][key.strip()] = value.strip()
    
    return creds

# =============================================================================
# AMAZON SP-API CLIENT
# =============================================================================

class AmazonMCFClient:
    def __init__(self, creds):
        self.client_id = creds["CLIENT_ID"]
        self.client_secret = creds["CLIENT_SECRET"]
        self.refresh_token = creds["REFRESH_TOKEN"]
        self.seller_id = creds["SELLER_ID"]
        self.marketplace_id = creds.get("MARKETPLACE_ID", "ATVPDKIKX0DER")
        self.access_token = None
        self.token_expires = 0
    
    def get_access_token(self):
        """Get or refresh access token"""
        if self.access_token and time.time() < self.token_expires - 60:
            return self.access_token
        
        response = requests.post(AMAZON_TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        
        if response.status_code != 200:
            raise Exception(f"Failed to get Amazon access token: {response.text}")
        
        data = response.json()
        self.access_token = data["access_token"]
        self.token_expires = time.time() + data["expires_in"]
        return self.access_token
    
    def _request(self, method, path, **kwargs):
        """Make authenticated request to SP-API"""
        token = self.get_access_token()
        headers = kwargs.pop("headers", {})
        headers["x-amz-access-token"] = token
        headers["Content-Type"] = "application/json"
        
        url = f"{AMAZON_SP_API_BASE}{path}"
        response = requests.request(method, url, headers=headers, **kwargs)
        return response
    
    def create_fulfillment_order(self, order_id, items, shipping_address, shipping_speed="Standard"):
        """
        Create an MCF fulfillment order
        
        items: list of {"sku": "AMAZON_SKU", "quantity": 1}
        shipping_address: {"name", "address1", "city", "state", "postal_code", "country"}
        shipping_speed: "Standard", "Expedited", or "Priority"
        """
        path = "/fba/outbound/2020-07-01/fulfillmentOrders"
        
        # Build line items
        line_items = []
        for i, item in enumerate(items):
            line_items.append({
                "sellerSku": item["sku"],
                "sellerFulfillmentOrderItemId": f"{order_id}-{i+1}",
                "quantity": item["quantity"]
            })
        
        payload = {
            "sellerFulfillmentOrderId": f"ETSY-{order_id}",
            "displayableOrderId": f"ETSY-{order_id}",
            "displayableOrderDate": datetime.now(timezone.utc).isoformat(),
            "displayableOrderComment": f"Etsy Order {order_id}",
            "shippingSpeedCategory": shipping_speed,
            "destinationAddress": {
                "name": shipping_address["name"],
                "addressLine1": shipping_address["address1"],
                "addressLine2": shipping_address.get("address2", ""),
                "city": shipping_address["city"],
                "stateOrRegion": shipping_address["state"],
                "postalCode": shipping_address["postal_code"],
                "countryCode": shipping_address.get("country", "US")
            },
            "items": line_items
        }
        
        response = self._request("POST", path, json=payload)
        
        if response.status_code in [200, 201]:
            log(f"✓ Created MCF order for Etsy #{order_id}")
            return {"success": True, "data": response.json() if response.text else {}}
        else:
            log(f"✗ Failed to create MCF order: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
    
    def get_fulfillment_order(self, order_id):
        """Get status of a fulfillment order"""
        path = f"/fba/outbound/2020-07-01/fulfillmentOrders/ETSY-{order_id}"
        response = self._request("GET", path)
        
        if response.status_code == 200:
            return response.json()
        return None

# =============================================================================
# ETSY API CLIENT
# =============================================================================

class EtsyClient:
    def __init__(self, creds):
        self.keystring = creds["KEYSTRING"]
        self.shared_secret = creds["SHARED_SECRET"]
        self.shop_id = creds["SHOP_ID"]
        self.access_token = creds.get("ACCESS_TOKEN", "")
        self.refresh_token = creds.get("REFRESH_TOKEN", "")
    
    def is_configured(self):
        """Check if we have valid credentials"""
        return bool(self.access_token)
    
    def _request(self, method, path, **kwargs):
        """Make authenticated request to Etsy API"""
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers["x-api-key"] = self.keystring
        
        url = f"{ETSY_API_BASE}{path}"
        response = requests.request(method, url, headers=headers, **kwargs)
        return response
    
    def get_open_orders(self):
        """Get all open (unfulfilled) orders"""
        path = f"/application/shops/{self.shop_id}/receipts?was_shipped=false&was_paid=true"
        response = self._request("GET", path)
        
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            log(f"✗ Failed to get Etsy orders: {response.status_code} - {response.text}")
            return []
    
    def mark_shipped(self, receipt_id, tracking_number, carrier):
        """Mark an order as shipped with tracking info"""
        path = f"/application/shops/{self.shop_id}/receipts/{receipt_id}/tracking"
        
        payload = {
            "tracking_code": tracking_number,
            "carrier_name": carrier
        }
        
        response = self._request("POST", path, json=payload)
        
        if response.status_code in [200, 201]:
            log(f"✓ Updated Etsy order #{receipt_id} with tracking")
            return True
        else:
            log(f"✗ Failed to update Etsy tracking: {response.status_code} - {response.text}")
            return False

# =============================================================================
# SKU MAPPING
# =============================================================================

def load_sku_map():
    """Load Etsy listing ID → Amazon SKU mapping"""
    if SKU_MAP_FILE.exists():
        return json.loads(SKU_MAP_FILE.read_text())
    return {}

def save_sku_map(sku_map):
    """Save SKU mapping"""
    SKU_MAP_FILE.write_text(json.dumps(sku_map, indent=2))

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def load_processed_orders():
    """Load set of already-processed order IDs"""
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()

def save_processed_orders(orders):
    """Save processed order IDs"""
    STATE_FILE.write_text(json.dumps(list(orders)))

# =============================================================================
# LOGGING
# =============================================================================

def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_orders():
    """Main order processing loop"""
    log("=" * 50)
    log(f"Starting Etsy→MCF fulfillment check for {BRAND.upper()}")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load credentials
    creds = load_credentials()
    
    # Check Etsy credentials
    etsy = EtsyClient(creds["etsy"])
    if not etsy.is_configured():
        log("⚠ Etsy API not configured yet (waiting for approval)")
        log("  Once approved, run etsy_oauth.py to get access token")
        return
    
    # Initialize Amazon client
    amazon = AmazonMCFClient(creds["amazon"])
    
    # Load state
    processed = load_processed_orders()
    sku_map = load_sku_map()
    
    if not sku_map:
        log("⚠ No SKU mapping configured. Create sku_map.json with:")
        log('  {"etsy_listing_id": "amazon_sku", ...}')
        return
    
    # Get open orders from Etsy
    orders = etsy.get_open_orders()
    log(f"Found {len(orders)} open Etsy orders")
    
    new_orders = 0
    for order in orders:
        receipt_id = str(order["receipt_id"])
        
        if receipt_id in processed:
            continue
        
        new_orders += 1
        log(f"Processing new order #{receipt_id}")
        
        # Extract shipping address
        shipping = {
            "name": order.get("name", ""),
            "address1": order.get("first_line", ""),
            "address2": order.get("second_line", ""),
            "city": order.get("city", ""),
            "state": order.get("state", ""),
            "postal_code": order.get("zip", ""),
            "country": order.get("country_iso", "US")
        }
        
        # Map Etsy items to Amazon SKUs
        items = []
        unmapped = []
        
        for transaction in order.get("transactions", []):
            listing_id = str(transaction["listing_id"])
            quantity = transaction["quantity"]
            
            if listing_id in sku_map:
                items.append({
                    "sku": sku_map[listing_id],
                    "quantity": quantity
                })
            else:
                unmapped.append(listing_id)
        
        if unmapped:
            log(f"  ⚠ Unmapped listings: {unmapped} - skipping order")
            continue
        
        if not items:
            log(f"  ⚠ No items to fulfill - skipping")
            continue
        
        # Create MCF order
        result = amazon.create_fulfillment_order(
            order_id=receipt_id,
            items=items,
            shipping_address=shipping
        )
        
        if result["success"]:
            processed.add(receipt_id)
            save_processed_orders(processed)
    
    log(f"Processed {new_orders} new orders")
    log("Done")

def check_tracking():
    """Check MCF orders for tracking updates and push to Etsy"""
    log("Checking for tracking updates...")
    
    creds = load_credentials()
    etsy = EtsyClient(creds["etsy"])
    amazon = AmazonMCFClient(creds["amazon"])
    
    if not etsy.is_configured():
        return
    
    # Load orders that need tracking updates
    tracking_file = DATA_DIR / f"{BRAND}_pending_tracking.json"
    if not tracking_file.exists():
        return
    
    pending = json.loads(tracking_file.read_text())
    updated = []
    
    for order_id in pending:
        fulfillment = amazon.get_fulfillment_order(order_id)
        if not fulfillment:
            continue
        
        # Check for tracking info
        packages = fulfillment.get("fulfillmentOrderResult", {}).get("fulfillmentShipments", [])
        for package in packages:
            tracking = package.get("trackingNumber")
            carrier = package.get("carrierCode", "USPS")
            
            if tracking:
                if etsy.mark_shipped(order_id, tracking, carrier):
                    updated.append(order_id)
                break
    
    # Remove updated orders from pending
    pending = [o for o in pending if o not in updated]
    tracking_file.write_text(json.dumps(pending))
    
    log(f"Updated tracking for {len(updated)} orders")

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--tracking":
        check_tracking()
    else:
        process_orders()
