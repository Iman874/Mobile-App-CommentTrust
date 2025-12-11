# ✅ Testing Checklist - Comments Detail & Full Pipeline

Quick checklist untuk melakukan testing fitur yang baru dibuat.

## 🚀 Prerequisite Setup

- [ ] Flask server running: `cd backend/app-backend-flask && python main.py`
- [ ] Server listening on: http://127.0.0.1:5001
- [ ] Test product exists: 30169103-19027487468
- [ ] review.json has 1050+ comments
- [ ] tag_statistics.json exists
- [ ] Browser ready (Chrome/Firefox/Safari)

---

## 📱 Test 1: Access Comments Detail Page

**Steps:**
1. [ ] Open Progress page: http://127.0.0.1:5001/progress
2. [ ] Scroll ke section "Histori Produk"
3. [ ] Find product "30169103-19027487468"
4. [ ] Click button "💬 View Comments"

**Expected:**
- [ ] Page loads in < 2 seconds
- [ ] Header shows: "Komentar - 30169103-19027487468"
- [ ] Sidebar visible dengan Search, Tag filters, Sentiment filters
- [ ] Comment cards displayed (10 per page)
- [ ] No console errors (F12)

---

## 🏷️ Test 2: Single Tag Filter

**Steps:**
1. [ ] Page sudah loaded
2. [ ] Di sidebar, check checkbox "Kualitas Bagus"
3. [ ] Observe hasil

**Expected:**
- [ ] Result counter shows: "Menampilkan 133 dari 1050"
- [ ] All visible comments have "Kualitas Bagus" tag
- [ ] Instant filtering (< 100ms)

---

## 🏷️🏷️ Test 3: Multiple Tag Filter (Logical AND)

**Steps:**
1. [ ] Check "Kualitas Bagus"
2. [ ] Check "Pengiriman Buruk"
3. [ ] Observe hasil

**Expected:**
- [ ] Result counter shows smaller number (< 20)
- [ ] ALL visible comments have **BOTH** tags
- [ ] No cards with just one tag

---

## 😊 Test 4: Sentiment Filter

**Steps:**
1. [ ] Uncheck "Negatif" di Sentiment section
2. [ ] Keep "Positif" dan "Netral" checked
3. [ ] Observe hasil

**Expected:**
- [ ] Only positive/neutral sentiment badges visible
- [ ] No red (negative) badges
- [ ] Result count updated

---

## 🔍 Test 5: Text Search

**Steps:**
1. [ ] Clear all tag filters (click "Hapus Semua")
2. [ ] Di Search Box, type "barang"
3. [ ] Observe hasil real-time

**Expected:**
- [ ] Results instant as you type
- [ ] Only comments containing "barang" shown
- [ ] Case-insensitive (test "BARANG" too)

---

## 🚀 Test 6: Quick Tag Toggle

**Steps:**
1. [ ] Find any comment card
2. [ ] Click one of the tag badges (blue pill)
3. [ ] Observe filter change

**Expected:**
- [ ] Corresponding checkbox toggle in sidebar
- [ ] Results updated instantly
- [ ] Only comments with that tag shown

---

## ⚡ Test 7: Bulk Select/Deselect

**Steps A - Select All:**
1. [ ] Click "Pilih Semua" button di Tag section
2. [ ] Observe checkboxes

**Expected:**
- [ ] All tag checkboxes become checked ✓
- [ ] Result shows all comments

**Steps B - Deselect All:**
1. [ ] Click "Hapus Semua" button
2. [ ] Observe checkboxes

**Expected:**
- [ ] All tag checkboxes become unchecked ☐
- [ ] Result shows: "Menampilkan 0 dari 1050"
- [ ] Empty state message displayed

---

## 📄 Test 8: Pagination

**Steps:**
1. [ ] At bottom of page, find pagination buttons
2. [ ] Current page should be [1]
3. [ ] Click page [2]
4. [ ] Scroll to top (should auto-scroll)

