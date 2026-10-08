
from sqlalchemy import create_engine, text

from src.common.config import get_settings

EXPECTED = {
    "row_count_reconciliation": (5_078_345, 5_078_345),
    "aml_positive_count": (5_177, 5_177),
    "duplicate_candidates": (9, 9),
    "invalid_transaction_dates": (0, 0),
    "invalid_same_account_flags": (0, 0),
    "missing_entity_keys": (0, 0),
    "invalid_amounts": (0, 0),
    "invalid_labels": (0, 0),
    "quality_issue_rows": (0, 0),
}


def main() -> None:
    engine = create_engine(
        get_settings().database_url,
        connect_args={"connect_timeout": 10},
    )

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SET statement_timeout = '15s'")
            )

            build = connection.execute(
                text(
                    "SELECT status, source_rows, staged_rows "
                    "FROM staging.build_runs "
                    "ORDER BY started_at DESC LIMIT 1"
                )
            ).mappings().one()

            results = connection.execute(
                text(
                    "SELECT check_name, observed_value, "
                    "expected_value, status "
                    "FROM staging.quality_results"
                )
            ).mappings().all()

        assert build["status"] == "completed", build
        assert build["source_rows"] == 5_078_345, build
        assert build["staged_rows"] == 5_078_345, build

        actual = {row["check_name"]: row for row in results}

        assert set(actual) == set(EXPECTED)

        for name, expected in EXPECTED.items():
            row = actual[name]
            assert (
                row["observed_value"],
                row["expected_value"],
            ) == expected, name
            assert row["status"] == "PASS", name
            print(f"PASS: {name}")

        print("\nPHASE 4 VALIDATION PASSED")
        print("Transactions: 5,078,345")
        print("AML positives: 5,177")
        print("Duplicate candidates: 9")
        print("Quality checks: 9/9")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
