"""Company Intelligence & Wikipedia Integration for Indian Equities.

Developer: KJshomay12
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class CompanyProfile:
    """Detailed profile of an exchange-listed company with Wikipedia metadata."""

    symbol: str
    company_name: str
    exchange: str
    isin: str
    sector: str
    industry: str
    market_cap_inr_cr: float
    pe_ratio: float
    pb_ratio: float
    dividend_yield_pct: float
    week_52_high: float
    week_52_low: float
    headquarters: str
    founded_year: int
    key_executives: str
    business_segments: list[str] = field(default_factory=list)
    wiki_title: str = ""
    wiki_summary: str = ""
    wiki_url: str = ""


# Verified Reference Database of Major Indian Listed Companies
COMPANY_DATABASE: dict[str, dict[str, Any]] = {
    "RELIANCE": {
        "symbol": "NSE:RELIANCE",
        "company_name": "Reliance Industries Limited",
        "exchange": "NSE / BSE",
        "isin": "INE002A01018",
        "sector": "Energy & Conglomerate",
        "industry": "Oil, Gas, Consumable Fuels, Retail & Telecom",
        "market_cap_inr_cr": 2005240.0,
        "pe_ratio": 28.4,
        "pb_ratio": 2.45,
        "dividend_yield_pct": 0.35,
        "week_52_high": 3217.90,
        "week_52_low": 2220.30,
        "headquarters": "Mumbai, Maharashtra, India",
        "founded_year": 1958,
        "key_executives": "Mukesh Ambani (Chairman & Managing Director)",
        "business_segments": [
            "Petrochemicals & Refining",
            "Oil & Gas Exploration",
            "Reliance Retail",
            "Jio Platforms (Telecommunications)",
            "New Energy & Green Power",
        ],
        "wiki_title": "Reliance_Industries",
        "fallback_summary": (
            "Reliance Industries Limited (RIL) is an Indian multinational conglomerate company, "
            "headquartered in Mumbai. Its diverse businesses include energy, petrochemicals, "
            "natural gas, retail, telecommunications, mass media, and textiles. Reliance is the largest "
            "publicly traded company in India by market capitalization and revenue."
        ),
    },
    "TCS": {
        "symbol": "NSE:TCS",
        "company_name": "Tata Consultancy Services Limited",
        "exchange": "NSE / BSE",
        "isin": "INE467B01029",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "market_cap_inr_cr": 1515000.0,
        "pe_ratio": 32.1,
        "pb_ratio": 14.8,
        "dividend_yield_pct": 1.25,
        "week_52_high": 4585.90,
        "week_52_low": 3313.00,
        "headquarters": "Mumbai, Maharashtra, India",
        "founded_year": 1968,
        "key_executives": "K. Krithivasan (CEO & MD), N. Chandrasekaran (Chairman)",
        "business_segments": [
            "Banking, Financial Services & Insurance (BFSI)",
            "Cloud & Cognitive Solutions",
            "Enterprise Solutions & Consulting",
            "Life Sciences & Healthcare IT",
        ],
        "wiki_title": "Tata_Consultancy_Services",
        "fallback_summary": (
            "Tata Consultancy Services (TCS) is an Indian multinational information technology services "
            "and consulting company headquartered in Mumbai. It is a part of the Tata Group and operates in "
            "150 locations across 50 countries. TCS is the second-largest Indian company by market capitalization."
        ),
    },
    "INFY": {
        "symbol": "NSE:INFY",
        "company_name": "Infosys Limited",
        "exchange": "NSE / BSE",
        "isin": "INE009A01021",
        "sector": "Information Technology",
        "industry": "IT Consulting & Software",
        "market_cap_inr_cr": 765400.0,
        "pe_ratio": 29.8,
        "pb_ratio": 8.6,
        "dividend_yield_pct": 2.10,
        "week_52_high": 1975.00,
        "week_52_low": 1358.35,
        "headquarters": "Bengaluru, Karnataka, India",
        "founded_year": 1981,
        "key_executives": "Salil Parekh (CEO & MD), Nandan Nilekani (Co-founder & Chairman)",
        "business_segments": [
            "Digital Business Transformation",
            "Infosys Topaz (Generative AI)",
            "Infosys Finacle (Core Banking Solution)",
            "Enterprise Cloud & Infrastructure",
        ],
        "wiki_title": "Infosys",
        "fallback_summary": (
            "Infosys Limited is an Indian multinational information technology company providing business "
            "consulting, information technology, and outsourcing services. Founded in Pune by seven engineers, "
            "it is headquartered in Bengaluru. Infosys was the first Indian company to be listed on NASDAQ."
        ),
    },
    "HDFCBANK": {
        "symbol": "NSE:HDFCBANK",
        "company_name": "HDFC Bank Limited",
        "exchange": "NSE / BSE",
        "isin": "INE040A01034",
        "sector": "Financial Services",
        "industry": "Private Banking & Financial Products",
        "market_cap_inr_cr": 1285000.0,
        "pe_ratio": 19.5,
        "pb_ratio": 2.85,
        "dividend_yield_pct": 1.15,
        "week_52_high": 1794.00,
        "week_52_low": 1363.55,
        "headquarters": "Mumbai, Maharashtra, India",
        "founded_year": 1994,
        "key_executives": "Sashidhar Jagdishan (CEO & MD), Atanu Chakraborty (Chairman)",
        "business_segments": [
            "Retail Banking & Mortgages",
            "Wholesale & Corporate Banking",
            "Treasury & Foreign Exchange",
            "Payment Products & Cards",
        ],
        "wiki_title": "HDFC_Bank",
        "fallback_summary": (
            "HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai. "
            "It is India's largest private sector bank by assets and world's tenth-largest bank by market "
            "capitalization following its merger with mortgage lender Housing Development Finance Corporation (HDFC)."
        ),
    },
    "ICICIBANK": {
        "symbol": "NSE:ICICIBANK",
        "company_name": "ICICI Bank Limited",
        "exchange": "NSE / BSE",
        "isin": "INE090A01021",
        "sector": "Financial Services",
        "industry": "Private Sector Banking",
        "market_cap_inr_cr": 875200.0,
        "pe_ratio": 18.2,
        "pb_ratio": 3.10,
        "dividend_yield_pct": 0.85,
        "week_52_high": 1300.00,
        "week_52_low": 915.00,
        "headquarters": "Mumbai, Maharashtra, India",
        "founded_year": 1994,
        "key_executives": "Sandeep Bakhshi (MD & CEO), Girish Chandra Chaturvedi (Chairman)",
        "business_segments": [
            "Retail Banking & Wealth Management",
            "Commercial & Corporate Banking",
            "Treasury Operations",
            "Digital Banking (iMobile Pay)",
        ],
        "wiki_title": "ICICI_Bank",
        "fallback_summary": (
            "ICICI Bank Limited is an Indian multinational bank and financial services company headquartered in "
            "Mumbai. It offers a wide range of banking products and financial services for corporate and retail "
            "customers through a variety of delivery channels and specialized subsidiaries."
        ),
    },
    "TATAMOTORS": {
        "symbol": "NSE:TATAMOTORS",
        "company_name": "Tata Motors Limited",
        "exchange": "NSE / BSE",
        "isin": "INE155A01022",
        "sector": "Automobile",
        "industry": "Commercial & Passenger Vehicles",
        "market_cap_inr_cr": 365800.0,
        "pe_ratio": 10.5,
        "pb_ratio": 3.8,
        "dividend_yield_pct": 0.60,
        "week_52_high": 1179.05,
        "week_52_low": 622.00,
        "headquarters": "Mumbai, Maharashtra, India",
        "founded_year": 1945,
        "key_executives": "N. Chandrasekaran (Chairman), P.B. Balaji (Group CFO)",
        "business_segments": [
            "Commercial Vehicles (Trucks & Buses)",
            "Passenger Vehicles (ICE & Electric Vehicles)",
            "Jaguar Land Rover (JLR)",
            "Vehicle Financing & Mobility Solutions",
        ],
        "wiki_title": "Tata_Motors",
        "fallback_summary": (
            "Tata Motors Limited is an Indian multinational automotive manufacturing company headquartered in "
            "Mumbai, part of the Tata Group. The company produces passenger cars, trucks, vans, coaches, and "
            "buses. It owns British luxury car marque Jaguar Land Rover and is India's leading electric car maker."
        ),
    },
    "SBIN": {
        "symbol": "NSE:SBIN",
        "company_name": "State Bank of India",
        "exchange": "NSE / BSE",
        "isin": "INE062A01020",
        "sector": "Financial Services",
        "industry": "Public Sector Commercial Banking",
        "market_cap_inr_cr": 735000.0,
        "pe_ratio": 11.2,
        "pb_ratio": 1.65,
        "dividend_yield_pct": 1.70,
        "week_52_high": 912.00,
        "week_52_low": 555.25,
        "headquarters": "Mumbai, Maharashtra, India",
        "founded_year": 1806,
        "key_executives": "C.S. Setty (Chairman)",
        "business_segments": [
            "Treasury Operations",
            "Corporate & Wholesale Banking",
            "Retail & Digital Banking (YONO)",
            "International Banking Operations",
        ],
        "wiki_title": "State_Bank_of_India",
        "fallback_summary": (
            "State Bank of India (SBI) is an Indian multinational public sector bank and financial services "
            "statutory body headquartered in Mumbai. SBI is the 48th largest bank in the world by total assets "
            "and ranks 221st in the Fortune Global 500 list, tracing its origins to the Bank of Calcutta in 1806."
        ),
    },
}

# Alias mapping for search flexibility
SEARCH_ALIASES: dict[str, str] = {
    "RELIANCE": "RELIANCE",
    "RIL": "RELIANCE",
    "MUKESH AMBANI": "RELIANCE",
    "TCS": "TCS",
    "TATA CONSULTANCY": "TCS",
    "INFY": "INFY",
    "INFOSYS": "INFY",
    "HDFC": "HDFCBANK",
    "HDFCBANK": "HDFCBANK",
    "ICICI": "ICICIBANK",
    "ICICIBANK": "ICICIBANK",
    "TATAMOTORS": "TATAMOTORS",
    "TATA MOTORS": "TATAMOTORS",
    "JLR": "TATAMOTORS",
    "SBI": "SBIN",
    "SBIN": "SBIN",
    "STATE BANK": "SBIN",
}


def find_company_key(query: str) -> str | None:
    """Find company key from user query (symbol, trading name, or alias)."""
    clean_q = query.strip().upper()
    if clean_q.startswith("NSE:") or clean_q.startswith("BSE:"):
        clean_q = clean_q.split(":")[-1]

    # Direct match in DB
    if clean_q in COMPANY_DATABASE:
        return clean_q

    # Alias match
    if clean_q in SEARCH_ALIASES:
        return SEARCH_ALIASES[clean_q]

    # Substring search in name or aliases
    for key, data in COMPANY_DATABASE.items():
        if clean_q in key or clean_q in data["company_name"].upper():
            return key

    for alias, target in SEARCH_ALIASES.items():
        if clean_q in alias:
            return target

    return None


def fetch_wikipedia_summary(wiki_title: str) -> tuple[str, str]:
    """Fetch live summary from Wikipedia REST API with timeout.

    Returns:
        tuple (summary_text, wiki_url)
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wiki_title)}"
    wiki_web_url = f"https://en.wikipedia.org/wiki/{wiki_title}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "EudaimoniaTerminal/0.1.0 (Developer: KJshomay12)"},
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            extract = data.get("extract", "")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", wiki_web_url)
            if extract:
                return extract, page_url
    except Exception:
        pass

    return "", wiki_web_url


