
import argparse
from pathlib import Path

from src.profiling.dataset_profiler import (
    inspect_csv,
    write_markdown_reports,
    write_profile,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile the IBM AML transaction dataset"
    )

    parser.add_argument(
        "--input",
        default="data/raw/HI-Small_Trans.csv",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100000,
    )

    parser.add_argument(
        "--output",
        default="reports/profiling/dataset_profile.json",
    )

    arguments = parser.parse_args()

    profile = inspect_csv(
        arguments.input,
        chunk_size=arguments.chunk_size,
    )

    write_profile(profile, arguments.output)

    write_markdown_reports(
        profile,
        "docs/data/PROFILING_REPORT.md",
        "docs/data/DATA_DICTIONARY.md",
    )

    print("Dataset profiling completed")
    print(f"Dataset: {profile['dataset_name']}")
    print(f"Rows: {profile['row_count']:,}")
    print(f"Columns: {profile['column_count']}")
    print(f"SHA-256: {profile['sha256']}")
    print(f"Profile: {Path(arguments.output).resolve()}")


if __name__ == "__main__":
    main()
