from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import os
from queue import Queue
import logging
from threading import Thread
from typing import Optional, IO

logger = logging.getLogger("Manager")

def _stream_pipe(pipe: IO[str], logger: logging.Logger, level: int = logging.INFO, prefix: str = "") -> None:
    for line in iter(pipe.readline, ''):
        if line:
            logger.log(level, prefix + line.rstrip())
    if hasattr(pipe, "close"):
        try:
            pipe.close()
        except Exception:
            pass

def run_and_stream(command: list[str], logger: logging.Logger, cwd: Optional[Path]=None, prefix: str = "") -> int:
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=str(cwd) if cwd else None,
    )
    t_out = Thread(target=_stream_pipe, args=(proc.stdout, logger, logging.INFO, prefix), daemon=True)
    t_err = Thread(target=_stream_pipe, args=(proc.stderr, logger, logging.ERROR, prefix), daemon=True)
    t_out.start()
    t_err.start()
    proc.wait()
    t_out.join()
    t_err.join()
    return proc.returncode

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
        ret = run_and_stream(command, logger, prefix=f"[Session {session_id}] ")
        if ret == 0:
            logger.info(f"[Session {session_id}] Successfully finished Item {id}")
        else:
            logger.error(f"[Session {session_id}] Failed Item {id} (Exit Code: {ret})")
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
    ret = run_and_stream(command, logger)
    if ret != 0:
        logger.error(f"Depot download for app {app_id} failed (Exit Code: {ret})")

def download_server(usr:str, pwd:str, path:Path, manifest:bool=False) -> None:
    os.makedirs(path, exist_ok=True)
    download_depot(233780, usr, pwd, path, manifest=manifest)
    os.chmod(path/"arma3server_x64", 0o777)