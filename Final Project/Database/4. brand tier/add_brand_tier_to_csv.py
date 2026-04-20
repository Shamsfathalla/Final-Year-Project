import csv

BRAND_TIER ={
    # Tier 1: Exotic
    "Ferrari": "Exotic", "Lamborghini": "Exotic", "Bentley": "Exotic", "Rolls-Royce": "Exotic", "Aston Martin": "Exotic",
    "McLaren": "Exotic", "Bugatti": "Exotic", "Maserati": "Exotic", "Lotus": "Exotic", "Caterham": "Exotic",
    
    # Tier 2: Luxury
    "Mercedes-Benz": "Luxury", "Mercedes": "Luxury", "BMW": "Luxury", "Audi": "Luxury", "Porsche": "Luxury", "Lexus": "Luxury",
    "Land Rover": "Luxury", "Range Rover": "Luxury", "Jaguar": "Luxury", "Volvo": "Luxury", "Polestar": "Luxury", "Cadillac": "Luxury", "Lincoln": "Luxury", "Infiniti": "Luxury",
    "Genesis": "Luxury", "Tesla": "Luxury", "Alfa Romeo": "Luxury", "Hummer": "Luxury", "Avatr": "Luxury", "Im Motors": "Luxury", "IM Motors": "Luxury", "Hongqi": "Luxury", 
    "M-Hero": "Luxury", "Voyah": "Luxury", "Zeekr": "Luxury",
    
    # Tier 3: Premium
    "Toyota": "Premium", "Honda": "Premium", "Hyundai": "Premium", "Kia": "Premium", "Mazda": "Premium", "DS": "Premium", "Volkswagen": "Premium",
    "Nissan": "Premium", "Mitsubishi": "Premium", "Ford": "Premium", "Chevrolet": "Premium", "Jeep": "Premium", "Peugeot": "Premium",
    "Citroen": "Premium", "Renault": "Premium", "Opel": "Premium", "Skoda": "Premium", "Seat": "Premium", "Subaru": "Premium", "Mini": "Premium",
    "Cupra": "Premium", "Dodge": "Premium", "Chrysler": "Premium", "Buick": "Premium", "GMC": "Premium", "MG": "Premium", "BYD": "Premium",
    "Geely": "Premium", "Chery": "Premium", "EXEED": "Premium", "Haval": "Premium", "Jetour": "Premium", "GAC": "Premium", "KGM": "Premium",
    "SsangYong": "Premium", "Arcfox": "Premium", "Li Auto": "Premium", "Lynk & co": "Premium", "Rox": "Premium", "Smart": "Premium", 
    "Xpeng": "Premium", "Xiaomi": "Premium",
    
    # Tier 4: Economy
    "Suzuki": "Economy", "Fiat": "Economy", "Lada": "Economy", "Daewoo": "Economy", "Daihatsu": "Economy", "Proton": "Economy",
    "Speranza": "Economy", "Changan": "Economy", "Chana": "Economy", "Changhe": "Economy", "JAC": "Economy", "BAIC": "Economy",
    "Brilliance": "Economy", "Great Wall": "Economy", "Lifan": "Economy", "DFSK": "Economy", "Dongfeng": "Economy", "Faw": "Economy",
    "Foton": "Economy", "Hafei": "Economy", "Haima": "Economy", "Hanteng": "Economy", "Havi": "Economy", "Hawtai": "Economy", "Isuzu": "Economy",
    "JMC": "Economy", "Kaiyi": "Economy", "Karry": "Economy", "Kenbo": "Economy", "Keyton": "Economy", "Kinglong": "Economy", "Lancia": "Economy",
    "Mahindra": "Economy", "Forthing": "Economy", "Canghe": "Economy", "Domy": "Economy", "Bestune": "Economy", "Deepal": "Economy", 
    "Soueast": "Economy", "VGV": "Economy", "Zotye": "Economy", "Nasr": "Economy", "Saipa": "Economy", "Senova": "Economy", 
    "Tata": "Economy", "Wuling": "Economy"
}


# Update merged_cars.csv: clear 'brand tier' column and fill it again
import pandas as pd

# Read the merged_cars.csv file
df = pd.read_csv('merged_cars.csv')

# Clear the 'brand tier' column
df['brand tier'] = ''

# Fill the 'brand tier' column based on BRAND_TIER mapping
df['brand tier'] = df['brand'].map(BRAND_TIER).fillna('')

# Save the updated DataFrame back to merged_cars.csv
df.to_csv('merged_cars.csv', index=False)