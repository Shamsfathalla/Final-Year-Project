# Enhanced HP Column Addition with Comprehensive Lookup
# Includes all brands with accurate HP values

import pandas as pd
import os

# Import all HP lookup dictionaries
from hp_premium import HP_PREMIUM
from hp_standard import HP_STANDARD
from hp_asian import HP_ASIAN
from hp_european import HP_EUROPEAN
from hp_other import HP_OTHER

# Combine all lookup dictionaries
HP_LOOKUP = {}
HP_LOOKUP.update(HP_PREMIUM)
HP_LOOKUP.update(HP_STANDARD)
HP_LOOKUP.update(HP_ASIAN)
HP_LOOKUP.update(HP_EUROPEAN)
HP_LOOKUP.update(HP_OTHER)

print(f"Total HP entries in lookup: {len(HP_LOOKUP)}")


def estimate_hp_from_engine(brand, model, engine, capacity, cylinders, turbo):
    """Estimate HP based on engine characteristics when exact match not found."""
    
    # Electric vehicles
    if "Electric" in str(engine) or capacity == 0:
        # Default estimates for electric vehicles by brand
        ev_hp = {
            "BMW": 340, "Mercedes-Benz": 300, "Audi": 300,
            "Hyundai": 220, "Kia": 215, "Toyota": 200,
            "BYD": 200, "Tesla": 400, "Volkswagen": 200,
            "Volvo": 300, "Porsche": 450, "Nissan": 150,
            "Honda": 180, "Peugeot": 136, "Renault": 130,
            "Chevrolet": 200, "Ford": 250, "Jaguar": 400,
            "Hummer": 1000, "Lotus": 600, "Rivian": 800,
            "Lucid": 800, "Rolls-Royce": 577, "Avatr": 578,
            "Deepal": 218, "Im Motors": 578,
        }
        return ev_hp.get(brand, 180)
    
    # Base HP calculation: HP per cc
    if turbo >= 1:
        hp_per_cc = 0.085  # 85 HP per liter for turbo
    else:
        hp_per_cc = 0.060  # 60 HP per liter for NA
    
    base_hp = capacity * hp_per_cc
    
    # Twin-turbo bonus
    if turbo == 2:
        base_hp *= 1.20
    
    # Cylinder count adjustment
    if cylinders >= 12:
        base_hp *= 1.35
    elif cylinders >= 8:
        base_hp *= 1.25
    elif cylinders >= 6:
        base_hp *= 1.12
    
    # Brand-specific tuning adjustments
    performance_brands = {
        "Ferrari": 1.45, "Lamborghini": 1.45, "Porsche": 1.30,
        "BMW": 1.18, "Mercedes-Benz": 1.18, "Audi": 1.18,
        "Aston Martin": 1.35, "Bentley": 1.25, "Maserati": 1.25,
        "Jaguar": 1.20, "Lotus": 1.35, "Cupra": 1.20,
        "Rolls-Royce": 1.20, "McLaren": 1.50, "Bugatti": 1.60,
        "Alfa Romeo": 1.15, "Mini": 1.12,
    }
    
    economy_brands = {
        "Daewoo": 0.82, "Lada": 0.75, "Fiat": 0.88,
        "Suzuki": 0.88, "Daihatsu": 0.85, "Chery": 0.88,
        "Geely": 0.88, "BYD": 0.88, "Brilliance": 0.85,
        "Changan": 0.88, "JAC": 0.88, "Chana": 0.85,
        "Hafei": 0.80, "Lifan": 0.82, "DFSK": 0.85,
    }
    
    if brand in performance_brands:
        base_hp *= performance_brands[brand]
    elif brand in economy_brands:
        base_hp *= economy_brands[brand]
    
    # Model-specific adjustments for performance variants
    model_lower = str(model).lower()
    engine_lower = str(engine).lower()
    
    # Performance model detection
    if any(x in model_lower for x in ['m2', 'm3', 'm4', 'm5', 'm6', 'm8']):
        base_hp = max(base_hp, 400)  # M cars minimum 400hp
    if 'cs' in model_lower and brand == 'BMW':
        base_hp *= 1.10  # CS variants are more powerful
    if 'competition' in model_lower:
        base_hp *= 1.08
    if any(x in model_lower for x in ['amg', 'rs', 'srt']):
        base_hp = max(base_hp, 350)
    if 'gt' in model_lower and brand in ['Ferrari', 'Porsche', 'Bentley', 'Aston Martin']:
        base_hp = max(base_hp, 450)
    if 'turbo' in engine_lower and 'twin' in engine_lower:
        base_hp *= 1.05
    
    # Ensure minimum reasonable values
    min_hp = 37
    if capacity >= 3000:
        min_hp = 150
    elif capacity >= 2000:
        min_hp = 100
    elif capacity >= 1500:
        min_hp = 70
    
    return max(int(base_hp), min_hp)


