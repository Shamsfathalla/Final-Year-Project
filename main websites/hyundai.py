import json
import os
import re
import pandas as pd
from playwright.sync_api import sync_playwright, Page, Playwright
from typing import Dict, Any, Optional

# --- Configuration ---

PRICES_URL = "https://hyundai-egypt.net/hyundai-models/"

MODEL_URLS = [
    "https://hyundai-egypt.net/models/i30-fb-2/",
    "https://hyundai-egypt.net/models/elantra-ad/",
    "https://hyundai-egypt.net/models/i30-hb/",
    "https://hyundai-egypt.net/models/ioniq-5-n/",
    "https://hyundai-egypt.net/models/staria/",
    "https://hyundai-egypt.net/models/ioniq-6/",
    "https://hyundai-egypt.net/models/santa-fe/",
    "https://hyundai-egypt.net/models/ioniq5/",
    "https://hyundai-egypt.net/models/elantra-cn7/",
    "https://hyundai-egypt.net/models/tucson/",
    "https://hyundai-egypt.net/models/accent-rb/"
]

OUTPUT_DIRECTORY = r"C:\Users\shams\fyp\datasets"
OUTPUT_FILENAME = "hyundai_egypt_models.csv"
OUTPUT_PATH = os.path.join(OUTPUT_DIRECTORY, OUTPUT_FILENAME)

# --- Helper Functions ---

def scrape_prices(page: Page) -> Dict[str, Dict[str, str]]:
    print(f"Navigating to prices page: {PRICES_URL}")
    page.goto(PRICES_URL, wait_until="domcontentloaded")

    price_data = {}
    page.wait_for_selector("div.car-model-container")
    containers = page.locator("div.car-model-container").all()
    print(f"Found {len(containers)} car models on the prices page.")

    for container in containers:
        try:
            link_element = container.locator("a").first
            url = link_element.get_attribute("href")
            name = link_element.locator("h2").inner_text()
            price = link_element.locator("p").inner_text()

            if url:
                price_data[url] = {
                    "name": name.strip(),
                    "price": price.strip()
                }
        except Exception as e:
            print(f"Could not parse a price container: {e}")

    return price_data


def get_tab_container_id_by_text(page: Page, tab_text: str) -> Optional[str]:
    tab_selector = 'ul#specs-tabs a'
    try:
        page.wait_for_selector(tab_selector, timeout=10000)
        all_tabs = page.locator(tab_selector).all()
        for tab in all_tabs:
            if tab.inner_text().strip().lower() == tab_text.lower():
                tab_id = tab.get_attribute('id')  # e.g., "tab1"
                if tab_id:
                    return f"{tab_id}C"
    except Exception as e:
        print(f"Error finding tabs: {e}")

    print(f"Warning: Could not find a tab with text '{tab_text}'")
    return None


def click_spec_tab_by_id(page: Page, tab_id_str: str):
    tab_selector = f'ul#specs-tabs a#{tab_id_str}'
    try:
        page.wait_for_selector(tab_selector, timeout=10000)
        page.locator(tab_selector).click()
        page.wait_for_selector(f"div#{tab_id_str}C", state="visible", timeout=5000)
    except Exception as e:
        print(f"Could not click tab with ID {tab_id_str}: {e}")


def scrape_specs_table(page: Page, tab_container_id: str, model_name: str = "") -> Dict[str, str]:
    """
    Scrapes a specifications table given its tab container ID.
    For Tucson: if 'Width' has multiple concatenated values, only take the first one.
    Prefers a 'common' colspan value when available.
    """
    specs = {}
    table_selector = f"div#{tab_container_id} table.styled-table tbody tr"

    try:
        page.locator(table_selector).first.wait_for(timeout=10000)
        rows = page.locator(table_selector).all()

        for row in rows:
            key_loc = row.locator("th")
            if key_loc.count() == 0:
                continue

            key = key_loc.first.inner_text().strip()
            value = "N/A"

            # Prefer 'common' colspan first
            common_value_loc = row.locator("td[colspan]")
            if common_value_loc.count() > 0:
                value = common_value_loc.first.inner_text().strip()
            else:
                first_td = row.locator("td").first
                if first_td.count() > 0:
                    value = first_td.inner_text().strip()

            # --- Tucson-specific width fix ---
            if "tucson" in model_name.lower() and "width" in key.lower():
                # If multiple numbers are squished together, grab only the first
                nums = re.findall(r"\d[\d,]*", value)
                if len(nums) > 1:
                    value = nums[0]

            specs[key] = value.strip()

    except Exception as e:
        print(f"Error scraping spec table '{tab_container_id}': {e}")

    return specs


