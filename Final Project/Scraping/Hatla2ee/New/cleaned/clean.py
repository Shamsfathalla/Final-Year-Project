import pandas as pd
import re

# 1. Load the CSV file
file_path = "hatla2ee_all_cars.csv" # Adjusted to assume the file is in the current directory
df = pd.read_csv(file_path)

# --- Step: Rename 'Power' to 'Engine Capacity' ---
df.rename(columns={'Power': 'Engine Capacity'}, inplace=True)

# --- NEW STEP: Drop the 'URL' and 'Car Title' columns ---
# errors='ignore' prevents the script from crashing if the columns are already missing
df.drop(columns=['URL', 'Car Title'], inplace=True, errors='ignore')

# 2. Clean the 'Model' column (Robust Fix)
if 'Model' in df.columns:
    df['Model'] = df['Model'].astype(str).str.replace(r'[^a-zA-Z0-9\s]', ' ', regex=True)
    df['Model'] = df['Model'].str.replace(r'\s+', ' ', regex=True).str.strip()

# 3. Clean the 'Price' column
df['Price'] = df['Price'].astype(str)
df['Price'] = df['Price'].str.replace(' EGP', '', regex=False)
df['Price'] = df['Price'].str.replace(',', '', regex=False)
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

# 4. Filter the DataFrame (Price >= 200,000)
df_filtered = df[df['Price'] >= 200000].copy()

# 5. Restore "N/A" for empty cells
df_filtered = df_filtered.fillna("N/A")

# 6. Save the result
df_filtered.to_csv('hatla2ee_new_clean.csv', index=False)

print("Rows filtered. 'Power' renamed. 'URL' and 'Car Title' dropped. 'Model' sanitized.")