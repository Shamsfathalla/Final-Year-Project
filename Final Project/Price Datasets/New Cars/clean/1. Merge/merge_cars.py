"""
Merge two car CSV files:
- Combine cars only if Brand, Model, Year, Trim AND Price match
- Standardize brand/model/trim names
- Fill missing body types from same brand/model
- Keep entry with most data if duplicates exist
- Merge image paths for matching cars
"""

import pandas as pd
import numpy as np
import os
import re

# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Load both CSV files
print("Loading CSV files...")
contact_df = pd.read_csv('contact_new_clean.csv')
hatla2ee_df = pd.read_csv('hatla2ee_new_clean.csv')

print(f"Contact cars: {len(contact_df)} rows")
print(f"Hatla2ee cars: {len(hatla2ee_df)} rows")

# =============================================
# BRAND NORMALIZATION
# =============================================
BRAND_MAPPING = {
    'alfa': 'Alfa Romeo', 'alfa romeo': 'Alfa Romeo', 
    'alpha': 'Alfa Romeo', 'alpha romeo': 'Alfa Romeo',
    'bmw': 'BMW', 'byd': 'BYD', 'gac': 'GAC', 'jac': 'JAC',
    'dfm': 'Dongfeng', 'dfsk': 'DFSK', 'dongfeng': 'Dongfeng',
    'baic': 'BAIC', 'im': 'IM Motors', 'im motors': 'IM Motors',
    'exeed': 'EXEED', 'ds': 'DS', 'arcfox': 'Arcfox',
    'mercedes': 'Mercedes', 'mercedes-benz': 'Mercedes', 'mercedes benz': 'Mercedes',
}

def standardize_brand(brand):
    if pd.isna(brand):
        return brand
    brand_clean = str(brand).strip().lower()
    if brand_clean in BRAND_MAPPING:
        return BRAND_MAPPING[brand_clean]
    for key, value in BRAND_MAPPING.items():
        if key in brand_clean:
            return value
    return str(brand).strip().title()

# =============================================
# MODEL NORMALIZATION
# =============================================
def standardize_model(model, brand=None, trim=None):
    if pd.isna(model):
        return model
    
    model = str(model).strip()
    brand_str = str(brand).strip() if pd.notna(brand) else ''
    
    # Remove brand name from model
    if brand_str:
        pattern = r'^' + re.escape(brand_str) + r'\s+'
        model = re.sub(pattern, '', model, flags=re.IGNORECASE)
        brand_lower = brand_str.lower()
        model_lower = model.lower()
        if model_lower.startswith(brand_lower + ' '):
            model = model[len(brand_str)+1:]
        elif model_lower.startswith(brand_lower):
            model = model[len(brand_str):]
    
    model = ' '.join(model.split())
    model = re.sub(r'([A-Za-z])\s+(\d)', r'\1\2', model)
    
    # BMW specific
    if brand_str.upper() == 'BMW':
        xdrive_match = re.match(r'^([A-Za-z]+\d*)(?:xdrive|Xdrive|XDRIVE)?\d*$', model, re.IGNORECASE)
        if xdrive_match:
            base = xdrive_match.group(1)
            base = re.sub(r'^I([0-9])', r'i\1', base)
            base = re.sub(r'^I([Xx])', r'i\1', base)
            base = re.sub(r'^Ix', 'iX', base)
            model = base
        
        if re.match(r'^\d\s*series$', model.lower()):
            trim_str = str(trim).strip() if pd.notna(trim) else ''
            trim_match = re.search(r'(\d{3}[a-z]?i?|[Mm]\d{3}[a-z]?i?)', trim_str)
            if trim_match:
                model = trim_match.group(1)
        
        model = model.replace(' I', 'i').replace(' i', 'i')
        if re.match(r'^\d{3}$', model):
            model = model + 'i'
        model = re.sub(r'^(\d{3})I$', r'\1i', model)
        
    model = re.sub(r'(xdrive|sdrive|edrive)\d*$', '', model, flags=re.IGNORECASE)
    model = model.strip()
    
    if brand_str.lower() == 'arcfox':
        model = model.title()
        if 'kaola' in model.lower():
            model = model.replace('Kaola', 'Koala').replace('kaola', 'Koala')
    
    if 'im' in brand_str.lower():
        model = model.upper().replace('MOTORS ', '').replace('IM ', '')
    
    if brand_str.lower() == 'genesis':
        model = model.upper().replace(' ', '')
    
    if brand_str.lower() == 'audi':
        model = model.replace('E Tron', 'e-tron').replace('E-Tron', 'e-tron').replace('Etron', 'e-tron')
    
    if brand_str.lower() == 'hyundai':
        model = re.sub(r'i\s+(\d+)', r'i\1', model)
        if 'ioniq' in model.lower():
            model = model.upper()
    
    if not any(x in brand_str.lower() for x in ['bmw', 'im', 'genesis']):
        model = model.title()
    
    model = re.sub(r'\b(Suv|Ev|Bev|Hev|Phev|Reev|Gt)\b', 
                   lambda m: m.group(1).upper(), model, flags=re.IGNORECASE)
    
    return model

