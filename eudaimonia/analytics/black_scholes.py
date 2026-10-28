"""Black-Scholes-Merton option pricing and analytical Greeks engine.

Developer: KJshomay12
"""

from __future__ import annotations

import math
from decimal import Decimal
from scipy.stats import norm

from eudaimonia.models.instrument import OptionType
from eudaimonia.models.options import Greeks, Moneyness


def standard_normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return float(norm.cdf(x))


def standard_normal_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return float(norm.pdf(x))


def calculate_d1_d2(
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
) -> tuple[float, float]:
    """Calculate d1 and d2 terms in Black-Scholes formula.

    Returns:
        tuple (d1, d2)
    """
    if spot <= 0 or strike <= 0 or volatility <= 0 or time_to_expiry_years <= 0:
        return 0.0, 0.0

    numerator = math.log(spot / strike) + (
        risk_free_rate - dividend_yield + 0.5 * (volatility**2)
    ) * time_to_expiry_years
    denominator = volatility * math.sqrt(time_to_expiry_years)
    d1 = numerator / denominator
    d2 = d1 - denominator
    return d1, d2


def black_scholes_price(
    option_type: OptionType,
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
) -> float:
    """Calculate European option price under Black-Scholes-Merton model.

    Inputs:
        option_type: CE (Call) or PE (Put)
        spot: Current underlying asset price (S)
        strike: Option strike price (K)
        time_to_expiry_years: Time to expiry in fraction of 365-day year (T)
        risk_free_rate: Annualized continuously compounded risk-free rate (r)
        volatility: Annualized volatility of underlying returns (sigma)
        dividend_yield: Continuous dividend yield (q)
    """
    if spot <= 0 or strike <= 0:
        return 0.0

    # At or past expiry
    if time_to_expiry_years <= 1e-7:
        if option_type == OptionType.CE:
            return max(0.0, spot - strike)
        else:
            return max(0.0, strike - spot)

    if volatility <= 1e-7:
        discount = math.exp(-risk_free_rate * time_to_expiry_years)
        div_discount = math.exp(-dividend_yield * time_to_expiry_years)
        forward = spot * div_discount / discount
        if option_type == OptionType.CE:
            return discount * max(0.0, forward - strike)
        else:
            return discount * max(0.0, strike - forward)

    d1, d2 = calculate_d1_d2(
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    df_q = math.exp(-dividend_yield * time_to_expiry_years)
    df_r = math.exp(-risk_free_rate * time_to_expiry_years)

    if option_type == OptionType.CE:
        price = spot * df_q * standard_normal_cdf(d1) - strike * df_r * standard_normal_cdf(d2)
    else:
        price = strike * df_r * standard_normal_cdf(-d2) - spot * df_q * standard_normal_cdf(-d1)

    return max(0.0, price)


def calculate_greeks(
    option_type: OptionType,
    spot: float,
    strike: float,
    time_to_expiry_years: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
) -> Greeks:
    """Calculate analytical Greeks under Black-Scholes-Merton framework.

    Greeks units:
        Delta: dV / dS (dimensionless)
        Gamma: d2V / dS2 (rate of change of delta per INR move in spot)
        Theta: 1 calendar day decay in INR (annual theta / 365)
        Vega: Change in INR for a 1 percentage point (0.01) increase in IV
        Rho: Change in INR for a 1 percentage point (0.01) increase in interest rate
    """
    if spot <= 0 or strike <= 0:
        return Greeks(iv=0.0, delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)

    # Intrinsic value
    if option_type == OptionType.CE:
        intrinsic = Decimal(str(round(max(0.0, spot - strike), 4)))
    else:
        intrinsic = Decimal(str(round(max(0.0, strike - spot), 4)))

    # Expiry edge case
    if time_to_expiry_years <= 1e-7:
        if option_type == OptionType.CE:
            delta = 1.0 if spot > strike else (0.5 if spot == strike else 0.0)
        else:
            delta = -1.0 if spot < strike else (-0.5 if spot == strike else 0.0)
        return Greeks(
            iv=volatility,
            delta=delta,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
            intrinsic_value=intrinsic,
            extrinsic_value=Decimal("0.0"),
        )

    if volatility <= 1e-7:
        return Greeks(
            iv=0.0,
            delta=1.0 if (option_type == OptionType.CE and spot > strike) else 0.0,
            gamma=0.0,
            theta=0.0,
            vega=0.0,
            rho=0.0,
            intrinsic_value=intrinsic,
            extrinsic_value=Decimal("0.0"),
        )

    d1, d2 = calculate_d1_d2(
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    sqrt_t = math.sqrt(time_to_expiry_years)
    df_q = math.exp(-dividend_yield * time_to_expiry_years)
    df_r = math.exp(-risk_free_rate * time_to_expiry_years)
    pdf_d1 = standard_normal_pdf(d1)
    cdf_d1 = standard_normal_cdf(d1)
    cdf_d2 = standard_normal_cdf(d2)

    # Delta
    if option_type == OptionType.CE:
        delta = df_q * cdf_d1
    else:
        delta = df_q * (cdf_d1 - 1.0)

    # Gamma (identical for Call and Put)
    gamma = (df_q * pdf_d1) / (spot * volatility * sqrt_t) if (spot * volatility * sqrt_t) > 0 else 0.0

    # Theta (Annual, then divided by 365 for daily decay)
    first_term = -(spot * volatility * df_q * pdf_d1) / (2.0 * sqrt_t)
    if option_type == OptionType.CE:
        second_term = -risk_free_rate * strike * df_r * cdf_d2
        third_term = dividend_yield * spot * df_q * cdf_d1
        annual_theta = first_term + second_term + third_term
    else:
        second_term = risk_free_rate * strike * df_r * standard_normal_cdf(-d2)
        third_term = -dividend_yield * spot * df_q * standard_normal_cdf(-d1)
        annual_theta = first_term + second_term + third_term

    daily_theta = annual_theta / 365.0

    # Vega (per 1% move in IV: divide by 100)
    vega_1pct = (spot * df_q * sqrt_t * pdf_d1) / 100.0

    # Rho (per 1% move in interest rate: divide by 100)
    if option_type == OptionType.CE:
        rho_1pct = (strike * time_to_expiry_years * df_r * cdf_d2) / 100.0
    else:
        rho_1pct = (-strike * time_to_expiry_years * df_r * standard_normal_cdf(-d2)) / 100.0

    bs_price = black_scholes_price(
        option_type=option_type,
        spot=spot,
        strike=strike,
        time_to_expiry_years=time_to_expiry_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )
    extrinsic = Decimal(str(round(max(0.0, bs_price - float(intrinsic)), 4)))

    return Greeks(
        iv=volatility,
        delta=round(delta, 4),
        gamma=round(gamma, 6),
        theta=round(daily_theta, 4),
        vega=round(vega_1pct, 4),
        rho=round(rho_1pct, 4),
        intrinsic_value=intrinsic,
        extrinsic_value=extrinsic,
        is_converged=True,
    )
