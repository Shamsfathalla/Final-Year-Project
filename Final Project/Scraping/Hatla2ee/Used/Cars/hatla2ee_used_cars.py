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
LINKS_FILE = "car_links.txt"
CSV_FILENAME = "hatla2ee_used_cars.csv"
IMAGES_ROOT = "images_used"

# WORKER SETTINGS
MAX_WORKERS = 4          
LINKS_PER_WORKER = 5     

HEADERS = [
    "Car Title", "Brand", "Model", "Price", "Year", "Trim", "Mileage", 
    "Condition", "Transmission", "Fuel Type", "CC", "Color", "Location",
    "Body Type", "Power", "Description Snippet", "Image Paths", "URL"
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
        
        # Force high resolution: replace thumbnail/medium/small with large
        url = re.sub(r'(thumbnail|medium|small)\.(jpg|jpeg|png|webp)', r'large.\2', url)
        
        # Extract extension
        ext_match = re.search(r'\.(jpg|jpeg|png|webp)$', url, re.IGNORECASE)
        ext = ext_match.group(1) if ext_match else "jpg"

        try:
            # Run fetch inside browser to avoid 403 Forbidden
            base64_data = page.evaluate("""async (url) => {
                try {
                    const response = await fetch(url);
                    if (response.status !== 200) return null;
                    const blob = await response.blob();
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
                
                filename = os.path.join(folder, f"img_{idx+1}.{ext}")
                with open(filename, 'wb') as f:
                    f.write(data)
                saved_paths.append(filename)
            
            time.sleep(0.1)
        except Exception:
            pass 
            
    return saved_paths

def process_batch(urls_batch, batch_id):
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
            try:
                page.goto(current_url, wait_until="domcontentloaded", timeout=45000)

                # --- 1. Title ---
                h1_text = "N/A"
                if page.locator("h1").first.is_visible():
                    h1_text = page.locator("h1").first.inner_text().strip()

                # --- 2. Overview Badges (Top Gray Boxes) ---
                overview_data = {
                    "Year": "N/A", "Mileage": "N/A", "Transmission": "N/A", "Fuel": "N/A"
                }
                
                badges = page.locator("#listing-overview div.bg-gray-50").all()
                for badge in badges:
                    text = badge.inner_text().strip()
                    if not text: continue
                    
                    if re.match(r'^\d{4}$', text):
                        overview_data["Year"] = text
                    elif "KM" in text or "Km" in text:
                        overview_data["Mileage"] = text
                    elif text in ["Automatic", "Manual", "CVT", "DSG", "Manual Automatic"]:
                        overview_data["Transmission"] = text
                    elif text in ["Gas", "Diesel", "Hybrid", "Electric", "Natural Gas"]:
                        overview_data["Fuel"] = text

                # --- 3. Specs Table ---
                raw_specs = page.evaluate("""() => {
                    const results = {};
                    const rows = document.querySelectorAll('#car-details div[class*="-mt-[1px]"]');
                    rows.forEach(row => {
                        const labelEl = row.querySelector('.text-muted-foreground');
                        const valueEl = row.querySelector('.font-medium');
                        if (labelEl && valueEl) {
                            results[labelEl.innerText.trim()] = valueEl.innerText.trim();
                        }
                    });
                    return results;
                }""")

                # --- 4. Description ---
                description_text = ""
                try:
                    desc_el = page.locator("#description")
                    if desc_el.is_visible():
                        description_text = desc_el.inner_text()
                except: pass

                # --- 5. Price ---
                price_val = "N/A"
                try:
                    price_el = page.locator("#listing-overview span.text-2xl span.leading-none.font-bold").first
                    if price_el.is_visible():
                        price_val = price_el.inner_text().strip()
                except: pass

                # --- Consolidation ---
                brand = raw_specs.get("Brand", "Unknown")
                model = raw_specs.get("Model", "Unknown")
                year_val = overview_data["Year"] if overview_data["Year"] != "N/A" else raw_specs.get("Year", "N/A")
                if year_val == "N/A":
                    year_match = re.search(r'\b(20\d{2}|19\d{2})\b', h1_text)
                    if year_match: year_val = year_match.group(1)

                cc_val = raw_specs.get("CC", "N/A")
                if cc_val == "N/A" or not cc_val:
                    cc_match = re.search(r'(\d{3,5})\s*(?:cc|CC|Cc)', description_text)
                    if cc_match: cc_val = cc_match.group(1)

                # --- 7. Images (RESTRICTED SCOPE FIX) ---
                safe_name = clean_filename(f"{brand}_{model}_{year_val}")
                unique_id = int(time.time() * 1000) % 100000 
                car_folder = os.path.join(IMAGES_ROOT, f"{safe_name}_{unique_id}")

                # Try to expand the gallery
                try:
                    btn = page.locator("div.grid div:has-text('Show All')").last
                    if btn.is_visible(): 
                        btn.click()
                        time.sleep(0.5)
                except: pass
                
                # 1. Capture content ONLY from the car image containers
                # This prevents scraping News/Ads images
                target_html = ""
                
                # A: The initial grid container (div.grid.mt-2...)
                grid_locator = page.locator("div.grid[class*='mt-2']") 
                if grid_locator.count() > 0:
                    target_html += grid_locator.first.inner_html()
                
                # B: The gallery slider container (div.touch-pan-y) - usually appears after click
                gallery_locator = page.locator("div.touch-pan-y")
                if gallery_locator.count() > 0:
                    target_html += gallery_locator.first.inner_html()

                # 2. Run Regex on the restricted HTML only
                image_urls = list(set(re.findall(r'https://legion-images\.hatla2ee\.com/(?:listing_image|original_image)/[a-zA-Z0-9-]+/(?:large|thumbnail|medium)\.(?:jpg|jpeg|png|webp)', target_html)))
                
                local_paths = download_images_sync(page, image_urls, car_folder)

                # --- 8. Build Row ---
                row = {
                    "Car Title": h1_text,
                    "Brand": brand,
                    "Model": model,
                    "Price": f"{price_val} EGP",
                    "Year": year_val,
                    "Trim": raw_specs.get("Class", "N/A"),
                    "Mileage": overview_data["Mileage"],
                    "Condition": raw_specs.get("Condition", "Used"),
                    "Transmission": overview_data["Transmission"],
                    "Fuel Type": overview_data["Fuel"],
                    "CC": cc_val,
                    "Color": raw_specs.get("Color", "N/A"),
                    "Location": raw_specs.get("Location", "N/A"),
                    "Body Type": raw_specs.get("Body Type", "N/A"),
                    "Power": raw_specs.get("Power", "N/A"),
                    "Description Snippet": description_text[:100].replace("\n", " ") + "...",
                    "Image Paths": "; ".join(local_paths),
                    "URL": current_url
                }
                results.append(row)
                print(f"    ✅ Worker {batch_id} finished: {brand} {model}")

            except Exception as e:
                print(f"    ❌ Worker {batch_id} failed on {current_url}: {e}")

        browser.close()
    
    return results

def run_workers():
    if not os.path.exists(LINKS_FILE):
        print(f"File {LINKS_FILE} not found!")
        return
        
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"🔥 Loaded {len(urls)} links. Starting {MAX_WORKERS} Workers...")

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
                print(f"❌ A batch failed completely: {e}")

    print("\n🎉 All workers completed.")

if __name__ == "__main__":
    run_workers()