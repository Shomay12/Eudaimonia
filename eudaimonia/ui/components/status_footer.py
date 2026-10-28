"""Terminal Footer displaying keyboard navigation shortcuts and active context.

Developer: KJshomay12
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class StatusFooter(Widget):
    """Bottom navigation helper and active context bar."""

    DEFAULT_CSS = """
    StatusFooter {
        height: 1;
        dock: bottom;
        background: #161b22;
        color: #8b949e;
        padding: 0 1;
        border-top: solid #21262d;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(id="footer-bar", **kwargs)
        self.active_context: str = "NIFTY"

    def compose(self) -> ComposeResult:
        yield Static(id="footer-text")

    def on_mount(self) -> None:
        self.update_context()

    def update_context(self, context_str: str | None = None) -> None:
        if context_str:
            self.active_context = context_str

        t = Text()
        t.append("F1", style="bold #58a6ff")
        t.append(" Help  ", style="#c9d1d9")

        t.append("F2", style="bold #58a6ff")
        t.append(" Overview  ", style="#c9d1d9")

        t.append("F3", style="bold #58a6ff")
        t.append(" Chain  ", style="#c9d1d9")

        t.append("F4", style="bold #58a6ff")
        t.append(" Quote/Depth  ", style="#c9d1d9")

        t.append("F5", style="bold #58a6ff")
        t.append(" Chart  ", style="#c9d1d9")

        t.append("F6", style="bold #58a6ff")
        t.append(" Watchlists  ", style="#c9d1d9")

        t.append(":", style="bold #d29922")
        t.append(" Cmd  ", style="#c9d1d9")

        t.append("q", style="bold #f85149")
        t.append(" Quit  ", style="#c9d1d9")

        t.append(f"| Target: {self.active_context}", style="bold #79c0ff")

        try:
            txt_widget = self.query_one("#footer-text", Static)
            txt_widget.update(t)
        except Exception:
            pass
