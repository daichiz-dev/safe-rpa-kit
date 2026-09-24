"""safe-rpa-kit: safe-by-default browser automation writes.

Three guarantees, first-class from the start:
  * dry-run is the default for every write;
  * a global write gate must be explicitly enabled for real writes;
  * every real write is read back and verified, or the call fails closed.
"""

from .adapter import BaseAdapter, WriteResult
from .crypto import ENC_PREFIX, KEY_ENV, SecretBox, generate_key
from .errors import (
    DecryptionError,
    SafeRpaError,
    VerificationError,
    WriteGateBlocked,
)
from .gate import WRITE_ENABLED_ENV, WriteGate, env_write_enabled
from .readback import (
    Comparator,
    default_comparator,
    normalized_str_comparator,
    verify_write,
)
from .tz import to_aware_utc, to_naive_utc

__version__ = "0.1.0"

__all__ = [
    "BaseAdapter",
    "WriteResult",
    "WriteGate",
    "WRITE_ENABLED_ENV",
    "env_write_enabled",
    "verify_write",
    "Comparator",
    "default_comparator",
    "normalized_str_comparator",
    "SecretBox",
    "generate_key",
    "ENC_PREFIX",
    "KEY_ENV",
    "to_naive_utc",
    "to_aware_utc",
    "SafeRpaError",
    "WriteGateBlocked",
    "VerificationError",
    "DecryptionError",
    "__version__",
]
