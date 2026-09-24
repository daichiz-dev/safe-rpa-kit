import pytest

from safe_rpa import VerificationError, normalized_str_comparator, verify_write


def test_match_passes():
    verify_write("abc", "abc")  # no raise


def test_mismatch_raises():
    with pytest.raises(VerificationError):
        verify_write("abc", "xyz")


def test_error_message_shows_both_values():
    with pytest.raises(VerificationError, match="wrote 'abc'.*'xyz'"):
        verify_write("abc", "xyz", field="note")


def test_normalized_comparator_ignores_whitespace():
    verify_write("  hello ", "hello", comparator=normalized_str_comparator)


def test_normalized_comparator_still_catches_real_diff():
    with pytest.raises(VerificationError):
        verify_write("hello", "goodbye", comparator=normalized_str_comparator)


def test_custom_comparator():
    case_insensitive = lambda e, a: str(e).lower() == str(a).lower()
    verify_write("YES", "yes", comparator=case_insensitive)
