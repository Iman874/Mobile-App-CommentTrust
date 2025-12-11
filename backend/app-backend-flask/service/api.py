from flask import Blueprint, request, jsonify, current_app, Response
import os
import uuid
import threading
import time
import json
import subprocess
from datetime import datetime
import urllib.request
import urllib.error
import urllib.parse
try:
    # prefer absolute import when running as script
    from utils import pipeline  # type: ignore
    from utils.scrapper import edge_runner  # type: ignore
except ImportError:
    # fallback: adjust sys.path
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import pipeline  # type: ignore
    from utils.scrapper import edge_runner  # type: ignore
import re
import math
import pandas as pd
import urllib.parse

bp = Blueprint('api', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "log")
JOBS = {}
os.makedirs(LOG_DIR, exist_ok=True)

def _merge_analysis_to_reviews(product_id: str, analysis_backend: str = 'indobert'):
    """Merge sentiment, fake detection, and trust scores from analysis CSVs back to review.json"""
    try:
        review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
        review_file = os.path.join(review_dir, 'review.json')
        analysis_dir = os.path.join(BASE_DIR, 'output', 'comment', product_id, analysis_backend)
        
        if not os.path.exists(review_file):
            return False
        
        # Load reviews
        with open(review_file, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
        
        if not isinstance(reviews, list):
            reviews = []
        
        # Load sentiment results
        sentiment_file = os.path.join(analysis_dir, 'review_sentiment.csv')
        if os.path.exists(sentiment_file):
            sentiment_df = pd.read_csv(sentiment_file, encoding='utf-8-sig')
            sentiment_map = {}
            for idx, row in sentiment_df.iterrows():
                if idx < len(reviews):
                    sentiment_map[idx] = {
                        'sentiment': row.get('sentiment', 'neutral'),
                        'sentiment_confidence': row.get('sentiment_confidence', 0.0)
                    }
        
        # Load fake detection results
        fake_file = os.path.join(analysis_dir, 'review_fake.csv')
        fake_map = {}
        if os.path.exists(fake_file):
            fake_df = pd.read_csv(fake_file, encoding='utf-8-sig')
            for idx, row in fake_df.iterrows():
                if idx < len(reviews):
                    fake_map[idx] = {
                        'is_fake': bool(row.get('is_fake', False)),
                        'fake_confidence': float(row.get('fake_confidence', 0.0))
                    }
        
        # Load trust scores
        trust_file = os.path.join(analysis_dir, 'review_trust.csv')
        trust_map = {}
        if os.path.exists(trust_file):
            trust_df = pd.read_csv(trust_file, encoding='utf-8-sig')
            for idx, row in trust_df.iterrows():
                if idx < len(reviews):
                    trust_map[idx] = {
                        'trust_score': float(row.get('trust_score', 0.0))
                    }
        
        # Merge back to reviews
        for idx, review in enumerate(reviews):
            if idx in sentiment_map:
                review['sentiment'] = sentiment_map[idx]['sentiment']
                review['sentiment_confidence'] = sentiment_map[idx]['sentiment_confidence']
            
            if idx in fake_map:
                review['is_fake'] = fake_map[idx]['is_fake']
                review['fake_confidence'] = fake_map[idx]['fake_confidence']
            
            if idx in trust_map:
                review['trust_score'] = trust_map[idx]['trust_score']
        
        # Save merged reviews
        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Error merging analysis: {e}")
        return False

def _log_filename(job: dict, kind: str):
    product_id = job.get('product_id') or job.get('id')
    stamp = job.get('created_local_stamp')
    if not stamp:
        now_local = datetime.now()  # local time for requested format
        stamp = now_local.strftime('%H-%d-%m-%Y')  # jam-tanggal-bln-tahun
        job['created_local_stamp'] = stamp
    return os.path.join(LOG_DIR, f"{kind}-{product_id}-{stamp}.log")

def _write_log(job_id: str, kind: str, line: str):
    job = JOBS.get(job_id)
    if not job:
        return
    fname = _log_filename(job, kind)
    ts = datetime.utcnow().isoformat()
    with open(fname, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

def _write_general_log(line: str):
    ts = datetime.utcnow().isoformat()
    fname = os.path.join(LOG_DIR, 'incoming.log')
    with open(fname, 'a', encoding='utf-8') as f:
        f.write(f"[{ts}] {line}\n")

def _tail_log(job_id: str, kind: str, lines: int = 200):
    job = JOBS.get(job_id)
    if not job:
        return []
    fname = _log_filename(job, kind)
    if not os.path.exists(fname):
        return []
    with open(fname, "r", encoding="utf-8") as f:
        data = f.read().splitlines()
    return data[-lines:]


def _normalize_shopee_link(link: str) -> str:
    """Return cleaned long form (without query)."""
    if not link:
        return link
    link = link.strip()
    # decode percent encoding for easier parsing
    link = urllib.parse.unquote(link)
    # trim whitespace + remove query part
    link = link.split("?")[0]
    return link

def _extract_ids(url: str):
    m = re.search(r"i\.(\d+)\.(\d+)", url)
    if m:
        return m.group(1), m.group(2)
    nums = re.findall(r"\d{5,}", url)
    if len(nums) >= 2:
        return nums[-2], nums[-1]
    return None, None

def _build_canonical(link: str) -> dict:
    """Produce canonical + short variants from a cleaned Shopee link."""
    cleaned = _normalize_shopee_link(link)
    shopid, itemid = _extract_ids(cleaned)
    # slug part before '-i.shopid.itemid'
    slug = None
    if shopid and itemid and '-i.' in cleaned:
        try:
            slug = cleaned.split('-i.')[0].split('/')[-1]
        except Exception:
            slug = None
    if shopid and itemid:
        canonical_slug = slug or ''
        canonical = f"https://shopee.co.id/{canonical_slug}-i.{shopid}.{itemid}" if canonical_slug else f"https://shopee.co.id/-i.{shopid}.{itemid}"
        # product path variant (often also resolves)
        product_variant = f"https://shopee.co.id/product/{shopid}/{itemid}"
        return {
            'cleaned': cleaned,
            'shopid': shopid,
            'itemid': itemid,
            'product_id': f"{shopid}-{itemid}",
            'canonical': canonical,
            'short': product_variant
        }
    # fallback when ids not found
    return {
        'cleaned': cleaned,
        'shopid': None,
        'itemid': None,
        'product_id': None,
        'canonical': cleaned,
        'short': cleaned
    }


def _run_job(job_id: str):
    job = JOBS[job_id]
    link = job["link"]
    _write_log(job_id, "process", f"START job for link: {link}")
    meta = _build_canonical(link)
    shopid, itemid = meta.get('shopid'), meta.get('itemid')
    product_id = f"{shopid}-{itemid}" if shopid and itemid else job_id
    job['product_id'] = product_id
    job['canonical'] = meta.get('canonical')
    job['short_link'] = meta.get('short')
    # SCRAPER PHASE
    job["phase"] = "scraper"
    job["scraper_total"] = 0
    job["scraper_progress"] = 0
    job['scraper_state'] = 'queued'
    job['scraper_block'] = None
    # run real scraper
    def _scraper_progress(done, total):
        try:
            job['scraper_total'] = int(total)
            job['scraper_progress'] = int(done)
        except Exception:
            pass
    def _scraper_log(msg):
        _write_log(job_id, 'process', str(msg))
    def _scraper_state(state: str, block: str|None):
        job['scraper_state'] = state
        job['scraper_block'] = block
        if state in {'waiting_login','captcha'}:
            _write_log(job_id, 'process', f"SCRAPER state {state}: {block}")

    # review dir per product - pipeline expects review.json here
    review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
    # optional force-scrape: clear previous review dir
    if job.get('force_scrape'):
        try:
            import shutil
            if os.path.isdir(review_dir):
                shutil.rmtree(review_dir, ignore_errors=True)
            _write_log(job_id, 'process', 'FORCE SCRAPE: cleared previous review dir')
        except Exception as e:
            _write_log(job_id, 'process', f'FORCE SCRAPE cleanup error: {e}')
    try:
        total = edge_runner.run(
            link=job.get('canonical') or job.get('short_link') or link,
            shopid=shopid or '',
            itemid=itemid or '',
            out_review_dir=review_dir,
            base_dir=BASE_DIR,
            force_copy=bool(job.get('force_copy_browser')),
            progress=_scraper_progress,
            log=_scraper_log,
            state_cb=_scraper_state
        )
    except Exception as e:
        job['phase'] = 'error'
        job['error'] = f'scraper failed: {e}'
        _write_log(job_id, 'process', f"ERROR scraper failed: {e}")
        return
    _write_log(job_id, 'process', 'SCRAPER finished')

    # ANALYSIS PHASE (internal pipeline)
    job['phase'] = 'analysis'
    job['analysis_progress'] = 0
    job['analysis_step_index'] = 0
    job['analysis_steps_total'] = 7  # init + 6 steps + done considered final marker
    job['analysis_step_name'] = 'pending'

    steps_order = [
        'init: resolve input',
        '[01] preprocess',
        '[01b] tokenize',
        '[03] sentiment',
        '[04] fake detect',
        '[05] trust score',
        '[06] summarize',
        'done'
    ]
    def _progress(pct, msg):
        try:
            job['analysis_progress'] = int(pct)
            if isinstance(msg, str):
                job['analysis_step_name'] = msg
                # map to index (1-based for UI)
                if msg in steps_order:
                    job['analysis_step_index'] = steps_order.index(msg) + 1
            _write_log(job_id, 'process', f"ANALYSIS {job['analysis_progress']}% :: {msg}")
        except Exception:
            pass

    try:
        out_dir = pipeline.run_pipeline(source_dir=review_dir, product_id=product_id, backend='indobert', progress=_progress)
        _write_log(job_id, 'process', f"OUTPUT pipeline finished; outputs at {out_dir}")
        
        # Merge sentiment, fake, trust results back to review.json
        _write_log(job_id, 'process', "Merging analysis results to reviews...")
        merge_ok = _merge_analysis_to_reviews(product_id, 'indobert')
        if merge_ok:
            _write_log(job_id, 'process', "Analysis results merged successfully")
        else:
            _write_log(job_id, 'process', "Warning: Could not merge analysis results")
        
        job['analysis_progress'] = 100
        job['phase'] = 'done'
        # notify Laravel
        job['laravel_sync_status'] = 'sending'
        job['laravel_sync_progress'] = 10
        try:
            ok, err = _notify_and_wait_laravel(job, product_id, force=bool(job.get('force_analysis') or job.get('force_scrape')))
            if ok:
                job['laravel_sync_status'] = 'ok'
                job['laravel_sync_progress'] = 100
                _write_log(job_id, 'process', 'Laravel sync succeeded')
            else:
                job['laravel_sync_status'] = 'error'
                job['laravel_sync_error'] = err
                job['laravel_sync_progress'] = 100
                _write_log(job_id, 'process', f'Laravel sync failed: {err}')
        except Exception as e:
            job['laravel_sync_status'] = 'error'
            job['laravel_sync_error'] = str(e)
            job['laravel_sync_progress'] = 100
            _write_log(job_id, 'process', f'Laravel notify exception: {e}')
    except Exception as e:
        job['phase'] = 'error'
        job['error'] = str(e)
        _write_log(job_id, 'process', f"ERROR pipeline error: {e}")


@bp.route('/input/link', methods=['POST'])
def input_link():
    j = request.get_json(force=True, silent=True) or request.form or {}
    link = j.get('link') if isinstance(j, dict) else None
    force_copy_browser = bool(j.get('force_copy_browser')) if isinstance(j, dict) else False
    if not link:
        return jsonify({'error': 'missing link parameter'}), 400
    norm_meta = _build_canonical(link)
    norm = norm_meta['cleaned']
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        'id': job_id,
        'link': norm,
        'phase': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'scraper_progress': 0,
        'scraper_total': 0,
        'analysis_progress': 0,
        'error': None,
        'canonical': norm_meta.get('canonical'),
        'short_link': norm_meta.get('short'),
        'product_id': norm_meta.get('product_id'),
        'force_copy_browser': force_copy_browser
    }
    _write_log(job_id, 'input', f"INPUT received link: {link} -> normalized: {norm}")
    # start background thread
    t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    t.start()
    return jsonify({
        'job_id': job_id,
        'status_url': f'/api/status/{job_id}',
        'progress_page': f'/progress?job={job_id}',
        'canonical': norm_meta.get('canonical'),
        'short_link': norm_meta.get('short'),
        'product_id': norm_meta.get('product_id')
    })


@bp.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    if job_id not in JOBS:
        return jsonify({'error': 'job not found'}), 404
    job = JOBS[job_id].copy()
    job['logs'] = {
        'input': _tail_log(job_id, 'input', lines=200),
        'process': _tail_log(job_id, 'process', lines=200)
    }
    return jsonify(job)

# legacy name removed; use _notify_and_wait_laravel

def _laravel_api_base() -> str:
    base = os.environ.get('LARAVEL_API_BASE')
    if base:
        return base.rstrip('/')
    hook = os.environ.get('LARAVEL_WEBHOOK_URL', 'http://127.0.0.1:8000/api/ingest/commenttrust')
    try:
        p = urllib.parse.urlsplit(hook)
        return f"{p.scheme}://{p.netloc}/api"
    except Exception:
        return 'http://127.0.0.1:8000/api'

def _notify_and_wait_laravel(job: dict, product_id: str, force: bool = False, max_post_retries: int = 3, poll_seconds: int = 120):
    """Post ingest to Laravel (retry) then poll /api/analysis/{product_id} until comments exist.
    Updates job['laravel_sync_*'] fields as progress UI feedback.
    Returns (ok, message).
    """
    api_base = _laravel_api_base()
    ingest_url = os.environ.get('LARAVEL_WEBHOOK_URL', f"{api_base}/ingest/commenttrust")
    payload = json.dumps({'product_id': product_id, 'force': bool(force)}).encode('utf-8')
    for i in range(max_post_retries):
        job['laravel_sync_status'] = f'sending({i+1}/{max_post_retries})'
        job['laravel_sync_progress'] = 10 + int(10*i)
        req = urllib.request.Request(ingest_url, data=payload, headers={'Content-Type':'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode('utf-8','ignore')
                _write_general_log(f'Notify Laravel ok {resp.status}: {body[:120]}')
                # also write into job process log for visibility in UI
                try:
                    _write_log(job.get('id') or job.get('job_id') or 'unknown', 'process', f"Laravel ingest accepted (HTTP {resp.status})")
                except Exception:
                    pass
                try:
                    jbody = json.loads(body)
                    if isinstance(jbody, dict) and 'inserted' in jbody:
                        job['laravel_sync_inserted'] = int(jbody.get('inserted') or 0)
                        try:
                            _write_log(job.get('id') or job.get('job_id') or 'unknown', 'process', f"Laravel ingest immediate inserted={job['laravel_sync_inserted']}")
                        except Exception:
                            pass
                except Exception:
                    pass
                break
        except Exception as e:
            _write_general_log(f'Notify Laravel attempt {i+1} failed: {e}')
            try:
                _write_log(job.get('id') or job.get('job_id') or 'unknown', 'process', f"Laravel ingest attempt {i+1} failed: {e}")
            except Exception:
                pass
            if i == max_post_retries-1:
                return False, f'notify failed: {e}'
        try:
            time.sleep(2*(i+1))
        except Exception:
            pass

    job['laravel_sync_status'] = 'waiting-db'
    analysis_url = f"{api_base}/analysis/{urllib.parse.quote(product_id)}"
    start = time.time()
    last_err = None
    last_count = -1
    polls = 0
    while time.time() - start < poll_seconds:
        try:
            with urllib.request.urlopen(analysis_url, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8','ignore'))
                    metrics = data.get('metrics') or {}
                    cnt = int(metrics.get('count_reviews') or 0)
                    elapsed = time.time() - start
                    pct = 40 + int(60 * min(1.0, elapsed / poll_seconds))
                    job['laravel_sync_progress'] = max(job.get('laravel_sync_progress', 40), pct)
                    polls += 1
                    # Log on first poll, on count increase, and every 5 polls
                    if cnt != last_count or polls % 5 == 1:
                        try:
                            _write_log(job.get('id') or job.get('job_id') or 'unknown', 'process', f"Laravel poll: count_reviews={cnt} status={job.get('laravel_sync_status','waiting-db')}")
                        except Exception:
                            pass
                        last_count = cnt
                    if cnt > 0:
                        job['laravel_sync_progress'] = 100
                        job['laravel_sync_status'] = 'ok'
                        return True, None
                else:
                    last_err = f'status {resp.status}'
        except Exception as e:
            last_err = str(e)
            try:
                _write_log(job.get('id') or job.get('job_id') or 'unknown', 'process', f"Laravel poll error: {last_err}")
            except Exception:
                pass
        time.sleep(2)
    job['laravel_sync_status'] = 'error'
    job['laravel_sync_error'] = last_err or 'timeout'
    job['laravel_sync_progress'] = 100
    return False, job['laravel_sync_error']

def _analysis_only(job_id: str, product_id: str):
    job = JOBS[job_id]
    job['phase'] = 'analysis'
    job['analysis_progress'] = 0
    job['analysis_step_index'] = 0
    job['analysis_steps_total'] = 7
    job['analysis_step_name'] = 'pending'

    steps_order = [
        'init: resolve input','[01] preprocess','[01b] tokenize','[03] sentiment','[04] fake detect','[05] trust score','[06] summarize','done'
    ]
    def _progress(pct, msg):
        try:
            job['analysis_progress'] = int(pct)
            if isinstance(msg, str):
                job['analysis_step_name'] = msg
                if msg in steps_order:
                    job['analysis_step_index'] = steps_order.index(msg)+1
            _write_log(job_id, 'process', f"ANALYSIS {job['analysis_progress']}% :: {msg}")
        except Exception:
            pass
    review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
    try:
        out_dir = pipeline.run_pipeline(source_dir=review_dir, product_id=product_id, backend='indobert', progress=_progress)
        _write_log(job_id, 'process', f"OUTPUT pipeline finished; outputs at {out_dir}")
        
        # Merge sentiment, fake, trust results back to review.json
        _write_log(job_id, 'process', "Merging analysis results to reviews...")
        merge_ok = _merge_analysis_to_reviews(product_id, 'indobert')
        if merge_ok:
            _write_log(job_id, 'process', "Analysis results merged successfully")
        else:
            _write_log(job_id, 'process', "Warning: Could not merge analysis results")
        
        job['analysis_progress'] = 100
        job['phase'] = 'done'
        job['laravel_sync_status'] = 'sending'
        job['laravel_sync_progress'] = 10
        try:
            ok, err = _notify_and_wait_laravel(job, product_id, force=bool(job.get('force_analysis')))
            if ok:
                job['laravel_sync_status'] = 'ok'
                job['laravel_sync_progress'] = 100
                _write_log(job_id, 'process', 'Laravel sync succeeded')
            else:
                job['laravel_sync_status'] = 'error'
                job['laravel_sync_error'] = err
                job['laravel_sync_progress'] = 100
                _write_log(job_id, 'process', f'Laravel sync failed: {err}')
        except Exception as e:
            job['laravel_sync_status'] = 'error'
            job['laravel_sync_error'] = str(e)
            job['laravel_sync_progress'] = 100
            _write_log(job_id, 'process', f'Laravel notify exception: {e}')
    except Exception as e:
        job['phase'] = 'error'
        job['error'] = str(e)
        _write_log(job_id, 'process', f"ERROR pipeline error: {e}")

@bp.route('/normalize', methods=['POST'])
def normalize_only():
    j = request.get_json(force=True, silent=True) or {}
    link = j.get('link')
    if not link:
        return jsonify({'error': 'missing link'}), 400
    meta = _build_canonical(link)
    return jsonify(meta)

@bp.route('/input/link/force-copy-browser', methods=['POST'])
def input_link_force_copy():
    j = request.get_json(force=True, silent=True) or request.form or {}
    link = j.get('link') if isinstance(j, dict) else None
    if not link:
        return jsonify({'error': 'missing link parameter'}), 400
    j = dict(j)
    j['force_copy_browser'] = True
    # reuse input_link logic
    with current_app.test_request_context(json=j):
        return input_link()


@bp.route('/force/scrape', methods=['POST'])
def force_scrape():
    j = request.get_json(force=True, silent=True) or request.form or {}
    link = j.get('link') if isinstance(j, dict) else None
    if not link:
        return jsonify({'error': 'missing link parameter'}), 400
    norm_meta = _build_canonical(link)
    norm = norm_meta['cleaned']
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        'id': job_id,
        'link': norm,
        'phase': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'scraper_progress': 0,
        'scraper_total': 0,
        'analysis_progress': 0,
        'error': None,
        'canonical': norm_meta.get('canonical'),
        'short_link': norm_meta.get('short'),
        'product_id': norm_meta.get('product_id'),
        'force_scrape': True
    }
    _write_log(job_id, 'input', f"FORCE SCRAPE received link: {link} -> normalized: {norm}")
    t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    t.start()
    return jsonify({'job_id': job_id, 'status_url': f'/api/status/{job_id}', 'progress_page': f'/progress?job={job_id}', 'product_id': norm_meta.get('product_id')})

@bp.route('/force/analysis', methods=['POST'])
def force_analysis():
    j = request.get_json(force=True, silent=True) or request.form or {}
    link = j.get('link') if isinstance(j, dict) else None
    product_id = j.get('product_id') if isinstance(j, dict) else None
    if link and not product_id:
        meta = _build_canonical(link)
        product_id = meta.get('product_id')
    if not product_id:
        return jsonify({'error':'missing product_id or link'}), 400
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        'id': job_id,
        'link': link or '',
        'phase': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'scraper_progress': 0,
        'scraper_total': 0,
        'analysis_progress': 0,
        'error': None,
        'product_id': product_id,
        'force_analysis': True
    }
    _write_log(job_id, 'input', f"FORCE ANALYSIS for product: {product_id}")
    t = threading.Thread(target=_analysis_only, args=(job_id, product_id), daemon=True)
    t.start()
    return jsonify({'job_id': job_id, 'status_url': f'/api/status/{job_id}', 'progress_page': f'/progress?job={job_id}', 'product_id': product_id})

@bp.route('/log', methods=['POST'])
def general_log():
    j = request.get_json(force=True, silent=True) or {}
    msg = str(j.get('message') or '')
    if not msg:
        return jsonify({'error':'missing message'}), 400
    _write_general_log(msg)
    return jsonify({'ok': True})


@bp.route('/result/<product_id>/all', methods=['GET'])
def result_all(product_id):
    base_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    review_dir = os.path.join(base_out, 'scrap-data', product_id)
    # choose backend directory (prefer indobert if exists else first)
    comment_root = os.path.join(base_out, 'comment', product_id)
    backend_dir = None
    if os.path.isdir(comment_root):
        # pick first subdir
        subs = [d for d in os.listdir(comment_root) if os.path.isdir(os.path.join(comment_root,d))]
        backend_dir = os.path.join(comment_root, subs[0]) if subs else None
    def _read(path):
        if not path or not os.path.exists(path):
            return None
        if path.endswith('.csv'):
            try:
                import pandas as pd
                return pd.read_csv(path, encoding='utf-8-sig').to_dict(orient='records')
            except Exception:
                return None
        if path.endswith('.json'):
            try:
                return json.load(open(path,'r',encoding='utf-8'))
            except Exception:
                return None
        return None
    review_raw = _read(os.path.join(review_dir, f'review-{product_id}.csv'))
    sentiment = _read(os.path.join(backend_dir or '', 'review_sentiment.csv'))
    fake_detection = _read(os.path.join(backend_dir or '', 'review_fake.csv'))
    trust = _read(os.path.join(backend_dir or '', 'review_trust.csv'))
    summary = _read(os.path.join(backend_dir or '', 'summary.json'))
    product_trust = _read(os.path.join(backend_dir or '', 'product_trust.json'))
    # Debug counts logging
    try:
        _write_general_log(f"RESULT all {product_id} counts review_raw={(len(review_raw) if isinstance(review_raw,list) else 0)} sentiment={(len(sentiment) if isinstance(sentiment,list) else 0)} trust={(len(trust) if isinstance(trust,list) else 0)} backend_dir={backend_dir}")
    except Exception:
        pass
    def _sanitize(v):
        import math
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return None
        return v
    def _walk(obj):
        if isinstance(obj, list):
            return [_walk(x) for x in obj]
        if isinstance(obj, dict):
            return {k: _walk(_sanitize(v)) for k, v in obj.items()}
        return _sanitize(obj)
    payload = {
        'product_id': product_id,
        'review_raw': _walk(review_raw),
        'sentiment': _walk(sentiment),
        'fake_detection': _walk(fake_detection),
        'trust': _walk(trust),
        'summary': _walk(summary),
        'product_trust': _walk(product_trust)
    }
    try:
        _write_general_log(f"SANITIZE JSON {product_id} done")
    except Exception:
        pass
    return jsonify(payload)


def _csv_to_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        import pandas as pd
        return pd.read_csv(path, encoding='utf-8-sig').to_dict(orient='records')
    except Exception:
        return []

def _json_load(path):
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path,'r',encoding='utf-8'))
    except Exception:
        return None

