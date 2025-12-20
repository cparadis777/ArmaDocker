from dotenv import load_dotenv
from pathlib import Path
import os
import depot_downloader
import mods
import subprocess
import datetime
import logging
from logging.handlers import RotatingFileHandler
import sys

log_file = f"arma_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler(f"/logs/{log_file}", maxBytes=5*1024*1024, backupCount=2)
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

logger = logging.getLogger("Manager")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def launch_server(server_path: Path, client_mods: list[mods.Mod], server_mods: list[mods.Mod]) -> None:
    """Launch the Arma 3 server.""" 

    client_mods_names = [mod.name for mod in sorted(client_mods, key=lambda m: m.order)]
    server_mods_names = [mod.name for mod in sorted(server_mods, key=lambda m: m.order)]
    server_name = os.environ.get("SERVER_NAME", "Arma 3 Server")
    server_mod_args = [f"-servermod={';'.join(server_mods_names)}"] if server_mods else []
    client_mod_args = [f"-mod={';'.join(client_mods_names)}"] if client_mods else []

    command = [
        "./arma3server_x64",
        "-config=server.cfg",   
        f"-name={server_name}",
    ] + server_mod_args + client_mod_args
    logger.info(f"Launching server with command: {' '.join(command)}")


    process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=server_path
        )

        # Stream server output to the file only
    for line in process.stdout:  # type: ignore
        clean_line = line.strip()
        if clean_line:
            # We use logger.debug (or a custom level) for server lines 
            # so they don't show up in the console_handler (set to INFO)
            logger.debug(f"[SERVER] {clean_line}")

    process.wait()
    
    if process.returncode != 0:
        logger.error(f"Server exited with error code {process.returncode}")
    else:
        logger.info("Server shut down gracefully.")

def copy_missions_files(missions_path:Path, server_path:Path) -> None:
    """Copy the missions from the missions directory to the server directory."""
    os.makedirs(server_path/"mpmissions", exist_ok=True)

    for mission in missions_path.iterdir():
        target = missions_path/mission.name
        link = Path(server_path/"mpmissions"/mission.name)
        
        # If symlink already exists, remove it first
        if link.exists() or link.is_symlink():
            link.unlink()
        
        link.symlink_to(target)
    
def copy_config(config_path:Path, server_path:Path) -> None:
    """Copy the configuration file to the server directory."""
    target = config_path
    link = Path(server_path/config_path.name)
    
    # If symlink already exists, remove it first
    if link.exists() or link.is_symlink():
        link.unlink()
    
    link.symlink_to(target)


def delete_or_unlink(files: list[Path]):
    for file in files:
        if file.is_symlink():
            file.unlink()
        else:
            os.remove(file)

def cleanup_files(server_path:Path):
    keys_dir: list[Path] = list((server_path/"keys").iterdir())
    mod_dirs: list[Path] = list(server_path.glob("@*"))
    mission_dir: list[Path] = list((server_path/"mpmissions").iterdir())
    delete_or_unlink(keys_dir)
    delete_or_unlink(mod_dirs)
    delete_or_unlink(mission_dir)


if __name__ == "__main__":
    load_dotenv()
    base_path = Path("/arma")
    usr = os.environ.get("STEAM_USER", "")
    pwd = os.environ.get("STEAM_PASS", "")
    MAX_DOWNLOADS: int = int(os.environ.get("N_DOWNLOAD_THREADS", "1"))
    
    server_path = Path("/server")

    os.makedirs(base_path/"mpmissions", exist_ok=True)
    os.makedirs("/logs", exist_ok=True)

    logger.info("Cleaning up existing files")
    cleanup_files(server_path)

    logger.info("Downloading server")

    depot_downloader.download_server(usr, pwd, server_path, manifest=False)
    
    logger.info("Downloading mods")

    client_mods, server_mods = mods.download_mods(Path("/arma/mods.json"), usr, pwd, base_path/"mods", MAX_DOWNLOADS)

    logger.info("Copying mods and keys")

    mods.copy_mods(mods_path=base_path/"mods/server_mods", server_path=server_path)
    mods.copy_mods(mods_path=base_path/"mods/client_mods", server_path=server_path)

    mods.copy_keys(mods_path=base_path/"mods/client_mods", server_path=server_path)
    mods.copy_keys(mods_path=base_path, server_path=server_path)
    
    logger.info("Copying missions and configs")

    copy_missions_files(missions_path=base_path/"mpmissions", server_path=server_path)
    copy_config(config_path=base_path/"server.cfg", server_path=server_path)

    logger.info("Launching server")

    launch_server(server_path, client_mods, server_mods)
