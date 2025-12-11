# 🧪 Comment Detail Feature - Testing Guide

Panduan testing lengkap untuk feature Comments Detail & Filtering dengan checklist dan skenario testing.

## 📋 Table of Contents
1. [Setup Prerequisites](#setup-prerequisites)
2. [Test Environment Checklist](#test-environment-checklist)
3. [API Endpoint Tests](#api-endpoint-tests)
4. [Frontend UI Tests](#frontend-ui-tests)
5. [Integration Tests](#integration-tests)
6. [Performance Tests](#performance-tests)
7. [Accessibility Tests](#accessibility-tests)
8. [Browser Compatibility](#browser-compatibility)
9. [Troubleshooting](#troubleshooting)

---

## Setup Prerequisites

Sebelum mulai testing, pastikan:

### ✅ Flask Server Running
```bash
cd /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-flask
source venv/bin/activate
python main.py
```

Expected output:
```
 * Running on http://127.0.0.1:5001
 * Debug mode: on
```

### ✅ Test Data Available
```bash
# Check if test products exist
ls -la output/review/
# Should show: 30169103-19027487468/ and 659665623-23043841983/

# Check review.json exists and has data
python3 -c "import json; d=json.load(open('output/review/30169103-19027487468/review.json')); print(f'Comments: {len(d)}')"
# Output: Comments: 1050

# Check tag_statistics.json exists
ls -la output/review/30169103-19027487468/tag_statistics.json
```

### ✅ Browser Ready
- Open Chrome, Firefox, Safari, or Edge
- Clear browser cache (Ctrl+Shift+Delete)
- Open DevTools (F12) for debugging

---

## Test Environment Checklist

### Backend Checks
- [ ] Flask server running on port 5001
- [ ] No Python syntax errors
- [ ] `/api/comments/<id>` endpoint working
- [ ] review.json file exists with valid JSON
- [ ] tag_statistics.json file exists with valid JSON
- [ ] All required fields in comments (username, comment, tags, sentiment)

### Frontend Checks
- [ ] comments-detail.html file exists
- [ ] All CSS styling loads correctly
- [ ] All JavaScript functions defined
- [ ] No console errors on page load
- [ ] Links from progress.html working

### Data Checks
- [ ] At least 2 test products in output/review/
- [ ] Each product has 100+ comments
- [ ] Each product has 10+ unique tags
- [ ] Comments have proper sentiment values
- [ ] Comments have tags array populated

---

## API Endpoint Tests

### Test 1: GET /api/comments/{product_id} - Success Case

**Setup:**
```bash
product_id="30169103-19027487468"
```

**Test Steps:**
1. Open terminal/Postman
2. Make GET request:
```bash
curl -X GET "http://127.0.0.1:5001/api/comments/30169103-19027487468"
```

3. Verify response:

**Expected Response (200):**
```json
{
  "ok": true,
  "comments": [
    {
      "comment": "Barang bagus...",
      "username": "user123",
      "sentiment": "positive",
      "tags": ["kualitas bagus"],
      "timestamp": "2024-12-10T...",
      "rating": 5,
      "trust_score": 0.85,
      "is_fake": false
    },
    ...
  ],
  "tag_stats": {
    "Kualitas Bagus": 133,
    "Pengiriman Buruk": 65,
    ...
  },
  "total": 1050
}
```

**Assertions:**
- ✅ Status code: 200
- ✅ `ok` field: true
- ✅ `comments` is array
- ✅ `comments.length` > 0
- ✅ `tag_stats` is object
- ✅ `total` matches array length
- ✅ Each comment has: comment, username, sentiment, tags, timestamp

**Pass Criteria:**
- Response valid JSON ✓
- All assertions pass ✓
- No errors in Flask logs ✓

---

### Test 2: GET /api/comments/{product_id} - Non-existent Product

**Test Steps:**
1. Make request dengan product ID yang tidak ada:
```bash
curl -X GET "http://127.0.0.1:5001/api/comments/invalid-product-id"
```

2. Verify response:

**Expected Response (404):**
```json
{
  "ok": false,
  "error": "Product not found"
}
```

**Assertions:**
- ✅ Status code: 404
- ✅ `ok` field: false
- ✅ `error` message present

---

### Test 3: GET /api/comments/{product_id} - Empty Product

**Setup:**
Jika ada product dengan 0 comments (unlikely, tapi test edge case):

**Expected Response (200):**
```json
{
  "ok": true,
  "comments": [],
  "tag_stats": {},
  "total": 0
}
```

**Assertions:**
- ✅ Status code: 200
- ✅ `comments` is empty array
- ✅ `tag_stats` is empty object
- ✅ `total`: 0

---

## Frontend UI Tests

### Test 4: Page Load & Initialization

**Test Steps:**
1. Open: `http://127.0.0.1:5001/static/comments-detail.html?product=30169103-19027487468`
2. Wait for page load (should complete in < 2 seconds)
3. Open DevTools Console (F12)
4. Check for errors

**Expected:**
- ✅ Page loads without error
- ✅ No console errors
- ✅ Header shows: "Komentar - 30169103-19027487468"
- ✅ Sidebar with Search, Tag filter, Sentiment filter visible
- ✅ Comments grid populated with cards
- ✅ Result counter shows: "Menampilkan X dari 1050 komentar"

**Pass Criteria:**
- Page fully loaded in < 2 seconds ✓
- No JavaScript errors ✓
- All UI elements visible ✓
- API called successfully ✓

---

### Test 5: Tag Filter - Single Tag Selection

**Test Steps:**
1. Halaman sudah loaded
2. Di sidebar, check "Kualitas Bagus"
3. Observe hasil filtering

**Expected:**
- ✅ Only comments dengan tag "Kualitas Bagus" ditampilkan
- ✅ Result counter updated (misal: "Menampilkan 133 dari 1050")
- ✅ Page re-renders < 100ms
- ✅ All visible comment cards have "Kualitas Bagus" tag

**Verify:**
```javascript
// In DevTools console:
filteredComments.every(c => c.tags && c.tags.includes("Kualitas Bagus"))
// Expected: true
```

---

### Test 6: Tag Filter - Multiple Tags (Logical AND)

**Test Steps:**
1. Halaman default (all tags visible)
2. Check "Kualitas Bagus"
3. Check "Pengiriman Buruk"
4. Observe hasil

**Expected:**
- ✅ Only comments dengan **BOTH** tags ditampilkan
- ✅ Result counter shows smaller number
- ✅ Every card has both tags in tag badges
- ✅ No card dengan hanya salah satu tag

**Verify:**
```javascript
filteredComments.every(c => 
  c.tags && 
  c.tags.includes("Kualitas Bagus") && 
  c.tags.includes("Pengiriman Buruk")
)
// Expected: true
```

---

### Test 7: Sentiment Filter - Exclude Negative

**Test Steps:**
1. Uncheck "Negatif" di Sentiment section
2. Positive dan Neutral tetap checked
3. Observe hasil

**Expected:**
- ✅ Only comments dengan sentiment "positive" atau "neutral" ditampilkan
- ✅ No "negative" sentiment badges visible
- ✅ Result counter updated
- ✅ Filtering done instantly

---

### Test 8: Text Search - Username

**Test Steps:**
1. Di Search Box, ketik username (misal: "budi")
2. Wait untuk real-time filter
3. Observe hasil

**Expected:**
- ✅ Only comments dengan username containing "budi" ditampilkan
- ✅ Case-insensitive (search "BUDI" same as "budi")
- ✅ Filtering instant as you type
- ✅ Result counter updated

---

### Test 9: Text Search - Comment Text

**Test Steps:**
1. Clear previous search
2. Di Search Box, ketik kata dari comment (misal: "lambat")
3. Observe hasil

**Expected:**
- ✅ Only comments containing "lambat" ditampilkan
- ✅ Works in both comment text dan username
- ✅ Case-insensitive
- ✅ Real-time filtering

---

### Test 10: Select All / Deselect All Tags

**Test Steps - Select All:**
1. Klik button "Pilih Semua" di Tag section
2. Observe checkbox states

**Expected:**
- ✅ Semua tag checkboxes menjadi checked ✓
- ✅ All tags active di filter
- ✅ Comments grid shows hasil dengan semua tag combinations

**Test Steps - Deselect All:**
1. Klik button "Hapus Semua" di Tag section

**Expected:**
- ✅ Semua tag checkboxes menjadi unchecked ☐
- ✅ Result counter shows: "Menampilkan 0 dari 1050"
- ✅ Comments grid shows empty state message
- ✅ Message: "Tidak ada komentar yang sesuai"

---

### Test 11: Tag Badge Click (Quick Filter)

**Test Steps:**
1. Scroll ke komentar card dengan multiple tags
2. Click salah satu tag badge (blue pill)
3. Observe filter change

**Expected:**
- ✅ Checkbox untuk tag itu toggle (checked → unchecked atau sebaliknya)
- ✅ Comments grid filter instant
- ✅ Result counter updated
- ✅ Tag badge visual change (highlight/dimmed)

---

### Test 12: Pagination Navigation

**Test Steps:**
1. Default view (page 1)
2. Scroll ke bottom untuk lihat pagination buttons
3. Click tombol next (atau page 2)
4. Observe page change

**Expected:**
- ✅ Comments grid update dengan komentar page berikutnya
- ✅ Page number button highlight berubah
- ✅ Auto-scroll to top of page
- ✅ Prev button enabled (jika page > 1)
- ✅ Next button disabled (jika page = last page)

**Verify:**
```javascript
// Komentar di page 2 harus berbeda dari page 1
filteredComments.slice(10, 20) // page 2 items
```

---

### Test 13: Back Button

**Test Steps:**
1. Di header, klik button "← Kembali"
2. Observe navigation

**Expected:**
- ✅ Browser history pop (back to previous page)
- ✅ Should go back to progress page atau referring page
- ✅ No data loss

---

### Test 14: Responsive Design - Desktop

**Test Steps:**
1. Open halaman di desktop (1920x1080)
2. Check layout

**Expected:**
- ✅ Sidebar left (300px fixed width)
- ✅ Main content right (flexible)
- ✅ 2-column layout
- ✅ Sidebar sticky saat scroll
- ✅ All elements visible tanpa horizontal scroll

---

### Test 15: Responsive Design - Tablet

**Test Steps:**
1. Resize browser ke tablet width (768px)
2. Check layout

**Expected:**
- ✅ Layout stack vertical (sidebar above, main below)
- ✅ Sidebar full width
- ✅ No horizontal scroll
- ✅ All buttons clickable
- ✅ Text readable tanpa zoom

---

### Test 16: Responsive Design - Mobile

**Test Steps:**
1. Resize browser ke mobile (375px)
2. Check layout

**Expected:**
- ✅ Fully functional layout
- ✅ Touch-friendly button sizes (min 44x44px)
- ✅ Text readable tanpa zoom
- ✅ Scrollable without issues

---

## Integration Tests

### Test 17: Flow - Complete Filter Scenario

**Scenario:** "Find all comments about delivery problems that are negative sentiment"

**Steps:**
1. Open `/static/comments-detail.html?product=30169103-19027487468`
2. Wait untuk page load
3. In sidebar, check "Pengiriman Buruk" tag
4. Uncheck "Positif" dan "Netral", leave "Negatif" checked
5. Scroll dan verifikasi hasil

**Expected:**
- ✅ Only comments dengan tag "Pengiriman Buruk" AND sentiment "negative"
- ✅ Result counter shows smaller subset
- ✅ All visible comments match criteria
- ✅ No false positives

---

### Test 18: Flow - Search + Filter Combination

**Scenario:** "Find comments from user 'budi' about delivery"

**Steps:**
1. Page loaded
2. In Search Box, type "budi"
3. In tag filter, check "Pengiriman Buruk"
4. Verify results

**Expected:**
- ✅ Only comments dari username containing "budi" 
- ✅ AND dengan tag "Pengiriman Buruk"
- ✅ Other filters (sentiment) tetap applied

---

### Test 19: Link from Progress Page

**Scenario:** Navigate from progress page ke comments detail

**Steps:**
1. Open `http://127.0.0.1:5001/progress`
2. Scroll ke "Histori Produk" section
3. Find a product card
4. Click "💬 View Comments" button
5. Verify navigation

**Expected:**
- ✅ Navigates to `/static/comments-detail.html?product={id}`
- ✅ Correct product_id passed in URL
- ✅ Page loads dengan data untuk product itu
- ✅ Header shows correct product_id

---

### Test 20: Link Back to Progress Page

**Scenario:** Go back dari comments detail ke progress

**Steps:**
1. On comments detail page
2. Click "← Kembali" button
3. Verify navigation

**Expected:**
- ✅ Goes back to progress page (atau referrer)
- ✅ Progress page still functional
- ✅ History section still shows

---

## Performance Tests

### Test 21: Page Load Time - Small Product (< 100 comments)

**Setup:**
```bash
# Create test product dengan few comments
```

**Steps:**
1. Open comments-detail page
2. Time dari navigation sampai fully rendered
3. Use DevTools Network tab untuk measure

**Expected:**
- ✅ Initial HTML: < 50ms
- ✅ CSS loaded: < 100ms
- ✅ JavaScript executed: < 200ms
- ✅ API call: < 500ms
- ✅ Total page load: < 2 seconds

---

### Test 22: Page Load Time - Large Product (> 1000 comments)

**Setup:**
Use product `30169103-19027487468` dengan 1050 comments

**Steps:**
1. Open comments-detail page
2. Measure load time

**Expected:**
- ✅ API response: < 1 second
- ✅ DOM rendering: < 500ms
- ✅ Total: < 2 seconds

**Performance Benchmark:**
- Small (< 100): ~500ms
- Medium (100-1000): ~1s
- Large (1000+): ~2s

---

### Test 23: Filter Application Speed

**Steps:**
1. Page loaded
2. Click checkbox untuk filter tag
3. Measure time sampai hasil filter muncul

**Expected:**
- ✅ < 100ms untuk update view
- ✅ No lag atau freeze
- ✅ Smooth filtering

---

### Test 24: Search Response Time

**Steps:**
1. Di search box, type "lambat"
2. Measure response time

**Expected:**
- ✅ Real-time filter (< 50ms per character)
- ✅ No lag saat typing
- ✅ Results update smooth

---

### Test 25: Pagination Speed

**Steps:**
1. Click page 5
2. Measure time sampai page 5 rendered

**Expected:**
- ✅ Instant (< 50ms)
- ✅ No API call needed
- ✅ Smooth navigation

---

## Accessibility Tests

### Test 26: Keyboard Navigation

**Steps:**
1. Open halaman
2. Press Tab untuk navigate elements
3. Verify semua interactive elements accessible

**Expected:**
- ✅ All buttons accessible via Tab
- ✅ Checkbox inputs focusable
- ✅ Text input focusable
- ✅ Enter key works di buttons
- ✅ Space key toggles checkboxes

---

### Test 27: Color Contrast

**Steps:**
1. Use browser color picker
2. Check text contrast ratios
3. Verify meets WCAG standards

**Expected:**
- ✅ Text on background: > 4.5:1 ratio
- ✅ Button labels: > 4.5:1 ratio
- ✅ Badge text: > 3:1 ratio
- ✅ All text readable for color-blind users

---

### Test 28: Screen Reader Compatibility

**Setup:**
Use browser built-in accessibility checker atau screen reader

**Steps:**
1. Enable screen reader
2. Navigate page using reader commands
3. Verify page structure read correctly

**Expected:**
- ✅ Headings read correctly (H1, H2, H3)
- ✅ Button labels read correctly
- ✅ Form labels associated with inputs
- ✅ Images have alt text (jika ada)
- ✅ Page structure logical

---

## Browser Compatibility

### Test 29: Chrome Latest

**Steps:**
1. Open halaman di Chrome latest version
2. Check functionality

**Expected:**
- ✅ All features working
- ✅ Styling correct
- ✅ No console errors
- ✅ Responsive design working

---

### Test 30: Firefox Latest

**Expected:**
- ✅ All features working
- ✅ CSS animations smooth
- ✅ No compatibility issues

---

### Test 31: Safari Latest

**Expected:**
- ✅ All features working
- ✅ Webkit-specific fixes applied
- ✅ No layout issues

---

### Test 32: Edge Latest

**Expected:**
- ✅ All features working
- ✅ Chromium-based, should match Chrome

---

## Troubleshooting

### Issue: API Returns 404 "Product not found"

**Diagnosis:**
```bash
ls output/review/
# Check jika product folder ada
```

**Fix:**
1. Verify product_id correct di URL
2. Check folder exists di output/review/
3. Run Re-Analyze untuk regenerate data

---

### Issue: Tags tidak tampil di filter sidebar

**Diagnosis:**
```bash
ls output/review/{product_id}/tag_statistics.json
# Check jika file ada
```

**Fix:**
1. File harus ada
2. Run Re-Analyze untuk regenerate
3. Refresh halaman

---

### Issue: Comments tidak muncul

**Diagnosis:**
1. Check API response di DevTools Network tab
2. Check review.json structure

**Fix:**
1. Ensure review.json valid JSON
2. Ensure comments array populated
3. Check sentiment field exists

---

### Issue: Filter tidak work

**Diagnosis:**
Open DevTools Console:
```javascript
console.log(allComments)
console.log(filteredComments)
console.log(getSelectedFilters())
```

**Fix:**
1. Verify data loaded correctly
2. Check event listeners attached
3. Hard refresh page (Ctrl+Shift+F5)

---

### Issue: Pagination broken

**Diagnosis:**
```javascript
// In console:
console.log(`Total: ${filteredComments.length}, Pages: ${Math.ceil(filteredComments.length / ITEMS_PER_PAGE)}`)
```

**Fix:**
1. Ensure ITEMS_PER_PAGE = 10
2. Verify pagination function
3. Refresh page

---

## Test Completion Checklist

Sebelum declare feature "Ready for Production":

### API Tests
- [ ] Test 1-3: All endpoint variations pass
- [ ] Response formats correct
- [ ] Error handling proper

### Frontend Tests
- [ ] Test 4-16: All UI tests pass
- [ ] Page loads without error
- [ ] All filters work correctly
- [ ] Pagination working
- [ ] Responsive design passes

### Integration Tests
- [ ] Test 17-20: Flow tests pass
- [ ] Navigation working
- [ ] Data consistency maintained

### Performance Tests
- [ ] Test 21-25: Load times acceptable
- [ ] Filtering responsive
- [ ] No performance regressions

### Accessibility Tests
- [ ] Test 26-28: Accessibility standards met
- [ ] Keyboard navigation working
- [ ] Screen reader compatible

### Browser Tests
- [ ] Test 29-32: All major browsers pass
- [ ] Consistent experience across browsers

---

## Sign-Off

**Tested By:** [Your Name]
**Date:** [Date]
**Status:** ☐ Pass ☐ Fail
**Notes:** [Any issues found]

---

**Last Updated:** December 11, 2024
**Version:** 1.0
