import pandas as pd
import numpy as np

# 1. Read the CSV file
df = pd.read_csv('biddex_cars_final.csv')

# 2. Drop unwanted columns
# Added 'Condition' here to drop "Car Status" at the source
# errors='ignore' ensures no crash if columns are missing
cols_to_drop = ['Power', 'URL', 'Condition']
df = df.drop(columns=cols_to_drop, errors='ignore')

# 3. Fix 'Price': Remove non-numeric characters and convert to numbers
df['Price'] = df['Price'].astype(str).str.replace(r'[^\d]', '', regex=True)
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df = df.dropna(subset=['Price'])

# 4. Rename columns
# removed 'Condition': 'Car Status' from here
df = df.rename(columns={
    'Kilometers': 'Mileage',
    'Cylinders': 'Cylinder Count'
})

# 5. Drop rows with empty cells in 'Image Paths'
df['Image Paths'] = df['Image Paths'].replace(r'^\s*$', np.nan, regex=True)
df = df.dropna(subset=['Image Paths'])

# 6. Reorder Columns
# We define the specific order required
desired_order = [
    'Brand', 'Model', 'Trim', 'Year', 'Price', 
    'Mileage', 'Color', 'Fuel Type', 'Body Shape', 
    'Transmission', 'Engine Capacity', 'Cylinder Count', 'Image Paths'
]

# select only these columns in this order
# check first to avoid KeyErrors if a column name is slightly different in your source
available_cols = [col for col in desired_order if col in df.columns]
df = df[available_cols]

# 7. Save to new CSV
df.to_csv('biddex_used_cars_data_ml.csv', index=False)

print("File cleaned, reordered, and saved as 'biddex_used_cars_data_ml.csv'")