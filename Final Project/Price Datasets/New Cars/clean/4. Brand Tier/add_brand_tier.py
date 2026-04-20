# Add Brand Tier column
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'new_cars.csv')
output_file = os.path.join(script_dir, 'new_cars_with_tier.csv')

# Brand Tier Dictionary (Egyptian Market)
# 1: Exotic
# 2: Luxury
# 3: Premium
# 4: Economy

BRAND_TIER = {
    # Tier 1: Exotic
    "Ferrari": 1,
    "Lamborghini": 1,
    "Bentley": 1,
    "Rolls-Royce": 1,
    "Aston Martin": 1,
    "McLaren": 1,
    "Bugatti": 1,
    "Maserati": 1,
    "Lotus": 1,
    "Caterham": 1,
    
    # Tier 2: Luxury
    "Mercedes-Benz": 2,
    "BMW": 2,
    "Audi": 2,
    "Porsche": 2,
    "Lexus": 2,
    "Land Rover": 2,
    "Jaguar": 2,
    "Volvo": 2,
    "Cadillac": 2,
    "Lincoln": 2,
    "Infiniti": 2,
    "Genesis": 2,
    "Tesla": 2,
    "Alfa Romeo": 2,
    "Hummer": 2,
    "Avatr": 2,
    "Xpeng": 2,
    "Im Motors": 2,
    
    # Tier 3: Premium
    "Toyota": 3,
    "Honda": 3,
    "Hyundai": 3,
    "Kia": 3,
    "Mazda": 3,
    "DS": 3,
    "Volkswagen": 3,
    "Nissan": 3,
    "Mitsubishi": 3,
    "Ford": 3,
    "Chevrolet": 3,
    "Jeep": 3,
    "Peugeot": 3,
    "Citroen": 3,
    "Renault": 3,
    "Opel": 3,
    "Skoda": 3,
    "Seat": 3,
    "Subaru": 3,
    "Mini": 3,
    "Cupra": 3,
    "Dodge": 3,
    "Chrysler": 3,
    "Buick": 3,
    "GMC": 3,
    "MG": 3,
    "BYD": 3,
    "Geely": 3,
    "Chery": 3,
    "EXEED": 3,
    "Haval": 3,
    "Jetour": 3,
    "GAC": 3,
    "KGM": 3,
    "SsangYong": 3,
    
    # Tier 4: Economy
    "Suzuki": 4,
    "Fiat": 4,
    "Lada": 4,
    "Daewoo": 4,
    "Daihatsu": 4,
    "Proton": 4,
    "Speranza": 4,
    "Changan": 4,
    "Chana": 4,
    "Changhe": 4,
    "JAC": 4,
    "BAIC": 4,
    "Brilliance": 4,
    "Great Wall": 4,
    "Lifan": 4,
    "DFSK": 4,
    "Dongfeng": 4,
    "Faw": 4,
    "Foton": 4,
    "Hafei": 4,
    "Haima": 4,
    "Hanteng": 4,
    "Havi": 4,
    "Hawtai": 4,
    "Isuzu": 4,
    "JMC": 4,
    "Kaiyi": 4,
    "Karry": 4,
    "Kenbo": 4,
    "Keyton": 4,
    "Kinglong": 4,
    "Lancia": 4,
    "Mahindra": 4,
    "Forthing": 4,
    "Canghe": 4,
    "Domy": 4,
    "Bestune": 4,
    "Deepal": 4,
}

print(f"Reading {input_file}...")
df = pd.read_csv(input_file)
print(f"Total rows: {len(df)}")

# Get all unique brands in the dataset
unique_brands = df['Brand'].unique()
print(f"Unique brands in dataset: {len(unique_brands)}")

# Check for missing brands
missing_brands = [b for b in unique_brands if b not in BRAND_TIER]
if missing_brands:
    print(f"Warning: Missing tier for brands: {missing_brands}")
    print("Assigning default tier 4 (Economy) for missing brands")

# Add Brand Tier column (default to 4 for unknown brands - Economy)
print("Adding Brand_Tier column...")
df['Brand_Tier'] = df['Brand'].map(BRAND_TIER).fillna(4).astype(int)

# Reorder columns to put Brand_Tier before Image_Paths
cols = list(df.columns)
cols.remove('Brand_Tier')

if 'Image_Paths' in cols:
    img_idx = cols.index('Image_Paths')
    cols.insert(img_idx, 'Brand_Tier')
else:
    cols.append('Brand_Tier')

df = df[cols]

# Save to new file
print(f"Saving to {output_file}...")
df.to_csv(output_file, index=False)

# Print statistics
print(f"\nDone!")
print(f"\nBrand Tier distribution:")
print(df['Brand_Tier'].value_counts().sort_index())

print(f"\nSample by tier:")
for tier in sorted(df['Brand_Tier'].unique()):
    tier_names = {1: "Exotic", 2: "Luxury", 3: "Premium", 4: "Economy"}
    sample = df[df['Brand_Tier'] == tier][['Brand', 'Model', 'Brand_Tier']].drop_duplicates('Brand').head(5)
    print(f"\nTier {tier} ({tier_names.get(tier, 'Unknown')}):")
    print(sample.to_string(index=False))
