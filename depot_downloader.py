import subprocess
from pathlib import Path

def download_workshop_item(id: int, user:str, passwd:str, dest:Path) -> None:
    subprocess.run([
        "DepotDownloader", 
        "-app", 
        "1074100",
        "-pubfile", 
        str(id),
        "-username",
        user,
        "-password",
        passwd,
        "-remember-password",
        "-dir",
        str(dest)]
    )

def download_depot(app_id: int, user:str, passwd:str, dest:Path) -> None:
    subprocess.run([
        "DepotDownloader", 
        "-app", 
        str(app_id),
        "-username",
        user,
        "-password",
        passwd,
        "-remember-password",
        "-dir",
        str(dest)]
    )