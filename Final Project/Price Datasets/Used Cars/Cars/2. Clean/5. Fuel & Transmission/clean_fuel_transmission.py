import pandas as pd

# 1. Read the CSV
df = pd.read_csv('merged_cars_ordered.csv')

# 2. Define the Mapping for Fuel Type
# Maps various synonyms (Gas, Gasoline, Petrol, etc.) to 'Gas'
fuel_mapping = {
    'Gas': 'Gas',
    'Gasoline': 'Gas',
    'Benzine': 'Gas',
    'Petrol': 'Gas',
    'Natural Gas': 'Gas',
    'Diesel': 'Diesel',
    'Hybrid': 'Hybrid',
    'Electric': 'Electric'
}

# 3. Define the Mapping for Transmission
# Standardizes case sensitivity and maps variations like CVT/DSG to 'Automatic'
transmission_mapping = {
    'Automatic': 'Automatic',
    'automatic': 'Automatic',
    'CVT': 'Automatic',
    'Cvt': 'Automatic',
    'cvt': 'Automatic',
    'DSG': 'Automatic',
    'Dct': 'Automatic',
    'Manual': 'Manual',
    'manual': 'Manual'
}

# 4. Apply the cleaning
df['Fuel Type'] = df['Fuel Type'].map(fuel_mapping)
df['Transmission'] = df['Transmission'].map(transmission_mapping)

# 5. Save the cleaned data
df.to_csv('cleaned_cars.csv', index=False)

# Optional: Verify the results
print("Unique Fuel Types:", df['Fuel Type'].unique())
print("Unique Transmission Types:", df['Transmission'].unique())