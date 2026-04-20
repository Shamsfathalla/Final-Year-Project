import pandas as pd
import string
import random

def generate_random_id(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_car_id(file_path):
    print(f"Reading {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Generate unique IDs
    print("Generating unique IDs...")
    num_rows = len(df)
    unique_ids = set()
    while len(unique_ids) < num_rows:
        unique_ids.add(generate_random_id())
    
    ids_list = list(unique_ids)
    random.shuffle(ids_list)
    
    # Insert column at the start
    if 'Car ID' in df.columns:
        print("'Car ID' column already exists. Skipping insertion.")
    else:
        df.insert(0, 'Car ID', ids_list)
        # Save back to CSV
        print(f"Saving updated CSV to {file_path}...")
        df.to_csv(file_path, index=False)
        print("Execution successful!")

if __name__ == "__main__":
    csv_path = r'c:\Users\shams\uni\fyp\Testing\database\id\merged_cars.csv'
    add_car_id(csv_path)