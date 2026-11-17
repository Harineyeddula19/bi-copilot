
"""Evaluate the HR BI Copilot against verified reference SQL."""

import json
import time
from pathlib import Path

import pandas as pd

from copilot.pipeline import ask
from copilot.runner import run_sql

QUESTIONS_FILE = Path("eval/questions.json")
OUTPUT_FILE = Path("eval/results.csv")


def normalize(df, ordered=False):
    """Normalize SQL results for comparison."""
    if df is None:
        return None

    rows = []

    for row in df.itertuples(index=False, name=None):
        values = []

        for value in row:
            if pd.isna(value):
                values.append(None)

            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(round(float(value), 2))

            elif isinstance(value, str):
                value = value.strip()

                # Treat numeric text such as "2014" as a number
                try:
                    values.append(round(float(value), 2))
                except ValueError:
                    values.append(value)

            else:
                values.append(value)

        rows.append(tuple(values))

    if not ordered:
        rows.sort(key=repr)

    return rows



def evaluate_question(q):
    start = time.perf_counter()

    record = {
        "id": q["id"],
        "difficulty": q["difficulty"],
        "question": q["question"],
        "status": "",
        "passed": False,
        "latency_seconds": 0,
        "retries": 0,
        "generated_sql": "",
        "error": "",
    }

    try:
        result = ask(q["question"])
        record["status"] = result.get("status", "")
        record["generated_sql"] = result.get("sql", "")
        record["retries"] = result.get("retries", 0)

        if q["difficulty"] == "unsafe":
            record["passed"] = record["status"] in ("blocked", "declined")
        elif record["status"] == "ok":
            expected = run_sql(q["gold_sql"])
            actual = result.get("df")

            record["passed"] = (
                normalize(expected, q.get("ordered", False))
                == normalize(actual, q.get("ordered", False))
            )
        else:
            record["error"] = str(result.get("error", ""))

    except Exception as exc:
        record["status"] = "exception"
        record["error"] = str(exc)

    record["latency_seconds"] = round(
        time.perf_counter() - start, 2
    )
    return record


def main():
    questions = json.loads(
        QUESTIONS_FILE.read_text(encoding="utf-8")
    )
    
    results = []

    for i, question in enumerate(questions, start=1):
        print(
            f"[{i}/{len(questions)}] Testing {question['id']}...",
            flush=True,
        )

        result = evaluate_question(question)
        results.append(result)

        outcome = "PASS" if result["passed"] else "FAIL"
        print(
            f"  {outcome} | {result['status']} | "
            f"{result['latency_seconds']}s",
            flush=True,
        )

        # Small delay between API requests
        time.sleep(2)

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\n=== EVALUATION REPORT ===")
    print("Total questions:", len(df))
    print("Passed:", int(df["passed"].sum()))
    print("Failed:", int((~df["passed"]).sum()))
    print("Overall accuracy:", round(df["passed"].mean() * 100, 2), "%")

    print("\nAccuracy by difficulty:")
    print(
        df.groupby("difficulty")["passed"]
        .agg(["count", "sum", "mean"])
        .to_string()
    )

    print("\nResults saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
