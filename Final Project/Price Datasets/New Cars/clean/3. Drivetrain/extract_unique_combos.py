import pandas as pd

df = pd.read_csv('new_cars_cleaned.csv')

# Get unique Brand + Model + Trim combinations
unique_combos = df[['Brand', 'Model', 'Trim']].drop_duplicates().sort_values(['Brand', 'Model', 'Trim'])

# Save to txt file with format: Brand | Model | Trim | Drivetrain
# You can fill in the Drivetrain column (FWD, RWD, AWD) in this file
with open('unique_brand_model_trim.txt', 'w', encoding='utf-8') as f:
    f.write(f"{'Brand':<25} | {'Model':<20} | {'Trim':<35} | Drivetrain\n")
    f.write('-' * 100 + '\n')
    for _, row in unique_combos.iterrows():
        f.write(f"{row['Brand']:<25} | {row['Model']:<20} | {row['Trim']:<35} | \n")

print(f"Total unique Brand/Model/Trim combinations: {len(unique_combos)}")
print("Saved to unique_brand_model_trim.txt")
print("\nUnique brands:", df['Brand'].nunique())
print("Unique models:", df['Model'].nunique())
