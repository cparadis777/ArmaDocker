import json
import os
from pathlib import Path
import depot_downloader
import dataclasses

@dataclasses.dataclass
class Mod():
    name: str
    id: int


def parse_mod_config(config_path: Path) -> tuple[list[Mod], list[Mod]]:
    """Parse the JSON configuration file and return its contents as a dictionary."""
    
    with config_path.open('r', encoding='utf-8') as config_file:
        config_data = json.load(config_file)
    
    server_mods: list[Mod] = [
        Mod(item["name"], item["id"]) 
        for item in config_data.get("server_mods", {})
    ]
    
    client_mods: list[Mod] = [
        Mod(item["name"], item["id"]) 
        for item in config_data.get("client_mods", {})
    ]

    return client_mods, server_mods

def download_mods(config_path:Path, usr:str, pwd:str, base_path:Path) -> None:
    """Download mods specified in the configuration file."""
    client_mods, server_mods = parse_mod_config(config_path)

    os.makedirs(base_path/"client_mods", exist_ok=True)
    os.makedirs(base_path/'server_mods', exist_ok=True)
   
    for mod in client_mods:
        depot_downloader.download_workshop_item(mod.id,usr, pwd, base_path/"client_mods"/mod.name)

    for mod in server_mods:
        depot_downloader.download_workshop_item(mod.id, usr, pwd, base_path/"server_mods"/mod.name)
    lowercase_mods(base_path)

def copy_keys(mods_path:Path, server_path:Path) -> None:
    """Copy the keys from the mods to the server directory."""
    server_keys_path = server_path/"keys"
    os.makedirs(server_keys_path, exist_ok=True)

    for mod_dir in mods_path.iterdir():
        mod_key_path = mod_dir/"keys"
        if mod_key_path.exists() and mod_key_path.is_dir():
            for key_file in mod_key_path.iterdir():
                target = server_keys_path/key_file.name
                link = Path(server_keys_path/key_file.name)
                
                # If symlink already exists, remove it first
                if link.exists() or link.is_symlink():
                    link.unlink()
                
                link.symlink_to(target)

def copy_mods(mods_path:Path, server_path:Path) -> list[str]:
    """Copy the mods from the mods directory to the server directory."""
    mods: list[str] = []
    for mod_dir in mods_path.iterdir():
        target = mod_dir
        link = Path(server_path/mod_dir.name)
        
        # If symlink already exists, remove it first
        if link.exists() or link.is_symlink():
            link.unlink()
        
        link.symlink_to(target)
        mods.append(mod_dir.name)
    return mods

def lowercase_mods(target_path: Path):
    """
    Recursively renames all files and directories to lowercase.
    """
    # Check if the path exists
    if not os.path.exists(target_path):
        print(f"Error: The path '{target_path}' does not exist.")
        return

    # topdown=False ensures we rename children before their parent directories
    for root, dirs, files in os.walk(target_path, topdown=False):
        
        # Process both files and directories in the current 'root'
        for name in files + dirs:
            old_path = os.path.join(root, name)
            
            # Create the lowercase version of the name
            new_name = name.lower()
            new_path = os.path.join(root, new_name)

            # Only rename if the name actually changed
            if old_path != new_path:
                try:
                    # Handle potential collisions (e.g., 'File.txt' and 'file.txt')
                    if os.path.exists(new_path):
                        print(f"Skipping: {new_path} already exists.")
                    else:
                        os.rename(old_path, new_path)
                        print(f"Renamed: {old_path} -> {new_path}")
                except OSError as e:
                    print(f"Error renaming {old_path}: {e}")