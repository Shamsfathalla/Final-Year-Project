import pandas as pd

# 1. Load the original CSV
df = pd.read_csv('hatla2ee_price_history_cleaned.csv')

# 2. Function to calculate the global year range for each Brand + Model (e.g. "2014-2021")
def get_global_year_range(x):
    years = sorted(x.dropna().unique())
    if len(years) == 0: return 'All'
    if len(years) == 1: return str(years[0])
    return f"{years[0]}-{years[-1]}"

# Create a mapping of Brand/Model to their combined Year range string
global_years = df.groupby(['Brand', 'Model'])['Year'].apply(get_global_year_range).reset_index()

# 3. Group prices by Brand, Model, and Month/Year (combining all years)
df_grouped = df.groupby(['Brand', 'Model', 'Month/Year'], as_index=False).agg({
    'Average Price': 'mean',
    'Min Price': 'min',
    'Max Price': 'max'
})

# 4. Merge the year range back into the aggregated dataset
df_final = pd.merge(df_grouped, global_years, on=['Brand', 'Model'], how='left')

# 5. Clean up the numbers (round averages to integers)
df_final['Average Price'] = df_final['Average Price'].round().astype(int)
df_final['Min Price'] = df_final['Min Price'].astype(int)
df_final['Max Price'] = df_final['Max Price'].astype(int)

# 6. Reorder the columns to match the original structure
df_final = df_final[['Brand', 'Model', 'Year', 'Month/Year', 'Average Price', 'Min Price', 'Max Price']]

# 7. Sort the values alphabetically to keep it organized
df_final.sort_values(by=['Brand', 'Model'], inplace=True)

# 8. Save the combined data to a new CSV file
df_final.to_csv('hatla2ee_price_history_aggregated.csv', index=False)

print("Data successfully aggregated and saved to 'hatla2ee_price_history_aggregated.csv'")