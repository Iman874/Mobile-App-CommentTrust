# Copilot / Agent Instructions — CommentTrust repo

Purpose: Short, practical guidance for an AI coding agent to be immediately productive in this repository. Keep edits scoped, add tests, and prefer minimal, safe changes.

## Big picture
- Two main backends and one mobile client:
  - Laravel app: `backend/app-backend-laravel` — primary web UI, DB, ingestion points and admin UI.
  - Flask analysis pipeline: `backend/app-backend-flask` — scraper + analysis (sentiment, fake detection, trust scoring); runs async jobs and writes CSV/JSON outputs into `output/`.
  - Flutter client: `comment_trust_app` — mobile UI consuming Laravel APIs (see `lib/services/analysis_service.dart`).
- Dataflow summary: Flask scrapes a Shopee product -> runs pipeline -> writes outputs into `output/scrap-data/<product>/review-*.csv` and `output/comment/<product>/<backend>/…`. Flask notifies Laravel via webhook; Laravel pulls `/api/result/<product>/all` to ingest comments into DB.

## Key files & entry points (use these when asked what to change)
- Laravel
  - API webhook for ingest: `routes/api.php` -> `POST /api/ingest/commenttrust` handled by `app/Http/Controllers/CommentTrustController.php`.
  - Tag handling: `app/Services/TagService.php` (attach/process CSVs and update product tag stats).
  - Where comments are stored & inserted in bulk: `app/Http/Controllers/CommentTrustController.php` (buffer flush at 1000 items, then `_insertCommentsWithTags`).
- Flask
  - Main app: `backend/app-backend-flask/main.py` (registers `service/api.py` blueprint).
  - API + job runner / endpoints: `backend/app-backend-flask/service/api.py` (endpoints: `/api/input/link`, `/api/result/<product>/all`, `/api/force/scrape`, `/api/force/analysis`, `/api/log`, `/api/health`).
  - Pipeline: `backend/app-backend-flask/utils/pipeline.py` and `utils/analysis/*.py` (examples of analysis steps: tokenize, sentiment, fake detect, trust, summarize).
- Data file locations (important when debugging):
  - Scraped reviews: `backend/app-backend-flask/output/scrap-data/<product>/review-<product>.csv` (and `product.json`).
  - Analysis outputs: `backend/app-backend-flask/output/comment/<product>/<backend>/review_sentiment.csv`, `review_fake.csv`, `review_trust.csv`, `summary.json`, `review_tags.csv`.

## Important conventions & gotchas
- Product ID format: `shopid-itemid` (e.g., `95959099-3249518513`). The Flask `_build_canonical` function creates these. Use that format when calling APIs directly.
- Ingestion preference: Laravel chooses the richest source in this order: `trust` -> `sentiment` -> `review_raw` (see `CommentTrustController::ingest`).
- Tag workflow: Flask may send `tags` per comment (array), `tags_csv`, and `tag_statistics`. Laravel stores `tags` JSON in `comments.tags`, then uses `TagService` to sync tag relationships after bulk insert.
- Bulk insert and tagging: `CommentTrustController` bulk-inserts comments, then fetches the just-inserted rows in reverse order to attach tags. Keep chunk size and index mapping intact if changing insertion logic.
- JSON sanitization: Flask sanitizes NaN/Infinity to `null` when building `/api/result/...`. Laravel also tries to sanitize malformed JSON and logs decode errors before attempting fixes.
- Edge/browser scrapers: Flask uses `edge_runner` and supports a headless/visible Edge driver; cookies and remote debug may be required to run scrapers locally (see `backend/app-backend-flask/how_tow_run.txt`).

## How to run & debug (examples)
- Run Flask locally:
  - Create venv, install: `python -m venv venv && source venv/bin/activate && pip install -r backend/app-backend-flask/requirements.txt`
  - Launch: `python backend/app-backend-flask/main.py` (listens on 0.0.0.0:5001). See `how_tow_run.txt` for notes on Edge remote debugging and cookies.
  - Schedule a job: `curl -X POST 'http://localhost:5001/api/input/link' -H 'Content-Type:application/json' -d '{"link":"https://shopee.co.id/…"}'`
  - Fetch analysis product JSON: `GET http://localhost:5001/api/result/95959099-3249518513/all`
- Run Laravel locally (typical flow):
  - `composer install`, copy `.env` and set `DB_*` and `FLASK_API_URL=http://localhost:5001`.
  - `php artisan key:generate` then `php artisan migrate`.
  - Serve: `php artisan serve --port=8000`.
  - Trigger ingest from Flask or manually: `curl -X POST 'http://localhost:8000/api/ingest/commenttrust' -H 'Content-Type:application/json' -d '{"product_id":"95959099-3249518513","force":true}'`
- Logs & quick checks:
  - Laravel logs: `backend/app-backend-laravel/storage/logs/laravel.log` (use for ingestion diagnostics; example lines show dataset sizes and sample row keys).
  - Flask logs: `backend/app-backend-flask/log/*.log` and `incoming.log`.
  - Useful endpoints: Flask `/api/health`, Laravel `/api/analysis/<productKey>` for product metrics.

## Testing & dev patterns
- Flask has small shell-based tests and edge wrapper scripts in `backend/app-backend-flask/test/` (see `run.sh`, `test_edge.sh`).
- Laravel unit/feature tests live in `backend/app-backend-laravel/tests/` and use PHPUnit. Run `./vendor/bin/phpunit` or `php artisan test`.
- When adding/adjusting the ingest flow, add an integration test that: 1) places a minimal `output/scrap-data/<product>/review-<product>.csv` and analysis CSVs in Flask outputs, 2) hits `/api/result/<product>/all` to validate sanitation, 3) POSTs to Laravel ingest and asserts comments are inserted and tags attached.

## When to ask for human guidance
- Any change to indexing/bulk-insert/tag attach logic — this is fragile due to the index-based mapping approach used after bulk insert.
- Changes to the product identifier format or canonicalization logic.
- Any change to the pipeline step ordering or output CSV schema (update both Flask `api.py` and Laravel ingestion mapping together).

---
If anything here is unclear or you want additional examples (curl snippets, sample JSON payloads, or unit test templates), tell me which area to expand and I’ll update the doc. ✅