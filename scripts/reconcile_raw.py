
import json
from pathlib import Path

from sqlalchemy import create_engine, text

from src.common.config import get_settings


def main() -> None:
    profile = json.loads(
        Path(
            "reports/profiling/dataset_profile.json"
        ).read_text(encoding="utf-8")
    )

    audit = json.loads(
        Path(
            "reports/profiling/source_audit.json"
        ).read_text(encoding="utf-8")
    )

    engine = create_engine(get_settings().database_url)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT COUNT(*) AS total_rows, "
                    "COUNT(*) FILTER (WHERE is_laundering = 1) "
                    "AS positive_labels, "
                    "MIN(transaction_timestamp) AS earliest, "
                    "MAX(transaction_timestamp) AS latest "
                    "FROM raw.transactions"
                )
            ).mappings().one()

            batches = connection.execute(
                text(
                    "SELECT COUNT(*) AS completed_batches "
                    "FROM raw.ingestion_batches "
                    "WHERE status = 'completed'"
                )
            ).scalar_one()

        assert result["total_rows"] == profile["row_count"]
        assert result["positive_labels"] == int(
            audit["aml_label_distribution"]["1"]
        )
        assert batches >= 1
        assert str(result["earliest"]) == audit["earliest_timestamp"]
        assert str(result["latest"]) == audit["latest_timestamp"]

        print("Raw ingestion reconciliation: PASS")
        print(f"Rows: {result['total_rows']:,}")
        print(f"AML-labeled rows: {result['positive_labels']:,}")
        print(f"Completed batches: {batches}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
