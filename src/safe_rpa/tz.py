"""Time-zone normalization: source-TZ -> naive UTC.

Automation frequently reads local wall-clock times from a UI (a schedule shown
in some regional time zone) and must store them consistently. Mixing naive and
aware datetimes, or storing local time as if it were UTC, produces silent offset
bugs that surface much later as data skewed by whole hours.

The rule enforced here: interpret every incoming time in an explicit source zone,
then reduce it to a *naive* datetime whose value is UTC. One canonical form goes
to storage; the offset math happens exactly once, here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def to_naive_utc(dt: datetime, source_tz: str | ZoneInfo) -> datetime:
    """Convert ``dt`` to a naive datetime expressed in UTC.

    Parameters
    ----------
    dt:
        Either an aware datetime (its own tzinfo wins; ``source_tz`` is ignored)
        or a naive datetime (assumed to be wall-clock time in ``source_tz``).
    source_tz:
        IANA zone name (e.g. ``"America/New_York"``) or a ``ZoneInfo``. Used only
        to interpret naive input.

    Returns
    -------
    datetime
        Naive datetime (``tzinfo is None``) whose fields represent UTC.
    """
    tz = ZoneInfo(source_tz) if isinstance(source_tz, str) else source_tz
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def to_aware_utc(dt: datetime, source_tz: str | ZoneInfo) -> datetime:
    """Like :func:`to_naive_utc` but keeps the UTC tzinfo attached."""
    tz = ZoneInfo(source_tz) if isinstance(source_tz, str) else source_tz
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(timezone.utc)
