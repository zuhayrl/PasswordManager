#!/usr/bin/env bash
set -euo pipefail

APP_NAME="password-manager"
ENTRYPOINT="main.py"
VENV_DIR=".build_venv"

if [[ ! -f "$ENTRYPOINT" ]]; then
  echo "Error: $ENTRYPOINT was not found in $(pwd)"
  exit 1
fi

# Check if python3-venv is installed (Debian/Ubuntu requirement)
if ! python3 -m venv --help &>/dev/null; then
  echo "Installing python3-venv (required for build)..."
  sudo apt-get update && sudo apt-get install -y python3-venv
fi

# Create temporary venv for build
echo "Creating temporary build environment..."
python3 -m venv "$VENV_DIR"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# Cleanup function
cleanup() {
  echo "Cleaning up build environment..."
  rm -rf "$VENV_DIR"
}
trap cleanup EXIT

# Install dependencies in venv
echo "Installing dependencies..."
"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install -r requirements.txt

echo "Building executable..."
"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name "$APP_NAME" \
  "$ENTRYPOINT"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    OUTPUT_PATH="dist/${APP_NAME}.exe"
    ;;
  *)
    OUTPUT_PATH="dist/${APP_NAME}"
    ;;
esac

echo
if [[ -f "$OUTPUT_PATH" ]]; then
  echo "Build complete: $OUTPUT_PATH"
  echo "Ship this binary to users on the SAME OS/architecture you built on."
else
  echo "Build finished, but output path was not found. Check dist/."
fi
