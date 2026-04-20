import pandas as pd

# Load the CSV file
df = pd.read_csv('Final_Used_Cars_Egypt_Assessed.csv')

# Drop rows where Year > 2020 or condition < 2
df_filtered = df[(df['Condition_Score'] > 1)]

# Save to a new CSV file
df_filtered.to_csv('Final_Used_Cars_Egypt_Assessed_filtered.csv', index=False)
