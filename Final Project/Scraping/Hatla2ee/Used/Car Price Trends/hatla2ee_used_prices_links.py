import time
import random
from playwright.sync_api import sync_playwright

# ==============================
# CONFIG
# ==============================
BASE_URL = "https://eg.hatla2ee.com"
START_URL = "https://eg.hatla2ee.com/en/car/used-prices"

def scrape_hatla2ee_links(page):
    print(f"🚙 Starting: {START_URL}")
    
    try:
        # Initial load
        page.goto(START_URL, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"   ❌ Failed to load site: {e}")
        return set()

    all_car_links = set()
    page_num = 1

    while True:
        print(f"   📄 Scraping Page {page_num}...")
        
        # Human-like scrolling behavior (helps trigger lazy loading if present)
        for _ in range(2):
            page.mouse.wheel(0, random.randint(500, 1000))
            time.sleep(random.uniform(0.5, 1.0))
        
        # ==============================
        # UPDATED LINK SELECTOR
        # ==============================
        # Targets the <a> tag inside the <td data-slot="table-cell"> that has the 'text-primary' class
        links_locator = page.locator('td[data-slot="table-cell"].text-primary a')
        
        try:
            # Wait for at least one link to be present
            links_locator.first.wait_for(timeout=5000)
        except:
            print("      ⚠️ No links found on this page. Ending.")
            break

        count_before = len(all_car_links)
        current_page_links = links_locator.all()
        
        for link in current_page_links:
            try:
                href = link.get_attribute("href")
                if href:
                    # Construct full URL
                    full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                    all_car_links.add(full_url)
            except:
                continue

        print(f"      Found {len(all_car_links) - count_before} new links (Total: {len(all_car_links)})")

        # ==============================
        # PAGINATION LOGIC
        # ==============================
        # The selector matches the HTML provided: 
        # <li data-slot="pagination-item"><a ...><svg class="lucide lucide-chevron-right ...">
        next_btn = page.locator('li[data-slot="pagination-item"] a:has(svg.lucide-chevron-right)').last
        
        # 1. Check if button exists
        if next_btn.count() == 0:
            print("      ⏹️ No Next button found (Selector mismatch). Finishing.")
            break

        # 2. Check if visible
        if not next_btn.is_visible():
            print("      ⏹️ Next button exists but is hidden. Finishing.")
            break

        # 3. Validation: Check href presence
        href_attr = next_btn.get_attribute("href")
        
        # If href is missing, empty, or just "#", we are at the end
        if not href_attr or href_attr == "#":
            print("      ⏹️ Reached the last page (No valid href).")
            break
            
        try:
            # 4. Navigate
            print(f"      ➡️ Navigating to Page {page_num + 1}...")
            
            next_btn.scroll_into_view_if_needed()
            
            # Click and wait for URL change
            with page.expect_navigation(timeout=15000):
                 next_btn.click()
            
            page_num += 1
            
            # Random delay for stealth
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"      ⏹️ Stopped/Error during navigation: {e}")
            break

    return all_car_links

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Stealth Injection
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        
        page = context.new_page()
        links = scrape_hatla2ee_links(page)
        browser.close()

        # Save results to file
        filename = "hatla2ee_used_prices_links.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for link in sorted(links):
                f.write(link + "\n")
        
        print(f"\n✅ Success! Total links found: {len(links)}")
        print(f"📂 Saved to: {filename}")

if __name__ == "__main__":
    main()