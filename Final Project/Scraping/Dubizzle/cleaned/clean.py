import pandas as pd

# 1. Read the CSV
df = pd.read_csv('dubizzle_cars_final.csv')

# 2. Drop rows where Price is the string "N/A"
df = df[df['Price'] != "N/A"]

# 3. Drop rows where "Price" or "Image Paths" are empty/null
df = df.dropna(subset=['Price', 'Image Paths'])

# 4. Drop "Power", "URL", and "Condition" (Car Status)
# We drop 'Condition' here because you requested to drop 'Car Status'
df = df.drop(columns=['Power', 'URL', 'Condition'], errors='ignore')

# 5. Add "Trim" column and leave it empty
df['Trim'] = None 

# 6. Rename columns to match your desired final output
# I have added mappings for Body Type, Transmission, and Cylinders to match your requested order names
df = df.rename(columns={
    'CC': 'Engine Capacity',
    'Kilometers': 'Mileage',
    'Body Type': 'Body Shape',         # Renaming to match your requested "Body Shape"
    'Transmission Type': 'Transmission', # Renaming to match your requested "Transmission"
    'Cylinders': 'Cylinder Count'      # Renaming to match your requested "Cylinder Count"
})

# 7. Transform Price: "EGP 200,000" -> 200000
df['Price'] = (
    df['Price']
    .astype(str)
    .str.replace(r'EGP\s*|,', '', regex=True)
)
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

# Drop rows if the Price formatting failed, then cast to integer
df = df.dropna(subset=['Price'])
df['Price'] = df['Price'].astype(int)

# 8. Reorder columns
# This enforces the exact order you requested
desired_order = [
    'Brand', 'Model', 'Trim', 'Year', 'Price', 'Mileage', 'Color', 
    'Fuel Type', 'Body Shape', 'Transmission', 'Engine Capacity', 
    'Cylinder Count', 'Image Paths'
]

# Select only these columns (reorders and filters out any extra unneeded columns)
# We use .reindex to avoid errors if a specific column is missing (it will fill with NaN),
# OR you can use df = df[desired_order] if you want it to error when a column is missing.
df = df.reindex(columns=desired_order)

# 9. Save to new CSV
df.to_csv('dubizzle_used_cars_data_ml.csv', index=False)

print("Done! Data cleaned, reordered, and saved to 'dubizzle_used_cars_data_ml.csv'.")