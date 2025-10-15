import json
import time


def _fetch_api_in_page(driver, url):
    js = f"""
    return fetch("{url}", {{
        method: "GET",
        headers: {{
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
            "referer": "https://shopee.co.id/"
        }},
        credentials: "same-origin"
    }}).then(r => r.text()).then(t => {{
        try {{ return JSON.parse(t); }} catch(e) {{ return {{__text: t}}; }}
    }}).catch(e => ({{__error: String(e)}}));
    """
    try:
        return driver.execute_script(js)
    except Exception as e:
        return {"__error": str(e)}


def _recursive_search(obj, match_fn):
    if isinstance(obj, dict):
        if match_fn(obj):
            return obj
        for v in obj.values():
            found = _recursive_search(v, match_fn)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _recursive_search(item, match_fn)
            if found is not None:
                return found
    return None


def _extract_product_from_embedded(driver, shopid, itemid):
    # try several global places and script tags
    probes = [
        "return (typeof window.__PRELOADED_STATE__ !== 'undefined') ? window.__PRELOADED_STATE__ : null;",
        "return (typeof window.__SHOPEE_REDUX_INITIAL_STATE__ !== 'undefined') ? window.__SHOPEE_REDUX_INITIAL_STATE__ : null;",
        "return (typeof window.__INITIAL_STATE__ !== 'undefined') ? window.__INITIAL_STATE__ : null;",
        "return (typeof window.__NEXT_DATA__ !== 'undefined') ? window.__NEXT_DATA__ : null;"
    ]
    for p in probes:
        try:
            obj = driver.execute_script(p)
        except Exception:
            obj = None
        if obj:
            # try to find an object that looks like the item (has itemid or item_basic)
            def match(o):
                if not isinstance(o, dict):
                    return False
                if "itemid" in o and str(o.get("itemid")) == str(itemid):
                    return True
                if "item_basic" in o and isinstance(o["item_basic"], dict) and str(o["item_basic"].get("itemid")) == str(itemid):
                    return True
                if "item" in o and isinstance(o["item"], dict) and str(o["item"].get("itemid")) == str(itemid):
                    return True
                return False
            found = _recursive_search(obj, match)
            if found:
                return found
    # try ld+json or NEXT_DATA script tags
    try:
        scripts = driver.execute_script("""
            var out = [];
            document.querySelectorAll('script[type="application/ld+json"], script[id="__NEXT_DATA__"]').forEach(s=>out.push(s.textContent));
            return out;
        """)
        if scripts:
            for txt in scripts:
                if not txt:
                    continue
                try:
                    parsed = json.loads(txt)
                except Exception:
                    continue
                found = _recursive_search(parsed, lambda o: isinstance(o, dict) and ("itemid" in o and str(o.get("itemid")) == str(itemid)))
                if found:
                    return found
    except Exception:
        pass
    return None


def _meta_fallback(driver):
    try:
        meta = driver.execute_script("""
            return {
                title: document.querySelector('meta[property=\"og:title\"]')?.content || document.title || null,
                description: document.querySelector('meta[property=\"og:description\"]')?.content || document.querySelector('meta[name=\"description\"]')?.content || null,
                image: document.querySelector('meta[property=\"og:image\"]')?.content || null,
                url: document.querySelector('meta[property=\"og:url\"]')?.content || location.href
            };
        """)
        return meta
    except Exception as e:
        return {"error": "meta_extract_failed", "message": str(e)}


def scrape_product(driver, shopid, itemid, timeout_ms=30000):
    """
    Robust product fetch: try API endpoints first, then embedded JSON (NEXT_DATA / redux), then meta tags.
    Returns a dict with product info (best effort) or dict with error key.
    """
    base = "https://shopee.co.id"
    endpoints = [
        f"{base}/api/v2/item/get?itemid={itemid}&shopid={shopid}",
        f"{base}/api/v4/item/get?itemid={itemid}&shopid={shopid}",
        f"{base}/api/v2/item/get?itemid={itemid}&shopid={shopid}&limit=0"  # slight variant
    ]

    # 1) Try API endpoints
    for url in endpoints:
        try:
            res = _fetch_api_in_page(driver, url)
        except Exception as e:
            res = {"__error": str(e)}
        if not res:
            continue
        # handle API wrapper
        if isinstance(res, dict) and "__error" in res:
            # network/exec error; try next
            continue
        # unwrap __text
        if isinstance(res, dict) and "__text" in res:
            try:
                parsed = json.loads(res["__text"])
                res = parsed
            except Exception:
                # leave as-is
                pass
        if isinstance(res, dict):
            # prefer res['data']
            if "data" in res and isinstance(res["data"], dict) and res["data"]:
                return res["data"]
            # direct item
            if "item" in res and isinstance(res["item"], dict):
                return res["item"]
            if "item_basic" in res and isinstance(res["item_basic"], dict):
                return res["item_basic"]
        # if we got raw JSON that looks like product, return it
        # else continue to next endpoint

    # 2) Try embedded page data (NEXT_DATA / redux state / ld+json)
    try:
        embedded = _extract_product_from_embedded(driver, shopid, itemid)
        if embedded:
            return embedded
    except Exception as e:
        # keep trying to fallback
        pass

    # 3) Meta tags fallback
    meta = _meta_fallback(driver)
    if meta:
        return {"source": "meta", "meta": meta}

    return {"error": "error_not_found", "shopid": shopid, "itemid": itemid}
