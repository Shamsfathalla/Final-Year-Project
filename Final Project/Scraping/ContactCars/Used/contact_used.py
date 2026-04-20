import os
import csv
import time
import random
import requests
import urllib.parse
from math import ceil
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
LINKS_FILE = "contactcars_links_clean.txt"
CSV_FILENAME = "used_cars_data.csv"
BASE_IMAGE_FOLDER = "images"
MAX_WORKERS = 4  # Number of parallel browsers (Adjust based on your CPU/RAM)

HEADERS = [
    "Brand", "Model", "Year", "Price", "Trim", "URL", "Image Paths",
    "Seller Name", "Seller Phone", "Car Status", "Body Shape", 
    "Transmission", "Mileage", "Fuel Type", "Engine Capacity", 
    "Color", "Cylinder Count"
]

# ==============================
# HELPER FUNCTIONS
# ==============================

def clean_text(text):
    return text.strip() if text else "N/A"

def extract_real_url(src):
    if not src: return None
    if "/_next/image" in src:
        try:
            parsed = urllib.parse.urlparse(src)
            query = urllib.parse.parse_qs(parsed.query)
            if 'url' in query:
                return query['url'][0]
        except:
            return src
    return src

def download_images(image_urls, car_title):
    """Downloads images into images/[car_title] subfolder."""
    # Sanitize folder name
    safe_folder_name = "".join(x for x in car_title if x.isalnum() or x in "._- ").strip()
    folder = os.path.join(BASE_IMAGE_FOLDER, safe_folder_name)
    
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True) # exist_ok=True prevents race conditions
    
    saved_paths = []
    unique_urls = list(image_urls)
    
    for idx, url in enumerate(unique_urls):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                ext = "jpg"
                if ".png" in url.lower(): ext = "png"
                elif ".webp" in url.lower(): ext = "webp"
                
                filename = os.path.join(folder, f"car_img_{idx+1}.{ext}")
                with open(filename, 'wb') as f:
                    f.write(response.content)
                saved_paths.append(filename)
        except Exception:
            pass
    return saved_paths

# ==============================
# CORE SCRAPER LOGIC
# ==============================

def scrape_single_car(page, url):
    """Scrapes a single URL using the provided page object."""
    print(f"🚙 Processing: {url}")
    try:
        # Stealthy navigation
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("body") 
        time.sleep(random.uniform(2, 4)) # Reduced slightly for parallel efficiency
        page.evaluate("window.scrollTo(0, 500);")
    except Exception as e:
        print(f"❌ Page load failed for {url}: {e}")
        return None

    # --- STEP 1: BASIC INFO ---
    try:
        full_title = clean_text(page.locator("h1.text-brand-900 pre").first.inner_text())
        price_val = clean_text(page.locator('div[id="#price"] h3').first.inner_text())
        price = f"{price_val} EGP"
        trim = clean_text(page.locator("h4.text-dark-blue").first.inner_text())
        
        parts = full_title.split()
        brand = parts[0] if len(parts) > 0 else "N/A"
        year = parts[-1] if len(parts) > 0 and parts[-1].isdigit() else "N/A"
        model = " ".join(parts[1:-1]) if len(parts) > 2 else "N/A"
    except Exception:
        full_title, brand, model, year, price, trim = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

    # --- STEP 2: SELLER INFO ---
    try:
        seller_name = clean_text(page.locator('span[class*="text-[#1C1C1C]"]').first.inner_text())
        phone_link = page.locator("a[href^='tel:']").first
        seller_phone = phone_link.get_attribute("href").replace("tel:", "") if phone_link.count() > 0 else "N/A"
    except Exception:
        seller_name, seller_phone = "N/A", "N/A"

    # --- STEP 3: GALLERY IMAGES ---
    img_urls = set()
    try:
        gallery_images = page.locator(".swiper-zoom-container img").all()
        for img in gallery_images:
            srcset = img.get_attribute("srcset")
            src = img.get_attribute("src")
            target = srcset.split(',')[-1].strip().split(' ')[0] if srcset else src
            real = extract_real_url(target)
            if real and ("digitaloceanspaces" in real or "contactcars" in real):
                img_urls.add(real)
    except Exception:
        pass
    
    local_image_paths = download_images(img_urls, full_title if full_title != "N/A" else "Unknown_Car")
    image_paths_string = "; ".join(local_image_paths)

    # --- STEP 4: SPECS SUMMARY ---
    try:
        summary_specs = page.evaluate("""() => {
            const data = {};
            const containers = document.querySelectorAll('div.flex.flex-col');
            containers.forEach(div => {
                const label = div.querySelector('span.text-dark-blue');
                const value = div.querySelector('h5');
                if (label && value) {
                    data[label.innerText.trim()] = value.innerText.trim();
                }
            });
            return data;
        }""")
    except Exception:
        summary_specs = {}

    return {
        "Brand": brand, "Model": model, "Year": year, "Price": price, "Trim": trim, 
        "URL": url, "Image Paths": image_paths_string,
        "Seller Name": seller_name, "Seller Phone": seller_phone,
        "Car Status": summary_specs.get("Car Status", "N/A"),
        "Body Shape": summary_specs.get("Body Shape", "N/A"),
        "Transmission": summary_specs.get("Transmission", "N/A"),
        "Mileage": summary_specs.get("Mileage", "N/A"),
        "Fuel Type": summary_specs.get("Fuel Type", "N/A"),
        "Engine Capacity": summary_specs.get("Engine Capacity", "N/A"),
        "Color": summary_specs.get("Color", "N/A"),
        "Cylinder Count": summary_specs.get("Cylinder Count", "N/A")
    }

