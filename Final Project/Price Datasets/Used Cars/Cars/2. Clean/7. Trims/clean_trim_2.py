import pandas as pd
import re

# Read the TSV file
df = pd.read_csv('cleaned_cars_v3.csv')

def clean_trim(trim):
    if pd.isna(trim):
        return 'Base'
    
    trim = str(trim).strip()
    
    # Remove "Cooper" from trim (Mini models)
    trim = re.sub(r'\bCooper\b\s*', '', trim, flags=re.IGNORECASE)
    
    # Remove Audi model codes from trim
    audi_models = [
        r'\bA[1-8]\b', r'\bQ[2-8]\b', r'\bRS[3-7]?\b', r'\bTT\b', r'\bR8\b',
        r'\bS[1-8]\b', r'\bE-Tron\b', r'\bAllroad\b'
    ]
    for pattern in audi_models:
        trim = re.sub(pattern, '', trim, flags=re.IGNORECASE)
    
    # Remove noise terms
    noise_terms = [
        r'\bGLS\b',
        r'\bIm motors?\b',
        r'\bImported\b',
        r'\bId\b',
    ]
    for pattern in noise_terms:
        trim = re.sub(pattern, '', trim, flags=re.IGNORECASE)
    
    # Normalize hyphens - remove standalone hyphens and normalize spacing around them
    # First, replace " - " or " -" or "- " with just "-" 
    trim = re.sub(r'\s*-\s*', '-', trim)
    # Remove leading/trailing hyphens
    trim = re.sub(r'^-+|-+$', '', trim)
    # Remove standalone hyphens that are alone
    trim = re.sub(r'\s+-\s+', ' ', trim)
    
    # Fix typos
    typo_fixes = {
        'Premire': 'Premier',
        'Confort': 'Comfort',
        'Eagel': 'Eagle',
        'Emegrand': 'Emgrand',
        'Ecooboost': 'Ecoboost',
        'Atoumatic': 'Automatic',
    }
    for typo, fix in typo_fixes.items():
        trim = trim.replace(typo, fix)
    
    # Normalize BMW drive variants (remove spaces)
    drive_patterns = [
        (r'sDrive (\d+I)', r'sDrive\1'),
        (r'xDrive (\d+I)', r'xDrive\1'),
        (r'xDrive(\d+)I', r'xDrive\1I'),  # Standardize case
    ]
    for pattern, replacement in drive_patterns:
        trim = re.sub(pattern, replacement, trim, flags=re.IGNORECASE)
    
    # Normalize xDrive/sDrive capitalization
    trim = re.sub(r'\bsdrive', 'sDrive', trim, flags=re.IGNORECASE)
    trim = re.sub(r'\bxdrive', 'xDrive', trim, flags=re.IGNORECASE)
    
    # Combine Gran/Grand variants
    trim = re.sub(r'\bGrand\b', 'Gran', trim)
    
    # Normalize TFSI patterns
    trim = re.sub(r'TFSI -Line', 'TFSI S-Line', trim)
    trim = re.sub(r'TFSI Sport -Line', 'TFSI Sport S-Line', trim)
    
    # Standardize case for specific trims
    case_fixes = {
        r'\bAx\b': 'AX',
        r'\bi3\b': 'I3',
        r'\bi4\b': 'I4',
        r'\bi5\b': 'I5',
        r'\bi7\b': 'I7',
        r'\bi8\b': 'I8',
        r'\biX\b': 'IX',
        r'\bIx\b': 'IX',
        r'\bx1\b': 'X1',
        r'\bx2\b': 'X2',
        r'\bx3\b': 'X3',
        r'\bx4\b': 'X4',
        r'\bx5\b': 'X5',
        r'\bx6\b': 'X6',
        r'\bx7\b': 'X7',
    }
    for pattern, fix in case_fixes.items():
        trim = re.sub(pattern, fix, trim)
    
    # Fix "128 nova" -> "128 Nova"
    trim = re.sub(r'128 nova', '128 Nova', trim, flags=re.IGNORECASE)
    
    # Standardize Line variants
    trim = re.sub(r'\bLine Plus\b', 'S-Line Plus', trim)
    trim = re.sub(r'^Line$', 'S-Line', trim)
    
    # Combine similar highline/baseline patterns
    trim = re.sub(r'\bAt Baseline\b', 'AT Baseline', trim)
    trim = re.sub(r'\bAt Highline\b', 'AT Highline', trim)
    
    # Standardize Ls/Lt/Lx variants to uppercase
    trim = re.sub(r'\bLs\b', 'LS', trim)
    trim = re.sub(r'\bLt\b', 'LT', trim)
    trim = re.sub(r'\bLx\b', 'LX', trim)
    trim = re.sub(r'\bLtz\b', 'LTZ', trim)
    trim = re.sub(r'\bLxi\b', 'LXI', trim)
    
    # Standardize SS/EV/EX
    trim = re.sub(r'\bSs\b', 'SS', trim)
    trim = re.sub(r'\bEv\b', 'EV', trim)
    trim = re.sub(r'\bEx\b', 'EX', trim)
    
    # Standardize Zl1/At4 etc
    trim = re.sub(r'\bZl1\b', 'ZL1', trim)
    trim = re.sub(r'\bAt4\b', 'AT4', trim)
    trim = re.sub(r'\bSt\b', 'ST', trim)
    
    # Normalize GLI/GLX/GLS
    trim = re.sub(r'\bGli\b', 'GLI', trim)
    trim = re.sub(r'\bGlx\b', 'GLX', trim)
    trim = re.sub(r'\bGls\b', 'GLS', trim)
    trim = re.sub(r'\bGlxi\b', 'GLXI', trim)
    trim = re.sub(r'\bGsi\b', 'GSI', trim)
    trim = re.sub(r'\bGs\b', 'GS', trim)
    trim = re.sub(r'\bGl\b', 'GL', trim)
    trim = re.sub(r'\bGb\b', 'GB', trim)
    trim = re.sub(r'\bGe\b', 'GE', trim)
    trim = re.sub(r'\bGf\b', 'GF', trim)
    
    # Standardize Dct/Drs
    trim = re.sub(r'(\d)Dct\b', r'\1DCT', trim)
    trim = re.sub(r'(\d)Drs\b', r'\1DRS', trim)
    
    # Standardize kWh
    trim = re.sub(r'\bKwh\b', 'kWh', trim)
    
    # Clean up multiple spaces
    trim = re.sub(r'\s+', ' ', trim).strip()
    
    # Remove orphaned numbers at start (from removed model codes like "40I xDrive" -> "xDrive")
    trim = re.sub(r'^\d+I?\s+', '', trim)
    
    # Remove "Inch" suffix (leftover noise)
    trim = re.sub(r'-?Inch$', '', trim)
    
    # Merge similar trim variations
    trim_merges = {
        # Spelling variations
        r'\bAccenta\b': 'Acenta',
        r'\bAccent\b': 'Acenta',
        r'\bAttractionn\b': 'Attraction',
        
        # Sport Line variants -> Sport-Line
        r'\bSport Line\b': 'Sport-Line',
        r'\bSport-line\b': 'Sport-Line',
        r'\bSportLine\b': 'Sport-Line',
        
        # X-Line variants
        r'\bX Line\b': 'X-Line',
        r'\bXLine\b': 'X-Line',
        
        # Luxury Line variants
        r'\bLuxury Line\b': 'Luxury-Line',
        r'\bLuxuryLine\b': 'Luxury-Line',
        
        # M Sport variants
        r'\bM Sport\b': 'M-Sport',
        r'\bMSport\b': 'M-Sport',
        
        # At -> AT prefix standardization
        r'^At\s+': 'AT ',
        
        # Active variants
        r'\bActive At\b': 'Active AT',
        r'\bActive Gl\b': 'Active GL',
        
        # Allure variants
        r'\bAllure At\b': 'Allure AT',
        
        # Remove "Base" if combined with other words
        r'\bBase Mid\b': 'Mid',
        r'\bMid Base\b': 'Mid',
    }
    for pattern, replacement in trim_merges.items():
        trim = re.sub(pattern, replacement, trim, flags=re.IGNORECASE)
    
    # Final cleanup
    trim = re.sub(r'\s+', ' ', trim).strip()
    trim = re.sub(r'^-+|-+$', '', trim).strip()
    
    return trim if trim else 'Base'

# Apply cleaning
df['Trim'] = df['Trim'].apply(clean_trim)

# Remove duplicates after cleaning
df_cleaned = df.drop_duplicates()

# Save to new file
df_cleaned.to_csv('cleaned_cars_v4.csv', index=False)

original_df = pd.read_csv('cleaned_cars_v3.csv')
print(f"Original rows: {len(original_df)}")
print(f"Cleaned rows: {len(df_cleaned)}")
print(f"Saved to: cleaned_cars_v4.csv")

# Show sample of changes
print("\nUnique trims after cleaning:")
print(sorted(df_cleaned['Trim'].unique())[:50])
