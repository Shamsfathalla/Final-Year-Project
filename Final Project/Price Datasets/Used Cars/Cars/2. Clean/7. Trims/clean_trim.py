import pandas as pd
import numpy as np
import re
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load the CSV file (from same directory as script)
input_filename = 'filled_car_data_2.csv'
file_path = os.path.join(script_dir, input_filename)
df = pd.read_csv(file_path)

print("=== Before Cleaning ===")
print(f"Total rows: {len(df)}")
print(f"Empty/NaN Trim values: {df['Trim'].isna().sum()}")
print(f"'Unspecified trim' count: {(df['Trim'] == 'Unspecified trim').sum()}")
print(f"'Standard' count: {(df['Trim'] == 'Standard').sum()}")

# =============================================================================
# STEP 1: Initial Cleanup - Strip whitespace and handle NaN
# =============================================================================
df['Trim'] = df['Trim'].astype(str).str.strip()
df['Trim'] = df['Trim'].replace(['nan', '', 'None', 'NaN'], np.nan)

# =============================================================================
# STEP 2: Define patterns to remove and preserve
# =============================================================================

# BMW xDrive/sDrive patterns to preserve (will be extracted and re-added)
bmw_drive_pattern = r'\b([xXsS][Dd]rive\s*\d*[iIdDeE]?)\b'
bmw_m_pattern = r'\b([xXsS][Dd]rive\s*[Mm]\d+[iIdDeE]?)\b'

# Audi TFSI patterns to preserve
audi_tfsi_pattern = r'\b(\d{2}\s*[Tt][Ff][Ss][Ii])\b'

# Performance trim names to preserve
performance_trims = [
    'Competition', 'ZL1', 'Z06', 'ZR1', 'GT', 'GT3', 'GT4', 'RS', 'SS',
    'AMG', 'M Sport', 'M-Sport', 'Msport', 'S-Line', 'S Line', 'Sline',
    'R-Line', 'R Line', 'Veloce', 'Quadrifoglio', 'Nismo', 'TRD', 'Type R',
    'STI', 'WRX', 'Hellcat', 'Demon', 'Trackhawk', 'SRT', 'Shelby',
    'Raptor', 'Lightning', 'SVT', 'ST', 'RS3', 'RS5', 'RS6', 'RS7',
    'M2', 'M3', 'M4', 'M5', 'M8', 'Pro', 'Pro Max', 'Plus', 'Cross',
    'E-Tron', 'Etron', 'Quattro', 'xLine', 'X-Line'
]

