"""Exception types for safe-rpa-kit.

All errors here are designed to *fail closed*: when the framework is unsure
whether a write is safe, it raises rather than proceeding silently.
"""


class SafeRpaError(Exception):
    """Base class for all safe-rpa-kit errors."""


class WriteGateBlocked(SafeRpaError, RuntimeError):
    """Raised when a real write is attempted while the global write gate is off.

    Inherits from RuntimeError so callers that broadly catch RuntimeError
    (a common pattern in automation harnesses) still stop.
    """


class VerificationError(SafeRpaError):
    """Raised when a post-write read-back does not match what was written."""


class DecryptionError(SafeRpaError):
    """Raised when a value cannot be decrypted (bad key or corrupt payload)."""
