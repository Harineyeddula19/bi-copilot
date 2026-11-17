
import sqlite3

conn = sqlite3.connect("data/hr.db")

# Check whether the employees table exists
table_exists = conn.execute(
    "SELECT COUNT(*) FROM sqlite_master "
    "WHERE type = 'table' AND name = 'employees'"
).fetchone()[0] == 1

print("Employee table exists:", table_exists)

if table_exists:
    # Count all employees
    total = conn.execute(
        "SELECT COUNT(*) FROM employees"
    ).fetchone()[0]

    # Count resigned employees
    resigned = conn.execute(
        "SELECT COUNT(*) FROM employees WHERE resigned = 1"
    ).fetchone()[0]

    print("Total employees:", total)
    print("Resigned employees:", resigned)

conn.close()
