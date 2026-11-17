from .runner import run_sql
from .validator import UnsafeSQL
from . import llm


def ask(question: str, max_retries: int = 1, use_retry: bool = True) -> dict:
    """Question -> SQL -> safe execution -> result, with one automatic fix attempt."""
    try:
        sql = llm.generate_sql(question)
    except Exception as e:
        return {"status": "api_error", "sql": "", "df": None,
                "error": str(e), "retries": 0}

    if sql.upper().startswith("CANNOT_ANSWER"):
        return {"status": "declined", "sql": sql, "df": None, "retries": 0}

    retries = 0
    while True:
        try:
            return {"status": "ok", "sql": sql, "df": run_sql(sql), "retries": retries}
        except UnsafeSQL as e:
            return {"status": "blocked", "sql": sql, "df": None,
                    "error": str(e), "retries": retries}
        except Exception as e:
            if not use_retry or retries >= max_retries:
                return {"status": "error", "sql": sql, "df": None,
                        "error": str(e), "retries": retries}
            retries += 1
            try:
                sql = llm.generate_sql(question, previous_sql=sql, error=str(e))
            except Exception as e2:
                return {"status": "api_error", "sql": sql, "df": None,
                        "error": str(e2), "retries": retries}