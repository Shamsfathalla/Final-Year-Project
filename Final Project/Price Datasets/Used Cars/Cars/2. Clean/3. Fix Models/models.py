import pandas as pd

# 1. Load the dataset
df = pd.read_csv('merged_all_used_cars_cleaned1.csv')

# 2. Extract unique combinations of Brand, Model, and Year
unique_models = df[['Brand', 'Model', 'Year']].drop_duplicates()

# 3. Sort the values for a clean list
unique_models = unique_models.sort_values(by=['Brand', 'Model', 'Year'])

# 4. Save to "unique_models.txt"
output_file = 'unique_models.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    for index, row in unique_models.iterrows():
        # Format: "Brand Model Year"
        line = f"{row['Brand']} {row['Model']} {row['Year']}"
        f.write(line + '\n')

print(f"Successfully saved unique models to {output_file}")