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

    return server_mods, client_mods

def download_mods(config_path:Path, usr:str, pwd:str, base_path:Path) -> None:
    """Download mods specified in the configuration file."""
    client_mods, server_mods = parse_mod_config(config_path)
    print(client_mods)
    print(server_mods)

    os.makedirs(base_path/"client_mods", exist_ok=True)
    os.makedirs(base_path/'server_mods', exist_ok=True)
   
    for mod in client_mods:
        print(mod)
        depot_downloader.download_workshop_item(mod.id,usr, pwd, base_path/"client_mods"/mod.name)

    for mod in server_mods:
        print(mod)
        depot_downloader.download_workshop_item(mod.id, usr, pwd, base_path/"server_mods"/mod.name)
