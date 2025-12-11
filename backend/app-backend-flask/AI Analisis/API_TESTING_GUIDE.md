# API Testing Guide - Analysis Endpoints

## Quick Start

All endpoints are available at `http://localhost:5000/api/`

## Endpoint Summary

| Endpoint | Method | Purpose | Mode |
|----------|--------|---------|------|
| `/analyze/full` | POST | Scrape + Analyze | Full workflow |
| `/analyze/scrape` | POST | Scrape only | Data collection |
| `/analyze/reanalyze` | POST | Analyze existing | Re-analysis |
| `/force/<product_id>` | POST | Force scrape | (deprecated, use /analyze/full) |
| `/force/analysis/<product_id>` | POST | Force analysis | (deprecated, use /analyze/reanalyze) |

## Test Examples

### 1. Full Analysis (Scrape + Analyze)

**cURL:**
```bash
curl -X POST http://localhost:5000/api/analyze/full \
  -H "Content-Type: application/json" \
  -d '{
    "link": "https://shopee.co.id/product/30169103-19027487468"
  }'
```

**Response:**
```json
{
  "ok": true,
  "job_id": "a1b2c3d4e5f6"
}
```

**Timeline:**
1. Scrape starts (5-10 minutes depending on comment count)
2. Analysis pipeline starts (~5 minutes for 1000+ comments)
3. Results merged to `output/scrap-data/{product_id}/review.json`
4. Check job status: `GET /api/status/{job_id}`

### 2. Scrape Only (Fast Data Collection)

**cURL:**
```bash
curl -X POST http://localhost:5000/api/analyze/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "link": "https://shopee.co.id/product/30169103-19027487468"
  }'
```

**Response:**
```json
{
  "ok": true,
  "job_id": "x1y2z3a4b5c6",
  "message": "Scrape-only job started"
}
```

**Timeline:**
1. Scrape starts (5-10 minutes)
2. Data saved to `output/scrap-data/{product_id}/`
3. Done - no analysis pipeline runs
4. Can be followed up with `/analyze/reanalyze`

**Use Cases:**
- Batch data collection for multiple products
- Quick snapshot of comments
- Defer expensive analysis to later

### 3. Re-analyze Existing Data

**cURL:**
```bash
curl -X POST http://localhost:5000/api/analyze/reanalyze \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "30169103-19027487468"
  }'
```

**Response:**
```json
{
  "ok": true,
  "job_id": "p1q2r3s4t5u6",
  "message": "Re-analyze job started"
}
```

**Timeline:**
1. Old analysis results deleted
2. Fresh pipeline runs (~5 minutes for 1000+ comments)
3. New sentiment/trust/fake detection generated
4. Results merged to `output/scrap-data/{product_id}/review.json`

**Use Cases:**
- Refine analysis with improved models
- Re-run with different backend (auto vs indobert)
- Update analysis after code changes
- Generate new tags with improved tagger

## Job Monitoring

### Get Job Status

**cURL:**
```bash
curl http://localhost:5000/api/status/{job_id}
```

**Response:**
```json
{
  "phase": "analysis",
  "scraper_progress": 100,
  "scraper_total": 1050,
  "analysis_progress": 45,
  "analysis_step_index": 3,
  "analysis_step_name": "[03] sentiment",
  "error": null
}
```

**Phases:**
- `queued` - Waiting to start
- `scraper` - Scraping product/comments
- `analysis` - Running analysis pipeline
- `done` - Complete
- `error` - Failed

### Get Jobs List

**cURL:**
```bash
curl http://localhost:5000/api/jobs
```

**Response:**
```json
{
  "jobs": [
    {
      "id": "abc123",
      "product_id": "30169103-19027487468",
      "phase": "done",
      "created_at": "2025-12-11T10:30:45.123456"
    }
  ]
}
```

## Output Data

### After Full Analysis

**Location:** `output/scrap-data/{product_id}/review.json`

