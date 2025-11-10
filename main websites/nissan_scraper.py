import re
import json
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError
import os
import pathlib
import numpy as np  # For handling N/A values in Pandas

# -------------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------------

# ✅ Force CSV save path to your desired folder
SAVE_FOLDER = r"C:\Users\shams\fyp\datasets"
os.makedirs(SAVE_FOLDER, exist_ok=True)
print(f"💾 CSV will be saved to: {SAVE_FOLDER}")

# --- List of all target cars ---
TARGET_CARS = [
    {"model": "Sunny", "url": "https://en.nissan.com.eg/vehicles/new/sunny/versions-and-specs.html"},
    {"model": "Patrol", "url": "https://en.nissan.com.eg/vehicles/new/allnewpatrol/specifications.html"},
    {"model": "Sentra", "url": "https://en.nissan.com.eg/vehicles/new/sentra/versions-and-specs.html"},
    {"model": "Juke", "url": "https://en.nissan.com.eg/vehicles/new/juke/specifications.html"},
    {"model": "Qashqai", "url": "https://en.nissan.com.eg/vehicles/new/qashqai/versions-and-specs.html"},
    {"model": "X-Trail", "url": "https://en.nissan.com.eg/vehicles/new/x-trail/specifications.html"}
]

# --- Comprehensive Spec Mapping ---
# Maps all possible HTML labels (keys) to a single standard CSV column name (value)
HTML_KEY_MAP = {
    # Engine & Power
    "Engine size / Displacement": "Engine Capacity (cc)",
    "Engine capacity, cc": "Engine Capacity (cc)",
    "Maximum Power (hp/rpm)": "Max Power",
    "Maximum Power (HP @ rpm)": "Max Power",  # Patrol variation
    "Max. engine power, PS (kW) @ rpm": "Max Power",
    "HP @ rpm": "Max Power",
    "hp/rpm": "Max Power",
    "No. of cylinders": "Cylinders",
    "No. of cylinders, configuration": "Cylinders",
    "Fuel Type": "Fuel Type",
    "Maximum Torque (Nm/rpm)": "Max Torque (Nm/rpm)",
    "Maximum Torque (Nm @ rpm)": "Max Torque (Nm/rpm)",  # Patrol variation
    "Max. torque, Nm @ rpm": "Max Torque (Nm/rpm)",
    "Torque (Nm/rpm)": "Max Torque (Nm/rpm)",
    "Engine type": "Engine Type",
    "Powertrain": "Powertrain",
    "Compression ratio": "Compression Ratio",
    "Emission Level": "Emission Level",

    # Drivetrain & Transmission
    "Wheels Driven": "Drivetrain",
    "Drivetrain": "Drivetrain",
    "Driven wheels": "Drivetrain",
    "Transmission type": "Transmission Type",
    "Transmission Type": "Transmission Type",
    "Gearbox Type": "Transmission Type",
    "Acceleration 0 - 100 kph, sec": "Acceleration 0-100 kph (sec)",
    "Max. speed, Kph": "Max Speed (Kph)",
    
    # Dimensions & Weight
    "Fuel Capacity (litres)": "Fuel Capacity (litres)",
    "Fuel tank capacity, litres": "Fuel Capacity (litres)",
    "Kerb Weight (kg)": "Kerb Weight (kg)",
    "Kerb Weight (min - max), kg": "Kerb Weight (kg)",
    "Gross Vehicle Weight, kg": "Gross Vehicle Weight (kg)",
    "Max. roof load, kg": "Max Roof Load (kg)",
    "Luggage volume (litres)": "Luggage Volume (litres)",
    "Luggage capacity 5 seats version (Seats Up), litres": "Luggage Volume (litres)",
    "Luggage capacity 5 seats version (Seats Down), litres": "Luggage Volume Seats Down (litres)",
    
    "Overall length (mm)": "Overall length (mm)",
    "Overall length, mm": "Overall length (mm)",
    "Overall Length with Pintle Hook, mm": "Overall length (mm)",  # Patrol variation
    
    "Overall width (mm)": "Overall width (mm)",
    "Overall width, mm": "Overall width (mm)",
    "Overall Width with mirrors, mm": "Overall width (mm)",  # Patrol variation
    "Overall width with mirrors, mm": "Overall width (mm)",  # X-Trail variation
    
    "Overall height (mm)": "Overall height (mm)",
    "Overall height, mm": "Overall height (mm)",
    "Overall Height (unladen), mm": "Overall height (mm)",  # Patrol variation
    
    "Wheelbase (mm)": "Wheelbase (mm)",
    "Wheelbase, mm": "Wheelbase (mm)"
}

