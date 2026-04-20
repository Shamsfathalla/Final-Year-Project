import pandas as pd
import numpy as np

# 1. Load your dataset
df = pd.read_csv('merged_cars.csv')

# 2. Replace all '-' with standard database NULLs (NaN)
df.replace('-', np.nan, inplace=True)

# 3. Remove commas from numbers (like width, length, height)
# so "1,873" becomes 1873
columns_with_commas = ['width', 'length', 'height']
for col in columns_with_commas:
    if df[col].dtype == 'object':
        df[col] = df[col].str.replace(',', '', regex=False)

# 4. Export the clean version
df.to_csv('database_ready_cars.csv', index=False)
print("Cleaned CSV created successfully!")