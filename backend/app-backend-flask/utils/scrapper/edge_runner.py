import os
import json
import shutil
import time
import socket
import subprocess
import re
import math
from urllib.parse import urlsplit
from typing import Callable, Tuple, Optional

from . import scrapper_produk as prod
from . import scrapper_comment as comm
from . import edge_driver_helper

def _save_to_root_output(root_output_dir: str, filename: str, data, log: Callable[[str], None]):
    """Save data to root output folder, appending to existing JSON array if present."""
    try:
        output_path = os.path.join(root_output_dir, filename)
        os.makedirs(root_output_dir, exist_ok=True)
        
        # If file exists and is an array, append; otherwise create new
        if os.path.exists(output_path) and filename == 'review.json':
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if isinstance(existing, list) and isinstance(data, list):
                    existing.extend(data)
                    data = existing
            except Exception as e:
                log(f"Warning: Could not append to {filename}: {e}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"Saved to root {filename}")
    except Exception as e:
        log(f"Error saving to root {filename}: {e}")

def _paths(base_dir: str) -> Tuple[str, str, str]:
    """Return driver, cookie, working profile directory (browser-dummy/edge_profile)."""
    dummy_root = os.path.join(base_dir, 'browser-dummy')
    driver_path = os.path.join(dummy_root, 'edgedriver_win64', 'msedgedriver.exe')
    cookie_path = os.path.join(dummy_root, 'cookie.json')
    work_profile = os.path.join(dummy_root, 'edge_profile')
    return driver_path, cookie_path, work_profile

def ensure_profile_copy(base_dir: str, force_copy: bool = False) -> str:
    r"""Ensure working profile directory (user-data-dir) at browser-dummy/edge_profile.
    Behavior:
        - If force_copy: delete existing edge_profile completely, then copy the user's Edge profile 'dummy-shoope'
            from %LOCALAPPDATA%\\Microsoft\\Edge\\User Data into edge_profile preserving folder name.
        - If 'dummy-shoope' does not exist, try copying 'Default' profile as fallback.
        - If neither exists: create empty directory.
    We preserve the profile directory name inside user-data-dir (edge_profile/<profile_name>) and write origin markers.
    """
    _, _, work_profile = _paths(base_dir)
    user_data_root = os.path.join(os.environ.get('LOCALAPPDATA',''), 'Microsoft','Edge','User Data')
    dummy_profile_src = os.path.join(user_data_root, 'dummy-shoope')
    default_profile_src = os.path.join(user_data_root, 'Default')
    origin_marker = os.path.join(work_profile, 'origin.txt')
    
    if force_copy:
        if os.path.isdir(work_profile):
            shutil.rmtree(work_profile, ignore_errors=True)
        os.makedirs(work_profile, exist_ok=True)
        profile_name = None
        src_used = None
        copied_files = 0
        if os.path.isdir(dummy_profile_src):
            profile_name = 'dummy-shoope'
            target_dir = os.path.join(work_profile, profile_name)
            os.makedirs(target_dir, exist_ok=True)
            copied_files = _copy_tree(dummy_profile_src, target_dir)
            src_used = dummy_profile_src
        elif os.path.isdir(default_profile_src):
            profile_name = 'Default'
            target_dir = os.path.join(work_profile, profile_name)
            os.makedirs(target_dir, exist_ok=True)
            copied_files = _copy_tree(default_profile_src, target_dir)
            src_used = default_profile_src
        else:
            profile_name = 'EMPTY'
            src_used = 'EMPTY'
        try:
            with open(origin_marker,'w',encoding='utf-8') as f:
                f.write(f"source={src_used}\nprofile={profile_name}\nfiles={copied_files}\n")
        except Exception:
            pass
    else:
        if not os.path.isdir(work_profile):
            os.makedirs(work_profile, exist_ok=True)
            # lazy init marker
            try:
                with open(origin_marker,'w',encoding='utf-8') as f:
                    f.write("source=INIT_EMPTY\nprofile=EMPTY\nfiles=0\n")
            except Exception:
                pass
    return work_profile

def _copy_tree(src: str, dst: str):
    # robust copy with per-file fallbacks to skip locked files
    if not os.path.isdir(src):
        return 0
    count = 0
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_root = os.path.join(dst, rel) if rel != '.' else dst
        os.makedirs(target_root, exist_ok=True)
        for d in dirs:
            os.makedirs(os.path.join(target_root, d), exist_ok=True)
        for f in files:
            src_f = os.path.join(root, f)
            dst_f = os.path.join(target_root, f)
            try:
                shutil.copy2(src_f, dst_f)
                count += 1
            except Exception:
                # skip locked / in-use files
                pass
    return count


def _choose_user_profile() -> tuple[str, Optional[str], str]:
    """Choose user's Edge profile directly (no copy).
    Returns (user_data_dir, profile_name, source_desc).
    Preference order: 'dummy-shoope' -> 'Profile 8' -> 'Default' -> first 'Profile *' -> None.
    """
    user_data_root = os.path.join(os.environ.get('LOCALAPPDATA',''), 'Microsoft','Edge','User Data')
    profile_name: Optional[str] = None
    source_desc = 'user-data'
    if os.path.isdir(user_data_root):
        try:
            entries = set(os.listdir(user_data_root))
        except Exception:
            entries = set()
        # case-insensitive mapping
        lowered = {e.lower(): e for e in entries}
        for cand in ['dummy-shoope', 'Profile 8', 'Default']:
            real = lowered.get(cand.lower())
            if real and os.path.isdir(os.path.join(user_data_root, real)):
                profile_name = real
                break
        if not profile_name:
            for name in entries:
                if name.lower().startswith('profile '):
                    profile_name = name
                    break
    return user_data_root, profile_name, source_desc


def _wait_port(host: str, port: int, timeout: float = 15.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def _find_edge_binary() -> Optional[str]:
    candidates = [
        r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
        r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""), r"Microsoft\\Edge\\Application\\msedge.exe"),
    ]
    for b in candidates:
        if b and os.path.exists(b):
            return b
    return None


