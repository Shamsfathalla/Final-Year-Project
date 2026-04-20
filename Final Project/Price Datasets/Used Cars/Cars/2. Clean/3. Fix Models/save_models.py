import csv
import os

# --- CONFIGURATION ---
INPUT_FILE = "unique_models.txt"
OUTPUT_FILE = "formatted_cars.csv"

# List of brands that have 2+ words to prevent them being split incorrectly
# (e.g. preventing "Land" -> Brand, "Rover" -> Model)
MULTI_WORD_BRANDS = [
    "Alfa Romeo", "Aston Martin", "Great Wall", "Land Rover", 
    "Range Rover", "Rolls-Royce", "Mercedes-Benz", "Dongfeng Venucia",
    "Im Motors", "KGM", "MG", "BYD", "GAC", "JAC", "JMC", "VGV", "DFSK"
]

def parse_line(line):
    line = line.strip()
    if not line:
        return None

    # 1. Extract Year (Always the last element)
    try:
        remainder, year = line.rsplit(' ', 1)
    except ValueError:
        return None  # Line didn't have a space/year

    # 2. Extract Brand and Model
    brand = ""
    model = ""
    
    # Check if the line starts with any of our special multi-word brands
    found_multi = False
    for mb in MULTI_WORD_BRANDS:
        # Check case-insensitive to be safe
        if remainder.lower().startswith(mb.lower()):
            brand = mb # Use the clean capitalization
            # Slice off the brand name from the start
            model = remainder[len(mb):].strip()
            found_multi = True
            break
            
    # If not a multi-word brand, just split by the first space
    if not found_multi:
        parts = remainder.split(' ', 1)
        brand = parts[0]
        # If there is a model part, use it; otherwise model is empty
        model = parts[1] if len(parts) > 1 else ""

    return {"Brand": brand, "Model": model, "Year": year}

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Could not find '{INPUT_FILE}'. Please create this file first.")
        return

    print(f"📂 Reading from {INPUT_FILE}...")
    
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f_out:
        
        writer = csv.DictWriter(f_out, fieldnames=["Brand", "Model", "Year"])
        writer.writeheader()
        
        for line in f_in:
            parsed_data = parse_line(line)
            if parsed_data:
                writer.writerow(parsed_data)
                count += 1
                
    print(f"✅ Success! Processed {count} cars.")
    print(f"📄 Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()