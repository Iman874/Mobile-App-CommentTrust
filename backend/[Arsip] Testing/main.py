#!/usr/bin/env python3
"""
shopee_api_reviews.py

Usage examples:
  # 1) Pakai storage_state (Playwright / Chrome) yang sudah kamu simpan:
  python shopee_api_reviews.py "https://shopee.co.id/...-i.919692407.23228047103" reviews.csv --storage shopee_storage.json

  # 2) Atau pakai cookie string (copy dari DevTools -> Application -> Cookies):
  python shopee_api_reviews.py "https://shopee.co.id/...-i.919692407.23228047103" reviews.csv --cookie "csrftoken=...; SPC_EC=...; ..."

  # 3) Jika perlu gunakan proxy (residential Indonesia):
  python shopee_api_reviews.py <url> out.csv --cookie "..." --proxy "http://user:pass@ip:port"

Notes:
  - Jika mendapat 403/401, refresh login (ambil cookie baru) atau coba proxy Indonesia.
  - Script ini untuk keperluan riset/dev. Jangan gunakan untuk abuse/crawling besar-besaran.
"""

import argparse, json, re, time, csv, sys
from urllib.parse import unquote
import requests

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://shopee.co.id/",
}

def extract_ids(url: str):
    s = unquote(url)
    patterns = [
        r"-i\.(\d+)\.(\d+)",
        r"i\.(\d+)\.(\d+)",
        r"/product[s]?/(\d+)/(\d+)",
        r"/(\d{5,})/(\d{5,})",
        r"(\d{5,})\.(\d{5,})",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            return m.group(1), m.group(2)
    nums = re.findall(r"\d{5,}", s)
    if len(nums) >= 2:
        return nums[-2], nums[-1]
    return None, None

def session_from_storage(storage_path, headers=None, proxies=None):
    headers = headers or HEADERS_BASE.copy()
    with open(storage_path, "r", encoding="utf-8") as f:
        store = json.load(f)
    cookies = store.get("cookies", [])
    s = requests.Session()
    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        domain = c.get("domain")
        path = c.get("path", "/")
        if name and value:
            # requests cookie jar will accept domain/path
            s.cookies.set(name, value, domain=domain, path=path)
    s.headers.update(headers)
    if proxies:
        s.proxies.update(proxies)
    return s

def session_from_cookie_string(cookie_string, headers=None, proxies=None):
    headers = headers or HEADERS_BASE.copy()
    s = requests.Session()
    # cookie_string like: "csrftoken=xxx; SPC_EC=yyy; ..."
    cookies = [c.strip() for c in cookie_string.split(";") if c.strip()]
    for c in cookies:
        if "=" in c:
            k,v = c.split("=",1)
            # domain unspecified; leave domain empty (requests will send cookie for host)
            s.cookies.set(k.strip(), v.strip())
    s.headers.update(headers)
    if proxies:
        s.proxies.update(proxies)
    return s

def fetch_ratings_page(session, shop_id, item_id, offset=0, limit=20, timeout=20):
    url = f"https://shopee.co.id/api/v2/item/get_ratings"
    params = {
        "filter": 0,
        "flag": 1,
        "itemid": item_id,
        "limit": limit,
        "offset": offset,
        "shopid": shop_id,
        "type": 0
    }
    r = session.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def collect_all_reviews(session, shop_id, item_id, out_csv, limit=20, delay=0.8, max_pages=10000):
    all_rows = []
    offset = 0
    page_no = 0
    while page_no < max_pages:
        page_no += 1
        try:
            data = fetch_ratings_page(session, shop_id, item_id, offset=offset, limit=limit)
        except requests.HTTPError as e:
            code = getattr(e.response, "status_code", None)
            print(f"\n[!] HTTP error {code}: {e}. Stopping.", file=sys.stderr)
            break
        except Exception as e:
            print(f"\n[!] Error fetching page: {e}. Stopping.", file=sys.stderr)
            break

        ratings = data.get("data", {}).get("ratings", [])
        if not ratings:
            break

        for r in ratings:
            all_rows.append({
                "username": r.get("author_username") or "",
                "comment": r.get("comment") or "",
                "rating_star": r.get("rating_star") or 0,
                "create_time": r.get("ctime") or "",
                "orderid": r.get("orderid") or "",
                "is_image": bool(r.get("images")),
                "images_count": len(r.get("images") or []),
            })

        offset += len(ratings)
        print(f"Fetched {len(all_rows)} reviews... (offset {offset})", end="\r")
        time.sleep(delay)

    print()
    if all_rows:
        keys = list(all_rows[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"[+] Saved {len(all_rows)} reviews to {out_csv}")
    else:
        print("[-] No reviews collected. Check product URL, cookies, or proxy.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("product_url", help="Full product URL (shortlink or full)")
    p.add_argument("out_csv", help="Output CSV path")
    p.add_argument("--storage", help="Path to Playwright storage_state json (optional)")
    p.add_argument("--cookie", help="Cookie string copied from browser (optional)")
    p.add_argument("--proxy", help="Proxy URL like http://user:pass@ip:port (optional)")
    p.add_argument("--limit", type=int, default=20, help="limit per page (default 20)")
    p.add_argument("--delay", type=float, default=0.8, help="delay between pages (seconds)")
    args = p.parse_args()

    shop_id, item_id = extract_ids(args.product_url)
    if not (shop_id and item_id):
        print("[-] Gagal ekstrak shop_id/item_id dari URL. Pastikan URL full product (format ...-i.<shopid>.<itemid>).")
        return

    proxies = None
    if args.proxy:
        proxies = {"http": args.proxy, "https": args.proxy}

    if args.storage:
        try:
            session = session_from_storage(args.storage, proxies=proxies)
        except Exception as e:
            print("[!] Gagal buat session dari storage:", e)
            return
    elif args.cookie:
        session = session_from_cookie_string(args.cookie, proxies=proxies)
    else:
        print("[-] Butuh --storage atau --cookie untuk otorisasi. Lihat help.")
        return

    # quick test: call a small request to check auth
    try:
        print("[*] Test request ke ratings endpoint...")
        test = fetch_ratings_page(session, shop_id, item_id, offset=0, limit=1)
        if not isinstance(test, dict):
            print("[!] Response tidak seperti yang diharapkan:", test)
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", None)
        print(f"[!] Test request failed HTTP {code}. Jika 403/401 -> cookie invalid atau perlu proxy.")
        return
    except Exception as e:
        print("[!] Test request error:", e)
        return

    collect_all_reviews(session, shop_id, item_id, args.out_csv, limit=args.limit, delay=args.delay)

if __name__ == "__main__":
    main()
