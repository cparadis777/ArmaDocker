import shutil
import json
import os
from pathlib import Path
import depot_downloader
import dataclasses
import logging
import uuid

logger= logging.getLogger("Manager")

@dataclasses.dataclass
class Mod():
    name: str
    id: int
    order: int = 99999


def parse_mod_config(config_path: Path) -> tuple[list[Mod], list[Mod]]:
    """Parse the JSON configuration file and return its contents as a dictionary."""
    
    with config_path.open('r', encoding='utf-8') as config_file:
        config_data = json.load(config_file)
    
    server_mods: list[Mod] = []
    client_mods: list[Mod] = []
    
    for item in config_data.get("server_mods", []):
        order = item.get("order", 99999)
        server_mods.append(Mod(item["name"], item["id"], order=order))
    
    for item in config_data.get("client_mods", []):
        order = item.get("order", 99999)
        client_mods.append(Mod(item["name"], item["id"], order=order))

    return client_mods, server_mods

def download_mods(config_path:Path, usr:str, pwd:str, base_path:Path, max_downloads: int) -> tuple[list[Mod], list[Mod]]:
    """Download mods specified in the configuration file."""
    client_mods, server_mods = parse_mod_config(config_path)
    

    os.makedirs(base_path/"client_mods", exist_ok=True)
    os.makedirs(base_path/'server_mods', exist_ok=True)
    
    client_mods_tuples: list[tuple[int, Path, bool]] = []
    server_mods_tuples: list[tuple[int, Path, bool]] = []


    for mod in client_mods:
        client_mods_tuples.append( (mod.id, base_path/"client_mods"/mod.name, False) )
    
    for mod in server_mods:
        server_mods_tuples.append( (mod.id, base_path/"server_mods"/mod.name, False) )

    logger.info("Downloading client mods")
    depot_downloader.download_workshop_items_parallel(client_mods_tuples, usr, pwd, max_downloads=max_downloads)
    logger.info("Downloading server mods")

    depot_downloader.download_workshop_items_parallel(server_mods_tuples, usr, pwd, max_downloads=max_downloads)

    logger.info("Lowercasing mods")

    lowercase_mods(base_path)
    return client_mods, server_mods

def copy_keys(mods_path: Path, server_path: Path) -> None:
    """
    Recursively finds all .bikey files within the mods_path 
    and symlinks them into the server/keys directory.
    """

    server_keys_path = server_path / "keys"
    
    try:
        os.makedirs(server_keys_path, exist_ok=True)
        logger.debug(f"Ensuring keys directory exists: {server_keys_path}")
    except OSError as e:
        logger.error(f"Could not create keys directory {server_keys_path}: {e}")
        return

    # rglob("*.[bB][iI][kK][eE][yY]") makes it case-insensitive for the search
    # regardless of the host OS behavior.
    bikey_files = list(mods_path.rglob("*.[bB][iI][kK][eE][yY]"))


    if not bikey_files:
        logger.warning(f"No .bikey files found in {mods_path}")
        return

    for key_file in bikey_files:
        # Use resolve() to get the absolute path; symlinks work better with absolute paths
        target = key_file.resolve()
        
        # The link name should be lowercase for Linux server compatibility
        link_name = key_file.name.lower()
        link = server_keys_path / link_name
        
        try:
            # Check for existing file or broken symlink
            if link.exists() or link.is_symlink():
                link.unlink()
            
            # Create the symlink
            link.symlink_to(target)
            logger.debug(f"Symlinked key: {link_name} -> {target}")
            
        except OSError as e:
            logger.error(f"Failed to symlink {key_file.name}: {e}")
        except Exception as e:
            logger.critical(f"Unexpected error with key {key_file.name}: {e}")

    logger.debug(f"Key synchronization complete. Processed {len(bikey_files)} keys.")

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
    Recursively renames files and directories to lowercase.
    Uses an external 'logger' object for reporting.
    """
    if not os.path.exists(target_path):
        logger.error(f"Path not found: {target_path}")
        return

    logger.info(f"Starting recursive lowercase rename in: {target_path}")

    # topdown=False is critical to rename children before parent directories
    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files + dirs:
            if name.startswith("."):
                continue
            old_path = os.path.join(root, name)
            new_name = name.lower()
            new_path = os.path.join(root, new_name)

            # Skip if already lowercase
            if name == new_name:
                continue

            try:
                # 1. Handle Case-Insensitive Filesystems (Windows/Mac/Docker Bind Mounts)
                # If path exists and samefile() is True, it's a "self-collision"
                if os.path.exists(new_path) and os.path.samefile(old_path, new_path):
                    temp_name = f"{uuid.uuid4().hex}.tmp"
                    temp_path = os.path.join(root, temp_name)
                    
                    os.rename(old_path, temp_path)
                    os.rename(temp_path, new_path)
                    logger.debug(f"Renamed (Bridge): '{name}' -> '{new_name}'")

                # 2. Handle True Collisions (Native Linux Case-Sensitivity)
                # If path exists but samefile() is False, these are two different files
                elif os.path.exists(new_path):
                    if os.path.isdir(new_path):
                        shutil.rmtree(new_path)
                        logger.debug(f"Collision: Deleted existing directory '{new_path}' to overwrite")
                    else:
                        os.remove(new_path)
                        logger.debug(f"Collision: Deleted existing file '{new_path}' to overwrite")
                    
                    os.rename(old_path, new_path)
                    logger.debug(f"Renamed (Overwrite): '{name}' -> '{new_name}'")

                # 3. Simple Rename
                else:
                    os.rename(old_path, new_path)
                    logger.debug(f"Renamed: '{name}' -> '{new_name}'")

            except OSError as e:
                logger.error(f"Failed to rename '{old_path}' to '{new_path}': {e}")
            except Exception as e:
                logger.critical(f"Unexpected error during processing of '{old_path}': {e}")

    logger.info("Lowercase rename process completed.")