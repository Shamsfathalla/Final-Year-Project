import os
import csv
import time
import re
import requests
import urllib.parse
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
LINKS_FILE = "biddex_links_full.txt"
CSV_FILENAME = "biddex_cars_final.csv"
FAILED_LINKS_FILE = "biddex_failed_urls.txt"
IMAGES_ROOT = "images_biddex"

# 🛑 SPEED SETTINGS (Updated)
MAX_WORKERS = 5          # 5 browsers at once
LINKS_PER_WORKER = 1     # Process 1 link at a time per worker to avoid races
PAGE_LOAD_SLEEP = 5      # Wait 5 seconds after page load before doing anything

# RETRY SETTINGS
MAX_RETRIES_LINK = 3     # How many times to reload the whole page if it fails
MAX_CLICK_ATTEMPTS = 15  # How many times to click "See More" before giving up

# Added "Trim" to headers
HEADERS_CSV = [
    "Brand", "Model", "Trim", "Price", "Year", "Kilometers", 
    "Condition", "Transmission", "Fuel Type", "CC", "Color", 
    "Body Type", "Power", "Cylinders", "Image Paths", "URL"
]

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_").strip()

def get_original_image_url(nextjs_url):
    try:
        parsed = urllib.parse.urlparse(nextjs_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'url' in query_params:
            return query_params['url'][0]
        return nextjs_url
    except:
        return nextjs_url

def create_stealth_browser(p):
    browser = p.chromium.launch(
        headless=False, 
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
    if not url: return None
    try:
        if not os.path.exists(folder): os.makedirs(folder)
        real_url = get_original_image_url(url)
        if real_url.startswith("/"): real_url = "https://biddex.com" + real_url
        
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://biddex.com/"}
        ext = "webp" if ".webp" in real_url else "jpg"
        filename = os.path.join(folder, f"img_{index}.{ext}")

        response = requests.get(real_url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(filename, 'wb') as f: f.write(response.content)
            return filename
    except: return None
    return None

def extract_specs_from_container(container):
    """Scrapes key-value pairs from a given locator (container)"""
    data = {}
    try:
        # Based on your HTML: <div class="flex items-center justify-between gap-2">
        rows = container.locator('div.flex.items-center.justify-between').all()
        for row in rows:
            texts = row.locator("p").all_inner_texts()
            # Usually: [Label, Value] e.g. ["Brand", "Nissan"]
            if len(texts) >= 2:
                key = texts[0].strip()
                val = texts[-1].strip()
                data[key] = val
    except: pass
    return data

def process_batch(urls_batch, batch_id):
    results = []
    failed_links = []
    
    with sync_playwright() as p:
        browser, context = create_stealth_browser(p)
        page = context.new_page()

        print(f"⚙️ Worker {batch_id} started. Tasks: {len(urls_batch)}")

        for current_url in urls_batch:
            link_success = False
            
            # --- PAGE RETRY LOOP ---
            for attempt in range(MAX_RETRIES_LINK):
                try:
                    print(f"   [W{batch_id}] Visiting: {current_url} (Attempt {attempt+1})")
                    
                    # 1. ROBUST NAVIGATION
                    page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
                    
                    # 🛑 CRITICAL SLOW DOWN: Wait for JS Hydration
                    print(f"      ⏳ [W{batch_id}] Warming up ({PAGE_LOAD_SLEEP}s)...")
                    time.sleep(PAGE_LOAD_SLEEP)

                    # 2. PRICE EXTRACTION
                    try:
                        price_locator = page.locator('p.text-xl.font-bold').filter(has_text="EGP").first
                        price_val = price_locator.inner_text().strip() if price_locator.is_visible() else "N/A"
                    except: price_val = "N/A"

                    # 3. INITIAL VISIBLE SPECS (Backup)
                    # We scrape what is visible immediately (Brand, Model, Year, etc.)
                    main_specs_container = page.locator("section#specification")
                    specs_map = extract_specs_from_container(main_specs_container)

                    # 4. "MUST OPEN" MODAL LOOP
                    # We look for the "See More" button inside the specs section
                    btn = page.locator("section#specification header button")
                    
                    if btn.is_visible():
                        modal_open = False
                        clicks = 0
                        
                        # Loop until modal is visible OR we hit max attempts
                        while not modal_open and clicks < MAX_CLICK_ATTEMPTS:
                            clicks += 1
                            
                            # Check if modal appeared from previous click
                            if page.locator('div[role="dialog"]').is_visible():
                                modal_open = True
                                break
                            
                            print(f"      👉 [W{batch_id}] Clicking 'See More' (Try {clicks})...")
                            
                            # TRY DIFFERENT CLICK STRATEGIES
                            try:
                                if clicks % 3 == 1:
                                    # Strategy A: JS Click (Best for overlays)
                                    btn.evaluate("el => el.click()")
                                elif clicks % 3 == 2:
                                    # Strategy B: Standard Click
                                    btn.click(timeout=1000, force=True)
                                else:
                                    # Strategy C: Coordinate Click (Nuclear option)
                                    box = btn.bounding_box()
                                    if box:
                                        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                            except: pass
                            
                            # Wait a bit to see if it opened
                            try:
                                page.locator('div[role="dialog"]').wait_for(state="visible", timeout=2000)
                                modal_open = True
                                print(f"      🔓 [W{batch_id}] Modal Opened!")
                            except:
                                # If stuck after 5 clicks, try scrolling slightly
                                if clicks == 5:
                                    page.mouse.wheel(0, 100)
                                time.sleep(1.5)

                        if modal_open:
                            # Update specs with hidden data
                            modal_specs = extract_specs_from_container(page.locator('div[role="dialog"]'))
                            specs_map.update(modal_specs)
                        else:
                            print(f"      ⚠️ [W{batch_id}] FAILED to open modal after {MAX_CLICK_ATTEMPTS} tries.")
                            # OPTIONAL: If you STRICTLY want to fail if not open, uncomment below:
                            # raise Exception("Could not open specs modal")

                    # 5. MAPPING DATA
                    brand = specs_map.get("Brand", "Unknown")
                    model = specs_map.get("Model", "Unknown")
                    year = specs_map.get("Year", "N/A")

                    row_data = {
                        "Brand": brand, 
                        "Model": model, 
                        "Trim": specs_map.get("Classification", "N/A"), # Scraped Classification -> Trim
                        "Price": price_val, 
                        "Year": year,
                        "Kilometers": specs_map.get("Mileage", "N/A"),
                        "Condition": specs_map.get("Car Condition", "N/A"),
                        "Transmission": specs_map.get("Transmission", "N/A"),
                        "Fuel Type": "Gasoline", # Default, update if found
                        "CC": specs_map.get("Engine Capacity", "N/A"),
                        "Color": specs_map.get("Color", "N/A"),
                        "Body Type": specs_map.get("Body Type", "N/A"),
                        "Power": specs_map.get("Horse Power", "N/A"),
                        "Cylinders": specs_map.get("Engine Cylinder Number", "N/A"),
                        "URL": current_url
                    }

                    # 6. IMAGE DOWNLOAD
                    try:
                        image_urls = []
                        # Priority 1: High Res Hidden
                        fancybox_imgs = page.locator('img[data-fancybox="image-details"]').all()
                        for img in fancybox_imgs:
                            src = img.get_attribute("src")
                            if src: image_urls.append(src)
                        
                        # Priority 2: Visible Slider
                        if not image_urls:
                            slider_imgs = page.locator('section img').all()
                            for img in slider_imgs:
                                src = img.get_attribute("src")
                                if src and "icon" not in src: image_urls.append(src)

                        image_urls = list(set(image_urls))
                        
                        local_paths = []
                        safe_name = clean_filename(f"{brand}_{model}_{year}")
                        unique_id = int(time.time() * 1000) % 100000 
                        car_folder = os.path.join(IMAGES_ROOT, f"{safe_name}_{unique_id}")

                        for idx, img_url in enumerate(image_urls):
                            path = download_file_python(img_url, car_folder, idx+1)
                            if path: local_paths.append(path)

                        row_data["Image Paths"] = "; ".join(local_paths)
                    
                    except Exception as e:
                        print(f"      ⚠️ [W{batch_id}] Image error: {e}")
                        row_data["Image Paths"] = ""

                    # 7. SUCCESS - SAVE ROW
                    results.append(row_data)
                    link_success = True
                    print(f"    ✅ [W{batch_id}] SAVED: {brand} {model} | Trim: {row_data['Trim']}")
                    break # Break Page Retry Loop

                except Exception as e:
                    print(f"      ⚠️ [W{batch_id}] Error attempt {attempt+1}: {e}")
                    # If failed, reload page and try again
                    if attempt < MAX_RETRIES_LINK - 1:
                        print(f"      🔄 [W{batch_id}] Reloading Page...")
                        try: page.reload(timeout=30000)
                        except: pass
                        time.sleep(3)
                    else:
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

    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
            writer.writeheader()

    batches = [urls[i:i + LINKS_PER_WORKER] for i in range(0, len(urls), LINKS_PER_WORKER)]
    
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, batch in enumerate(batches):
            futures.append(executor.submit(process_batch, batch, i+1))
        
        for future in as_completed(futures):
            try:
                batch_results, batch_failed = future.result()
                
                # Write Results Immediately
                with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
                    for row in batch_results:
                        writer.writerow(row)
                
                if batch_failed:
                    with open(FAILED_LINKS_FILE, "a", encoding="utf-8") as f:
                        for link in batch_failed:
                            f.write(link + "\n")
                            
            except Exception as e:
                print(f"❌ Critical Worker Failure: {e}")

    print("\n🎉 All processing complete.")

if __name__ == "__main__":
    run_workers()