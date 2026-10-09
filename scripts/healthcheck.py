from __future__ import annotations

import argparse
import sys
from urllib.request import urlopen

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def check_database() -> bool:
    engine = None

    try:
        engine = create_engine(
            get_settings().database_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5},
        )

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM investigation.vw_prioritized_alerts"
                )
            ).scalar_one()

        print("DATABASE CONNECTION: OK")
        print(f"ALERT COUNT: {count}")
        return True

    except Exception as exc:
        print(f"DATABASE HEALTH CHECK FAILED: {exc}")
        return False

    finally:
        if engine is not None:
            engine.dispose()


def check_dashboard(url: str) -> bool:
    try:
        with urlopen(url, timeout=5) as response:
            if response.status != 200:
                print(f"DASHBOARD HTTP STATUS: {response.status}")
                return False

        print("DASHBOARD HEALTH: OK")
        return True

    except Exception as exc:
        print(f"DASHBOARD HEALTH CHECK FAILED: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dashboard-url",
        default="http://127.0.0.1:8502/_stcore/health",
    )
    parser.add_argument(
        "--skip-dashboard",
        action="store_true",
    )
    args = parser.parse_args()

    database_ok = check_database()
    dashboard_ok = (
        True
        if args.skip_dashboard
        else check_dashboard(args.dashboard_url)
    )

    if database_ok and dashboard_ok:
        print("FCI PLATFORM HEALTHY")
        return

    sys.exit(1)


if __name__ == "__main__":
    main()
