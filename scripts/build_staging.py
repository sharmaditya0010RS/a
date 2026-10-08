import json

from src.common.config import get_settings
from src.transformation.staging import build_staging


def main() -> None:
    result = build_staging(
        database_url=get_settings().database_url,
        schema_path="sql/staging/001_create_staging_schema.sql",
        transformation_path="sql/staging/002_populate_staging.sql",
        quality_path="sql/quality/001_quality_checks.sql",
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()