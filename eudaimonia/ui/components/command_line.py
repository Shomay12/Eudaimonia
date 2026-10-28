"""Interactive command line component with validation and suggestions.

Developer: KJshomay12
"""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class CommandSubmitted(Message):
    """Event sent when user submits a valid command."""

    def __init__(self, command: str, args: list[str]) -> None:
        super().__init__()
        self.command = command.lower()
        self.args = args


class CommandLine(Widget):
    """Bottom docked command input bar with syntax checking."""

    DEFAULT_CSS = """
    CommandLine {
        height: 3;
        dock: bottom;
        background: #161b22;
        border-top: solid #30363d;
        padding: 0 1;
        display: none;
    }
    CommandLine.visible {
        display: block;
    }
    #cmd-input {
        background: #0d1117;
        color: #58a6ff;
        border: none;
        height: 1;
    }
    #cmd-feedback {
        height: 1;
        color: #8b949e;
    }
    """

    KNOWN_COMMANDS = [
        "help",
        "status",
        "exchanges",
        "instruments",
        "watchlist",
        "watch",
        "unwatch",
        "quote",
        "chain",
        "expiry",
        "chart",
        "depth",
        "greeks",
        "company",
        "info",
        "wiki",
        "search",
        "history",
        "settings",
        "quit",
        "exit",
    ]

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter command (e.g. 'chain NIFTY', 'chart RELIANCE -i 5m', 'help')...", id="cmd-input")
        yield Static(id="cmd-feedback")

    def open_prompt(self, prefill: str = "") -> None:
        self.add_class("visible")
        inp = self.query_one("#cmd-input", Input)
        inp.value = prefill
        inp.focus()
        self.update_feedback("Type 'help' to see all commands. Press ESC to cancel.")

    def close_prompt(self) -> None:
        self.remove_class("visible")
        inp = self.query_one("#cmd-input", Input)
        inp.value = ""

    def update_feedback(self, msg: str, is_error: bool = False) -> None:
        fb = self.query_one("#cmd-feedback", Static)
        style = "#f85149" if is_error else "#8b949e"
        fb.update(Text(msg, style=style))

    def on_input_changed(self, event: Input.Changed) -> None:
        text = event.value.strip()
        if not text:
            self.update_feedback("Available: " + ", ".join(self.KNOWN_COMMANDS[:8]) + "...")
            return

        parts = text.split()
        cmd = parts[0].lower()

        # Check command match
        matches = [c for c in self.KNOWN_COMMANDS if c.startswith(cmd)]
        if matches:
            self.update_feedback(f"Matches: {', '.join(matches)}")
        else:
            self.update_feedback(f"Unknown command: '{cmd}'. Type 'help' for reference.", is_error=True)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            self.close_prompt()
            return

        parts = text.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("quit", "exit", "q"):
            self.app.exit()
            return

        if cmd not in self.KNOWN_COMMANDS:
            self.update_feedback(f"Unknown command '{cmd}'. See 'help'.", is_error=True)
            return

        self.post_message(CommandSubmitted(command=cmd, args=args))
        self.close_prompt()
