import os
import csv
import re
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

SAVE_PATH = r"C:\Users\shams\fyp\datasets"
CSV_FILE = os.path.join(SAVE_PATH, "mg_cars.csv")

MODEL_URLS = [
    "https://www.mgmotor.com.eg/model/mg-one/",
    "https://www.mgmotor.com.eg/model/electric-model/",  # MG4
    "https://www.mgmotor.com.eg/model/mg5/",
    "https://www.mgmotor.com.eg/model/mg6/",
    "https://www.mgmotor.com.eg/model/mg7/",
    "https://www.mgmotor.com.eg/model/rx5-plus/",
    "https://www.mgmotor.com.eg/model/zs/",
    "https://www.mgmotor.com.eg/model/new-hs/",
    "https://www.mgmotor.com.eg/model/new-zs/",
]
PRICE_URL = "https://www.mgmotor.com.eg/buying-guide/#"

# ============================================================

def extract_specs_from_red_box(page):
    """Extract performance data from the red info box and spec table."""
    specs = {"Engine": None, "Max Power": None, "Max Torque": None, "Transmission": None}

    # --- Extract Engine / Power / Torque from the red box ---
    try:
        red_box_locator = page.locator("div.section_box_red").first
        red_box_locator.wait_for(timeout=10000)

        spec_items = red_box_locator.locator("div.single_info div.text")
        for item in spec_items.all():
            label_el = item.locator("h4")
            value_el = item.locator("p")
            if label_el.is_visible() and value_el.is_visible():
                label = label_el.inner_text().strip().lower()
                value = value_el.inner_text().strip()
                if "engine" in label:
                    specs["Engine"] = value
                elif "power" in label:
                    specs["Max Power"] = value
                elif "torque" in label:
                    specs["Max Torque"] = value
    except PlaywrightTimeoutError:
        print("     ⚠️ Red spec box not found or timed out.")
    except Exception as e:
        print(f"     ❌ Error extracting red box specs: {e}")

    # --- Extract Transmission from table rows ---
    try:
        # Find <tr> where first <td> contains "Transmission"
        rows = page.locator("table tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            # Ensure the row has at least one cell
            if row.locator("td").count() == 0:
                continue

            header_cell = row.locator("td").nth(0)
            if header_cell.is_visible():
                label = header_cell.inner_text().strip().lower()
                
                if "transmission" in label:
                    value_cells = row.locator("td")
                    clean_value = None

                    # Try to get value from the second column (nth(1))
                    if value_cells.count() > 1:
                        raw_value_1 = value_cells.nth(1).inner_text().strip()
                        clean_value = re.sub(r"\s+", " ", raw_value_1).strip()

                    # If value from col 1 was empty, try the third column (nth(2))
                    if (not clean_value) and (value_cells.count() > 2):
                        raw_value_2 = value_cells.nth(2).inner_text().strip()
                        clean_value = re.sub(r"\s+", " ", raw_value_2).strip()
                        if clean_value:
                             print(f"     ⚙️ Transmission found (from col 2): {clean_value}")

                    # If we found a non-empty value from either column
                    if clean_value:
                        if not specs["Transmission"]: # Only log the first one found
                             print(f"     ⚙️ Transmission found: {clean_value}")
                        specs["Transmission"] = clean_value
                        break # Stop searching rows once we find a valid transmission
                    
    except Exception as e:
        print(f"     ⚠️ Transmission table search failed: {e}")

    if not specs["Transmission"]:
        print("     ⚠️ Transmission not found on page.")
        # Uncomment below to save missing pages for inspection
        # with open(f"missing_transmission_{int(time.time())}.html", "w", encoding="utf-8") as f:
        #     f.write(page.content())

    return specs


# ============================================================

def scrape_prices(page):
    """Scrape car prices from buying guide page."""
    prices = {}
    try:
        print("⏳ Waiting for price boxes to load...")
        price_list_locator = page.locator("div.all_list")
        price_list_locator.locator("div.single p.price").first.wait_for(timeout=30000)
        print("✅ Price boxes loaded.")

        car_boxes = price_list_locator.locator("div.single")
        for box in car_boxes.all():
            name_el = box.locator("h3")
            price_el = box.locator("p.price")
            if name_el.is_visible() and price_el.is_visible():
                name = name_el.inner_text().strip()
                price_text = price_el.inner_text().strip()
                price = re.sub(r"[^0-9,]", "", price_text).replace(",", "")
                if price.isdigit():
                    prices[name.lower()] = price
                else:
                    print(f"     ⚠️ Could not parse price for '{name}': '{price_text}'")
    except PlaywrightTimeoutError:
        print("❌ Timed out waiting for price elements.")
    except Exception as e:
        print(f"❌ Failed to scrape prices: {e}")
    return prices


# ============================================================

def main():
    os.makedirs(SAVE_PATH, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ---------- Scrape Prices ----------
        print(f"💰 Scraping Prices from {PRICE_URL}")
        try:
            page.goto(PRICE_URL, wait_until="domcontentloaded", timeout=60000)
            page.locator("div.all_list").wait_for(timeout=60000)
            time.sleep(3)
        except PlaywrightTimeoutError:
            print("⚠️ Page load timeout or price list container not found. Check URL/selectors.")
            browser.close()
            return

        prices = scrape_prices(page)
        if not prices:
            print("❌ No prices found. Exiting.")
            browser.close()
            return
        print(f"✅ Found {len(prices)} prices.")

        # ---------- Scrape Models ----------
        all_data = []
        for url in MODEL_URLS:
            print("=" * 70)
            print(f"🚗 Scraping {url}")
            model_data = {
                "Model": "Unknown", "Engine": None, "Max Power": None,
                "Max Torque": None, "Transmission": None, "Price": None
            }
            try:
                url_model_name_part = url.strip("/").split("/")[-1]
                if url_model_name_part == "electric-model":
                    model_name = "MG4"
                elif url_model_name_part == "new-hs":
                    model_name = "HS"
                else:
                    model_name = url_model_name_part.replace("-", " ").upper()
                model_data["Model"] = model_name
                print(f"     Model name from URL: {model_name}")

                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("div.section_box_red, table", timeout=60000)
                print("     Page loaded, extracting specs...")

                specs = extract_specs_from_red_box(page)
                model_data.update(specs)

                # --- Price Matching ---
                matched_price = None
                simple_model_name = model_name.lower().replace(" ", "").replace("plus", "")
                for scraped_name_lower, price in prices.items():
                    simple_scraped_name = scraped_name_lower.replace(" ", "").replace("plus", "")
                    if simple_model_name in simple_scraped_name:
                        if simple_model_name == "zs" and "newzs" in simple_scraped_name and "NEW ZS" not in model_name:
                            continue
                        if simple_model_name == "newzs" and "newzs" not in simple_scraped_name and "NEW ZS" in model_name:
                            continue
                        matched_price = price
                        print(f"     ✅ Price matched: '{model_name}' matched with '{scraped_name_lower}' -> {price}")
                        break

                if not matched_price:
                    print(f"     ⚠️ No price found for model '{model_name}'")

                model_data["Price"] = matched_price
                all_data.append(model_data)
                print(f"     📊 Scraped Data: {model_data}")

            except PlaywrightTimeoutError:
                print(f"❌ Timeout error for {url}")
            except Exception as e:
                print(f"❌ Failed processing {url}: {e}")
                all_data.append(model_data)

        browser.close()

        # ---------- Save CSV ----------
        if not all_data:
            print("\n❌ No data collected, CSV not saved.")
            return

        fieldnames = ["Model", "Engine", "Max Power", "Max Torque", "Transmission", "Price"]
        try:
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
            print(f"\n💾 CSV saved successfully to: {CSV_FILE}")
        except IOError as e:
            print(f"\n❌ Error saving CSV file: {e}")
        except Exception as e:
            print(f"\n❌ Unexpected error during CSV writing: {e}")


# ============================================================

if __name__ == "__main__":
    main()