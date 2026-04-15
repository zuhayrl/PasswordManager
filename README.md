# Password Manager

A secure, encrypted password vault implementation using industry-standard cryptographic algorithms.

## Overview

This password manager encrypts passwords using a master passphrase. The key is derived from your passphrase each time, meaning passwords cannot be decrypted without the correct passphrase. The encryption key is never stored on disk.

## How It Works

### Security Architecture

The system uses two cryptographic components:

1. **Argon2** - A memory-hard key derivation function that converts your master passphrase into a cryptographic key
   - Resistant to brute-force attacks due to high memory and computational requirements
   - Time cost: 3 iterations
   - Memory cost: 65536 KB (~64 MB)
   - Parallelism: 2 threads
   - Output: 32-byte key for AES-256

2. **AES-GCM** - Authenticated encryption algorithm
   - Provides both confidentiality (encryption) and authenticity (integrity checking)
   - 12-byte random nonce generated for each encryption
   - Fails with incorrect passphrase (authentication tag won't match)

### Data Flow

**Saving:**
```
Master Passphrase + Random Salt
         ↓
    [Argon2 Hashing]
         ↓
    Encryption Key (32 bytes)
         ↓
    [AES-GCM Encryption with Random Nonce]
         ↓
Password Dictionary → JSON → Encrypted Ciphertext
         ↓
Vault File: [Salt (16 bytes)][Nonce (12 bytes)][Ciphertext]
```

**Loading:**
```
Vault File: [Salt][Nonce][Ciphertext]
         ↓
Extract: salt, nonce, ciphertext
         ↓
Master Passphrase + Extracted Salt
         ↓
    [Argon2 Hashing]
         ↓
    Same Encryption Key
         ↓
    [AES-GCM Decryption & Authentication]
         ↓
Plaintext JSON → Password Dictionary
(Fails if passphrase is wrong)
```

## Installation

Install required dependencies:

```bash
pip install argon2-cffi cryptography
```

## Usage

### Basic Example

```python
from Test import save_vault, load_vault

# Define your passwords
passwords = {
    "gmail": "mypassword123",
    "github": "github_token_abc",
    "bank": "secure_pin_456"
}

# Save vault with master passphrase
save_vault("MyMasterPassword", passwords, "vault.bin")

# Load vault (need correct passphrase)
loaded = load_vault("MyMasterPassword", "vault.bin")
print(loaded)  # {"gmail": "...", "github": "...", "bank": "..."}
```

### Handling Wrong Passphrase

```python
try:
    data = load_vault("WrongPassword", "vault.bin")
except Exception as e:
    print(f"Access denied: {type(e).__name__}")
    # AES-GCM authentication fails with wrong passphrase
```

### Updating Passwords

```python
# Load existing vault
passwords = load_vault("MyMasterPassword", "vault.bin")

# Add or modify passwords
passwords["twitter"] = "new_twitter_password"
passwords["gmail"] = "updated_password"

# Save updated vault
save_vault("MyMasterPassword", passwords, "vault.bin")
```

## Security Features

- ✅ **Random Salt** - Each vault gets a unique salt, preventing rainbow table attacks
- ✅ **Random Nonce** - Each encryption uses a fresh nonce, required for AES-GCM security
- ✅ **Authentication** - AES-GCM detects tampering or corruption
- ✅ **Memory-Hard Hashing** - Argon2 resists GPU-accelerated attacks
- ✅ **No Key Storage** - Encryption key is derived from passphrase, never stored

## API Reference

### `derive_key(passphrase: str, salt: bytes) -> bytes`
Derives a 32-byte encryption key from a passphrase using Argon2.

**Parameters:**
- `passphrase`: Master password (string)
- `salt`: Random bytes for key derivation (16 bytes)

**Returns:** 32-byte encryption key

### `save_vault(passphrase: str, data: dict, path: str)`
Encrypts and saves password data to a file.

**Parameters:**
- `passphrase`: Master password (string)
- `data`: Dictionary of passwords (e.g., `{"service": "password"}`)
- `path`: File path to save vault (string)

**Returns:** None (writes binary file)

### `load_vault(passphrase: str, path: str) -> dict`
Decrypts and loads password data from a vault file.

**Parameters:**
- `passphrase`: Master password (string)
- `path`: File path of vault (string)

**Returns:** Dictionary of passwords

**Raises:**
- `InvalidTag` - If passphrase is incorrect
- `FileNotFoundError` - If vault file doesn't exist
- `JSONDecodeError` - If vault data is corrupted

## File Format

Vault files are binary with the following structure:

```
Byte Position | Length | Content
0-15          | 16     | Salt (used by Argon2)
16-27         | 12     | Nonce (used by AES-GCM)
28+           | var    | Ciphertext (encrypted JSON data)
```

## Running the Example

The `Test.py` file includes a complete working example:

```bash
python3 Test.py
```

This demonstrates:
1. Creating and saving a vault
2. Loading with correct passphrase
3. Handling authentication failure
4. Updating and re-encrypting the vault
5. Verifying changes