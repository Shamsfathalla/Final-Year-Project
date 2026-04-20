import pandas as pd

# Load CSVs
new_cars = pd.read_csv('new_cars.csv')
used_cars = pd.read_csv('used_cars.csv')

# Define the target column order as requested
column_order = [
    'brand', 'model', 'trim', 'year', 'price', 'mileage', 'color', 
    'brand tier', 'transmission', 'fuel type', 'body type', 'condition', 
    'car condition', 'engine', 'engine capacity', 'cylinder count', 
    'turbo count', 'horsepower', 'torque', 'max speed', 'acceleration', 
    'drivetrain', 'number of gears', 'fuel tank capacity', 'fuel consumption', 
    'electric fuel consumption', 'max electric driving range', 
    'width', 'length', 'height', 'wheelbase', 'seats', 'image paths',
    'model_average_price', 'model_min_price', 'model_max_price'
]

# Mapping for New Cars
new_mapping = {
    'Brand': 'brand',
    'Model': 'model',
    'Trim': 'trim',
    'Year': 'year',
    'Price': 'price',
    'Brand_Tier': 'brand tier',
    'Transmission': 'transmission',
    'Fuel_Type': 'fuel type',
    'Body_Type': 'body type',
    'Car_Condition': 'car condition',
    'Engine_Capacity': 'engine capacity',
    'Cylinders': 'cylinder count',
    'Horsepower': 'horsepower',
    'Torque': 'torque',
    'Max_Speed': 'max speed',
    'Acceleration': 'acceleration',
    'Drivetrain': 'drivetrain',
    'Number_of_Gears': 'number of gears',
    'Fuel_Tank': 'fuel tank capacity',
    'Fuel_Consumption': 'fuel consumption',
    'Electric_Fuel Consumption': 'electric fuel consumption',
    'Max_Electric_Driving_Range': 'max electric driving range',
    'Width': 'width',
    'Length': 'length',
    'Height': 'height',
    'Wheelbase': 'wheelbase',
    'Seats': 'seats',
    'Image_Paths': 'image paths'
}

# Mapping for Used Cars
used_mapping = {
    'Brand': 'brand',
    'Model': 'model',
    'Trim': 'trim',
    'Year': 'year',
    'Price': 'price',
    'Mileage': 'mileage',
    'Color': 'color',
    'Brand_Tier': 'brand tier',
    'Transmission': 'transmission',
    'Fuel Type': 'fuel type',
    'Body Shape': 'body type',
    'Condition': 'condition',
    'Car_Condition': 'car condition',
    'Engine': 'engine',
    'Engine Capacity': 'engine capacity',
    'Cylinder Count': 'cylinder count',
    'Turbo Count': 'turbo count',
    'HP': 'horsepower',
    'Drivetrain': 'drivetrain',
    'Image Paths': 'image paths',
    'model_average_price': 'model_average_price',
    'model_min_price': 'model_min_price',
    'model_max_price': 'model_max_price'
}

# Map Brand_Tier numeric values to strings if necessary
tier_map = {4: 'economy', 3: 'premium', 2: 'luxury', 1: 'exotic', '4': 'economy', '3': 'premium', '2': 'luxury', '1': 'exotic'}
new_cars['Brand_Tier'] = new_cars['Brand_Tier'].map(tier_map)
used_cars['Brand_Tier'] = used_cars['Brand_Tier'].map(tier_map)

# Select and Rename columns
new_processed = new_cars.rename(columns=new_mapping)
# Filter only columns that exist in mapping to avoid issues if source is missing something
new_processed = new_processed[[c for c in new_mapping.values() if c in new_processed.columns]]

used_processed = used_cars.rename(columns=used_mapping)
used_processed = used_processed[[c for c in used_mapping.values() if c in used_processed.columns]]

# Concatenate
merged = pd.concat([new_processed, used_processed], ignore_index=True)

# Reindex to ensure final order
merged = merged.reindex(columns=column_order)

# Fill missing with "-" EXCEPT for the new model price columns to keep them truly null/NaN
cols_to_fill = [c for c in column_order if c not in ['model_average_price', 'model_min_price', 'model_max_price']]
merged[cols_to_fill] = merged[cols_to_fill].fillna('-')

# Save to CSV
merged.to_csv('merged_cars.csv', index=False)
print("Merge complete! Output saved to 'merged_cars.csv'.")