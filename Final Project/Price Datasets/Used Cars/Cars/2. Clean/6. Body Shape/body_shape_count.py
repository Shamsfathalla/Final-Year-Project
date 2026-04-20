import pandas as pd

# Load the dataset
df = pd.read_csv('cleaned_cars.csv')

# --- TASK 1: Counts of Body Shape types ---
# value_counts() finds unique types and how many times they appear
shape_counts = df['Body Shape'].value_counts()

with open('body_shape_counts.txt', 'w') as f:
    f.write("BODY SHAPE COUNTS\n")
    f.write("=================\n")
    # Write each shape and its count (e.g., Sedan: 15)
    for shape, count in shape_counts.items():
        f.write(f"{shape}: {count}\n")

print("Created 'body_shape_counts.txt'")


# --- TASK 2: Cars with Blank Body Shape ---
# Filter for NaN values and select only the required columns
missing_shapes = df[df['Body Shape'].isna()][['Brand', 'Model', 'Year']]

# We save this as a tab-separated or space-separated file for readability in .txt
missing_shapes.to_csv('missing_body_shapes.txt', sep='\t', index=False)

print("Created 'missing_body_shapes.txt'")