import pytest

from safe_rpa import WriteGate, WriteGateBlocked, env_write_enabled


def test_gate_off_by_default(monkeypatch):
    monkeypatch.delenv("SAFE_RPA_WRITE_ENABLED", raising=False)
    gate = WriteGate()
    assert gate.enabled is False
    with pytest.raises(WriteGateBlocked):
        gate.check()


def test_explicit_enabled_bypasses_env(monkeypatch):
    monkeypatch.delenv("SAFE_RPA_WRITE_ENABLED", raising=False)
    gate = WriteGate(enabled=True)
    assert gate.enabled is True
    gate.check()  # does not raise


def test_explicit_disabled_beats_env(monkeypatch):
    monkeypatch.setenv("SAFE_RPA_WRITE_ENABLED", "1")
    gate = WriteGate(enabled=False)
    assert gate.enabled is False
    with pytest.raises(WriteGateBlocked):
        gate.check()


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", "enabled"])
def test_env_truthy_values(monkeypatch, value):
    monkeypatch.setenv("SAFE_RPA_WRITE_ENABLED", value)
    assert env_write_enabled() is True
    assert WriteGate().enabled is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "maybe"])
def test_env_falsey_values(monkeypatch, value):
    monkeypatch.setenv("SAFE_RPA_WRITE_ENABLED", value)
    assert env_write_enabled() is False
    with pytest.raises(WriteGateBlocked):
        WriteGate().check()


def test_custom_env_var(monkeypatch):
    monkeypatch.setenv("MY_APP_WRITE", "on")
    gate = WriteGate(env_var="MY_APP_WRITE")
    assert gate.enabled is True


def test_blocked_message_mentions_target(monkeypatch):
    monkeypatch.delenv("SAFE_RPA_WRITE_ENABLED", raising=False)
    gate = WriteGate(name="staging-target")
    with pytest.raises(WriteGateBlocked, match="staging-target"):
        gate.check()
