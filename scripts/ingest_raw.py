
import argparse
import json
from pathlib import Path

from src.common.config import get_settings
from src.ingestion.raw_loader import load_raw_dataset


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="data/raw/HI-Small_Trans.csv",
    )

    parser.add_argument(
        "--profile",
        default="reports/profiling/dataset_profile.json",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000,
    )

    arguments = parser.parse_args()

    profile = json.loads(
        Path(arguments.profile).read_text(encoding="utf-8")
    )

    settings = get_settings()

    result = load_raw_dataset(
        database_url=settings.database_url,
        source_path=arguments.input,
        schema_path="sql/raw/001_create_raw_schema.sql",
        expected_rows=profile["row_count"],
        chunk_size=arguments.chunk_size,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
