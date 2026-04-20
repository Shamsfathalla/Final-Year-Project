import time
import random
from playwright.sync_api import sync_playwright

# ==============================
# CONFIG
# ==============================
BASE_URL = "https://www.contactcars.com"

BRANDS = [
    "aito", "alfa_romeo", "arcfox", "audi", "avatr", "baic", "bak", "baw", 
    "bentley", "bestune", "bmw", "brilliance", "byd", "cadillac", "caterham", 
    "chana", "changan", "chery", "chevrolet", "chrysler", "citroen", "cupra", 
    "daewoo", "daihatsu", "deepal", "dfsk", "dodge", "dongfeng", "dongfeng_aeolus", 
    "ds", "exeed", "fangchengbao", "faw", "ferrari", "fiat", "ford", "forthing", 
    "foton", "gac", "geely", "genesis", "gmc", "great_wall", "haima", "havi", 
    "haval", "hawtai", "honda", "hongqi", "hummer", "hyundai", "im_motors", 
    "isuzu", "jac", "jaguar", "jeep", "jetour", "jmc", "kaiyi", "kgm", "kia", 
    "kyc", "lada", "lamborghini", "land_rover", "leapmotor", "lexus", "li_auto", 
    "lincoln", "lotus", "lynk_&_co", "m_hero", "mahindra", "maserati", "mazda", 
    "mercedes", "mg", "mini", "mitsubishi", "nasr", "nissan", "opel", "peugeot", 
    "polestar", "porsche", "proton", "range_rover", "renault", "rolls_royce", 
    "rox", "saipa", "sandstorm", "seat", "senova", "shineray", "skoda", "smart", 
    "soueast", "ssangyong", "subaru", "suzuki", "tesla", "toyota", "vgv", 
    "volkswagen", "volvo", "voyah", "wingamm", "xiaomi", "xpeng", "zeekr", "zotye"
]

def scrape_brand_stealth(page, brand):
    url = f"{BASE_URL}/en/used-cars/{brand}"
    print(f"\n🚙 Starting brand: {brand}")
    
    try:
        # Initial sleep for anti-bot
        time.sleep(random.uniform(2, 4))
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"   ❌ Failed to load {brand}: {e}")
        return set()

    brand_links = set()
    page_num = 1

    while True:
        print(f"   📄 Scraping Page {page_num}...")

        # Wait for the presence of car cards
        try:
            page.wait_for_selector('.px-3.pt-2.bg-white-900', timeout=10000)
        except:
            print(f"      ⚠️ No more car cards or page failed to load for {brand}.")
            break

        # Human-like scrolling to trigger lazy loading if applicable
        for _ in range(3):
            page.mouse.wheel(0, random.randint(400, 900))
            time.sleep(random.uniform(0.6, 1.2))
        
        # Selectors for car detail links
        card_selector = "a.block.relative.h-60.w-full, a.px-3.pt-2.bg-white-900"
        links_locator = page.locator(card_selector)
        count_before = len(brand_links)
        
        elements = links_locator.all()
        for element in elements:
            try:
                href = element.get_attribute("href")
                if not href: continue

                # Filter logic
                if (
                    "/used-cars/" in href 
                    and "/city/" not in href 
                    and "/governorate/" not in href
                    and brand in href.lower()
                ):
                    full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                    brand_links.add(full_url)
            except:
                continue

        print(f"       Found {len(brand_links) - count_before} new links (Brand Total: {len(brand_links)})")

        # --- PAGINATION LOGIC ---
        # Look for 'Next' text or the specific pagination button
        next_button = page.locator('button:has-text("Next"), a:has-text("Next"), [aria-label="Next Page"]')
        
        clicked = False
        # Check if the button exists and is not disabled
        if next_button.count() > 0:
            for i in range(next_button.count()):
                btn = next_button.nth(i)
                if btn.is_visible() and btn.is_enabled():
                    try:
                        # Random delay before clicking to simulate human thought
                        time.sleep(random.uniform(1, 2))
                        btn.click()
                        clicked = True
                        print(f"       ➡️ Navigating to page {page_num + 1}...")
                        
                        # Wait for page to update (longer wait for content change)
                        time.sleep(random.uniform(4, 7)) 
                        page_num += 1
                        break
                    except:
                        continue
        
        if not clicked:
            print(f"       ⏹️ End of listings for {brand}.")
            break

    return brand_links

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Set to True if you don't want to see the browser
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768}
        )
        
        # Stealth: Remove webdriver flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        unique_brands = sorted(list(set(BRANDS)))
        total_extracted = 0

        # Clear file at the start
        open("contactcars_links_clean.txt", "w", encoding="utf-8").close()

        for brand in unique_brands:
            links = scrape_brand_stealth(page, brand)
            
            if links:
                # Append to file after every brand to prevent data loss
                with open("contactcars_links_clean.txt", "a", encoding="utf-8") as f:
                    for link in sorted(list(links)):
                        f.write(link + "\n")
                
                total_extracted += len(links)
                print(f"✅ Saved {len(links)} links for {brand}.")
            
            # Larger cooldown between different brands
            time.sleep(random.uniform(5, 10))

        browser.close()
        print(f"\n🚀 SCRAPING COMPLETE. Total links found: {total_extracted}")

if __name__ == "__main__":
    main()