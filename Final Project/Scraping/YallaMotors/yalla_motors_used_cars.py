import os
import csv
import time
import re
import random 
import requests
from urllib.parse import urlparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
TEST_MODE = False  
TEST_LINK = "https://egypt.yallamotor.com/used-cars/jeep/cherokee/2011/used-jeep-cherokee-2011-cairo-1586843"

LINKS_FILE = "yallamotor_complete_links.txt"
CSV_FILENAME = "yallamotor_cars.csv"
IMAGES_ROOT = "images_yallamotor"

# WORKER SETTINGS
MAX_WORKERS = 5         
LINKS_PER_WORKER = 5    

HEADERS = [
    "Car Title", "Brand", "Model", "Price", "Year", "Trim", "Mileage", 
    "Condition", "Transmission", "Fuel Type", "CC", "Color", "Location",
    "Body Type", "Image Paths", "URL"
]

# Browser-like headers for Python requests
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://egypt.yallamotor.com/",
    "Accept-Language": "en-US,en;q=0.9"
}

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_").strip()

def extract_brand_model_from_url(url):
    try:
        path_parts = urlparse(url).path.split('/')
        if "used-cars" in path_parts:
            idx = path_parts.index("used-cars")
            if len(path_parts) > idx + 3:
                return path_parts[idx+1], path_parts[idx+2], path_parts[idx+3]
    except:
        pass
    return "Unknown", "Unknown", "N/A"

def derive_trim(title, brand, model, year):
    if not title: return "N/A"
    clean_title = title.lower().replace("used", "").replace(brand.lower(), "").replace(model.lower(), "").replace(str(year), "")
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    return clean_title.title() if clean_title else "Base/Standard"

