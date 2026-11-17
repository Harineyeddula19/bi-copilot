import sqlite3
import time
import pandas as pd
from .validator import validate

DB_URI = "file:data/hr.db?mode=ro"   # read-only connection


def run_sql(sql: str, timeout_s: float = 5.0) -> pd.DataFrame:
    safe_sql = validate(sql)
    con = sqlite3.connect(DB_URI, uri=True)
    try:
        start = time.time()
        con.set_progress_handler(
            lambda: 1 if time.time() - start > timeout_s else 0, 10000)
        return pd.read_sql_query(safe_sql, con)
    finally:
        con.close()