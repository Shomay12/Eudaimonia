"""Command-line interface entry point for Eudaimonia.

Developer: KJshomay12
"""

from __future__ import annotations

import argparse
import sys

from eudaimonia import __version__
from eudaimonia.config import settings
from eudaimonia.models.events import DataMode
from eudaimonia.providers.registry import get_market_data_provider
from eudaimonia.ui.app import EudaimoniaApp


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="eudaimonia",
        description="Eudaimonia - Terminal-Native Indian Market Data & Options Analytics Terminal (NSE / BSE)",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"Eudaimonia {__version__} by KJshomay12",
    )
    parser.add_argument(
        "--provider",
        "-p",
        choices=["mock", "kite", "upstox", "dhan"],
        default=settings.PROVIDER_NAME,
        help="Market data provider adapter (default: mock)",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["MOCK", "LIVE", "HISTORICAL", "DELAYED"],
        default=settings.DATA_MODE,
        help="Data mode (default: MOCK)",
    )
    parser.add_argument(
        "--exchange",
        "-e",
        choices=["NSE", "BSE"],
        default=settings.DEFAULT_EXCHANGE,
        help="Default primary exchange (default: NSE)",
    )
    parser.add_argument(
        "--underlying",
        "-u",
        default=settings.DEFAULT_UNDERLYING,
        help="Default active underlying index or equity (default: NIFTY)",
    )
    return parser.parse_args(args)


def main() -> int:
    """CLI application runner."""
    args = parse_args()

    # Apply command line overrides
    settings.PROVIDER_NAME = args.provider
    settings.DATA_MODE = args.mode
    settings.DEFAULT_EXCHANGE = args.exchange
    settings.DEFAULT_UNDERLYING = args.underlying

    provider = get_market_data_provider(args.provider)
    app = EudaimoniaApp(provider=provider)

    try:
        app.run()
        return 0
    except (KeyboardInterrupt, SystemExit):
        return 0
    except Exception as exc:
        print(f"Error launching Eudaimonia: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
