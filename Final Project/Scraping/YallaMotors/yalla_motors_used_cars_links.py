import time
import random
import re
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# ==============================
# CONFIGURATION
# ==============================
SEARCH_URL = "https://egypt.yallamotor.com/used-cars/search"
DOMAIN_URL = "https://egypt.yallamotor.com"
OUTPUT_FILE = "yallamotor_complete_links.txt"
NUM_WORKERS = 4 

# ==============================
# 1. DISCOVERY PHASE
# ==============================
def get_total_pages():
    print("--- 🔍 Discovery Phase: Finding total car count ---")
    total_pages = 1
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded")
            
            # Target the header text
            target_locator = page.locator("span").filter(has_text=re.compile(r"Used & New Cars For Sale"))
            target_locator.first.wait_for(state="attached", timeout=15000)
            
            info_text = target_locator.first.text_content()
            print(f"   Found header text: '{info_text}'")
            
            # Extract number (e.g., "4,775")
            match = re.search(r"([\d,]+)\s+Used\s*&\s*New", info_text)
            
            if match:
                total_cars_str = match.group(1).replace(',', '')
                total_cars = int(total_cars_str)
                items_per_page = 22
                
                # Add a buffer of 3 extra pages just to be safe
                total_pages = math.ceil(total_cars / items_per_page) + 3
                print(f"   ✅ Discovery Successful: {total_cars} cars. Calculated {total_pages} pages (with buffer).")
            else:
                print("   ⚠️ Regex failed. Defaulting to 1 page.")

        except Exception as e:
            print(f"   ❌ Discovery Error: {e}")
            total_pages = 0
        finally:
            browser.close()
            
    return total_pages

# ==============================
# 2. WORKER FUNCTION
# ==============================
def scrape_batch(page_numbers, worker_id):
    found_links = set()
    print(f"[Worker {worker_id}] 🚀 Started. Handling {len(page_numbers)} pages.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        for current_page in page_numbers:
            # Construct URL
            if current_page == 1:
                target_url = SEARCH_URL
            else:
                target_url = f"{SEARCH_URL}?page={current_page}"

            try:
                # Retry logic
                for attempt in range(2):
                    try:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                        
                        # 1. Wait for first item
                        page.locator('a.hover\:text-main').first.wait_for(state="attached", timeout=15000)
                        
                        # 2. Scroll to bottom to trigger lazy loading
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1.5) # Wait for bottom items to populate
                        
                        break
                    except:
                        if attempt == 1: raise
                        time.sleep(2)

                # Extraction
                elements = page.locator('a.hover\:text-main').all()
                new_count = 0
                
                for element in elements:
                    href = element.get_attribute("href")
                    # Ensure it's a valid car link
                    if href and "/used-cars/" in href and "utm_source" in href:
                        if href.startswith("/"):
                            full_link = f"{DOMAIN_URL}{href}"
                        else:
                            full_link = href
                        
                        clean_link = full_link.split('?')[0]
                        found_links.add(clean_link)
                        new_count += 1
                
                print(f"[Worker {worker_id}] ✅ Page {current_page} done. (+{new_count} links)")

            except Exception as e:
                print(f"[Worker {worker_id}] ❌ Failed Page {current_page}: {e}")

            # Short sleep to prevent IP ban
            time.sleep(random.uniform(1.0, 2.5))

        browser.close()
        print(f"[Worker {worker_id}] 🏁 Finished.")
        
    return found_links

# ==============================
# 3. MAIN CONTROLLER
# ==============================
def main():
    total_pages = get_total_pages()
    
    if total_pages == 0:
        print("Discovery failed. Exiting.")
        return

    all_pages = list(range(1, total_pages + 1))
    
    # Split work
    chunk_size = math.ceil(len(all_pages) / NUM_WORKERS)
    batches = [all_pages[i:i + chunk_size] for i in range(0, len(all_pages), chunk_size)]

    global_links = set()

    print(f"\n--- ⚙️ Execution Phase ---")
    print(f"Distributing {total_pages} pages across {len(batches)} workers.")

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for i, batch in enumerate(batches):
            if batch:
                futures.append(executor.submit(scrape_batch, batch, i+1))

        for future in as_completed(futures):
            try:
                links = future.result()
                global_links.update(links)
            except Exception as e:
                print(f"Worker crashed: {e}")

    print(f"\n--- 💾 Saving ---")
    print(f"Total unique links collected: {len(global_links)}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(global_links):
            f.write(link + "\n")
            
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()