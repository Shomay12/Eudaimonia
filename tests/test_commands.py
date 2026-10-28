"""Tests for Command Line validation and CLI argument parsing.

Developer: KJshomay12
"""

from __future__ import annotations

import pytest

from eudaimonia.cli import parse_args
from eudaimonia.ui.components.command_line import CommandLine


def test_cli_argument_parsing():
    args = parse_args(["--provider", "mock", "--underlying", "BANKNIFTY", "--exchange", "NSE"])
    assert args.provider == "mock"
    assert args.underlying == "BANKNIFTY"
    assert args.exchange == "NSE"


def test_command_line_known_commands():
    cmd_widget = CommandLine()
    expected = ["help", "status", "exchanges", "instruments", "watchlist", "watch", "quote", "chain", "chart", "depth", "quit"]
    for c in expected:
        assert c in cmd_widget.KNOWN_COMMANDS
