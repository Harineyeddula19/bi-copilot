
import sqlite3
import time
import pandas as pd
from .validator import validate, MAX_ROWS

DB_URI = "file:data/hr.db?mode=ro"


def run_sql(sql: str, timeout_s: float = 5.0) -> pd.DataFrame:
    safe_sql = validate(sql)

    con = sqlite3.connect(DB_URI, uri=True)

    try:
        start = time.monotonic()

        con.set_progress_handler(
            lambda: 1 if time.monotonic() - start > timeout_s else 0,
            10000
        )

        # Fetch no more than MAX_ROWS + 1 rows.
        cursor = con.execute(safe_sql)
        rows = cursor.fetchmany(MAX_ROWS + 1)

        # Reject oversized results rather than silently truncating them.
        if len(rows) > MAX_ROWS:
            raise ValueError(
                f"Query returned more than {MAX_ROWS} rows."
            )

        columns = [column[0] for column in cursor.description]
        return pd.DataFrame.from_records(rows, columns=columns)

    finally:
        con.close()
