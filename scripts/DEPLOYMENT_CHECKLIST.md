# Deployment Checklist - Sellerboard Automation

## Pre-Deployment (Tonight, after Board Meeting)

### 1. Apply Date Picker Fix ⏱️ 15 min
- [ ] Update `sellerboard_auto_export_final.py` with visual date picker code
- [ ] Replace JavaScript date manipulation with UI clicks
- [ ] Test date range sets correctly (verify screenshot shows 90-day range)

### 2. End-to-End Testing ⏱️ 30 min  
- [ ] Test Black Owned brand download
- [ ] Test CardPlug brand download
- [ ] Test Kinfolk brand download
- [ ] Verify all 3 CSV files are 500KB-6MB (not tiny files)
- [ ] Verify sku_velocity.json processes correctly

### 3. Update Cron Job ⏱️ 10 min
- [ ] Edit `/Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh`
- [ ] Replace processing-only command with full automation:
  ```bash
  # OLD (just processing):
  # python3 sellerboard_export.py --process
  
  # NEW (full automation):
  python3 sellerboard_auto_export_final.py --headless
  ```
- [ ] Test cron wrapper runs manually
- [ ] Check crontab is set for 2 AM CST: `0 2 * * * /path/to/sellerboard_daily.sh`

### 4. Backup Plan ⏱️ 5 min
- [ ] Keep existing CSVs as backup (don't delete old ones initially)
- [ ] Set up fallback notification if script fails
- [ ] Document manual download procedure (in case automation fails)

---

## Deployment Night (Feb 2, 2026 - Tonight)

### Final Checks (11:30 PM)
- [ ] 1Password is authenticated (`op signin`)
- [ ] Playwright is installed (`playwright install chromium`)
- [ ] Log file permissions are correct
- [ ] No other processes using browser/Sellerboard

### Post-Run Checks (2:05 AM - or next morning)
- [ ] Check log: `/Users/ellisbot/.openclaw/workspace/data/sellerboard/auto_export.log`
- [ ] Verify 3 CSV files downloaded with correct timestamps
- [ ] Verify sku_velocity.json updated
- [ ] Check profitability dashboard generated

---

## Success Criteria

✅ **All 3 brands downloaded automatically**
✅ **CSV files are 500KB-6MB each (not tiny)**
✅ **sku_velocity.json updated successfully**
✅ **No manual intervention needed**
✅ **Marco wakes up to fresh data**

---

## Rollback Plan

If automation fails at 2 AM:

1. **Immediate:** Old CSVs still exist from previous run
2. **Morning:** Marco manually downloads missing CSVs
3. **Next day:** Debug and fix before next 2 AM run

---

## Monitoring

### Log Locations
- Main log: `/Users/ellisbot/.openclaw/workspace/data/sellerboard/auto_export.log`
- Cron log: `/Users/ellisbot/.openclaw/workspace/data/sellerboard/daily_processing.log`
- Screenshots: `/Users/ellisbot/.openclaw/workspace/data/sellerboard/screenshots/`

### Alert Triggers
- If CSV files are <100KB → Something wrong
- If script runs >10 minutes → Hung/timeout
- If any brand fails 3x → Skip and alert

---

**Last Updated:** 2026-02-02 15:42 - Code Agent
