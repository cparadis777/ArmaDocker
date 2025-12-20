from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import os
from queue import Queue
import logging

logger = logging.getLogger("Manager")

def download_workshop_item(id: int, user:str, passwd:str, dest:Path, manifest:bool=False, id_pool: Queue[int] | None = None) -> None:
    session_id:int = 10
    if id_pool:
        session_id = id_pool.get()

    logger.info(f"Downloading workshop item {id} to {dest.name} with session id {session_id}")
    command = [
        "DepotDownloader", 
        "-app", 
        "107410",
        "-pubfile", 
        str(id),
        "-username",
        user,
        "-password",
        passwd,
        "-remember-password",
        "-loginid",
        str(session_id),
        "-dir",
        str(dest),
        "-max-downloads",
        "12"]
    
    if manifest:
        command.append("-manifest-only")

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"[Session {session_id}] Successfully finished Item {id}")
        else:
            logger.error(f"[Session {session_id}] Failed Item {id} (Exit Code: {result.returncode})")
            if result.stdout:
                logger.error(f"STDOUT: {result.stdout.strip()}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr.strip()}")  
            
    except Exception as e:
        logger.exception(f"[Session {session_id}] Critical failure for {id}: {e}")    
    finally:
   
        if id_pool:
            id_pool.put(session_id)
            id_pool.task_done()

def download_workshop_items_parallel(items: list[tuple[int, Path, bool]], user:str, passwd:str, max_downloads:int=1) -> None:
    ID_START: int=10
    POOL_SIZE: int = max_downloads

    id_pool: Queue[int] = Queue()
    for i in range(ID_START, ID_START + POOL_SIZE):
        id_pool.put(i)

    with ThreadPoolExecutor(max_workers=POOL_SIZE) as executor:
        for item in items:
            executor.submit(download_workshop_item, item[0], user, passwd, item[1], item[2], id_pool)



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
    os.chmod(path/"arma3server_x64", 0o777)