def _launch_edge_with_remote(user_data_dir: str, profile_name: Optional[str], port: int, log: Callable[[str], None]) -> bool:
    bin_path = _find_edge_binary()
    if not bin_path:
        log("SCRAPER cannot find msedge.exe to launch with remote debugging")
        return False
    args = [bin_path, f"--remote-debugging-port={port}", f"--user-data-dir={user_data_dir}"]
    if profile_name:
        args.append(f"--profile-directory={profile_name}")
    try:
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"SCRAPER launched Edge remote-debug with profile={profile_name} on {port}")
        return True
    except Exception as e:
        log(f"SCRAPER failed to launch Edge with remote debug: {e}")
        return False


def _make_driver(base_dir: str, user_data_dir: str, profile_name: Optional[str], log: Callable[[str], None], state_cb: Callable[[str, Optional[str]], None]):
    # Try cross-platform Edge driver helper first
    import platform
    os_mode = edge_driver_helper._detect_os_mode()
    
    if os_mode == "windows":
        # Windows: Use existing behavior with remote debugging
        log(f"SCRAPER detected Windows OS; using remote debugging approach")
        return _make_driver_windows(base_dir, user_data_dir, profile_name, log, state_cb)
    else:
        # Linux: Use direct driver initialization (may not support remote debugging)
        log(f"SCRAPER detected Linux OS; using direct driver initialization")
        return _make_driver_linux(log, state_cb)


def _make_driver_windows(base_dir: str, user_data_dir: str, profile_name: Optional[str], log: Callable[[str], None], state_cb: Callable[[str, Optional[str]], None]):
    # Use explicit driver path to avoid selenium-manager
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.edge.options import Options
    driver_path, _, _ = _paths(base_dir)
    if not os.path.exists(driver_path):
        raise FileNotFoundError(
            f"msedgedriver not found at {driver_path}. "
            f"Place it under app-backend-flask/browser-dummy/edgedriver_win64/msedgedriver.exe"
        )
    # Try to attach to existing Edge with remote debugging first
    attach_opts = Options()
    remote_port = 9222
    try:
        attach_opts.debugger_address = f"127.0.0.1:{remote_port}"
    except Exception:
        pass
    service = EdgeService(driver_path)
    # Attempt attach first
    try:
        driver = webdriver.Edge(service=service, options=attach_opts)
    except Exception:
        # Not attachable: start Edge with remote debugging using selected profile
        state_cb('launch_remote', f'Starting Edge with remote debugging ({remote_port})')
        started = _launch_edge_with_remote(user_data_dir, profile_name, remote_port, log)
        if not started:
            state_cb('profile_locked', f'Profile in use; close Edge or start Edge with --remote-debugging-port={remote_port}')
            raise
        # Wait for port then attach
        if not _wait_port('127.0.0.1', remote_port, timeout=20.0):
            # Guide user to start manually and keep waiting a bit longer
            cmd = f'"{_find_edge_binary() or "msedge"}" --remote-debugging-port={remote_port} --user-data-dir="{user_data_dir}"' + (f' --profile-directory="{profile_name}"' if profile_name else '')
            log('SCRAPER remote debugging not open yet; if a window reused an existing Edge process, please close all Edge windows for this profile and start Edge manually with:')
            log(cmd)
            state_cb('await_remote', 'Waiting for Edge remote debugging; follow instructions in logs')
            # wait up to 120s more
            if not _wait_port('127.0.0.1', remote_port, timeout=120.0):
                state_cb('profile_locked', 'Remote debugging port not reachable')
                raise RuntimeError(f'Edge remote debugging not reachable on {remote_port}')
        # update attach address in case options cached
        try:
            attach_opts.debugger_address = f"127.0.0.1:{remote_port}"
        except Exception:
            pass
        driver = webdriver.Edge(service=service, options=attach_opts)
    try:
        driver.set_window_size(1200, 900)
    except Exception:
        pass
    return driver


