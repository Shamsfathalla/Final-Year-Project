import time
import random
from playwright.sync_api import sync_playwright

# --- Configuration ---
SEARCH_URL = "https://biddex.com/search/vehicles/used?sale_type=fixed-price"
DOMAIN_URL = "https://biddex.com"
OUTPUT_FILE = "biddex_links_full.txt"

def create_stealth_browser(p):
    """
    Creates a browser context with stealth modifications to avoid detection.
    """
    browser = p.chromium.launch(
        headless=False,  # False to help bypass bot detection
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
    
    # Inject script to hide webdriver property
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)
    
    return browser, context

def scrape_infinite_scroll():
    print("--- Starting FULL Scraper for Biddex ---")
    print("This will run until the end of the list. Press Ctrl+C to stop early and save.")
    
    found_links = set()
    
    with sync_playwright() as p:
        browser, context = create_stealth_browser(p)
        page = context.new_page()
        
        try:
            print(f"Navigating to: {SEARCH_URL}")
            page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5) # Allow initial load

            if "error" in page.url or page.title() == "Access Denied":
                print("!!! BLOCKED: Access Denied on load !!!")
                return found_links

            no_change_count = 0
            
            while True:
                # 1. Scrape currently visible links
                cards = page.locator('a.item-sale-type-container[href^="/en/product/"]')
                count = cards.count()
                
                new_links_batch = 0
                for i in range(count):
                    try:
                        href = cards.nth(i).get_attribute("href")
                        if href:
                            full_link = f"{DOMAIN_URL}{href}"
                            if full_link not in found_links:
                                found_links.add(full_link)
                                new_links_batch += 1
                    except:
                        continue

                if new_links_batch > 0:
                    print(f"Collected {len(found_links)} unique cars... (+{new_links_batch} new)")
                    no_change_count = 0 # Reset counter if we found new links
                
                # 2. Scroll Logic
                previous_height = page.evaluate("document.body.scrollHeight")
                
                # Aggressive scroll down
                page.mouse.wheel(0, 5000) 
                time.sleep(random.uniform(1.5, 3.0)) 
                
                # Ensure we hit the absolute bottom to trigger HTMX/AJAX loader
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2) 

                # 3. Check if page grew
                new_height = page.evaluate("document.body.scrollHeight")
                
                if new_height == previous_height:
                    no_change_count += 1
                    print(f"No height change... (Attempt {no_change_count}/4)")
                    
                    # Try jiggle scroll to wake up lazy loader
                    if no_change_count < 4:
                        page.mouse.wheel(0, -700) # Scroll up a bit
                        time.sleep(1)
                        page.mouse.wheel(0, 700)  # Scroll back down
                        time.sleep(1.5)
                    else:
                        print("--- End of List Reached (or blocked) ---")
                        break
                
        except KeyboardInterrupt:
            print("\n!!! User interrupted script. Saving collected links... !!!")
        except Exception as e:
            print(f"An error occurred: {e}")
            
        finally:
            browser.close()
            
    return found_links

def main():
    print(f"\n--- Execution Phase ---")
    
    global_unique_links = scrape_infinite_scroll()
    
    if not global_unique_links:
        print("No links found.")
        return

    print(f"\n--- Saving ---")
    print(f"Total unique links collected: {len(global_unique_links)}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for link in sorted(global_unique_links):
            f.write(link + "\n")
            
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()