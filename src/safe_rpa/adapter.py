"""Abstract base for a safe RPA adapter.

An adapter drives one target (a website, an internal tool). Subclasses implement
the target-specific plumbing (``login``, ``_read`` / ``read_back``, and the raw
``_do_write``). The base class wires the three safety guarantees around every
write so subclasses cannot forget them:

1. dry-run by default: ``write(...)`` has ``dry_run=True`` unless told otherwise;
2. the global write gate must be enabled before any real write executes;
3. after a real write, the value is read back and verified, or the call fails.

Subclasses that follow this contract get "safe by construction" writes for free.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .gate import WriteGate
from .readback import Comparator, default_comparator, verify_write


@dataclass
class WriteResult:
    """Outcome of a :meth:`BaseAdapter.write` call."""

    field: str
    expected: Any
    performed: bool          # True only if a real write happened
    dry_run: bool
    verified: bool           # True if read-back confirmed the write
    actual: Any = None       # value read back (when performed)


class BaseAdapter(ABC):
    """Base class enforcing dry-run / gate / read-back on every write."""

    def __init__(self, gate: WriteGate | None = None) -> None:
        self.gate = gate or WriteGate()

    # --- target-specific plumbing (subclasses implement) -----------------

    @abstractmethod
    def login(self) -> None:
        """Authenticate to the target. Raise on failure."""

    @abstractmethod
    def read_back(self, field: str) -> Any:
        """Re-read the current value of ``field`` from the target."""

    @abstractmethod
    def _do_write(self, field: str, value: Any) -> None:
        """Perform the raw, irreversible write to the target.

        Called only after the write gate has passed. Subclasses must NOT add
        their own gating here; that is the base class's job.
        """

    # --- safe write orchestration (do not override) ----------------------

    def write(
        self,
        field: str,
        value: Any,
        dry_run: bool = True,
        comparator: Comparator = default_comparator,
    ) -> WriteResult:
        """Write ``value`` to ``field``, safely.

        With ``dry_run=True`` (the default) nothing is written: the call returns
        a plan. With ``dry_run=False`` the write gate is checked first (raising
        :class:`~safe_rpa.errors.WriteGateBlocked` if off), the raw write runs,
        and the result is read back and verified (raising
        :class:`~safe_rpa.errors.VerificationError` on mismatch).
        """
        if dry_run:
            return WriteResult(
                field=field,
                expected=value,
                performed=False,
                dry_run=True,
                verified=False,
            )

        # Real write path: gate, write, read back, verify.
        self.gate.check(action=f"write to {field}")
        self._do_write(field, value)
        actual = self.read_back(field)
        verify_write(value, actual, comparator=comparator, field=field)
        return WriteResult(
            field=field,
            expected=value,
            performed=True,
            dry_run=False,
            verified=True,
            actual=actual,
        )
