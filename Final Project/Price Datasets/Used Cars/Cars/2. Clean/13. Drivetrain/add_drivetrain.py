"""
Add Drivetrain column to car CSV - reads/saves from current directory.
Drivetrain: FWD, RWD, AWD - placed before Brand_Tier column.
"""
import pandas as pd
import os

# Brand defaults (most common drivetrain for brand)
BRAND_DEFAULTS = {
    "Alfa Romeo": "FWD", "Aston Martin": "RWD", "Audi": "FWD", "Avatr": "AWD",
    "BAIC": "FWD", "BMW": "RWD", "BYD": "FWD", "Bentley": "AWD", "Bestune": "FWD",
    "Brilliance": "FWD", "Buick": "FWD", "Cadillac": "RWD", "Canghe": "FWD",
    "Caterham": "RWD", "Chana": "FWD", "Changan": "FWD", "Changhe": "FWD",
    "Chery": "FWD", "Chevrolet": "FWD", "Chrysler": "FWD", "Citroen": "FWD",
    "Cupra": "FWD", "DFSK": "FWD", "DS": "FWD", "Daewoo": "FWD", "Daihatsu": "FWD",
    "Deepal": "FWD", "Dodge": "RWD", "Domy": "FWD", "Dongfeng": "FWD",
    "EXEED": "FWD", "Faw": "FWD", "Ferrari": "RWD", "Fiat": "FWD", "Ford": "FWD",
    "Forthing": "FWD", "Foton": "FWD", "GAC": "FWD", "GMC": "RWD", "Geely": "FWD",
    "Great Wall": "FWD", "Hafei": "FWD", "Haima": "FWD", "Hanteng": "FWD",
    "Haval": "FWD", "Havi": "FWD", "Hawtai": "FWD", "Honda": "FWD", "Hummer": "AWD",
    "Hyundai": "FWD", "Im Motors": "AWD", "Infiniti": "RWD", "Isuzu": "RWD",
    "JAC": "FWD", "JMC": "RWD", "Jaguar": "RWD", "Jeep": "AWD", "Jetour": "FWD",
    "KGM": "AWD", "Kaiyi": "FWD", "Karry": "FWD", "Kenbo": "FWD", "Keyton": "FWD",
    "Kia": "FWD", "Kinglong": "RWD", "Lada": "FWD", "Lamborghini": "AWD",
    "Lancia": "FWD", "Land Rover": "AWD", "Lexus": "RWD", "Lifan": "FWD",
    "Lincoln": "RWD", "Lotus": "RWD", "MG": "FWD", "Mahindra": "RWD",
    "Maserati": "RWD", "Mazda": "FWD", "Mercedes-Benz": "RWD", "Mini": "FWD",
    "Mitsubishi": "FWD", "Morgan": "RWD", "Nasr": "FWD", "Nissan": "FWD",
    "Opel": "FWD", "Peugeot": "FWD", "Polestar": "AWD", "Porsche": "RWD",
    "Proton": "FWD", "Range Rover": "AWD", "Renault": "FWD", "Rolls-Royce": "RWD",
    "Rox": "FWD", "Saipa": "FWD", "Seat": "FWD", "Senova": "FWD", "Skoda": "FWD",
    "Smart": "RWD", "Soueast": "FWD", "Speranza": "FWD", "SsangYong": "FWD",
    "Subaru": "AWD", "Suzuki": "FWD", "Tata": "RWD", "Tesla": "RWD",
    "Toyota": "FWD", "VGV": "FWD", "Volkswagen": "FWD", "Volvo": "FWD",
    "Wingamm": "FWD", "Wuling": "FWD", "XPeng": "AWD", "Xiaomi": "RWD",
    "Zeekr": "RWD", "Zotye": "FWD",
}

