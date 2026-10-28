"""Tests for Black-Scholes pricing, analytical Greeks, PCR, and Max Pain.

Developer: KJshomay12
"""

from __future__ import annotations

import math
from decimal import Decimal
import pytest

from eudaimonia.analytics.black_scholes import (
    black_scholes_price,
    calculate_d1_d2,
    calculate_greeks,
)
from eudaimonia.analytics.chain_analytics import (
    calculate_max_pain,
    calculate_pcr,
    classify_moneyness,
    find_atm_strike,
)
from eudaimonia.models.instrument import OptionType
from eudaimonia.models.options import Moneyness, OptionStrikeRow


def test_put_call_parity():
    """Verify Put-Call parity: C - P = S * exp(-q*T) - K * exp(-r*T)."""
    spot = 25000.0
    strike = 25000.0
    t = 30.0 / 365.0
    r = 0.065
    vol = 0.15

    c = black_scholes_price(OptionType.CE, spot, strike, t, r, vol)
    p = black_scholes_price(OptionType.PE, spot, strike, t, r, vol)

    expected_diff = spot - strike * math.exp(-r * t)
    actual_diff = c - p

    assert pytest.approx(actual_diff, rel=1e-4) == expected_diff


def test_analytical_greeks_properties():
    """Verify standard Greek bounds and properties."""
    spot = 24800.0
    strike = 25000.0
    t = 14.0 / 365.0
    r = 0.065
    vol = 0.14

    ce_greeks = calculate_greeks(OptionType.CE, spot, strike, t, r, vol)
    pe_greeks = calculate_greeks(OptionType.PE, spot, strike, t, r, vol)

    # Delta bounds
    assert 0.0 <= ce_greeks.delta <= 1.0
    assert -1.0 <= pe_greeks.delta <= 0.0

    # Gamma must be equal and strictly positive
    assert ce_greeks.gamma > 0.0
    assert pytest.approx(ce_greeks.gamma, rel=1e-5) == pe_greeks.gamma

    # Vega must be positive
    assert ce_greeks.vega > 0.0
    assert pytest.approx(ce_greeks.vega, rel=1e-5) == pe_greeks.vega

    # Theta decay should be negative
    assert ce_greeks.theta < 0.0
    assert pe_greeks.theta < 0.0


def test_pcr_calculation():
    # Regular values
    assert calculate_pcr(1500000, 1000000) == 1.5
    assert calculate_pcr(800000, 1000000) == 0.8

    # Division by zero
    assert calculate_pcr(50000, 0) is None


def test_atm_strike_finder():
    strikes = [Decimal(str(x)) for x in [24800, 24850, 24900, 24950, 25000]]
    assert find_atm_strike(Decimal("24890.0"), strikes) == Decimal("24900")
    assert find_atm_strike(Decimal("24860.0"), strikes) == Decimal("24850")


def test_moneyness_classification():
    atm = Decimal("25000")
    # Call
    assert classify_moneyness(Decimal("24900"), Decimal("25000"), atm, OptionType.CE) == Moneyness.ITM
    assert classify_moneyness(Decimal("25000"), Decimal("25000"), atm, OptionType.CE) == Moneyness.ATM
    assert classify_moneyness(Decimal("25100"), Decimal("25000"), atm, OptionType.CE) == Moneyness.OTM
    # Put
    assert classify_moneyness(Decimal("25100"), Decimal("25000"), atm, OptionType.PE) == Moneyness.ITM
    assert classify_moneyness(Decimal("25000"), Decimal("25000"), atm, OptionType.PE) == Moneyness.ATM
    assert classify_moneyness(Decimal("24900"), Decimal("25000"), atm, OptionType.PE) == Moneyness.OTM


def test_max_pain_calculation():
    # Construct synthetic strike ladder
    # Suppose massive Call OI at 25000 and massive Put OI at 24800
    from eudaimonia.models.market_data import MarketTick
    from datetime import datetime, timezone
    from eudaimonia.models.instrument import Exchange, Segment

    now = datetime.now(timezone.utc)

    def make_tick(sym: str, oi: int) -> MarketTick:
        return MarketTick(
            symbol=sym,
            exchange=Exchange.NSE,
            segment=Segment.DERIVATIVE,
            provider_id="mock",
            ltp=Decimal("100.0"),
            open_interest=oi,
            exchange_time=now,
            receipt_time=now,
        )

    rows = [
        OptionStrikeRow(
            strike_price=Decimal("24800"),
            call_tick=make_tick("CE24800", oi=10000),
            put_tick=make_tick("PE24800", oi=100000),
        ),
        OptionStrikeRow(
            strike_price=Decimal("24900"),
            call_tick=make_tick("CE24900", oi=50000),
            put_tick=make_tick("PE24900", oi=50000),
        ),
        OptionStrikeRow(
            strike_price=Decimal("25000"),
            call_tick=make_tick("CE25000", oi=100000),
            put_tick=make_tick("PE25000", oi=10000),
        ),
    ]

    max_pain = calculate_max_pain(rows)
    # The middle strike 24900 balances the payouts
    assert max_pain == Decimal("24900")
