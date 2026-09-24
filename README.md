# safe-rpa-kit

[![CI](https://github.com/daichiz-dev/safe-rpa-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/daichiz-dev/safe-rpa-kit/actions/workflows/ci.yml)

Browser automation that writes to production systems fails in a particular,
nasty way: **it fails silently.** A selector drifts, a form quietly truncates a
field, an optimistic UI shows "Saved" without persisting, a job runs with a
config pointing at the wrong environment. Nothing throws. The automation reports
success. Days later someone notices the data is wrong — often at scale, across
every record the job touched.

`safe-rpa-kit` is a small framework that makes those failures **loud and rare**
by treating three defenses as first-class concerns from the very first line of
code, not as things you bolt on after the first incident.

## The three defenses

### 1. Dry-run is the default

Every write goes through `BaseAdapter.write(...)`, whose signature is
`dry_run: bool = True`. If you call it and forget to think about production, you
get a **plan**, not a mutation. Writing for real is a conscious act
(`dry_run=False`), never the path of least resistance.

*Prevents:* accidental writes from a half-finished script, a test run against a
live target, a copy-pasted call left in a loop.

### 2. A global write gate (fail-closed)

Even a deliberate `dry_run=False` write is refused unless a separate global gate
is enabled — via the `SAFE_RPA_WRITE_ENABLED` environment variable or an explicit
`WriteGate(enabled=True)`. If the gate is off, `write` raises `WriteGateBlocked`
and touches nothing.

*Prevents:* a correct-looking job running in the wrong environment; a forgotten
flag turning into 200,000 mutated rows. The default answer to "should I write?"
is **no**, and someone has to say yes out of band.

### 3. Read-back verification (fail-closed)

After a real write, the adapter re-reads the field from the target and compares
it to what it meant to write. Mismatch → `VerificationError`, and the call is
treated as a failure. "The POST returned 200" is not evidence that the value
persisted; reading it back is.

*Prevents:* silent truncation, ignored inputs, stale caches, optimistic UIs that
never actually saved.

Together: writes are **impossible by accident**, **off by default**, and **not
trusted until re-read**.

## Install

```bash
pip install safe-rpa-kit          # core (cryptography only)
pip install "safe-rpa-kit[browser]"   # adds Playwright for real adapters
```

## Quickstart

Subclass `BaseAdapter` and implement three target-specific methods. The base
class wraps dry-run, the gate, and read-back around every write for you.

```python
from safe_rpa import BaseAdapter, WriteGate

class MyAdapter(BaseAdapter):
    def login(self):
        ...  # authenticate to your target

    def read_back(self, field):
        return ...  # re-read the current value of `field`

    def _do_write(self, field, value):
        ...  # the raw, irreversible write (called only after the gate passes)

adapter = MyAdapter(gate=WriteGate())  # gate off unless env enables it
adapter.login()

# Safe by default: nothing is written, you get a plan.
plan = adapter.write("headline", "Summer sale")
assert plan.performed is False and plan.dry_run is True

# Real write: requires SAFE_RPA_WRITE_ENABLED=1 (or WriteGate(enabled=True)).
# Runs the write, reads it back, verifies it — or raises.
result = adapter.write("headline", "Summer sale", dry_run=False)
assert result.verified is True
```

If the gate is off, that last call raises `WriteGateBlocked`. If the target
stored something different, it raises `VerificationError`. You never get a false
"success".

A complete runnable example against a fictional notepad page is in
[`examples/example_adapter.py`](examples/example_adapter.py).

### Custom comparators

Targets often round-trip values through HTML and re-pad them. Supply a
comparator so cosmetic differences don't read as failures — while real ones
still do:

```python
from safe_rpa import normalized_str_comparator
adapter.write("note", "hello", dry_run=False, comparator=normalized_str_comparator)
```

## Secret encryption (Fernet)

Automation needs credentials, and credentials must not sit in plaintext in your
config or database. `SecretBox` wraps Fernet (authenticated symmetric crypto)
with two practical touches:

```python
from safe_rpa import SecretBox, generate_key

box = SecretBox(key=generate_key())   # or SecretBox() to read SAFE_RPA_FERNET_KEY
token = box.encrypt("target-password")   # -> "enc:v1:...."
box.decrypt(token)                        # -> "target-password"
```

- **Version prefix** `enc:v1:` on every ciphertext, so you can evolve the scheme
  later and tell encrypted values from plaintext at a glance.
- **Backward-compatible decryption**: a value *without* the prefix is treated as
  legacy plaintext and returned unchanged. This lets you roll encryption out to
  an existing store gradually instead of in one risky big-bang migration.

Store the key outside the repo (an env var or secret manager), never alongside
the ciphertext.

## The time-zone trap

Automation reads local wall-clock times off a UI (a schedule shown in some
regional zone) and must store them consistently. The classic bug: store local
time as if it were UTC, or mix naive and aware datetimes, and every record ends
up skewed by whole hours — a discrepancy that only surfaces much later.

`to_naive_utc` enforces one rule: interpret the incoming time in an explicit
source zone, then reduce it to a naive datetime whose value is UTC. The offset
math happens exactly once.

```python
from datetime import datetime
from safe_rpa import to_naive_utc

# 09:00 wall-clock in a UTC+9 zone -> 00:00 UTC, stored naive.
to_naive_utc(datetime(2026, 7, 3, 9, 0), "Asia/Tokyo")
# datetime(2026, 7, 3, 0, 0)
```

Aware input keeps its own offset (the `source_tz` argument is ignored), so you
can't accidentally double-convert.

## Why is `dry_run` defaulted to `True`?

Because defaults are what happen when someone is tired, in a hurry, or doesn't
yet understand the blast radius of the code they're running. A framework whose
default writes to production is a framework that *will* write to production by
accident — the only question is when.

Making `dry_run=True` the default inverts the risk. The worst case for a careless
call is "nothing happened, here's what would have." Doing real damage requires
three deliberate, independent acts: pass `dry_run=False`, enable the write gate,
and have the value actually survive read-back. Each is a place a mistake gets
caught instead of committed. Safety you have to remember to turn on is safety
that gets forgotten; this kit makes safety the thing you have to remember to turn
*off*.

## License

MIT © 2026 daichiz-dev
