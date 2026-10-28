"""Tests for Implied Volatility solver and edge cases.

Developer: KJshomay12
"""

from __future__ import annotations

import pytest

from eudaimonia.analytics.black_scholes import black_scholes_price
from eudaimonia.analytics.implied_vol import calculate_implied_volatility
from eudaimonia.models.instrument import OptionType


def test_iv_solver_convergence():
    """Verify that IV solver recovers exact volatility from Black-Scholes price."""
    spot = 24500.0
    strike = 24600.0
    t = 15.0 / 365.0
    r = 0.065
    target_vol = 0.165

    # Generate theoretical call and put prices
    ce_price = black_scholes_price(OptionType.CE, spot, strike, t, r, target_vol)
    pe_price = black_scholes_price(OptionType.PE, spot, strike, t, r, target_vol)

    # Solve for IV
    solved_ce_iv = calculate_implied_volatility(OptionType.CE, ce_price, spot, strike, t, r)
    solved_pe_iv = calculate_implied_volatility(OptionType.PE, pe_price, spot, strike, t, r)

    assert solved_ce_iv is not None
    assert solved_pe_iv is not None
    assert pytest.approx(solved_ce_iv, abs=1e-3) == target_vol
    assert pytest.approx(solved_pe_iv, abs=1e-3) == target_vol


def test_iv_solver_arbitrage_violation():
    """Verify that arbitrage-violating market prices return None instead of crashing."""
    spot = 25000.0
    strike = 24000.0
    t = 10.0 / 365.0
    r = 0.065

    # Intrinsic value is ~1000. Market price of 500 violates no-arbitrage lower bound.
    impossible_ce_price = 500.0
    result = calculate_implied_volatility(OptionType.CE, impossible_ce_price, spot, strike, t, r)
    assert result is None

    # Market price exceeding spot (26000 > 25000) violates upper bound
    impossible_upper_price = 26000.0
    result_upper = calculate_implied_volatility(OptionType.CE, impossible_upper_price, spot, strike, t, r)
    assert result_upper is None
