import pandas as pd

# Load the CSV
df = pd.read_csv('new_cars.csv')

# Add the new column with value "New"
df['Car_Condition'] = 'New'

# Save the updated CSV
df.to_csv('new_cars.csv', index=False)