def get_company_profile(query: str, fetch_live_wiki: bool = True) -> CompanyProfile | None:
    """Retrieve full company intelligence including Wikipedia details."""
    key = find_company_key(query)
    if not key:
        return None

    data = COMPANY_DATABASE[key]
    wiki_title = data.get("wiki_title", "")
    summary = ""
    wiki_url = f"https://en.wikipedia.org/wiki/{wiki_title}"

    if fetch_live_wiki and wiki_title:
        live_extract, live_url = fetch_wikipedia_summary(wiki_title)
        if live_extract:
            summary = live_extract
            wiki_url = live_url

    # Fallback to local verified summary if network unavailable or offline
    if not summary:
        summary = data.get("fallback_summary", "Wikipedia summary unavailable.")

    return CompanyProfile(
        symbol=data["symbol"],
        company_name=data["company_name"],
        exchange=data["exchange"],
        isin=data["isin"],
        sector=data["sector"],
        industry=data["industry"],
        market_cap_inr_cr=data["market_cap_inr_cr"],
        pe_ratio=data["pe_ratio"],
        pb_ratio=data["pb_ratio"],
        dividend_yield_pct=data["dividend_yield_pct"],
        week_52_high=data["week_52_high"],
        week_52_low=data["week_52_low"],
        headquarters=data["headquarters"],
        founded_year=data["founded_year"],
        key_executives=data["key_executives"],
        business_segments=data.get("business_segments", []),
        wiki_title=wiki_title,
        wiki_summary=summary,
        wiki_url=wiki_url,
    )
