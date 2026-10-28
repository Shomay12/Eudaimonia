"""Implied Volatility solver for European options using Brent's method and Newton-Raphson.

Developer: KJshomay12
"""

from __future__ import annotations

import math
from scipy.optimize import brentq

from eudaimonia.analytics.black_scholes import black_scholes_price
from eudaimonia.models.instrument import OptionType

MIN_VOLATILITY = 0.0001  # 0.01%
MAX_VOLATILITY = 5.0     # 500%
TOLERANCE = 1e-5
MAX_ITERATIONS = 100


def calculate_implied_volatility(
    option_type: OptionType,
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    dividend_yield: float = 0.0,
) -> float | None:
    """Solve for implied volatility sigma such that BS(sigma) == market_price.

    Returns:
        float implied volatility, or None if arbitrage violated or solution does not converge.
    """
    if market_price <= 0 or spot <= 0 or strike <= 0 or time_to_expiry_years <= 1e-6:
        return None

    # Theoretical lower bound checks (no arbitrage condition)
    df_q = math.exp(-dividend_yield * time_to_expiry_years)
    df_r = math.exp(-risk_free_rate * time_to_expiry_years)

    if option_type == OptionType.CE:
        intrinsic = max(0.0, spot * df_q - strike * df_r)
        upper_bound = spot * df_q
    else:
        intrinsic = max(0.0, strike * df_r - spot * df_q)
        upper_bound = strike * df_r

    if market_price < intrinsic - 1e-4 or market_price > upper_bound + 1e-4:
        return None

    def objective(sigma: float) -> float:
        return black_scholes_price(
            option_type=option_type,
            spot=spot,
            strike=strike,
            time_to_expiry_years=time_to_expiry_years,
            risk_free_rate=risk_free_rate,
            volatility=sigma,
            dividend_yield=dividend_yield,
        ) - market_price

    # Check bounds
    try:
        f_low = objective(MIN_VOLATILITY)
        f_high = objective(MAX_VOLATILITY)

        if f_low * f_high > 0:
            # Cannot bracket root in [0.01%, 500%]
            return None

        # Brent's method provides quadratic convergence and guaranteed bracketing
        root = brentq(objective, MIN_VOLATILITY, MAX_VOLATILITY, xtol=TOLERANCE, maxiter=MAX_ITERATIONS)
        return float(round(root, 4))
    except (ValueError, RuntimeError):
        return None
