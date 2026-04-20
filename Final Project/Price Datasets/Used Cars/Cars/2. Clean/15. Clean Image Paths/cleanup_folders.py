"""
Find folders from original source directories that weren't copied to Used_Images.
"""
import csv
import os
import shutil


def find_unused_folders(csv_path, source_folders, used_folder='Used_Images', unused_folder='Unused_Images'):
    """
    Find folders from original sources that aren't in Used_Images and copy them.
    """
    # Get all folders that were copied (exist in Used_Images)
    copied_folder_names = set()
    for item in os.listdir(used_folder):
        if os.path.isdir(os.path.join(used_folder, item)):
            copied_folder_names.add(item)
    
    print(f"Found {len(copied_folder_names)} folders in {used_folder}")
    
    # Get all folders from original sources
    all_source_folders = []  # (source_path, folder_name)
    for source in source_folders:
        if os.path.exists(source):
            for item in os.listdir(source):
                full_path = os.path.join(source, item)
                if os.path.isdir(full_path):
                    all_source_folders.append((full_path, item))
    
    print(f"Found {len(all_source_folders)} total folders in original sources")
    
    # Find folders that weren't copied
    unused = []
    for full_path, folder_name in all_source_folders:
        if folder_name not in copied_folder_names:
            unused.append((full_path, folder_name))
    
    print(f"Found {len(unused)} unused folders")
    
    # Copy unused folders
    os.makedirs(unused_folder, exist_ok=True)
    copied = 0
    for src_path, folder_name in unused:
        dst = os.path.join(unused_folder, folder_name)
        try:
            if not os.path.exists(dst):
                shutil.copytree(src_path, dst)
                copied += 1
                if copied % 100 == 0:
                    print(f"Copied {copied} folders...")
        except Exception as e:
            print(f"Error copying {folder_name}: {e}")
    
    print(f"\nDone! Copied {copied} unused folders to '{unused_folder}'")


if __name__ == '__main__':
    csv_path = 'Final_Used_Cars_Egypt.csv'
    
    # Original source folders
    source_folders = [
        'images',
        'images_biddex',
        'images_dubizzle',
        'images_used',
        'images_yallamotor'
    ]
    
    used_folder = 'Used_Images'
    unused_folder = 'Unused_Images'
    
    find_unused_folders(csv_path, source_folders, used_folder, unused_folder)
