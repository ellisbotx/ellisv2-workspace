# GitHub Auto-Backup Setup

Your workspace is configured to automatically backup to GitHub every night at 4 AM CST.

**Repository:** https://github.com/ellisbotx/ellisv2-workspace

---

## One-Time Setup (Authentication)

Before the automated backups can push to GitHub, you need to authenticate once:

### Step 1: Create a GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: "Ellis Workspace Backup"
4. Select scopes: **✓ repo** (all repo permissions)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### Step 2: Authenticate Git

Run these commands in Terminal:

```bash
cd /Users/ellisbot/.openclaw/workspace
git push origin main
```

When prompted for credentials:
- **Username:** ellisbotx
- **Password:** [paste your Personal Access Token]

macOS will save these credentials in Keychain - you won't need to enter them again!

### Step 3: Install the Cron Job

Run:
```bash
bash /Users/ellisbot/.openclaw/workspace/INSTALL_GIT_BACKUP.sh
```

---

## What Gets Backed Up?

Every night at 4 AM, after dashboards update, these files automatically commit and push:

- All dashboard files (trifecta/*.html)
- All scripts (scripts/*.py, scripts/*.sh)
- All data files (data/*.json, data/*.csv)
- Memory files (memory/*.md, MEMORY.md)
- Configuration files (credentials, settings)

**Commit message format:** `Auto-backup: 2026-02-02 19:45 CST`

---

## Schedule

- **2:00 AM** - Sellerboard processing
- **3:00 AM** - Dashboard updates
- **4:00 AM** - GitHub backup ← NEW!

---

## Checking Backups

View your backups at: https://github.com/ellisbotx/ellisv2-workspace/commits

Each night's changes will show up as a new commit.

---

## Troubleshooting

**If backups aren't pushing:**

1. Check the log:
   ```bash
   tail -50 /Users/ellisbot/.openclaw/workspace/data/logs/git_backup.log
   ```

2. Test manually:
   ```bash
   cd /Users/ellisbot/.openclaw/workspace
   git push origin main
   ```

3. Re-authenticate if needed (your token may have expired)
