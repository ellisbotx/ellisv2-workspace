#!/usr/bin/env python3
"""
Etsy → Amazon MCF Automation
Monitors Etsy orders and automatically fulfills them via Amazon Multi-Channel Fulfillment.
"""

import json
import time
import hashlib
import hmac
import base64
import logging
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, quote
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
STATE_FILE = SCRIPT_DIR / "state.json"
LOG_FILE = SCRIPT_DIR / "automation.log"

# Amazon SP-API endpoints
AMAZON_LWA_ENDPOINT = "https://api.amazon.com/auth/o2/token"
AMAZON_SP_API_ENDPOINT = "https://sellingpartnerapi-na.amazon.com"

# Etsy API endpoints
ETSY_API_BASE = "https://openapi.etsy.com/v3"


class Config:
    """Load and manage configuration."""
    
    def __init__(self, brand="card_plug"):
        with open(CONFIG_FILE, 'r') as f:
            self.data = json.load(f)
        self.brand = brand
        self.brand_config = self.data.get(brand, {})
        
    @property
    def etsy(self):
        return self.brand_config.get("etsy", {})
    
    @property
    def amazon(self):
        return self.brand_config.get("amazon", {})


class State:
    """Track processed orders and pending fulfillments."""
    
    def __init__(self):
        self.file = STATE_FILE
        self.data = self._load()
    
    def _load(self):
        if self.file.exists():
            with open(self.file, 'r') as f:
                return json.load(f)
        return {
            "processed_etsy_orders": [],
            "pending_mcf_orders": {},  # etsy_order_id -> mcf_order_id
            "last_check": None
        }
    
    def save(self):
        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def is_processed(self, order_id):
        return str(order_id) in self.data["processed_etsy_orders"]
    
    def mark_processed(self, order_id):
        self.data["processed_etsy_orders"].append(str(order_id))
        # Keep only last 1000 orders
        self.data["processed_etsy_orders"] = self.data["processed_etsy_orders"][-1000:]
        self.save()
    
    def add_pending_mcf(self, etsy_order_id, mcf_order_id):
        self.data["pending_mcf_orders"][str(etsy_order_id)] = mcf_order_id
        self.save()
    
    def remove_pending_mcf(self, etsy_order_id):
        self.data["pending_mcf_orders"].pop(str(etsy_order_id), None)
        self.save()
    
    def get_pending_mcf_orders(self):
        return self.data["pending_mcf_orders"].copy()