# =============================================
# TRIM NORMALIZATION
# =============================================
TRIM_MAPPING = {
    's line': 'S-Line', 's-line': 'S-Line', 'sline': 'S-Line',
    'm sport': 'M Sport', 'm-sport': 'M Sport', 'msport': 'M Sport',
    'amg line': 'AMG Line', 'amg-line': 'AMG Line',
    'r line': 'R-Line', 'r-line': 'R-Line', 'rline': 'R-Line',
    'gt line': 'GT-Line', 'gt-line': 'GT-Line', 'gtline': 'GT-Line',
    'n line': 'N-Line', 'n-line': 'N-Line', 'nline': 'N-Line',
    'f sport': 'F Sport', 'f-sport': 'F Sport', 'fsport': 'F Sport',
}

def standardize_trim(trim):
    if pd.isna(trim):
        return 'Base'
    trim = str(trim).strip()
    trim = ' '.join(trim.split())
    
    trim_lower = trim.lower()
    for pattern, replacement in TRIM_MAPPING.items():
        if pattern in trim_lower:
            trim = re.sub(pattern, replacement, trim, flags=re.IGNORECASE)
    
    return trim.title()

# =============================================
# FIX ALFA ROMEO
# =============================================
def fix_alfa_romeo(row):
    brand = str(row['Brand']).strip().lower() if pd.notna(row['Brand']) else ''
    model = str(row['Model']).strip() if pd.notna(row['Model']) else ''
    
    if brand == 'alfa' and model.lower().startswith('romeo'):
        model = model.lower().replace('romeo ', '').replace('romeo', '').strip().title()
        return 'Alfa Romeo', model
    return row['Brand'], row['Model']

# Apply fixes
fixed_data = contact_df.apply(fix_alfa_romeo, axis=1, result_type='expand')
contact_df['Brand'] = fixed_data[0]
contact_df['Model'] = fixed_data[1]

contact_df['Brand'] = contact_df['Brand'].apply(standardize_brand)
hatla2ee_df['Brand'] = hatla2ee_df['Brand'].apply(standardize_brand)

contact_df['Model'] = contact_df.apply(
    lambda row: standardize_model(row['Model'], row['Brand'], row['Trim']), axis=1)
hatla2ee_df['Model'] = hatla2ee_df.apply(
    lambda row: standardize_model(row['Model'], row['Brand'], row['Trim']), axis=1)

contact_df['Year'] = pd.to_numeric(contact_df['Year'], errors='coerce').astype('Int64')
hatla2ee_df['Year'] = pd.to_numeric(hatla2ee_df['Year'], errors='coerce').astype('Int64')

contact_df['Trim'] = contact_df['Trim'].apply(standardize_trim)
hatla2ee_df['Trim'] = hatla2ee_df['Trim'].apply(standardize_trim)

