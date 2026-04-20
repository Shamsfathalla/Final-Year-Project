import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. EXTENDED DICTIONARY MAPPING
# ---------------------------------------------------------
# This dictionary contains your original mappings plus specific fixes
# for the cars identified in 'remaining_missing_cars.txt'.
extended_mappings = {
    # --- SEDANS ---
    ('Fiat', '128'): 'Sedan', ('Fiat', 'Shahin'): 'Sedan', ('Fiat', '131'): 'Sedan',
    ('Fiat', 'Tipo'): 'Sedan', ('Fiat', 'Linea'): 'Sedan', ('Fiat', 'Siena'): 'Sedan',
    ('Fiat', '1100'): 'Sedan', ('Fiat', '1200'): 'Sedan', ('Lancia', 'Thema'): 'Sedan',
    ('Daewoo', 'Lanos'): 'Sedan', ('Daewoo', 'Nubira 1'): 'Sedan', ('Daewoo', 'Nubira 2'): 'Sedan',
    ('Chevrolet', 'Lanos'): 'Sedan', ('Chevrolet', 'Aveo'): 'Sedan', ('Chevrolet', 'Optra'): 'Sedan',
    ('Chevrolet', 'Cruze'): 'Sedan', ('Chevrolet', 'Cavalier'): 'Sedan', ('Chevrolet', 'Lumina'): 'Sedan',
    ('Chevrolet', 'CSV CR8'): 'Sedan', ('Buick', 'Roadmaster'): 'Sedan',
    ('Hyundai', 'Verna'): 'Sedan', ('Hyundai', 'Elantra'): 'Sedan', ('Hyundai', 'Accent'): 'Sedan',
    ('Hyundai', 'Sonata'): 'Sedan', ('Hyundai', 'Centennial'): 'Sedan', ('Hyundai', 'XD'): 'Sedan',
    ('Kia', 'Cerato'): 'Sedan', ('Kia', 'Rio'): 'Sedan', ('Kia', 'Spectra'): 'Sedan', ('Kia', 'K5'): 'Sedan',
    ('Toyota', 'Corolla'): 'Sedan', ('Toyota', 'Yaris'): 'Sedan', ('Toyota', 'Camry'): 'Sedan',
    ('Toyota', 'Aurion'): 'Sedan', ('Toyota', 'bZ3'): 'Sedan', ('Toyota', 'Crown'): 'Sedan', ('Toyota', 'Ascent'): 'Sedan',
    ('Nissan', 'Sunny'): 'Sedan', ('Nissan', 'Sentra'): 'Sedan', ('Nissan', 'Maxima'): 'Sedan',
    ('Mitsubishi', 'Lancer'): 'Sedan', ('Mitsubishi', 'Shark'): 'Sedan',
    ('BMW', '316i'): 'Sedan', ('BMW', '318i'): 'Sedan', ('BMW', '320i'): 'Sedan', ('BMW', '520i'): 'Sedan',
    ('Bentley', 'Mulsanne'): 'Sedan', ('Chrysler', '300c'): 'Sedan', ('Jaguar', 'X-type'): 'Sedan',
    ('Mercedes-Benz', 'C 180'): 'Sedan', ('Mercedes-Benz', 'E 200'): 'Sedan', ('Mercedes-Benz', 'C 220'): 'Sedan',
    ('Mercedes-Benz', 'E 220'): 'Sedan', ('Mercedes-Benz', 'S 550'): 'Sedan', ('Mercedes-Benz', 'SEL 500'): 'Sedan',
    ('Mercedes-Benz', '230E'): 'Sedan', ('Mercedes-Benz', '280'): 'Sedan', ('Mercedes-Benz', '240'): 'Sedan',
    ('Mercedes-Benz', '300'): 'Sedan', ('Mercedes-Benz', '320'): 'Sedan', ('Mercedes-Benz', '280S'): 'Sedan',
    ('Mercedes-Benz', '250 SE'): 'Sedan', ('Mercedes-Benz', '300 SD'): 'Sedan', ('Mercedes-Benz', 'EQS 580'): 'Sedan',
    ('Mercedes-Benz', 'CLA 250+'): 'Sedan', ('Mercedes-Benz', 'C63'): 'Sedan',
    ('BYD', 'F3'): 'Sedan', ('BYD', 'Qin Plus'): 'Sedan', ('BYD', 'F5'): 'Sedan', ('BYD', 'Seal'): 'Sedan',
    ('Geely', 'Emgrand 7'): 'Sedan', ('Geely', 'Ec7'): 'Sedan',
    ('Chery', 'Arrizo 5'): 'Sedan', ('Chery', 'A5'): 'Sedan', ('Chery', 'Arrizo 3'): 'Sedan', ('Chery', 'E5'): 'Sedan',
    ('MG', '360'): 'Sedan', ('MG', '750'): 'Sedan',
    ('Renault', 'Logan'): 'Sedan', ('Renault', 'Megane'): 'Sedan', ('Renault', 'Laguna'): 'Sedan',
    ('Opel', 'Astra'): 'Sedan', ('Opel', 'Vectra'): 'Sedan', ('Opel', 'Insignia'): 'Sedan',
    ('Lada', '2107'): 'Sedan', ('Lada', 'Granta'): 'Sedan', ('Lada', 'Priora'): 'Sedan',
    ('Lexus', 'ES300'): 'Sedan', ('Lexus', 'LS300'): 'Sedan', ('Lexus', 'LS300c'): 'Sedan',
    ('Lifan', '520'): 'Sedan', ('Volkswagen', 'Cc'): 'Sedan', ('Zotye', 'Z300'): 'Sedan',
    ('Changan', 'Eado'): 'Sedan', ('Changan', 'Eado plus'): 'Sedan', ('Senova', 'A3'): 'Sedan',

    # --- SUVS / CROSSOVERS ---
    ('Hyundai', 'Tucson'): 'SUV', ('Hyundai', 'IX35'): 'SUV', ('Hyundai', 'Creta'): 'SUV',
    ('Hyundai', 'Creta SU2'): 'SUV', ('Hyundai', 'Grand Creta'): 'SUV', ('Hyundai', 'Venue'): 'SUV',
    ('Hyundai', 'Terracan'): 'SUV', ('Hyundai', 'Ioniq 5'): 'SUV',
    ('Kia', 'Sportage'): 'SUV', ('Kia', 'Sorento'): 'SUV',
    ('Nissan', 'Qashqai'): 'SUV', ('Nissan', 'Juke'): 'SUV', ('Nissan', 'Rogue'): 'SUV',
    ('Nissan', 'Xterra'): 'SUV', ('Nissan', 'Kicks'): 'SUV',
    ('Chery', 'Tiggo'): 'SUV', ('Chery', 'Tiggo 3'): 'SUV', ('Chery', 'Tiggo 7'): 'SUV',
    ('Chery', 'EQ7'): 'SUV', ('Chery', 'Tiggo 2'): 'SUV',
    ('Mitsubishi', 'Pajero'): 'SUV', ('Toyota', 'Fortuner'): 'SUV', ('Toyota', 'Prado'): 'SUV',
    ('Toyota', 'Land Cruiser'): 'SUV', ('Toyota', 'C-hr'): 'SUV',
    ('BMW', 'X3'): 'SUV', ('BMW', 'X5'): 'SUV', ('BMW', 'x1'): 'SUV', ('BMW', 'Ix'): 'SUV',
    ('Mercedes-Benz', 'GLC 200'): 'SUV', ('Mercedes-Benz', 'EQB 260'): 'SUV', ('Mercedes-Benz', 'GLE 350'): 'SUV',
    ('Mercedes-Benz', 'ML 350'): 'SUV', ('Mercedes-Benz', 'GLC 63'): 'SUV', ('Mercedes-Benz', 'G 350'): 'SUV',
    ('Mercedes-Benz', 'GLC 350 E'): 'SUV', ('Mercedes-Benz', 'M 320'): 'SUV',
    ('Jeep', 'Cherokee'): 'SUV', ('Jeep', 'Grand Cherokee'): 'SUV', ('Jeep', 'Wrangler'): 'SUV',
    ('Jeep', 'Renegade'): 'SUV', ('Jeep', 'Compass'): 'SUV', ('Jeep', 'SRT8'): 'SUV',
    ('Chevrolet', 'Captiva'): 'SUV', ('Chevrolet', 'Blazer'): 'SUV', ('Chevrolet', 'Frontera'): 'SUV',
    ('Chevrolet', 'Suburban'): 'SUV', ('Chevrolet', 'Tahoe'): 'SUV', ('Chevrolet', 'Trax'): 'SUV',
    ('Chevrolet', 'Groove'): 'SUV',
    ('Renault', 'Duster'): 'SUV',
    ('MG', 'ZS'): 'SUV', ('MG', 'RX5'): 'SUV', ('MG', 'HS+'): 'SUV', ('MG', 'ONE'): 'SUV',
    ('MG', 'RX8'): 'SUV', ('MG', 'Rx5'): 'SUV', ('MG', 'Hs'): 'SUV',
    ('Peugeot', '3008'): 'SUV', ('Suzuki', 'Vitara'): 'SUV', ('Suzuki', 'Grand vitara'): 'SUV',
    ('Suzuki', 'S-cross'): 'SUV', ('Suzuki', 'Fronx'): 'SUV',
    ('Aston Martin', 'DBX'): 'SUV', ('Avatr', '7'): 'SUV', ('Avatr', '11'): 'SUV',
    ('BAIC', 'X7'): 'SUV', ('BAIC', 'X35'): 'SUV', ('BAIC', 'X5'): 'SUV',
    ('BYD', 'Tang L'): 'SUV', ('BYD', 'Atto 3'): 'SUV', ('BYD', 'Leopard 5'): 'SUV',
    ('Canghe', 'Q35'): 'SUV', ('Changan', 'CS85'): 'SUV', ('Changan', 'UNI-T'): 'SUV',
    ('Daihatsu', 'Rocky'): 'SUV', ('DFSK', 'EAGLE 580'): 'SUV', ('DFSK', 'Glory 580'): 'SUV',
    ('DS', '7 Crossback'): 'SUV', ('Ford', 'Bronco Raptor'): 'SUV', ('Ford', 'Edge'): 'SUV',
    ('Ford', 'Escape'): 'SUV', ('Ford', 'Territory'): 'SUV',
    ('Geely', 'Geometry C'): 'SUV', ('Geely', 'Gx2'): 'SUV', ('Hanteng', 'X7S'): 'SUV',
    ('Honda', 'ZRV'): 'SUV', ('Honda', 'Pilot'): 'SUV', ('Im Motors', 'Ls7'): 'SUV',
    ('Jetour', 'X70S'): 'SUV', ('Kaiyi', 'X3 Pro'): 'SUV', ('Kenbo', 'H3'): 'SUV',
    ('Lada', '4x4'): 'SUV', ('Mahindra', 'Xuv500'): 'SUV', ('Mazda', 'Cx-9'): 'SUV',
    ('Opel', 'Antara'): 'SUV', ('Porsche', 'Cayenne GTS'): 'SUV', ('Porsche', 'Macan T'): 'SUV',
    ('Senova', 'X35'): 'SUV', ('Skoda', 'Kushaq'): 'SUV', ('Skoda', 'Yeti'): 'SUV',
    ('Soueast', 'S09'): 'SUV', ('Soueast', 'DX3'): 'SUV', ('Soueast', 'DX8S Coupe'): 'SUV', ('Soueast', 'S05'): 'SUV',
    ('SsangYong', 'Xlv'): 'SUV', ('Subaru', 'Crosstrek'): 'SUV', ('Subaru', 'Xv'): 'SUV',
    ('VGV', 'U70 Pro'): 'SUV', ('Volvo', 'XC30'): 'SUV', ('Volvo', 'XC70'): 'SUV', ('Zeekr', '7X'): 'SUV',

    # --- HATCHBACKS ---
    ('Fiat', 'Punto'): 'Hatchback', ('Fiat', '500'): 'Hatchback', ('Fiat', '127'): 'Hatchback',
    ('Fiat', '500 E'): 'Hatchback',
    ('Daewoo', 'Juliet'): 'Hatchback', ('Kia', 'Picanto'): 'Hatchback',
    ('Hyundai', 'i10'): 'Hatchback', ('Hyundai', 'i20'): 'Hatchback', ('Hyundai', 'Getz'): 'Hatchback',
    ('Hyundai', 'EON'): 'Hatchback', ('Hyundai', 'IONIQ'): 'Hatchback',
    ('Renault', 'Sandero'): 'Hatchback', ('Renault', 'Clio'): 'Hatchback', ('Renault', 'Sandero Stepway'): 'Hatchback',
    ('Peugeot', '206'): 'Hatchback', ('Peugeot', '106'): 'Hatchback',
    ('Seat', 'Ibiza'): 'Hatchback', ('Seat', 'Leon'): 'Hatchback',
    ('Ford', 'Fiesta'): 'Hatchback',
    ('Volkswagen', 'Golf'): 'Hatchback', ('Volkswagen', 'Polo'): 'Hatchback', ('Volkswagen', 'ID3'): 'Hatchback',
    ('Suzuki', 'Swift'): 'Hatchback', ('Suzuki', 'Maruti'): 'Hatchback', ('Suzuki', 'Alto'): 'Hatchback',
    ('Suzuki', 'Sx4'): 'Hatchback',
    ('Mini', 'Cooper'): 'Hatchback',
    ('BYD', 'F0'): 'Hatchback',
    ('Audi', 'A1'): 'Hatchback', ('BAIC', 'A1'): 'Hatchback', ('BMW', 'I3'): 'Hatchback', ('BMW', 'i3'): 'Hatchback',
    ('Citroen', 'Ax'): 'Hatchback', ('Geely', 'Panda'): 'Hatchback', ('Geely', 'Lc'): 'Hatchback', ('Geely', 'Gc2'): 'Hatchback',
    ('Great Wall', 'Coolbear'): 'Hatchback', ('Hafei', 'Lobo'): 'Hatchback',
    ('JAC', 'A10'): 'Hatchback', ('JAC', 'J2'): 'Hatchback', ('JAC', 'J3'): 'Hatchback',
    ('Lexus', 'CT200H'): 'Hatchback', ('Mercedes-Benz', 'A 160'): 'Hatchback',
    ('Nissan', 'Leaf'): 'Hatchback', ('Opel', 'Adam'): 'Hatchback',
    ('Smart', 'Fortwo'): 'Hatchback', ('Toyota', 'GR Corolla'): 'Hatchback',
    ('Wuling', 'Bingo'): 'Hatchback', ('Zotye', 'Z100'): 'Hatchback',

    # --- COUPES / CONVERTIBLES / ROADSTERS ---
    ('Alfa Romeo', '4c'): 'Convertible',
    ('Aston Martin', 'DBS Superleggera Volante'): 'Convertible',
    ('BMW', 'M4 CS'): 'Coupe', ('BMW', 'Z3'): 'Convertible', ('BMW', 'I8'): 'Coupe',
    ('Caterham', 'Seven 275 R'): 'Convertible',
    ('Hyundai', 'Tiburon'): 'Coupe',
    ('Kia', 'Koup'): 'Coupe',
    ('Mercedes-Benz', 'SLC 300'): 'Convertible', ('Mercedes-Benz', 'SLK 300'): 'Convertible',
    ('Mercedes-Benz', 'AMG GT63'): 'Coupe',
    ('Mercedes-Benz', 'CLC 180'): 'Coupe', ('Mercedes-Benz', 'CLC 200'): 'Coupe', ('Mercedes-Benz', 'CLC'): 'Coupe',
    ('Morgan', 'Aero 8'): 'Convertible',
    ('Nissan', '370Z'): 'Coupe',
    ('Porsche', 'Cayman GTS'): 'Coupe',

    # --- VANS / MPVS ---
    ('BAIC', 'MZ 40'): 'Van',
    ('Canghe', 'M50'): 'MPV', ('Chana', 'New Star'): 'Van',
    ('Chevrolet', 'Astro'): 'Van', ('Chevrolet', 'Move'): 'Van', ('Chevrolet', 'HHR'): 'MPV',
    ('Chrysler', 'Town-country'): 'MPV', ('Chrysler', 'Grand-voyager'): 'MPV',
    ('Citroen', 'Picasso'): 'MPV', ('Citroen', 'Spacetourer'): 'Van',
    ('Daihatsu', 'Gran max'): 'Van',
    ('Fiat', 'Doblo'): 'Van', ('Fiat', 'Ducato'): 'Van', ('Fiat', '500 L'): 'MPV',
    ('Foton', 'Gratour'): 'MPV',
    ('Honda', 'Odyssey'): 'MPV', ('Hyundai', 'Ix20'): 'MPV',
    ('Karry', 'Q22'): 'Van', ('Kenbo', 'Minivan'): 'Van', ('Kinglong', 'Van'): 'Van',
    ('Kia', 'Ray'): 'MPV',
    ('Mercedes-Benz', 'EQV 300'): 'Van', ('Mercedes-Benz', 'B 160'): 'MPV',
    ('Mitsubishi', 'Grandis'): 'MPV',
    ('Opel', 'Zafira Tourer'): 'MPV', ('Peugeot', 'Traveller'): 'Van',
    ('Proton', 'Exora'): 'MPV', ('Suzuki', 'Carry'): 'Van', ('Suzuki', 'APV'): 'Van', ('Suzuki', 'Apv'): 'Van',
    ('Toyota', 'Rumion'): 'MPV',

    # --- TRUCKS ---
    ('Chevrolet', 'N-Series'): 'Truck', ('Chevrolet', 'T-Series'): 'Truck',
    ('Chevrolet', 'Avalanche'): 'Truck', ('Chevrolet', 'C10'): 'Truck',
    ('Dodge', 'Dakota'): 'Truck',
    ('DFSK', 'K01s'): 'Truck',
    ('Great Wall', 'Poer'): 'Truck',
    ('Hyundai', 'Santa Cruz'): 'Truck',
    ('Isuzu', 'Npr'): 'Truck',
    ('JMC', 'Boarding'): 'Truck',
    ('Tata', 'Xenon'): 'Truck',
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

    # Clean whitespace and normalize for mapping
    # We create temporary columns for mapping to ensure case-insensitivity or strip issues don't break lookups
    df['Brand_Clean'] = df['Brand'].astype(str).str.strip()
    df['Model_Clean'] = df['Model'].astype(str).str.strip()

    initial_missing = df['Body Shape'].isna().sum()
    print(f"Initial missing Body Shapes: {initial_missing}")

    # --- Step 1: Fill using Mode (Existing Data) ---
    print("Step 1: Filling from existing data (Mode)...")
    mode_map = df[df['Body Shape'].notna()].groupby(['Brand_Clean', 'Model_Clean'])['Body Shape'].apply(
        lambda x: x.mode()[0] if not x.mode().empty else np.nan
    ).to_dict()
    
    def fill_from_mode(row):
        if pd.isna(row['Body Shape']):
            return mode_map.get((row['Brand_Clean'], row['Model_Clean']), np.nan)
        return row['Body Shape']

    df['Body Shape'] = df.apply(fill_from_mode, axis=1)

    # --- Step 2: Fill using Extended Dictionary ---
    print("Step 2: Filling from Extended Dictionary...")
    
    def fill_from_dict(row):
        if pd.isna(row['Body Shape']):
            # Try exact match
            val = extended_mappings.get((row['Brand_Clean'], row['Model_Clean']))
            if val: return val
            
            # Fallback: Try Capitalized match if original was lowercase/mixed
            val_cap = extended_mappings.get((row['Brand_Clean'], row['Model_Clean'].capitalize()))
            if val_cap: return val_cap
            
            return row['Body Shape']
        return row['Body Shape']

    df['Body Shape'] = df.apply(fill_from_dict, axis=1)

    # Drop temporary columns
    df.drop(columns=['Brand_Clean', 'Model_Clean'], inplace=True)

    # --- Step 3: Save Output & Missing Log ---
    final_missing_count = df['Body Shape'].isna().sum()
    print(f"Finished. Missing values reduced from {initial_missing} to {final_missing_count}")
    
    # Save the main filled dataset
    print(f"Saving filled dataset to: {output_csv_path}")
    df.to_csv(output_csv_path, index=False)

    # Save remaining empty cars to a TXT file (Brand & Model only) if any exist
    if final_missing_count > 0:
        print(f"Saving {final_missing_count} remaining empty rows to: {missing_txt_path}")
        missing_rows = df[df['Body Shape'].isna()][['Brand', 'Model']]
        missing_rows.to_csv(missing_txt_path, sep='\t', index=False)
    else:
        print("Great news! No missing body shapes remain.")

    print("Done.")

# ---------------------------------------------------------
# 3. RUN THE SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    # FILE NAMES
    # Ensure these match your actual file names
    input_filename = 'filled_car_data.csv'       
    output_filename = 'filled_car_data_2.csv' 
    missing_filename = 'remaining_missing_cars_v2.txt' 
    
    process_car_data(input_filename, output_filename, missing_filename)