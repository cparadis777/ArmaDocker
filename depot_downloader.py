import subprocess
from pathlib import Path
import os

def download_workshop_item(id: int, user:str, passwd:str, dest:Path, manifest:bool=False) -> None:
    command = [
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
    if manifest:
        command.append("-manifest-only")
    subprocess.run(command)

def download_depot(app_id: int, user:str, passwd:str, dest:Path, manifest:bool=False) -> None:
    command =  [
        "DepotDownloader", 
        "-app", 
        str(app_id),
        "-username",
        user,
        "-password",
        passwd,
        "-remember-password",
        "-dir",
        str(dest)
    ]
    if manifest:
        command.append("-manifest-only")
    subprocess.run( command)

def download_server(usr:str, pwd:str, path:Path, manifest:bool=False) -> None:
    os.makedirs(path, exist_ok=True)
    download_depot(233780, usr, pwd, path, manifest=manifest)