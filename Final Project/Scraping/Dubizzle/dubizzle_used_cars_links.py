import time
import random
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# --- Configuration ---
SEARCH_URL = "https://www.dubizzle.com.eg/en/vehicles/cars-for-sale/used/"
DOMAIN_URL = "https://www.dubizzle.com.eg"
OUTPUT_FILE = "dubizzle_links_full.txt"

# !!! SAFETY UPDATE: Reduced to 2 !!!
NUM_WORKERS = 2

# Set to False to scrape ALL pages
TEST_MODE = False

def create_stealth_browser(p):
    browser = p.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--start-maximized', 
            '--no-sandbox',
            '--disable-infobars'
        ]
    )
    
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='Africa/Cairo',
        device_scale_factor=1,
    )
    
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context

def get_total_pages():
    print("--- Discovery Phase: Finding total pages ---")
    max_page = 1
    
    with sync_playwright() as p:
        browser, context = create_stealth_browser(p)
        page = context.new_page()
        
        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded")
            time.sleep(5) # Increased discovery wait
            
            if "error.html" in page.url:
                print("!!! BLOCKED: Redirected to error.html during discovery !!!")
                return 0

            try:
                page.wait_for_selector('div[role="navigation"]', state="attached", timeout=10000)
                pagination_texts = page.locator('div[role="navigation"] a').all_inner_texts()
                
                page_numbers = []
                for text in pagination_texts:
                    clean_text = re.sub(r'\D', '', text)
                    if clean_text:
                        page_numbers.append(int(clean_text))
                
                if page_numbers:
                    max_page = max(page_numbers)
                    print(f"Discovery successful: Found {max_page} total pages.")
            except:
                print("Pagination not found. Defaulting to 1 page.")
                return 1

        except Exception as e:
            print(f"Error during discovery: {e}")
        finally:
            browser.close()
            
    return max_page

def scrape_batch(page_numbers, worker_id):
    # Stagger Start: Worker 1 (0s), Worker 2 (5s wait)
    start_delay = (worker_id - 1) * 5
    if start_delay > 0:
        print(f"[Worker {worker_id}] Pausing {start_delay}s to start safely...")
        time.sleep(start_delay)

    found_links = set()
    print(f"[Worker {worker_id}] Started. Handling {len(page_numbers)} pages.")

    with sync_playwright() as p:
        browser, context = create_stealth_browser(p)
        page = context.new_page()

        for index, current_page in enumerate(page_numbers):
            
            # Refresh browser every 15 pages to stay fresh
            if index > 0 and index % 15 == 0:
                print(f"[Worker {worker_id}] Refreshing browser session...")
                page.close()
                context.close()
                browser.close()
                browser, context = create_stealth_browser(p)
                page = context.new_page()

            target_url = SEARCH_URL if current_page == 1 else f"{SEARCH_URL}?page={current_page}"

            try:
                for attempt in range(2):
                    try:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                        
                        if "error.html" in page.url:
                            raise Exception("Blocked: Redirected to error.html")

                        page.mouse.wheel(0, 500)
                        time.sleep(1) # Wait longer after scroll

                        page.wait_for_selector('a[href^="/en/ad/"]', state="attached", timeout=15000)
                        
                        if page.locator('a[href^="/en/ad/"]').count() > 0:
                            break
                        else:
                            time.sleep(2) 
                    except Exception as e:
                        if attempt == 1: raise e
                        print(f"[Worker {worker_id}] Retrying page {current_page}...")
                        time.sleep(5) # Increased retry sleep

                ad_links = page.locator('a[href^="/en/ad/"]')
                count = ad_links.count()
                new_links_on_page = 0
                
                for i in range(count):
                    link_element = ad_links.nth(i)
                    relative_href = link_element.get_attribute("href")

                    if relative_href:
                        full_link = f"{DOMAIN_URL}{relative_href}"
                        if full_link not in found_links:
                            found_links.add(full_link)
                            new_links_on_page += 1
                
                print(f"[Worker {worker_id}] Page {current_page} done (+{new_links_on_page} links)")

            except Exception as e:
                print(f"[Worker {worker_id}] Failed Page {current_page}: {e}")
                if "Blocked" in str(e):
                    print(f"!!! WORKER {worker_id} BLOCKED. EXITING TO SAVE OTHERS. !!!")
                    break

            # SAFETY SLEEP: Increased to 4-8 seconds
            time.sleep(random.uniform(4.0, 8.0))

        browser.close()
        print(f"[Worker {worker_id}] Finished.")
        
    return found_links

def main():
    total_pages = get_total_pages()
    if total_pages == 0: return

    if TEST_MODE:
        total_pages = min(total_pages, 2)

    all_pages = list(range(1, total_pages + 1))
    
    active_workers = min(NUM_WORKERS, len(all_pages))
    chunk_size = len(all_pages) // active_workers + (1 if len(all_pages) % active_workers > 0 else 0)
    batches = [all_pages[i:i + chunk_size] for i in range(0, len(all_pages), chunk_size)]

    global_unique_links = set()

    print(f"\n--- Execution Phase ---")
    print(f"Goal: {total_pages} pages using {active_workers} workers.")
    
    with ProcessPoolExecutor(max_workers=active_workers) as executor:
        futures = []
        for i, batch in enumerate(batches):
            if batch:
                futures.append(executor.submit(scrape_batch, batch, i+1))

        for future in as_completed(futures):
            try:
                links = future.result()
                global_unique_links.update(links)
            except Exception as e:
                print(f"Worker failed: {e}")

    print(f"\n--- Saving ---")
    print(f"Total unique links collected: {len(global_unique_links)}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(global_unique_links):
            f.write(link + "\n")
            
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()