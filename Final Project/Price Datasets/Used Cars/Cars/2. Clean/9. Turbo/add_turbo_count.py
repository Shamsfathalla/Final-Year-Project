import pandas as pd
import re

# Read the CSV file
df = pd.read_csv('cleaned_cars_v5.csv')

def get_turbo_count(engine):
    """
    Determine turbo count based on engine description.
    0: No Turbo / Natural Aspiration
    1: Turbo / Supercharged
    2: Twin Turbo / Biturbo / Quad Turbo
    """
    if pd.isna(engine):
        return 0
    
    engine_lower = str(engine).lower()
    
    # Check for twin/bi/quad turbo first (2)
    if any(term in engine_lower for term in ['twin-turbo', 'twin turbo', 'twinturbo', 
                                               'biturbo', 'bi-turbo', 'bi turbo',
                                               'quad turbo', 'quad-turbo', 'quadturbo']):
        return 2
    
    # Check for single turbo/supercharged (1)
    if any(term in engine_lower for term in ['turbo', 'turbocharged', 
                                               'supercharged', 'supercharger',
                                               'tfsi',  # Audi's turbocharged engines
                                               'tsi',   # VW's turbocharged engines
                                               't-gdi', # Hyundai/Kia turbo
                                               'ecoboost']):  # Ford turbo
        return 1
    
    # No turbo / Natural aspiration (0)
    return 0

# Apply the function to create the new column
df['Turbo Count'] = df['Engine'].apply(get_turbo_count)

# Reorder columns to place 'Turbo Count' after 'Cylinder Count'
columns = df.columns.tolist()

# Find the index of 'Cylinder Count'
cyl_idx = columns.index('Cylinder Count')

# Remove 'Turbo Count' from its current position (at the end)
columns.remove('Turbo Count')

# Insert 'Turbo Count' right after 'Cylinder Count'
columns.insert(cyl_idx + 1, 'Turbo Count')

# Reorder the dataframe
df = df[columns]

# Save to new CSV
df.to_csv('cleaned_cars_v6.csv', index=False)

# Print some statistics
print("Turbo Count Distribution:")
print(df['Turbo Count'].value_counts().sort_index())
print(f"\nTotal rows processed: {len(df)}")

# Show some examples of each category
print("\n--- Examples of No Turbo (0) ---")
print(df[df['Turbo Count'] == 0]['Engine'].head(5).tolist())

print("\n--- Examples of Turbo/Supercharged (1) ---")
print(df[df['Turbo Count'] == 1]['Engine'].head(5).tolist())

print("\n--- Examples of Twin Turbo/Biturbo (2) ---")
print(df[df['Turbo Count'] == 2]['Engine'].head(5).tolist())

print("\nSaved to cleaned_cars_v6.csv")
