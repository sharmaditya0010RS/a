from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings

ROOT = Path(__file__).resolve().parents[1]

SQL_PATH = (
    ROOT
    / "sql"
    / "investigation"
    / "002_performance_indexes.sql"
)


def main() -> None:
    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"SQL file not found: {SQL_PATH}"
        )

    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    statements = [
        statement.strip()
        for statement in SQL_PATH.read_text(
            encoding="utf-8"
        ).split(";")
        if statement.strip()
        and not statement.strip().startswith("--")
    ]

    # Strip full-line comments before splitting statements.
    sql_text = "\n".join(
        line
        for line in SQL_PATH.read_text(
            encoding="utf-8"
        ).splitlines()
        if not line.lstrip().startswith("--")
    )

    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    try:
        with engine.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            for index, statement in enumerate(
                statements,
                start=1,
            ):
                label = " ".join(statement.split())[:100]

                print(
                    f"[{index}/{len(statements)}] {label}",
                    flush=True,
                )

                connection.execute(text(statement))

            print(
                "\nPHASE 9 INDEX OPTIMIZATION COMPLETE",
                flush=True,
            )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()