contact_df['Price'] = pd.to_numeric(contact_df['Price'], errors='coerce').astype('Int64')
hatla2ee_df['Price'] = pd.to_numeric(hatla2ee_df['Price'], errors='coerce').astype('Int64')

# =============================================
# REMOVE MODEL=TRIM DUPLICATES
# =============================================
def remove_model_equals_trim_duplicates(df):
    df['base_key'] = (
        df['Brand'].astype(str) + '|' + 
        df['Model'].astype(str).str.lower() + '|' + 
        df['Year'].astype(str) + '|' +
        df['Price'].astype(str)
    )
    
    df['model_equals_trim'] = df.apply(
        lambda row: str(row['Model']).lower().strip() == str(row['Trim']).lower().strip(), 
        axis=1
    )
    
    keys_with_both = df.groupby('base_key').apply(
        lambda g: g['model_equals_trim'].any() and (~g['model_equals_trim']).any()
    )
    keys_to_filter = set(keys_with_both[keys_with_both].index)
    
    mask = ~((df['base_key'].isin(keys_to_filter)) & (df['model_equals_trim']))
    result = df[mask].drop(columns=['base_key', 'model_equals_trim'])
    
    removed = len(df) - len(result)
    if removed > 0:
        print(f"Removed {removed} duplicate entries where model=trim")
    
    return result

contact_df = remove_model_equals_trim_duplicates(contact_df)
hatla2ee_df = remove_model_equals_trim_duplicates(hatla2ee_df)

# Create match key
contact_df['match_key'] = (
    contact_df['Brand'].astype(str) + '|' + 
    contact_df['Model'].astype(str).str.lower() + '|' + 
    contact_df['Year'].astype(str) + '|' + 
    contact_df['Trim'].astype(str).str.lower() + '|' +
    contact_df['Price'].astype(str)
)

hatla2ee_df['match_key'] = (
    hatla2ee_df['Brand'].astype(str) + '|' + 
    hatla2ee_df['Model'].astype(str).str.lower() + '|' + 
    hatla2ee_df['Year'].astype(str) + '|' + 
    hatla2ee_df['Trim'].astype(str).str.lower() + '|' +
    hatla2ee_df['Price'].astype(str)
)

print(f"\nUnique cars in Contact: {contact_df['match_key'].nunique()}")
print(f"Unique cars in Hatla2ee: {hatla2ee_df['match_key'].nunique()}")

contact_keys = set(contact_df['match_key'])
hatla2ee_keys = set(hatla2ee_df['match_key'])
common_keys = contact_keys.intersection(hatla2ee_keys)
print(f"Exact matches: {len(common_keys)}")

# =============================================
# CREATE UNIFIED DATAFRAMES
# =============================================

contact_unified = pd.DataFrame({
    'Brand': contact_df['Brand'],
    'Model': contact_df['Model'],
    'Year': contact_df['Year'],
    'Price': contact_df['Price'],
    'Trim': contact_df['Trim'],
    'Image_Paths': contact_df['Image Paths'],
    'Transmission': 'Automatic',
    'Fuel_Type': None,
    'Body_Type': None,
    'Engine_Capacity': None,
    'Horsepower': contact_df['Combined Maximum Power (HP @ RPM)'],
    'Torque': contact_df['Combined Maximum Torque (N.m @ RPM)'],
    'Max_Speed': contact_df['Maximum Speed (Km/h)'],
    'Acceleration': contact_df['Acceleration (0 - 100 km/h)'],
    'Width': contact_df['Width (mm)'],
    'Length': contact_df['Length (mm)'],
    'Height': contact_df['Height (mm)'],
    'Wheelbase': contact_df['Wheelbase (mm)'],
    'Seats': contact_df['Number of Seats'],
    'Cylinders': contact_df['Cylinders'],
    'Fuel_Tank': contact_df['Fuel Tank Capacity (Litre)'],
    'Number_of_Gears': contact_df['Number of Gears'],
    'Fuel_Consumption': contact_df['Combined Fuel/Energy Consumption (Liter/100 KM)'],
    'match_key': contact_df['match_key'],
})