def clean_trim_value(trim, brand=None, model=None):
    """Clean a single trim value with comprehensive rules."""
    if pd.isna(trim) or trim in ['nan', '', 'None', 'NaN']:
        return 'Base'
    
    original = str(trim).strip()
    
    # Handle Unspecified and Standard immediately
    if original.lower() in ['unspecified trim', 'unspecified', 'standard', 'undefined', 'underfined']:
        return 'Base'
    
    # =========================================================================
    # EXTRACT patterns to preserve BEFORE removal operations
    # =========================================================================
    preserved_patterns = []
    
    # Extract BMW xDrive/sDrive patterns
    xdrive_matches = re.findall(bmw_drive_pattern, original, flags=re.IGNORECASE)
    preserved_patterns.extend(xdrive_matches)
    
    xdrive_m_matches = re.findall(bmw_m_pattern, original, flags=re.IGNORECASE)
    preserved_patterns.extend(xdrive_m_matches)
    
    # Extract Audi TFSI patterns
    tfsi_matches = re.findall(audi_tfsi_pattern, original, flags=re.IGNORECASE)
    preserved_patterns.extend(tfsi_matches)
    
    # Start with original
    cleaned = original
    
    # =========================================================================
    # REMOVE engine specs (e.g., 1.4 A/T, 2.0 F/O, 1.5 M/T, 3.0 A/T)
    # =========================================================================
    # Remove engine displacement + transmission patterns
    cleaned = re.sub(r'\b\d+\.?\d*\s*[AaMm]/[Tt]\b', '', cleaned)
    cleaned = re.sub(r'\b\d+\.?\d*\s*[Ff]/[Oo]\b', '', cleaned)
    cleaned = re.sub(r'\b\d+\.?\d*\s*[Tt]/[Ll]\b', '', cleaned)
    cleaned = re.sub(r'\b\d+\.?\d*\s*[Hh]/[Ll]\b', '', cleaned)
    cleaned = re.sub(r'\b\d+\.?\d*\s*[Hh]/[Bb]\b', '', cleaned)
    cleaned = re.sub(r'\b\d+\.?\d*\s*[Ss]/[Rr]\b', '', cleaned)
    
    # Remove standalone transmission codes
    cleaned = re.sub(r'\bA/T\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bM/T\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bF/O\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bH/L\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bT/L\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bH/B\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bS/R\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bCVT\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bDCT\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bTDCT\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove transmission words
    cleaned = re.sub(r'\b[Aa]utomatic\b', '', cleaned)
    cleaned = re.sub(r'\b[Aa]utomtic\b', '', cleaned)  # Misspelling
    cleaned = re.sub(r'\b[Aa]utmtic\b', '', cleaned)   # Misspelling
    cleaned = re.sub(r'\bِ?[Aa]utomatic\b', '', cleaned)  # With Arabic char
    cleaned = re.sub(r'\b[Mm]anual‏?\b', '', cleaned)  # With hidden char
    cleaned = re.sub(r'\b[Mm]anual\b', '', cleaned)
    
    # =========================================================================
    # REMOVE horsepower values
    # =========================================================================
    cleaned = re.sub(r'\b\d+\s*[Hh][Pp]\b', '', cleaned)
    cleaned = re.sub(r'\(\s*\d+\s*[Hh][Pp]\s*\)', '', cleaned)
    
    # =========================================================================
    # REMOVE engine capacity patterns
    # =========================================================================
    # Remove L/T capacity (1.0L, 2.0T, 1.5L, etc.) but preserve before removing
    cleaned = re.sub(r'\b\d+\.?\d*\s*[LlTt]\b', '', cleaned)
    
    # Remove CC values (1600cc, 2000 cc)
    cleaned = re.sub(r'\b\d+\s*[Cc][Cc]\b', '', cleaned)
    
    # Remove valve patterns (16v, 8v, 24v, etc.)
    cleaned = re.sub(r'\b\d+[Vv]\b', '', cleaned)
    
    # Remove V-engine types (V6, V8, V12) - but not in names like "V3", "V5" for Brilliance
    if brand and brand.lower() not in ['brilliance']:
        cleaned = re.sub(r'\bV\d+\b', '', cleaned, flags=re.IGNORECASE)
    
    # =========================================================================
    # REMOVE brackets and their contents
    # =========================================================================
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    
    # =========================================================================
    # REMOVE model numbers/names that appear in trims
    # =========================================================================
    # BMW model numbers (320i, 520i, 118i, etc.) - but preserve as separate trim if it's the only thing
    if brand and brand.lower() == 'bmw':
        cleaned = re.sub(r'\b(BMW\s+)?[Xx][1-7]\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bSeries\s*\d\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b\d\s*[Ss]eries\b', '', cleaned)
    
    # Audi model numbers (A3, A4, Q3, Q7, etc.)
    if brand and brand.lower() == 'audi':
        cleaned = re.sub(r'\b[AaQqSsRr][1-8]\b', '', cleaned)
        cleaned = re.sub(r'\bRS[QE]?\d\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove model name from trim (e.g., "Grand Cherokee" in trim for Jeep Grand Cherokee)
    if model:
        # Handle model names with spaces (e.g., "Grand Cherokee", "X-Trail")
        model_pattern = r'\b' + re.escape(str(model)) + r'\b'
        cleaned = re.sub(model_pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Also handle model name parts separately (e.g., "Tiggo7" -> remove "Tiggo")
        model_parts = str(model).replace('-', ' ').replace('_', ' ').split()
        for part in model_parts:
            if len(part) > 2:  # Only remove parts longer than 2 chars
                cleaned = re.sub(r'\b' + re.escape(part) + r'\d*\b', '', cleaned, flags=re.IGNORECASE)
    
    # =========================================================================
    # REMOVE body type references
    # =========================================================================
    body_types = [
        'Sedan', 'Coupe', 'Hatchback', 'HB', 'SUV', 'Crossover', 'Wagon',
        'Estate', 'Convertible', 'Cabriolet', 'Roadster', 'Van', 'Pickup',
        'Truck', 'Gran Coupe', 'GC', 'Grand Coupe', 'Sportback', 'Sport Back',
        'Active Tourer', 'Gran Turismo', 'Station Wagon', 'SW', 'Door', 'Doors',
        '4D', '5D', '2D', '4 Door', '5 Door', '2 Door'
    ]
    for body in body_types:
        cleaned = re.sub(r'\b' + re.escape(body) + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    # =========================================================================
    # REMOVE brand names if they appear in trim
    # =========================================================================
    brands_to_remove = [
        'Alfa Romeo', 'Aston Martin', 'Audi', 'Bentley', 'BMW', 'Brilliance',
        'BYD', 'Cadillac', 'Changan', 'Chery', 'Chevrolet', 'Chrysler', 'Citroen',
        'Daihatsu', 'Dodge', 'DS', 'Fiat', 'Ford', 'GAC', 'Geely', 'GMC', 'Haval',
        'Honda', 'Hyundai', 'Infiniti', 'Isuzu', 'Jaguar', 'Jeep', 'Jetour', 'Kia',
        'Lada', 'Lamborghini', 'Land Rover', 'Range Rover', 'Lexus', 'Lincoln',
        'Maserati', 'Mazda', 'McLaren', 'Mercedes', 'Mercedes-Benz', 'Benz', 'MG',
        'Mini', 'Mitsubishi', 'Nissan', 'Opel', 'Peugeot', 'Porsche', 'Proton',
        'Renault', 'Rolls Royce', 'Saab', 'Seat', 'Skoda', 'Smart', 'Ssangyong',
        'Subaru', 'Suzuki', 'Tesla', 'Toyota', 'Volkswagen', 'VW', 'Volvo'
    ]
    for brand_name in brands_to_remove:
        cleaned = re.sub(r'\b' + re.escape(brand_name) + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    # =========================================================================
    # REMOVE common model names that appear in trims
    # =========================================================================
    common_models = [
        # Chery models
        'Tiggo', 'Arrizo', 'Envy',
        # Jeep models  
        'Grand Cherokee', 'Cherokee', 'Wrangler', 'Renegade', 'Compass', 'Liberty',
        # Mitsubishi models
        'Lancer', 'Pajero', 'Eclipse', 'Outlander', 'Xpander', 'Attrage', 'Mirage',
        # Nissan models
        'Sunny', 'Sentra', 'Qashqai', 'Juke', 'X-Trail', 'Tiida', 'Kicks', 'Pathfinder',
        # Hyundai models
        'Elantra', 'Tucson', 'Accent', 'Sonata', 'Creta', 'Santa Fe', 'i10', 'i20', 'i30',
        # Toyota models
        'Corolla', 'Camry', 'Yaris', 'RAV4', 'Hilux', 'Fortuner', 'Land Cruiser',
        # Honda models
        'Civic', 'Accord', 'City', 'CR-V', 'HR-V', 'Jazz', 'Fit',
        # Kia models
        'Cerato', 'Sportage', 'Sorento', 'Rio', 'Picanto', 'Carens', 'Ceed', 'Soul', 'XCeed',
        # Geely models
        'Emgrand', 'Coolray', 'Okavango', 'Pandino', 'Starray',
        # Fiat models
        'Tipo', 'Punto', 'Panda', 'Uno', '500', '128', '127', 'Siena', 'Tempra',
        # Opel models
        'Astra', 'Corsa', 'Insignia', 'Mokka', 'Crossland', 'Grandland', 'Vectra',
        # Peugeot models
        '208', '308', '408', '508', '2008', '3008', '5008',
        # BMW model codes
        '116i', '118i', '218i', '316i', '318i', '320i', '328i', '330i', '340i',
        '418i', '420i', '430i', '520i', '523i', '525i', '528i', '530i', '535i',
        '640i', '730i', '740i', '750i', 'M850i',
        # Mercedes model codes
        'C200', 'C250', 'C300', 'E200', 'E250', 'E300', 'E350', 'S350', 'S400', 'S500',
        'GLA200', 'GLC200', 'GLC300', 'GLE350', 'GLS450',
        # BYD models
        'Atto', 'Seal', 'Song', 'Tang', 'Yuan', 'Qin', 'Seagull',
        # Changan models
        'Alsvin', 'Eado', 'CS35', 'CS55', 'CS75', 'CS85', 'UNI-T',
        # Jetour models  
        'X70', 'X70S', 'X95', 'Dashing',
        # Other common ones
        "Cee'd", 'Rio', 'Sportback', 'Classic', 'Cross'
    ]
    for model_name in common_models:
        cleaned = re.sub(r'\b' + re.escape(model_name) + r'\b', '', cleaned, flags=re.IGNORECASE)
    
    # =========================================================================
    # REMOVE misc patterns
    # =========================================================================
    # Remove "full option" and variations
    cleaned = re.sub(r'\bfull\s*option\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bF/O\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove standalone numbers (but not in patterns like "40i")
    cleaned = re.sub(r'\b\d+\b', '', cleaned)
    
    # Remove "with" phrases
    cleaned = re.sub(r'\bwith\s+\w+\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bw/\w+\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove "New Shape", "Old Shape", "Facelift", "FL", "LCI"
    cleaned = re.sub(r'\b(New|Old)\s*Shape\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bFacelift\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bFL\b', '', cleaned)
    cleaned = re.sub(r'\bLCI\b', '', cleaned)
    cleaned = re.sub(r'\bCKD\b', '', cleaned)
    
    # Remove category references
    cleaned = re.sub(r'\b\d+(st|nd|rd|th)\s*Category\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove drive train patterns (2WD, 4WD, AWD, FWD, RWD, 4X4, 4X2)
    cleaned = re.sub(r'\b[24]\s*[Ww][Dd]\b', '', cleaned)
    cleaned = re.sub(r'\b[Aa][Ww][Dd]\b', '', cleaned)
    cleaned = re.sub(r'\b[Ff][Ww][Dd]\b', '', cleaned)
    cleaned = re.sub(r'\b[Rr][Ww][Dd]\b', '', cleaned)
    cleaned = re.sub(r'\b4[Xx][24]\b', '', cleaned)
    
    # Remove ordinal patterns (1st, 2nd, 3rd, 4th, etc.) when standalone
    cleaned = re.sub(r'\b\d+(st|nd|rd|th)\b', '', cleaned, flags=re.IGNORECASE)
    
    # =========================================================================
    # REMOVE random symbols and special characters
    # =========================================================================
    # Remove slashes at word boundaries
    cleaned = re.sub(r'\s*/\s*', ' ', cleaned)
    
    # Remove other special characters (keep letters, numbers, spaces, hyphens)
    cleaned = re.sub(r'[^\w\s\-]', '', cleaned)
    
    # Remove standalone single characters
    cleaned = re.sub(r'\b[a-zA-Z]\b', '', cleaned)
    
    # =========================================================================
    # ADD BACK preserved patterns
    # =========================================================================
    if preserved_patterns:
        # Standardize xDrive patterns
        standardized = []
        for p in preserved_patterns:
            # Standardize BMW xDrive/sDrive
            p_clean = re.sub(r'^[xX]', 'x', p)
            p_clean = re.sub(r'^[sS]', 's', p_clean)
            p_clean = re.sub(r'[Dd]rive', 'Drive', p_clean)
            p_clean = re.sub(r'[Mm](\d+)', r'M\1', p_clean)
            p_clean = re.sub(r'(\d+)[iI]$', r'\1i', p_clean)
            p_clean = re.sub(r'(\d+)[dD]$', r'\1d', p_clean)
            p_clean = re.sub(r'(\d+)[eE]$', r'\1e', p_clean)
            # Standardize TFSI
            p_clean = re.sub(r'[Tt][Ff][Ss][Ii]', 'TFSI', p_clean)
            standardized.append(p_clean)
        
        preserved_str = ' '.join(set(standardized))
        cleaned = (cleaned + ' ' + preserved_str).strip()
    
    # =========================================================================
    # FINAL CLEANUP
    # =========================================================================
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Remove leading/trailing hyphens
    cleaned = cleaned.strip('-').strip()
    
    # Remove duplicate words (e.g., "Luxury Luxury" -> "Luxury")
    words = cleaned.split()
    seen = set()
    unique_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in seen:
            seen.add(word_lower)
            unique_words.append(word)
    cleaned = ' '.join(unique_words)
    
    # If empty after all cleaning, return Base
    if not cleaned or cleaned.lower() in ['base', '']:
        return 'Base'
    
    return cleaned

# =============================================================================
# STEP 3: Apply cleaning function with brand context
# =============================================================================
def apply_clean_with_context(row):
    return clean_trim_value(row['Trim'], row.get('Brand'), row.get('Model'))

df['Trim'] = df.apply(apply_clean_with_context, axis=1)

# =============================================================================
# STEP 4: Fix common misspellings and standardize names
# =============================================================================
trim_mapping = {
    # Misspellings
    'Spirit': 'Sport',
    'Sprit': 'Sport',
    'Spoort': 'Sport',
    'Sprt': 'Sport',
    'Luxry': 'Luxury',
    'Luxuary': 'Luxury',
    'Premum': 'Premium',
    'Premiun': 'Premium',
    'Comfrt': 'Comfort',
    'Dynamc': 'Dynamic',
    'Exclsive': 'Exclusive',
    'Exclusve': 'Exclusive',
    'Elegnce': 'Elegance',
    'Elegence': 'Elegance',
    'Signatre': 'Signature',
    'Signture': 'Signature',
    'Avantgard': 'Avantgarde',
    'Ambiton': 'Ambition',
    'Alure': 'Allure',
    'Allur': 'Allure',
    'Titanim': 'Titanium',
    'Titanum': 'Titanium',
    'Platnum': 'Platinum',
    'Platinium': 'Platinum',
    
    # S-Line standardization
    'Sline': 'S-Line',
    'S Line': 'S-Line',
    'S-line': 'S-Line',
    's-line': 'S-Line',
    'Sline Plus': 'S-Line Plus',
    'S Line Plus': 'S-Line Plus',
    
    # M-Sport standardization
    'Msport': 'M Sport',
    'M-sport': 'M Sport',
    'M-Sport': 'M Sport',
    
    # X-Line standardization
    'Xline': 'X-Line',
    'X line': 'X-Line',
    'X Line': 'X-Line',
    
    # R-Line standardization
    'Rline': 'R-Line',
    'R line': 'R-Line',
    'R Line': 'R-Line',
    
    # GT-Line standardization
    'Gtline': 'GT-Line',
    'Gt-line': 'GT-Line',
    'GT line': 'GT-Line',
    'GT Line': 'GT-Line',
    'Gt Line': 'GT-Line',
    
    # E-Tron standardization
    'Etron': 'E-Tron',
    'E Tron': 'E-Tron',
    'E-tron': 'E-Tron',
    
    # Line variations
    'High Line': 'Highline',
    'High-Line': 'Highline',
    'High-line': 'Highline',
    'Top Line': 'Topline',
    'Top-Line': 'Topline',
    'Top-line': 'Topline',
    'Base Line': 'Baseline',
    'Base-Line': 'Baseline',
    'Base-line': 'Baseline',
    'Mid Line': 'Midline',
    'Mid-Line': 'Midline',
    'Mid-line': 'Midline',
    
    # Standard -> Base
    'Standard': 'Base',
    'Basic': 'Base',
}

# Apply mapping
for old, new in trim_mapping.items():
    df['Trim'] = df['Trim'].str.replace(r'\b' + re.escape(old) + r'\b', new, flags=re.IGNORECASE, regex=True)

# =============================================================================
# STEP 5: Title Case standardization (with exceptions)
# =============================================================================
def standardize_case(trim):
    if pd.isna(trim):
        return 'Base'
    
    trim = str(trim).strip()
    if not trim:
        return 'Base'
    
    # Words that should stay uppercase
    uppercase_words = ['TFSI', 'GT', 'AWD', 'FWD', 'RWD', '4WD', '2WD', 'EV', 'HEV', 
                       'PHEV', 'GLS', 'GLX', 'GLE', 'GLI', 'GTI', 'GDI', 'MPI', 
                       'SV', 'LX', 'EX', 'DX', 'SE', 'LE', 'XLE', 'SR', 'SL']
    
    # Words that should have specific casing
    special_case = {
        'xdrive': 'xDrive',
        'sdrive': 'sDrive',
        'e-tron': 'E-Tron',
        's-line': 'S-Line',
        'm sport': 'M Sport',
        'x-line': 'X-Line',
        'r-line': 'R-Line',
        'gt-line': 'GT-Line',
    }
    
    # Apply title case first
    result = trim.title()
    
    # Fix uppercase words
    for word in uppercase_words:
        result = re.sub(r'\b' + word.title() + r'\b', word, result)
    
    # Fix special case words
    for old, new in special_case.items():
        result = re.sub(r'\b' + re.escape(old) + r'\b', new, result, flags=re.IGNORECASE)
    
    # Fix BMW xDrive/sDrive patterns
    result = re.sub(r'\bXdrive', 'xDrive', result)
    result = re.sub(r'\bSdrive', 'sDrive', result)
    
    return result

df['Trim'] = df['Trim'].apply(standardize_case)

# =============================================================================
# STEP 6: Final cleanup and fill remaining empty values
# =============================================================================
df['Trim'] = df['Trim'].str.strip()
df['Trim'] = df['Trim'].replace(['', 'nan', 'None', 'NaN'], 'Base')
df['Trim'] = df['Trim'].fillna('Base')

# Clean up any double spaces that may have formed
df['Trim'] = df['Trim'].str.replace(r'\s+', ' ', regex=True)

# =============================================================================
# STEP 7: Print results and save
# =============================================================================
print("\n=== After Cleaning ===")
print(f"Total rows: {len(df)}")
print(f"Empty/NaN Trim values: {df['Trim'].isna().sum()}")
print(f"'Base' count: {(df['Trim'] == 'Base').sum()}")
print(f"Unique trim count: {df['Trim'].nunique()}")

print("\n=== Top 40 Most Common Trims ===")
print(df['Trim'].value_counts().head(40))

# Save the cleaned file
output_filename = 'cleaned_cars_v3.csv'
output_path = os.path.join(script_dir, output_filename)
df.to_csv(output_path, index=False)

print(f"\n✓ Cleaned file saved to: {output_path}")

# =============================================================================
# STEP 8: Generate sample transformations for validation
# =============================================================================
print("\n=== Sample Transformations (for validation) ===")
# Load original to compare
original_df = pd.read_csv(file_path)
comparison = pd.DataFrame({
    'Original': original_df['Trim'].head(50),
    'Cleaned': df['Trim'].head(50)
})
# Show only rows where there was a change
changed = comparison[comparison['Original'] != comparison['Cleaned']]
print(changed.head(30).to_string())
