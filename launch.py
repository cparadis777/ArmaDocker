from dotenv import load_dotenv
from pathlib import Path
import os
import depot_downloader
import mods





if __name__ == "__main__":
    load_dotenv()
    base_path = Path("/opt/arma")
    usr = os.environ.get("STEAM_USER", "")
    pwd = os.environ.get("STEAM_PASS", "")
    #depot_downloader.download_server(usr, pwd, base_path/"server", manifest=True)
    mods.download_mods(Path("/opt/arma/mods.json"), usr, pwd, base_path/"mods")
