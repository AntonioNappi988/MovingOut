#!/usr/bin/env bash
# MovingOut installer (command: movout)
# Works out of the box: if python3 (or its curses module) is missing, it is
# installed automatically using whatever package manager this distro has.
set -euo pipefail

PREFIX="/usr/local/lib/movout"
BIN="/usr/local/bin/movout"
MAN_DIR="/usr/local/share/man/man1"

detect_pm() {
  if command -v apt-get >/dev/null 2>&1; then echo apt
  elif command -v dnf >/dev/null 2>&1; then echo dnf
  elif command -v yum >/dev/null 2>&1; then echo yum
  elif command -v pacman >/dev/null 2>&1; then echo pacman
  elif command -v zypper >/dev/null 2>&1; then echo zypper
  elif command -v apk >/dev/null 2>&1; then echo apk
  else echo unknown
  fi
}

install_pkg() {
  local pm="$1"; shift
  case "$pm" in
    apt)    sudo apt-get update -y && sudo apt-get install -y "$@" ;;
    dnf)    sudo dnf install -y "$@" ;;
    yum)    sudo yum install -y "$@" ;;
    pacman) sudo pacman -Sy --noconfirm --needed "$@" ;;
    zypper) sudo zypper --non-interactive install "$@" ;;
    apk)    sudo apk add "$@" ;;
    *)      return 1 ;;
  esac
}

PM="$(detect_pm)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found on this system."
  if [ "$PM" = "unknown" ]; then
    echo "Error: no supported package manager (apt/dnf/yum/pacman/zypper/apk) was detected." >&2
    echo "Please install python3 manually and re-run this script." >&2
    exit 1
  fi
  echo "Installing it automatically via $PM ..."
  PKG_NAME="python3"
  [ "$PM" = "pacman" ] && PKG_NAME="python"
  if install_pkg "$PM" "$PKG_NAME"; then
    echo ">>> python3 was not installed -- MovingOut installed it automatically via $PM."
  else
    echo "Error: automatic installation of python3 failed. Please install it manually and re-run this script." >&2
    exit 1
  fi
fi

if ! python3 -c "import curses" >/dev/null 2>&1; then
  echo "The python3 'curses' module was not found. Attempting automatic install..."
  CURSES_PKG=""
  case "$PM" in
    apk) CURSES_PKG="py3-curses" ;;   # Alpine ships it as a separate package
    apt) CURSES_PKG="python3" ;;      # reinstalling/upgrading python3 covers it on Debian/Ubuntu
    *)   CURSES_PKG="" ;;
  esac
  if [ -n "$CURSES_PKG" ]; then
    install_pkg "$PM" "$CURSES_PKG" || true
  fi
  if ! python3 -c "import curses" >/dev/null 2>&1; then
    echo "Error: python3 'curses' module is still not available." >&2
    echo "This is unusual, curses ships with python3 on virtually all distros -- check your python3 install." >&2
    exit 1
  fi
  echo ">>> python3 'curses' module was missing -- MovingOut installed it automatically."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing MovingOut to $PREFIX ..."
sudo mkdir -p "$PREFIX" "$MAN_DIR"
sudo cp -r "$SCRIPT_DIR/movout" "$PREFIX/"

sudo tee "$BIN" > /dev/null <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$PREFIX:\${PYTHONPATH:-}"
exec python3 -m movout "\$@"
EOF
sudo chmod +x "$BIN"

if [ -f "$SCRIPT_DIR/man/movout.1" ]; then
  sudo cp "$SCRIPT_DIR/man/movout.1" "$MAN_DIR/movout.1"
  sudo mandb >/dev/null 2>&1 || sudo makewhatis "$(dirname "$MAN_DIR")" >/dev/null 2>&1 || true
fi

echo "Done. Run: movout"
echo "  movout        -> open the interactive TUI (same as movout -s)"
echo "  movout -c     -> print a scan summary without generating anything"
echo "  movout -h     -> full option list"
echo "  man movout    -> full manual and TUI keybindings"