hatla2ee_unified = pd.DataFrame({
    'Brand': hatla2ee_df['Brand'],
    'Model': hatla2ee_df['Model'],
    'Year': hatla2ee_df['Year'],
    'Price': hatla2ee_df['Price'],
    'Trim': hatla2ee_df['Trim'],
    'Image_Paths': hatla2ee_df['Image Paths'],
    'Transmission': hatla2ee_df['Transmission'],
    'Fuel_Type': hatla2ee_df['Fuel Type'],
    'Body_Type': hatla2ee_df['Body Type'],
    'Engine_Capacity': hatla2ee_df['Engine Capacity'],
    'Horsepower': hatla2ee_df['Horsepower'],
    'Torque': hatla2ee_df['Torque'],
    'Max_Speed': None,
    'Acceleration': hatla2ee_df['Acceleration'],
    'Width': hatla2ee_df['Width'],
    'Length': hatla2ee_df['Length'],
    'Height': hatla2ee_df['Height'],
    'Wheelbase': hatla2ee_df['Wheel Base'],
    'Seats': hatla2ee_df['Seats'],
    'Cylinders': hatla2ee_df['Number of Cylinders'],
    'Fuel_Tank': hatla2ee_df['Fuel Tank Capacity'],
    'Number_of_Gears': hatla2ee_df['Speeds'],
    'Fuel_Consumption': hatla2ee_df['Consumption'],
    'match_key': hatla2ee_df['match_key'],
})

# =============================================
# MERGE MATCHING CARS
# =============================================

def count_valid_fields(row):
    """Count non-empty, non-null fields (excluding key columns)"""
    key_cols = ['Brand', 'Model', 'Year', 'Trim', 'Price', 'match_key']
    count = 0
    for col, val in row.items():
        if col in key_cols:
            continue
        if pd.notna(val) and str(val).strip() not in ['', 'N/A', 'nan', '0', 'None']:
            count += 1
    return count

def merge_rows(row1, row2):
    merged = {}
    for col in row1.index:
        if col == 'Image_Paths':
            paths1 = str(row1[col]) if pd.notna(row1[col]) and str(row1[col]) != 'nan' else ''
            paths2 = str(row2[col]) if pd.notna(row2[col]) and str(row2[col]) != 'nan' else ''
            all_paths = [p for p in [paths1, paths2] if p]
            merged[col] = '; '.join(all_paths) if all_paths else None
        elif col == 'match_key':
            merged[col] = row1[col]
        else:
            val1, val2 = row1[col], row2[col]
            val1_valid = pd.notna(val1) and str(val1).strip() not in ['', 'N/A', 'nan', '0', 'None']
            val2_valid = pd.notna(val2) and str(val2).strip() not in ['', 'N/A', 'nan', '0', 'None']
            merged[col] = val1 if val1_valid else (val2 if val2_valid else val1)
    return pd.Series(merged)

# Merge matches
merged_rows = []
for key in common_keys:
    c_match = contact_unified[contact_unified['match_key'] == key]
    h_match = hatla2ee_unified[hatla2ee_unified['match_key'] == key]
    if len(c_match) > 0 and len(h_match) > 0:
        merged_rows.append(merge_rows(c_match.iloc[0], h_match.iloc[0]))

merged_df = pd.DataFrame(merged_rows) if merged_rows else pd.DataFrame()

contact_unique = contact_unified[~contact_unified['match_key'].isin(common_keys)]
hatla2ee_unique = hatla2ee_unified[~hatla2ee_unified['match_key'].isin(common_keys)]

print(f"\nMerged cars: {len(merged_df)}")
print(f"Unique from Contact: {len(contact_unique)}")
print(f"Unique from Hatla2ee: {len(hatla2ee_unique)}")

# Combine
final_df = pd.concat([merged_df, contact_unique, hatla2ee_unique], ignore_index=True)
final_df = final_df.drop(columns=['match_key'], errors='ignore')

# Clean N/A values
for col in final_df.columns:
    if final_df[col].dtype == 'object':
        final_df[col] = final_df[col].replace(['N/A', 'nan', 'None', ''], np.nan)