**Sample Data:**
```json
[
  {
    "id": "comment_id_1",
    "userid": 123456,
    "username": "buyer_name",
    "rating": 5,
    "comment": "Sangat puas dengan produknya",
    "likes": 45,
    "create_time": "2025-01-15",
    "sentiment": "positive",
    "sentiment_confidence": 0.95,
    "is_fake": false,
    "fake_confidence": 0.02,
    "trust_score": 87.5,
    "tags": ["Kualitas Bagus", "Pengiriman Cepat"],
    "comment_clean": "sangat puas produk"
  }
]
```

### Analysis Results Location

**Sentiment:** `output/comment/{product_id}/indobert/review_sentiment.csv`
**Fake Detection:** `output/comment/{product_id}/indobert/review_fake.csv`
**Trust Scores:** `output/comment/{product_id}/indobert/review_trust.csv`
**Summary:** `output/comment/{product_id}/indobert/summary.json`

## Error Handling

### Product Not Found (Re-analyze Only)

**Request:**
```bash
curl -X POST http://localhost:5000/api/analyze/reanalyze \
  -d '{"product_id": "invalid-id"}'
```

**Response (404):**
```json
{
  "error": "Product has not been scraped yet"
}
```

### Missing Required Parameter

**Request:**
```bash
curl -X POST http://localhost:5000/api/analyze/full \
  -d '{}'
```

**Response (400):**
```json
{
  "error": "missing link parameter"
}
```

## Performance Benchmarks

| Operation | Time | Data Size |
|-----------|------|-----------|
| Scrape 1000 comments | 8-12 min | 2-5 MB |
| Analyze 1000 comments | 5-8 min | 10-20 MB |
| Full workflow | 13-20 min | 12-25 MB |
| Re-analyze 1000 | 5-8 min | 10-20 MB |

## Tips & Best Practices

### 1. Use Scrape-Only for Batch Operations
```bash
# Collect data for multiple products quickly
for product_id in list.txt; do
  curl -X POST http://localhost:5000/api/analyze/scrape \
    -H "Content-Type: application/json" \
    -d "{\"link\": \"https://shopee.co.id/product/$product_id\"}"
done

# Then re-analyze all when ready
```

### 2. Monitor Progress
```bash
while true; do
  curl http://localhost:5000/api/status/{job_id} | jq '.analysis_progress'
  sleep 10
done
```

### 3. Check Available Products
```bash
curl http://localhost:5000/api/history/products | jq '.products[] | {name, review_count, analysis_done}'
```

### 4. Get Product Statistics
```bash
curl http://localhost:5000/api/product/{product_id}/stats | jq '.'
```

### 5. View Comments with Filters
```bash
curl "http://localhost:5000/api/comments/{product_id}?sentiment=positive&tag=Kualitas" | jq '.'
```

## Troubleshooting

### Job Stuck in "analysis" Phase
- Check server logs: `tail -f backend/app-backend-flask/log/jobs.log`
- Check if scraper data exists: `ls -la output/scrap-data/{product_id}/`
- Restart Flask if needed

### Sentiment Not Appearing
- Verify analysis completed: `GET /api/status/{job_id}`
- Check CSV exists: `ls output/comment/{product_id}/indobert/review_sentiment.csv`
- Verify merge completed in logs

### Out of Disk Space
- Check: `df -h`
- Clean old jobs: `rm -rf output/comment/old-product-ids/*`
- Archive data: `tar czf archive.tar.gz output/scrap-data/old-products/`

## API Response Structure

### Success Response
```json
{
  "ok": true,
  "job_id": "xyz123",
  "message": "Operation started/completed"
}
```

### Error Response
```json
{
  "error": "Error description",
  "ok": false
}
```

## Documentation Links

- Full specification: `ANALYSIS_RESTRUCTURE.md`
- Data consolidation: `DATA_CONSOLIDATION_FIX.md`
- Comments detail feature: `COMMENTS_DETAIL_FEATURE.md`
