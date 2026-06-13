import shutil
import json
import os
from pathlib import Path
import depot_downloader
import dataclasses
import logging
import uuid

logger = logging.getLogger("Manager")


@dataclasses.dataclass
class Mod:
    name: str
    id: int
    order: int = 99999


def parse_mod_config(config_path: Path) -> tuple[list[Mod], list[Mod]]:
    """Parse the JSON configuration file and return client and server mods."""
    with config_path.open("r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    server_mods: list[Mod] = []
    client_mods: list[Mod] = []

    for item in config_data.get("server_mods", []):
        order = item.get("order", 99999)
        server_mods.append(Mod(item["name"], int(item["id"]), order=order))

    for item in config_data.get("client_mods", []):
        order = item.get("order", 99999)
        client_mods.append(Mod(item["name"], int(item["id"]), order=order))

    return client_mods, server_mods


def download_mods(
    config_path: Path, usr: str, pwd: str, base_path: Path, max_downloads: int
) -> tuple[list[Mod], list[Mod]]:
    """Download mods specified in the configuration file."""
    client_mods, server_mods = parse_mod_config(config_path)

    (base_path / "client_mods").mkdir(parents=True, exist_ok=True)
    (base_path / "server_mods").mkdir(parents=True, exist_ok=True)

    client_mods_tuples: list[tuple[int, Path, bool]] = []
    server_mods_tuples: list[tuple[int, Path, bool]] = []

    for mod in client_mods:
        client_mods_tuples.append((mod.id, base_path / "client_mods" / mod.name, False))

    for mod in server_mods:
        server_mods_tuples.append((mod.id, base_path / "server_mods" / mod.name, False))

    logger.info("Downloading client mods")
    depot_downloader.download_workshop_items_parallel(
        client_mods_tuples, usr, pwd, max_downloads=max_downloads
    )
    logger.info("Downloading server mods")
    depot_downloader.download_workshop_items_parallel(
        server_mods_tuples, usr, pwd, max_downloads=max_downloads
    )

    logger.info("Lowercasing mods")
    lowercase_mods(base_path)
    return client_mods, server_mods


def copy_keys(mods_path: Path, server_path: Path) -> None:
    """
    Recursively finds all .bikey files within the mods_path
    and symlinks them into the server/keys directory.
    """
    server_keys_path = server_path / "keys"
    server_keys_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensuring keys directory exists: {server_keys_path}")

    bikey_files = list(mods_path.rglob("*.[bB][iI][kK][eE][yY]"))
    if not bikey_files:
        logger.warning(f"No .bikey files found in {mods_path}")
        return

    for key_file in bikey_files:
        target = key_file.resolve()
        link_name = key_file.name.lower()
        link = server_keys_path / link_name

        try:
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(target)
            logger.debug(f"Symlinked key: {link_name} -> {target}")
        except OSError as e:
            logger.error(f"Failed to symlink {key_file.name}: {e}")
        except Exception as e:
            logger.critical(f"Unexpected error with key {key_file.name}: {e}")

    logger.debug(f"Key synchronization complete. Processed {len(bikey_files)} keys.")


def copy_mods(mods_path: Path, server_path: Path) -> list[str]:
    """Symlink the mods from the mods directory to the server directory."""
    mods: list[str] = []
    for mod_dir in mods_path.iterdir():
        link = server_path / mod_dir.name
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(mod_dir)
        mods.append(mod_dir.name)
    return mods


def lowercase_mods(target_path: Path) -> None:
    """Recursively renames files and directories to lowercase."""
    if not target_path.exists():
        logger.error(f"Path not found: {target_path}")
        return

    logger.info(f"Starting recursive lowercase rename in: {target_path}")

    for root, dirs, files in os.walk(target_path, topdown=False):
        for name in files + dirs:
            if name.startswith("."):
                continue
            old_path = Path(root) / name
            new_name = name.lower()
            new_path = Path(root) / new_name

            if name == new_name:
                continue

            try:
                if new_path.exists() and new_path.samefile(old_path):
                    temp_path = old_path.with_suffix(f".tmp-{uuid.uuid4().hex}")
                    old_path.rename(temp_path)
                    temp_path.rename(new_path)
                    logger.debug(f"Renamed (Bridge): '{name}' -> '{new_name}'")
                elif new_path.exists():
                    if new_path.is_dir():
                        shutil.rmtree(new_path)
                    else:
                        new_path.unlink()
                    old_path.rename(new_path)
                    logger.debug(f"Renamed (Overwrite): '{name}' -> '{new_name}'")
                else:
                    old_path.rename(new_path)
                    logger.debug(f"Renamed: '{name}' -> '{new_name}'")

            except OSError as e:
                logger.error(f"Failed to rename '{old_path}' to '{new_path}': {e}")
            except Exception as e:
                logger.critical(f"Unexpected error during processing of '{old_path}': {e}")

    logger.info("Lowercase rename process completed.")
