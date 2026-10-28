"""Tests for Instrument Master and reference catalog.

Developer: KJshomay12
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import pytest

from eudaimonia.engine.instrument_master import InstrumentMaster
from eudaimonia.models.instrument import Exchange, Instrument, InstrumentType, OptionType, Segment


def test_instrument_master_indexing():
    master = InstrumentMaster()
    exp = date(2026, 10, 29)

    inst1 = Instrument(
        symbol="NSE:NIFTY",
        tradingsymbol="NIFTY",
        name="Nifty 50 Index",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_id="idx_nifty",
        underlying="NIFTY",
    )
    inst2 = Instrument(
        symbol="NSE:NIFTY26OCT25000CE",
        tradingsymbol="NIFTY26OCT25000CE",
        name="NIFTY 25000 CE",
        exchange=Exchange.NSE,
        segment=Segment.DERIVATIVE,
        instrument_type=InstrumentType.OPTION,
        provider_id="opt_1",
        underlying="NIFTY",
        strike_price=Decimal("25000.0"),
        expiry_date=exp,
        option_type=OptionType.CE,
    )
    inst3 = Instrument(
        symbol="NSE:NIFTY26OCT25000PE",
        tradingsymbol="NIFTY26OCT25000PE",
        name="NIFTY 25000 PE",
        exchange=Exchange.NSE,
        segment=Segment.DERIVATIVE,
        instrument_type=InstrumentType.OPTION,
        provider_id="opt_2",
        underlying="NIFTY",
        strike_price=Decimal("25000.0"),
        expiry_date=exp,
        option_type=OptionType.PE,
    )

    master.load_instruments([inst1, inst2, inst3])

    assert master.count() == 3
    assert master.get_by_symbol("NSE:NIFTY") == inst1
    assert master.get_by_symbol("NIFTY") == inst1
    assert master.get_by_provider_id("opt_1") == inst2

    # Query option
    found_ce = master.get_option_contract("NIFTY", exp, OptionType.CE, Decimal("25000.0"))
    assert found_ce == inst2

    # Expiries and strikes
    expiries = master.get_available_expiries("NIFTY")
    assert exp in expiries

    strikes = master.get_available_strikes("NIFTY", exp)
    assert Decimal("25000.0") in strikes

    # Search
    results = master.search_instruments("25000")
    assert len(results) == 2
