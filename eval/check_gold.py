"""Run every gold SQL query and show its result, so you can confirm each one is correct."""
import json
from copilot.runner import run_sql

questions = json.load(open("eval/questions.json", encoding="utf-8"))
problems = 0
for q in questions:
    if "gold_sql" not in q:
        print(f"{q['id']:4} {q['difficulty']:7} (no SQL needed)  {q['question']}")
        continue
    try:
        df = run_sql(q["gold_sql"])
        preview = df.iloc[0].tolist() if len(df) else "EMPTY"
        print(f"{q['id']:4} {q['difficulty']:7} rows={len(df):<3} first={preview}")
        if df.empty:
            problems += 1
    except Exception as e:
        problems += 1
        print(f"{q['id']:4} {q['difficulty']:7} ERROR: {e}")
print("\nProblems:", problems)