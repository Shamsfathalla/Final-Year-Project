import pandas as pd

# 1. Configuration
input_csv = 'filled_car_data_2.csv'
output_txt = 'unique_cars.txt'

try:
    # 2. Read the CSV
    df = pd.read_csv(input_csv)

    # 3. Extract specific columns
    # Make sure these names match your CSV headers exactly
    selected_columns = ['Brand', 'Model', 'Trim', 'Year']
    df_subset = df[selected_columns]

    # 4. Drop duplicates (keep unique rows only)
    unique_cars = df_subset.drop_duplicates()

    # 5. Save to TXT file
    # sep='\t' uses a tab to separate columns. Change to ',' for comma.
    unique_cars.to_csv(output_txt, sep='\t', index=False)

    print(f"Successfully saved {len(unique_cars)} unique entries to {output_txt}")

except FileNotFoundError:
    print(f"Error: The file '{input_csv}' was not found.")
except KeyError as e:
    print(f"Error: Column not found in CSV - {e}")