def _backend_dir(product_id):
    base_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output','comment',product_id)
    if not os.path.isdir(base_out):
        return None
    subs = [d for d in os.listdir(base_out) if os.path.isdir(os.path.join(base_out,d))]
    return os.path.join(base_out, subs[0]) if subs else None

@bp.route('/result/<product_id>/comment', methods=['GET'])
def result_comment(product_id):
    review_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output','scrap-data',product_id)
    data = _csv_to_json_list(os.path.join(review_dir, f'review-{product_id}.csv'))
    return jsonify({'product_id': product_id, 'comments': data})

@bp.route('/result/<product_id>/detail-produk', methods=['GET'])
def result_detail_product(product_id):
    # product detail minimal di product_trust.json
    bdir = _backend_dir(product_id)
    detail = _json_load(os.path.join(bdir or '', 'product_trust.json'))
    return jsonify({'product_id': product_id, 'detail': detail})

@bp.route('/result/<product_id>/sentiment-analisis', methods=['GET'])
def result_sentiment(product_id):
    bdir = _backend_dir(product_id)
    data = _csv_to_json_list(os.path.join(bdir or '', 'review_sentiment.csv'))
    return jsonify({'product_id': product_id, 'sentiment': data})

@bp.route('/result/<product_id>/fake-review-detect', methods=['GET'])
def result_fake(product_id):
    bdir = _backend_dir(product_id)
    data = _csv_to_json_list(os.path.join(bdir or '', 'review_fake.csv'))
    return jsonify({'product_id': product_id, 'fake_detection': data})

