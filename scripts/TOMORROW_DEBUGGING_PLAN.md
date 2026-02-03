# Tomorrow's Debugging Plan - Sellerboard Download Fix

**Goal:** Get CSV downloads working automatically  
**Current Status:** 90% complete, download mechanism needs fix  
**Target:** Complete by tomorrow afternoon

---

## 🎯 Quick Wins to Try First (30 minutes)

### 1. Run the Form Capture Script
```bash
cd /Users/ellisbot/.openclaw/workspace/scripts
python3 sellerboard_form_capture.py
```

**What it does:**
- Logs into Sellerboard
- Navigates to export page
- Captures ALL network requests when Download is clicked
- Shows form POST data

**What we're looking for:**
- The actual URL that generates the CSV
- POST parameters needed
- Whether it's a direct download or async job

**Time:** 5 minutes

---

### 2. Test Current Implementation
```bash
cd /Users/ellisbot/.openclaw/workspace/scripts
python3 sellerboard_auto_export.py --brand kinfolk
```

**Check:**
- Does Strategy 2 (async handling) complete?
- Does Strategy 3 (Downloads folder monitoring) find the file?
- What's in the latest screenshots?

**Time:** 10 minutes

---

### 3. Manual Browser Test
1. Open browser to Sellerboard
2. Navigate to Dashboard by product export
3. Open DevTools → Network tab
4. Click Download
5. Watch what happens:
   - Immediate download?
   - Modal appears?
   - Takes time to generate?
   - Email sent?

**Time:** 5 minutes

---

## 🔧 Debugging Strategies (in order of likelihood)

### Strategy A: Downloads Folder Monitoring (MOST PROMISING)

**Theory:** The CSV downloads to ~/Downloads/, we just need to detect and move it.

**Current implementation:** Strategy 3 in `sellerboard_auto_export.py`

**Improvements to try:**
1. Use browser download path from Playwright context
2. Monitor for partial files (.crdownload)
3. Wait longer (exports might take 2-3 minutes)
4. Check for filename patterns (might have timestamp)

**Code location:** Line ~580 in sellerboard_auto_export.py

---

### Strategy B: Async Export Handling

**Theory:** Click "Download" → Server generates → Wait for "ready" → Download file

**Current implementation:** Strategy 2

**Improvements to try:**
1. Look for modal with progress indicator
2. Check for button text change ("Download" → "Generating..." → "Download Ready")
3. Poll for new download link in page HTML
4. Check for email notification option (might need to click "Email me")

**Code location:** Line ~530 in sellerboard_auto_export.py

---

### Strategy C: Direct API Request

**Theory:** Bypass the button, call the export API directly

**Steps:**
1. Capture the form POST data (use form_capture.py)
2. Replicate the request with `page.request.post()`
3. Handle the response:
   - If immediate: Save body as CSV
   - If async: Extract job ID, poll for completion

**Example:**
```python
# After capturing the POST data
response = page.request.post(
    "https://app.sellerboard.com/en/export/dashboard-goods",
    data={
        "period_from": "1730707200",
        "period_to": "1738483200",
        # ... other params
    }
)

if response.ok:
    # Check if it's CSV or JSON (job ID)
    content_type = response.headers.get('content-type')
    if 'csv' in content_type:
        output_file.write_bytes(response.body())
    else:
        # Handle async job
        job_data = response.json()
        # Poll for completion...
```

---

### Strategy D: Network Request Interception

**Theory:** Intercept the download response and save it

**Implementation:**
```python
def handle_response(response):
    if 'csv' in response.url or 'export' in response.url:
        if response.ok and 'text/csv' in response.headers.get('content-type', ''):
            output_file.write_bytes(response.body())
            logger.info("✓ Downloaded via response interception")

page.on('response', handle_response)

# Then click download button
page.evaluate('...')

# Wait for response
time.sleep(30)
```

---

## 📊 Decision Tree

