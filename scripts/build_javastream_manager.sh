#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
COMMON_DIR="$BUILD_DIR/common"
APP_DIR="$COMMON_DIR/opt/javastream"
VENV_DIR="$APP_DIR/venv"
APP_CODE_DIR="$APP_DIR/app"
MANAGER_DIR="$APP_DIR/manager"
BIN_DIR="$APP_DIR/bin"

VERSION=$(python3 - <<'PY'
import tomllib
from pathlib import Path
pyproject = tomllib.loads(Path("pyproject.toml").read_text())
print(pyproject.get("project", {}).get("version", "0.1.0"))
PY
)

rm -rf "$BUILD_DIR"
mkdir -p "$APP_CODE_DIR" "$MANAGER_DIR" "$BIN_DIR"

cp -a "$ROOT_DIR/comet" "$APP_CODE_DIR/"
cp -a "$ROOT_DIR/README.md" "$APP_CODE_DIR/"
cp -a "$ROOT_DIR/LICENSE" "$APP_CODE_DIR/"
cp -a "$ROOT_DIR/pyproject.toml" "$APP_CODE_DIR/"

cp -a "$ROOT_DIR/manager/javastream_manager.py" "$MANAGER_DIR/"
cp -a "$ROOT_DIR/manager/assets/javastream.svg" "$MANAGER_DIR/"

REQ_FILE="$BUILD_DIR/requirements.txt"
python3 - <<'PY' > "$REQ_FILE"
import tomllib
from pathlib import Path
pyproject = tomllib.loads(Path("pyproject.toml").read_text())
for dep in pyproject.get("project", {}).get("dependencies", []):
    print(dep)
PY

if command -v uv >/dev/null 2>&1; then
  uv venv "$VENV_DIR"
  VENV_PY="$VENV_DIR/bin/python"
  uv pip install --python "$VENV_PY" -r "$REQ_FILE"
else
  python3 -m venv "$VENV_DIR"
  VENV_PY="$VENV_DIR/bin/python"
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install -r "$REQ_FILE"
fi

cat <<'EOF_SCRIPT' > "$BIN_DIR/javastream-manager"
#!/usr/bin/env bash
set -euo pipefail
SOURCE_PATH="${BASH_SOURCE[0]}"
while [ -L "$SOURCE_PATH" ]; do
  SOURCE_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
  SOURCE_PATH="$(readlink "$SOURCE_PATH")"
  [[ "$SOURCE_PATH" != /* ]] && SOURCE_PATH="$SOURCE_DIR/$SOURCE_PATH"
done
ROOT_DIR="$(cd "$(dirname "$SOURCE_PATH")/.." && pwd)"
export JAVASTREAM_APP_ROOT="$ROOT_DIR/app"
export PYTHONPATH="$ROOT_DIR/app"
if ! "$ROOT_DIR/venv/bin/python" - <<'PY'
try:
    import tkinter  # noqa: F401
except Exception as exc:
    raise SystemExit(str(exc))
PY
then
  echo "JavaStream Manager requires tkinter support." 1>&2
  echo "Install python3-tk (Debian/Ubuntu) or tk (Fedora/Arch), then retry." 1>&2
  exit 1
fi
exec "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/manager/javastream_manager.py"
EOF_SCRIPT

cat <<'EOF_SCRIPT' > "$BIN_DIR/javastream-server"
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/app"
export FASTAPI_HOST="${FASTAPI_HOST:-127.0.0.1}"
export FASTAPI_PORT="${FASTAPI_PORT:-8000}"
export DATABASE_PATH="${DATABASE_PATH:-$HOME/.local/share/javastream/javastream.db}"
exec "$ROOT_DIR/venv/bin/python" -m comet.main
EOF_SCRIPT

chmod +x "$BIN_DIR/javastream-manager" "$BIN_DIR/javastream-server"

TAR_DIR="$BUILD_DIR/tar"
mkdir -p "$TAR_DIR"
cp -a "$APP_DIR" "$TAR_DIR/javastream"
tar -czf "$BUILD_DIR/JavaStream-Manager-$VERSION.tar.gz" -C "$TAR_DIR" javastream

DEB_DIR="$BUILD_DIR/deb"
mkdir -p "$DEB_DIR/DEBIAN" "$DEB_DIR/opt" "$DEB_DIR/usr/bin" \
  "$DEB_DIR/usr/share/applications" "$DEB_DIR/usr/share/icons/hicolor/scalable/apps"

cp -a "$APP_DIR" "$DEB_DIR/opt/javastream"
ln -s /opt/javastream/bin/javastream-manager "$DEB_DIR/usr/bin/javastream-manager"
cp -a "$ROOT_DIR/manager/assets/javastream-manager.desktop" "$DEB_DIR/usr/share/applications/"
cp -a "$ROOT_DIR/manager/assets/javastream.svg" "$DEB_DIR/usr/share/icons/hicolor/scalable/apps/"

cat <<EOF_CTRL > "$DEB_DIR/DEBIAN/control"
Package: javastream-manager
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: JavaStream
Depends: python3 (>= 3.11), python3-tk
Description: JavaStream Manager controls the JavaStream server and dashboard.
EOF_CTRL

chmod 0755 "$DEB_DIR/DEBIAN"
chmod 0644 "$DEB_DIR/DEBIAN/control"

dpkg-deb --build "$DEB_DIR" "$BUILD_DIR/JavaStream-Manager-$VERSION.deb"

APPDIR="$BUILD_DIR/appimage/AppDir"
mkdir -p "$APPDIR/usr"
cp -a "$DEB_DIR/opt" "$APPDIR/usr/"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps"

ln -s ../opt/javastream/bin/javastream-manager "$APPDIR/usr/bin/javastream-manager"
cp -a "$ROOT_DIR/manager/assets/javastream-manager.desktop" "$APPDIR/usr/share/applications/"
cp -a "$ROOT_DIR/manager/assets/javastream.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/"

cp -a "$ROOT_DIR/manager/assets/javastream-manager.desktop" "$APPDIR/javastream-manager.desktop"
cp -a "$ROOT_DIR/manager/assets/javastream.svg" "$APPDIR/javastream.svg"

cat <<'EOF_RUN' > "$APPDIR/AppRun"
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$HERE/usr/bin/javastream-manager"
EOF_RUN
chmod +x "$APPDIR/AppRun"

APPIMAGETOOL="$(command -v appimagetool || true)"
if [[ -z "$APPIMAGETOOL" ]]; then
  APPIMAGETOOL="$BUILD_DIR/appimagetool.AppImage"
  curl -L -o "$APPIMAGETOOL" \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x "$APPIMAGETOOL"
fi

APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$BUILD_DIR/JavaStream-Manager-$VERSION.AppImage"

echo "Build complete:"
echo "- $BUILD_DIR/JavaStream-Manager-$VERSION.tar.gz"
echo "- $BUILD_DIR/JavaStream-Manager-$VERSION.deb"
echo "- $BUILD_DIR/JavaStream-Manager-$VERSION.AppImage"
