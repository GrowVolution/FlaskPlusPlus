#!/usr/bin/env bash
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

extract_home_from_path() {
  local path="$1"
  if echo "$path" | grep -qE "^/home/[^/]+"; then
    echo "$path" | grep -oE "^/home/[^/]+"
  elif echo "$path" | grep -qE "^/Users/[^/]+"; then
    echo "$path" | grep -oE "^/Users/[^/]+"
  else
    echo ""
  fi
}

detect_target_user() {
  # 1) via sudo gestartet?
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
SETUP_PY="$SCRIPT_DIR/setup.py"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ ! -f "$SETUP_PY" ]; then
  echo "setup.py not found at: $SETUP_PY" >&2
  exit 1
fi

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
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
      echo "Installing dependencies from requirements.txt..."
      "$VENV_PYTHON" -m pip install --upgrade pip
      "$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"
    fi
  else
    echo "Virtualenv python not found at $VENV_PYTHON" >&2
    exit 1
  fi
}

generate_fs_translations() {
  local cfg="$SCRIPT_DIR/babel.cfg"
  local pot="$SCRIPT_DIR/messages.pot"
  local trans="$SCRIPT_DIR/translations"

  mkdir -p "$trans"

  if [ ! -f "$cfg" ]; then
    echo "Warning: babel.cfg not found at $cfg – using default extract patterns."
    cat >"$SCRIPT_DIR/.babel.fallback.cfg" <<'CFG'
[python: **/**.py]

[jinja2: **/templates/**.html]
extensions=jinja2.ext.i18n
CFG
    cfg="$SCRIPT_DIR/.babel.fallback.cfg"
  fi

  echo "Extracting messages to $pot..."
  "$VENV_DIR/bin/pybabel" extract -F "$cfg" -o "$pot" "$SCRIPT_DIR" || return 1

  if [ -f "$trans/en/LC_MESSAGES/messages.po" ]; then
    echo "Updating existing catalogs (en)..."
    "$VENV_DIR/bin/pybabel" update -i "$pot" -d "$trans" || return 1
  else
    echo "Initializing catalogs (en)..."
    "$VENV_DIR/bin/pybabel" init -i "$pot" -d "$trans" -l en || return 1
  fi

  echo "Compiling catalogs..."
  "$VENV_DIR/bin/pybabel" compile -d "$trans" || return 1
}

if is_root && [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
  echo "Preparing environment as user: $TARGET_USER"
  sudo -H -u "$TARGET_USER" bash -c "
    set -e
    PYTHON=\"$PYTHON\"
    SCRIPT_DIR=\"$SCRIPT_DIR\"
    VENV_DIR=\"$VENV_DIR\"
    VENV_PYTHON=\"$VENV_PYTHON\"
    SETUP_PY=\"$SETUP_PY\"
    $(declare -f prepare_venv)
    $(declare -f generate_fs_translations)

    prepare_venv
    \"$VENV_PYTHON\" -m pip show Babel >/dev/null 2>&1 || \"$VENV_PYTHON\" -m pip install Babel
    generate_fs_translations
    \"$VENV_PYTHON\" \"$SETUP_PY\"
  "
else
  echo "Preparing environment as current user: $(id -un)"
  prepare_venv
  "$VENV_PYTHON" -m pip show Babel >/dev/null 2>&1 || "$VENV_PYTHON" -m pip install Babel
  generate_fs_translations
  "$VENV_PYTHON" "$SETUP_PY"
fi
