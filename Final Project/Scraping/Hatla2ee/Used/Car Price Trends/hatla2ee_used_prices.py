import asyncio
import csv
import random
import os
from playwright.async_api import async_playwright

# ==============================
# CONFIG
# ==============================
INPUT_FILE = "hatla2ee_used_prices_links.txt"
OUTPUT_FILE = "hatla2ee_price_history.csv"
CONCURRENCY_LIMIT = 4  # Equivalent to 4 workers

# ==============================
# HELPER FUNCTIONS
# ==============================
def clean_price(text):
    """Converts '70,000 EGP' to '70000'."""
    if not text:
        return ""
    return text.replace("EGP", "").replace(",", "").strip()

def get_car_name(url, page_title_element=None):
    """Attempts to find the car name from URL or passed element text."""
    if page_title_element:
        return page_title_element.strip()
    
    try:
        parts = url.strip().split('/')
        if len(parts) >= 3:
            return f"{parts[-3]} {parts[-2]} {parts[-1]}".replace("-", " ").title()
    except:
        return "Unknown Car"
    return "Unknown Car"

# ==============================
# ASYNC WORKER
# ==============================
async def scrape_single_car(semaphore, browser, url, csv_writer, file_lock):
    """
    Acquires a semaphore slot, opens a new page, scrapes data, and writes to CSV safely.
    """
    async with semaphore:
        # Create a new isolated page for this task
        # We inject the stealth script immediately upon creation
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        page = await context.new_page()
        
        print(f"   🚙 Processing: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Try to get H1 for car name
            try:
                h1_text = await page.inner_text("h1", timeout=1000)
                car_name = get_car_name(url, h1_text)
            except:
                car_name = get_car_name(url)

            page_num = 1
            
            while True:
                # Random scroll
                await page.mouse.wheel(0, 300)
                
                # Check for table rows
                rows_locator = page.locator('tbody[data-slot="table-body"] tr')
                
                try:
                    # Wait briefly for rows
                    await rows_locator.first.wait_for(timeout=3000)
                except:
                    # No table found on this page
                    break

                count = await rows_locator.count()

                # Extract data from all rows on current page
                for i in range(count):
                    try:
                        row = rows_locator.nth(i)
                        
                        # Get all text contents for the 4 cells we need
                        # We use JavaScript evaluation for speed instead of 4 separate Playwright calls per row
                        cells_data = await row.evaluate("""(row) => {
                            const cells = row.querySelectorAll('td');
                            return [
                                cells[0].innerText.trim(),
                                cells[1].innerText,
                                cells[2].innerText,
                                cells[3].innerText
                            ]
                        }""")

                        date_text = cells_data[0]
                        avg = clean_price(cells_data[1])
                        min_p = clean_price(cells_data[2])
                        max_p = clean_price(cells_data[3])

                        # Write to CSV safely using Lock
                        async with file_lock:
                            csv_writer.writerow([car_name, url, date_text, avg, min_p, max_p])

                    except Exception:
                        continue
                
                # ==============================
                # PAGINATION LOGIC
                # ==============================
                next_btn = page.locator('li[data-slot="pagination-item"] a:has(svg.lucide-chevron-right)').last
                
                if not await next_btn.is_visible():
                    break
                
                href = await next_btn.get_attribute("href")
                if not href or href == "#":
                    break

                try:
                    await next_btn.scroll_into_view_if_needed()
                    await next_btn.click()
                    # Wait for network or small timeout
                    await page.wait_for_timeout(random.randint(1500, 2500))
                    page_num += 1
                except:
                    break
        
        except Exception as e:
            print(f"   ❌ Error on {url}: {e}")
        
        finally:
            await context.close()


# ==============================
# MAIN ASYNC LOOP
# ==============================
async def main():
    # 1. Validation
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file '{INPUT_FILE}' not found.")
        return

    # 2. Read URLs
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"🚀 Found {len(urls)} cars. Starting {CONCURRENCY_LIMIT} async workers...")

    # 3. Setup Async Playwright
    async with async_playwright() as p:
        # Launch ONE browser instance
        browser = await p.chromium.launch(headless=False)
        
        # 4. Setup CSV and Locks
        # 'file_lock' ensures only one task writes to the file at a time
        file_lock = asyncio.Lock()
        
        # 'semaphore' ensures we only have CONCURRENCY_LIMIT active tabs at once
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Car Name", "URL", "Month/Year", "Average Price", "Min Price", "Max Price"])
            
            # 5. Create Tasks
            tasks = []
            for url in urls:
                task = asyncio.create_task(
                    scrape_single_car(semaphore, browser, url, writer, file_lock)
                )
                tasks.append(task)
            
            # 6. Run all tasks
            await asyncio.gather(*tasks)

        print(f"\n✅ Done! Data saved to {OUTPUT_FILE}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())