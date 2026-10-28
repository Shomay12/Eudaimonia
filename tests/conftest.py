"""Pytest configuration and deterministic test fixtures.

Developer: KJshomay12
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
import pytest

# Ensure testing uses a temporary SQLite database
os.environ["EUDAIMONIA_DB_PATH"] = str(Path(__file__).parent / "test_eudaimonia.db")
os.environ["EUDAIMONIA_DATA_MODE"] = "MOCK"
os.environ["EUDAIMONIA_PROVIDER"] = "mock"


@pytest.fixture(autouse=True)
def clean_test_db():
    test_db = Path(os.environ["EUDAIMONIA_DB_PATH"])
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass
    yield
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass
