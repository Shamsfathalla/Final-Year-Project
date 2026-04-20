import pandas as pd

# Load the dataset
file_path = r"C:\Users\shams\uni\fyp\Testing\Scrape\Contact\New\Final\cleaned\new_cars_data.csv"
df = pd.read_csv(file_path)

# 1. Remove rows where Brand is "N/A" (the string) or actual NaN
# We filter out the specific rows you don't want while keeping "N/A" elsewhere
df = df[df['Brand'].notna()]
df = df[df['Brand'].astype(str).str.upper() != 'N/A']

# 2. Clean the Price column
# We create a temporary series to find rows to drop, but update the original column
temp_price = pd.to_numeric(
    df['Price'].astype(str).str.replace(',', '').str.replace(' EGP', ''), 
    errors='coerce'
)

# 3. Drop rows where Price would be 1 EGP
# This uses the temp_price to filter the dataframe rows
df = df[temp_price != 1]

# Now, update the actual Price column to the clean format "1000000"
# We fill any conversion errors back with "N/A" to satisfy your requirement
df['Price'] = temp_price.fillna("N/A")

# Remove decimals if the price is a valid number
df['Price'] = df['Price'].apply(lambda x: int(x) if isinstance(x, float) and not pd.isna(x) else x)

# 4. Drop specific columns
cols_to_drop = ['URL']
df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

# Save the cleaned file
# na_rep="N/A" ensures that any actual NaNs are written as the string "N/A" in the CSV
df.to_csv('contact_new_clean.csv', index=False, na_rep="N/A")

print(f"Cleaning complete. Remaining rows: {len(df)}")