@bp.route('/result/<product_id>/trust-score', methods=['GET'])
def result_trust(product_id):
    bdir = _backend_dir(product_id)
    data = _csv_to_json_list(os.path.join(bdir or '', 'review_trust.csv'))
    return jsonify({'product_id': product_id, 'trust': data})

@bp.route('/result/<product_id>/summarize', methods=['GET'])
def result_summary(product_id):
    bdir = _backend_dir(product_id)
    data = _json_load(os.path.join(bdir or '', 'summary.json'))
    return jsonify({'product_id': product_id, 'summary': data})

@bp.route('/health', methods=['GET'])
def health():
    """Return basic health diagnostics to debug loading issues."""
    edge_runner_import = True
    try:
        _ = edge_runner
    except Exception:
        edge_runner_import = False
    # check critical paths
    driver_path, cookie_path, profile_dir = edge_runner._paths(BASE_DIR) if edge_runner_import else (None,None,None)
    return jsonify({
        'status': 'ok',
        'edge_runner_import': edge_runner_import,
        'driver_exists': bool(driver_path and os.path.exists(driver_path)),
        'driver_path': driver_path,
        'cookie_exists': bool(cookie_path and os.path.exists(cookie_path)),
        'cookie_path': cookie_path,
        'profile_dir_exists': bool(profile_dir and os.path.isdir(profile_dir)),
        'profile_dir': profile_dir,
        'jobs_count': len(JOBS)
    })


