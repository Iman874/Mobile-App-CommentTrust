import os
import json
from bs4 import BeautifulSoup

def parse_comments_from_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    comments = []
    # Cari semua elemen yang kemungkinan berisi komentar Shopee
    # Biasanya di div dengan class mengandung "shopee-product-rating" atau "product-ratings"
    for rating_div in soup.find_all("div", class_=lambda c: c and ("product-ratings" in c or "shopee-product-rating" in c)):
        # User
        user = ""
        user_tag = rating_div.find("div", class_=lambda c: c and ("username" in c or "user" in c))
        if user_tag:
            user = user_tag.get_text(strip=True)
        # Rating
        rating = None
        rating_tag = rating_div.find("div", class_=lambda c: c and ("rating" in c or "star" in c))
        if rating_tag:
            try:
                rating = float(rating_tag.get_text(strip=True).replace(",", "."))
            except:
                rating = None
        # Comment
        comment = ""
        comment_tag = rating_div.find("div", class_=lambda c: c and ("comment" in c or "content" in c or "text" in c))
        if comment_tag:
            comment = comment_tag.get_text(strip=True)
        # Media
        has_media = False
        media_tag = rating_div.find(lambda tag: tag.name in ["img", "video"])
        if media_tag:
            has_media = True
        # Fallback jika tidak ketemu, ambil text dari rating_div
        if not comment:
            comment = rating_div.get_text(" ", strip=True)
        # Simpan jika ada komentar
        if comment and user:
            comments.append({
                "user": user,
                "rating": rating,
                "comment": comment,
                "has_media": has_media
            })
    # Jika tidak ketemu, coba cari pola di seluruh HTML
    if not comments:
        for div in soup.find_all("div"):
            text = div.get_text(" ", strip=True)
            # Cari pola username, rating, komentar, media
            if "Laporkan" in text and "|" in text:
                user = ""
                rating = None
                comment = ""
                has_media = False
                # User: ambil sebelum tanggal
                user_split = text.split("|")[0].strip()
                user = user_split.split(" ")[0]
                # Rating: cari angka 1-5
                rating_search = [float(s.replace(",", ".")) for s in text.split() if s.replace(",", ".").replace(".", "", 1).isdigit() and 1 <= float(s.replace(",", ".")) <= 5]
                rating = rating_search[0] if rating_search else None
                # Comment: ambil setelah "Fitur Terbaik:" atau setelah "|"
                comment = text.split("|")[-1].split("Laporkan")[0].strip()
                # Media: cek ada kata 'video', 'gambar', 'foto'
                has_media = any(x in text.lower() for x in ["video", "gambar", "foto"])
                comments.append({
                    "user": user,
                    "rating": rating,
                    "comment": comment,
                    "has_media": has_media
                })
    return comments

def parse_comments_from_multiple_html(html_files):
    all_comments = []
    for html_path in html_files:
        comments = parse_comments_from_html(html_path)
        all_comments.extend(comments)
    return all_comments

if __name__ == "__main__":
    html_path = "html/42165231468.html"
    out_folder = "comment"
    os.makedirs(out_folder, exist_ok=True)
    out_path = os.path.join(out_folder, "42165231468.json")
    comments = parse_comments_from_html(html_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"[+] Hasil parsing komentar Shopee disimpan di: {out_path}")

    # Contoh: parsing semua file HTML hasil paging
    html_folder = "html"
    html_files = [os.path.join(html_folder, f) for f in os.listdir(html_folder) if f.startswith("42165231468") and f.endswith(".html")]
    out_folder = "comment"
    os.makedirs(out_folder, exist_ok=True)
    out_path = os.path.join(out_folder, "42165231468.json")
    comments = parse_comments_from_multiple_html(html_files)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"[+] Hasil parsing semua komentar Shopee (paging) disimpan di: {out_path}")

# --- Tambahan: cara scraping semua komentar Shopee dengan Playwright ---
"""
Tips untuk scraping semua komentar Shopee:
1. Gunakan Playwright/Selenium untuk membuka halaman produk Shopee.
2. Scroll ke bawah secara otomatis sampai semua komentar/review termuat.
3. Setelah semua komentar termuat, ambil page.content() dan simpan ke HTML.
4. Lakukan parsing seperti biasa.

Contoh auto-scroll dengan Playwright:
-------------------------------------------------
from playwright.sync_api import sync_playwright
import time

def download_full_shopee_html(url, storage_path, out_folder):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        # ...set cookies seperti sebelumnya...
        page = context.new_page()
        page.goto(url)
        # Scroll ke bawah sampai semua komentar/review termuat
        last_height = 0
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        html = page.content()
        # ...simpan html seperti biasa...
        browser.close()
-------------------------------------------------
Setelah itu, parsing seperti biasa.

Catatan:
- Shopee membatasi jumlah komentar yang bisa di-load, jadi untuk ribuan komentar, scraping API Shopee lebih efisien (perlu teknik lanjutan).
- Untuk scraping legal dan etis, jangan terlalu sering request dan jangan scrape data user tanpa izin.
"""
