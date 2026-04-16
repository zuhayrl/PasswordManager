# Password Manager

Terminal-based password manager with encrypted vault storage.

It uses a master passphrase to derive an encryption key at runtime. The passphrase is not written to disk.

## Features

- Encrypted vault with per-entry password encryption.
- Add, update, remove, and reveal credentials from a Textual UI.
- Keyboard shortcuts for fast navigation.
- Standalone executable builds for shipping to users.

## Security Model

This project uses:

- Argon2id-style key derivation (via `argon2-cffi`) to derive a 32-byte key from your passphrase.
- AES-GCM authenticated encryption (via `cryptography`) for credential password fields.
- Random per-vault salt and random nonce per encrypted password.

What is stored:

- `passwords.vault` stores metadata and encrypted credential payloads.
- The passphrase itself is not stored in the vault file.

What is not stored:

- The passphrase is entered during sensitive actions and used in memory.
- No "remember passphrase" behavior is implemented.

## Project Structure

- `main.py`: Textual app (UI, flows, actions, key bindings).
- `Functions.py`: crypto and vault operations.
- `passwords.vault`: local vault file (ignored by git).
- `build_release.sh`: one-command build for standalone executable.
- `requirements.txt`: Python dependencies.

## Requirements

- Python 3.10+
- Linux, macOS, or Windows
- **Debian/Ubuntu only**: `python3-venv` (automatically installed by build script if missing)

## Local Development Setup

```bash
pip install -r requirements.txt
```

## Run The App

```bash
python3 main.py
```

On first use:

1. Choose **Add**.
2. Enter service, username, password.
3. If no vault exists yet, set a new master passphrase.

For existing vaults:

- Add/Remove/Reveal actions prompt for the passphrase.

## Keyboard Shortcuts

- `a`: Add credential
- `delete`: Remove selected credential
- `p`: Reveal selected password
- `r`: Refresh vault view
- `q`: Quit

## Standalone Shipping (No Python Required For End User)

Build a single-file executable with PyInstaller:

```bash
bash build_release.sh
```

The build script automatically creates a temporary virtual environment, installs dependencies, builds the executable, and cleans up.

- Linux: `dist/password-manager`
- macOS: `dist/password-manager`
- Windows: `dist/password-manager.exe`

Distribution notes:

- Build on each target OS/architecture you want to support.
- Do not expect a Linux build to run on Windows/macOS.
- Ships only the executable; does not bundle personal vault data.

## Multi-Device Usage

If you want one vault across multiple devices:

1. Keep `passwords.vault` in a synced folder (for example: Dropbox, OneDrive, iCloud Drive, Syncthing).
2. Run the app on each device.
3. Use the same passphrase everywhere.

Recommended:

- Ensure only one device writes to the vault at a time to avoid sync conflicts.

```

## Troubleshooting

### "Incorrect passphrase or unreadable vault"

- Verify you entered the correct passphrase.
- Confirm `passwords.vault` is valid JSON and not corrupted by sync conflicts.

### Build command fails

- Activate your virtual environment.
- Reinstall dependencies: `pip install -r requirements.txt`.
- Check your Python version (`python3 --version`).

### App runs but no credentials appear

- Confirm you are opening the expected `passwords.vault` file in the current working directory.

## Development Notes

- Keep `passwords.vault` out of source control.
- Keep passphrase handling ephemeral and in memory.
- Review cryptography dependency updates regularly.