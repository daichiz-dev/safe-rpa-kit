from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from safe_rpa import to_aware_utc, to_naive_utc


def test_naive_input_interpreted_in_source_zone():
    # 09:00 in a UTC+9 zone is 00:00 UTC.
    dt = datetime(2026, 7, 3, 9, 0, 0)
    result = to_naive_utc(dt, "Asia/Tokyo")
    assert result == datetime(2026, 7, 3, 0, 0, 0)
    assert result.tzinfo is None


def test_aware_input_ignores_source_tz():
    dt = datetime(2026, 7, 3, 12, 0, 0, tzinfo=ZoneInfo("America/New_York"))
    # Its own offset wins; source_tz arg is ignored.
    result = to_naive_utc(dt, "Asia/Tokyo")
    expected = dt.astimezone(timezone.utc).replace(tzinfo=None)
    assert result == expected
    assert result.tzinfo is None


def test_zoneinfo_object_accepted():
    dt = datetime(2026, 1, 1, 0, 0, 0)
    result = to_naive_utc(dt, ZoneInfo("Asia/Tokyo"))
    assert result == datetime(2025, 12, 31, 15, 0, 0)


def test_to_aware_utc_keeps_tzinfo():
    dt = datetime(2026, 7, 3, 9, 0, 0)
    result = to_aware_utc(dt, "Asia/Tokyo")
    assert result.tzinfo == timezone.utc
    assert result == datetime(2026, 7, 3, 0, 0, 0, tzinfo=timezone.utc)


def test_utc_source_is_identity():
    dt = datetime(2026, 7, 3, 5, 30, 0)
    assert to_naive_utc(dt, "UTC") == dt
