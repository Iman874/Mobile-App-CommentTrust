import json
import os
from playwright.sync_api import sync_playwright

def load_cookies(storage_path):
    with open(storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Support format: {"cookies": [...]}
    cookies = data["cookies"] if isinstance(data, dict) and "cookies" in data else data
    return cookies

def set_cookies_to_context(context, cookies):
    # Playwright expects cookies to have 'name', 'value', 'domain', 'path'
    valid_cookies = []
    for c in cookies:
        if "name" in c and "value" in c and "domain" in c:
            # Ensure 'sameSite' is valid
            same_site = c.get("sameSite", "Lax")
            if same_site not in ("Strict", "Lax", "None"):
                same_site = "Lax"
            c["sameSite"] = same_site
            valid_cookies.append(c)
    context.add_cookies(valid_cookies)

def download_shopee_html(url, storage_path, out_folder):
    os.makedirs(out_folder, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        # Set cookies
        cookies = load_cookies(storage_path)
        set_cookies_to_context(context, cookies)
        page = context.new_page()
        page.goto(url)
        input("[!] Jika halaman sudah terbuka dan tidak captcha, tekan ENTER di sini...")
        html = page.content()
        # Simpan HTML
        filename = url.split("/")[-1].split("?")[0] or "shopee_page"
        out_path = os.path.join(out_folder, f"{filename}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[+] HTML halaman Shopee disimpan di: {out_path}")
        browser.close()

if __name__ == "__main__":
    # Contoh penggunaan
    url = input("Masukkan URL produk Shopee: ").strip()
    storage_path = "shopee_storage.json"  # Path ke file cookies
    out_folder = "html"
    download_shopee_html(url, storage_path, out_folder)