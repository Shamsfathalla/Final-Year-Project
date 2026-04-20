import asyncio
import json
import csv
import os
from playwright.async_api import async_playwright, Locator

async def scrape_spec_table(table_locator: Locator):
    """
    Helper function to scrape a specifications table (Performance/Dimensions)
    which has trims as columns.
    """
    trims_data = []
    
    # --- 1. Get trim names from the table header ---
    header_cells = await table_locator.locator("thead th").all()
    trim_names = []
    for i, cell in enumerate(header_cells):
        if i == 0:  # Skip the first header (e.g., "Performance")
            continue
        trim_name = (await cell.text_content()).strip()
        trim_names.append(trim_name)
        trims_data.append({"trim_name": trim_name, "specs": {}})

    # --- 2. Get data from the table body ---
    rows = await table_locator.locator("tbody tr").all()
    for row in rows:
        cells = await row.locator("td").all()
        if not cells:
            continue
        
        spec_name = (await cells[0].text_content()).strip()
        
        for i, value_cell in enumerate(cells[1:]):
            if i < len(trims_data):
                value = (await value_cell.text_content()).strip()
                trims_data[i]["specs"][spec_name] = value
                
    return trims_data

async def main():
    urls = [
        "https://www.kia.com.eg/models/specifications/The_K4",
        "https://www.kia.com.eg/models/specifications/The_Carnival",
        "https://www.kia.com.eg/models/specifications/The_Sorento",
        "https://www.kia.com.eg/models/specifications/The_Sportage",
        "https://www.kia.com.eg/models/specifications/The_Seltos"
    ]
    
    # --- CSV Setup ---
    output_dir = r"C:\Users\shams\fyp\datasets"
    # New file name for this specific data
    csv_file = os.path.join(output_dir, "kia_specs_perf_dims_wide.csv") 
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_trims_data = [] 
    all_column_headers = set(["Car", "Trim"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for url in urls:
            print(f"--- Scraping {url} ---")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                car_name_element = await page.query_selector("h1.bottom_nav_title")
                car_name = (await car_name_element.text_content()).strip() if car_name_element else url.split('/')[-1]
                
                print(f"Found car: {car_name}")
                scraped_car_data = {}

                # Find all specification blocks
                spec_blocks = await page.locator("section.specifications .container > div[class*='mb-4']").all()
                
                if not spec_blocks:
                    print("No specification blocks found. Skipping.")
                    continue
                
                # --- Define the categories you want ---
                desired_categories = ["Performance", "Dimensions"]

                for block in spec_blocks:
                    class_attr = await block.get_attribute("class")
                    if not class_attr:
                        continue
                    
                    category_name = class_attr.split(' ')[0]
                    
                    # --- Filter for desired categories ---
                    if category_name not in desired_categories:
                        print(f"Skipping non-desired category: {category_name}")
                        continue
                    
                    # This code will only run if category_name is "Performance" or "Dimensions"
                    table_locator = block.locator(".table")
                    
                    if await table_locator.count() > 0:
                        print(f"Scraping {category_name} data...")
                        scraped_car_data[category_name] = await scrape_spec_table(table_locator)
                    else:
                        print(f"{category_name} block found, but no table inside.")
                        
                # --- Transform data from category-first to trim-first ---
                trims_for_this_car = {}

                for category_name, trims_list in scraped_car_data.items():
                    for trim_info in trims_list:
                        trim_name = trim_info["trim_name"]
                        
                        if trim_name not in trims_for_this_car:
                            trims_for_this_car[trim_name] = {
                                "Car": car_name,
                                "Trim": trim_name
                            }
                        
                        for spec_name, spec_value in trim_info["specs"].items():
                            flat_col_name = f"{category_name}_{spec_name}"
                            trims_for_this_car[trim_name][flat_col_name] = spec_value
                            all_column_headers.add(flat_col_name) 

                all_trims_data.extend(trims_for_this_car.values())

            except Exception as e:
                print(f"ERROR: Failed to scrape {url}. Reason: {e}")
        
        await browser.close()
        
    if not all_trims_data:
        print("\n\n--- No data was scraped. CSV file not written. ---")
        return

    # Create a sorted list of headers for consistent column order
    ordered_headers = ["Car", "Trim"]
    other_headers = sorted(list(all_column_headers - {"Car", "Trim"}))
    ordered_headers.extend(other_headers)

    try:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=ordered_headers)
            writer.writeheader()
            writer.writerows(all_trims_data)
        print(f"\n\n--- Successfully saved Performance & Dimensions data to {csv_file} ---")
    except PermissionError:
        print(f"\n\n--- ERROR: Failed to write CSV file. Permission denied. ---")
        print(f"Please make sure the file '{csv_file}' is not open and you have write permissions.")
        print("Scraped data (JSON format):")
        print(json.dumps(all_trims_data, indent=2))
    except Exception as e:
        print(f"\n\n--- ERROR: Failed to write CSV file ---")
        print(f"Reason: {e}")
        print("Scraped data (JSON format):")
        print(json.dumps(all_trims_data, indent=2))

if __name__ == "__main__":
    asyncio.run(main())