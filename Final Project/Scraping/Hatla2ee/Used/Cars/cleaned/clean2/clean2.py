import pandas as pd
import numpy as np

# 1. Read the CSV file
df = pd.read_csv('cleaned_data.csv')

# --- Previous Cleaning Steps ---

# Drop rows with empty "Image Paths"
df = df.dropna(subset=['Image Paths'])

# Clean "Price": Remove ' EGP', remove commas, convert to numeric
df['Price'] = df['Price'].astype(str).str.replace(' EGP', '', regex=False)
df['Price'] = df['Price'].str.replace(',', '', regex=False)
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df = df.dropna(subset=['Price'])

# Drop rows where Price is cheaper than 10,000
df = df[df['Price'] >= 10000]

# Drop rows where Price < 100,000 AND Year > 2015 (As per your previous logic)
condition_to_drop = (df['Price'] < 100000) & (df['Year'] > 2015)
df = df[~condition_to_drop]

# --- New Steps: Rename, Add Empty Columns, Reorder ---

# 2. Rename columns
# We only need to rename CC -> Engine Capacity now.
# We are NOT renaming 'Condition' to 'Car Status' because we are dropping it.
df = df.rename(columns={
    'CC': 'Engine Capacity'
})

# 3. Add new columns with empty values
df['Cylinder Count'] = np.nan  # or use "" for empty string
df['Body Shape'] = np.nan      # or use "" for empty string

# 4. Reorder columns
# Exact order requested:
desired_order = [
    'Brand', 'Model', 'Trim', 'Year', 'Price', 'Mileage', 
    'Color', 'Fuel Type', 'Body Shape', 'Transmission', 
    'Engine Capacity', 'Cylinder Count', 'Image Paths'
]

# Select columns in the specific order
# Note: This effectively drops "Condition"/"Car Status" because it is not in the list
df = df[desired_order]

# 5. Save to a new CSV file
output_filename = 'hatla2ee_used_cars_data_ml.csv'
df.to_csv(output_filename, index=False)

print(f"Processing complete. Saved to '{output_filename}'.")
print(df.head())