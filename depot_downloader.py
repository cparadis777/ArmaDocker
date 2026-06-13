from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import os
from queue import Queue
import logging

logger = logging.getLogger("Manager")


def run_and_stream(command: list[str], cwd: Path | None = None, prefix: str = "") -> int:
    """Run a command and stream merged stdout/stderr to the logger."""
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(cwd) if cwd else None,
    )
    for line in proc.stdout:  # type: ignore
        clean = line.strip()
        if clean:
            logger.info(prefix + clean)
    proc.wait()
    return proc.returncode


def download_workshop_item(
    id: int,
    user: str,
    passwd: str,
    dest: Path,
    manifest: bool = False,
    id_pool: Queue[int] | None = None,
) -> None:
    session_id = 10
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
        "12",
    ]

    if manifest:
        command.append("-manifest-only")

    ret = run_and_stream(command, cwd=None, prefix=f"[Session {session_id}] ")
    if ret != 0:
        raise RuntimeError(f"[Session {session_id}] Failed Item {id} (Exit Code: {ret})")
    logger.info(f"[Session {session_id}] Successfully finished Item {id}")

    if id_pool:
        id_pool.put(session_id)


def download_workshop_items_parallel(
    items: list[tuple[int, Path, bool]],
    user: str,
    passwd: str,
    max_downloads: int = 1,
) -> None:
    id_start = 10
    pool_size = max_downloads

    id_pool: Queue[int] = Queue()
    for i in range(id_start, id_start + pool_size):
        id_pool.put(i)

    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        for item in items:
            executor.submit(download_workshop_item, item[0], user, passwd, item[1], item[2], id_pool)


def download_depot(
    app_id: int, user: str, passwd: str, dest: Path, manifest: bool = False
) -> None:
    command = [
        "DepotDownloader",
        "-app",
        str(app_id),
        "-username",
        user,
        "-password",
        passwd,
        "-remember-password",
        "-dir",
        str(dest),
    ]
    if manifest:
        command.append("-manifest-only")
    ret = run_and_stream(command)
    if ret != 0:
        raise RuntimeError(f"Depot download for app {app_id} failed (Exit Code: {ret})")


def download_server(usr: str, pwd: str, path: Path, manifest: bool = False) -> None:
    os.makedirs(path, exist_ok=True)
    download_depot(233780, usr, pwd, path, manifest=manifest)
    server_binary = path / "arma3server_x64"
    if server_binary.exists():
        os.chmod(server_binary, 0o755)