# Model-specific overrides (where different from brand default)
MODEL_OVERRIDES = {
    # Alfa Romeo
    ("Alfa Romeo", "Giulia"): "RWD", ("Alfa Romeo", "Stelvio"): "AWD", ("Alfa Romeo", "4c"): "RWD",
    # Audi - Q5+ and RS/S models are AWD
    ("Audi", "Q4"): "AWD", ("Audi", "Q5"): "AWD", ("Audi", "Q7"): "AWD", ("Audi", "Q8"): "AWD",
    ("Audi", "A7"): "AWD", ("Audi", "A8"): "AWD", ("Audi", "RS3"): "AWD", ("Audi", "RS5"): "AWD",
    ("Audi", "RSQ8"): "AWD", ("Audi", "S5"): "AWD", ("Audi", "TT"): "AWD",
    # BMW - X models AWD, base sedans RWD
    ("BMW", "X1"): "AWD", ("BMW", "X2"): "AWD", ("BMW", "X3"): "AWD", ("BMW", "X3M"): "AWD",
    ("BMW", "X4"): "AWD", ("BMW", "X4M"): "AWD", ("BMW", "X5"): "AWD", ("BMW", "X5M"): "AWD",
    ("BMW", "X6"): "AWD", ("BMW", "X6M"): "AWD", ("BMW", "X7"): "AWD", ("BMW", "XM"): "AWD",
    ("BMW", "IX"): "AWD", ("BMW", "IX1"): "AWD", ("BMW", "Ix"): "AWD", ("BMW", "iX"): "AWD",
    ("BMW", "I8"): "AWD", ("BMW", "M5"): "AWD", ("BMW", "M8"): "AWD", ("BMW", "M850i"): "AWD",
    # Mercedes - GLC+ SUVs AWD, G-Class AWD
    ("Mercedes-Benz", "A 180"): "FWD", ("Mercedes-Benz", "A 200"): "FWD", ("Mercedes-Benz", "A 150"): "FWD",
    ("Mercedes-Benz", "A 160"): "FWD", ("Mercedes-Benz", "A 250e"): "FWD", ("Mercedes-Benz", "A35"): "AWD",
    ("Mercedes-Benz", "B 150"): "FWD", ("Mercedes-Benz", "B 160"): "FWD", ("Mercedes-Benz", "B 180"): "FWD",
    ("Mercedes-Benz", "B 200"): "FWD", ("Mercedes-Benz", "CLA 180"): "FWD", ("Mercedes-Benz", "CLA 200"): "FWD",
    ("Mercedes-Benz", "CLA 250+"): "FWD", ("Mercedes-Benz", "CLA 45s"): "AWD",
    ("Mercedes-Benz", "GLA 180"): "FWD", ("Mercedes-Benz", "GLA 200"): "FWD",
    ("Mercedes-Benz", "GLB 200"): "FWD", ("Mercedes-Benz", "EQA 260"): "FWD", ("Mercedes-Benz", "EQB 260"): "FWD",
    ("Mercedes-Benz", "GLC 200"): "AWD", ("Mercedes-Benz", "GLC 250"): "AWD", ("Mercedes-Benz", "GLC 300"): "AWD",
    ("Mercedes-Benz", "GLC 350 E"): "AWD", ("Mercedes-Benz", "GLC 43"): "AWD", ("Mercedes-Benz", "GLC 63"): "AWD",
    ("Mercedes-Benz", "GLE 350"): "AWD", ("Mercedes-Benz", "GLE 450"): "AWD", ("Mercedes-Benz", "GLE 63"): "AWD",
    ("Mercedes-Benz", "GLK 250"): "AWD", ("Mercedes-Benz", "GLK 300"): "AWD", ("Mercedes-Benz", "GLK 350"): "AWD",
    ("Mercedes-Benz", "GLS 500"): "AWD", ("Mercedes-Benz", "GLS 580"): "AWD",
    ("Mercedes-Benz", "G 350"): "AWD", ("Mercedes-Benz", "G 500"): "AWD", ("Mercedes-Benz", "G63"): "AWD",
    # Mercedes AMG performance models
    ("Mercedes-Benz", "C43"): "AWD", ("Mercedes-Benz", "C63"): "RWD", ("Mercedes-Benz", "C63 S"): "RWD",
    ("Mercedes-Benz", "E53"): "AWD", ("Mercedes-Benz", "E63"): "AWD", ("Mercedes-Benz", "E63S"): "AWD",
    ("Mercedes-Benz", "GT43"): "AWD", ("Mercedes-Benz", "GT53"): "AWD", ("Mercedes-Benz", "GT63"): "AWD",
    ("Mercedes-Benz", "S63"): "AWD", ("Mercedes-Benz", "SL43"): "AWD",
    # Porsche - Cayenne/Macan AWD
    ("Porsche", "Cayenne"): "AWD", ("Porsche", "Cayenne Coupe"): "AWD", ("Porsche", "Cayenne GTS"): "AWD",
    ("Porsche", "Cayenne S"): "AWD", ("Porsche", "Macan"): "AWD", ("Porsche", "Macan Electric"): "AWD",
    ("Porsche", "Macan S"): "AWD", ("Porsche", "Macan T"): "AWD", ("Porsche", "Taycan Cross Turismo"): "AWD",
    # Toyota - Land Cruiser, Fortuner, Hilux
    ("Toyota", "Land Cruiser"): "AWD", ("Toyota", "Fortuner"): "RWD", ("Toyota", "Hilux"): "RWD",
    ("Toyota", "GR Corolla"): "AWD", ("Toyota", "GR86"): "RWD", ("Toyota", "Sequoia"): "RWD",
    # Nissan
    ("Nissan", "Patrol"): "AWD", ("Nissan", "370Z"): "RWD", ("Nissan", "Pathfinder"): "AWD",
    # Ford
    ("Ford", "Mustang"): "RWD", ("Ford", "Bronco Raptor"): "AWD", ("Ford", "Explorer"): "RWD",
    ("Ford", "Ranger"): "RWD",
    # Chevrolet
    ("Chevrolet", "Camaro"): "RWD", ("Chevrolet", "Corvette"): "RWD", ("Chevrolet", "Tahoe"): "RWD",
    ("Chevrolet", "Suburban"): "RWD", ("Chevrolet", "Silverado"): "RWD", ("Chevrolet", "Pickup"): "RWD",
    # Dodge - all RWD/AWD muscle cars
    ("Dodge", "Challenger"): "RWD", ("Dodge", "Charger"): "RWD", ("Dodge", "Durango"): "RWD",
    ("Dodge", "Ram"): "RWD", ("Dodge", "Dakota"): "RWD",
    # Jeep
    ("Jeep", "Cherokee"): "FWD", ("Jeep", "Compass"): "FWD", ("Jeep", "Renegade"): "FWD",
    # Lexus
    ("Lexus", "ES300"): "FWD", ("Lexus", "CT200H"): "FWD",
    # Volkswagen
    ("Volkswagen", "Touareg"): "AWD", ("Volkswagen", "ID3"): "RWD", ("Volkswagen", "ID4"): "RWD",
    ("Volkswagen", "ID6"): "RWD",
    # Volvo - XC60+ AWD
    ("Volvo", "XC60"): "AWD", ("Volvo", "XC70"): "AWD", ("Volvo", "XC90"): "AWD",
    # Maserati
    ("Maserati", "Levante"): "AWD", ("Maserati", "Grecale"): "AWD",
    # Ferrari
    ("Ferrari", "Purosangue"): "AWD",
    # Mitsubishi
    ("Mitsubishi", "Pajero"): "AWD", ("Mitsubishi", "Outlander"): "AWD",
    # Suzuki
    ("Suzuki", "Jimny"): "AWD", ("Suzuki", "Grand Vitara"): "AWD", ("Suzuki", "Grand vitara"): "AWD",
    # Daihatsu
    ("Daihatsu", "Terios"): "AWD", ("Daihatsu", "Grand Terios"): "AWD", ("Daihatsu", "Rocky"): "AWD",
    ("Daihatsu", "Feroza"): "AWD",
    # Subaru - BRZ is RWD exception
    ("Subaru", "BRZ"): "RWD",
    # Hyundai
    ("Hyundai", "Genesis"): "RWD", ("Hyundai", "Ioniq 5"): "RWD",
    # Kia
    ("Kia", "Stinger"): "RWD",
    # Tesla
    ("Tesla", "Model S"): "AWD", ("Tesla", "Model X"): "AWD", ("Tesla", "Cybertruck"): "AWD",
    # Rolls-Royce
    ("Rolls-Royce", "Cullinan"): "AWD",
    # Infiniti
    ("Infiniti", "FX"): "AWD",
    # Isuzu
    ("Isuzu", "D-Max"): "RWD",
    # GMC
    ("GMC", "Terrain"): "FWD",
    # Mazda
    ("Mazda", "RX"): "RWD",
    # Lotus
    ("Lotus", "Eletre"): "AWD",
    # Haval
    ("Haval", "H9"): "AWD",
    # SsangYong
    ("SsangYong", "Torres"): "AWD", ("SsangYong", "Actyon"): "AWD",
    # Lincoln
    ("Lincoln", "Aviator"): "RWD",
    # Chrysler
    ("Chrysler", "300C"): "RWD", ("Chrysler", "300c"): "RWD", ("Chrysler", "C300"): "RWD",
    ("Chrysler", "M300"): "RWD",
    # Cadillac
    ("Cadillac", "Escalade"): "RWD",
    # BYD
    ("BYD", "Seal"): "RWD", ("BYD", "Tang L"): "AWD", ("BYD", "Leopard 5"): "AWD",
    # Jaguar
    ("Jaguar", "F-pace"): "AWD",
}


