#!/bin/bash
# Simple one-command installer for the 3 AM dashboard cron job

echo "Installing Trifecta Dashboard cron job..."

# Get current crontab
crontab -l 2>/dev/null > /tmp/current_cron_backup.txt

# Add the new job (if not already there)
if grep -q "dashboard_daily.sh" /tmp/current_cron_backup.txt 2>/dev/null; then
    echo "✓ Cron job already installed!"
else
    echo "0 3 * * * /Users/ellisbot/.openclaw/workspace/scripts/dashboard_daily.sh >> /Users/ellisbot/.openclaw/workspace/data/logs/cron_dashboard.log 2>&1" >> /tmp/current_cron_backup.txt
    crontab /tmp/current_cron_backup.txt
    echo "✓ Cron job installed successfully!"
fi

echo ""
echo "Installed jobs:"
crontab -l | grep dashboard

echo ""
echo "Dashboard will auto-update every night at 3 AM CST"
