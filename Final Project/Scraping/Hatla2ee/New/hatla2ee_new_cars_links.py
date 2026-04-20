import time
import random
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# --- Configuration ---
# Updated for New Cars
SEARCH_URL = "https://eg.hatla2ee.com/en/new-car/search"
DOMAIN_URL = "https://eg.hatla2ee.com"
NUM_WORKERS = 4
OUTPUT_FILE = "new_car_links.txt"

def get_total_pages():
    """
    Scrapes the first page to find the total number of pages from the pagination bar.
    """
    print("--- Discovery Phase: Finding total pages ---")
    max_page = 1
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            page.goto(SEARCH_URL, wait_until="domcontentloaded")
            
            # Wait for pagination to appear
            page.wait_for_selector('nav[aria-label="pagination"]', timeout=15000)
            
            # Get all text from pagination links
            pagination_texts = page.locator('nav[aria-label="pagination"] li a').all_inner_texts()
            
            # Filter and convert to integers
            page_numbers = []
            for text in pagination_texts:
                clean_text = re.sub(r'\D', '', text)
                if clean_text:
                    page_numbers.append(int(clean_text))
            
            if page_numbers:
                max_page = max(page_numbers)
                print(f"Discovery successful: Found {max_page} total pages.")
            else:
                print("Could not extract numbers from pagination. Defaulting to 1.")

        except Exception as e:
            print(f"Error during discovery: {e}")
        finally:
            browser.close()
            
    return max_page

def scrape_batch(page_numbers, worker_id):
    """
    Worker function: Scrapes a specific list of page numbers.
    """
    found_links = set()
    print(f"[Worker {worker_id}] Started. Handling {len(page_numbers)} pages.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        for current_page in page_numbers:
            # Construct URL (Changed '&' to '?' because the base URL has no params)
            if current_page == 1:
                target_url = SEARCH_URL
            else:
                target_url = f"{SEARCH_URL}?page={current_page}"

            try:
                # Retry logic
                for attempt in range(2):
                    try:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
                        # Updated selector: Target the main card container
                        page.wait_for_selector('div[data-slot="card"]', timeout=15000)
                        break 
                    except:
                        if attempt == 1: raise 
                        time.sleep(2)

                # Locate all car cards
                cards = page.locator('div[data-slot="card"]')
                count = cards.count()
                
                new_links_on_page = 0

                for i in range(count):
                    card = cards.nth(i)
                    
                    # Updated selector: The link is now inside the 'card-header' slot
                    # We check specifically for the 'a' tag inside the header
                    link_locator = card.locator('div[data-slot="card-header"] a').first
                    
                    # IMPORTANT: Check if the link exists.
                    # This prevents the script from crashing on the "Sell My Car" banner/card
                    # which has data-slot="card" but NO card-header.
                    if link_locator.count() > 0:
                        relative_href = link_locator.get_attribute("href")

                        if relative_href:
                            full_link = f"{DOMAIN_URL}{relative_href}"
                            found_links.add(full_link)
                            new_links_on_page += 1
                
                print(f"[Worker {worker_id}] Page {current_page} complete. (+{new_links_on_page} links)")

            except Exception as e:
                print(f"[Worker {worker_id}] Failed Page {current_page}: {e}")

            time.sleep(random.uniform(1.5, 3.5))

        browser.close()
        print(f"[Worker {worker_id}] Finished.")
        
    return found_links

def main():
    # 1. Discovery Phase
    total_pages = get_total_pages()
    
    if total_pages == 0:
        print("No pages found. Exiting.")
        return

    # 2. Distribution Phase
    all_pages = list(range(1, total_pages + 1))
    
    chunk_size = len(all_pages) // NUM_WORKERS + (len(all_pages) % NUM_WORKERS > 0)
    batches = [all_pages[i:i + chunk_size] for i in range(0, len(all_pages), chunk_size)]

    global_unique_links = set()

    print(f"\n--- Execution Phase ---")
    print(f"Distributing {total_pages} pages across {NUM_WORKERS} workers.")

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for i, batch in enumerate(batches):
            if batch:
                futures.append(executor.submit(scrape_batch, batch, i+1))

        # 3. Collection Phase
        for future in as_completed(futures):
            try:
                links = future.result()
                global_unique_links.update(links)
            except Exception as e:
                print(f"Worker failed: {e}")

    # 4. Save to file
    print(f"\n--- Saving ---")
    print(f"Total unique links collected: {len(global_unique_links)}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(global_unique_links):
            f.write(link + "\n")
            
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()