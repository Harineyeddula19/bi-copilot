
from copilot.runner import run_sql
from copilot.validator import UnsafeSQL

tests = {
    "DELETE operation": "DELETE FROM employees",
    "DROP operation": "DROP TABLE employees",
    "UPDATE operation": "UPDATE employees SET resigned = 0",
    "INSERT operation": "INSERT INTO employees (employee_id) VALUES (999999)",
    "Multiple statements": "SELECT * FROM employees; DROP TABLE employees",
    "Restricted metadata": "SELECT * FROM sqlite_master",
    "Unauthorized table": "SELECT * FROM secret_table",
}

passed = 0

for name, sql in tests.items():
    try:
        run_sql(sql)
        print(f"FAIL: {name} was allowed")
    except UnsafeSQL:
        print(f"PASS: {name} was blocked")
        passed += 1
    except Exception as exc:
        print(f"CHECK: {name} raised {type(exc).__name__}: {exc}")

print(f"\nSecurity tests passed: {passed}/{len(tests)}")
