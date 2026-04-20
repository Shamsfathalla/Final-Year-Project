"""
Script to clean Price, Mileage, and Engine Capacity columns
- Removes all alphabetic characters
- Removes commas
- Keeps only numeric values
- Suitable for machine learning
"""

import pandas as pd
import re

def clean_numeric(value):
    """Extract only numeric digits from a value"""
    if pd.isna(value):
        return None
    # Convert to string and remove all non-numeric characters except dots
    cleaned = re.sub(r'[^\d.]', '', str(value))
    # Handle empty strings
    if cleaned == '' or cleaned == '.':
        return None
    # Remove trailing dots
    cleaned = cleaned.rstrip('.')
    # If multiple dots, keep only the first one
    parts = cleaned.split('.')
    if len(parts) > 2:
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    return cleaned

def main():
    # Read the CSV file from current directory
    input_file = "cleaned_cars_v4.csv"
    output_file = "cleaned_cars_v5.csv"
    
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Total rows: {len(df)}")
    
    # Show sample before cleaning
    print("\n--- Sample BEFORE cleaning ---")
    print(df[['Price', 'Mileage', 'Engine Capacity']].head(10))
    
    # Clean Price column
    print("\nCleaning Price column...")
    df['Price'] = df['Price'].apply(clean_numeric)
    
    # Clean Mileage column
    print("Cleaning Mileage column...")
    df['Mileage'] = df['Mileage'].apply(clean_numeric)
    
    # Clean Engine Capacity column
    print("Cleaning Engine Capacity column...")
    df['Engine Capacity'] = df['Engine Capacity'].apply(clean_numeric)
    
    # Convert to numeric types
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df['Mileage'] = pd.to_numeric(df['Mileage'], errors='coerce')
    df['Engine Capacity'] = pd.to_numeric(df['Engine Capacity'], errors='coerce')
    
    # Show sample after cleaning
    print("\n--- Sample AFTER cleaning ---")
    print(df[['Price', 'Mileage', 'Engine Capacity']].head(10))
    
    # Show data types
    print("\n--- Data Types ---")
    print(f"Price: {df['Price'].dtype}")
    print(f"Mileage: {df['Mileage'].dtype}")
    print(f"Engine Capacity: {df['Engine Capacity'].dtype}")
    
    # Save to new CSV
    print(f"\nSaving to {output_file}...")
    df.to_csv(output_file, index=False)
    
    print("Done!")
    print(f"\nNull counts after cleaning:")
    print(f"Price: {df['Price'].isna().sum()}")
    print(f"Mileage: {df['Mileage'].isna().sum()}")
    print(f"Engine Capacity: {df['Engine Capacity'].isna().sum()}")

if __name__ == "__main__":
    main()
