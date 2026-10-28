"""Instrument Master catalog for NSE and BSE.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable

from eudaimonia.models.instrument import Exchange, Instrument, InstrumentType, OptionType, Segment


class InstrumentMaster:
    """In-memory reference catalog of all instruments across exchanges."""

    def __init__(self) -> None:
        # Key: canonical symbol (e.g. "NSE:NIFTY")
        self._by_symbol: dict[str, Instrument] = {}
        # Key: provider token/id
        self._by_provider_id: dict[str, Instrument] = {}
        # Key: (underlying, expiry, option_type, strike)
        self._options_lookup: dict[tuple[str, date, OptionType, Decimal], Instrument] = {}
        # Key: underlying -> sorted set of available expiry dates
        self._expiries_by_underlying: dict[str, set[date]] = {}
        # Key: (underlying, expiry) -> sorted set of strikes
        self._strikes_by_underlying_expiry: dict[tuple[str, date], set[Decimal]] = {}

    def load_instruments(self, instruments: Iterable[Instrument]) -> None:
        """Populate or update instrument index."""
        for inst in instruments:
            self._by_symbol[inst.symbol] = inst
            self._by_provider_id[inst.provider_id] = inst

            if inst.instrument_type == InstrumentType.OPTION and inst.underlying and inst.expiry_date and inst.strike_price and inst.option_type:
                key = (inst.underlying.upper(), inst.expiry_date, inst.option_type, inst.strike_price)
                self._options_lookup[key] = inst

                # Track expiries
                if inst.underlying.upper() not in self._expiries_by_underlying:
                    self._expiries_by_underlying[inst.underlying.upper()] = set()
                self._expiries_by_underlying[inst.underlying.upper()].add(inst.expiry_date)

                # Track strikes
                ue_key = (inst.underlying.upper(), inst.expiry_date)
                if ue_key not in self._strikes_by_underlying_expiry:
                    self._strikes_by_underlying_expiry[ue_key] = set()
                self._strikes_by_underlying_expiry[ue_key].add(inst.strike_price)

    def get_by_symbol(self, symbol: str) -> Instrument | None:
        """Lookup by internal canonical symbol e.g. 'NSE:NIFTY' or 'BSE:SENSEX'."""
        if symbol in self._by_symbol:
            return self._by_symbol[symbol]
        # Fallback without exchange prefix
        for s, inst in self._by_symbol.items():
            if inst.tradingsymbol.upper() == symbol.upper() or s.split(":")[-1].upper() == symbol.upper():
                return inst
        return None

    def get_by_provider_id(self, provider_id: str) -> Instrument | None:
        return self._by_provider_id.get(provider_id)

    def get_option_contract(
        self,
        underlying: str,
        expiry: date,
        option_type: OptionType,
        strike: Decimal,
    ) -> Instrument | None:
        return self._options_lookup.get((underlying.upper(), expiry, option_type, strike))

    def get_available_expiries(self, underlying: str) -> list[date]:
        """Return sorted list of available expiry dates for an underlying."""
        expiries = self._expiries_by_underlying.get(underlying.upper(), set())
        return sorted(expiries)

    def get_available_strikes(self, underlying: str, expiry: date) -> list[Decimal]:
        """Return sorted list of available strikes for given underlying and expiry."""
        strikes = self._strikes_by_underlying_expiry.get((underlying.upper(), expiry), set())
        return sorted(strikes)

    def search_instruments(self, query: str, limit: int = 20) -> list[Instrument]:
        """Search instruments by symbol or name."""
        q = query.upper()
        matches: list[Instrument] = []
        for inst in self._by_symbol.values():
            if q in inst.symbol.upper() or q in inst.tradingsymbol.upper() or q in inst.name.upper():
                matches.append(inst)
                if len(matches) >= limit:
                    break
        return matches

    def get_all_indices(self) -> list[Instrument]:
        return [inst for inst in self._by_symbol.values() if inst.instrument_type == InstrumentType.INDEX]

    def count(self) -> int:
        return len(self._by_symbol)
