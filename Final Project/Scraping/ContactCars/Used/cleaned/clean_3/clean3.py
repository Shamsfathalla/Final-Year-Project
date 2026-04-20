import pandas as pd

# 1. Load the data
input_filename = "used_cars_data_smart_fixed.csv"
output_filename = "contact_used_cars_data_ml.csv"

try:
    df = pd.read_csv(input_filename)
    print(f"📂 Loaded: {input_filename} ({len(df)} rows)")

    # 2. Define columns to drop
    # Added 'Car Status' to the list as requested
    columns_to_drop = ["URL", "Seller Name", "Seller Phone", "Car Status"]

    # 3. Drop them safely
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # 4. Reorder Columns
    # Defining the exact order requested
    desired_order = [
        "Brand", "Model", "Trim", "Year", "Price", 
        "Mileage", "Color", "Fuel Type", "Body Shape", 
        "Transmission", "Engine Capacity", "Cylinder Count", 
        "Image Paths"
    ]
    
    # Check if all columns exist before reordering to prevent errors
    # (This handles casing differences or missing columns gracefully)
    available_cols = [col for col in desired_order if col in df.columns]
    df = df[available_cols]

    # 5. Save the Final ML-Ready CSV
    df.to_csv(output_filename, index=False)
    
    print("\n✅ Columns Dropped:")
    for col in columns_to_drop:
        print(f"   - {col}")

    print("\n✅ Columns Reordered. Final Sequence:")
    print(df.columns.tolist())
        
    print(f"\n💾 Saved final dataset to: {output_filename}")
    print(f"📊 Final Shape: {df.shape} (Rows, Columns)")
    print("\nFirst 5 rows preview:")
    print(df.head())

except FileNotFoundError:
    print(f"❌ Error: Could not find '{input_filename}'. Make sure you ran the previous script.")
except KeyError as e:
    print(f"❌ Error during reordering: One of the requested columns is missing from the data.\nDetails: {e}")