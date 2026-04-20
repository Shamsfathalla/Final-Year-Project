import csv
import os
import shutil
from pathlib import Path


def consolidate_images(csv_path, output_csv, output_folder='Used_Images'):
    """
    Copy all unique image folders to a single folder and update CSV paths.
    
    Args:
        csv_path: Path to the original CSV file
        output_csv: Path for the output CSV with updated paths
        output_folder: Name of the folder to consolidate images into
    """
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Track copied folders to avoid duplicates
    copied_folders = {}  # old_path -> new_folder_name
    
    # Read CSV and process
    rows = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row_idx, row in enumerate(reader):
            image_paths_str = row.get('Image Paths', '')
            
            if image_paths_str:
                paths = [p.strip() for p in image_paths_str.split(';') if p.strip()]
                new_paths = []
                
                for img_path in paths:
                    old_folder = os.path.dirname(img_path)
                    img_filename = os.path.basename(img_path)
                    
                    # Check if we already copied this folder
                    if old_folder not in copied_folders:
                        # Check if source exists
                        if not os.path.exists(old_folder):
                            continue
                        
                        # Create new folder name (just use the folder basename)
                        new_folder_name = os.path.basename(old_folder)
                        
                        # Handle naming conflicts by adding suffix
                        base_name = new_folder_name
                        counter = 1
                        while new_folder_name in copied_folders.values():
                            new_folder_name = f"{base_name}_{counter}"
                            counter += 1
                        
                        copied_folders[old_folder] = new_folder_name
                        
                        # Copy the folder
                        dst_folder = os.path.join(output_folder, new_folder_name)
                        if not os.path.exists(dst_folder):
                            shutil.copytree(old_folder, dst_folder)
                            print(f"Copied: {old_folder} -> {dst_folder}")
                    
                    # Build new path
                    if old_folder in copied_folders:
                        new_folder_name = copied_folders[old_folder]
                        new_path = os.path.join(output_folder, new_folder_name, img_filename)
                        new_paths.append(new_path)
                
                row['Image Paths'] = '; '.join(new_paths)
            
            rows.append(row)
            
            if (row_idx + 1) % 1000 == 0:
                print(f"Processed {row_idx + 1} rows...")
    
    # Write CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nDone!")
    print(f"Copied {len(copied_folders)} unique folders to '{output_folder}'")
    print(f"Updated CSV saved to: {output_csv}")


if __name__ == '__main__':
    csv_path = 'Used_Cars_Egypt.csv'
    output_csv = 'Final_Used_Cars_Egypt.csv'
    output_folder = 'Used_Images'
    
    consolidate_images(csv_path, output_csv, output_folder)
