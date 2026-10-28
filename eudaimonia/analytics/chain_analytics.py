"""Option chain analytics: PCR, Max Pain, ATM/ITM/OTM moneyness classification.

Developer: KJshomay12
"""

from __future__ import annotations

from decimal import Decimal

from eudaimonia.models.instrument import OptionType
from eudaimonia.models.options import Moneyness, OptionStrikeRow


def calculate_pcr(put_value: int | float, call_value: int | float) -> float | None:
    """Calculate Put-Call Ratio (PCR).

    PCR = Total Put Metric / Total Call Metric
    Returns None if call_value <= 0.
    """
    if call_value <= 0:
        return None
    return round(float(put_value) / float(call_value), 4)


def find_atm_strike(spot: Decimal, available_strikes: list[Decimal]) -> Decimal:
    """Find the At-The-Money (ATM) strike closest to the underlying spot price."""
    if not available_strikes:
        return spot
    return min(available_strikes, key=lambda strike: abs(strike - spot))


def classify_moneyness(
    strike: Decimal,
    spot: Decimal,
    atm_strike: Decimal,
    option_type: OptionType,
) -> Moneyness:
    """Determine whether a strike is ATM, ITM, or OTM for Calls and Puts.

    Conventions:
        - Strike == atm_strike: ATM
        - For Calls:
            - strike < atm_strike: ITM (in-the-money)
            - strike > atm_strike: OTM (out-of-the-money)
        - For Puts:
            - strike > atm_strike: ITM (in-the-money)
            - strike < atm_strike: OTM (out-of-the-money)
    """
    if strike == atm_strike:
        return Moneyness.ATM

    if option_type == OptionType.CE:
        return Moneyness.ITM if strike < atm_strike else Moneyness.OTM
    else:
        return Moneyness.ITM if strike > atm_strike else Moneyness.OTM


def calculate_max_pain(strikes_data: list[OptionStrikeRow]) -> Decimal | None:
    """Calculate the Max Pain strike price.

    Max Pain is the strike price at which option buyers (as an aggregate)
    lose the most money, meaning option sellers incur the minimum payout.

    Payout for underlying settling at expiration strike S:
        Call Loss = Call OI * max(0, S - Strike_K)
        Put Loss = Put OI * max(0, Strike_K - S)
        Total Payout(S) = sum_over_all_K(Call Loss + Put Loss)

    Returns:
        Strike with minimum total payout, or None if strikes_data is empty.
    """
    if not strikes_data:
        return None

    candidate_strikes = [row.strike_price for row in strikes_data]
    min_loss: Decimal | None = None
    max_pain_strike: Decimal | None = None

    for target_price in candidate_strikes:
        total_loss = Decimal("0.0")
        for row in strikes_data:
            k = row.strike_price
            ce_oi = Decimal(str(row.call_oi))
            pe_oi = Decimal(str(row.put_oi))

            # Call payoff at target_price
            if target_price > k:
                total_loss += ce_oi * (target_price - k)

            # Put payoff at target_price
            if target_price < k:
                total_loss += pe_oi * (k - target_price)

        if min_loss is None or total_loss < min_loss:
            min_loss = total_loss
            max_pain_strike = target_price

    return max_pain_strike
