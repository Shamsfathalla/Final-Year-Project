import pandas as pd
import numpy as np

# ==========================================
# 1. LOAD AND PRE-PROCESS
# ==========================================
filename = "used_cars_data.csv"
output_filename = "used_cars_data_clean.csv"

# Load with options to handle whitespace automatically
df = pd.read_csv(filename, skipinitialspace=True)

print(f"🔹 Original Row Count: {len(df)}")

# Function to normalize missing values
def normalize_nan(val):
    if pd.isna(val): return np.nan
    s = str(val).strip()
    # Check for various forms of "Missing"
    if s.lower() in ['n/a', 'nan', '--', '-', '', 'null', 'unknown']:
        return np.nan
    return s

# Apply this to the whole dataframe to fix "--" and "N/A"
df = df.applymap(normalize_nan)

# ==========================================
# 2. DROP "TOTAL GARBAGE" ROWS
# ==========================================
# If a car doesn't have a Brand, Model, Year, or Price, it is useless for ML.
# This removes the rows like: "N/A N/A N/A ..."
initial_drop_cols = ['Brand', 'Model', 'Year', 'Price']
df.dropna(subset=initial_drop_cols, inplace=True)

print(f"🔹 Rows after removing entries with no Price/Brand/Year: {len(df)}")

# ==========================================
# 3. CLEAN NUMERIC COLUMNS
# ==========================================
def clean_numeric(x):
    if pd.isna(x): return np.nan
    # Remove characters that aren't numbers (keep only digits and decimal point)
    # This handles "1,200,000 EGP", "1600 cc", etc.
    clean_str = ''.join(c for c in str(x) if c.isdigit() or c == '.')
    if not clean_str: return np.nan
    return float(clean_str)

df['Price_Clean'] = df['Price'].apply(clean_numeric)
df['CC_Clean'] = df['Engine Capacity'].apply(clean_numeric)
df['Cylinders_Clean'] = df['Cylinder Count'].apply(clean_numeric)

# Drop rows where Price is 0 or NaN (failed parsing)
df = df[df['Price_Clean'] > 0]

print(f"🔹 Rows after parsing numbers: {len(df)}")

# ==========================================
# 4. IMPUTE MISSING CYLINDERS (Your Logic)
# ==========================================
# Logic: If Cylinders are missing, look for the 'Mode' (most common) cylinder count
# first in cars with same Brand+Model+CC, then in cars with just same CC.

# Step A: Fill matching Brand + Model + CC
df['Cylinders_Clean'] = df.groupby(['Brand', 'Model', 'CC_Clean'])['Cylinders_Clean'].transform(
    lambda x: x.fillna(x.mode().iloc[0] if not x.mode().empty else np.nan)
)

# Step B: Fill matching CC only (Fallback)
df['Cylinders_Clean'] = df.groupby('CC_Clean')['Cylinders_Clean'].transform(
    lambda x: x.fillna(x.mode().iloc[0] if not x.mode().empty else np.nan)
)

# Update the real column
df['Cylinder Count'] = df['Cylinders_Clean']

# ==========================================
# 5. HANDLE TRIM & FINAL CLEANUP
# ==========================================
# Protect missing trims so they don't get dropped
df['Trim'] = df['Trim'].fillna("Unspecified")

# Now drop rows where we STILL have missing critical data
# (e.g. Engine Capacity was "--" and couldn't be fixed, or Cylinders couldn't be found)
critical_cols = ['Price_Clean', 'CC_Clean', 'Cylinder Count', 'Transmission', 'Body Shape']
df.dropna(subset=critical_cols, inplace=True)

# Format columns nicely (Integers)
df['Price'] = df['Price_Clean'].astype(int)
df['Engine Capacity'] = df['CC_Clean'].astype(int)
df['Cylinder Count'] = df['Cylinder Count'].astype(int)

# Remove helper columns
df.drop(columns=['Price_Clean', 'CC_Clean', 'Cylinders_Clean'], inplace=True)

print(f"✅ Final Clean Row Count: {len(df)}")

if len(df) == 0:
    print("⚠️ WARNING: CSV is empty. Check if your 'Price' or 'Engine Capacity' columns are formatted unexpectedly.")
else:
    df.to_csv(output_filename, index=False)
    print(f"💾 Saved to {output_filename}")