```
Click Download Button
    ↓
Does file appear in ~/Downloads within 30s?
    ├─ YES → Strategy 3 works! ✅
    └─ NO → Check page for changes
        ↓
        Does modal appear with "Generating..."?
            ├─ YES → Wait for "Ready" → Try Strategy 2
            └─ NO → Check network tab
                ↓
                See POST request to /export/?
                    ├─ YES → Check response
                    │    ├─ Returns CSV → Strategy 4 (direct request)
                    │    └─ Returns JSON (job_id) → Poll for completion
                    └─ NO → Button might not be working
                        → Try JavaScript .click()
                        → Try form.submit()
                        → Check for errors in console
```

---

## 🧪 Test Cases

### Test 1: Single Brand (Kinfolk)
```bash
python3 sellerboard_auto_export.py --brand kinfolk
```
**Expected:** CSV downloads successfully
**Time:** ~2 minutes

### Test 2: All 3 Brands
```bash
python3 sellerboard_auto_export.py
```
**Expected:** All 3 CSVs download
**Time:** ~6 minutes

### Test 3: Verify File Quality
```bash
# Check file size (should be 4-6 MB)
ls -lh /Users/ellisbot/.openclaw/workspace/data/sellerboard/*.csv

# Check it's valid CSV (should show column headers)
head -3 /Users/ellisbot/.openclaw/workspace/data/sellerboard/kinfolk_dashboard_by_product_90d.csv

# Check row count (should be ~4000-5000 rows)
wc -l /Users/ellisbot/.openclaw/workspace/data/sellerboard/*.csv
```

---

## 📝 Debugging Checklist

- [ ] Run form_capture.py to see network requests
- [ ] Check latest screenshots in screenshots/ folder
- [ ] Review auto_export.log for error messages
- [ ] Manually test download in browser with DevTools open
- [ ] Try Strategy 3 (Downloads folder) with longer wait
- [ ] Try Strategy 2 (async) with better ready detection
- [ ] Try Strategy 4 (direct API) if we have the endpoint
- [ ] Add response interception as fallback
- [ ] Test with all 3 brands
- [ ] Verify CSV files are valid (not HTML)
- [ ] Update documentation with working solution

---

## 🎯 Success Criteria

**Must Have:**
- [ ] All 3 CSVs download successfully
- [ ] Files are valid CSV (not HTML)
- [ ] File sizes correct (4-6 MB each)
- [ ] Row counts reasonable (~4000-5000 each)
- [ ] Process completes in < 10 minutes
- [ ] No manual intervention required

**Nice to Have:**
- [ ] Retry logic for failed downloads
- [ ] File validation checks
- [ ] Email notification on failure
- [ ] Progress logging every 10 seconds

---

## 🚀 Once It Works

### 1. Test End-to-End
```bash
# Full automation test
bash /Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh
```

### 2. Schedule for 2 AM
Already integrated! Just verify it's enabled:
```bash
crontab -l | grep sellerboard
```

### 3. Document the Solution
Update these files:
- `README_SELLERBOARD.md` with working instructions
- `SELLERBOARD_AUTOMATION_STATUS.md` with completion notes
- `sellerboard_auto_export.py` with comments explaining why it works

### 4. Monitor First Automated Run
- Set alert for 2:05 AM to check logs
- Verify 3 CSVs downloaded
- Verify profitability dashboard generated
- Celebrate! 🎉

---

## 💡 Pro Tips

1. **Screenshot Everything:** The screenshots folder is gold for debugging
2. **Log Verbosely:** Better too much info than too little
3. **Test Incrementally:** Get one brand working first
4. **Check File Contents:** Make sure it's CSV, not HTML
5. **Monitor Downloads:** Watch ~/Downloads/ folder in real-time
6. **Time Box It:** If stuck after 1 hour, try different strategy
7. **Ask for Help:** Sellerboard support might explain their export process

---

## 📞 If Still Stuck

**Fallback Options:**

1. **Email Export:** Use "Email me when ready" button, download from email
2. **API Alternative:** Check if Sellerboard has an official API
3. **Scheduled Export:** See if Sellerboard can email CSVs daily automatically
4. **Hybrid Approach:** Keep manual for now, automate other parts

**Remember:** 90% is automated. Last 10% is annoying but solvable!

---

*Created: February 2, 2026, 3:30 PM*  
*Estimated debug time: 30-60 minutes*  
*Confidence: High (multiple strategies available)*
