import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. DICTIONARY MAPPING
# ---------------------------------------------------------
model_body_map = {
    # SEDANS
    ('Fiat', '128'): 'Sedan', ('Fiat', 'Shahin'): 'Sedan', ('Fiat', '131'): 'Sedan',
    ('Fiat', 'Tipo'): 'Sedan', ('Fiat', 'Linea'): 'Sedan', ('Fiat', 'Siena'): 'Sedan',
    ('Daewoo', 'Lanos'): 'Sedan', ('Daewoo', 'Nubira 1'): 'Sedan', ('Daewoo', 'Nubira 2'): 'Sedan',
    ('Chevrolet', 'Lanos'): 'Sedan', ('Chevrolet', 'Aveo'): 'Sedan', ('Chevrolet', 'Optra'): 'Sedan',
    ('Chevrolet', 'Cruze'): 'Sedan', ('Hyundai', 'Verna'): 'Sedan', ('Hyundai', 'Elantra'): 'Sedan',
    ('Hyundai', 'Accent'): 'Sedan', ('Hyundai', 'Sonata'): 'Sedan', ('Kia', 'Cerato'): 'Sedan',
    ('Kia', 'Rio'): 'Sedan', ('Kia', 'Spectra'): 'Sedan', ('Toyota', 'Corolla'): 'Sedan',
    ('Toyota', 'Yaris'): 'Sedan', ('Toyota', 'Camry'): 'Sedan', ('Nissan', 'Sunny'): 'Sedan',
    ('Nissan', 'Sentra'): 'Sedan', ('Mitsubishi', 'Lancer'): 'Sedan', ('Mitsubishi', 'Shark'): 'Sedan',
    ('BMW', '316i'): 'Sedan', ('BMW', '318i'): 'Sedan', ('BMW', '320i'): 'Sedan',
    ('BMW', '520i'): 'Sedan', ('Mercedes-Benz', 'C 180'): 'Sedan', ('Mercedes-Benz', 'E 200'): 'Sedan',
    ('BYD', 'F3'): 'Sedan', ('Geely', 'Emgrand 7'): 'Sedan', ('Chery', 'Arrizo 5'): 'Sedan',
    ('Renault', 'Logan'): 'Sedan', ('Renault', 'Megane'): 'Sedan', ('Opel', 'Astra'): 'Sedan',
    ('Opel', 'Vectra'): 'Sedan', ('Opel', 'Insignia'): 'Sedan', ('Lada', '2107'): 'Sedan',
    ('Lada', 'Granta'): 'Sedan',

    # SUVS / CROSSOVERS
    ('Hyundai', 'Tucson'): 'SUV', ('Hyundai', 'IX35'): 'SUV', ('Hyundai', 'Creta'): 'SUV',
    ('Kia', 'Sportage'): 'SUV', ('Kia', 'Sorento'): 'SUV', ('Nissan', 'Qashqai'): 'SUV',
    ('Nissan', 'Juke'): 'SUV', ('Chery', 'Tiggo'): 'SUV', ('Chery', 'Tiggo 3'): 'SUV',
    ('Chery', 'Tiggo 7'): 'SUV', ('Mitsubishi', 'Pajero'): 'SUV', ('Toyota', 'Fortuner'): 'SUV',
    ('Toyota', 'Prado'): 'SUV', ('Toyota', 'Land Cruiser'): 'SUV', ('BMW', 'X3'): 'SUV',
    ('BMW', 'X5'): 'SUV', ('Mercedes-Benz', 'GLC 200'): 'SUV', ('Jeep', 'Cherokee'): 'SUV',
    ('Jeep', 'Grand Cherokee'): 'SUV', ('Jeep', 'Wrangler'): 'SUV', ('Jeep', 'Renegade'): 'SUV',
    ('Chevrolet', 'Captiva'): 'SUV', ('Renault', 'Duster'): 'SUV', ('Renault', 'Sandero Stepway'): 'Hatchback',
    ('MG', 'ZS'): 'SUV', ('MG', 'RX5'): 'SUV', ('Peugeot', '3008'): 'SUV', ('Suzuki', 'Vitara'): 'SUV',

    # HATCHBACKS
    ('Fiat', 'Punto'): 'Hatchback', ('Fiat', '500'): 'Hatchback', ('Fiat', '127'): 'Hatchback',
    ('Daewoo', 'Juliet'): 'Hatchback', ('Kia', 'Picanto'): 'Hatchback', ('Hyundai', 'i10'): 'Hatchback',
    ('Hyundai', 'i20'): 'Hatchback', ('Hyundai', 'Getz'): 'Hatchback', ('Renault', 'Sandero'): 'Hatchback',
    ('Renault', 'Clio'): 'Hatchback', ('Peugeot', '206'): 'Hatchback', ('Seat', 'Ibiza'): 'Hatchback',
    ('Seat', 'Leon'): 'Hatchback', ('Ford', 'Fiesta'): 'Hatchback', ('Volkswagen', 'Golf'): 'Hatchback',
    ('Volkswagen', 'Polo'): 'Hatchback', ('Suzuki', 'Swift'): 'Hatchback', ('Suzuki', 'Maruti'): 'Hatchback',
    ('Suzuki', 'Alto'): 'Hatchback', ('Mini', 'Cooper'): 'Hatchback', ('BYD', 'F0'): 'Hatchback',
}

