import pandas as pd
import re

# Read the CSV file
df = pd.read_csv('hatla2ee_price_history.csv')

# Drop the URL column
df = df.drop(columns=['URL'])

# Function to extract Brand, Model, and Year from Car Name
def parse_car_name(car_name):
    """
    Parse car names like "Used Audi Q3 2021 Prices" or "Used BMW 318 2010 Prices"
    Returns: Brand, Model, Year
    """
    # Remove "Used " prefix and " Prices" suffix
    cleaned = car_name.replace("Used ", "").replace(" Prices", "")
    
    # Split into parts
    parts = cleaned.split()
    
    if len(parts) >= 3:
        brand = parts[0]  # First word is the brand
        year = parts[-1]  # Last word is the year
        model = ' '.join(parts[1:-1])  # Everything in between is the model
        return brand, model, year
    elif len(parts) == 2:
        return parts[0], parts[1], None
    else:
        return cleaned, None, None

# Apply the function to create new columns
df[['Brand', 'Model', 'Year']] = df['Car Name'].apply(lambda x: pd.Series(parse_car_name(x)))

# Drop the original Car Name column
df = df.drop(columns=['Car Name'])

# Reorder columns to put Brand, Model, Year first
cols = ['Brand', 'Model', 'Year'] + [col for col in df.columns if col not in ['Brand', 'Model', 'Year']]
df = df[cols]

# Filter out rows where Month/Year is not a valid date
# Valid dates have format like "Jan 2026", "Oct 2025", etc.
valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def is_valid_date(value):
    """Check if Month/Year value starts with a valid month abbreviation"""
    if pd.isna(value):
        return False
    parts = str(value).split()
    if len(parts) >= 1 and parts[0] in valid_months:
        return True
    return False

# Count rows before filtering
rows_before = len(df)

# Apply filter
df = df[df['Month/Year'].apply(is_valid_date)]

# Count rows after filtering
rows_after = len(df)
print(f"Removed {rows_before - rows_after} rows with invalid dates in Month/Year column")

# Save the cleaned data
df.to_csv('hatla2ee_price_history_cleaned.csv', index=False)

# Display sample output
print("Sample of cleaned data:")
print(df.head(20))
print(f"\nTotal rows: {len(df)}")
print(f"\nUnique Brands: {df['Brand'].nunique()}")
print(f"Unique Models: {df['Model'].nunique()}")
print(f"Unique Years: {df['Year'].nunique()}")
print("\nColumns:", list(df.columns))
