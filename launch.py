from dotenv import load_dotenv
from pathlib import Path
import os
import depot_downloader
import mods
import subprocess

def launch_server(server_path: Path, client_mods: list[str], server_mods: list[str]) -> None:
    """Launch the Arma 3 server.""" 
    server_name = os.environ.get("SERVER_NAME", "Arma 3 Server")
    server_mod_args = [f"-servermod={';'.join(server_mods)}"] if server_mods else []
    client_mod_args = [f"-mod={';'.join(client_mods)}"] if client_mods else []
    print([file.name for file in server_path.iterdir()])
    command = [
        "./arma3server_x64",
        "-config=server.cfg",
        f"-name={server_name}",
    ] + server_mod_args + client_mod_args
    subprocess.run(command, cwd=server_path)

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

if __name__ == "__main__":
    load_dotenv()
    base_path = Path("/arma")
    usr = os.environ.get("STEAM_USER", "")
    pwd = os.environ.get("STEAM_PASS", "")
    server_path = Path("/server")

    os.makedirs(base_path/"mpmissions", exist_ok=True)
    os.makedirs("/logs", exist_ok=True)
    depot_downloader.download_server(usr, pwd, server_path, manifest=False)
    mods.download_mods(Path("/arma/mods.json"), usr, pwd, base_path/"mods")
    server_mods = mods.copy_mods(mods_path=base_path/"mods/server_mods", server_path=server_path)
    client_mods = mods.copy_mods(mods_path=base_path/"mods/client_mods", server_path=server_path)

    mods.copy_keys(mods_path=base_path/"mods/client_mods", server_path=server_path)
    copy_missions_files(missions_path=base_path/"mpmissions", server_path=server_path)
    copy_config(config_path=base_path/"server.cfg", server_path=server_path)
    launch_server(server_path, client_mods, server_mods)
