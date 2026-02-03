# Etsy → Amazon MCF Automation

Automatically fulfills Etsy orders through Amazon Multi-Channel Fulfillment (MCF).

## Setup Status

### Card Plug
- [x] Etsy API Key
- [x] Amazon SP-API Credentials  
- [ ] Etsy OAuth Token (need to run setup)
- [ ] SKU Mapping (Etsy listings → Amazon SKUs)

## Files

| File | Purpose |
|------|---------|
| `config.json` | API credentials (keep secure!) |
| `sku_map.json` | Maps Etsy listing IDs to Amazon SKUs |
| `state.json` | Tracks processed orders (auto-generated) |
| `etsy_mcf_automation.py` | Main automation script |
| `etsy_oauth_setup.py` | One-time Etsy authorization |

## Quick Start

### 1. Authorize Etsy (one-time)
```bash
cd /Users/ellisbot/.openclaw/workspace/scripts/etsy-mcf
python3 etsy_oauth_setup.py
```
This opens a browser - log into Etsy and authorize the app.

### 2. Set up SKU mapping
Edit `sku_map.json` to map Etsy listing IDs to Amazon SKUs:
```json
{
  "1234567890": "CARDPLUG-GAME-001",
  "9876543210": "CARDPLUG-GAME-002"
}
```

### 3. Test the connection
```bash
python3 etsy_mcf_automation.py --test-etsy
python3 etsy_mcf_automation.py --test-amazon
```

### 4. Run once (manual)
```bash
python3 etsy_mcf_automation.py
```

### 5. Run continuously (daemon mode)
```bash
python3 etsy_mcf_automation.py --daemon --interval 300
```
Checks every 5 minutes (300 seconds).

## How It Works

1. **Polls Etsy** for new paid, unshipped orders
2. **Creates MCF order** in Amazon for each new order
3. **Monitors Amazon** for tracking numbers
4. **Updates Etsy** with tracking when available

## Troubleshooting

### "No Etsy refresh token"
Run `python3 etsy_oauth_setup.py` to authorize.

### "No SKU mapping for Etsy listing"
Add the listing ID to `sku_map.json`.

### Amazon token errors
The refresh token may have expired. Get a new one from Seller Central.
