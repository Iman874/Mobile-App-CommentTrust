# main_edge.py
import json, time, re
import os
import sys
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import subprocess
import shutil
import tempfile
import atexit

# Import modular scrapers (must be in same folder)
try:
    from scrapper_comment import scrape_comments
    from scrapper_produk import scrape_product
except Exception as _e:
    print(f"[!] Gagal mengimpor modul scrapper: {_e}")
    print("    Pastikan file scrapper_comment.py dan scrapper_produk.py berada di folder yang sama dan tidak mengandung error.")
    sys.exit(1)

# ===== Konfigurasi produk Shopee =====
PRODUCT_URL = "https://shopee.co.id/opaanlp-i.897415298.41461232589"
LIMIT = 20
# set to None to fetch all pages until API returns no more ratings
MAX_PAGES = None
DELAY = 1.0

# new: import expand helper if available
try:
	from link import expand_shopee_link
except Exception:
	expand_shopee_link = None

# prompt user for product URL (overrides default)
user_input = input("Enter Shopee product URL (full or short share URL) [leave empty to use default]: ").strip()
if user_input:
	PRODUCT_URL = user_input
	# if short share link, try to expand using link.py (if available)
	if ("s.shopee" in PRODUCT_URL or PRODUCT_URL.startswith("https://s.")) and expand_shopee_link:
		try:
			info = expand_shopee_link(PRODUCT_URL, headless=False, timeout=30)
			PRODUCT_URL = info.get("canonical_url") or info.get("expanded_url") or PRODUCT_URL
			print(f"[>] Expanded short link -> {PRODUCT_URL}")
		except Exception as e:
			print(f"[!] Failed to expand short link: {e}; proceeding with provided URL.")

# ===== Ambil shopid dan itemid dari URL =====
def extract_ids(url):
    m = re.search(r"i\.(\d+)\.(\d+)", url)
    if m:
        return m.group(1), m.group(2)
    nums = re.findall(r"\d{5,}", url)
    if len(nums) >= 2:
        return nums[-2], nums[-1]
    return None, None

shopid, itemid = extract_ids(PRODUCT_URL)
if not (shopid and itemid):
    raise SystemExit("❌ Gagal ekstrak shopid/itemid dari URL")

# ===== Setup koneksi ke Edge (CDP) =====
opts = Options()
# Gunakan Edge yang sudah dibuka dengan port debugging (9222)
REMOTE_DEBUG_ADDRESS = "127.0.0.1:9222"

# Prefer edgedriver lokal di folder repository (relative ke file ini)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOCAL_DRIVER = os.path.join(BASE_DIR, "edgedriver_win64", "msedgedriver.exe")
# jika Anda sudah set variabel ini ke path lain, itu tetap dipakai; jika tidak, gunakan default lokal bila ada
EDGE_DRIVER_PATH = EDGE_DRIVER_PATH if "EDGE_DRIVER_PATH" in globals() and os.path.exists(EDGE_DRIVER_PATH) else (DEFAULT_LOCAL_DRIVER if os.path.exists(DEFAULT_LOCAL_DRIVER) else r".\edgedriver_win64\msedgedriver.exe")

