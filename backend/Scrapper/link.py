import sys
import json
import time
import argparse
import re
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

def extract_shop_and_ids(url: str):
    s = unquote(url)
    # try patterns that include shopname
    m = re.search(r"/([^/]+)-i\.(\d+)\.(\d+)", s)
    if m:
        return m.group(1), m.group(2), m.group(3)
    m = re.search(r"/([^/]+)/(\d+)/(\d+)", s)
    if m:
        return m.group(1), m.group(2), m.group(3)
    # fallback patterns without shopname
    m = re.search(r"-i\.(\d+)\.(\d+)", s)
    if m:
        return None, m.group(1), m.group(2)
    nums = re.findall(r"\d{5,}", s)
    if len(nums) >= 2:
        return None, nums[-2], nums[-1]
    return None, None, None

def canonical_product_url(shopname, shopid, itemid):
    if shopid and itemid:
        if shopname:
            return f"https://shopee.co.id/{shopname}-i.{shopid}.{itemid}"
        return f"https://shopee.co.id/-i.{shopid}.{itemid}"
    return None

def expand_shopee_link(short_url: str, headless: bool = False, timeout: int = 30):
    """
    Open short_url in Playwright, follow redirects, try to extract shopname/shopid/itemid.
    Return dict with expanded_url, canonical_url, shopname, shopid, itemid.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport={"width":1280,"height":800})
        page = ctx.new_page()
        try:
            try:
                page.goto(short_url, wait_until="networkidle", timeout=timeout*1000)
            except PWTimeoutError:
                try:
                    page.goto(short_url, wait_until="load", timeout=timeout*1000)
                except Exception:
                    pass

            time.sleep(0.5)
            cur = page.url or short_url

            # if still on short domain, attempt to click anchor to full shopee link
            parsed = urlparse(cur)
            if parsed.netloc and ("s.shopee" in parsed.netloc or parsed.netloc.startswith("s.")):
                try:
                    href = page.eval_on_selector("a[href*='shopee.co']", "el => el.href", timeout=2000)
                except Exception:
                    href = None
                if href:
                    try:
                        page.goto(href, wait_until="networkidle", timeout=timeout*1000)
                        time.sleep(0.4)
                        cur = page.url
                    except Exception:
                        pass

            expanded = cur

            # try direct extraction from URL
            shopname, shopid, itemid = extract_shop_and_ids(expanded)

            # if no shopname, try to find a path in page content that includes it
            if (not shopname) and expanded:
                try:
                    content = page.content() or ""
                    # look for patterns like /opaanlp-i.897415298.41461232589 in page HTML
                    m = re.search(r"/([A-Za-z0-9%_.\-]+)-i\.(\d+)\.(\d+)", content)
                    if m:
                        shopname, shopid, itemid = m.group(1), m.group(2), m.group(3)
                except Exception:
                    pass

            # if still no shopname, check meta og:url
            if (not shopname):
                try:
                    og = page.eval_on_selector("meta[property='og:url']", "el => el.content", timeout=1000)
                    if og:
                        sn, sid, iid = extract_shop_and_ids(og)
                        if sid and iid:
                            shopname = sn
                            shopid = sid
                            itemid = iid
                            expanded = og
                except Exception:
                    pass

            # try NEXT_DATA or global JS objects for shop username if missing
            if (not shopname):
                try:
                    # return stringified NEXT_DATA if present
                    nd = page.evaluate("typeof window.__NEXT_DATA__ !== 'undefined' ? JSON.stringify(window.__NEXT_DATA__) : ''")
                    if nd:
                        m = re.search(r'"shop_name"\s*:\s*"([^"]+)"', nd)
                        if not m:
                            m = re.search(r'"shop_username"\s*:\s*"([^"]+)"', nd)
                        if m:
                            candidate = m.group(1)
                            # verify it pairs with ids
                            ids = extract_shop_and_ids(nd)
                            if ids[1] == shopid and ids[2] == itemid:
                                shopname = candidate
                    # also try other globals
                except Exception:
                    pass

            canon = canonical_product_url(shopname, shopid, itemid)

            return {
                "short_url": short_url,
                "expanded_url": expanded,
                "canonical_url": canon,
                "shopname": shopname,
                "shopid": shopid,
                "itemid": itemid
            }
        finally:
            try:
                ctx.close()
                browser.close()
            except Exception:
                pass

def cli():
    p = argparse.ArgumentParser(description="Expand Shopee short/share URL to product URL + extract ids")
    p.add_argument("url", help="Short Shopee URL (e.g. https://s.shopee.co.id/...)")
    p.add_argument("--headless", action="store_true", help="Run browser headless")
    p.add_argument("--timeout", type=int, default=30, help="Navigation timeout (seconds)")
    args = p.parse_args()
    out = expand_shopee_link(args.url, headless=args.headless, timeout=args.timeout)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    cli()
