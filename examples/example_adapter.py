"""Example adapter for a fictional "notepad" web app.

This targets a made-up demo page (a single text field with a Save button).
There is no real service behind it; the selectors and flow are illustrative
only. It exists to show how to subclass :class:`safe_rpa.BaseAdapter` so that
dry-run, the write gate, and read-back verification all apply automatically.

Run against your own local demo page, e.g. a static HTML file served at
http://localhost:8000/ with:

    <input id="note-field">
    <button id="save-button">Save</button>

Requires ``playwright`` (``pip install playwright && playwright install``).
"""

from __future__ import annotations

from typing import Any

from safe_rpa import BaseAdapter, WriteGate


class NotepadAdapter(BaseAdapter):
    """Drives a fictional single-field notepad page via Playwright."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/",
        gate: WriteGate | None = None,
    ) -> None:
        super().__init__(gate=gate)
        self.base_url = base_url
        self._page = None
        self._browser = None
        self._pw = None

    def login(self) -> None:
        # Import locally so the rest of the kit has no hard Playwright dependency.
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._page = self._browser.new_page()
        self._page.goto(self.base_url)
        # A real adapter would fill a login form here. The demo page is open,
        # so we simply confirm the note field is present.
        self._page.wait_for_selector("#note-field")

    def read_back(self, field: str) -> Any:
        assert self._page is not None, "call login() first"
        return self._page.input_value("#note-field")

    def _do_write(self, field: str, value: Any) -> None:
        assert self._page is not None, "call login() first"
        self._page.fill("#note-field", str(value))
        self._page.click("#save-button")

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._pw is not None:
            self._pw.stop()


def main() -> None:
    # Off by default -> the real write below would raise WriteGateBlocked.
    # Pass enabled=True (or set SAFE_RPA_WRITE_ENABLED=1) to actually write.
    adapter = NotepadAdapter(gate=WriteGate(enabled=False))
    adapter.login()
    try:
        # Safe preview: nothing is written.
        plan = adapter.write("note", "hello world", dry_run=True)
        print("dry-run plan:", plan)

        # Real write (blocked here because the gate is off):
        # result = adapter.write("note", "hello world", dry_run=False)
        # print("wrote and verified:", result)
    finally:
        adapter.close()


if __name__ == "__main__":
    main()