def find_edge_executable():
    # common install locations on Windows (used to set binary_location if available)
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.join(os.environ.get("LOCALAPPDATA",""), r"Microsoft\Edge\Application\msedge.exe"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

EDGE_BINARY = find_edge_executable()

# --- Added: stealth / profile options ---
# decide profile dir (prefer default Edge user-data if present, fall back to local profile)
# Correct default path is "...\\Microsoft\\Edge\\User Data"
DEFAULT_EDGE_USERDATA = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data")
DEFAULT_PROFILE_DIR = os.path.join(DEFAULT_EDGE_USERDATA, "Default")

def is_edge_running():
    try:
        out = subprocess.check_output(["tasklist"], text=True, stderr=subprocess.DEVNULL)
        return "msedge.exe" in out.lower()
    except Exception:
        return False

def copy_profile_to_temp(src_profile_dir):
    """Copy 'Default' profile into a temporary user-data-dir and return its path.
       Returns tuple (tmp_user_data_dir, tmp_default_dir)."""
    tmp_user_data = tempfile.mkdtemp(prefix="edge_user_data_")
    tmp_default = os.path.join(tmp_user_data, "Default")
    try:
        shutil.copytree(src_profile_dir, tmp_default)
    except Exception as e:
        # cleanup and re-raise
        try:
            shutil.rmtree(tmp_user_data)
        except Exception:
            pass
        raise
    # register cleanup
    def _cleanup():
        try:
            shutil.rmtree(tmp_user_data)
        except Exception:
            pass
    atexit.register(_cleanup)
    return tmp_user_data, tmp_default

if os.path.exists(DEFAULT_EDGE_USERDATA):
    PROFILE_DIR = DEFAULT_EDGE_USERDATA
    USE_DEFAULT_PROFILE = True
    if os.path.exists(DEFAULT_PROFILE_DIR):
        print(f"[>] Detected default Edge profile: {DEFAULT_PROFILE_DIR} — will try to use it if launching.")
    else:
        print(f"[>] Detected Edge user-data dir: {DEFAULT_EDGE_USERDATA} (no 'Default' subfolder found). Will still attempt to use user-data dir.")

    if is_edge_running():
        print("⚠️ Microsoft Edge process appears to be running. Using the system profile may fail due to profile lock.")
        print("Options: [C]lose Edge and re-run  [A]ttach via remote-debugging (manual)  [U]se a temporary copy of Default profile and continue")
        choice = input("Choose (C/A/U) [U]: ")

        if choice == "c":
            print("➡️ Please close all Edge windows, then re-run the script.")
            sys.exit(1)
        if choice == "a":
            print("➡️ To attach to an already-running Edge, start Edge with remote debugging:")
            print(r'   "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\Temp\edge-debug"')
            print("Then run this script again to attach. Exiting.")
            sys.exit(1)
        if choice == "u":
            # make a temp copy of the Default profile and use that as user-data-dir to avoid lock
            if os.path.exists(DEFAULT_PROFILE_DIR):
                try:
                    tmp_user_data, tmp_default = copy_profile_to_temp(DEFAULT_PROFILE_DIR)
                    PROFILE_DIR = tmp_user_data
                    USE_DEFAULT_PROFILE = True
                    print(f"[>] Created temporary copy of Default profile at {tmp_user_data} — continuing using this copy.")
                except Exception as e:
                    print(f"[!] Gagal membuat salinan profil Default: {e}")
                    print("➡️ Tutup Edge atau pilih opsi lain. Exiting.")
                    sys.exit(1)
            else:
                print("[!] Default profile folder not found to copy. Close Edge and re-run or use local profile.")
                sys.exit(1)
else:
    PROFILE_DIR = os.path.join(BASE_DIR, "edge_profile")
    os.makedirs(PROFILE_DIR, exist_ok=True)
    USE_DEFAULT_PROFILE = False
    print(f"[>] Default Edge user-data not found — using local profile: {PROFILE_DIR}")

# set a common Edge user agent (adjust if needed)
EDGE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69"

# Prepare two separate Options objects:
# - attach_opts: used to attach to an already-running Edge (DO NOT set user-data-dir)
# - launch_opts: used only if we must start a new Edge (set user-data-dir/profile here)
attach_opts = Options()
attach_opts.debugger_address = REMOTE_DEBUG_ADDRESS

launch_opts = Options()
launch_opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
if USE_DEFAULT_PROFILE:
    launch_opts.add_argument("--profile-directory=Default")
launch_opts.add_argument(f"--user-agent={EDGE_UA}")
launch_opts.add_argument("--disable-blink-features=AutomationControlled")
launch_opts.add_experimental_option("excludeSwitches", ["enable-automation"])
launch_opts.add_experimental_option("useAutomationExtension", False)
# optional window size
launch_opts.add_argument("--window-size=1280,800")

def install_driver_with_manager():
    try:
        return EdgeChromiumDriverManager().install()
    except requests.exceptions.RequestException as e:
        # propagate a clear network indicator
        raise RuntimeError("network") from e
    except Exception:
        raise

driver = None
attached = False
# 1) Try to attach to an existing Edge with remote debugging (no user-data-dir)
try:
    # prefer provided edgedriver if exists locally, otherwise try webdriver_manager
    if os.path.exists(EDGE_DRIVER_PATH):
        svc_path = EDGE_DRIVER_PATH
    else:
        try:
            svc_path = install_driver_with_manager()
        except RuntimeError:
            print("⚠️ webdriver_manager gagal mengunduh driver karena masalah jaringan/DNS dan tidak menemukan edgedriver lokal.")
            print("➡️ Solusi: letakkan msedgedriver.exe ke folder edgedriver_win64/ (lokasi: edgedriver_win64/msedgedriver.exe) atau set EDGE_DRIVER_PATH ke path msedgedriver.exe Anda.")
            sys.exit(1)
        except Exception as e:
            print(f"⚠️ Gagal menentukan edgedriver: {e}")
            sys.exit(1)

    svc = Service(svc_path)
    # Attempt attach using attach_opts (no user-data-dir so it won't spawn a new profile)
    driver = webdriver.Edge(service=svc, options=attach_opts)
    attached = True
    print("✅ Attached to existing Edge via remote debugging.")
except Exception as e:
    print(f"⚠️ Gagal attach ke Edge pada {REMOTE_DEBUG_ADDRESS}: {e}")
    print("➡️ Akan meluncurkan Edge WebDriver baru menggunakan profile lokal/default sebagai fallback...")
    attached = False
    # Fallback: launch a fresh Edge WebDriver (using launch_opts)
    try:
        # set binary if available
        if EDGE_BINARY:
            launch_opts.binary_location = EDGE_BINARY

        if os.path.exists(EDGE_DRIVER_PATH):
            svc2_path = EDGE_DRIVER_PATH
        else:
            try:
                svc2_path = install_driver_with_manager()
            except RuntimeError:
                raise SystemExit(
                    "❌ Gagal memulai Edge WebDriver karena mesin tidak dapat mengunduh edgedriver (network/DNS error)\n\n"
                    "Tindakan yang disarankan:\n"
                    "1) Download msedgedriver yang sesuai dengan versi Microsoft Edge Anda:\n"
                    "   https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/\n"
                    "2) Simpan executable msedgedriver.exe di folder 'edgedriver_win64' di sampel repo sehingga path menjadi:\n"
                    f"   {os.path.join(BASE_DIR, 'edgedriver_win64', 'msedgedriver.exe')}\n"
                    "3) Jalankan ulang skrip.\n"
                )
            except Exception as e2:
                raise SystemExit(f"❌ Gagal menginstall edgedriver otomatis: {e2}")

        svc2 = Service(svc2_path)
        driver = webdriver.Edge(service=svc2, options=launch_opts)
        attached = False
        print("✅ Edge WebDriver diluncurkan otomatis (baru) menggunakan profile lokal/default.")
    except WebDriverException as e2:
        raise SystemExit(
            f"❌ Gagal memulai Edge WebDriver: {e2}\n\n"
            "Jika Anda sudah memiliki edgedriver lokal, pastikan file berada di edgedriver_win64/msedgedriver.exe "
            "atau set EDGE_DRIVER_PATH ke lokasi file tersebut di awal skrip."
        )

# --- Inject stealth script on new document (if driver supports CDP) ---
stealth_script = r"""
Object.defineProperty(navigator, 'webdriver', {get: () => false});
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
"""

try:
    # Use CDP to run script on every new document (works on Chromium-based browsers)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_script})
except Exception:
    # not critical; continue even if CDP not available
    pass

# Setelah berhasil punya `driver`, lanjutkan ke buka URL
# Buka halaman Shopee agar user dapat login / menyelesaikan captcha terlebih dahulu
print("➡️ Membuka Shopee untuk login. Silakan login & selesaikan captcha di jendela browser yang terbuka.")
driver.get("https://shopee.co.id/")
time.sleep(2)

# --- NEW: coba muat cookie dari cookie.json di folder ini (jika ada) dan tambahkan ke browser ---
cookie_file = os.path.join(BASE_DIR, "cookie.json")
_added = 0
if os.path.exists(cookie_file):
    try:
        with open(cookie_file, "r", encoding="utf-8") as cf:
            cj = json.load(cf)
        raw = cj.get("cookies") if isinstance(cj, dict) and "cookies" in cj else (cj if isinstance(cj, list) else [])
        for c in raw:
            name = c.get("name")
            value = c.get("value")
            if not name or value is None:
                continue
            cookie = {"name": name, "value": value, "path": c.get("path", "/")}
            # normalize domain (Selenium may not like leading dot on some setups)
            dom = c.get("domain") or c.get("hostOnly") and c.get("hostOnly") or None
            if dom:
                cookie["domain"] = dom.lstrip(".")
            # expiry handling
            if "expirationDate" in c:
                try:
                    cookie["expiry"] = int(c.get("expirationDate"))
                except Exception:
                    pass
            # secure/httpOnly flags
            if "secure" in c:
                cookie["secure"] = bool(c.get("secure"))
            if "httpOnly" in c:
                cookie["httpOnly"] = bool(c.get("httpOnly"))
            try:
                # must be on the cookie domain to add, ensure on shopee domain
                driver.add_cookie(cookie)
                _added += 1
            except Exception as e:
                # some cookies (httpOnly or domain mismatch) may fail to add via Selenium; ignore
                # but continue trying others
                # print minimal debug
                print(f"[!] cookie add failed for {name}: {e}")
        if _added:
            print(f"[>] Added {_added} cookies from {cookie_file} into browser session. Refreshing page...")
            driver.refresh()
            time.sleep(1.5)
    except Exception as e:
        print(f"[!] Gagal memuat/menambahkan cookie dari {cookie_file}: {e}")

# NEW: jika kita attach ke Edge yang sudah berjalan dan situs mendeteksi anti-bot,
# instruksikan user untuk membuka TAB BARU di browser mereka dan login/solve captcha di tab itu.
def quick_is_antibot():
    try:
        url = (driver.current_url or "").lower()
        src = (driver.page_source or "").lower()
        if "verify/captcha" in url or "anti_bot_tracking" in url:
            return True
        if "terjadi kesalahan" in src or ("captcha" in src and "try again" in src):
            return True
    except Exception:
        pass
    return False

if attached and quick_is_antibot():
    print("⚠️ Halaman terdeteksi menampilkan captcha/anti-bot pada tab yang ter-attach.")
    print("➡️ Silakan buka TAB BARU di Microsoft Edge (profil yang sama), paste URL produk berikut dan login/selesaikan captcha di TAB BARU itu:")
    print(f"   {PRODUCT_URL}")
    print("➡️ Setelah Anda login & captcha diselesaikan di tab baru, kembali ke terminal dan tekan ENTER untuk melanjutkan pengambilan data.")
else:
    print("[*] Jika challenge/captcha muncul di halaman, selesaikan di browser. Jika Anda selesai, tekan ENTER di terminal.")

input("Tekan ENTER setelah login/captcha selesai...")

# Setelah konfirmasi, buka halaman produk dan lanjutkan proses scraping
# we'll attempt navigation + check for anti-bot indicators and allow retry
def is_antibot_page():
    try:
        url = driver.current_url or ""
        src = driver.page_source or ""
        url_lower = url.lower()
        src_lower = src.lower()
        if "verify/captcha" in url_lower or "anti_bot_tracking" in url_lower:
            return True
        if "terjadi kesalahan" in src_lower or "captcha" in src_lower and "try again" in src_lower:
            return True
    except Exception:
        pass
    return False

# try navigation and check
driver.get(PRODUCT_URL)
time.sleep(3)
if is_antibot_page():
    print("⚠️ Halaman terdeteksi sebagai anti-bot / error. Akan membuka ulang profile untuk Anda menyelesaikan challenge.")
    print("➡️ Pastikan Anda menyelesaikan captcha/login di window Edge yang muncul. Setelah selesai, tekan ENTER untuk melanjutkan.")
    # open the product again (profile dir preserves cookies), allow manual solve
    driver.get(PRODUCT_URL)
    input("Tekan ENTER setelah challenge diselesaikan di browser...")
    # small wait then re-check
    time.sleep(2)
    if is_antibot_page():
        print("❌ Masih terdeteksi anti-bot setelah percobaan manual. Opsi:\n- Coba refresh beberapa kali,\n- Gunakan Playwright main.py dengan storage_state cookie, atau\n- Pastikan profile di edge_profile sudah berisi sesi login/cookie yang valid.")
        sys.exit(1)

# ===== NEW: use modular scrapers =====
# Scrape product metadata first (best-effort)
try:
	print(f"[>] Mengambil data produk (shopid={shopid}, itemid={itemid}) ...")
	product_data = scrape_product(driver, shopid, itemid)
	if product_data:
		with open("produk.json", "w", encoding="utf-8") as f:
			json.dump(product_data, f, ensure_ascii=False, indent=2)
		print(f"[+] Saved product data to produk.json")
	else:
		print("[-] Gagal ambil data produk (kosong).")
except Exception as e:
	print("[!] Error saat mengambil data produk:", e)

# Scrape comments/reviews using the separated module
try:
	print("[>] Mulai mengambil komentar/review ...")
	comments = scrape_comments(driver, shopid, itemid, limit=LIMIT, delay=DELAY, max_pages=MAX_PAGES)
	if comments:
		with open("review.json", "w", encoding="utf-8") as f:
			json.dump(comments, f, ensure_ascii=False, indent=2)
		print(f"[+] Saved {len(comments)} reviews to review.json")
	else:
		print("[-] No reviews collected. Check cookies, open page status, or possible blocking.")
except Exception as e:
	print("[!] Error saat mengambil komentar:", e)

# cleanup and exit (unchanged)
driver.quit()
