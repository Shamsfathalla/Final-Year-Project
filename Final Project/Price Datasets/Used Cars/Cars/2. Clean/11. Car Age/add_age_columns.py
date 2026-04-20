# Add car_age and miles_per_year columns
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'cleaned_cars_v7.csv')
output_file = os.path.join(script_dir, 'cleaned_cars_v8.csv')

# Current year
CURRENT_YEAR = 2026

print(f"Reading {input_file}...")
df = pd.read_csv(input_file)
print(f"Total rows: {len(df)}")

# Add car_age column
print("Adding car_age column...")
df['car_age'] = CURRENT_YEAR - df['Year']

# Add miles_per_year column (handle division by zero for brand new cars)
print("Adding miles_per_year column...")
df['miles_per_year'] = df.apply(
    lambda row: round(row['Mileage'] / row['car_age'], 1) if row['car_age'] > 0 else 0,
    axis=1
)

# Reorder columns to put car_age and miles_per_year before Image Paths
cols = list(df.columns)
cols.remove('car_age')
cols.remove('miles_per_year')

# Find Image Paths position
if 'Image Paths' in cols:
    img_idx = cols.index('Image Paths')
    cols.insert(img_idx, 'miles_per_year')
    cols.insert(img_idx, 'car_age')
else:
    # If no Image Paths, add at the end
    cols.append('car_age')
    cols.append('miles_per_year')

df = df[cols]

# Save to new file
print(f"Saving to {output_file}...")
df.to_csv(output_file, index=False)

# Print statistics
print(f"\nDone!")
print(f"car_age range: {df['car_age'].min()} - {df['car_age'].max()} years")
print(f"miles_per_year range: {df['miles_per_year'].min()} - {df['miles_per_year'].max()}")

print(f"\nSample output:")
print(df[['Brand', 'Model', 'Year', 'Mileage', 'car_age', 'miles_per_year']].head(20).to_string())