def download_images_python(image_urls, folder):
    """
    Downloads images using Python requests with stealth headers.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    saved_paths = []
    
    for idx, url in enumerate(image_urls):
        if not url: continue
        
        # Detect Extension
        clean_url = url.split('?')[0]
        ext_match = re.search(r'\.(jpg|jpeg|png|webp)', clean_url, re.IGNORECASE)
        ext = ext_match.group(1).lower() if ext_match else "jpg"
        
        filename = os.path.join(folder, f"img_{idx+1}.{ext}")
        
        try:
            # Random tiny delay between image downloads
            time.sleep(random.uniform(0.1, 0.4))
            
            response = requests.get(url, headers=DOWNLOAD_HEADERS, timeout=20)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                saved_paths.append(filename)
            else:
                print(f"       ⚠️ Download Failed ({response.status_code}): {url}")
                
        except Exception as e:
            print(f"       ⚠️ File Error: {e}")
            pass 
            
    return saved_paths

def process_batch(urls_batch, batch_id):
    results = []
    
    with sync_playwright() as p:
        # --- STEALTH 1: Launch Args ---
        browser = p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        
        # --- STEALTH 2: Context & User Agent ---
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # --- STEALTH 3: Mask WebDriver Property ---
        # This prevents the site from detecting 'navigator.webdriver = true'
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        print(f"⚙️ Worker {batch_id} processing {len(urls_batch)} links...")

        for current_url in urls_batch:
            try:
                # --- STEALTH 4: Human-like Navigation ---
                page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
                
                # Random delay after load to look like a human reading
                time.sleep(random.uniform(1.5, 3.0)) 
                
                # --- 1. Basic Info ---
                h1_text = "N/A"
                if page.locator("h1").count() > 0:
                    h1_text = page.locator("h1").first.inner_text().strip()

                price_text = "N/A"
                price_locator = page.locator("div.text-3xl.font-bold.text-gray-900")
                if price_locator.count() > 0:
                    price_text = price_locator.first.inner_text().strip()
                
                # --- 2. Specs ---
                specs_map = {}
                spec_cards = page.locator("div.grid div.text-center").all()
                if not spec_cards:
                    spec_cards = page.locator("div.space-y-3").all()

                for card in spec_cards:
                    try:
                        label_el = card.locator("[class*='text-gray-600']").first
                        value_el = card.locator(".font-semibold").first
                        if label_el.is_visible() and value_el.is_visible():
                            specs_map[label_el.inner_text().strip()] = value_el.inner_text().strip()
                    except:
                        continue

                url_brand, url_model, url_year = extract_brand_model_from_url(current_url)
                final_year = specs_map.get("Year", specs_map.get("Model Year", url_year))
                trim_val = derive_trim(h1_text, url_brand, url_model, final_year)

                # --- 3. URL Extraction ---
                print(f"    🔍 Worker {batch_id}: Extracting URLs for {url_model}...")
                
                unique_urls = []
                # Retry logic for loading assets
                for attempt in range(2):
                    # Scroll a bit to trigger lazy loading (Human behavior)
                    page.mouse.wheel(0, 500)
                    time.sleep(0.5)
                    
                    try:
                        page.wait_for_selector('.embla-thumb__container img', timeout=3000)
                    except: pass

                    raw_urls = page.evaluate("""() => {
                        const urls = [];
                        // 1. Thumbnails (Best Source)
                        document.querySelectorAll('.embla-thumb__container img').forEach(img => urls.push(img.src));
                        // 2. Main Image (Fallback)
                        document.querySelectorAll('img.object-cover.object-center').forEach(img => urls.push(img.src));
                        // 3. Slider Inner (Fallback)
                        document.querySelectorAll('.embla__slide__inner img').forEach(img => urls.push(img.src));
                        return urls;
                    }""")

                    seen_urls = set()
                    unique_urls = []
                    
                    for src in raw_urls:
                        if "ymimg1.b8cdn.com" in src:
                            high_res = src.replace("thumb_", "listing_main_").replace("small_", "listing_main_")
                            if "listing_main" in high_res:
                                if high_res not in seen_urls:
                                    unique_urls.append(high_res)
                                    seen_urls.add(high_res)
                    
                    if len(unique_urls) > 0:
                        break
                    time.sleep(1.5)

                # --- 4. Python Download ---
                unique_id = int(time.time() * 1000) % 100000 
                safe_name = clean_filename(f"{url_brand}_{url_model}_{final_year}")
                car_folder = os.path.join(IMAGES_ROOT, f"{safe_name}_{unique_id}")

                if len(unique_urls) > 0:
                    print(f"    ⬇️  Worker {batch_id}: Downloading {len(unique_urls)} images...")
                    local_paths = download_images_python(unique_urls, car_folder)
                else:
                    print(f"    ❌ Worker {batch_id}: No images found.")
                    local_paths = []

                # --- 5. Build Row ---
                row = {
                    "Car Title": h1_text,
                    "Brand": url_brand.capitalize(),
                    "Model": url_model.capitalize(),
                    "Price": price_text,
                    "Year": final_year,
                    "Trim": trim_val,
                    "Mileage": specs_map.get("Kilometers", "N/A"),
                    "Condition": "Used",
                    "Transmission": specs_map.get("Transmission", "N/A"),
                    "Fuel Type": specs_map.get("Fuel Type", "N/A"),
                    "CC": specs_map.get("Engine (CC)", "N/A"),
                    "Color": specs_map.get("Exterior Color", "N/A"),
                    "Location": specs_map.get("Location", "N/A"),
                    "Body Type": specs_map.get("Body Style", "N/A"),
                    "Image Paths": "; ".join(local_paths),
                    "URL": current_url
                }
                
                results.append(row)
                print(f"    ✅ Worker {batch_id}: Finished {url_brand} {url_model} ({len(local_paths)} imgs)")

            except Exception as e:
                print(f"    ❌ Worker {batch_id} Failed {current_url}: {e}")

        browser.close()
    
    return results

def run_scraper():
    if TEST_MODE:
        print(f"🧪 TEST MODE: Processing single link.")
        urls = [TEST_LINK]
    else:
        if not os.path.exists(LINKS_FILE):
            print(f"File {LINKS_FILE} not found!")
            return
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"🔥 Loaded {len(urls)} links. Starting {MAX_WORKERS} Parallel Workers...")

    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()

    batches = [urls[i:i + LINKS_PER_WORKER] for i in range(0, len(urls), LINKS_PER_WORKER)]
    
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, batch in enumerate(batches):
            futures.append(executor.submit(process_batch, batch, i+1))
        
        for future in as_completed(futures):
            try:
                batch_results = future.result()
                with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=HEADERS)
                    for row in batch_results:
                        writer.writerow(row)
            except Exception as e:
                print(f"❌ Batch Error: {e}")

    print("\n🎉 Scraper finished.")

if __name__ == "__main__":
    run_scraper()