# ---------------------------------------------------------
# 2. PROCESSING FUNCTION
# ---------------------------------------------------------
def process_car_data(input_csv_path, output_csv_path, missing_txt_path):
    print(f"Reading data from: {input_csv_path}")
    
    try:
        df = pd.read_csv(input_csv_path) 
    except FileNotFoundError:
        print(f"Error: The file '{input_csv_path}' was not found.")
        return

    # Clean whitespace
    df['Brand'] = df['Brand'].astype(str).str.strip()
    df['Model'] = df['Model'].astype(str).str.strip()

    initial_missing = df['Body Shape'].isna().sum()
    print(f"Initial missing Body Shapes: {initial_missing}")

    # --- Step 1: Fill using Mode (Existing Data) ---
    print("Step 1: Filling from existing data (Mode)...")
    mode_map = df[df['Body Shape'].notna()].groupby(['Brand', 'Model'])['Body Shape'].apply(
        lambda x: x.mode()[0] if not x.mode().empty else np.nan
    ).to_dict()
    
    def fill_from_mode(row):
        if pd.isna(row['Body Shape']):
            return mode_map.get((row['Brand'], row['Model']), np.nan)
        return row['Body Shape']

    df['Body Shape'] = df.apply(fill_from_mode, axis=1)

    # --- Step 2: Fill using Dictionary (Hardcoded) ---
    print("Step 2: Filling from Dictionary...")
    
    def fill_from_dict(row):
        if pd.isna(row['Body Shape']):
            return model_body_map.get((row['Brand'], row['Model']), row['Body Shape'])
        return row['Body Shape']

    df['Body Shape'] = df.apply(fill_from_dict, axis=1)

    # --- Step 3: Save Output & Missing Log ---
    final_missing_count = df['Body Shape'].isna().sum()
    print(f"Finished. Missing values reduced from {initial_missing} to {final_missing_count}")
    
    # Save the main full dataset
    print(f"Saving filled dataset to: {output_csv_path}")
    df.to_csv(output_csv_path, index=False)

    # Save remaining empty cars to a TXT file (Brand & Model only)
    if final_missing_count > 0:
        print(f"Saving {final_missing_count} remaining empty rows to: {missing_txt_path}")
        
        # Filter for missing rows AND select only specific columns
        missing_rows = df[df['Body Shape'].isna()][['Brand', 'Model']]
        
        # Optional: Uncomment the next line if you only want a unique list of missing models (no duplicates)
        # missing_rows = missing_rows.drop_duplicates()

        missing_rows.to_csv(missing_txt_path, sep='\t', index=False)
    else:
        print("Great news! No missing body shapes remain.")

    print("Done.")

# ---------------------------------------------------------
# 3. RUN THE SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    # FILE NAMES
    input_filename = 'cleaned_body_shapes.csv'       
    output_filename = 'filled_car_data.csv' 
    missing_filename = 'remaining_missing_cars.txt' 
    
    process_car_data(input_filename, output_filename, missing_filename)