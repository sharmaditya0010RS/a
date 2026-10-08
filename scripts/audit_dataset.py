
import argparse
import json
import tempfile
from pathlib import Path

from src.profiling.source_audit import (
    audit_source,
    save_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="data/raw/HI-Small_Trans.csv",
    )

    parser.add_argument(
        "--output",
        default="reports/profiling/source_audit.json",
    )

    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory(
        prefix="fci_source_audit_"
    ) as temporary_directory:
        index_path = (
            Path(temporary_directory) / "row_fingerprints.sqlite"
        )

        result = audit_source(
            arguments.input,
            index_path,
        )

    save_audit(result, arguments.output)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