# ===== Visualization Endpoint =====
FAKE_THRESHOLD = 0.6

def _resolve_product_backend_dir(product_id: str):
    base_out = os.path.join(BASE_DIR, 'output', 'comment', product_id)
    # If directory missing, return a sensible guess path to avoid 404s
    if not os.path.isdir(base_out):
        return os.path.join(base_out, 'indobert')
    subs = [d for d in os.listdir(base_out) if os.path.isdir(os.path.join(base_out, d))]
    if not subs:
        return os.path.join(base_out, 'indobert')
    # prefer indobert if exists
    preferred = [s for s in subs if s.lower().startswith('indobert')]
    if preferred:
        return os.path.join(base_out, preferred[0])
    return os.path.join(base_out, subs[0])

def _normalize_trust(avg_trust: float) -> float:
    """Normalize average trust (0..100) to a calibrated 0..100%.

    Previously we applied sigmoid( v/10 ), which pushes any v>0 quickly to ~100%.
    Calibrate by centering at 50 and scaling by 10 so that:
      - v=50 -> 50%
      - v=80 -> ~95%
      - v=20 -> ~5%
    This yields a more realistic indicator when fake_rate is present.
    """
    try:
        v = float(avg_trust)
        if not (v == v):  # NaN
            return 0.0
    except Exception:
        return 0.0
    v = max(0.0, min(100.0, v))
    z = (v - 50.0) / 10.0
    return round(100.0 / (1.0 + math.exp(-z)), 2)

