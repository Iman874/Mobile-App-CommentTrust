import time
import json

def _fetch_ratings_via_driver(driver, shopid, itemid, offset=0, limit=20, timeout_ms=30000):
	js = f"""
	return fetch("https://shopee.co.id/api/v2/item/get_ratings?itemid={itemid}&shopid={shopid}&offset={offset}&limit={limit}&type=0&filter=0", {{
		method: "GET",
		headers: {{
			"accept": "application/json, text/javascript, */*; q=0.01",
			"x-requested-with": "XMLHttpRequest",
			"referer": "https://shopee.co.id/"
		}},
		credentials: "same-origin"
	}}).then(r => r.text()).then(t => {{
		try {{ return JSON.parse(t); }} catch(e) {{ return {{__text: t}}; }}
	}});
	"""
	return driver.execute_script(js)

def scrape_comments(driver, shopid, itemid, limit=20, delay=1.0, max_pages=None):
	"""Paginate ratings API via in-page fetch (inherits cookies)."""
	all_reviews = []
	offset = 0
	page_no = 0
	while True:
		page_no += 1
		data = _fetch_ratings_via_driver(driver, shopid, itemid, offset=offset, limit=limit)
		if not isinstance(data, dict):
			break
		ratings = data.get("data", {}).get("ratings") or []
		if not ratings:
			break
		all_reviews.extend(ratings)
		if len(ratings) < limit:
			break
		if (max_pages is not None) and (page_no >= max_pages):
			break
		offset += len(ratings)
		time.sleep(delay)
	return all_reviews

