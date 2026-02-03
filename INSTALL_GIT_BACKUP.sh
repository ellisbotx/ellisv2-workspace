#!/bin/bash
# Simple installer for the GitHub daily backup cron job

echo "Installing GitHub backup cron job..."

# Get current crontab
crontab -l 2>/dev/null > /tmp/current_cron_backup.txt

# Add the new job (if not already there)
if grep -q "git_daily_backup.sh" /tmp/current_cron_backup.txt 2>/dev/null; then
    echo "✓ GitHub backup cron job already installed!"
else
    echo "0 4 * * * /Users/ellisbot/.openclaw/workspace/scripts/git_daily_backup.sh >> /Users/ellisbot/.openclaw/workspace/data/logs/cron_git.log 2>&1" >> /tmp/current_cron_backup.txt
    crontab /tmp/current_cron_backup.txt
    echo "✓ GitHub backup cron job installed successfully!"
fi

echo ""
echo "Installed schedule:"
crontab -l | grep -E "dashboard|sellerboard|git_daily"

echo ""
echo "Your workspace will now auto-backup to GitHub every night at 4 AM CST"
echo "Repository: https://github.com/ellisbotx/ellisv2-workspace"