def get_drivetrain(brand, model, trim, engine):
    """Get drivetrain based on brand/model with AWD detection from trim/engine."""
    key = (brand, model)
    
    # Check model-specific override first
    if key in MODEL_OVERRIDES:
        drivetrain = MODEL_OVERRIDES[key]
    elif brand in BRAND_DEFAULTS:
        drivetrain = BRAND_DEFAULTS[brand]
    else:
        drivetrain = "FWD"  # Ultimate fallback
    
    # Check for AWD indicators in trim/engine that override to AWD
    trim_lower = str(trim).lower() if pd.notna(trim) else ""
    engine_lower = str(engine).lower() if pd.notna(engine) else ""
    
    awd_indicators = ['quattro', 'xdrive', '4matic', '4x4', 'awd', 'all-wheel', 
                      'all wheel', '4wd', 'e-four', 's-line plus']
    
    for indicator in awd_indicators:
        if indicator in trim_lower or indicator in engine_lower:
            return "AWD"
    
    return drivetrain


def main():
    # Get current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "cleaned_cars_v9.csv")
    output_file = os.path.join(script_dir, "cleaned_cars_v10.csv")
    
    print(f"Reading from: {input_file}")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows")
    
    # Add Drivetrain column
    print("Adding Drivetrain column...")
    df['Drivetrain'] = df.apply(
        lambda row: get_drivetrain(row['Brand'], row['Model'], row['Trim'], row['Engine']),
        axis=1
    )
    
    # Reorder columns - place Drivetrain after HP
    cols = list(df.columns)
    cols.remove('Drivetrain')
    hp_idx = cols.index('HP')
    cols.insert(hp_idx + 1, 'Drivetrain')
    df = df[cols]
    
    # Show distribution
    print("\nDrivetrain distribution:")
    print(df['Drivetrain'].value_counts())
    
    # Show sample by brand
    print("\nSample by brand:")
    sample = df.groupby(['Brand', 'Model', 'Drivetrain']).size().reset_index(name='count')
    print(sample.head(20).to_string())
    
    # Save
    df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