# Create a unique, sorted list of all desired final CSV columns
DESIRED_SPEC_KEYS = sorted(list(set(HTML_KEY_MAP.values())))

# This list will hold all data from all cars
ALL_CARS_DATA = []

# -------------------------------------------------------------------------
# MAIN SCRAPER
# -------------------------------------------------------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    print("🚀 Browser launched.")

    for car in TARGET_CARS:
        model_name = car['model']
        url = car['url']
        page = None
        
        print("\n" + "="*50)
        print(f"🚘 Now scraping: {model_name}")
        print(f"🌐 Navigating to {url} ...")

        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            print("✅ Page loaded.")
            
            page.wait_for_selector("div.c_099-1", timeout=30000)
            print("✅ Trim containers detected.")

            generation = "N/A"
            try:
                gen_element = page.locator("div[data-vehicle-id]").first
                generation = gen_element.get_attribute("data-vehicle-id")
                print(f"ℹ️ Found generation/model ID: {generation}")
            except Exception as e:
                print(f"⚠️ Could not extract generation for {model_name}: {e}")

            trim_containers = page.locator("div.c_099-1").all()
            print(f"🔍 Found {len(trim_containers)} trim containers for {model_name}.")

            if not trim_containers:
                html = page.content()
                debug_path = os.path.join(SAVE_FOLDER, f"nissan_debug_no_trims_{model_name}.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"⚠️ No trims found for {model_name} — saved debug HTML.")
                continue

            for container in trim_containers:
                try:
                    trim_name = container.locator("h2").text_content().strip()
                    price_text = "N/A"
                    try:
                        price_element = container.locator("span.full-price span").first
                        price_text = price_element.text_content().strip().replace("EGP", "").replace(",", "").strip()
                    except Exception:
                        price_text = "N/A"

                    print(f"  -> Scraping trim: {trim_name}, Price: {price_text}")

                    specs_data = {key: "N/A" for key in DESIRED_SPEC_KEYS}
                    found_specs = False

                    # --- Method 1 (Sunny/Sentra/Qashqai layout) ---
                    spec_items_m1 = container.locator("li.technical-detail-item").all()
                    if spec_items_m1:
                        found_specs = True
                        print(f"    -> Using Method 1 (p.detail-title) found {len(spec_items_m1)} specs.")
                        for item in spec_items_m1:
                            try:
                                key_text = item.locator("p.detail-title").text_content().strip()
                                value_text = item.locator("p.detail-description").text_content().strip()
                                
                                if key_text in HTML_KEY_MAP:
                                    standard_key = HTML_KEY_MAP[key_text]
                                    if value_text and value_text.strip():
                                        specs_data[standard_key] = value_text.strip()
                            except Exception:
                                pass

                    # --- Method 2 (Patrol/Juke/X-Trail layout) ---
                    if not found_specs:
                        dts = container.locator("dt").all()
                        dds = container.locator("dd").all()
                        if dts and len(dts) == len(dds):
                            found_specs = True
                            print(f"    -> Using Method 2 (dt/dd) found {len(dts)} specs.")
                            
                            keys = [dt.text_content().strip() for dt in dts]
                            values = [dd.text_content().strip() for dd in dds]

                            for key_text, value_text in zip(keys, values):
                                if key_text in HTML_KEY_MAP:
                                    standard_key = HTML_KEY_MAP[key_text]
                                    if value_text and value_text.strip():
                                        specs_data[standard_key] = value_text.strip()
                    
                    if not found_specs:
                        print("    -> ⚠️ No spec structure (Method 1 or 2) found.")

                    car_info = {
                        "Brand": "Nissan",
                        "Model": model_name,
                        "Trim": trim_name,
                        "Generation": generation,
                        "Price": price_text
                    }
                    car_info.update(specs_data)
                    ALL_CARS_DATA.append(car_info)

                except Exception as e:
                    print(f"⚠️ Error processing a trim container for {model_name}: {e}")

        except TimeoutError as e:
            print(f"⏰ Timeout Error for {model_name}: {e}")
            if page:
                html = page.content()
                debug_path = os.path.join(SAVE_FOLDER, f"nissan_debug_timeout_{model_name}.html")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"⚠️ Saved debug HTML to: {debug_path}")
        
        except Exception as e:
            print(f"❌ Unexpected error for {model_name}: {e}")
        
        finally:
            if page:
                page.close()
                print(f"✅ Page closed for {model_name}.")

    browser.close()
    print("\n" + "="*50)
    print("🏁 Browser closed. All scraping finished.")

