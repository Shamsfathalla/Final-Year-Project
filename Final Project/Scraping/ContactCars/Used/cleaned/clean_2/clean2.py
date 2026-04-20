import pandas as pd
import numpy as np

# Load Data
df = pd.read_csv("used_cars_data_clean.csv")

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Brands that almost NEVER have > 4 cylinders in the Egyptian market 
# (unless it's a specific massive SUV like a Toyota Land Cruiser)
economy_brands = [
    'Fiat', 'Peugeot', 'Citroen', 'Renault', 'Suzuki', 'Chevrolet', 
    'Opel', 'Skoda', 'Seat', 'Volkswagen', 'BYD', 'Chery', 'Lada', 
    'Proton', 'Geely', 'MG', 'Daihatsu'
]

# High-Performance brands that are allowed to have big engines
performance_brands = [
    'Rolls', 'Rolls-Royce', 'Bentley', 'Ferrari', 'Lamborghini', 
    'Aston Martin', 'McLaren', 'Maserati', 'Porsche', 'Jaguar'
]

def is_plausible(row):
    """
    Returns True if the cylinder count makes sense for the engine size/brand.
    Returns False if it looks like a lie/typo.
    """
    cyl = row['Cylinder Count']
    cc = row['Engine Capacity']
    brand = str(row['Brand'])
    
    # CASE 1: 12 Cylinders
    if cyl == 12:
        # Must be huge engine OR Super Luxury brand
        if cc >= 4500 or brand in performance_brands: return True
        return False

    # CASE 2: 8 Cylinders
    if cyl == 8:
        # V8s are rarely under 3.5L (3500cc)
        if cc >= 3500: return True
        # Exception for smaller V8s (very rare modern, but some old Ferraris/BMWs exist)
        if brand in performance_brands and cc >= 3000: return True
        # American Muscle (Mustang/Charger) or German V8s
        if brand in ['Ford', 'Dodge', 'Jeep', 'BMW', 'Mercedes', 'Audi'] and cc >= 3900: return True
        return False

    # CASE 3: 6 Cylinders
    if cyl == 6:
        # V6s are usually 2.5L (2500cc) and up. 
        # Some rare 2.0L V6 exist, but extremely unlikely for brands like Kia/Hyundai in Egypt.
        if cc >= 2400: return True
        # Exception for BMW/Mercedes 6-cylinders which can be 2.0L-3.0L in older models
        if brand in ['BMW', 'Mercedes'] and cc >= 2000: return True
        return False

    # 4 Cylinder and below are usually always plausible for any car
    return True

def fix_cylinders(row, all_data):
    """
    If plausible, keep it. 
    If not, find the 'Twin' car to copy correct data from.
    """
    current_cyl = row['Cylinder Count']
    
    # 1. If it passes the "Lie Detector", keep it.
    if is_plausible(row):
        return current_cyl
    
    # ---------------------------------------------------------
    # SMART LOOKUP (The Fixer)
    # ---------------------------------------------------------
    brand = str(row['Brand'])
    model = str(row['Model'])
    cc = row['Engine Capacity']

    # Strategy A: Find "Twin" (Same Brand, Model, CC) with a "Normal" cylinder count (<= 4)
    # We look for <=4 because that is the most likely truth for these fake V6/V8/V12s
    twin_matches = all_data[
        (all_data['Brand'] == brand) & 
        (all_data['Model'] == model) & 
        (all_data['Engine Capacity'] == cc) &
        (all_data['Cylinder Count'] <= 4) &  # Look for the sanity check
        (all_data['Cylinder Count'] > 0)
    ]
    
    if not twin_matches.empty:
        return int(twin_matches['Cylinder Count'].mode().iloc[0])

    # Strategy B: Fallback Logic if no twins found
    # If it failed the 'is_plausible' check, it implies the engine is too small for the cylinder count.
    # Therefore, we downgrade it.
    
    if brand in economy_brands:
        return 4 # Almost certainly 4 cylinders
    
    if cc < 1200: return 3
    if cc < 2000: return 4
    if cc < 3000: return 4 # 2.4L or 2.5L usually 4 cyl these days
    
    return 6 # Fallback for weird mid-range engines

# Apply Logic
print("⏳ Verifying 6, 8, and 12 Cylinder claims...")
df['Cylinder Count'] = df.apply(lambda row: fix_cylinders(row, df), axis=1)

# Verification Prints
print("\n--- Sanity Check Results ---")
suspicious_cars = ['Tipo', 'Logan', 'Corolla', 'Cerato', 'Lancer', 'Sunny']
for model in suspicious_cars:
    subset = df[df['Model'].str.contains(model, case=False, na=False)]
    if not subset.empty:
        print(f"Model: {model} | Cylinders found: {subset['Cylinder Count'].unique()} (Should be [3] or [4])")

df.to_csv("used_cars_data_smart_fixed.csv", index=False)
print("\n✅ All cylinders validated. Saved to 'used_cars_data_smart_fixed.csv'")