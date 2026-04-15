# Password Manager

from cryptography.hazmat.primitives.kdf.argon2 import Argon2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, json

SALT_SIZE = 16
NONCE_SIZE = 12

def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = Argon2(
        time_cost=3, memory_cost=65536, parallelism=2,
        hash_len=32, salt=salt
    )
    return kdf.derive(passphrase.encode())

def save_vault(passphrase: str, data: dict, path: str):
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(nonce, json.dumps(data).encode(), None)
    with open(path, "wb") as f:
        f.write(salt + nonce + ciphertext)

def load_vault(passphrase: str, path: str) -> dict:
    with open(path, "rb") as f:
        blob = f.read()
    salt, nonce, ciphertext = blob[:16], blob[16:28], blob[28:]
    key = derive_key(passphrase, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)  # raises if wrong passphrase
    return json.loads(plaintext)


if __name__ == "__main__":
    print("test")