"""Headless integration test for Eudaimonia Textual Application.

Developer: KJshomay12
"""

from __future__ import annotations

import asyncio
import pytest

from eudaimonia.models.market_data import CandleInterval
from eudaimonia.providers.mock_provider import MockMarketDataProvider
from eudaimonia.ui.app import EudaimoniaApp
from eudaimonia.ui.components.command_line import CommandSubmitted


@pytest.mark.asyncio
async def test_eudaimonia_app_lifecycle():
    provider = MockMarketDataProvider()
    app = EudaimoniaApp(provider=provider)

    async with app.run_test() as pilot:
        # Verify app mounted
        assert app.is_running
        assert app.current_screen_name == "overview"

        # Wait a moment for background ticks to arrive
        await pilot.pause(0.5)

        # Switch to options chain screen
        app.action_switch_screen("chain")
        assert app.current_screen_name == "chain"
        await pilot.pause(0.2)

        # Expiry navigation
        app.action_chain_next_expiry()
        app.action_chain_prev_expiry()
        app.action_chain_zoom_in()
        app.action_chain_zoom_out()

        # Switch to quote screen
        app.action_switch_screen("quote")
        assert app.current_screen_name == "quote"
        await pilot.pause(0.2)

        # Switch to candlestick chart screen
        app.action_switch_screen("chart")
        assert app.current_screen_name == "chart"
        await pilot.pause(0.2)

        # Chart interval changes
        app.action_chart_m1()
        assert app.chart_screen.interval == CandleInterval.M1
        app.action_chart_m5()
        assert app.chart_screen.interval == CandleInterval.M5
        app.action_chart_toggle_vwap()

        # Open and test command line
        app.action_open_cmd()
        assert app.cmd_line.has_class("visible")

        # Submit command
        await app.on_command_submitted(CommandSubmitted(command="chain", args=["BANKNIFTY"]))
        assert app.current_screen_name == "chain"
        assert app.state_engine.active_underlying == "BANKNIFTY"

        # Switch to help screen
        app.action_switch_screen("help")
        assert app.current_screen_name == "help"

        # Press escape to return to overview
        app.action_handle_escape()
        assert app.current_screen_name == "overview"
