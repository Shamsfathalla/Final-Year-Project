import pandas as pd

df = pd.read_csv('new_cars_cleaned.csv')

# Read the filled-in drivetrain lookup from the txt file
drivetrain_lookup = {}
with open('unique_brand_model_trim_filled.txt', 'r', encoding='utf-8') as f:
    next(f)  # skip header
    next(f)  # skip separator line
    for line in f:
        parts = line.strip().split('|')
        if len(parts) >= 4:
            brand = parts[0].strip()
            model = parts[1].strip()
            trim = parts[2].strip()
            drivetrain = parts[3].strip()
            if drivetrain:  # only if filled in
                drivetrain_lookup[(brand, model, trim)] = drivetrain

# Apply drivetrain values
def get_drivetrain(row):
    key = (row['Brand'], row['Model'], row['Trim'])
    return drivetrain_lookup.get(key, '')

df['Drivetrain'] = df.apply(get_drivetrain, axis=1)

# Check how many were filled
filled = df['Drivetrain'].ne('').sum()
total = len(df)
print(f"Filled {filled}/{total} rows with drivetrain values")
print(f"Missing: {total - filled} rows")

# Save to new CSV
df.to_csv('new_cars_with_drivetrain.csv', index=False)
print("\nSaved to new_cars_with_drivetrain.csv")
