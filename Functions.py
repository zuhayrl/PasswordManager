# Password Manager - Secure Vault Implementation

from argon2.low_level import hash_secret_raw, Type  # Argon2 for key derivation
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # AES-GCM for encryption
import os, json, base64  # os for random bytes, json for serialization, base64 for encoding

# Configuration constants
SALT_SIZE = 16      # 16 bytes of random salt for Argon2
NONCE_SIZE = 12     # 12 bytes of random nonce for AES-GCM

# Derive Key
def derive_key(passphrase: str, salt: bytes) -> bytes:
    # Convert passphrase into a 32-byte encryption key using Argon2
    # Argon2 is memory-hard: resists brute-force and GPU attacks
    # time_cost=3: iterations, memory_cost=65536: ~64MB, parallelism=2: threads
    return hash_secret_raw(
        secret=passphrase.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,  # 32 bytes = 256-bit key for AES-256
        type=Type.I
    )

# Encrypt Password
def encrypt_password(password: str, key: bytes) -> tuple:
    # Encrypt a single password with AES-GCM, return (nonce, ciphertext) as base64 strings
    nonce = os.urandom(NONCE_SIZE)  # Fresh nonce for each password
    ciphertext = AESGCM(key).encrypt(nonce, password.encode(), None)
    # Return base64-encoded strings for JSON storage
    return base64.b64encode(nonce).decode(), base64.b64encode(ciphertext).decode()

# Decrypt Password
def decrypt_password(nonce_b64: str, ciphertext_b64: str, key: bytes) -> str:
    # Decrypt a single password using AES-GCM, takes base64-encoded strings
    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    return plaintext.decode()

# Create Vault
def create_vault(passphrase: str, path: str) -> None:
    # Create an empty vault file
    salt = os.urandom(SALT_SIZE)
    vault_data = {
        "salt": base64.b64encode(salt).decode(),
        "entries": []
    }
    with open(path, "w") as f:
        json.dump(vault_data, f, indent=2)

# Load Vault
def load_vault(passphrase: str, path: str) -> dict:
    # Load vault structure and return the key + vault data for manipulation
    with open(path, "r") as f:
        vault_data = json.load(f)
    
    # Decode salt from base64 and derive the master key
    salt = base64.b64decode(vault_data["salt"])
    key = derive_key(passphrase, salt)

    # Verify the passphrase against an existing entry when possible.
    entries = vault_data.get("entries", [])
    if entries:
        first_entry = entries[0]
        decrypt_password(first_entry["password_nonce"], first_entry["password_ciphertext"], key)
    
    return {"key": key, "data": vault_data}

# Save Vault
def save_vault(vault: dict, path: str) -> None:
    # Save vault to file (encrypted passwords are already in the data)
    with open(path, "w") as f:
        json.dump(vault["data"], f, indent=2)

# Add Credential
def add_credential(vault: dict, service: str, username: str, password: str) -> None:
    # Add or update a credential in the vault (in memory)
    key = vault["key"]
    
    # Encrypt the password with a fresh nonce
    nonce_b64, ciphertext_b64 = encrypt_password(password, key)
    
    # Find existing entry for this service
    entry = None
    for e in vault["data"]["entries"]:
        if e["service"] == service:
            entry = e
            break
    
    if entry:
        # Update existing entry
        entry["username"] = username
        entry["password_nonce"] = nonce_b64
        entry["password_ciphertext"] = ciphertext_b64
    else:
        # Create new entry
        vault["data"]["entries"].append({
            "service": service,
            "username": username,
            "password_nonce": nonce_b64,
            "password_ciphertext": ciphertext_b64
        })

# Remove Credential
def remove_credential(vault: dict, service: str) -> bool:
    # Remove a credential from the vault (in memory). Returns True if found and removed
    for i, entry in enumerate(vault["data"]["entries"]):
        if entry["service"] == service:
            vault["data"]["entries"].pop(i)
            return True
    return False

