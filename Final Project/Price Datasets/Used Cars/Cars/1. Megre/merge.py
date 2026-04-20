import pandas as pd
import os

# 1. Define the list of file names (assuming they are .csv files)
file_names = [
    "biddex_used_cars_data_ml.csv",
    "contact_used_cars_data_ml.csv",
    "dubizzle_used_cars_data_ml.csv",
    "hatla2ee_used_cars_data_ml.csv",
    "yalla_motors_used_cars_data_ml.csv"
]

# 2. Define the exact column order you required
target_columns = [
    "Brand", 
    "Model", 
    "Trim", 
    "Year", 
    "Price", 
    "Mileage", 
    "Color", 
    "Fuel Type", 
    "Body Shape", 
    "Transmission", 
    "Engine Capacity", 
    "Cylinder Count", 
    "Image Paths"
]

dataframes_list = []

print("Starting merge process...")

for file in file_names:
    # Check if file exists to prevent crashing
    if os.path.exists(file):
        try:
            # Read the CSV
            df = pd.read_csv(file)
            
            # --- CRITICAL STEP ---
            # .reindex(columns=...) does two things:
            # 1. It reorders the columns to match your list exactly.
            # 2. If a dataset is missing a column (e.g., 'cylinder count'), 
            #    it adds that column and fills it with NaN/Empty automatically.
            df = df.reindex(columns=target_columns)
            
            # Add to list
            dataframes_list.append(df)
            print(f"Successfully processed: {file} | Shape: {df.shape}")
            
        except Exception as e:
            print(f"Error reading {file}: {e}")
    else:
        print(f"File not found: {file}")

# 3. Concatenate (Stack) all datasets together
if dataframes_list:
    merged_df = pd.concat(dataframes_list, ignore_index=True)

    # 4. Save the final merged file
    output_filename = "merged_all_used_cars.csv"
    merged_df.to_csv(output_filename, index=False)
    
    print("-" * 30)
    print(f"Merge Complete! Saved as '{output_filename}'")
    print(f"Total Rows: {merged_df.shape[0]}")
    print(f"Total Columns: {merged_df.shape[1]}")
else:
    print("No dataframes were loaded.")