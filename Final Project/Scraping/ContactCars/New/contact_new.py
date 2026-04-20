import os
import csv
import time
import random
import requests
import urllib.parse
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
LINKS_FILE = "contactcars_links_full.txt"
CSV_FILENAME = "new_cars_data.csv"
BASE_IMAGE_FOLDER = "images"

TARGET_SECTIONS = [
    "Shape & Dimensions", 
    "Performance Overview", 
    "ICE Powertrain", 
    "Drivetrain"
]

HEADERS = [
    "Brand", "Model", "Year", "Price", "Trim", "URL", "Image Paths",
    "Length (mm)", "Width (mm)", "Height (mm)", "Wheelbase (mm)",
    "Number of Seats", "Combined Maximum Power (HP @ RPM)", 
    "Combined Maximum Torque (N.m @ RPM)", "Maximum Speed (Km/h)", 
    "Acceleration (0 - 100 km/h)", "Fuel Tank Capacity (Litre)", 
    "Combined Fuel/Energy Consumption (Liter/100 KM)", 
    "Cylinders", "Recommend Fuel Grade", "Number of Gears"
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

def download_images(image_urls, car_folder_name):
    """Downloads images into a specific subfolder for each car."""
    # Sanitize folder name (remove characters that are invalid for Windows/Linux paths)
    folder = os.path.join(BASE_IMAGE_FOLDER, "".join(x for x in car_folder_name if x.isalnum() or x in "._- "))
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    saved_paths = []
    for idx, url in enumerate(image_urls):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                ext = "jpg"
                if ".png" in url: ext = "png"
                elif ".webp" in url: ext = "webp"
                
                filename = os.path.join(folder, f"car_img_{idx+1}.{ext}")
                with open(filename, 'wb') as f:
                    f.write(response.content)
                saved_paths.append(filename)
        except Exception as e:
            print(f"    ⚠️ Failed to download {url}: {e}")
            
    return saved_paths

# ==============================
# MAIN SCRAPER LOGIC
# ==============================

def scrape_car(page, url):
    print(f"🚙 Processing: {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(random.uniform(2, 4))
    except Exception as e:
        print(f"❌ Error loading {url}: {e}")
        return None

    # Step 1: Basic Info
    try:
        full_title = clean_text(page.locator("h1.text-brand-700.h-500").first.inner_text())
        price = clean_text(page.locator("h3.h-500.text-brand").first.inner_text())
        trim = clean_text(page.locator("h4.text-brand-700.txt-sm").first.inner_text())
    except:
        full_title, price, trim = "N/A", "N/A", "N/A"

    parts = full_title.split()
    if len(parts) >= 3 and parts[-1].isdigit():
        year, brand, model = parts[-1], parts[0], " ".join(parts[1:-1])
    else:
        brand, year, model = full_title, "N/A", "N/A"

    # Step 2: Images
    img_urls = set()
    carousel_imgs = page.locator("#car-details-carousel img").all()
    for img in carousel_imgs:
        src = img.get_attribute("src")
        real_url = extract_real_url(src)
        if real_url and "contactcars.fra1.cdn" in real_url:
            img_urls.add(real_url)
    
    # Download images into a folder named after the car (e.g., "Mercedes C180")
    local_image_paths = download_images(img_urls, full_title)
    image_paths_string = "; ".join(local_image_paths)

    # Step 3: Open Specs
    try:
        specs_button = page.locator("button", has_text="Detailed Specs")
        if specs_button.is_visible():
            specs_button.click()
            time.sleep(1.5)
    except: pass

    # Step 4: Extract Technical Specs
    scraped_specs = page.evaluate("""() => {
        const data = {};
        const rows = document.querySelectorAll('div.flex.items-center.justify-between.text-brand-700.border-b');
        rows.forEach(row => {
            const labelEl = row.querySelector('h5');
            const valueEl = row.querySelector('h4');
            if (labelEl && valueEl) {
                data[labelEl.innerText.trim()] = valueEl.innerText.trim();
            }
        });
        return data;
    }""")

    spec_data = {k: "N/A" for k in HEADERS if k not in ["Brand", "Model", "Year", "Price", "Trim", "URL", "Image Paths"]}
    for js_label, js_value in scraped_specs.items():
        for header_key in spec_data.keys():
            clean_header = header_key.split("(")[0].strip()
            if clean_header.lower() == js_label.split("(")[0].strip().lower():
                 spec_data[header_key] = js_value

    return {
        "Brand": brand, "Model": model, "Year": year, "Price": price, 
        "Trim": trim, "URL": url, "Image Paths": image_paths_string, **spec_data
    }

def run():
    # Read links from file
    if not os.path.exists(LINKS_FILE):
        print(f"❌ Error: {LINKS_FILE} not found.")
        return

    with open(LINKS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"📂 Found {len(urls)} links to scrape.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768}
        )
        page = context.new_page()

        # Initialize CSV and write headers
        file_exists = os.path.isfile(CSV_FILENAME)
        with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            if not file_exists:
                writer.writeheader()

            for url in urls:
                car_data = scrape_car(page, url)
                if car_data:
                    writer.writerow(car_data)
                    f.flush() # Ensure data is written to disk immediately
                    print(f"✅ Saved: {car_data['Brand']} {car_data['Model']}")
                
                # Random delay between cars to avoid detection
                time.sleep(random.uniform(1, 3))

        browser.close()
        print(f"\n✨ All done! Data saved to {CSV_FILENAME}")

if __name__ == "__main__":
    run()