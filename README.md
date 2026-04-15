# PasswordManager

Uses a memory based hash/key to encrypt, cant be decrypted without the hash/key, and the key isn't stored

SAVE:   passphrase + salt → [Argon2] → key → [AES-GCM + nonce] → ciphertext → disk  
LOAD:   disk → split → salt + nonce + ciphertext
        passphrase + salt → [Argon2] → same key → [AES-GCM verify] → plaintext