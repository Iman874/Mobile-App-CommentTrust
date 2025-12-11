# Copilot Instructions for Mobile-App-CommentTrust

These instructions help AI coding agents work productively in this repo. Focus on the concrete architecture, workflows, and conventions used here.

## Overview
- **Monorepo components:**
  - `comment_trust_app/` — Flutter mobile/web app (Dart).
  - `backend/app-backend-flask/` — Python Flask backend + scraping/analysis utilities.
  - `backend/app-backend-laravel/` — Laravel (PHP) backend scaffold.
  - `Scrapper/` — Python scripts for data collection and NLP pipeline.
- **Goal:** Scrape product comments/reviews, analyze sentiment/trust/fake reviews, serve results to the app, and visualize progress.

## Architecture & Data Flow
- **Scraping + Analysis (Python):**
  - Primary scripts live in `Scrapper/` (`scrapper_comment.py`, `scrapper_produk.py`, `main_analisis.py`). Outputs stored under `Scrapper/output/`.
  - Flask app integrates scraping and pipelines via `backend/app-backend-flask/utils/` and `backend/app-backend-flask/service/`.
  - Key orchestrators:
    - `backend/app-backend-flask/utils/pipeline.py` — processing pipeline steps.
    - `backend/app-backend-flask/utils/progress_bar.py` — progress reporting.
    - `backend/app-backend-flask/service/api.py` — HTTP endpoints invoking pipeline/scraper.
  - Static progress UIs: `backend/app-backend-flask/static/` (`index.html`, `progress.html`, `visualisasi.html`).
- **Mobile App (Flutter):**
  - Entry: `comment_trust_app/lib/main.dart`.
  - App-specific UI/components live under `comment_trust_app/lib/frontend/`.
  - Assets in `comment_trust_app/assets/`.
  - The app likely consumes Flask/Laravel endpoints for comments and analysis results.
- **Laravel backend:**
  - Typical Laravel layout; routes in `backend/app-backend-laravel/routes/` (`api.php`, `web.php`).
  - Use if PHP stack is preferred for serving/aggregating results. Currently reads as scaffold; confirm active usage before major changes.

## Developer Workflows
- **Flutter app (run/test/build):**
  - Run mobile/web:
    ```sh
    cd comment_trust_app
    flutter pub get
    flutter run
    ```
  - Run web:
    ```sh
    cd comment_trust_app
    flutter run -d chrome
    ```
  - Tests:
    ```sh
    cd comment_trust_app
    flutter test
    ```
- **Flask backend (run):**
  - Dependencies: see `backend/app-backend-flask/requirements.txt`.
  - Entrypoint:
    ```sh
    cd backend/app-backend-flask
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python main.py
    ```
  - Endpoints live in `service/api.py`; static pages in `static/`.
- **Scrapper pipeline (run):**
  - Dependencies: `Scrapper/requirements.txt`.
  - Example commands:
    ```sh
    cd Scrapper
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python scrapper_comment.py
    python main_analisis.py
    ```
- **Laravel backend (run):**
  - Requires PHP, Composer, Node.
  - Typical bootstrap:
    ```sh
    cd backend/app-backend-laravel
    composer install
    cp .env.example .env && php artisan key:generate
    php artisan serve
    ```

## Conventions & Patterns
- **Python (Flask + Scrapper):**
  - Keep scraping in `Scrapper/` and reusable pipeline logic in `backend/app-backend-flask/utils/`.
  - Expose orchestrated operations via `backend/app-backend-flask/service/api.py`.
  - Store outputs under relevant `output/` folders (`backend/app-backend-flask/output/`, `Scrapper/output/`).
- **Flutter:**
  - Entry and routing through `lib/main.dart`; app-specific UI under `lib/frontend/`.
  - Static assets referenced from `assets/` and `web/` for PWA.
- **Laravel:**
  - Use `routes/api.php` for JSON endpoints; `routes/web.php` for web pages.
  - Standard MVC in `app/Models`, `app/Http/Controllers` (controllers may be missing; add as needed).

## Integration Points
- **App → Backend APIs:**
  - The Flutter app should call Flask/Laravel endpoints for:
    - Triggering scrapes/pipelines (`service/api.py` routes).
    - Fetching processed comments/reviews (`output/comment/`, `output/review/`).
  - When adding new endpoints, update `service/api.py` and ensure CORS if serving to web app.
- **Progress & Visualization:**
  - Use `progress_bar.py` to emit status; render with `static/progress.html`.
  - Visualizations hosted via Flask `static/visualisasi.html`, reading data from output directories.

## Practical Examples
- **Add a new pipeline step:** Implement in `backend/app-backend-flask/utils/analysis/` and wire it in `utils/pipeline.py`, then expose via a route in `service/api.py`.
- **New scraper target:** Add a script in `Scrapper/` and write to `Scrapper/output/`; optionally add a thin wrapper route in Flask to trigger it.
- **Mobile UI for results:** Create a page in `comment_trust_app/lib/frontend/` that fetches JSON from Flask and displays charts.

## Notes & Gotchas
- Selenium/Edge drivers exist under `edgedriver_win64/`; running scrapers headless on Linux may require driver changes and profile setup (`Scrapper/edge_profile/`).
- Some folders like `backend/[Arsip] Testing/` contain archived/testing scripts; avoid depending on them for production workflows.
- `backend/app-backend-flask/log/` holds runtime logs; check here when debugging.

## Where to Look First
- `comment_trust_app/lib/main.dart` (app entry)
- `backend/app-backend-flask/service/api.py` (Flask routes)
- `backend/app-backend-flask/utils/pipeline.py` (analysis orchestration)
- `Scrapper/scrapper_comment.py` and `Scrapper/main_analisis.py` (data ingestion/analysis)

If any of these sections are unclear or incomplete, tell me what you need (e.g., specific endpoints in `api.py`, current data formats in `output/`) and I’ll refine this file.