import pytest

from safe_rpa import ENC_PREFIX, DecryptionError, SecretBox, generate_key


def test_round_trip():
    box = SecretBox(key=generate_key())
    token = box.encrypt("s3cr3t")
    assert token.startswith(ENC_PREFIX)
    assert box.decrypt(token) == "s3cr3t"


def test_ciphertext_is_not_plaintext():
    box = SecretBox(key=generate_key())
    token = box.encrypt("s3cr3t")
    assert "s3cr3t" not in token


def test_plaintext_passthrough_backward_compat():
    box = SecretBox(key=generate_key())
    # A legacy, unprefixed value decrypts to itself.
    assert box.decrypt("legacy-plaintext") == "legacy-plaintext"


def test_is_encrypted():
    box = SecretBox(key=generate_key())
    token = box.encrypt("x")
    assert SecretBox.is_encrypted(token) is True
    assert SecretBox.is_encrypted("nope") is False


def test_wrong_key_raises():
    token = SecretBox(key=generate_key()).encrypt("x")
    other = SecretBox(key=generate_key())
    with pytest.raises(DecryptionError):
        other.decrypt(token)


def test_key_from_env(monkeypatch):
    monkeypatch.setenv("SAFE_RPA_FERNET_KEY", generate_key())
    box = SecretBox()
    assert box.decrypt(box.encrypt("hi")) == "hi"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("SAFE_RPA_FERNET_KEY", raising=False)
    with pytest.raises(DecryptionError):
        SecretBox()
