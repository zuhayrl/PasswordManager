#!/usr/bin/env bash
set -euo pipefail

APP_NAME="password-manager"
ENTRYPOINT="main.py"

if [[ ! -f "$ENTRYPOINT" ]]; then
  echo "Error: $ENTRYPOINT was not found in $(pwd)"
  exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

python3 -m PyInstaller \
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
