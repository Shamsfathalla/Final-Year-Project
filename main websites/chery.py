import asyncio
import csv
import os
import re # Import regex module for cleaning price
from playwright.async_api import async_playwright, Locator, Page

async def scrape_chery_specs(page: Page, category_button_text: str) -> dict:
    """
    Scrapes specifications for a given category from the Chery page's tabbed interface.
    """
    specs_data = {}
    
    # --- 1. Find the button for the category to get the target div ID ---
    # Use a case-insensitive text match, and allow partial match at start/end
    category_button = page.locator(f'#myTab button:text-matches("^{re.escape(category_button_text)}$", "i")')
                                    # Try exact match first
    
    if await category_button.count() == 0:
         # Try partial match if exact fails (e.g., "Powertrain" might be just "Power")
         category_button = page.locator(f'#myTab button:text-matches("{category_button_text}", "i")')
         
    if await category_button.count() == 0:
        print(f"Warning: Tab button for '{category_button_text}' not found.")
        return specs_data
        
    target_id = await category_button.get_attribute("data-tabs-target")
    if not target_id:
        print(f"Warning: Could not get target ID for '{category_button_text}'.")
        return specs_data
        
    # --- 2. Locate the corresponding content div ---
    if not target_id.startswith('#'):
        target_id = f"#{target_id}"
        
    category_div = page.locator(f'#myTabContent {target_id}')
    if await category_div.count() == 0:
        print(f"Warning: Content div '{target_id}' for '{category_button_text}' not found.")
        return specs_data
        
    # --- 3. Extract key-value pairs ---
    spec_rows = await category_div.locator("div.flex.justify-between").all()
    
    for row in spec_rows:
        spans = await row.locator("span").all()
        if len(spans) == 2:
            spec_name = (await spans[0].text_content()).strip()
            spec_value = (await spans[1].text_content()).strip()
            
            if spec_name.lower() == "option" and spec_value.lower() == "value":
                continue
                
            specs_data[spec_name] = spec_value
            
    return specs_data

async def get_price(page: Page) -> str:
    """Extracts the starting price from the page."""
    price = "N/A"
    price_locator_desktop = page.locator("#vehicleBanner .desktop-view div p.text-xl")
    price_locator_mobile = page.locator("#vehicleBanner .mobile-view p.text-xl")

    if await price_locator_desktop.count() > 0:
        price_text = await price_locator_desktop.first.text_content()
    elif await price_locator_mobile.count() > 0:
        all_mobile_p = await price_locator_mobile.all()
        price_text = "N/A"
        for p_element in all_mobile_p:
            text = await p_element.text_content()
            if text and "EGP" in text:
                price_text = text
                break
    else:
        price_text = "N/A"

    if price_text and price_text != "N/A":
        price = re.sub(r'[^\d]', '', price_text) 
        
    return price if price else "N/A"

async def main():
    urls = [
        "https://www.chery-eg.com/en/car/arrizo-8",
        "https://www.chery-eg.com/en/car/tiggo-9",
        "https://www.chery-eg.com/en/car/eq7", # This one is electric, should have 'Battery'
        "https://www.chery-eg.com/en/car/tiggo-4-pro",
        "https://www.chery-eg.com/en/car/arrizo-5",
        "https://www.chery-eg.com/en/car/tiggo-7-pro-max",
        "https://www.chery-eg.com/en/car/tiggo-8",
        "https://www.chery-eg.com/en/car/tiggo-8-pro-max",
    ]
    
    # --- CSV Setup ---
    output_dir = r"C:\Users\shams\fyp\datasets"
    # Updated file name
    csv_file = os.path.join(output_dir, "chery_specs_pow_batt_dims_wide.csv") 
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_cars_data = [] 
    all_column_headers = set(["Car", "Price"]) 
    # *** Updated categories to scrape ***
    categories_to_scrape = ["Dimensions", "Powertrain", "Battery"] 

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_navigation_timeout(90000) 
        
        unique_urls = list(dict.fromkeys(urls)) 

        for url in unique_urls:
            print(f"--- Scraping {url} ---")
            try:
                # Add retry logic for navigation
                retries = 3
                for i in range(retries):
                    try:
                        await page.goto(url, wait_until="domcontentloaded")
                        break # Success
                    except Exception as nav_error:
                        print(f"Navigation attempt {i+1}/{retries} failed: {nav_error}")
                        if i == retries - 1:
                            raise # Re-raise the exception if all retries fail
                        await asyncio.sleep(5) # Wait before retrying


                title = await page.title()
                car_name = title.split('|')[0].strip() if '|' in title else url.split('/')[-1]
                print(f"Found car: {car_name}")

                price = await get_price(page)
                print(f"Found price: {price}")
                
                car_dict = {
                    "Car": car_name,
                    "Price": price
                }

                # --- Scrape Specified Categories ---
                for category in categories_to_scrape:
                    print(f"Scraping {category} data...")
                    specs = await scrape_chery_specs(page, category)
                    
                    if specs:
                        for spec_name, spec_value in specs.items():
                            col_name = f"{category}_{spec_name}"
                            car_dict[col_name] = spec_value
                            all_column_headers.add(col_name)
                    else:
                        # Don't print warning if category is 'Battery' and car is not electric
                        # We can refine this check later if needed, for now just check category name
                        if category.lower() != 'battery':
                             print(f"No data found for {category}")
                        else:
                             print(f"No 'Battery' data found (expected for non-EVs).")


                all_cars_data.append(car_dict)

            except Exception as e:
                print(f"ERROR: Failed to scrape {url}. Reason: {type(e).__name__} - {e}")
                # Optional: Add specific error handling, e.g., for timeouts
                if "Timeout" in str(e):
                    print("Timeout occurred during scraping this URL.")
        
        await browser.close()
        
    # --- Write all data to CSV using DictWriter ---
    if not all_cars_data:
        print("\n\n--- No data was scraped. CSV file not written. ---")
        return

    ordered_headers = ["Car", "Price"]
    other_headers = sorted(list(all_column_headers - {"Car", "Price"}))
    ordered_headers.extend(other_headers)

    try:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=ordered_headers)
            writer.writeheader()
            writer.writerows(all_cars_data)
        print(f"\n\n--- Successfully saved Chery Price, Dimensions, Powertrain & Battery data to {csv_file} ---")
    except PermissionError:
        print(f"\n\n--- ERROR: Failed to write CSV file. Permission denied. ---")
        print(f"Please make sure the file '{csv_file}' is not open and you have write permissions.")
        print("Scraped data (JSON format):")
        print(json.dumps(all_cars_data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n\n--- ERROR: Failed to write CSV file ---")
        print(f"Reason: {e}")
        print("Scraped data (JSON format):")
        print(json.dumps(all_cars_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())