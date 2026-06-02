from app.core.security import encrypt_aes, decrypt_aes


def encrypt_sensitive_data(plaintext: str) -> str:
    return encrypt_aes(plaintext)


def decrypt_sensitive_data(encrypted: str) -> str:
    return decrypt_aes(encrypted)