class EtsyClient:
    """Etsy API v3 client with OAuth support."""
    
    def __init__(self, config: Config):
        self.api_key = config.etsy["api_key"]
        self.shared_secret = config.etsy["shared_secret"]
        self.shop_name = config.etsy["shop_name"]
        self.shop_id = config.etsy.get("shop_id")
        self.access_token = config.etsy.get("access_token")
        self.refresh_token_value = config.etsy.get("refresh_token")
        self.config = config
        
    def _refresh_access_token(self):
        """Refresh the Etsy access token."""
        if not self.refresh_token_value:
            logger.error("No Etsy refresh token - run etsy_oauth_setup.py first")
            return None
            
        url = "https://api.etsy.com/v3/public/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.api_key,
            "refresh_token": self.refresh_token_value
        }
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info["access_token"]
                self.refresh_token_value = token_info["refresh_token"]
                logger.info("Etsy access token refreshed")
                return self.access_token
            else:
                logger.error(f"Failed to refresh Etsy token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing Etsy token: {e}")
            return None
        
    def _get_headers(self):
        if not self.access_token:
            self._refresh_access_token()
        return {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "Content-Type": "application/json"
        }
    
    def get_shop_id(self):
        """Get numeric shop ID from shop name."""
        if self.shop_id:
            return self.shop_id
        
        headers = self._get_headers()
        if not headers.get("Authorization"):
            logger.error("No access token - run etsy_oauth_setup.py first")
            return None
            
        # Use getMe to get user info, then shops
        url = f"{ETSY_API_BASE}/application/users/me"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("user_id")
                
                # Now get the shop for this user
                shop_url = f"{ETSY_API_BASE}/application/users/{user_id}/shops"
                shop_response = requests.get(shop_url, headers=headers)
                
                if shop_response.status_code == 200:
                    shops = shop_response.json().get("results", [])
                    if shops:
                        self.shop_id = shops[0].get("shop_id")
                        logger.info(f"Found shop ID: {self.shop_id}")
                        return self.shop_id
                        
                logger.error(f"Failed to get shop: {shop_response.status_code}")
                return None
            elif response.status_code == 401:
                # Token expired, try refresh
                self._refresh_access_token()
                return self.get_shop_id()
            else:
                logger.error(f"Failed to get user: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting shop ID: {e}")
            return None
    
    def get_open_orders(self):
        """Get open/unfulfilled orders from Etsy."""
        shop_id = self.get_shop_id()
        if not shop_id:
            logger.error("Cannot get orders without shop ID")
            return []
        
        headers = self._get_headers()
        
        # Get receipts (orders) that are not shipped
        url = f"{ETSY_API_BASE}/application/shops/{shop_id}/receipts"
        params = {
            "was_shipped": "false",
            "was_paid": "true",
            "limit": 25
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("results", [])
                logger.info(f"Found {len(orders)} open orders on Etsy")
                return orders
            elif response.status_code == 401:
                # Try refreshing token
                self._refresh_access_token()
                headers = self._get_headers()
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                logger.error("Etsy API authentication failed after token refresh")
                return []
            else:
                logger.error(f"Failed to get orders: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def update_tracking(self, receipt_id, carrier, tracking_number):
        """Update an Etsy order with tracking information."""
        shop_id = self.get_shop_id()
        if not shop_id:
            return False
        
        url = f"{ETSY_API_BASE}/application/shops/{shop_id}/receipts/{receipt_id}/tracking"
        headers = self._get_headers()
        
        # Map Amazon carrier names to Etsy carrier names
        carrier_map = {
            "USPS": "usps",
            "UPS": "ups",
            "FEDEX": "fedex",
            "DHL": "dhl",
            "AMAZON": "other"
        }
        etsy_carrier = carrier_map.get(carrier.upper(), "other")
        
        data = {
            "tracking_code": tracking_number,
            "carrier_name": etsy_carrier
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code in [200, 201]:
                logger.info(f"Updated tracking for order {receipt_id}: {tracking_number}")
                return True
            else:
                logger.error(f"Failed to update tracking: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating tracking: {e}")
            return False


class AmazonSPAPI:
    """Amazon Selling Partner API client for MCF."""
    
    def __init__(self, config: Config):
        self.client_id = config.amazon["client_id"]
        self.client_secret = config.amazon["client_secret"]
        self.refresh_token = config.amazon["refresh_token"]
        self.seller_id = config.amazon["seller_id"]
        self.marketplace_id = config.amazon.get("marketplace", "ATVPDKIKX0DER")  # US
        self.access_token = None
        self.token_expires = None
    
    def _refresh_access_token(self):
        """Get a new access token using the refresh token."""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(AMAZON_LWA_ENDPOINT, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                logger.info("Amazon access token refreshed")
                return self.access_token
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def _get_headers(self):
        token = self._refresh_access_token()
        if not token:
            return None
        return {
            "x-amz-access-token": token,
            "Content-Type": "application/json"
        }
    
    def create_fulfillment_order(self, order_data):
        """
        Create an MCF fulfillment order.
        
        order_data should contain:
        - seller_fulfillment_order_id: unique ID for this order
        - displayable_order_id: customer-facing order ID
        - displayable_order_date: ISO date string
        - displayable_order_comment: message to include
        - shipping_speed: Standard, Expedited, or Priority
        - destination_address: dict with name, addressLine1, city, stateOrRegion, postalCode, countryCode
        - items: list of dicts with sellerSku, sellerFulfillmentOrderItemId, quantity
        """
        headers = self._get_headers()
        if not headers:
            return None
        
        url = f"{AMAZON_SP_API_ENDPOINT}/fba/outbound/2020-07-01/fulfillmentOrders"
        
        payload = {
            "sellerFulfillmentOrderId": order_data["seller_fulfillment_order_id"],
            "displayableOrderId": order_data["displayable_order_id"],
            "displayableOrderDate": order_data["displayable_order_date"],
            "displayableOrderComment": order_data.get("displayable_order_comment", "Thank you for your order!"),
            "shippingSpeedCategory": order_data.get("shipping_speed", "Standard"),
            "destinationAddress": order_data["destination_address"],
            "items": order_data["items"],
            "marketplaceId": self.marketplace_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in [200, 201]:
                logger.info(f"Created MCF order: {order_data['seller_fulfillment_order_id']}")
                return order_data["seller_fulfillment_order_id"]
            else:
                logger.error(f"Failed to create MCF order: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating MCF order: {e}")
            return None
    
    def get_fulfillment_order(self, seller_fulfillment_order_id):
        """Get status and tracking for an MCF order."""
        headers = self._get_headers()
        if not headers:
            return None
        
        url = f"{AMAZON_SP_API_ENDPOINT}/fba/outbound/2020-07-01/fulfillmentOrders/{seller_fulfillment_order_id}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get MCF order: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting MCF order: {e}")
            return None
    
    def get_tracking_info(self, seller_fulfillment_order_id):
        """Extract tracking info from a fulfillment order."""
        order = self.get_fulfillment_order(seller_fulfillment_order_id)
        if not order:
            return None
        
        payload = order.get("payload", {})
        fulfillment_order = payload.get("fulfillmentOrder", {})
        status = fulfillment_order.get("fulfillmentOrderStatus")
        
        # Get shipments
        fulfillment_shipments = payload.get("fulfillmentShipments", [])
        
        for shipment in fulfillment_shipments:
            tracking = shipment.get("fulfillmentShipmentPackage", [])
            for package in tracking:
                tracking_number = package.get("trackingNumber")
                carrier = package.get("carrierCode")
                if tracking_number:
                    return {
                        "status": status,
                        "tracking_number": tracking_number,
                        "carrier": carrier
                    }
        
        return {"status": status, "tracking_number": None, "carrier": None}


class EtsyMCFAutomation:
    """Main automation class that ties everything together."""
    
    def __init__(self, brand="card_plug"):
        self.config = Config(brand)
        self.state = State()
        self.etsy = EtsyClient(self.config)
        self.amazon = AmazonSPAPI(self.config)
        self.sku_map = self._load_sku_map()
    
    def _load_sku_map(self):
        """Load Etsy listing ID to Amazon SKU mapping."""
        map_file = SCRIPT_DIR / "sku_map.json"
        if map_file.exists():
            with open(map_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_sku_map(self):
        """Save SKU mapping."""
        map_file = SCRIPT_DIR / "sku_map.json"
        with open(map_file, 'w') as f:
            json.dump(self.sku_map, f, indent=2)
    
    def _etsy_to_amazon_address(self, etsy_order):
        """Convert Etsy address format to Amazon format."""
        return {
            "name": etsy_order.get("name", "Customer"),
            "addressLine1": etsy_order.get("first_line", ""),
            "addressLine2": etsy_order.get("second_line", ""),
            "city": etsy_order.get("city", ""),
            "stateOrRegion": etsy_order.get("state", ""),
            "postalCode": etsy_order.get("zip", ""),
            "countryCode": etsy_order.get("country_iso", "US")
        }
    
    def process_new_orders(self):
        """Check for new Etsy orders and create MCF fulfillments."""
        logger.info("Checking for new Etsy orders...")
        orders = self.etsy.get_open_orders()
        
        new_orders_processed = 0
        for order in orders:
            receipt_id = order.get("receipt_id")
            
            if self.state.is_processed(receipt_id):
                continue
            
            logger.info(f"Processing new order: {receipt_id}")
            
            # Extract order details
            transactions = order.get("transactions", [])
            if not transactions:
                logger.warning(f"Order {receipt_id} has no transactions, skipping")
                continue
            
            # Build MCF order
            items = []
            for txn in transactions:
                listing_id = str(txn.get("listing_id"))
                quantity = txn.get("quantity", 1)
                
                # Look up Amazon SKU
                amazon_sku = self.sku_map.get(listing_id)
                if not amazon_sku:
                    logger.warning(f"No SKU mapping for Etsy listing {listing_id}")
                    # Use listing ID as SKU fallback (won't work without mapping)
                    continue
                
                items.append({
                    "sellerSku": amazon_sku,
                    "sellerFulfillmentOrderItemId": f"{receipt_id}-{listing_id}",
                    "quantity": quantity
                })
            
            if not items:
                logger.warning(f"Order {receipt_id} has no mappable items, skipping")
                self.state.mark_processed(receipt_id)
                continue
            
            # Create MCF order
            mcf_order_id = f"ETSY-{receipt_id}"
            order_data = {
                "seller_fulfillment_order_id": mcf_order_id,
                "displayable_order_id": f"Etsy #{receipt_id}",
                "displayable_order_date": order.get("created_timestamp", datetime.now().isoformat()),
                "displayable_order_comment": "Thank you for your Etsy order!",
                "shipping_speed": "Standard",
                "destination_address": self._etsy_to_amazon_address(order),
                "items": items
            }
            
            result = self.amazon.create_fulfillment_order(order_data)
            if result:
                self.state.add_pending_mcf(receipt_id, mcf_order_id)
                self.state.mark_processed(receipt_id)
                new_orders_processed += 1
                logger.info(f"Created MCF order {mcf_order_id} for Etsy order {receipt_id}")
            else:
                logger.error(f"Failed to create MCF order for {receipt_id}")
        
        return new_orders_processed
    
    def check_tracking_updates(self):
        """Check pending MCF orders for tracking updates."""
        logger.info("Checking for tracking updates...")
        pending = self.state.get_pending_mcf_orders()
        
        updates_pushed = 0
        for etsy_order_id, mcf_order_id in pending.items():
            tracking_info = self.amazon.get_tracking_info(mcf_order_id)
            
            if not tracking_info:
                continue
            
            status = tracking_info.get("status")
            tracking_number = tracking_info.get("tracking_number")
            carrier = tracking_info.get("carrier")
            
            logger.info(f"MCF order {mcf_order_id}: status={status}, tracking={tracking_number}")
            
            if tracking_number:
                # Push tracking to Etsy
                success = self.etsy.update_tracking(etsy_order_id, carrier or "OTHER", tracking_number)
                if success:
                    self.state.remove_pending_mcf(etsy_order_id)
                    updates_pushed += 1
                    logger.info(f"Pushed tracking to Etsy order {etsy_order_id}")
            elif status in ["Complete", "Cancelled"]:
                # Order complete but no tracking (shouldn't happen)
                self.state.remove_pending_mcf(etsy_order_id)
        
        return updates_pushed
    
    def run_once(self):
        """Run one cycle of the automation."""
        logger.info("=" * 50)
        logger.info("Starting automation cycle")
        
        # Process new orders
        new_orders = self.process_new_orders()
        logger.info(f"Processed {new_orders} new orders")
        
        # Check tracking updates
        tracking_updates = self.check_tracking_updates()
        logger.info(f"Pushed {tracking_updates} tracking updates")
        
        logger.info("Cycle complete")
        return {"new_orders": new_orders, "tracking_updates": tracking_updates}
    
    def run_daemon(self, interval_seconds=300):
        """Run continuously, checking every interval."""
        logger.info(f"Starting daemon mode (interval: {interval_seconds}s)")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"Error in automation cycle: {e}")
            
            logger.info(f"Sleeping for {interval_seconds} seconds...")
            time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="Etsy → Amazon MCF Automation")
    parser.add_argument("--brand", default="card_plug", help="Brand to process (default: card_plug)")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    parser.add_argument("--test-amazon", action="store_true", help="Test Amazon API connection")
    parser.add_argument("--test-etsy", action="store_true", help="Test Etsy API connection")
    args = parser.parse_args()
    
    automation = EtsyMCFAutomation(args.brand)
    
    if args.test_amazon:
        logger.info("Testing Amazon SP-API connection...")
        token = automation.amazon._refresh_access_token()
        if token:
            logger.info("✅ Amazon API connection successful!")
        else:
            logger.error("❌ Amazon API connection failed")
        return
    
    if args.test_etsy:
        logger.info("Testing Etsy API connection...")
        shop_id = automation.etsy.get_shop_id()
        if shop_id:
            logger.info(f"✅ Etsy API connection successful! Shop ID: {shop_id}")
            orders = automation.etsy.get_open_orders()
            logger.info(f"   Found {len(orders)} open orders")
        else:
            logger.error("❌ Etsy API connection failed")
        return
    
    if args.daemon:
        automation.run_daemon(args.interval)
    else:
        automation.run_once()


if __name__ == "__main__":
    main()
