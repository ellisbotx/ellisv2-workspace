#!/usr/bin/env python3
"""
Etsy OAuth 2.0 Setup Script
Run this once to get your access and refresh tokens.
"""

import json
import webbrowser
import secrets
import hashlib
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import requests

# Load config
CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback."""
    
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query:
            self.server.auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Success!</h1><p>You can close this window and return to the terminal.</p></body></html>')
        else:
            self.server.auth_code = None
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error = query.get('error', ['Unknown error'])[0]
            self.wfile.write(f'<html><body><h1>Error</h1><p>{error}</p></body></html>'.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging

def generate_code_verifier():
    """Generate PKCE code verifier."""
    return secrets.token_urlsafe(32)

def generate_code_challenge(verifier):
    """Generate PKCE code challenge from verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

def main():
    print("=" * 50)
    print("Etsy OAuth Setup")
    print("=" * 50)
    
    config = load_config()
    brand = "card_plug"  # Default to card_plug
    
    api_key = config[brand]["etsy"]["api_key"]
    redirect_uri = "http://localhost:3000/callback"
    
    # Generate PKCE codes
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(16)
    
    # Scopes needed for order access
    scopes = [
        "transactions_r",  # Read transactions/orders
        "transactions_w",  # Write (for updating tracking)
        "shops_r",         # Read shop info
        "shops_w"          # Write shop info (for shipping)
    ]
    
    # Build authorization URL
    auth_params = {
        "response_type": "code",
        "client_id": api_key,
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"https://www.etsy.com/oauth/connect?{urlencode(auth_params)}"
    
    print(f"\n1. Opening browser for Etsy authorization...")
    print(f"\n   If browser doesn't open, visit this URL:\n")
    print(f"   {auth_url}\n")
    
    # Start local server to receive callback
    server = HTTPServer(('localhost', 3000), OAuthCallbackHandler)
    server.auth_code = None
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("2. Waiting for authorization (will timeout in 5 minutes)...")
    server.timeout = 300
    
    while server.auth_code is None:
        server.handle_request()
    
    auth_code = server.auth_code
    print(f"\n3. Received authorization code!")
    
    # Exchange code for tokens
    print("4. Exchanging code for access token...")
    
    token_url = "https://api.etsy.com/v3/public/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": api_key,
        "redirect_uri": redirect_uri,
        "code": auth_code,
        "code_verifier": code_verifier
    }
    
    response = requests.post(token_url, data=token_data)
    
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        
        # Save to config
        config[brand]["etsy"]["access_token"] = access_token
        config[brand]["etsy"]["refresh_token"] = refresh_token
        save_config(config)
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Tokens saved to config.json")
        print("=" * 50)
        print(f"\nAccess Token: {access_token[:20]}...")
        print(f"Refresh Token: {refresh_token[:20]}...")
        print("\nYou can now run the automation script!")
        
    else:
        print(f"\n❌ Failed to get tokens: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
