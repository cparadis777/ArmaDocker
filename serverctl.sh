#!/usr/bin/env bash
set -euo pipefail

# Simple helper to manage the ArmaDocker compose stack.
# Usage: serverctl.sh <command> [--mode quick|update]
# Commands: start stop restart status logs
# Modes:
#   quick  -> UPDATE_ON_START=0 (skip downloads/validation)
#   update -> UPDATE_ON_START=1 (perform updates before starting)

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [--mode quick|update]

Commands:
  start        Start the server (default: update)
  stop         Stop and remove the server container
  restart      Stop then start
  status       Show compose ps
  logs         Tail service logs

Modes:
  --mode quick    Quick start: set UPDATE_ON_START=0 (skip updates)
  --mode update   Update start: set UPDATE_ON_START=1 (perform updates)

Environment:
  COMPOSE_CMD     Override compose command (default: podman compose if available, else docker compose)

Examples:
  UPDATE_ON_START=0 $(basename "$0") start      # quick start
  $(basename "$0") start --mode update         # start and force update
  $(basename "$0") restart --mode quick        # restart quickly
EOF
}

# determine compose command
COMPOSE_CMD=${COMPOSE_CMD:-}
if [ -z "${COMPOSE_CMD}" ]; then
  if command -v podman >/dev/null 2>&1; then
    COMPOSE_CMD="podman compose"
  elif command -v docker >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  else
    echo "Error: neither podman nor docker found in PATH. Set COMPOSE_CMD to your compose command." >&2
    exit 1
  fi
fi

# Require Bash
if [ -z "${BASH_VERSION:-}" ]; then
  echo "Error: this script requires Bash. Run it with 'bash serverctl.sh' or make it executable and run './serverctl.sh'" >&2
  exit 2
fi

# Ensure script runs from repository root (script lives in repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
cd "${REPO_ROOT}"

# Preflight checks
if [ ! -f "${REPO_ROOT}/.env" ]; then
  echo "Error: .env file not found. Please copy .env.example to .env and fill in your credentials." >&2
  exit 1
fi

if [ ! -f "${REPO_ROOT}/arma/mods.json" ]; then
  echo "Warning: arma/mods.json not found. No mods will be loaded." >&2
fi

if [ $# -lt 1 ]; then
  usage
  exit 2
fi

CMD=$1; shift || true
MODE="update" # default
while [ $# -gt 0 ]; do
  case "$1" in
    --mode)
      shift
      MODE=${1:-}
      shift || true
      ;;
    --mode=*)
      MODE="${1#--mode=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

run_compose() {
  if [ "${MODE}" = "quick" ] || [ "${MODE}" = "0" ]; then
    env UPDATE_ON_START=0 ${COMPOSE_CMD} "$@"
  else
    env UPDATE_ON_START=1 ${COMPOSE_CMD} "$@"
  fi
}

case "$CMD" in
  start)
    echo "Starting server (mode=${MODE})..."
    run_compose up -d --force-recreate
    ;;

  stop)
    echo "Stopping server..."
    ${COMPOSE_CMD} down
    ;;

  restart)
    echo "Restarting server (mode=${MODE})..."
    ${COMPOSE_CMD} down
    run_compose up -d --force-recreate
    ;;

  status)
    ${COMPOSE_CMD} ps
    ;;

  logs)
    ${COMPOSE_CMD} logs -f arma3-server
    ;;

  *)
    echo "Unknown command: $CMD" >&2
    usage
    exit 2
    ;;
esac

exit 0
