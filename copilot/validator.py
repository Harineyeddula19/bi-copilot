import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"employees", "departments", "jobs", "compensation",
                  "performance", "work_patterns"}
MAX_ROWS = 1000


class UnsafeSQL(Exception):
    pass


def validate(sql: str) -> str:
    sql = sql.strip().rstrip(";")
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as e:
        raise UnsafeSQL(f"Could not parse SQL: {e}")
    if len(statements) != 1 or statements[0] is None:
        raise UnsafeSQL("Exactly one statement is allowed")
    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.With, exp.Subquery)):
        raise UnsafeSQL("Only SELECT queries are allowed")
    banned = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
              exp.Alter, exp.Command, exp.Pragma, exp.Attach)
    if tree.find(*banned):
        raise UnsafeSQL("Write or administrative statements are not allowed")
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        name = t.name.lower()
        if name not in ALLOWED_TABLES and name not in cte_names:
            raise UnsafeSQL(f"Table not allowed: {t.name}")
    if not tree.args.get("limit") and isinstance(tree, exp.Select):
        tree = tree.limit(MAX_ROWS)
    return tree.sql(dialect="sqlite")