# ==============================
# WORKER PROCESS
# ==============================

def process_batch(urls, batch_id):
    """
    This function runs in a separate process.
    It launches its own browser, processes a list of URLs, and returns the results.
    """
    results = []
    print(f"⚙️ Worker {batch_id} starting with {len(urls)} URLs...")
    
    with sync_playwright() as p:
        # Launch browser for this worker
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for url in urls:
            data = scrape_single_car(page, url)
            if data:
                results.append(data)
            
            # Short sleep between cars within the same worker
            time.sleep(random.uniform(2, 3))

        browser.close()
    
    print(f"✅ Worker {batch_id} finished.")
    return results

# ==============================
# MAIN CONTROLLER
# ==============================

def run_parallel():
    if not os.path.exists(LINKS_FILE):
        print(f"❌ {LINKS_FILE} not found!")
        return

    # 1. Read URLs
    with open(LINKS_FILE, "r") as f:
        all_urls = [line.strip() for line in f if line.strip()]

    if not all_urls:
        print("No URLs found.")
        return

    print(f"🚀 Starting scrape for {len(all_urls)} URLs using {MAX_WORKERS} workers.")

    # 2. Setup CSV (Write Header)
    # We do this once in the main process
    file_exists = os.path.isfile(CSV_FILENAME)
    if not file_exists:
        with open(CSV_FILENAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()

    # 3. Split URLs into batches
    batch_size = ceil(len(all_urls) / MAX_WORKERS)
    batches = [all_urls[i:i + batch_size] for i in range(0, len(all_urls), batch_size)]

    # 4. Execute in Parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks
        futures = {executor.submit(process_batch, batch, i): i for i, batch in enumerate(batches)}

        # Process results as they come in
        with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            
            for future in as_completed(futures):
                batch_results = future.result()
                if batch_results:
                    for row in batch_results:
                        writer.writerow(row)
                    f.flush()
                    print(f"💾 Saved {len(batch_results)} records from a worker batch.")

    print(f"✨ Parallel Scrape Complete. Data in {CSV_FILENAME}")

if __name__ == "__main__":
    # Required for multiprocessing on Windows
    run_parallel()