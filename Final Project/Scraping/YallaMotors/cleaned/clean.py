import pandas as pd
import numpy as np

# Load the CSV file
df = pd.read_csv('yallamotor_cars.csv')

# 1. Drop unwanted columns
# Added 'Condition' here (which was previously renamed to 'Car Status') to drop it immediately.
cols_to_drop = ['Car Title', 'Location', 'URL', 'Condition']
df = df.drop(columns=cols_to_drop, errors='ignore')

# 2. Rename columns
# Removed 'Condition' renaming since we dropped it.
df = df.rename(columns={
    'CC': 'Engine Capacity'
})

# 3. Clean the 'Price' column
if 'Price' in df.columns:
    df['Price'] = df['Price'].astype(str)
    df['Price'] = df['Price'].str.replace('EGP', '', regex=False).str.strip()
    
    # Filter rows based on Price < 10,000
    temp_price = pd.to_numeric(df['Price'].str.replace(',', ''), errors='coerce')
    df = df[temp_price >= 10000]

# 4. Drop rows with empty Image Path
if 'Image Paths' in df.columns:
    df['Image Paths'] = df['Image Paths'].replace('', np.nan)
    df = df.dropna(subset=['Image Paths'])

# 5. Add 'Cylinder Count' column with empty values
df['Cylinder Count'] = np.nan

# 6. Reorder columns
# Defines the exact order requested. 
# Note: Ensure the CSV has columns named 'Brand', 'Model', etc., or this step will raise a KeyError.
# I matched 'image paths' from your text to 'Image Paths' from your code.
desired_order = [
    'Brand', 'Model', 'Trim', 'Year', 'Price', 'Mileage', 
    'Color', 'Fuel Type', 'Body Shape', 'Transmission', 
    'Engine Capacity', 'Cylinder Count', 'Image Paths'
]

# Reindex ensures the order. Columns missing from the CSV will be created as empty (NaN).
df = df.reindex(columns=desired_order)

# Save the cleaned data
df.to_csv('yalla_motors_used_cars_data_ml.csv', index=False)

print("Data cleaning complete. Saved to 'yalla_motors_used_cars_data_ml.csv'")