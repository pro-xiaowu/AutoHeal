import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    verify_password,
)
from app.core.settings import Settings


def test_password_hash_round_trip_and_rejects_wrong_password():
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_jwt_contains_subject_and_role():
    settings = Settings(_env_file=None, secret_key="test-secret")
    token = create_access_token("user-1", "admin", settings)

    claims = decode_access_token(token, settings)

    assert claims["sub"] == "user-1"
    assert claims["role"] == "admin"
    assert "exp" in claims


def test_invalid_jwt_raises_controlled_exception():
    settings = Settings(_env_file=None, secret_key="test-secret")

    with pytest.raises(ValueError, match="Invalid authentication token"):
        decode_access_token("not-a-jwt", settings)


def test_secret_encryption_round_trip_is_prefixed_and_not_plaintext():
    settings = Settings(
        _env_file=None,
        fernet_key="0Vv2P6W3Jj3X7P0zZt3Tq1b6c4l5w2x8s9d0f1g2h3i=",
    )
    encrypted = encrypt_secret("sk-test", settings)

    assert encrypted.startswith("fernet:")
    assert "sk-test" not in encrypted
    assert decrypt_secret(encrypted, settings) == "sk-test"