**Expected:**
- [ ] Page 2 comments loaded (different 10 comments)
- [ ] Page button [2] highlighted
- [ ] Prev button enabled, Next button enabled
- [ ] < 50ms load time

---

## 📊 Test 9: Verify API Endpoint

**Steps:**
```bash
# In terminal
curl "http://127.0.0.1:5001/api/comments/30169103-19027487468" | python3 -m json.tool | head -100
```

**Expected:**
- [ ] Returns valid JSON
- [ ] `"ok": true`
- [ ] `"comments"` array with 1050 items
- [ ] `"tag_stats"` object with tag counts
- [ ] Each comment has `"tags"` field
- [ ] Status code 200

---

## 🔄 Test 10: Re-analyze Endpoint

**Steps:**
```bash
# Start request
curl -X POST "http://127.0.0.1:5001/api/reanalyze/30169103-19027487468"

# Response should be:
# {"ok": true, "job_id": "abc12345"}
```

**Expected:**
- [ ] Returns JSON with job_id
- [ ] Status code 200

---

## 👀 Test 11: Monitor Re-analyze Progress

**Steps:**
1. [ ] Open Progress page: http://127.0.0.1:5001/progress
2. [ ] Watch the jobs table
3. [ ] Look for job with analysis_progress changing

**Expected:**
- [ ] Job appear dalam "Job Queue"
- [ ] Progress goes: 0% → 20% → 40% → 70% → 90% → 100%
- [ ] Step names update:
  - [ ] "Cleaning old analysis files"
  - [ ] "Running full analysis pipeline"
  - [ ] "Extracting and applying comment tags"
  - [ ] "Full re-analysis completed successfully"

---

## 📁 Test 12: Verify Analysis Files Recreated

**Steps:**
1. [ ] Before re-analyze, check:
   ```bash
   ls -la output/comment/30169103-19027487468/indobert/
   ```

2. [ ] Click Re-Analyze button

3. [ ] During re-analyze, folder should be deleted (~ step 1)

4. [ ] After complete, check again:
   ```bash
   ls -la output/comment/30169103-19027487468/indobert/
   ```

**Expected:**
- [ ] After completion, folder recreated with fresh files:
  - [ ] review_clean.csv (fresh)
  - [ ] review_tokens.csv (fresh)
  - [ ] review_sentiment.csv (fresh)
  - [ ] review_fake.csv (fresh)
  - [ ] review_trust.csv (fresh)
  - [ ] review_tagged.csv (fresh)

---

## 🏷️ Test 13: Verify Tags Updated After Re-analyze

**Steps:**
1. [ ] Before re-analyze, check tags:
   ```bash
   python3 -c "import json; d=json.load(open('output/review/30169103-19027487468/review.json')); print(f'Sample tags: {d[0][\"tags\"]}')"
   ```

2. [ ] Run Re-Analyze

3. [ ] Check tags again:
   ```bash
   python3 -c "import json; d=json.load(open('output/review/30169103-19027487468/review.json')); print(f'Sample tags: {d[0][\"tags\"]}')"
   ```

**Expected:**
- [ ] Tags present in review.json
- [ ] Same structure before/after (but possibly different assignments)
- [ ] tag_statistics.json updated

---

## 📱 Test 14: Responsive Design (Mobile)

**Steps:**
1. [ ] Open DevTools (F12)
2. [ ] Toggle device toolbar (Ctrl+Shift+M)
3. [ ] Select "iPhone 12" or "iPad"
4. [ ] Test filtering, search, pagination

**Expected:**
- [ ] Layout responsive (sidebar above, content below)
- [ ] All buttons accessible
- [ ] Text readable without zoom
- [ ] No horizontal scroll

---

## 🎨 Test 15: UI Styling

**Steps:**
1. [ ] Check colors of sentiment badges:
   - [ ] Positive: Green ✅
   - [ ] Neutral: Orange ⚪
   - [ ] Negative: Red ❌

2. [ ] Check tag badges:
   - [ ] Blue color, clickable

3. [ ] Check card hover:
   - [ ] Shadow increases
   - [ ] Slight lift animation

