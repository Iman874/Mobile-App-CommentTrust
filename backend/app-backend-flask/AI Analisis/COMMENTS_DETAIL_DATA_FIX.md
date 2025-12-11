# Comments Detail Page - Data Display Fix

## Problems Fixed

### 1. Rating Display Issue
**Problem:** Rating menampilkan nilai 0 atau 1 (salah) padahal seharusnya 1-5
**Root Cause:** Frontend menggunakan field `rating` (internal 0-2) bukan `rating_star` (actual 1-5)

**Fix:**
```javascript
// BEFORE (Wrong)
const rating = comment.rating || comment.detailed_rating?.product_quality || 0;

// AFTER (Correct) 
const rating = comment.rating_star || comment.rating || comment.detailed_rating?.product_quality || 0;
```

### 2. Trust Score Display Issue  
**Problem:** Trust score ditampilkan sebagai 8000% - 9800% (salah)
**Root Cause:** Frontend mengalikan trust_score dengan 100, padahal data sudah dalam skala 0-100

**Fix:**
```javascript
// BEFORE (Wrong - multiply by 100)
📊 Trust: ${(comment.trust_score * 100).toFixed(0)}%

// AFTER (Correct - display as-is)
📊 Trust: ${comment.trust_score.toFixed(1)}%
```

## Data Verification

### Actual Data in review.json:
```json
{
  "rating": 1,           // ❌ Internal (0-2) - DON'T USE
  "rating_star": 5,      // ✅ Correct (1-5) - USE THIS
  "trust_score": 96.89,  // ✅ Already 0-100 scale
  "sentiment": "positive",
  "is_fake": false
}
```

### Display Results:

**Before Fix:**
- Rating: 1/5 ⭐ (WRONG - should be 5)
- Trust: 9689% 📊 (WRONG - should be 96.9%)

**After Fix:**
- Rating: 5/5 ⭐ (CORRECT)
- Trust: 96.9% 📊 (CORRECT)

## Files Modified

### `static/comments-detail.html`

**Line ~648** - Rating field priority:
```javascript
// Prioritize rating_star over rating
const rating = comment.rating_star || comment.rating || comment.detailed_rating?.product_quality || 0;
```

**Line ~677** - Trust score display:
```javascript
// Display trust_score as-is (already 0-100), don't multiply
${comment.trust_score !== undefined ? `<div class="score-item">📊 Trust: ${comment.trust_score.toFixed(1)}%</div>` : ''}
```

**Line ~674** - Score section visibility:
```javascript
// Show score section if ANY field exists (not just rating)
${(rating > 0 || comment.trust_score !== undefined || comment.is_fake !== undefined) ? `
```

## Testing Verification

Run test to verify data:
```bash
cd backend/app-backend-flask
python3 << 'EOF'
import json
with open('output/scrap-data/30169103-19027487468/review.json', 'r') as f:
    reviews = json.load(f)
    r = reviews[0]
    print(f"Rating: {r.get('rating')} vs rating_star: {r.get('rating_star')}")
    print(f"Trust: {r.get('trust_score')}")
EOF
```

Expected output:
```
Rating: 1 vs rating_star: 5
Trust: 96.89
```

## Impact

✅ Rating now displays correct 1-5 star values
✅ Trust score displays in proper 0-100% range
✅ All comment cards show accurate metrics
✅ User sees meaningful data instead of confusing values

## Related Fixes
- See `RATING_FIELD_FIX.md` for API endpoint rating fixes
- See `DATA_CONSOLIDATION_FIX.md` for sentiment merge fixes
