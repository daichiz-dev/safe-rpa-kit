"""Secret encryption helper built on Fernet (symmetric authenticated crypto).

Credentials used by automation (target passwords, API tokens) should never sit
in config files or a database as plaintext. This wraps :mod:`cryptography`'s
Fernet with two conveniences:

1. A version prefix (``enc:v1:``) on every ciphertext, so you can evolve the
   scheme later and tell encrypted values apart from plaintext at a glance.
2. Backward-compatible decryption: a value *without* the prefix is assumed to be
   legacy plaintext and returned as-is. This lets you roll encryption out to an
   existing store gradually instead of in one risky migration.

The key comes from an explicit argument or an environment variable. Generate one
with :func:`generate_key`.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken

from .errors import DecryptionError

#: Prefix marking a value encrypted by this module, version 1.
ENC_PREFIX = "enc:v1:"

#: Environment variable read when no key is passed explicitly.
KEY_ENV = "SAFE_RPA_FERNET_KEY"


def generate_key() -> str:
    """Return a fresh URL-safe base64 Fernet key as a str."""
    return Fernet.generate_key().decode("ascii")


def _resolve_key(key: str | bytes | None, key_env: str) -> bytes:
    if key is None:
        key = os.environ.get(key_env)
    if not key:
        raise DecryptionError(
            f"No Fernet key provided and {key_env} is unset. Pass key=... or "
            f"set the environment variable."
        )
    return key.encode("ascii") if isinstance(key, str) else key


class SecretBox:
    """Encrypt/decrypt secrets with a versioned, plaintext-tolerant scheme."""

    def __init__(self, key: str | bytes | None = None, key_env: str = KEY_ENV) -> None:
        self._fernet = Fernet(_resolve_key(key, key_env))

    def encrypt(self, plaintext: str) -> str:
        """Return ``enc:v1:<token>`` for the given plaintext string."""
        token = self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return ENC_PREFIX + token

    def decrypt(self, value: str) -> str:
        """Decrypt a value produced by :meth:`encrypt`.

        A value that lacks the ``enc:v1:`` prefix is treated as legacy plaintext
        and returned unchanged (backward compatibility).
        """
        if not value.startswith(ENC_PREFIX):
            return value  # legacy plaintext, transparently passed through
        token = value[len(ENC_PREFIX):].encode("ascii")
        try:
            return self._fernet.decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            raise DecryptionError(
                "Failed to decrypt value: wrong key or corrupted ciphertext."
            ) from exc

    @staticmethod
    def is_encrypted(value: str) -> bool:
        """True if the value carries this module's encryption prefix."""
        return value.startswith(ENC_PREFIX)
