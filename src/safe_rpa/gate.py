"""Global write gate.

The gate is the single choke point that decides whether *any* real write to a
production target is permitted. It is off by default. Turning it on requires an
explicit, out-of-band signal (an environment variable, or an explicit constructor
argument) so that a write can never happen just because a code path was reached.

Design intent: writes should be *impossible by accident*. A forgotten flag, a
misconfigured job, or a stray call in a test all resolve to "blocked", never to
"wrote to production".
"""

from __future__ import annotations

import os

from .errors import WriteGateBlocked

#: Environment variable consulted when no explicit override is given.
WRITE_ENABLED_ENV = "SAFE_RPA_WRITE_ENABLED"

#: Values (case-insensitive) that count as "enabled". Everything else is off.
_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})


def env_write_enabled(env_var: str = WRITE_ENABLED_ENV) -> bool:
    """Return True only if the environment explicitly enables writes."""
    raw = os.environ.get(env_var, "")
    return raw.strip().lower() in _TRUTHY


class WriteGate:
    """Fail-closed gate guarding real writes.

    Parameters
    ----------
    enabled:
        Explicit override. If left as ``None`` (default) the gate reads the
        environment variable ``env_var``. Passing ``True``/``False`` bypasses
        the environment entirely, which is handy in tests.
    env_var:
        Name of the environment variable to consult when ``enabled`` is None.
    name:
        Optional label used in error messages (e.g. a target/site identifier).
    """

    def __init__(
        self,
        enabled: bool | None = None,
        env_var: str = WRITE_ENABLED_ENV,
        name: str = "default",
    ) -> None:
        self.env_var = env_var
        self.name = name
        self._explicit = enabled

    @property
    def enabled(self) -> bool:
        """Whether real writes are currently permitted."""
        if self._explicit is not None:
            return self._explicit
        return env_write_enabled(self.env_var)

    def check(self, action: str = "write") -> None:
        """Raise :class:`WriteGateBlocked` unless writes are enabled.

        Call this immediately before performing a real, irreversible write.
        """
        if not self.enabled:
            raise WriteGateBlocked(
                f"Real {action} on target '{self.name}' is blocked: write gate "
                f"is off. Set {self.env_var}=1 (or pass enabled=True) to allow "
                f"production writes. Refusing to proceed (fail-closed)."
            )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"WriteGate(name={self.name!r}, enabled={self.enabled})"
