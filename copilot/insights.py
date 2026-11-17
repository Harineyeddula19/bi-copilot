
"""Generate simple, data-grounded HR business insights."""

import pandas as pd


def generate_insight(question: str, df: pd.DataFrame) -> str:
    """Create a short explanation based on the SQL results."""

    if df is None or df.empty:
        return ""

    question_lower = question.lower()
    columns = {str(col).lower(): col for col in df.columns}

    # Case 1: Highest department attrition rate
    if (
        "attrition" in question_lower
        and "highest" in question_lower
        and "department_name" in columns
        and "attrition_rate" in columns
    ):
        dept_col = columns["department_name"]
        rate_col = columns["attrition_rate"]

        valid = df.dropna(subset=[dept_col, rate_col])
        if not valid.empty:
            top = valid.loc[
                pd.to_numeric(valid[rate_col], errors="coerce").idxmax()
            ]

            department = top[dept_col]
            rate = float(top[rate_col])

            return (
                f"{department} has the highest attrition rate "
                f"at {rate:.2f}% among the departments in the result. "
                "HR teams could investigate potential retention challenges "
                "in this department."
            )

    # Case 2: Hiring trends by year
    if (
        ("hire" in question_lower or "hiring" in question_lower)
        and "hire_year" in columns
        and "hires" in columns
    ):
        year_col = columns["hire_year"]
        hires_col = columns["hires"]

        valid = df.dropna(subset=[year_col, hires_col])
        if not valid.empty:
            top = valid.loc[
                pd.to_numeric(valid[hires_col], errors="coerce").idxmax()
            ]

            return (
                f"The highest number of hires in the displayed results "
                f"occurred in {top[year_col]}, with "
                f"{int(top[hires_col]):,} employees hired."
            )

    # Case 3: Average monthly salary by job title
    if (
        "salary" in question_lower
        and "job_title" in columns
        and ("avg_salary" in columns or "avg_monthly_salary" in columns)
    ):
        job_col = columns["job_title"]
        salary_col = columns.get("avg_monthly_salary") or columns.get("avg_salary")

        valid = df.dropna(subset=[job_col, salary_col])
        if not valid.empty:
            top = valid.loc[
                pd.to_numeric(valid[salary_col], errors="coerce").idxmax()
            ]

            return (
                f"{top[job_col]} has the highest average monthly salary "
                f"in the displayed results, at {float(top[salary_col]):,.2f} "
                "salary units."
            )

    # General fallback
    return (
        f"The query returned {len(df):,} row(s). "
        "Review the results table and chart for additional patterns."
    )
