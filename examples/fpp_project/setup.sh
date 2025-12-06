#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

readonly SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

is_root() { [ "${EUID:-$(id -u)}" -eq 0 ]; }

detect_pkg_mgr() {
  if command -v apt-get >/dev/null 2>&1; then echo "apt"; return
  elif command -v dnf >/dev/null 2>&1; then echo "dnf"; return
  elif command -v pacman >/dev/null 2>&1; then echo "pacman"; return
  elif command -v apk >/dev/null 2>&1; then echo "apk"; return
  elif command -v zypper >/dev/null 2>&1; then echo "zypper"; return
  fi
  echo "unknown"
}

ensure_python() {
  if command -v python3 >/dev/null 2>&1 && python3 -m ensurepip --version >/dev/null 2>&1; then
      return
    fi
    echo "Missing python3."

  if ! is_root; then
    echo "Please run as root to install python3." >&2
    exit 1
  fi

  case "$(detect_pkg_mgr)" in
    apt)
      export DEBIAN_FRONTEND=noninteractive
      apt-get update -y
      apt-get install -y python3 python3-venv python3-pip
      ;;
    dnf)
      dnf install -y python3 python3-pip python3-virtualenv || dnf install -y python3
      ;;
    pacman)
      pacman -Sy --noconfirm python python-pip
      ;;
    apk)
      apk add --no-cache python3 py3-pip
      ;;
    zypper)
      zypper --non-interactive refresh
      zypper --non-interactive install python3 python3-pip
      ;;
    *)
      echo "Unknown packet manager - please install python3 manually." >&2
      exit 1
      ;;
  esac
}

detect_target_user() {
  if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    echo "$SUDO_USER"; return
  fi

  local home_dir; home_dir="$(extract_home_from_path "$SCRIPT_DIR")"
  if [ -n "$home_dir" ] && [ -d "$home_dir" ]; then
    if stat -c '%U' "$home_dir" >/dev/null 2>&1; then
      stat -c '%U' "$home_dir"
    else
      stat -f '%Su' "$home_dir"
    fi
    return
  fi

  if stat -c '%U' "$SCRIPT_DIR" >/dev/null 2>&1; then
    stat -c '%U' "$SCRIPT_DIR"
  else
    stat -f '%Su' "$SCRIPT_DIR"
  fi
}

ensure_python

TARGET_USER="$(detect_target_user || true)"
PYTHON="python3"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

prepare_venv() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    $PYTHON -m venv "$VENV_DIR"
    if is_root && [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
      echo "Changing ownership of $VENV_DIR to $TARGET_USER..."
      chown -R "$TARGET_USER":"$TARGET_USER" "$VENV_DIR"
    fi
  fi

  if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" -m ensurepip
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install flaskpp
  else
    echo "Virtualenv python not found at $VENV_PYTHON" >&2
    exit 1
  fi
}

if is_root && [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
  echo "Preparing environment as user: $TARGET_USER"
  sudo -H -u "$TARGET_USER" bash -c "
    set -e
    PYTHON=\"$PYTHON\"
    VENV_DIR=\"$VENV_DIR\"
    VENV_PYTHON=\"$VENV_PYTHON\"
    $(declare -f prepare_venv)

    prepare_venv
  "
else
  echo "Preparing environment as current user: $(id -un)"
  prepare_venv
fi

#####################################
#      Flask++ Setup Toolchain      #
#####################################

fpp init
fpp modules install example --src ../example_module
#fpp modules install mymodule -s https://github.com/OrgaOrUser/fpp-module
fpp setup
fpp run --interactive
