from dotenv import load_dotenv
from pathlib import Path
import os
import depot_downloader


if __name__ == "__main__":
    load_dotenv()
    download_path = Path("/opt/server")
    usr = os.environ.get("STEAM_USER", "")
    pwd = os.environ.get("STEAM_PASS", "")
    depot_downloader.download_depot(233780, usr, pwd, download_path)