def scrape_model_page(page: Page, url: str, name: str) -> Dict[str, Any]:
    print(f"Scraping model page: {url}")
    page.goto(url, wait_until="domcontentloaded")

    car_details = {}

    # --- Dimensions ---
    print("...finding 'Dimensions' tab...")
    dim_tab_id = get_tab_container_id_by_text(page, "Dimensions")

    if dim_tab_id:
        print(f"...scraping dimensions from '{dim_tab_id}'...")
        car_details["dimensions"] = scrape_specs_table(page, dim_tab_id, name)
    else:
        print(f"Failed to find 'Dimensions' tab for {url}")
        car_details["dimensions"] = {}

    # --- EV or Fuel Specs ---
    if "ioniq" in name.lower():
        print(f"...scraping EV specs for {name}...")
        ev_specs = {}

        perf_tab_id = get_tab_container_id_by_text(page, "Performance")
        if perf_tab_id:
            click_spec_tab_by_id(page, perf_tab_id.replace('C', ''))
            ev_specs["performance"] = scrape_specs_table(page, perf_tab_id, name)

        eng_tab_id = get_tab_container_id_by_text(page, "Engine")
        if eng_tab_id:
            click_spec_tab_by_id(page, eng_tab_id.replace('C', ''))
            ev_specs["engine"] = scrape_specs_table(page, eng_tab_id, name)

        bat_tab_id = get_tab_container_id_by_text(page, "Battery")
        if bat_tab_id:
            click_spec_tab_by_id(page, bat_tab_id.replace('C', ''))
            ev_specs["battery"] = scrape_specs_table(page, bat_tab_id, name)

        car_details.update(ev_specs)

    else:
        print(f"...scraping Fuel specs for {name}...")
        eng_perf_tab_id = get_tab_container_id_by_text(page, "Engine Performance")
        if eng_perf_tab_id:
            click_spec_tab_by_id(page, eng_perf_tab_id.replace('C', ''))
            car_details["engine_performance"] = scrape_specs_table(page, eng_perf_tab_id, name)
        else:
            print(f"Failed to find 'Engine Performance' tab for {name}")
            car_details["engine_performance"] = {}

    return car_details


# --- Main Execution ---

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        all_car_data = []

        try:
            prices = scrape_prices(page)
            print(f"\nSuccessfully scraped {len(prices)} prices/names.")
            print("-" * 30)

            for url in MODEL_URLS:
                car_name = prices.get(url, {}).get("name", "")
                if not car_name:
                    print(f"Warning: No name found for {url}, skipping scrape logic.")
                    continue

                model_specs = scrape_model_page(page, url, car_name)
                model_specs.update(prices[url])
                all_car_data.append(model_specs)
                print(f"Finished scraping {model_specs.get('name')}\n")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            page.close()
            context.close()
            browser.close()

    if all_car_data:
        print("\n" + "=" * 50)
        print("SCRAPING COMPLETE. Processing data for CSV...")

        flattened_data = []
        for row in all_car_data:
            flat_row = {
                "name": row.get("name"),
                "price": row.get("price"),
            }

            if "dimensions" in row and row["dimensions"]:
                for key, value in row["dimensions"].items():
                    flat_row[f"dim_{key}"] = value

            if "engine_performance" in row and row["engine_performance"]:
                for key, value in row["engine_performance"].items():
                    flat_row[f"fuel_eng_{key}"] = value

            if "performance" in row and row["performance"]:
                for key, value in row["performance"].items():
                    flat_row[f"ev_perf_{key}"] = value
            if "engine" in row and row["engine"]:
                for key, value in row["engine"].items():
                    flat_row[f"ev_eng_{key}"] = value
            if "battery" in row and row["battery"]:
                for key, value in row["battery"].items():
                    flat_row[f"ev_bat_{key}"] = value

            flattened_data.append(flat_row)

        try:
            df = pd.DataFrame(flattened_data)
            os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
            df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

            print(f"\n✅ Successfully saved data to:")
            print(f"{OUTPUT_PATH}")

        except Exception as e:
            print(f"\nError saving file to {OUTPUT_PATH}: {e}")
            print("Dumping data as JSON instead:")
            print(json.dumps(all_car_data, indent=2))
    else:
        print("No data was scraped.")


if __name__ == "__main__":
    main()