# =============================================
# FILL MISSING BODY TYPES FROM SAME BRAND/MODEL
# =============================================
print("\nFilling missing body types from same brand/model...")

# Create lookup: brand+model -> body_type (from rows that have it)
body_type_lookup = {}
for _, row in final_df.iterrows():
    if pd.notna(row['Body_Type']) and str(row['Body_Type']).strip():
        key = f"{row['Brand']}|{row['Model']}".lower()
        if key not in body_type_lookup:
            body_type_lookup[key] = row['Body_Type']

# Fill missing body types
filled_count = 0
for idx in final_df.index:
    if pd.isna(final_df.at[idx, 'Body_Type']) or not str(final_df.at[idx, 'Body_Type']).strip():
        key = f"{final_df.at[idx, 'Brand']}|{final_df.at[idx, 'Model']}".lower()
        if key in body_type_lookup:
            final_df.at[idx, 'Body_Type'] = body_type_lookup[key]
            filled_count += 1

print(f"Filled {filled_count} missing body types")

# =============================================
# REMOVE EXACT DUPLICATES (keep one with most info)
# =============================================
print("\nRemoving exact duplicates (keeping entry with most info)...")

final_df['info_count'] = final_df.apply(count_valid_fields, axis=1)

# Create full duplicate key (all main fields)
final_df['full_key'] = (
    final_df['Brand'].astype(str) + '|' + 
    final_df['Model'].astype(str).str.lower() + '|' + 
    final_df['Year'].astype(str) + '|' + 
    final_df['Trim'].astype(str).str.lower() + '|' +
    final_df['Price'].astype(str)
)

# Sort by info_count descending, then drop duplicates keeping first (most info)
before_count = len(final_df)
final_df = final_df.sort_values('info_count', ascending=False)
final_df = final_df.drop_duplicates(subset='full_key', keep='first')
after_count = len(final_df)
print(f"Removed {before_count - after_count} exact duplicates")

final_df = final_df.drop(columns=['info_count', 'full_key'], errors='ignore')

# =============================================
# FINAL CLEANUP
# =============================================
final_df['base_key'] = (
    final_df['Brand'].astype(str) + '|' + 
    final_df['Model'].astype(str).str.lower() + '|' + 
    final_df['Year'].astype(str) + '|' +
    final_df['Price'].astype(str)
)

final_df['model_equals_trim'] = final_df.apply(
    lambda row: str(row['Model']).lower().strip() == str(row['Trim']).lower().strip(), 
    axis=1
)

keys_with_both = final_df.groupby('base_key').apply(
    lambda g: g['model_equals_trim'].any() and (~g['model_equals_trim']).any()
)
keys_to_filter = set(keys_with_both[keys_with_both].index)

before_count = len(final_df)
final_df = final_df[~((final_df['base_key'].isin(keys_to_filter)) & (final_df['model_equals_trim']))]
after_count = len(final_df)
if before_count > after_count:
    print(f"Final cleanup: Removed {before_count - after_count} model=trim duplicates")

final_df = final_df.drop(columns=['base_key', 'model_equals_trim'], errors='ignore')
final_df = final_df.sort_values(['Brand', 'Model', 'Year', 'Trim', 'Price']).reset_index(drop=True)

print(f"\n=== FINAL SUMMARY ===")
print(f"Total cars: {len(final_df)}")
print(f"Unique brands: {final_df['Brand'].nunique()}")

final_df.to_csv('merged_cars.csv', index=False, encoding='utf-8')
print(f"\nSaved to: merged_cars.csv")

print("\n=== Cars per Brand ===")
print(final_df['Brand'].value_counts().head(20).to_string())

# Show sample Audi trims to verify S-Line fix
audi_df = final_df[final_df['Brand'] == 'Audi'][['Model', 'Year', 'Trim', 'Body_Type']].head(10)
print("\n=== Sample Audi (verify S-Line trim) ===")
print(audi_df.to_string())
