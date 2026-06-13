from dotenv import load_dotenv
from pathlib import Path
import os
import sys
import depot_downloader
import mods
import subprocess
import logging
import logging_config

logger = logging.getLogger("Manager")
server_logger = logging.getLogger("server")

ARMA_KEYS: list[str] = [
    "a3.bikey",
    "a3c.bikey",
    "csla.bikey",
    "ef.bikey",
    "gm.bikey",
    "rf.bikey",
    "spe.bikey",
    "vn.bikey",
    "ws.bikey",
]


def str_to_bool(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() not in ("0", "false", "no", "n", "off", "")


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
        "-filePatching",
        f"-name={server_name}",
    ] + server_mod_args + client_mod_args
    logger.info(f"Launching server with command: {' '.join(command)}")

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=server_path,
    )

    for line in process.stdout:  # type: ignore
        clean_line = line.strip()
        if clean_line:
            server_logger.debug(f"[SERVER] {clean_line}")

    process.wait()

    if process.returncode != 0:
        logger.error(f"Server exited with error code {process.returncode}")
    else:
        logger.info("Server shut down gracefully.")


def copy_missions_files(missions_path: Path, server_path: Path) -> None:
    """Symlink the missions from the missions directory to the server directory."""
    (server_path / "mpmissions").mkdir(parents=True, exist_ok=True)

    for mission in missions_path.iterdir():
        target = mission
        link = server_path / "mpmissions" / mission.name

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


def delete_or_unlink(files: list[Path]) -> None:
    for file in files:
        if file.is_symlink():
            file.unlink()
        else:
            file.unlink()

def copy_cba_settings(settings_file) -> None:
    target = settings_file
    link = Path("/home/steam/arma3/userconfig/cba_settings.sqf")
    os.makedirs("/home/steam/arma3/userconfig")

    if link.exists() or link.is_symlink():
        link.unlink()

    link.symlink_to(target)
    
def cleanup_files(server_path: Path) -> None:
    keys_dir = [key for key in (server_path / "keys").iterdir() if key.name not in ARMA_KEYS]
    logger.info(f"Cleaning up non-vanilla keys: {[k.name for k in keys_dir]}")
    mod_dirs = list(server_path.glob("@*"))
    mission_dir = list((server_path / "mpmissions").iterdir())
    delete_or_unlink(keys_dir)
    delete_or_unlink(mod_dirs)
    delete_or_unlink(mission_dir)


def validate_quick_start(server_path: Path, base_path: Path) -> bool:
    """Validate that quick-start prerequisites are met."""
    if not (server_path / "arma3server_x64").exists():
        logger.warning("Quick-start validation failed: server binary missing")
        return False

    if not (base_path / "mods.json").exists():
        logger.warning("Quick-start validation failed: mods.json missing")
        return False

    try:
        client_mods, server_mods = mods.parse_mod_config(base_path / "mods.json")
    except Exception:
        logger.warning("Quick-start validation failed: mods.json unreadable")
        return False

    missing_mods = []
    for mod in client_mods:
        if not (base_path / "mods" / "client_mods" / mod.name).exists():
            missing_mods.append(mod.name)
    for mod in server_mods:
        if not (base_path / "mods" / "server_mods" / mod.name).exists():
            missing_mods.append(mod.name)

    if missing_mods:
        logger.warning(f"Quick-start validation failed: missing mods {missing_mods}")
        return False

    logger.info("Quick-start validation passed")
    return True


def perform_updates() -> tuple[list[mods.Mod], list[mods.Mod]]:
    usr = os.environ.get("STEAM_USER", "")
    pwd = os.environ.get("STEAM_PASS", "")
    max_downloads = int(os.environ.get("N_DOWNLOAD_THREADS", "1"))
    base_path = Path("/arma")
    server_path = Path("/server")

    logger.info("Downloading server")
    depot_downloader.download_server(usr, pwd, server_path, manifest=False)
    cleanup_files(server_path)

    logger.info("Downloading mods")
    client_mods, server_mods = mods.download_mods(
        base_path / "mods.json", usr, pwd, base_path / "mods", max_downloads
    )

    logger.info("Copying mods and keys")
    mods.copy_mods(mods_path=base_path / "mods/server_mods", server_path=server_path)
    mods.copy_mods(mods_path=base_path / "mods/client_mods", server_path=server_path)
    mods.copy_keys(mods_path=base_path / "mods/client_mods", server_path=server_path)
    mods.copy_keys(mods_path=base_path, server_path=server_path)

    logger.info("Copying missions and configs")
    copy_missions_files(missions_path=base_path / "mpmissions", server_path=server_path)
    copy_config(config_path=base_path / "server.cfg", server_path=server_path)
    return client_mods, server_mods


if __name__ == "__main__":
    logging_config.setup_logging()

    load_dotenv()
    base_path = Path("/arma")
    server_path = Path("/server")

    (base_path / "mpmissions").mkdir(parents=True, exist_ok=True)
    (base_path / "logs").mkdir(parents=True, exist_ok=True)

    update_on_start = str_to_bool(os.environ.get("UPDATE_ON_START"))

    client_mods: list[mods.Mod] = []
    server_mods: list[mods.Mod] = []

    if not update_on_start:
        logger.info("Quick start requested (UPDATE_ON_START=0): skipping updates")
        if validate_quick_start(server_path, base_path):
            try:
                client_mods, server_mods = mods.parse_mod_config(base_path / "mods.json")
                logger.info("Recreating mod and key symlinks for quick start")
                mods.copy_mods(mods_path=base_path / "mods/server_mods", server_path=server_path)
                mods.copy_mods(mods_path=base_path / "mods/client_mods", server_path=server_path)
                mods.copy_keys(mods_path=base_path / "mods/client_mods", server_path=server_path)
                mods.copy_keys(mods_path=base_path, server_path=server_path)

                logger.info("Quick-start preflight complete; launching server")
            except Exception:
                logger.exception("Quick-start preflight failed")
                sys.exit(1)
        else:
            logger.warning("Quick-start validation failed; falling back to full update")
            try:
                client_mods, server_mods = perform_updates()
            except Exception:
                logger.exception("Update failed during fallback")
                sys.exit(1)
    else:
        logger.info("Update requested (UPDATE_ON_START != 0): running updates before starting server")
        try:
            client_mods, server_mods = perform_updates()
        except Exception:
            logger.exception("Update failed during perform_updates")
            sys.exit(1)

    copy_missions_files(missions_path=base_path / "mpmissions", server_path=server_path)
    copy_config(config_path=base_path / "server.cfg", server_path=server_path)
    copy_cba_settings(base_path/"cba_settings.sqf")
    logger.info("Launching server")
    launch_server(server_path, client_mods, server_mods)
    logger.info("Server shutdown")