import time
import random
from playwright.sync_api import sync_playwright

# ==============================
# CONFIG
# ==============================
BASE_URL = "https://www.contactcars.com"

BRANDS = [
    "aito", "alfa_romeo", "arcfox", "audi", "avatr", "baic", "bak", "baw", "bmw", "byd",
    "bentley", "bestune", "cadillac", "changan", "chery", "chevrolet", "citroen", "cupra",
    "dfsk", "ds", "deepal", "dodge", "dongfeng", "dongfeng_aeolus", "exeed", "fangchengbao",
    "ferrari", "fiat", "ford", "forthing", "foton", "gac", "gmc", "geely", "genesis", "haval",
    "honda", "hongqi", "hummer", "hyundai", "im_motors", "isuzu", "jac", "jaguar", "jeep",
    "jetour", "kgm", "kyc", "kaiyi", "kia", "lamborghini", "land_rover", "leapmotor",
    "li_auto", "lotus", "lynk_&_co", "m_hero", "mg", "maserati", "mazda", "mercedes", "mini",
    "mitsubishi", "nissan", "opel", "peugeot", "porsche", "proton", "rox", "range_rover",
    "renault", "rolls_royce", "sandstorm", "seat", "shineray", "skoda", "smart", "soueast",
    "ssangyong", "subaru", "suzuki", "tesla", "toyota", "vgv", "volkswagen", "volvo",
    "voyah", "wingamm", "xpeng", "zeekr", "xiaomi"
]

def scrape_brand_stealth(page, brand):
    url = f"{BASE_URL}/en/new-cars/{brand}"
    print(f"\n🚙 Starting brand: {brand.upper()}")
    
    try:
        # Randomized wait before loading to mimic human delay
        time.sleep(random.uniform(2, 4))
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"   ❌ Failed to load {brand} (Might be empty or invalid): {e}")
        return set()

    brand_links = set()
    page_num = 1

    while True:
        print(f"   📄 Scraping Page {page_num}...")
        
        # 1. Human-like Scrolling
        # Scroll down in chunks to ensure lazy-loaded elements appear
        for _ in range(4):
            page.mouse.wheel(0, random.randint(400, 900))
            time.sleep(random.uniform(0.6, 1.2))
        
        # 2. Extract Links (Universal Selector)
        links_locator = page.locator('a[href*="/new-cars/"]')
        count_before = len(brand_links)
        
        for i in range(links_locator.count()):
            try:
                href = links_locator.nth(i).get_attribute("href")
                
                # === FILTERING LOGIC ===
                # 1. Depth Check: Must have at least 4 slashes (e.g. /en/new-cars/brand/id)
                # 2. Exclusion Check: Must NOT contain "/for-sale" (used cars/dealer listings)
                if href and href.count("/") >= 4 and "/for-sale" not in href:
                    
                    if href.startswith("/"):
                        full_url = f"{BASE_URL}{href}"
                    else:
                        full_url = href
                    
                    brand_links.add(full_url)
            except:
                continue

        print(f"      Found {len(brand_links) - count_before} new links (Total: {len(brand_links)})")

        # 3. Handle Pagination
        # Specific SVG path for the "Next" arrow found on ContactCars
        next_arrow_path = "M14.43 5.93L20.5 12l-6.07 6.07M3.5 12h16.83"
        next_btn_selector = f'button.p-2.h-10.rounded.border.border-brand-100:has(svg path[d="{next_arrow_path}"])'
        next_buttons = page.locator(next_btn_selector)
        
        clicked = False
        
        # Loop to find the visible, enabled button
        for i in range(next_buttons.count()):
            btn = next_buttons.nth(i)
            if btn.is_visible() and not btn.is_disabled():
                try:
                    # Move mouse to button before clicking (Anti-Bot behavior)
                    box = btn.bounding_box()
                    if box:
                        page.mouse.move(box['x'] + 10, box['y'] + 10)
                    
                    btn.click()
                    clicked = True
                    
                    # Random wait for next page load
                    time.sleep(random.uniform(3, 5)) 
                    page_num += 1
                    break
                except:
                    continue
        
        if not clicked:
            print("      ⏹️ Finished (No more pages).")
            break

    return brand_links

def main():
    # ⚠️ TIP: If you get 403 errors immediately, switch to a mobile hotspot for a new IP.
    
    with sync_playwright() as p:
        # Launch options to hide the "AutomationControlled" flag
        browser = p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768}
        )
        
        # === MANUAL STEALTH INJECTION ===
        # Hides the webdriver property to avoid detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()

        all_links = set()

        for idx, brand in enumerate(BRANDS, 1):
            print(f"[{idx}/{len(BRANDS)}] Processing...")
            links = scrape_brand_stealth(page, brand)
            all_links.update(links)
            
            # Short pause between brands
            time.sleep(random.uniform(3, 6))

        browser.close()

        output_file = "contactcars_links_full.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for link in sorted(all_links):
                f.write(link + "\n")
        
        print("\n" + "="*40)
        print(f"✅ SCRAPING COMPLETE")
        print(f"🔗 Total Unique Links Found: {len(all_links)}")
        print(f"📂 Saved to: {output_file}")
        print("="*40)

if __name__ == "__main__":
    main()