# -------------------------------------------------------------------------
# DATA PROCESSING & SAVE TO CSV
# -------------------------------------------------------------------------
if ALL_CARS_DATA:
    df = pd.DataFrame(ALL_CARS_DATA)
    print("\n🔄 Processing data: Filling in missing common specs...")
    
    base_cols = ["Brand", "Model", "Trim", "Generation", "Price"]
    # Get all spec columns that were actually created
    spec_cols = [col for col in df.columns if col not in base_cols]
    
    # Replace any "N/A" strings with actual np.nan for pandas processing
    df.replace("N/A", np.nan, inplace=True)
    filled_cols = []

    # Define the fill function to be used with transform
    def fill_common_spec(group_series):
        # Find all unique, non-null values
        unique_vals = group_series.dropna().unique()
        
        # If there is exactly ONE unique value, fill NAs with it
        if len(unique_vals) == 1:
            return group_series.fillna(unique_vals[0])
        # Otherwise (0 or >1 unique values), return the series as-is
        else:
            return group_series

    # Group by 'Model' and apply the fill logic to each spec column
    for col in spec_cols:
        before = df[col].isna().sum()
        df[col] = df.groupby("Model")[col].transform(fill_common_spec)
        after = df[col].isna().sum()
        if before > after:
            filled_cols.append(col)

    if filled_cols:
        print(f"✅ Filled in missing data for: {', '.join(filled_cols)}")
    else:
        print("ℹ️ No missing data filled.")

    # Replace np.nan back with "N/A" for a clean CSV
    df.fillna("N/A", inplace=True)
    
    # Re-order columns: base_cols first, then all desired spec_cols sorted
    # This ensures all columns from DESIRED_SPEC_KEYS are present, even if all N/A
    final_cols = base_cols.copy()
    for spec_key in DESIRED_SPEC_KEYS:
        if spec_key in df.columns:
            final_cols.append(spec_key)
        else:
            # Add column as "N/A" if it was never found during scrape
            df[spec_key] = "N/A"
            final_cols.append(spec_key)

    df = df[final_cols] # Apply final column order

    csv_path = os.path.join(SAVE_FOLDER, "nissan_egypt_models.csv")
    try:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\n✅ Success! All data saved to:\n{csv_path}")
        print("\n--- DataFrame Info ---")
        df.info()
    except Exception as e:
        print(f"\n❌ Could not save CSV: {e}")
else:
    print("\n⚠️ No data was scraped from any URL.")