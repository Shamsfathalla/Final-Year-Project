import pandas as pd

# Read the CSV file
df = pd.read_csv('merged_cars.csv')

# Extract unique brands
unique_brands = df['brand'].dropna().unique()

# Save to new CSV
pd.DataFrame({'brand': unique_brands}).to_csv('unique_brands.csv', index=False)

print("Unique brands saved to unique_brands.csv")