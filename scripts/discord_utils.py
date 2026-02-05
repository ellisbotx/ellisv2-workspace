#!/usr/bin/env python3
"""
Discord Utilities for OpenClaw
Helpers for posting messages to the right channels
"""

import json
import subprocess
from pathlib import Path

WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
CONFIG_PATH = WORKSPACE / "config" / "discord_channels.json"


def load_config():
    """Load Discord channel configuration."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Discord config not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def get_channel_id(channel_name):
    """Get channel ID by name (e.g., 'reports', 'alerts')."""
    config = load_config()
    if channel_name not in config["channels"]:
        raise ValueError(f"Channel '{channel_name}' not found in config")
    return config["channels"][channel_name]["id"]


def post_message(channel_name, message, silent=False):
    """
    Post a message to a Discord channel.
    
    Args:
        channel_name: Channel key from config (e.g., 'reports', 'alerts')
        message: Message text (markdown supported)
        silent: If True, suppress notification
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        channel_id = get_channel_id(channel_name)
        
        cmd = [
            "openclaw", "message", "send",
            "--channel", "discord",
            "--target", channel_id,
            "--message", message
        ]
        
        if silent:
            cmd.append("--silent")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    
    except Exception as e:
        print(f"Failed to post to #{channel_name}: {e}")
        return False


def post_alert(message):
    """Post to #alerts channel."""
    return post_message("alerts", message)


def post_report(message, silent=True):
    """Post to #reports channel (silent by default)."""
    return post_message("reports", message, silent=silent)


def post_automation(message, silent=True):
    """Post to #automation channel (silent by default)."""
    return post_message("automation", message, silent=silent)


def post_orders(message):
    """Post to #orders channel."""
    return post_message("orders", message)


def post_inventory(message):
    """Post to #inventory channel."""
    return post_message("inventory", message)


def post_products(message):
    """Post to #products channel."""
    return post_message("products", message)


def post_analytics(message):
    """Post to #analytics channel."""
    return post_message("analytics", message)


def post_dashboard(message):
    """Post to #dashboard channel."""
    return post_message("dashboard", message)


def post_suppliers(message):
    """Post to #suppliers channel."""
    return post_message("suppliers", message)


def post_creative(message):
    """Post to #creative channel."""
    return post_message("creative", message)


def post_finance(message):
    """Post to #finance channel."""
    return post_message("finance", message)


def post_done(message, silent=True):
    """Post to #done channel (silent by default)."""
    return post_message("done", message, silent=silent)


def post_system(message):
    """Post to #system channel (for meta updates, learning, memory, skills)."""
    return post_message("system", message)


if __name__ == "__main__":
    # Test posting
    print("Testing Discord posting...")
    
    # Test report
    post_report("📊 Test report message")
    print("Posted to #reports")
    
    # Test automation
    post_automation("⚙️ Test automation message")
    print("Posted to #automation")
    
    print("\nDone! Check Discord channels.")
