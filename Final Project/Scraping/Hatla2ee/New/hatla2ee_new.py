import os
import csv
import time
import base64
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
LINKS_FILE = "new_car_links.txt"
CSV_FILENAME = "hatla2ee_all_cars.csv"
IMAGES_ROOT = "images"

# WORKER SETTINGS
MAX_WORKERS = 5          # How many Chrome browsers to run at the same time
LINKS_PER_WORKER = 5     # How many links one browser processes before restarting
MAX_RETRIES = 3          # NUMBER OF TIMES TO RETRY A FAILED PAGE

HEADERS = [
    "Car Title", "Brand", "Model", "Price", "Year", "Trim", "Transmission", 
    "Fuel Type", "Body Type", "Power", "Speeds", "Horsepower", 
    "Fuel", "Consumption", "Width", "Length", "Height", 
    "Wheel Base", "Seats", "Number of Cylinders", 
    "Fuel Tank Capacity", "Torque", "Acceleration", "Image Paths", "URL"
]

def clean_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "", text).replace(" ", "_").strip()

def download_images_sync(page, image_urls, folder):
    """Downloads images using the browser context in the worker."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    saved_paths = []
    
    for idx, url in enumerate(image_urls):
        if not url: continue
        
        # dynamic replacement for thumbnails if they exist, preserving extension
        url = re.sub(r'thumbnail\.(jpg|jpeg|png|webp)', r'large.\1', url)
        
        # Extract extension from URL (default to .jpg if not found)
        ext_match = re.search(r'\.(jpg|jpeg|png|webp)$', url, re.IGNORECASE)
        ext = ext_match.group(1) if ext_match else "jpg"

        try:
            base64_data = page.evaluate("""async (url) => {
                try {
                    const response = await fetch(url, {mode: 'no-cors'});
                    const responseStandard = await fetch(url);
                    if (responseStandard.status !== 200) return null;
                    const blob = await responseStandard.blob();
                    return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                } catch (err) { return null; }
            }""", url)

            if base64_data:
                header, encoded = base64_data.split(",", 1)
                data = base64.b64decode(encoded)
                
                # Save with the correct detected extension
                filename = os.path.join(folder, f"img_{idx+1}.{ext}")
                
                with open(filename, 'wb') as f:
                    f.write(data)
                saved_paths.append(filename)
            
            time.sleep(0.1)
        except Exception:
            pass # Silent fail for images to keep speed up
            
    return saved_paths

def process_batch(urls_batch, batch_id):
    """
    This function runs inside a separate process (Worker).
    """
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-web-security", "--disable-features=IsolateOrigins,site-per-process"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"⚙️ Worker {batch_id} started processing {len(urls_batch)} links...")

        for current_url in urls_batch:
            # === RETRY LOGIC START ===
            page_loaded = False
            for attempt in range(MAX_RETRIES):
                try:
                    response = page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
                    
                    # Check if the server returned a 500-level error (Bad Gateway, Internal Error, etc.)
                    if response and response.status >= 500:
                        print(f"⚠️ Worker {batch_id}: Got status {response.status} for {current_url}. Retrying ({attempt+1}/{MAX_RETRIES})...")
                        time.sleep(3) # Wait 3 seconds before retrying
                        continue

                    page_loaded = True
                    break # Success, exit retry loop

                except Exception as e:
                    print(f"⚠️ Worker {batch_id}: Network error on {current_url}: {e}. Retrying ({attempt+1}/{MAX_RETRIES})...")
                    time.sleep(3)
            
            if not page_loaded:
                print(f"❌ Worker {batch_id}: Failed to load {current_url} after {MAX_RETRIES} attempts. Skipping.")
                continue
            # === RETRY LOGIC END ===

            try:
                # --- 1. Title ---
                h1_text = ""
                try:
                    if page.locator("h1").first.is_visible():
                        h1_text = page.locator("h1").first.inner_text().strip()
                except: pass

                # --- 2. Identity (Brand/Model) ---
                brand, model = "Unknown", "Unknown"
                try:
                    parts = page.url.split('/')
                    if 'new-car' in parts:
                        idx = parts.index('new-car')
                        if len(parts) > idx + 1: brand = parts[idx + 1].replace("-", " ").title().strip()
                        if len(parts) > idx + 2: model = parts[idx + 2].replace("-", " ").title().split('?')[0].strip()
                except: pass

                # --- 3. Year ---
                year_val = "2025"
                year_match = re.search(r'\b(20\d{2})\b', h1_text)
                if year_match: year_val = year_match.group(1)

                # --- 4. Trim ---
                trim_val = h1_text
                clean_h1 = " ".join(h1_text.split())
                for item in [brand, model, year_val]:
                    trim_val = re.sub(re.escape(item), "", trim_val, flags=re.IGNORECASE)
                
                junk_phrases = ["New Cash or Installment", "Cash or Installment", "New", "Cash", "Installment", " or "]
                for junk in junk_phrases:
                    trim_val = re.sub(re.escape(junk), "", trim_val, flags=re.IGNORECASE)
                
                if "/" in trim_val: trim_val = trim_val.split("/")[-1]
                trim_val = re.sub(r'^[^\w]+|[^\w]+$', '', trim_val).strip()
                if not trim_val or len(trim_val) < 2: trim_val = "Baseline"

                # --- 5. Price ---
                price_val = "N/A"
                try:
                    price_el = page.locator("span.text-2xl span.leading-none.font-bold").first
                    if price_el.is_visible():
                        price_val = price_el.inner_text().strip()
                except: pass

                # --- 6. Specs ---
                raw_specs = page.evaluate("""() => {
                    const results = {};
                    const rows = document.querySelectorAll('#car-details div[class*="-mt-[1px]"]');
                    rows.forEach(row => {
                        const labelEl = row.querySelector('.text-muted-foreground');
                        const valueEl = row.querySelector('.font-medium');
                        if (labelEl && valueEl) results[labelEl.innerText.trim()] = valueEl.innerText.trim();
                    });
                    return results;
                }""")

                # --- 7. Images ---
                safe_name = clean_filename(f"{brand}_{model}_{trim_val}")
                unique_id = int(time.time() * 1000) % 100000 
                car_folder = os.path.join(IMAGES_ROOT, f"{safe_name}_{unique_id}")

                try:
                    btn = page.locator("div.grid div:has-text('Show All')").last
                    if btn.is_visible(): 
                        btn.click()
                        time.sleep(0.5)
                except: pass
                
                content = page.content()
                
                # UPDATED REGEX: Now catches jpg, jpeg, png, webp
                image_urls = list(set(re.findall(r'https://legion-images\.hatla2ee\.com/original_image/[a-zA-Z0-9-]+/large\.(?:jpg|jpeg|png|webp)', content)))
                
                local_paths = download_images_sync(page, image_urls, car_folder)

                # --- 8. Build Row ---
                row = {
                    "Car Title": h1_text, "Brand": brand, "Model": model, "Price": f"{price_val} EGP",
                    "Year": year_val, "Trim": trim_val,
                    "Transmission": raw_specs.get("Transmission", "N/A"),
                    "Fuel Type": raw_specs.get("Fuel Type", "N/A"),
                    "Body Type": raw_specs.get("Body Type", "N/A"),
                    "Power": raw_specs.get("Power", "N/A"),
                    "Speeds": raw_specs.get("Speeds", "N/A"),
                    "Horsepower": raw_specs.get("Horse power", "N/A"),
                    "Fuel": raw_specs.get("Fuel", "N/A"),
                    "Consumption": raw_specs.get("Consumption", "N/A"),
                    "Width": raw_specs.get("Width", "N/A"),
                    "Length": raw_specs.get("Length", "N/A"),
                    "Height": raw_specs.get("Height", "N/A"),
                    "Wheel Base": raw_specs.get("Wheel Base", "N/A"),
                    "Seats": raw_specs.get("Seats", "N/A"),
                    "Number of Cylinders": raw_specs.get("Number Of Cylinder", "N/A"),
                    "Fuel Tank Capacity": raw_specs.get("Fuel Tank Capacity", "N/A"),
                    "Torque": raw_specs.get("Torque Of Newton", "N/A"),
                    "Acceleration": raw_specs.get("Acceleration", "N/A"),
                    "Image Paths": "; ".join(local_paths),
                    "URL": current_url
                }
                results.append(row)
                print(f"    ✅ Worker {batch_id} finished: {brand} {model}")

            except Exception as e:
                print(f"    ❌ Worker {batch_id} processing failed on {current_url}: {e}")

        browser.close()
    
    return results

def run_workers():
    if not os.path.exists(LINKS_FILE):
        print("Link file not found")
        return
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"🔥 Loaded {len(urls)} links. Starting {MAX_WORKERS} Workers...")

    # --- 1. Initialize CSV with Headers (Run Once) ---
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
                
                if not batch_results:
                    continue

                # --- 2. Append Data (No Headers) ---
                with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=HEADERS)
                    # Note: writer.writeheader() is intentionally REMOVED here
                    for row in batch_results:
                        writer.writerow(row)
                        
            except Exception as e:
                print(f"❌ A batch failed completely: {e}")

    print("\n🎉 All workers completed.")

if __name__ == "__main__":
    run_workers()