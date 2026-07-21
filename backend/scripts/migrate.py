import os
from pathlib import Path

import psycopg2


database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is required")

project_root = Path(__file__).resolve().parents[2]
migrations = sorted((project_root / "migrations").glob("*.sql"))
if not migrations:
    raise RuntimeError("No SQL migrations were found")

connection = psycopg2.connect(database_url)
try:
    for migration in migrations:
        with connection.cursor() as cursor:
            cursor.execute(migration.read_text(encoding="utf-8"))
        connection.commit()
        print(f"applied {migration.name}")
except Exception:
    connection.rollback()
    raise
finally:
    connection.close()
