# Rating Field Fix - Summary

## Problem
Rating yang ditampilkan di halaman Progress untuk produk menunjukkan "N/A" padahal data rating ada di scrapped data.

## Root Cause
Ada **dua field rating** di data Shopee:
- `rating`: Nilai 0, 1, 2 (INTERNAL - bukan untuk display)
- `rating_star`: Nilai 1.0-5.0 (ACTUAL rating bintang yang benar)

API endpoint menggunakan field yang salah:
```python
# WRONG
'rating': product_data.get('rating')  # Returns None or wrong value
```

## Solution
Updated API endpoints untuk menggunakan field yang benar dari `item_rating.rating_star`:

```python
# CORRECT
'rating': product_data.get('item_rating', {}).get('rating_star', 0)
```

## Files Modified

### 1. `service/api.py`
**Line ~1001** - `/history/products` endpoint:
```python
# OLD
'rating': product_data.get('rating'),

# NEW  
'rating': product_data.get('item_rating', {}).get('rating_star', 0),
```

**Line ~1058** - `/product/<product_id>/stats` endpoint:
```python
# OLD
'rating': product_data.get('rating'),

# NEW
'rating': product_data.get('item_rating', {}).get('rating_star', 0),
```

## Data Structure Reference

### product.json structure:
```json
{
  "item_rating": {
    "rating_count": [1050, 16, 3, 21, 81, 929],
    "rating_star": 4.8131553860819825
  }
}
```

### review.json structure (per review):
```json
{
  "rating": 1,           // INTERNAL (0, 1, 2) - DON'T USE FOR DISPLAY
  "rating_star": 5,      // ACTUAL star rating (1-5) - USE THIS
  "comment": "...",
  ...
}
```

## Pipeline Analysis Already Correct

The analysis pipeline was **already using the correct field**:

### `utils/analysis/01-text-ekstraksi.py` (Line 34):
```python
"rating": r.get("rating_star") or r.get("rating") or None,
```

### `utils/pipeline.py` (Line 393):
```python
"rating": r.get("rating_star") or r.get("rating") or None,
```

Both correctly prioritize `rating_star` over `rating`, so CSV files contain correct values (1-5 scale).

## Verification

**Before Fix:**
```
GET /api/history/products
{
  "products": [{
    "rating": null  // ❌ Wrong - returns None
  }]
}
```

**After Fix:**
```
GET /api/history/products  
{
  "products": [{
    "rating": 4.81  // ✅ Correct - actual star rating
  }]
}
```

## Impact

- ✅ Product history cards now show correct rating (e.g., 4.81 ⭐)
- ✅ Product stats API returns accurate rating
- ✅ UI displays proper star ratings instead of "N/A"
- ✅ Analysis pipeline continues to work correctly (was already correct)

## Testing

Run Flask server and check:
1. Visit `/static/progress.html`
2. Check product history cards
3. Verify rating shows as `4.81 ⭐` (not "N/A")
4. Click "View Detail" - rating should be accurate

## Related Documentation
- See `DATA_CONSOLIDATION_FIX.md` for sentiment/trust merge fixes
- See `SCRAP_DATA_REORGANIZATION.md` for directory structure changes
