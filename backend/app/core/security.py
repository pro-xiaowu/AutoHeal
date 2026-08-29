from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import Settings


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_context.verify(password, password_hash)


def create_access_token(subject: str, role: str, settings: Settings) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        claims = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except (JWTError, ValueError, TypeError) as exc:
        raise ValueError("Invalid authentication token") from exc
    if not claims.get("sub"):
        raise ValueError("Invalid authentication token")
    return claims


def _fernet(settings: Settings) -> Fernet:
    try:
        return Fernet(settings.fernet_key)
    except (ValueError, TypeError) as exc:
        raise ValueError("FERNET_KEY must be a valid Fernet key") from exc


def encrypt_secret(value: str, settings: Settings) -> str:
    if value.startswith("fernet:"):
        return value
    encrypted = _fernet(settings).encrypt(value.encode("utf-8")).decode("ascii")
    return f"fernet:{encrypted}"


def decrypt_secret(value: str, settings: Settings) -> str:
    if not value.startswith("fernet:"):
        return value
    encrypted = value.removeprefix("fernet:")
    try:
        return _fernet(settings).decrypt(encrypted.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
        raise ValueError("Unable to decrypt secret") from exc