def get_hp(row):
    """Get HP for a given row, using lookup or estimation."""
    try:
        key = (
            str(row['Brand']),
            str(row['Model']),
            str(row['Engine']),
            int(row['Engine Capacity']) if pd.notna(row['Engine Capacity']) else 0,
            int(row['Cylinder Count']) if pd.notna(row['Cylinder Count']) else 0,
            int(row['Turbo Count']) if pd.notna(row['Turbo Count']) else 0
        )
        
        # Try exact match first
        if key in HP_LOOKUP:
            return HP_LOOKUP[key]
        
        # Fallback to estimation
        return estimate_hp_from_engine(
            key[0], key[1], key[2], key[3], key[4], key[5]
        )
    except Exception as e:
        print(f"Error processing row: {e}")
        return 100  # Default fallback


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'cleaned_cars_v6.csv')
    output_file = os.path.join(script_dir, 'cleaned_cars_v7.csv')
    
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Total rows: {len(df)}")
    
    # Add HP column
    print("Calculating HP values...")
    df['HP'] = df.apply(get_hp, axis=1)
    
    # Reorder columns to put HP after Turbo Count
    cols = list(df.columns)
    turbo_idx = cols.index('Turbo Count')
    cols.remove('HP')
    cols.insert(turbo_idx + 1, 'HP')
    df = df[cols]
    
    # Count exact matches vs estimates
    exact_matches = 0
    for _, row in df.iterrows():
        key = (
            str(row['Brand']),
            str(row['Model']),
            str(row['Engine']),
            int(row['Engine Capacity']) if pd.notna(row['Engine Capacity']) else 0,
            int(row['Cylinder Count']) if pd.notna(row['Cylinder Count']) else 0,
            int(row['Turbo Count']) if pd.notna(row['Turbo Count']) else 0
        )
        if key in HP_LOOKUP:
            exact_matches += 1
    
    print(f"\nExact lookup matches: {exact_matches}/{len(df)} ({100*exact_matches/len(df):.1f}%)")
    print(f"Estimated values: {len(df) - exact_matches}")
    
    # Save to new file
    print(f"\nSaving to {output_file}...")
    df.to_csv(output_file, index=False)
    
    # Print statistics
    print(f"\nDone! HP column added.")
    print(f"HP range: {df['HP'].min()} - {df['HP'].max()}")
    
    # Show sample of special cars
    print(f"\n=== Sample Special/Performance Cars ===")
    special_cars = df[df['Model'].str.contains('M4|M3|M5|RS|AMG|GT|CS', case=False, na=False)]
    if len(special_cars) > 0:
        print(special_cars[['Brand', 'Model', 'Engine', 'HP']].head(30).to_string())
    
    print(f"\n=== Sample Regular Cars ===")
    regular_cars = df[df['Brand'].isin(['Toyota', 'Honda', 'Hyundai', 'Kia', 'Chevrolet'])]
    if len(regular_cars) > 0:
        print(regular_cars[['Brand', 'Model', 'Engine', 'HP']].sample(min(30, len(regular_cars))).to_string())


if __name__ == "__main__":
    main()
