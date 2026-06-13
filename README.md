# ArmaDocker

Arma 3 Dedicated Server containerized for Docker or Podman.

## Quick Start

1. Copy the example environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your Steam credentials and server settings
   ```

2. Configure your mods in `arma/mods.json`.

3. Configure your server settings in `arma/server.cfg.template`. The following environment variables are expanded at runtime:
   - `SERVER_NAME`
   - `SERVER_PASSWORD`
   - `SERVER_ADMIN_PASSWORD`
   - `SERVER_COMMAND_PASSWORD`

4. Start the server:
   ```bash
   ./serverctl.sh start --mode update
   ```

5. For subsequent quick starts (skip downloads):
   ```bash
   ./serverctl.sh start --mode quick
   ```

## Available Commands

| Command | Description |
|---|---|
| `start` | Start the server (default: update) |
| `stop` | Stop and remove the container |
| `restart` | Restart the server |
| `status` | Show running containers |
| `logs` | Tail server logs |

## Directory Structure

- `arma/mods.json` — Workshop mod list with load order
- `arma/server.cfg.template` — Server configuration template
- `arma/mpmissions/` — Mission files
- `arma/logs/` — Server logs (mounted from container)
- `.env` — Secrets and settings (do not commit)

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `STEAM_USER` | Steam username | *(required)* |
| `STEAM_PASS` | Steam password | *(required)* |
| `SERVER_NAME` | Server hostname | `Arma 3 Server` |
| `SERVER_PASSWORD` | Server join password | `changeme` |
| `SERVER_ADMIN_PASSWORD` | Admin password | `changeme` |
| `SERVER_COMMAND_PASSWORD` | Server command password | `changeme` |
| `N_DOWNLOAD_THREADS` | Concurrent mod downloads | `4` |
| `LOG_LEVEL` | Python log level | `INFO` |
| `UPDATE_ON_START` | `0` for quick start, `1` for update | `1` |

## Networking

The server exposes the following ports:

| Port | Protocol | Purpose |
|---|---|---|
| 2302-2306 | UDP | Game traffic |
| 2302-2306 | TCP | Steam query / RCON |

## Requirements

- [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/)
- A Steam account that owns Arma 3
- Bash (for `serverctl.sh`)
