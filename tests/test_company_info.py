"""Tests for Company Intelligence and Wikipedia integration.

Developer: KJshomay12
"""

from __future__ import annotations

import pytest

from eudaimonia.engine.company_info import find_company_key, get_company_profile


def test_company_key_lookup():
    assert find_company_key("RELIANCE") == "RELIANCE"
    assert find_company_key("NSE:RELIANCE") == "RELIANCE"
    assert find_company_key("Reliance Industries") == "RELIANCE"
    assert find_company_key("Mukesh Ambani") == "RELIANCE"
    assert find_company_key("TCS") == "TCS"
    assert find_company_key("Tata Consultancy") == "TCS"
    assert find_company_key("Infosys") == "INFY"
    assert find_company_key("HDFC") == "HDFCBANK"
    assert find_company_key("Tata Motors") == "TATAMOTORS"
    assert find_company_key("SBI") == "SBIN"


def test_company_profile_data():
    profile = get_company_profile("TCS", fetch_live_wiki=False)
    assert profile is not None
    assert profile.company_name == "Tata Consultancy Services Limited"
    assert profile.symbol == "NSE:TCS"
    assert profile.sector == "Information Technology"
    assert profile.market_cap_inr_cr > 1000000.0
    assert "Mumbai" in profile.headquarters
    assert profile.founded_year == 1968
    assert len(profile.wiki_summary) > 50
    assert "Tata" in profile.wiki_summary


def test_nonexistent_company():
    profile = get_company_profile("UNKNOWN_XYZ_CORP_999", fetch_live_wiki=False)
    assert profile is None