def _make_driver_linux(log: Callable[[str], None], state_cb: Callable[[str, Optional[str]], None]):
    """Initialize Edge driver for Linux using the cross-platform helper."""
    try:
        log("SCRAPER initializing Edge driver for Linux")
        driver = edge_driver_helper.create_edge_driver(debug=True)
        try:
            driver.set_window_size(1200, 900)
        except Exception:
            pass
        log("SCRAPER Edge driver initialized successfully on Linux")
        return driver
    except FileNotFoundError as e:
        state_cb('error', f'Edge driver or binary not found: {str(e)}')
        raise
    except PermissionError as e:
        state_cb('error', f'Permission error: {str(e)}')
        raise
    except Exception as e:
        state_cb('error', f'Failed to initialize Edge driver: {str(e)}')
        raise

def _load_cookies_into_driver(driver, cookie_path: str, log: Callable[[str], None]):
    try:
        # support alternative cookies.json filename
        candidates = [cookie_path]
        alt = os.path.join(os.path.dirname(cookie_path), 'cookies.json')
        if alt not in candidates:
            candidates.append(alt)
        selected = None
        for c in candidates:
            if os.path.exists(c):
                selected = c
                break
        if not selected:
            log(f"SCRAPER cookie file not found (tried: {', '.join(candidates)})")
            return
        with open(selected, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cookies = []
        if isinstance(data, dict) and 'cookies' in data:
            cookies = data['cookies']
        elif isinstance(data, list):
            cookies = data
        elif isinstance(data, dict):
            # map name->value form
            cookies = [{"name": k, "value": str(v), "domain": ".shopee.co.id", "path": "/"} for k,v in data.items()]
        # must be on domain before adding cookies
        driver.get("https://shopee.co.id/")
        time.sleep(1)
        added = 0
        for c in cookies:
            try:
                c2 = {k: c[k] for k in c if k in {"name","value","domain","path","expiry","secure","httpOnly"}}
                if "domain" not in c2:
                    c2["domain"] = ".shopee.co.id"
                if "path" not in c2:
                    c2["path"] = "/"
                driver.add_cookie(c2)
                added += 1
            except Exception:
                # ignore individual failures
                pass
        log(f"SCRAPER injected {added} cookies from {os.path.basename(selected)} into session")
    except Exception as e:
        log(f"SCRAPER cookie injection error: {e}")

def _is_logged_in(driver) -> bool:
    """Heuristic login detection via presence of common auth cookies."""
    try:
        cookies = driver.get_cookies() or []
        for c in cookies:
            if c.get('name') in {'SPC_EC','SPC_U','SPC_F'}:
                return True
    except Exception:
        pass
    return False

def _url_indicates_captcha(url: str) -> bool:
    u = (url or '').lower()
    if not u:
        return False
    patterns = [
        'captcha', 'verify', 'challenge', 'areyouhuman', 'are-you-human',
        'antibot', 'anti-bot', 'security', 'accessdenied', 'access-denied'
    ]
    if any(p in u for p in patterns):
        # restrict to common hosts too, but keep generic
        return True
    return False

def _dom_indicates_captcha(driver) -> bool:
    try:
        html = (driver.page_source or '').lower()
        if any(k in html for k in ['captcha', 'i\'m not a robot', 'saya bukan robot', 'hcaptcha', 'recaptcha', 'klik untuk verifikasi']):
            return True
        # quick iframe check via JS to avoid large HTML scanning repeatedly
        try:
            frames = driver.execute_script("return Array.from(document.querySelectorAll('iframe')).map(f=>f.src||'');") or []
            frames_l = [str(x).lower() for x in frames]
            if any('captcha' in x or 'recaptcha' in x or 'hcaptcha' in x for x in frames_l):
                return True
        except Exception:
            pass
    except Exception:
        pass
    return False

def _get_all_tabs(driver):
    tabs = []
    try:
        current = driver.current_window_handle
    except Exception:
        current = None
    handles = []
    try:
        handles = list(driver.window_handles)
    except Exception:
        handles = []
    for h in handles:
        try:
            driver.switch_to.window(h)
            url = ''
            title = ''
            try:
                url = driver.current_url or ''
            except Exception:
                url = ''
            try:
                title = driver.title or ''
            except Exception:
                title = ''
            tabs.append((h, url, title))
        except Exception:
            continue
    # restore focus
    if current:
        try:
            driver.switch_to.window(current)
        except Exception:
            pass
    return tabs

def _has_captcha_any_tab(driver) -> bool:
    # True if any tab URL/DOM clearly shows captcha/challenge
    tabs = _get_all_tabs(driver)
    for h, url, title in tabs:
        if _url_indicates_captcha(url):
            return True
    # If URLs don't show it, try DOM of current tab only (avoid switching costs)
    return _dom_indicates_captcha(driver)

def _product_token_from_link(link: str, shopid: str, itemid: str) -> Optional[str]:
    # Shopee product links often contain "-i.<shop>.<item>"; use that for robust detection
    try:
        m = re.search(r"-i\.(\d+)\.(\d+)", link)
        if m:
            return f"i.{m.group(1)}.{m.group(2)}"
    except Exception:
        pass
    if shopid and itemid:
        return f"i.{shopid}.{itemid}"
    return None

def _find_tab_with_product(driver, token: Optional[str], fallback_url: Optional[str] = None) -> Optional[str]:
    if not token and not fallback_url:
        return None
    tabs = _get_all_tabs(driver)
    # prefer token match
    if token:
        for h, url, _ in tabs:
            if token in (url or ''):
                return h
    # fallback: host/path similarity
    if fallback_url:
        try:
            t = urlsplit(fallback_url)
            for h, url, _ in tabs:
                u = urlsplit(url)
                if u.netloc.endswith('shopee.co.id') and t.path.split('/')[:2] == u.path.split('/')[:2]:
                    return h
        except Exception:
            pass
    return None

def run(link: str, shopid: str, itemid: str, out_review_dir: str, base_dir: str, force_copy: bool,
    progress: Callable[[int, int], None], log: Callable[[str], None], state_cb: Callable[[str, Optional[str]], None] = lambda s,m: None):
    os.makedirs(out_review_dir, exist_ok=True)
    # choose user Edge profile directly (no copying)
    user_data_dir, prof_name, src_desc = _choose_user_profile()
    log(f"SCRAPER using user profile: user-data={user_data_dir} profile={prof_name}")
    state_cb('starting', None)
    # start driver (attach/launch remote)
    driver = _make_driver(base_dir, user_data_dir, prof_name, log, state_cb)
    try:
        # cookies
        _, cookie_path, _ = _paths(base_dir)
        _load_cookies_into_driver(driver, cookie_path, log)
        # Navigate to product immediately; then wait states based on open tabs
        product_url = link or f"https://shopee.co.id/product/{shopid}/{itemid}"
        token = _product_token_from_link(product_url, shopid, itemid)
        state_cb('navigate_product', None)
        driver.get(product_url)
        time.sleep(0.5)

        # Unified wait loop: consider solved if product tab opens, even if a captcha tab remains
        start_wait = time.time()
        cap_notified = 0
        login_notified = 0
        while True:
            prod_tab = _find_tab_with_product(driver, token, product_url)
            if prod_tab:
                try:
                    driver.switch_to.window(prod_tab)
                except Exception:
                    pass
                state_cb('product_open', 'Halaman produk terbuka — lanjut scraping')
                log('SCRAPER product tab detected; proceeding')
                break

            if _has_captcha_any_tab(driver):
                state_cb('captcha', 'Captcha terdeteksi — selesaikan secara manual di tab baru')
                if cap_notified % 5 == 0:
                    log('SCRAPER captcha detected; waiting user solve...')
                cap_notified += 1
            elif not _is_logged_in(driver):
                state_cb('waiting_login', 'Belum login — silakan login di jendela Edge')
                if login_notified % 5 == 0:
                    log('SCRAPER waiting for manual login...')
                login_notified += 1
            else:
                # logged in and no captcha detected, but product tab not found — re-navigate
                try:
                    driver.get(product_url)
                except Exception:
                    pass

            if time.time() - start_wait > 240:
                raise RuntimeError('Timeout menunggu login/captcha atau halaman produk')
            time.sleep(2)

        # fetch product with retries
        state_cb('fetch_product', None)
        log("SCRAPER fetch product data")
        prod_data = None
        for attempt in range(1, 2):
            try:
                prod_data = prod.scrape_product(driver, shopid, itemid)
                if prod_data:
                    break
                else:
                    raise RuntimeError('empty product data')
            except Exception as e:
                state_cb('retry_product', f'Gagal ambil data produk; coba lagi ({attempt}/2)')
                log(f"SCRAPER product fetch failed (attempt {attempt}/2): {e}")
                time.sleep(min(1 + attempt, 2))
        if not prod_data:
            log('SCRAPER product fetch failed after 2 attempts; lanjut komentar')
            prod_data = {}
        with open(os.path.join(out_review_dir, 'product.json'), 'w', encoding='utf-8') as f:
            json.dump(prod_data, f, ensure_ascii=False, indent=2)

        # estimate total ratings if available
        total_reviews = 0
        try:
            # various possible fields
            if isinstance(prod_data, dict):
                if 'item_rating' in prod_data and isinstance(prod_data['item_rating'], dict):
                    rc = prod_data['item_rating'].get('rating_count')
                    if isinstance(rc, list):
                        total_reviews = sum(int(x) for x in rc if isinstance(x, (int,float)))
                    elif isinstance(rc, (int,float)):
                        total_reviews = int(rc)
                elif 'data' in prod_data and isinstance(prod_data['data'], dict):
                    rc = prod_data['data'].get('rating_count')
                    if isinstance(rc, list):
                        total_reviews = sum(int(x) for x in rc if isinstance(x, (int,float)))
        except Exception:
            total_reviews = 0
        if total_reviews <= 0:
            total_reviews = 200  # fallback estimate for UI
        progress(0, total_reviews)

        # fetch comments paginated with per-page retries
        state_cb('fetch_comments', None)
        log("SCRAPER fetch comments")
        all_reviews = []
        limit = 20
        # Precompute an upper bound of pages to avoid infinite loops
        total_pages = math.ceil(total_reviews / limit) if total_reviews > 0 else None
        offset = 0
        page = 0
        while True:
            page += 1
            ratings = []
            fetch_ok = False
            for attempt in range(1, 2):
                try:
                    data = comm._fetch_ratings_via_driver(driver, shopid, itemid, offset=offset, limit=limit)
                    if isinstance(data, dict):
                        ratings = (data.get('data') or {}).get('ratings') or []
                    else:
                        ratings = []
                    if ratings:
                        fetch_ok = True
                        break
                    else:
                        raise RuntimeError('empty ratings')
                except Exception as e:
                    state_cb('retry_comments', f'Halaman {page}: coba lagi ({attempt}/2)')
                    log(f"SCRAPER ratings fetch page {page} offset {offset} failed (attempt {attempt}/2): {e}")
                    time.sleep(min(1 + attempt, 2))
            if not fetch_ok:
                # gagal 2x, lanjut ke halaman berikutnya sesuai instruksi
                log(f"SCRAPER skip page {page} after 2 failures; lanjut halaman berikutnya")
                offset += limit
                # Stop when reaching or passing the last page estimate
                if (total_pages is not None and page >= total_pages) or offset >= total_reviews:
                    log(f"SCRAPER reached last page without data; stopping at page {page}")
                    break
                # Additional hard guard to avoid runaway loops in case of bad estimates
                if page > 100:
                    log("SCRAPER page cap reached (100); stopping to avoid infinite loop")
                    break
                continue

            all_reviews.extend(ratings)
            progress(len(all_reviews), total_reviews)
            log(f"SCRAPER page {page}: collected {len(all_reviews)}/{total_reviews}")
            if len(ratings) < limit:
                break
            offset += len(ratings)
            time.sleep(0.1)

        # write outputs expected by pipeline (list is accepted)
        with open(os.path.join(out_review_dir, 'review.json'), 'w', encoding='utf-8') as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)
        
        state_cb('done', None)
        log(f"SCRAPER finished; total {len(all_reviews)} reviews saved")
        return len(all_reviews)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
