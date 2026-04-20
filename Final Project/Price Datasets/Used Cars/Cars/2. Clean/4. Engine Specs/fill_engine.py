import pandas as pd

# Define file names
base_file = "merged_all_used_cars_cleaned1.csv"
mapping_file = "fully_mapped_cars_egypt_filled_final.csv"
output_file = "merged_cars_ordered.csv"

# Load the datasets
df_base = pd.read_csv(base_file)
df_mapping = pd.read_csv(mapping_file)

# 1. Drop the columns from the base file to ensure complete override
columns_to_override = ['Engine Capacity', 'Cylinder Count']
df_base_cleaned = df_base.drop(columns=columns_to_override, errors='ignore')

# 2. Select the keys and the new data from the mapping file
# Note: Ensure these column names match your CSV headers exactly
mapping_cols = ['Brand', 'Model', 'Year', 'Engine Capacity', 'Cylinder Count', 'Engine']
df_mapping_subset = df_mapping[mapping_cols].drop_duplicates(subset=['Brand', 'Model', 'Year'])

# 3. Perform the merge
# We keep all records from the original base file
df_final = pd.merge(df_base_cleaned, df_mapping_subset, on=['Brand', 'Model', 'Year'], how='left')

# 4. Define the exact header order requested
# If any of these columns don't exist in your base file, they will be created as empty
final_header_order = [
    'Brand', 'Model', 'Trim', 'Year', 'Price', 'Mileage', 
    'Color', 'Fuel Type', 'Body Shape', 'Transmission', 
    'engine', 'Engine Capacity', 'Cylinder Count', "Image Paths"
]

# Standardize case to match your requested list (Optional, but safer)
# This handles situations where columns might be 'brand' vs 'Brand'
df_final.columns = [c.title() if c.lower() != 'engine' else 'engine' for c in df_final.columns]
actual_final_order = [c for c in final_header_order if c in df_final.columns]

# Reorder the dataframe
df_final = df_final[actual_final_order]

# 5. Save to CSV
df_final.to_csv(output_file, index=False)

print(f"Process complete. File saved as {output_file} with the requested header order.")