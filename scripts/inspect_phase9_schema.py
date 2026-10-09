from sqlalchemy import create_engine, text

from src.common.config import get_settings

TABLES = [
    ("risk", "alerts"),
    ("risk", "transaction_scores"),
    ("risk", "rule_hits"),
    ("warehouse", "fact_transactions"),
    ("behavior", "entity_risk_profiles"),
    ("behavior", "rapid_movement"),
    ("analytics", "vw_investigation_queue"),
    ("analytics", "vw_entity_risk_leaderboard"),
]


def main() -> None:
    engine = create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
    )

    sql = text(
        """
        SELECT
            column_name,
            data_type,
            ordinal_position
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
        ORDER BY ordinal_position
        """
    )

    try:
        with engine.connect() as connection:
            for schema, table in TABLES:
                print(f"\n{'=' * 65}")
                print(f"{schema}.{table}")
                print("=" * 65)

                rows = connection.execute(
                    sql,
                    {
                        "schema": schema,
                        "table": table,
                    },
                ).mappings().all()

                if not rows:
                    print("NOT FOUND / NO VISIBLE COLUMNS")
                    continue

                for row in rows:
                    print(
                        f"{row['column_name']:<38} "
                        f"{row['data_type']}"
                    )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()