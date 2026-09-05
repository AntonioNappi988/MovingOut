#!/usr/bin/env bash
# Builds a .deb package for MovingOut, installable with:
#   sudo apt install ./movout_<version>_all.deb
# or
#   sudo dpkg -i movout_<version>_all.deb
set -euo pipefail

VERSION="1.0.0"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_DIR="$(mktemp -d)"
trap 'rm -rf "$PKG_DIR"' EXIT

install -d "$PKG_DIR/DEBIAN"
install -d "$PKG_DIR/usr/lib/movout"
install -d "$PKG_DIR/usr/bin"
install -d "$PKG_DIR/usr/share/man/man1"
install -d "$PKG_DIR/usr/share/doc/movout"

cp -r "$ROOT_DIR/movout" "$PKG_DIR/usr/lib/movout/"
cp "$ROOT_DIR/man/movout.1" "$PKG_DIR/usr/share/man/man1/movout.1"
gzip -n -9 "$PKG_DIR/usr/share/man/man1/movout.1"
cp "$ROOT_DIR/LICENSE" "$PKG_DIR/usr/share/doc/movout/copyright"

cat > "$PKG_DIR/usr/bin/movout" <<'EOF'
#!/usr/bin/env bash
export PYTHONPATH="/usr/lib/movout:${PYTHONPATH:-}"
exec python3 -m movout "$@"
EOF
chmod +x "$PKG_DIR/usr/bin/movout"

cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: movout
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3
Maintainer: Antonio Nappi <https://github.com/AntonioNappi988>
Homepage: https://github.com/AntonioNappi988/movingout
Description: Linux distro-hopping / porting tool
 MovingOut (movout) scans installed packages, systemd services and custom
 scripts on the current machine and generates a single self-installing .sh
 script to reproduce them on a new machine, same distro or a different one.
EOF

OUT="$ROOT_DIR/movout_${VERSION}_all.deb"
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT"
echo "Built: $OUT"
echo "Install with: sudo apt install $OUT   (or: sudo dpkg -i $OUT)"
