import pandas as pd

# Read the CSV file
input_csv = 'Used_Cars_Egypt.csv'
df = pd.read_csv(input_csv)


# Calculate the average, min, and max price for each (Brand, Model) group
grouped = df.groupby(['Brand', 'Model'])['Price'].agg([
	('model_average_price', 'mean'),
	('model_min_price', 'min'),
	('model_max_price', 'max')
]).reset_index()


# Merge the calculated columns back to the original DataFrame
df = df.merge(grouped, on=['Brand', 'Model'], how='left')

# Round the price columns to 2 decimal places
df['model_average_price'] = df['model_average_price'].round(2)
df['model_min_price'] = df['model_min_price'].round(2)
df['model_max_price'] = df['model_max_price'].round(2)

# Save to a new CSV file
output_csv = 'Used_Cars_Egypt_with_model_avg.csv'
df.to_csv(output_csv, index=False)
