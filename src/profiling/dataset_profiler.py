
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def inspect_csv(
    file_path: str | Path,
    chunk_size: int = 100000,
    encoding: str = "utf-8-sig",
) -> dict:
    path = Path(file_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    columns = None
    row_count = 0
    missing_counts = Counter()
    observed_types = {}
    nonempty_counts = Counter()
    distinct_samples = {}
    sample_limit = 10000
    sample_rows = []
    sample_row_limit = 20

    reader = pd.read_csv(
        path,
        chunksize=chunk_size,
        dtype=str,
        encoding=encoding,
        keep_default_na=False,
        on_bad_lines="error",
        low_memory=False,
    )

    for chunk in reader:
        if columns is None:
            columns = list(chunk.columns)

            if len(columns) != len(set(columns)):
                raise ValueError("Duplicate column names detected")

            observed_types = {
                column: {
                    "integer_candidate": True,
                    "decimal_candidate": True,
                    "datetime_candidate": True,
                }
                for column in columns
            }

            distinct_samples = {
                column: set() for column in columns
            }

        row_count += len(chunk)

        if len(sample_rows) < sample_row_limit:
            needed = sample_row_limit - len(sample_rows)
            sample_rows.extend(
                chunk.head(needed).to_dict(orient="records")
            )

        for column in columns:
            values = chunk[column].astype(str).str.strip()
            present = values.ne("")

            missing_counts[column] += int((~present).sum())
            nonempty_counts[column] += int(present.sum())

            valid_values = values[present]

            if valid_values.empty:
                continue

            numeric_values = pd.to_numeric(
                valid_values.str.replace(",", "", regex=False),
                errors="coerce",
            )

            integer_valid = numeric_values.notna() & (
                numeric_values % 1 == 0
            )

            observed_types[column]["integer_candidate"] &= bool(
                integer_valid.all()
            )

            observed_types[column]["decimal_candidate"] &= bool(
                numeric_values.notna().all()
            )

            date_values = pd.to_datetime(
                valid_values,
                errors="coerce",
                format="mixed",
            )

            observed_types[column]["datetime_candidate"] &= bool(
                date_values.notna().all()
            )

            remaining = sample_limit - len(distinct_samples[column])

            if remaining > 0:
                distinct_samples[column].update(
                    valid_values.drop_duplicates().head(remaining).tolist()
                )

    if columns is None:
        raise ValueError("CSV has no readable data header")

    field_profiles = []

    for column in columns:
        flags = observed_types[column]

        if nonempty_counts[column] == 0:
            inferred_type = "unknown"
        elif flags["integer_candidate"]:
            inferred_type = "integer_candidate"
        elif flags["decimal_candidate"]:
            inferred_type = "decimal_candidate"
        elif flags["datetime_candidate"]:
            inferred_type = "datetime_candidate"
        else:
            inferred_type = "string"

        field_profiles.append(
            {
                "column": column,
                "inferred_type": inferred_type,
                "missing_count": missing_counts[column],
                "nonempty_count": nonempty_counts[column],
                "missing_percentage": round(
                    100 * missing_counts[column] / row_count, 4
                )
                if row_count
                else None,
                "sample_distinct_count": len(
                    distinct_samples[column]
                ),
                "sample_distinct_count_capped": (
                    len(distinct_samples[column]) >= sample_limit
                ),
                "sample_values": sorted(
                    distinct_samples[column]
                )[:10],
            }
        )

    return {
        "dataset_name": path.name,
        "source_path": str(path),
        "file_size_bytes": path.stat().st_size,
        "sha256": file_checksum(path),
        "profiled_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "row_count": row_count,
        "column_count": len(columns),
        "columns": columns,
        "chunk_size": chunk_size,
        "field_profiles": field_profiles,
        "sample_rows": sample_rows,
        "profiling_limitations": [
            "All columns were read as strings to preserve source values.",
            "Type inference is provisional and not a database schema.",
            "Distinct counts are capped samples, not exact cardinalities.",
            "Empty strings are treated as missing.",
            "Duplicate rows have not yet been measured.",
            "Timestamp parsing does not establish source timezone.",
            "No AML label semantics are assumed.",
        ],
    }


def write_profile(profile: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as target:
        json.dump(profile, target, indent=2, ensure_ascii=False)


def write_markdown_reports(
    profile: dict,
    report_path: str | Path,
    dictionary_path: str | Path,
) -> None:
    report = Path(report_path)
    dictionary = Path(dictionary_path)

    report.parent.mkdir(parents=True, exist_ok=True)
    dictionary.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# Dataset Profiling Report",
        "",
        f"Dataset: `{profile['dataset_name']}`",
        "",
        f"Rows: {profile['row_count']:,}",
        "",
        f"Columns: {profile['column_count']}",
        "",
        f"File size: {profile['file_size_bytes']:,} bytes",
        "",
        f"SHA-256: `{profile['sha256']}`",
        "",
        f"Profiled at UTC: {profile['profiled_at_utc']}",
        "",
        "## Field Completeness",
        "",
        "| Field | Inferred Type | Missing | Missing % |",
        "|---|---|---:|---:|",
    ]

    dictionary_lines = [
        "# Dataset Data Dictionary",
        "",
        "Source-derived preliminary dictionary.",
        "",
        "Business definitions require separate validation.",
        "",
        "| Source Field | Inferred Type | Nonempty Rows | Example Values |",
        "|---|---|---:|---|",
    ]

    for field in profile["field_profiles"]:
        missing_pct = field["missing_percentage"]
        percentage = (
            f"{missing_pct:.4f}"
            if missing_pct is not None
            else "N/A"
        )

        report_lines.append(
            f"| {field['column']} | "
            f"{field['inferred_type']} | "
            f"{field['missing_count']:,} | "
            f"{percentage} |"
        )

        examples = ", ".join(
            str(value).replace("|", "/")
            for value in field["sample_values"][:3]
        )

        dictionary_lines.append(
            f"| {field['column']} | "
            f"{field['inferred_type']} | "
            f"{field['nonempty_count']:,} | "
            f"{examples} |"
        )

    report_lines.extend(
        [
            "",
            "## Profiling Limitations",
            "",
        ]
    )

    report_lines.extend(
        f"- {item}"
        for item in profile["profiling_limitations"]
    )

    dictionary_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Inferred types are candidates only.",
            "",
            "Field descriptions, keys, monetary semantics, "
            "and AML label interpretation remain subject to review.",
        ]
    )

    report.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    dictionary.write_text(
        "\n".join(dictionary_lines) + "\n",
        encoding="utf-8",
    )