def _trust_level(val_percent: float):
    if val_percent >= 71.0:
        return 'High', 'trust-high'
    if val_percent >= 41.0:
        return 'Medium', 'trust-med'
    return 'Low', 'trust-low'

@bp.route('/visualisasi/<product_id>', methods=['GET'])
def visualisasi_data(product_id):
    bdir = _resolve_product_backend_dir(product_id)
    # Check if backend directory is found
    if not bdir:
        return jsonify({'error': 'product backend dir not found', 'product_id': product_id}), 404
    trust_csv = os.path.join(bdir, 'review_trust.csv')
    summary_json = os.path.join(bdir, 'summary.json')
    product_trust_json = os.path.join(bdir, 'product_trust.json')
    df = None
    if os.path.exists(trust_csv):
        try:
            df = pd.read_csv(trust_csv, encoding='utf-8-sig')
        except Exception:
            try:
                df = pd.read_csv(trust_csv)
            except Exception:
                df = None
    # fallback to sentiment file for minimal metrics
    df_sent = None
    sent_csv = os.path.join(bdir, 'review_sentiment.csv')
    if df is None and os.path.exists(sent_csv):
        try:
            df_sent = pd.read_csv(sent_csv, encoding='utf-8-sig')
        except Exception:
            try:
                df_sent = pd.read_csv(sent_csv)
            except Exception:
                df_sent = None
    summary = {}
    if os.path.exists(summary_json):
        try:
            summary = json.load(open(summary_json,'r',encoding='utf-8'))
        except Exception:
            summary = {}
    product_trust = {}
    if os.path.exists(product_trust_json):
        try:
            product_trust = json.load(open(product_trust_json,'r',encoding='utf-8'))
        except Exception:
            product_trust = {}
    # metrics
    count_reviews = 0
    avg_rating = 0.0
    avg_trust_score = 0.0
    fake_rate = 0.0
    sentiment_counts = {}
    trust_hist = [0]*10
    fake_score_hist = {'bins':[], 'counts':[], 'colors':[]}
    pros = summary.get('pros') or []
    cons = summary.get('cons') or []
    pos_sum = summary.get('positive_summary') or ''
    neg_sum = summary.get('negative_summary') or ''
    if df is not None and len(df) > 0:
        count_reviews = int(len(df))
        avg_rating = float(pd.to_numeric(df.get('rating', 0), errors='coerce').fillna(0).mean())
        avg_trust_score = float(pd.to_numeric(df.get('trust_score', 0), errors='coerce').fillna(0).mean())
        sentiment_counts = df.get('sentiment', pd.Series([])).astype(str).str.lower().value_counts().to_dict()
        # trust histogram (0..100 bucket by 10)
        trust_vals = pd.to_numeric(df.get('trust_score', 0), errors='coerce').fillna(0).clip(0,100).tolist()
        for v in trust_vals:
            idx = min(9, int(v)//10)
            trust_hist[idx] += 1
        # fake score rate
        fs_series = pd.to_numeric(df.get('fake_score', df.get('suspicion_score', 0)), errors='coerce').fillna(0).clip(0,1)
        fake_rate = float((fs_series >= FAKE_THRESHOLD).mean())
        # histogram 0..1 step 0.1
        edges = [i/10 for i in range(11)]
        labels = [f"{edges[i]:.1f}-{edges[i+1]:.1f}" for i in range(10)]
        cat = pd.cut(fs_series, bins=edges, include_lowest=True, right=True, labels=labels)
        counts = cat.value_counts().reindex(labels, fill_value=0).tolist()
        colors = []
        thr = float(FAKE_THRESHOLD)
        for i in range(10):
            mid = (edges[i]+edges[i+1])/2.0
            colors.append('#d62728' if mid >= thr else '#59a14f')
        fake_score_hist = {'bins': labels, 'counts': counts, 'colors': colors, 'threshold': thr}
    elif df_sent is not None and len(df_sent) > 0:
        # minimal metrics using sentiment-only file
        count_reviews = int(len(df_sent))
        avg_rating = float(pd.to_numeric(df_sent.get('rating', 0), errors='coerce').fillna(0).mean())
        sentiment_counts = df_sent.get('sentiment', pd.Series([])).astype(str).str.lower().value_counts().to_dict()

    # Ensure all three sentiment keys exist for UI consistency
    for k in ('positive','negative','neutral'):
        if k not in sentiment_counts:
            sentiment_counts[k] = 0

    avg_trust_percent = _normalize_trust(avg_trust_score)
    trust_level_text, trust_level_class = _trust_level(avg_trust_percent)
    # existence flags for UI troubleshooting
    exists = {
        'backend_dir': os.path.isdir(bdir),
        'trust_csv': os.path.exists(trust_csv),
        'summary_json': os.path.exists(summary_json),
        'product_trust_json': os.path.exists(product_trust_json),
        'sentiment_csv': os.path.exists(os.path.join(bdir, 'review_sentiment.csv')),
        'review_csv': os.path.exists(os.path.join(BASE_DIR, 'output', 'scrap-data', product_id, f'review-{product_id}.csv'))
    }
    return jsonify({
        'product_id': product_id,
        'backend_dir': bdir,
        'exists': exists,
        'metrics': {
            'count_reviews': count_reviews,
            'avg_rating': round(avg_rating,2),
            'avg_trust_score': round(avg_trust_score,2),
            'avg_trust_percent_norm': avg_trust_percent,
            'trust_level': trust_level_text,
            'trust_level_class': trust_level_class,
            'fake_rate': round(fake_rate,4),
            'sentiment_counts': sentiment_counts,
            'trust_hist': trust_hist,
            'fake_score_hist': fake_score_hist,
            'pros': pros,
            'cons': cons,
            'positive_summary': pos_sum,
            'negative_summary': neg_sum
        },
        'summary_raw': summary,
        'product_trust_raw': product_trust,
        'updated_at': datetime.utcnow().isoformat()
    })

@bp.route('/visualisasi.html')
def visualisasi_page_redirect():
    # allow /visualisasi.html?product=<id> to serve static file easily
    # We simply read the static html and return (no template engine used)
    static_path = os.path.join(BASE_DIR, 'static', 'visualisasi.html')
    if not os.path.exists(static_path):
        return Response('<h3>visualisasi.html not found</h3>', mimetype='text/html')
    with open(static_path, 'r', encoding='utf-8') as f:
        return Response(f.read(), mimetype='text/html')

# Manual re-sync endpoint to re-notify Laravel without reanalysis
# Endpoint untuk menampilkan histori produk yang sudah di-scrape
@bp.route('/history/products', methods=['GET'])
def history_products():
    """List all products that have been scraped with basic statistics."""
    review_base = os.path.join(BASE_DIR, 'output', 'scrap-data')
    products = []
    
    if not os.path.isdir(review_base):
        return jsonify({'products': []})
    
    for product_id in os.listdir(review_base):
        product_dir = os.path.join(review_base, product_id)
        if not os.path.isdir(product_dir):
            continue
        
        # Read product.json
        product_file = os.path.join(product_dir, 'product.json')
        product_data = {}
        if os.path.exists(product_file):
            try:
                with open(product_file, 'r', encoding='utf-8') as f:
                    product_data = json.load(f)
            except Exception:
                pass
        
        # Read review.json and count
        review_file = os.path.join(product_dir, 'review.json')
        review_count = 0
        if os.path.exists(review_file):
            try:
                with open(review_file, 'r', encoding='utf-8') as f:
                    reviews = json.load(f)
                    review_count = len(reviews) if isinstance(reviews, list) else 0
            except Exception:
                pass
        
        # Check if analysis is done
        analysis_done = False
        analysis_dir = os.path.join(BASE_DIR, 'output', 'comment', product_id, 'indobert')
        if os.path.isdir(analysis_dir):
            analysis_done = os.path.exists(os.path.join(analysis_dir, 'review_trust.csv'))
        
        products.append({
            'product_id': product_id,
            'product_name': product_data.get('name') or product_data.get('name_prefix') or 'Unknown',
            'shop_name': product_data.get('shop', {}).get('name') if isinstance(product_data.get('shop'), dict) else '',
            'price': product_data.get('price'),
            'review_count': review_count,
            'analysis_done': analysis_done,
            'rating': product_data.get('item_rating', {}).get('rating_star', 0),
        })
    
    # Sort by product_id (newest first)
    products.sort(key=lambda x: x['product_id'], reverse=True)
    return jsonify({'products': products})


@bp.route('/product/<product_id>/stats', methods=['GET'])
def product_stats(product_id: str):
    """Get statistics for a specific product."""
    product_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
    
    if not os.path.isdir(product_dir):
        return jsonify({'error': 'Product not found'}), 404
    
    # Read reviews and calculate stats
    review_file = os.path.join(product_dir, 'review.json')
    reviews = []
    if os.path.exists(review_file):
        try:
            with open(review_file, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
                if not isinstance(reviews, list):
                    reviews = []
        except Exception:
            reviews = []
    
    # Read product info
    product_file = os.path.join(product_dir, 'product.json')
    product_data = {}
    if os.path.exists(product_file):
        try:
            with open(product_file, 'r', encoding='utf-8') as f:
                product_data = json.load(f)
        except Exception:
            pass
    
    # Get tag statistics if available (from analysis)
    from utils.comment_tagger import get_tag_statistics
    tag_stats = {}
    if reviews and len(reviews) > 0 and 'tags' in reviews[0]:
        tag_stats = get_tag_statistics(reviews)
    
    # Count sentiment if available
    sentiment_count = {'positive': 0, 'neutral': 0, 'negative': 0}
    for review in reviews:
        sentiment = review.get('sentiment', '').lower()
        if sentiment in sentiment_count:
            sentiment_count[sentiment] += 1
    
    return jsonify({
        'product_id': product_id,
        'product_name': product_data.get('name') or product_data.get('name_prefix') or 'Unknown',
        'review_count': len(reviews),
        'sentiment_count': sentiment_count,
        'tag_stats': tag_stats,
        'rating': product_data.get('item_rating', {}).get('rating_star', 0),
    })


@bp.route('/reanalyze/<product_id>', methods=['POST'])
def reanalyze_product(product_id: str):
    """Re-run FULL analysis on existing product reviews, deleting old analysis files and starting fresh."""
    job_id = uuid.uuid4().hex[:8]
    job = {
        'id': job_id,
        'product_id': product_id,
        'phase': 'analysis',
        'analysis_progress': 0,
        'analysis_step_index': 0,
        'analysis_step_name': 'Starting full re-analysis',
    }
    JOBS[job_id] = job
    
    def thread_fn():
        try:
            _write_log(job_id, 'process', f"REANALYZE request for product {product_id}")
            
            # Step 1: Delete old analysis files to ensure fresh start
            job['analysis_step_name'] = 'Cleaning old analysis files...'
            job['analysis_progress'] = 10
            
            analysis_dirs_to_clean = [
                os.path.join(BASE_DIR, 'output', 'comment', product_id, 'auto'),
                os.path.join(BASE_DIR, 'output', 'comment', product_id, 'indobert'),
            ]
            
            for analysis_dir in analysis_dirs_to_clean:
                if os.path.isdir(analysis_dir):
                    try:
                        import shutil
                        shutil.rmtree(analysis_dir)
                        _write_log(job_id, 'process', f"Deleted analysis directory: {analysis_dir}")
                    except Exception as e:
                        _write_log(job_id, 'process', f"Warning: Could not delete {analysis_dir}: {e}")
            
            # Step 2: Run full pipeline
            job['analysis_step_name'] = 'Running full analysis pipeline...'
            job['analysis_progress'] = 20
            
            review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
            review_file = os.path.join(review_dir, 'review.json')
            
            if not os.path.exists(review_file):
                job['phase'] = 'error'
                job['error'] = 'Review file not found'
                _write_log(job_id, 'process', 'ERROR: review.json not found')
                return
            
            # Run the full pipeline
            def progress_callback(percent, msg):
                job['analysis_progress'] = 20 + int(percent * 0.75)  # Map to 20-95%
                job['analysis_step_name'] = msg
                _write_log(job_id, 'process', f"[{percent}%] {msg}")
            
            pipeline_output_dir = pipeline.run_pipeline(
                source_dir=review_dir,
                product_id=product_id,
                backend='indobert',
                progress=progress_callback
            )
            
            _write_log(job_id, 'process', f"Pipeline completed, output: {pipeline_output_dir}")
            
            # Step 2.5: Merge sentiment, fake, trust results back to review.json
            job['analysis_step_name'] = 'Merging analysis results to reviews...'
            job['analysis_progress'] = 92
            merge_ok = _merge_analysis_to_reviews(product_id, 'indobert')
            if merge_ok:
                _write_log(job_id, 'process', "Analysis results merged successfully")
            else:
                _write_log(job_id, 'process', "Warning: Could not merge analysis results")
            
            # Step 3: Apply tagging to reviews
            job['analysis_step_name'] = 'Extracting and applying comment tags...'
            job['analysis_progress'] = 95
            
            with open(review_file, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
                if not isinstance(reviews, list):
                    reviews = []
            
            from utils.comment_tagger import tag_comments, get_tag_statistics
            tagged_reviews = tag_comments(reviews, source_field='comment')
            _write_log(job_id, 'process', f"Tagged {len(tagged_reviews)} reviews")
            
            # Save tagged reviews back to review.json
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(tagged_reviews, f, ensure_ascii=False, indent=2)
            
            # Save tag statistics
            tag_stats = get_tag_statistics(tagged_reviews)
            stats_file = os.path.join(review_dir, 'tag_statistics.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(tag_stats, f, ensure_ascii=False, indent=2)
            
            _write_log(job_id, 'process', f"Saved tag statistics: {json.dumps(tag_stats)}")
            
            # Step 4: Create tagged CSV in analysis directory
            analysis_dir = os.path.join(BASE_DIR, 'output', 'comment', product_id, 'indobert')
            if os.path.isdir(analysis_dir):
                import pandas as pd
                
                tagged_csv_path = os.path.join(analysis_dir, 'review_tagged.csv')
                data_for_csv = []
                for review in tagged_reviews:
                    data_for_csv.append({
                        'comment': review.get('comment', ''),
                        'tags': ' | '.join(review.get('tags', [])),
                        'sentiment': review.get('sentiment', ''),
                        'is_fake': review.get('is_fake', ''),
                        'trust_score': review.get('trust_score', ''),
                    })
                
                df = pd.DataFrame(data_for_csv)
                df.to_csv(tagged_csv_path, index=False, encoding='utf-8-sig')
                _write_log(job_id, 'process', f"Saved tagged reviews CSV: {tagged_csv_path}")
            
            job['analysis_progress'] = 100
            job['phase'] = 'done'
            job['analysis_step_name'] = 'Full re-analysis completed successfully'
            _write_log(job_id, 'process', 'REANALYZE finished successfully')
            
        except Exception as e:
            import traceback
            job['phase'] = 'error'
            job['error'] = str(e)
            _write_log(job_id, 'process', f"ERROR during reanalyze: {e}")
            _write_log(job_id, 'process', traceback.format_exc())
    
    thread = threading.Thread(target=thread_fn, daemon=True)
    thread.start()
    
    return jsonify({'ok': True, 'job_id': job_id})


@bp.route('/comments/<product_id>', methods=['GET'])
def get_comments_detail(product_id: str):
    """Get detailed comments for a product with tag statistics"""
    try:
        review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
        review_file = os.path.join(review_dir, 'review.json')
        tag_stats_file = os.path.join(review_dir, 'tag_statistics.json')
        
        # Load reviews
        if not os.path.exists(review_file):
            return jsonify({'ok': False, 'error': 'Product not found'}), 404
        
        with open(review_file, 'r', encoding='utf-8') as f:
            comments = json.load(f)
        
        # Load tag statistics
        tag_stats = {}
        if os.path.exists(tag_stats_file):
            with open(tag_stats_file, 'r', encoding='utf-8') as f:
                tag_stats = json.load(f)
        
        # Ensure comments is a list
        if isinstance(comments, dict):
            comments = comments.get('reviews', [])
        
        return jsonify({
            'ok': True,
            'comments': comments,
            'tag_stats': tag_stats,
            'total': len(comments)
        })
    
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/resync/<product_id>', methods=['POST'])
def resync_laravel(product_id: str):
    job_id = uuid.uuid4().hex[:8]
    job = {
        'id': job_id,
        'product_id': product_id,
        'phase': 'done',
        'laravel_sync_status': 'sending',
        'laravel_sync_progress': 10,
    }
    JOBS[job_id] = job
    _write_log(job_id, 'process', f"RESYNC request for product {product_id}")
    ok, err = _notify_and_wait_laravel(job, product_id, force=True, max_post_retries=3, poll_seconds=120)
    if ok:
        _write_log(job_id, 'process', 'RESYNC succeeded')
        return jsonify({'ok': True, 'job_id': job_id, 'status': 'ok'})
    _write_log(job_id, 'process', f"RESYNC failed: {err}")
    return jsonify({'ok': False, 'job_id': job_id, 'error': err}), 500


# ============================================================================
# NEW ANALYSIS ENDPOINTS (v2)
# ============================================================================

@bp.route('/analyze/full', methods=['POST'])
def analyze_full():
    """Full analysis: Scrape product data + Analyze comments
    Request JSON: { "link": "https://shopee.co.id/..." }
    """
    j = request.get_json(force=True, silent=True) or request.form or {}
    link = j.get('link') if isinstance(j, dict) else None
    if not link:
        return jsonify({'error': 'missing link parameter'}), 400
    
    norm_meta = _build_canonical(link)
    norm = norm_meta['cleaned']
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        'id': job_id,
        'link': norm,
        'phase': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'scraper_progress': 0,
        'scraper_total': 0,
        'analysis_progress': 0,
        'error': None,
        'canonical': norm_meta.get('canonical'),
        'short_link': norm_meta.get('short'),
        'product_id': norm_meta.get('product_id'),
        'force_copy_browser': j.get('force_copy_browser', False),
        'mode': 'full'  # Mark as full analysis mode
    }
    
    thread = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    thread.start()
    return jsonify({'ok': True, 'job_id': job_id})


@bp.route('/analyze/scrape', methods=['POST'])
def analyze_scrape_only():
    """Scrape only: Download product data and comments, no analysis
    Request JSON: { "link": "https://shopee.co.id/..." }
    """
    j = request.get_json(force=True, silent=True) or request.form or {}
    link = j.get('link') if isinstance(j, dict) else None
    if not link:
        return jsonify({'error': 'missing link parameter'}), 400
    
    norm_meta = _build_canonical(link)
    norm = norm_meta['cleaned']
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        'id': job_id,
        'link': norm,
        'phase': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'scraper_progress': 0,
        'scraper_total': 0,
        'error': None,
        'canonical': norm_meta.get('canonical'),
        'short_link': norm_meta.get('short'),
        'product_id': norm_meta.get('product_id'),
        'force_copy_browser': j.get('force_copy_browser', False),
        'mode': 'scrape_only'  # Mark as scrape-only mode
    }
    
    def scrape_only_job(job_id: str):
        job = JOBS[job_id]
        link = job["link"]
        _write_log(job_id, "process", f"START scrape-only job for link: {link}")
        meta = _build_canonical(link)
        shopid, itemid = meta.get('shopid'), meta.get('itemid')
        product_id = f"{shopid}-{itemid}" if shopid and itemid else job_id
        job['product_id'] = product_id
        job['canonical'] = meta.get('canonical')
        job['short_link'] = meta.get('short')
        
        job["phase"] = "scraper"
        job["scraper_total"] = 0
        job["scraper_progress"] = 0
        job['scraper_state'] = 'queued'
        job['scraper_block'] = None
        
        def _scraper_progress(done, total):
            try:
                job['scraper_total'] = int(total)
                job['scraper_progress'] = int(done)
            except Exception:
                pass
        
        def _scraper_log(msg):
            _write_log(job_id, 'scraper', msg)
        
        def _scraper_state(state, block):
            job['scraper_state'] = state
            job['scraper_block'] = block
            if state in {'waiting_login','captcha'}:
                _write_log(job_id, 'process', f"SCRAPER state {state}: {block}")
        
        review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
        os.makedirs(review_dir, exist_ok=True)
        
        if job.get('force_scrape'):
            try:
                if os.path.isdir(review_dir):
                    shutil.rmtree(review_dir, ignore_errors=True)
                _write_log(job_id, 'process', 'FORCE SCRAPE: cleared previous review dir')
            except Exception as e:
                _write_log(job_id, 'process', f'FORCE SCRAPE cleanup error: {e}')
        
        try:
            reviews_count = edge_runner.run(
                link=job.get('canonical') or job.get('short_link') or link,
                shopid=shopid or '',
                itemid=itemid or '',
                out_review_dir=review_dir,
                base_dir=BASE_DIR,
                force_copy=bool(job.get('force_copy_browser')),
                progress=_scraper_progress,
                log=_scraper_log,
                state_cb=_scraper_state
            )
        except Exception as e:
            job['phase'] = 'error'
            job['error'] = f'scraper failed: {e}'
            _write_log(job_id, 'process', f"ERROR scraper failed: {e}")
            return
        
        _write_log(job_id, 'process', 'SCRAPER finished')
        job['phase'] = 'done'
        job['scraper_total'] = reviews_count
        job['scraper_progress'] = reviews_count
        _write_log(job_id, 'process', f"Scrape-only job completed: {reviews_count} comments saved")
    
    thread = threading.Thread(target=scrape_only_job, args=(job_id,), daemon=True)
    thread.start()
    return jsonify({'ok': True, 'job_id': job_id, 'message': 'Scrape-only job started'})


@bp.route('/analyze/reanalyze', methods=['POST'])
def analyze_reanalyze():
    """Re-analyze existing scraped data: Full analysis pipeline on already-scraped data
    Request JSON: { "product_id": "shopid-itemid" }
    """
    j = request.get_json(force=True, silent=True) or request.form or {}
    product_id = j.get('product_id') if isinstance(j, dict) else None
    if not product_id:
        return jsonify({'error': 'missing product_id parameter'}), 400
    
    # Check if product has been scraped
    review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
    review_file = os.path.join(review_dir, 'review.json')
    if not os.path.exists(review_file):
        return jsonify({'error': 'Product has not been scraped yet'}), 404
    
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        'id': job_id,
        'product_id': product_id,
        'phase': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'analysis_progress': 0,
        'analysis_step_index': 0,
        'analysis_steps_total': 7,
        'analysis_step_name': 'pending',
        'error': None,
        'mode': 'reanalyze_only'
    }
    
    def reanalyze_job(job_id: str):
        """Reanalyze only: Skip scraping, run full analysis pipeline on existing data"""
        job = JOBS[job_id]
        product_id = job['product_id']
        _write_log(job_id, 'process', f"START re-analyze job for product {product_id}")
        
        job['phase'] = 'analysis'
        job['analysis_progress'] = 0
        job['analysis_step_index'] = 0
        
        steps_order = [
            'init: resolve input',
            '[01] preprocess',
            '[01b] tokenize',
            '[03] sentiment',
            '[04] fake detect',
            '[05] trust score',
            '[06] summarize',
            'done'
        ]
        
        def _progress(pct, msg):
            try:
                job['analysis_progress'] = int(pct)
                if isinstance(msg, str):
                    job['analysis_step_name'] = msg
                    if msg in steps_order:
                        job['analysis_step_index'] = steps_order.index(msg) + 1
                _write_log(job_id, 'process', f"ANALYSIS {job['analysis_progress']}% :: {msg}")
            except Exception:
                pass
        
        try:
            review_dir = os.path.join(BASE_DIR, 'output', 'scrap-data', product_id)
            review_file = os.path.join(review_dir, 'review.json')
            
            if not os.path.exists(review_file):
                job['phase'] = 'error'
                job['error'] = 'Review file not found'
                _write_log(job_id, 'process', 'ERROR: review.json not found')
                return
            
            # Delete old analysis files first
            analysis_dirs_to_clean = [
                os.path.join(BASE_DIR, 'output', 'comment', product_id, 'auto'),
                os.path.join(BASE_DIR, 'output', 'comment', product_id, 'indobert'),
            ]
            
            for analysis_dir in analysis_dirs_to_clean:
                if os.path.isdir(analysis_dir):
                    try:
                        shutil.rmtree(analysis_dir)
                        _write_log(job_id, 'process', f"Deleted analysis directory: {analysis_dir}")
                    except Exception as e:
                        _write_log(job_id, 'process', f"Warning: Could not delete {analysis_dir}: {e}")
            
            # Run full pipeline
            job['analysis_step_name'] = 'Running full analysis pipeline...'
            job['analysis_progress'] = 20
            
            _write_log(job_id, 'process', f"Starting pipeline for {product_id}")
            pipeline_output_dir = pipeline.run_pipeline(
                source_dir=review_dir,
                product_id=product_id,
                backend='indobert',
                progress=_progress
            )
            
            _write_log(job_id, 'process', f"Pipeline completed, output: {pipeline_output_dir}")
            
            # Merge sentiment, fake, trust results back to review.json
            job['analysis_step_name'] = 'Merging analysis results to reviews...'
            job['analysis_progress'] = 92
            merge_ok = _merge_analysis_to_reviews(product_id, 'indobert')
            if merge_ok:
                _write_log(job_id, 'process', "Analysis results merged successfully")
            else:
                _write_log(job_id, 'process', "Warning: Could not merge analysis results")
            
            # Apply tagging
            job['analysis_step_name'] = 'Extracting and applying comment tags...'
            job['analysis_progress'] = 95
            
            with open(review_file, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
                if not isinstance(reviews, list):
                    reviews = []
            
            from utils.comment_tagger import tag_comments, get_tag_statistics
            tagged_reviews = tag_comments(reviews, source_field='comment')
            _write_log(job_id, 'process', f"Tagged {len(tagged_reviews)} reviews")
            
            # Save tagged reviews
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(tagged_reviews, f, ensure_ascii=False, indent=2)
            
            # Save tag statistics
            tag_stats = get_tag_statistics(tagged_reviews)
            stats_file = os.path.join(review_dir, 'tag_statistics.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(tag_stats, f, ensure_ascii=False, indent=2)
            
            _write_log(job_id, 'process', f"Saved tag statistics: {json.dumps(tag_stats)}")
            
            # Create tagged CSV
            analysis_dir = os.path.join(BASE_DIR, 'output', 'comment', product_id, 'indobert')
            if os.path.isdir(analysis_dir):
                tagged_csv_path = os.path.join(analysis_dir, 'review_tagged.csv')
                data_for_csv = []
                for review in tagged_reviews:
                    data_for_csv.append({
                        'comment': review.get('comment', ''),
                        'tags': ' | '.join(review.get('tags', [])),
                        'sentiment': review.get('sentiment', ''),
                        'is_fake': review.get('is_fake', ''),
                        'trust_score': review.get('trust_score', ''),
                    })
                
                df = pd.DataFrame(data_for_csv)
                df.to_csv(tagged_csv_path, index=False, encoding='utf-8-sig')
                _write_log(job_id, 'process', f"Saved tagged reviews CSV: {tagged_csv_path}")
            
            job['analysis_progress'] = 100
            job['phase'] = 'done'
            job['analysis_step_name'] = 'Re-analysis completed successfully'
            _write_log(job_id, 'process', 'RE-ANALYZE finished successfully')
            
        except Exception as e:
            import traceback
            job['phase'] = 'error'
            job['error'] = str(e)
            _write_log(job_id, 'process', f"ERROR during re-analyze: {e}")
            _write_log(job_id, 'process', traceback.format_exc())
    
    thread = threading.Thread(target=reanalyze_job, args=(job_id,), daemon=True)
    thread.start()
    return jsonify({'ok': True, 'job_id': job_id, 'message': 'Re-analyze job started'})

