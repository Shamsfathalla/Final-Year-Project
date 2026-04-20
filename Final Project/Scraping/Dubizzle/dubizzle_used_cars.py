import os
import csv
import time
import re
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
LINKS_FILE = "dubizzle_links_full.txt"
CSV_FILENAME = "dubizzle_cars_final.csv"
FAILED_LINKS_FILE = "failed_urls.txt"
IMAGES_ROOT = "images_dubizzle"

# WORKER SETTINGS
MAX_WORKERS = 5
LINKS_PER_WORKER = 5      

# RETRY SETTINGS
MAX_RETRIES = 3
RETRY_DELAY = 5 # Seconds to wait before reloading

# Removed Title, Location, Description
HEADERS_CSV = [
    "Brand", "Model", "Price", "Year", "Kilometers", 
    "Condition", "Transmission", "Fuel Type", "CC", "Color", 
    "Body Type", "Power", "Image Paths", "URL"
]

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_").strip()

def create_stealth_browser(p):
    browser = p.chromium.launch(
        headless=False, # Set to True if you want it to run invisibly
        args=['--disable-blink-features=AutomationControlled', '--start-maximized', '--no-sandbox']
    )
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='Africa/Cairo'
    )
    return browser, context

def download_file_python(url, folder, index):
    """Downloads image using Python requests with retries."""
    if not url: return None
    if not os.path.exists(folder): os.makedirs(folder)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.dubizzle.com.eg/",
    }

    ext_match = re.search(r'\.(jpg|jpeg|png|webp|heic)', url, re.IGNORECASE)
    ext = ext_match.group(1) if ext_match else "jpg"
    filename = os.path.join(folder, f"img_{index}.{ext}")

    # Try High Res -> Original
    urls_to_try = []
    if re.search(r'-\d+x\d+\.', url):
        high_res = re.sub(r'-\d+x\d+\.', '-800x600.', url)
        if high_res != url: urls_to_try.append(high_res)
    urls_to_try.append(url)

    for target_url in urls_to_try:
        try:
            response = requests.get(target_url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
        except: pass
    return None

def process_batch(urls_batch, batch_id):
    results = []
    failed_links = []
    
    with sync_playwright() as p:
        browser, context = create_stealth_browser(p)
        page = context.new_page()

        print(f"⚙️ Worker {batch_id} started processing {len(urls_batch)} links...")

        for current_url in urls_batch:
            success = False
            
            # --- RETRY LOOP ---
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"   [W{batch_id}] Processing: {current_url} (Attempt {attempt+1}/{MAX_RETRIES})")
                    
                    # Navigation with timeout
                    page.goto(current_url, wait_until="domcontentloaded", timeout=45000)
                    
                    # Basic check: verify if we are on a valid page (look for price or h1)
                    try:
                        page.wait_for_selector('h1', timeout=5000)
                    except:
                        if attempt < MAX_RETRIES - 1:
                            print(f"      ⚠️ [W{batch_id}] Page didn't load correctly. Retrying...")
                            time.sleep(RETRY_DELAY)
                            continue
                        else:
                            raise Exception("Page failed to load essential elements.")

                    # --- DATA EXTRACTION ---
                    
                    # 1. Price
                    price_val = "N/A"
                    if page.locator('span[aria-label="Price"]').count() > 0:
                        price_val = page.locator('span[aria-label="Price"]').first.inner_text().strip()

                    # 2. Key Details (Icons Grid)
                    key_specs = {
                        "Year": "N/A", "Kilometers": "N/A", "Condition": "N/A",
                        "Fuel Type": "N/A", "Transmission Type": "N/A", "Engine Capacity (CC)": "N/A"
                    }
                    for label in key_specs.keys():
                        try:
                            el = page.locator(f"//span[text()='{label}']/following-sibling::span").first
                            if el.is_visible(): key_specs[label] = el.inner_text().strip()
                        except: continue

                    # 3. Detailed Specs
                    full_specs = {}
                    spec_rows = page.locator("div._92439ac7").all()
                    for row in spec_rows:
                        spans = row.locator("span").all()
                        if len(spans) >= 2:
                            full_specs[spans[0].inner_text().strip()] = spans[1].inner_text().strip()

                    # Consolidation
                    brand = full_specs.get("Brand", "Unknown")
                    model = full_specs.get("Model", "Unknown")
                    year = key_specs["Year"] if key_specs["Year"] != "N/A" else full_specs.get("Year", "N/A")

                    # 4. Images
                    safe_name = clean_filename(f"{brand}_{model}_{year}")
                    unique_id = int(time.time() * 1000) % 100000 
                    car_folder = os.path.join(IMAGES_ROOT, f"{safe_name}_{unique_id}")

                    image_urls = []
                    try:
                        # Try gallery button
                        gallery_btn = page.locator("div:has-text('See')").filter(has_text="photos").last
                        if gallery_btn.is_visible():
                            gallery_btn.click()
                            page.wait_for_selector('div[aria-label="Gallery dialog photo grid"]', timeout=5000)
                            time.sleep(1)
                            imgs = page.locator('div[aria-label="Gallery dialog photo grid"] img').all()
                        else:
                            # Fallback slider
                            imgs = page.locator('div[aria-label="Gallery"] img').all()
                        
                        for img in imgs:
                            src = img.get_attribute("src")
                            if src: image_urls.append(src)
                    except: pass
                    
                    image_urls = list(set(image_urls))
                    
                    # Download Images
                    local_paths = []
                    for idx, url in enumerate(image_urls):
                        path = download_file_python(url, car_folder, idx+1)
                        if path: local_paths.append(path)

                    # 5. Build Row
                    row = {
                        "Brand": brand,
                        "Model": model,
                        "Price": price_val,
                        "Year": year,
                        "Kilometers": key_specs["Kilometers"],
                        "Condition": key_specs["Condition"],
                        "Transmission": key_specs["Transmission Type"],
                        "Fuel Type": key_specs["Fuel Type"],
                        "CC": key_specs["Engine Capacity (CC)"],
                        "Color": full_specs.get("Color", "N/A"),
                        "Body Type": full_specs.get("Body Type", "N/A"),
                        "Power": full_specs.get("Power (hp)", "N/A"),
                        "Image Paths": "; ".join(local_paths),
                        "URL": current_url
                    }
                    results.append(row)
                    success = True
                    print(f"    ✅ [W{batch_id}] Success: {brand} {model}")
                    break # Break retry loop on success

                except Exception as e:
                    print(f"      ⚠️ [W{batch_id}] Error on attempt {attempt+1}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                    else:
                        print(f"      ❌ [W{batch_id}] PERMANENT FAIL: {current_url}")
                        failed_links.append(current_url)

        browser.close()
    
    return results, failed_links

def run_workers():
    if not os.path.exists(LINKS_FILE):
        print(f"File {LINKS_FILE} not found!")
        return
        
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"🔥 Loaded {len(urls)} links. Starting {MAX_WORKERS} Workers...")

    # Initialize Output Files
    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
            writer.writeheader()

    # Split work
    batches = [urls[i:i + LINKS_PER_WORKER] for i in range(0, len(urls), LINKS_PER_WORKER)]
    
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, batch in enumerate(batches):
            futures.append(executor.submit(process_batch, batch, i+1))
        
        for future in as_completed(futures):
            try:
                batch_results, batch_failed = future.result()
                
                # Write Successes
                with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
                    for row in batch_results:
                        writer.writerow(row)
                
                # Write Failures
                if batch_failed:
                    with open(FAILED_LINKS_FILE, "a", encoding="utf-8") as f:
                        for link in batch_failed:
                            f.write(link + "\n")
                            
            except Exception as e:
                print(f"❌ Critical Worker Failure: {e}")

    print("\n🎉 All processing complete.")

if __name__ == "__main__":
    run_workers()