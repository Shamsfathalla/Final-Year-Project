import pandas as pd

def clean_body_shapes(input_file, output_file):
    # 1. Load the dataset
    # Assuming the column containing the shapes is named 'Body shape'
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return

    # 2. Define the mapping dictionary
    # Keys are the current names from your txt file
    # Values are the target names you requested
    shape_mapping = {
        # SUV & 4x4 Group
        'SUV': 'SUV',
        'Crossover': 'SUV',
        '4X4': '4X4',
        
        # Sedan Group
        'Sedan': 'Sedan',
        
        # Hatchback Group
        'Hatchback': 'Hatchback',
        'Small city car': 'Hatchback',
        
        # Estate / Station Wagon Group
        'Estate': 'Station',
        'Station': 'Station',
        
        # Sports & Coupe Group
        'Sports / Coupe': 'Coupe',  
        'Coupe': 'Coupe',
        
        # Van Group
        'Van': 'Van',
        'Van / Bus': 'Van',
        'MPV': 'Van',  # Multi-Purpose Vehicles are generally categorized as Vans
        
        # Convertible Group
        'Convertible': 'Convertible',
        'Cabriolet': 'Convertible',
        
        # Truck Group
        'Pickup': 'Truck',
        'Truck': 'Truck'
    }

    # 3. Clean and Apply Mapping
    # Ensure the column is string type and strip whitespace
    if 'Body Shape' in df.columns:
        df['Body Shape'] = df['Body Shape'].astype(str).str.strip()
        
        # Map the values. 
        # using .replace() ensures that if a value isn't in the map, it stays as is.
        # using .map() would turn unmapped values into NaN.
        df['Body Shape'] = df['Body Shape'].replace(shape_mapping)
        
        # Optional: Filter to keep only the allowed list if you want to remove unknowns
        allowed_shapes = [
            'Sedan', 'SUV', 'Hatchback', '4X4', 'Coupe', 
            'Van', 'Convertible', 'Pickup', 'Station'
        ]
        # Uncomment the next line if you want to drop rows that don't match the target list
        # df = df[df['Body Shape'].isin(allowed_shapes)]

        print("Body shapes merged successfully.")
        print(df['Body Shape'].value_counts())
    else:
        print("Error: Column 'Body Shape' not found in CSV.")
        return

    # 4. Save to new CSV
    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to '{output_file}'")

# Example Usage:
# Replace 'your_data.csv' with your actual csv filename
clean_body_shapes('cleaned_cars.csv', 'cleaned_body_shapes.csv')