import pandas as pd

# Load your dataset
df = pd.read_csv('hatla2ee_used_cars.csv')

# List of columns identified from your image
columns_to_remove = [
    'Car Title','Location', 'Power', 'Description Snippet', "URL", "Body Type"
]

# Drop the columns
# errors='ignore' is added just in case of typos or missing columns
df_cleaned = df.drop(columns=columns_to_remove, errors='ignore')

# Save the result
df_cleaned.to_csv('cleaned_data.csv', index=False)

print("Columns dropped successfully!")