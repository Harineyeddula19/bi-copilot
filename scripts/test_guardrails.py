from copilot.runner import run_sql
from copilot.validator import UnsafeSQL

# (query, should_it_run)
tests = [
    ("SELECT COUNT(*) AS n FROM employees", True),
    ("SELECT d.department_name, AVG(e.resigned) r FROM employees e "
     "JOIN departments d USING(department_id) GROUP BY 1", True),
    ("WITH x AS (SELECT * FROM employees) SELECT COUNT(*) FROM x", True),
    ("DELETE FROM employees", False),
    ("SELECT 1; DROP TABLE employees", False),
    ("DROP TABLE employees", False),
    ("PRAGMA table_info(employees)", False),
    ("SELECT * FROM sqlite_master", False),
    ("UPDATE employees SET resigned = 0", False),
    ("WITH x AS (DELETE FROM employees RETURNING *) SELECT * FROM x", False),
]

correct = 0
for sql, should_run in tests:
    try:
        run_sql(sql)
        ran = True
        note = "ran"
    except UnsafeSQL as e:
        ran = False
        note = f"blocked: {e}"
    ok = ran == should_run
    correct += ok
    print(("PASS" if ok else "FAIL"), "|", sql[:55], "->", note)

print(f"\n{correct}/{len(tests)} behaved as expected")