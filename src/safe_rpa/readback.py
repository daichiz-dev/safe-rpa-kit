"""Read-back verification.

A write is not "done" until you have re-read the target and confirmed it holds
what you intended. Many automation targets accept a write (HTTP 200, no error
dialog) yet silently drop or transform it: truncated fields, ignored inputs,
optimistic UIs that never persisted, stale caches. Read-back turns those silent
failures into loud ones.
"""

from __future__ import annotations

from typing import Any, Callable

from .errors import VerificationError

#: A comparator takes (expected, actual) and returns True if they match.
Comparator = Callable[[Any, Any], bool]


def default_comparator(expected: Any, actual: Any) -> bool:
    """Strict equality comparison."""
    return expected == actual


def normalized_str_comparator(expected: Any, actual: Any) -> bool:
    """Compare as whitespace-trimmed strings.

    Useful when a target round-trips values through HTML and re-pads them.
    """
    return str(expected).strip() == str(actual).strip()


def verify_write(
    expected: Any,
    actual: Any,
    comparator: Comparator = default_comparator,
    field: str = "value",
) -> None:
    """Confirm a read-back matches what was written, or raise.

    Parameters
    ----------
    expected:
        The value that was supposed to be written.
    actual:
        The value read back from the target after the write.
    comparator:
        Pluggable predicate ``(expected, actual) -> bool``. Defaults to strict
        equality. Swap in :func:`normalized_str_comparator` or your own.
    field:
        Human-readable name of the field, for the error message.

    Raises
    ------
    VerificationError:
        If the comparator reports a mismatch (fail-closed).
    """
    if not comparator(expected, actual):
        raise VerificationError(
            f"Read-back mismatch on {field!r}: wrote {expected!r} but target "
            f"now holds {actual!r}. The write did not persist as intended; "
            f"treating as failure (fail-closed)."
        )
