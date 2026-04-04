import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    key = get_settings().ENCRYPTION_KEY
    # Ensure key is valid Fernet format (32 url-safe base64-encoded bytes)
    try:
        Fernet(key.encode())
        return Fernet(key.encode())
    except (ValueError, Exception):
        # Derive a valid Fernet key from whatever string was provided
        derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        return Fernet(derived)


def encrypt_api_key(plaintext: str) -> str:
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    f = _get_fernet()
    try:
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        return ""


def mask_api_key(plaintext: str) -> str:
    if len(plaintext) <= 8:
        return "*" * len(plaintext)
    return plaintext[:4] + "*" * (len(plaintext) - 8) + plaintext[-4:]