**Expected:**
- [ ] All colors match spec
- [ ] Hover effects smooth
- [ ] No visual glitches

---

## 🔐 Test 16: Error Handling

**Steps A - Invalid Product ID:**
1. [ ] Navigate to:
   ```
   http://127.0.0.1:5001/static/comments-detail.html?product=invalid-product-id
   ```

**Expected:**
- [ ] Error message displayed
- [ ] No console errors
- [ ] Graceful error handling

**Steps B - Missing Comments:**
1. [ ] For product with 0 comments, should show:
   - [ ] "Tidak ada komentar yang sesuai" message
   - [ ] Empty state UI

**Expected:**
- [ ] Proper empty state message
- [ ] No crashes

---

## ⏱️ Test 17: Performance Baseline

**Steps:**
1. [ ] Open DevTools → Network tab
2. [ ] Hard refresh (Ctrl+Shift+F5)
3. [ ] Note load times:
   - [ ] HTML load: ___ms
   - [ ] CSS load: ___ms
   - [ ] JS load: ___ms
   - [ ] API call: ___ms
   - [ ] **Total: ___ms**

**Expected:**
- [ ] HTML: < 50ms
- [ ] CSS: < 100ms
- [ ] JS: < 200ms
- [ ] API: < 500ms
- [ ] **Total: < 2s**

---

## 📊 Test 18: Comments Count Validation

**Steps:**
```bash
# Check total comments
python3 -c "import json; d=json.load(open('output/review/30169103-19027487468/review.json')); print(f'Total: {len(d)}')"

# Check comments with tags
python3 -c "import json; d=json.load(open('output/review/30169103-19027487468/review.json')); tagged = [c for c in d if c.get('tags')]; print(f'With tags: {len(tagged)}')"
```

**Expected:**
- [ ] Total count matches API response
- [ ] Tag percentage: 20-30% (most comments get tags)
- [ ] At least 10 unique tags

---

## 🎯 Test 19: End-to-End Workflow

**Steps:**
1. [ ] Start from fresh
2. [ ] Navigate to Progress page
3. [ ] Click "View Comments" on product
4. [ ] Apply filter (tag + sentiment)
5. [ ] Search for keyword
6. [ ] Click tag badge (quick filter)
7. [ ] Navigate through pagination
8. [ ] Go back to Progress page (Back button)
9. [ ] Click "Re-Analyze"
10. [ ] Wait for completion
11. [ ] Navigate to comments again
12. [ ] Verify fresh data loaded

**Expected:**
- [ ] All steps work smoothly
- [ ] No errors at any point
- [ ] Data refreshed after re-analyze
- [ ] Seamless navigation

---

## ✅ Final Verification

### Backend
- [ ] Python syntax OK: `python3 -m py_compile service/api.py`
- [ ] Python syntax OK: `python3 -m py_compile utils/pipeline.py`
- [ ] Flask runs without error
- [ ] No Python exceptions in logs

### Frontend
- [ ] No console errors (F12)
- [ ] No CSS styling issues
- [ ] All buttons functional
- [ ] Responsive on all screen sizes

### Data
- [ ] Comments load correctly
- [ ] Tags extracted properly
- [ ] Statistics calculated
- [ ] API response valid JSON

### Performance
- [ ] Page load < 2s
- [ ] Filtering < 100ms
- [ ] No UI freezes
- [ ] Memory usage reasonable

---

## 📋 Sign-Off

**Tester Name:** ___________________
**Date:** ___________________
**Status:** 
- [ ] ✅ All tests passed
- [ ] ⚠️ Some issues found (list below)
- [ ] ❌ Critical issues

**Issues Found:**
1. ___________________________________
2. ___________________________________
3. ___________________________________

**Notes:**
________________________________
________________________________
________________________________

---

**Happy Testing! 🎉**

If any issue found, please check:
1. Flask server running
2. Browser console (F12) for errors
3. Backend logs: `tail -f log/process*.log`
4. Network tab for API responses
5. Refer to troubleshooting guides in documentation

---

**Last Updated:** December 11, 2024
