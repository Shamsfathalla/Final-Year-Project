import os
import pandas as pd
import shutil

# Configuration
csv_path = r"new_cars.csv"
images_dir = r"images"
DRY_RUN = False  # Set to False to actually delete folders

# Read CSV
if not os.path.exists(csv_path):
    print(f"Error: CSV file not found at {csv_path}")
    exit(1)

df = pd.read_csv(csv_path)

# Collect referenced folders (case-insensitive for comparison)
referenced_folders = set()
for paths in df['Image_Paths'].dropna():
    for path in str(paths).split(';'):
        path = path.strip().replace("\\", "/") # Normalize separators
        if path.startswith("images/"):
            # Extract folder name: images/Folder Name/img.jpg -> Folder Name
            parts = path[len("images/"):].strip("/").split('/')
            if parts:
                folder_name = parts[0]
                referenced_folders.add(folder_name.lower())

print(f"Total entries in CSV: {len(df)}")
print(f"Unique referenced folders in CSV: {len(referenced_folders)}")

# List all folders in images directory
if not os.path.exists(images_dir):
    print(f"Error: Images directory not found at {images_dir}")
    exit(1)

all_folders = [f for f in os.listdir(images_dir) if os.path.isdir(os.path.join(images_dir, f))]
print(f"Total folders found on disk: {len(all_folders)}")

# Delete folders not referenced
deleted_count = 0
for folder in all_folders:
    if folder.lower() not in referenced_folders:
        folder_path = os.path.join(images_dir, folder)
        if DRY_RUN:
            print(f"[DRY RUN] Would delete: {folder_path}")
        else:
            print(f"Deleting: {folder_path}")
            shutil.rmtree(folder_path)
        deleted_count += 1

if deleted_count == 0:
    print("No redundant folders found to delete.")
elif DRY_RUN:
    print(f"Dry run complete. {deleted_count} folders would be deleted.")
else:
    print(f"Cleanup complete. {deleted_count} folders deleted.")

# After removal, check for missing folders
missing_cars = []
for idx, row in df.iterrows():
    found = False
    paths = str(row['Image_Paths']).split(';')
    for path in paths:
        path = path.strip().replace("\\", "/")
        if path.startswith("images/"):
            parts = path[len("images/"):].strip("/").split('/')
            if parts:
                folder = parts[0]
                folder_path = os.path.join(images_dir, folder)
                if os.path.isdir(folder_path):
                    found = True
                    break
    if not found:
        car_info = f"{row['Brand']} {row['Model']} {row['Year']} {row.get('Trim', '')}"
        missing_cars.append(car_info)

if missing_cars:
    print(f"\nAlert: {len(missing_cars)} entries have NO image folder on disk:")
    for car in missing_cars[:10]: # Limit output
        print(f" - {car}")
    if len(missing_cars) > 10:
        print(f" ... and {len(missing_cars) - 10} more.")
else:
    print("\nVerification successful: All CSV entries have their image folder on disk.")
