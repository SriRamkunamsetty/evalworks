import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from evalworks.config import settings

_key = base64.urlsafe_b64encode(hashlib.sha256(settings.data_encryption_key.encode()).digest())
_fernet = Fernet(_key)


def encrypt_secret(value: str) -> str:
    return _fernet.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    try:
        return _fernet.decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise ValueError("Stored encrypted secret cannot be decrypted") from exc