# Get Credential
def get_credential(vault: dict, service: str) -> dict:
    # Get a decrypted credential from the vault
    key = vault["key"]
    
    for entry in vault["data"]["entries"]:
        if entry["service"] == service:
            # Decrypt the password
            password = decrypt_password(entry["password_nonce"], entry["password_ciphertext"], key)
            return {
                "service": service,
                "username": entry["username"],
                "password": password
            }
    return None

# List Credentials
def list_credentials(vault: dict) -> list:
    # List all credentials (username + service, passwords not shown)
    return [
        {
            "service": entry["service"],
            "username": entry["username"]
        }
        for entry in vault["data"]["entries"]
    ]


if __name__ == "__main__":
    # Example usage
    """
    master_password = "SuperSecurePassphrase123!"
    vault_file = "passwords.vault"
    
    print("=" * 60)
    print("PASSWORD MANAGER - EXAMPLE USAGE")
    print("=" * 60)
    
    # Step 1: Create an empty vault
    print("\n[1] Creating empty vault...")
    create_vault(master_password, vault_file)
    print(f"✓ Vault created at '{vault_file}'")
    
    # Step 2: Load and add credentials
    print("\n[2] Loading vault and adding credentials...")
    vault = load_vault(master_password, vault_file)
    add_credential(vault, "gmail", "user@gmail.com", "secure_gmail_password_123")
    add_credential(vault, "github", "myusername", "github_token_abc123xyz")
    add_credential(vault, "linkedin", "john.doe", "linkedin_pass_456")
    add_credential(vault, "bank", "account_id_789", "bank_pin_7890")
    save_vault(vault, vault_file)
    print(f"✓ Added 4 credentials to vault")
    
    # Step 3: List all credentials (usernames visible, passwords hidden)
    print("\n[3] Listing all stored credentials...")
    vault = load_vault(master_password, vault_file)
    print("  Stored credentials:")
    for cred in list_credentials(vault):
        print(f"    - {cred['service']}: {cred['username']}")
    
    # Step 4: Retrieve a single credential
    print("\n[4] Retrieving specific credential...")
    cred = get_credential(vault, "gmail")
    print(f"  Service: {cred['service']}")
    print(f"  Username: {cred['username']}")
    print(f"  Password: {cred['password']}")
    
    # Step 5: Add a single new credential
    print("\n[5] Adding a new credential without re-encrypting vault...")
    add_credential(vault, "twitter", "john_doe", "twitter_pass_999")
    save_vault(vault, vault_file)
    print(f"✓ Added twitter credential")
    print(f"  Total credentials: {len(list_credentials(vault))}")
    
    # Step 6: Update an existing credential
    print("\n[6] Updating an existing credential...")
    add_credential(vault, "github", "mynewusername", "new_github_token_xyz789")
    save_vault(vault, vault_file)
    cred = get_credential(vault, "github")
    print(f"✓ Updated github credential")
    print(f"  New username: {cred['username']}")
    print(f"  New password: {cred['password']}")
    
    # Step 7: Remove a credential
    print("\n[7] Removing a credential...")
    remove_credential(vault, "linkedin")
    save_vault(vault, vault_file)
    print(f"✓ Removed linkedin credential")
    print(f"  Remaining credentials: {len(list_credentials(vault))}")
    
    # Step 8: Verify with wrong passphrase
    print("\n[8] Attempting to load vault with WRONG passphrase...")
    try:
        wrong_vault = load_vault("WrongPassword", vault_file)
        # Trying to decrypt a password with wrong key will fail
        cred = get_credential(wrong_vault, "gmail")
    except Exception as e:
        print(f"✗ Access denied: {type(e).__name__}")
        print(f"  (Cannot decrypt with incorrect passphrase)")
    
    print("\n" + "=" * 60)
    print("✓ All operations completed successfully!")
    print("=" * 60)
    """
