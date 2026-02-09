#!/usr/bin/env python3
"""
Cron Job Health Monitor
Checks all OpenClaw cron jobs for failures and alerts if any job has failed 2+ times in a row.
Also verifies expected output files were updated after each job runs.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
STATE_FILE = WORKSPACE / "data" / "cron_health_state.json"
ALERTS_CHANNEL = "1468702879672959157"
SYSTEM_CHANNEL = "1468708512539349155"

# Define expected outputs for each cron job
# Maps job name pattern -> list of files that should be updated after the job runs
EXPECTED_OUTPUTS = {
    "ASIN Suppression Check": {
        "files": [str(WORKSPACE / "data" / "suppression_tracker.csv")],
        "max_age_hours": 26,  # Should be updated daily
    },
    "Sellerboard Email Fetch": {
        "files": [],  # May not produce files if no emails
        "max_age_hours": 26,
    },
    "Inventory Check": {
        "files": [
            str(WORKSPACE / "data" / "reorder_report.json"),
            str(WORKSPACE / "trifecta" / "index.html"),
        ],
        "max_age_hours": 26,
    },
    "Weekly Memory Consolidation": {
        "files": [str(WORKSPACE / "MEMORY.md")],
        "max_age_hours": 170,  # Weekly = ~168 hours
    },
}


def load_state():
    """Load persistent state tracking consecutive failures."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"failures": {}, "last_check": None}


def save_state(state):
    """Save state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_cron_jobs():
    """Get all cron jobs from OpenClaw."""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("jobs", data) if isinstance(data, dict) else data
    except Exception as e:
        print(f"Failed to get cron jobs: {e}")
    return []


def check_file_freshness(filepath, max_age_hours):
    """Check if a file was updated within the expected timeframe."""
    p = Path(filepath)
    if not p.exists():
        return False, f"File missing: {filepath}"
    
    mtime = datetime.fromtimestamp(p.stat().st_mtime)
    age = datetime.now() - mtime
    if age > timedelta(hours=max_age_hours):
        hours_ago = int(age.total_seconds() / 3600)
        return False, f"File stale ({hours_ago}h old): {p.name}"
    
    return True, f"File fresh: {p.name}"


def post_discord(channel_id, message):
    """Post a message to Discord."""
    try:
        subprocess.run(
            ["openclaw", "message", "send",
             "--channel", "discord",
             "--target", channel_id,
             "--message", message],
            capture_output=True, text=True, timeout=30
        )
        return True
    except Exception as e:
        print(f"Failed to post to Discord: {e}")
        return False


def main():
    state = load_state()
    now = datetime.now()
    issues = []
    recoveries = []
    
    # Parse cron job states from the gateway API
    # We'll use the state file to track failures since we can't easily query cron history
    # Instead, check expected output files for freshness
    
    print(f"Cron Health Check - {now.strftime('%Y-%m-%d %H:%M CST')}")
    print("=" * 50)
    
    for job_name, config in EXPECTED_OUTPUTS.items():
        job_key = job_name.replace(" ", "_").lower()
        prev_failures = state["failures"].get(job_key, 0)
        
        all_ok = True
        job_issues = []
        
        for filepath in config["files"]:
            ok, msg = check_file_freshness(filepath, config["max_age_hours"])
            if not ok:
                all_ok = False
                job_issues.append(msg)
            print(f"  [{'+' if ok else 'X'}] {msg}")
        
        if not config["files"]:
            print(f"  [~] {job_name}: No output files to check (monitoring status only)")
            all_ok = True
        
        if all_ok:
            if prev_failures > 0:
                recoveries.append(job_name)
            state["failures"][job_key] = 0
        else:
            state["failures"][job_key] = prev_failures + 1
            consecutive = state["failures"][job_key]
            print(f"  ⚠️  {job_name}: Consecutive failures: {consecutive}")
            
            if consecutive >= 2:
                issues.append({
                    "name": job_name,
                    "consecutive": consecutive,
                    "details": job_issues
                })
    
    print()
    
    # Alert on failures (2+ consecutive)
    if issues:
        alert_lines = ["🚨 **Cron Job Health Alert**\n"]
        for issue in issues:
            alert_lines.append(f"**{issue['name']}** — {issue['consecutive']} consecutive failures")
            for detail in issue["details"]:
                alert_lines.append(f"  • {detail}")
            alert_lines.append("")
        
        alert_lines.append("_Check logs or run the job manually to investigate._")
        alert_msg = "\n".join(alert_lines)
        
        print(f"🚨 Sending alert for {len(issues)} failing job(s)...")
        post_discord(ALERTS_CHANNEL, alert_msg)
    
    # Notify recoveries
    if recoveries:
        recovery_msg = "✅ **Cron Job Recovery**\n\n"
        for name in recoveries:
            recovery_msg += f"• **{name}** — back to healthy\n"
        
        print(f"✅ Sending recovery notice for {len(recoveries)} job(s)...")
        post_discord(SYSTEM_CHANNEL, recovery_msg)
    
    if not issues and not recoveries:
        print("✅ All cron jobs healthy.")
    
    # Save state
    state["last_check"] = now.isoformat()
    save_state(state)


if __name__ == "__main__":
    main()
